from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import random
import sys
import time

from .simulation import Simulation


def _memory_mb() -> float:
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
                        ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
                        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
                        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                        ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t)]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        psapi = ctypes.WinDLL("psapi", use_last_error=True)
        kernel32.GetCurrentProcess.restype = wintypes.HANDLE
        psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        psapi.GetProcessMemoryInfo.restype = wintypes.BOOL
        if not psapi.GetProcessMemoryInfo(kernel32.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
            raise OSError(ctypes.get_last_error(), "GetProcessMemoryInfo failed")
        return counters.WorkingSetSize / (1024 * 1024)
    import resource
    usage = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return usage / (1024 * 1024) if sys.platform == "darwin" else usage / 1024


def run_soak(seed: int, nights: int) -> dict:
    started = time.perf_counter()
    results: list[str] = []
    crashes = 0
    mem_start = _memory_mb()
    for index in range(nights):
        rng = random.Random(seed + index + 1)
        night = index % 3 + 1
        try:
            sim = Simulation(seed + index + 1, night)
            direction = [0.0, 0.0]
            max_ticks = int(sim.time_left_s * 60)
            for tick in range(max_ticks):
                if tick % 30 == 0:
                    angle = rng.random() * math.tau
                    direction = [math.cos(angle), math.sin(angle)]
                controls = {
                    "move": direction,
                    "jump": rng.random() < 0.05,
                    "dash": rng.random() < 0.03,
                    "pulse": rng.random() < 0.02,
                    "interact": rng.random() < 0.10,
                }
                sim.step(controls)
                if sim.state in ("won", "lost"):
                    break
            results.append(sim.state if sim.state in ("won", "lost") else "lost")
        except Exception:
            crashes += 1
            results.append("crashed")
    return {
        "nights": nights, "crashes": crashes, "results": results,
        "mem_start_mb": round(mem_start, 3), "mem_end_mb": round(_memory_mb(), 3),
        "duration_s": round(time.perf_counter() - started, 3),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True, type=int)
    parser.add_argument("--nights", required=True, type=int)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    result = run_soak(args.seed, args.nights)
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if result["crashes"] == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())

