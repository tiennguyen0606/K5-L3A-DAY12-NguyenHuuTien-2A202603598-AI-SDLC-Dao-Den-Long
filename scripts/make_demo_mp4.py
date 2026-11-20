#!/usr/bin/env python3
"""Capture short gameplay screenshots via Chrome CDP and stitch a demo.mp4."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile
import time
from urllib.request import urlopen

from lantern_islands.benchmark import _find_chrome, _free_port
from lantern_islands.cdp import CdpWebSocket

ROOT = Path(__file__).resolve().parents[1]
FFMPEG = Path(
    r"C:\Users\Tien\AppData\Local\Microsoft\WinGet\Packages"
    r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.1-full_build\bin\ffmpeg.exe"
)
OUT = ROOT / "docs" / "demo" / "demo.mp4"


def main() -> int:
    if not FFMPEG.exists():
        raise SystemExit(f"ffmpeg not found: {FFMPEG}")
    debug_port = _free_port()
    profile = ROOT / ".demo-chrome-profile"
    url = "http://127.0.0.1:8000/?autostart=1"
    command = [
        _find_chrome(),
        "--headless=new",
        "--no-sandbox",
        "--window-size=1280,720",
        f"--remote-debugging-port={debug_port}",
        f"--user-data-dir={profile}",
        url,
    ]
    process = subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    client = None
    with tempfile.TemporaryDirectory() as tmp:
        frames = Path(tmp)
        try:
            websocket_url = None
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                try:
                    pages = json.load(urlopen(f"http://127.0.0.1:{debug_port}/json/list", timeout=1))
                    page = next((item for item in pages if item.get("type") == "page"), None)
                    if page:
                        websocket_url = page["webSocketDebuggerUrl"]
                        break
                except Exception:
                    time.sleep(0.2)
            if not websocket_url:
                raise RuntimeError("Chrome page did not start; is webapp running on :8000?")
            client = CdpWebSocket(websocket_url)
            client.call("Page.enable")
            client.call("Emulation.setDeviceMetricsOverride", {
                "width": 1280, "height": 720, "deviceScaleFactor": 1, "mobile": False,
            })
            time.sleep(2.5)
            # Click start if still on menu.
            client.call("Runtime.evaluate", {
                "expression": "document.querySelector('#start')?.click()",
            })
            time.sleep(1.0)
            # Nudge movement keys via synthesized JS state.
            client.call("Runtime.evaluate", {
                "expression": """
                  (() => {
                    const press = (key, code) => {
                      window.dispatchEvent(new KeyboardEvent('keydown', {key, code, bubbles:true}));
                    };
                    press('w','KeyW');
                    setTimeout(() => press('e','KeyE'), 800);
                    setTimeout(() => press('q','KeyQ'), 1600);
                    setTimeout(() => press(' ','Space'), 2200);
                  })()
                """,
            })
            for index in range(90):  # ~30s at 3 fps after capture
                shot = client.call("Page.captureScreenshot", {"format": "png", "fromSurface": True})
                (frames / f"frame-{index:03d}.png").write_bytes(base64.b64decode(shot["data"]))
                # mild camera/player motion
                if index % 10 == 0:
                    client.call("Runtime.evaluate", {
                        "expression": "window.dispatchEvent(new KeyboardEvent('keydown',{key:'d',code:'KeyD',bubbles:true}))",
                    })
                if index % 10 == 5:
                    client.call("Runtime.evaluate", {
                        "expression": "window.dispatchEvent(new KeyboardEvent('keyup',{key:'d',code:'KeyD',bubbles:true}))",
                    })
                time.sleep(0.25)
            # Prepend still evidence slides.
            slide_dir = frames / "slides"
            slide_dir.mkdir()
            for name, dest in [("menu.png", "000.png"), ("play.png", "001.png")]:
                src = ROOT / "docs" / "demo" / name
                if src.exists():
                    shutil.copy(src, slide_dir / dest)
            # Build concat list: 3s each slide + gameplay at 4 fps
            list_file = frames / "list.txt"
            lines = []
            for slide in sorted(slide_dir.glob("*.png")):
                lines.append(f"file '{slide.as_posix()}'")
                lines.append("duration 3")
            for frame in sorted(frames.glob("frame-*.png")):
                lines.append(f"file '{frame.as_posix()}'")
                lines.append("duration 0.25")
            if frames.glob("frame-*.png"):
                last = sorted(frames.glob("frame-*.png"))[-1]
                lines.append(f"file '{last.as_posix()}'")
            list_file.write_text("\n".join(lines) + "\n", encoding="utf-8")
            OUT.parent.mkdir(parents=True, exist_ok=True)
            cmd = [
                str(FFMPEG), "-y", "-f", "concat", "-safe", "0",
                "-i", str(list_file),
                "-vf", "scale=1280:720:force_original_aspect_ratio=decrease,pad=1280:720:(ow-iw)/2:(oh-ih)/2",
                "-r", "30", "-pix_fmt", "yuv420p", str(OUT),
            ]
            subprocess.run(cmd, check=True)
            print(f"wrote {OUT} ({OUT.stat().st_size} bytes)")
            return 0
        finally:
            if client:
                client.close()
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()


if __name__ == "__main__":
    raise SystemExit(main())
