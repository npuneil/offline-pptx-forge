"""Local llama-server lifecycle (start / reuse / stop) on the RTX Spark GPU."""
from __future__ import annotations

import json
import subprocess
import time
import urllib.request

from .config import CONTEXT, DEFAULT_MODEL, LLAMA_SERVER, PORT, RUNS, model_path

STATE = RUNS / "server.json"


def _get(url: str, timeout: float = 2.0):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def health(port: int = PORT) -> bool:
    try:
        return _get(f"http://127.0.0.1:{port}/health").get("status") == "ok"
    except Exception:
        return False


def loaded_model(port: int = PORT) -> str | None:
    try:
        data = _get(f"http://127.0.0.1:{port}/v1/models")
        return data["data"][0]["id"]
    except Exception:
        return None


ATTACH_PORTS = (8090, 8080)


def find_existing(model: str) -> int | None:
    """Locate an already-running local llama-server that serves the same model (shared machine)."""
    for port in (PORT, *ATTACH_PORTS):
        if health(port) and loaded_model(port) == model:
            return port
    return None


def start(model: str = DEFAULT_MODEL, port: int = PORT, ctx: int = CONTEXT, wait: float = 600) -> dict:
    """Start (or reuse) llama-server. Returns {'reused', 'load_s', 'pid', 'model', 'port'}."""
    existing = find_existing(model)
    if existing:
        return {"reused": True, "load_s": 0.0, "model": model, "port": existing}
    if health(port):
        stop(port)
    gguf, _ = model_path(model)
    log = (RUNS / "server.log").open("w", encoding="utf-8")
    cmd = [str(LLAMA_SERVER), "--model", str(gguf), "--alias", model, "--host", "127.0.0.1",
           "--port", str(port), "--ctx-size", str(ctx), "--parallel", "1", "--gpu-layers", "999",
           "--fit", "on", "--flash-attn", "auto", "--jinja", "--no-context-shift",
           "--reasoning", "off", "--metrics", "--no-webui"]
    t0 = time.perf_counter()
    proc = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT,
                            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    while time.perf_counter() - t0 < wait:
        if proc.poll() is not None:
            raise RuntimeError(f"llama-server exited early (code {proc.returncode}); see runs/server.log")
        if health(port):
            break
        time.sleep(0.5)
    else:
        proc.kill()
        raise TimeoutError("llama-server did not become healthy")
    info = {"reused": False, "load_s": round(time.perf_counter() - t0, 2), "pid": proc.pid,
            "model": model, "port": port, "gguf": str(gguf)}
    STATE.write_text(json.dumps(info, indent=2), encoding="utf-8")
    return info


def stop(port: int = PORT) -> bool:
    """Stop only the llama-server this harness started (tracked PID)."""
    if not STATE.exists():
        return False
    info = json.loads(STATE.read_text(encoding="utf-8"))
    if info.get("port") != port:
        return False
    subprocess.run(["powershell", "-NoProfile", "-Command",
                    f"Stop-Process -Id {int(info['pid'])} -ErrorAction SilentlyContinue"],
                   capture_output=True)
    STATE.unlink(missing_ok=True)
    for _ in range(20):
        if not health(port):
            return True
        time.sleep(0.25)
    return not health(port)
