from __future__ import annotations

import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
from pathlib import Path
import platform
import shutil
import socket
import subprocess
import threading
import time
from urllib.request import urlopen

from .cdp import CdpWebSocket


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    index = max(0, math.ceil(percentile * len(ordered)) - 1)
    return ordered[index]


def calculate_metrics(frame_ms: list[float]) -> dict:
    if not frame_ms:
        raise ValueError("at least one measured frame is required")
    count = len(frame_ms)
    worst_count = max(1, math.ceil(0.01 * count))
    worst = sorted(frame_ms, reverse=True)[:worst_count]
    return {
        "avg_fps": 1000 * count / sum(frame_ms),
        "p1_low_fps": 1000 / (sum(worst) / len(worst)),
        "frame_ms_p95": _percentile(frame_ms, 0.95),
        "frames": count,
    }


class _QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:
        pass


def _free_port() -> int:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def _find_chrome() -> str:
    candidates = [
        os.environ.get("CHROME_BIN"), shutil.which("google-chrome"), shutil.which("chrome"),
        shutil.which("chromium"), shutil.which("chromium-browser"),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return str(candidate)
    raise RuntimeError("Chrome/Chromium not found; set CHROME_BIN")


def run_benchmark(seed: int, duration: int) -> dict:
    handler = partial(_QuietHandler, directory="web")
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    debug_port = _free_port()
    url = f"http://127.0.0.1:{server.server_port}/benchmark.html?duration={duration}&seed={seed}"
    profile = Path(".bench-chrome-profile").resolve()
    command = [
        _find_chrome(), "--headless=new", "--no-sandbox", "--disable-gpu-vsync",
        "--window-size=1280,720", f"--remote-debugging-port={debug_port}",
        f"--user-data-dir={profile}", url,
    ]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    client = None
    try:
        deadline = time.monotonic() + 12
        websocket_url = None
        while time.monotonic() < deadline:
            try:
                pages = json.load(urlopen(f"http://127.0.0.1:{debug_port}/json/list", timeout=1))
                page = next((item for item in pages if item.get("type") == "page" and "benchmark.html" in item.get("url", "")), None)
                if page:
                    websocket_url = page["webSocketDebuggerUrl"]
                    break
            except Exception:
                time.sleep(0.1)
        if not websocket_url:
            raise RuntimeError("benchmark page did not start")
        client = CdpWebSocket(websocket_url)
        deadline = time.monotonic() + duration + 15
        result = None
        while time.monotonic() < deadline:
            response = client.call("Runtime.evaluate", {"expression": "JSON.stringify(window.benchmarkResult || null)", "returnByValue": True})
            value = response.get("result", {}).get("value", "null")
            result = json.loads(value)
            if result:
                break
            time.sleep(0.25)
        if not result:
            raise RuntimeError("benchmark timed out")
        result["os"] = platform.platform()
        result["peak_mem_mb"] = None
        result["vsync_off"] = True
        for key in ("avg_fps", "p1_low_fps", "frame_ms_p95", "load_ms"):
            result[key] = round(float(result[key]), 3)
        return result
    finally:
        if client:
            client.close()
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        server.shutdown()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--duration", required=True, type=int)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    Path(args.out).write_text(json.dumps(run_benchmark(args.seed, args.duration), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
