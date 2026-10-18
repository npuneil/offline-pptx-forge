"""GPU power sampling via nvidia-smi -> measured energy for a generation window."""
from __future__ import annotations

import subprocess
import threading
import time

from .config import ASSUMPTIONS


class PowerMeter:
    """Samples GPU board power every 250 ms; integrates to Wh. Adds a fixed platform overhead."""

    def __init__(self, interval_ms: int = 250):
        self.interval_ms = interval_ms
        self.samples: list[tuple[float, float]] = []
        self._proc = None
        self._thread = None
        self.t0 = self.t1 = 0.0

    def __enter__(self):
        self.t0 = time.perf_counter()
        try:
            self._proc = subprocess.Popen(
                ["nvidia-smi", "--query-gpu=power.draw", "--format=csv,noheader,nounits", "-i", "0",
                 f"-lms", str(self.interval_ms)],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
            self._thread = threading.Thread(target=self._read, daemon=True)
            self._thread.start()
        except FileNotFoundError:
            self._proc = None
        return self

    def _read(self):
        for line in self._proc.stdout:
            try:
                self.samples.append((time.perf_counter(), float(line.strip())))
            except ValueError:
                pass

    def __exit__(self, *exc):
        self.t1 = time.perf_counter()
        if self._proc:
            self._proc.terminate()
            try:
                self._proc.wait(timeout=3)
            except Exception:
                self._proc.kill()

    def result(self) -> dict:
        dur = max(self.t1 - self.t0, 1e-6)
        watts = [w for _, w in self.samples]
        avg = sum(watts) / len(watts) if watts else 0.0
        gpu_wh = avg * dur / 3600
        platform_wh = ASSUMPTIONS["platform_overhead_w"] * dur / 3600
        return {"seconds": round(dur, 2), "samples": len(watts), "gpu_avg_w": round(avg, 1),
                "gpu_peak_w": round(max(watts), 1) if watts else 0.0,
                "gpu_wh": round(gpu_wh, 4), "platform_wh": round(platform_wh, 4),
                "total_wh": round(gpu_wh + platform_wh, 4)}
