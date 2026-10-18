"""Stdlib streaming client for the local OpenAI-compatible llama-server."""
from __future__ import annotations

import json
import time
import urllib.request

from .config import PORT

ACTIVE = {"port": PORT}


def use_port(port: int):
    ACTIVE["port"] = port


def chat(messages: list[dict], port: int | None = None, max_tokens: int = 6000, temperature: float = 0.4,
         json_schema: dict | None = None, json_mode: bool = False, seed: int = 7, top_p: float = 0.9) -> dict:
    """Stream a chat completion. Returns text plus timing/usage telemetry."""
    body = {"model": "local", "messages": messages, "stream": True, "max_tokens": max_tokens,
            "temperature": temperature, "top_p": top_p, "seed": seed,
            "stream_options": {"include_usage": True}, "timings_per_token": False}
    if json_schema is not None:
        body["response_format"] = {"type": "json_schema", "json_schema": {"name": "deck", "schema": json_schema}}
    elif json_mode:
        body["response_format"] = {"type": "json_object"}
    port = port or ACTIVE["port"]
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions",
                                 data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    t0 = time.perf_counter()
    ttft = None
    parts: list[str] = []
    usage, timings, finish = {}, {}, None
    with urllib.request.urlopen(req, timeout=900) as resp:
        for raw in resp:
            line = raw.decode("utf-8", "replace").strip()
            if not line.startswith("data:"):
                continue
            payload = line[5:].strip()
            if payload == "[DONE]":
                break
            try:
                evt = json.loads(payload)
            except json.JSONDecodeError:
                continue
            for ch in evt.get("choices") or []:
                delta = (ch.get("delta") or {}).get("content")
                if delta:
                    if ttft is None:
                        ttft = time.perf_counter() - t0
                    parts.append(delta)
                if ch.get("finish_reason"):
                    finish = ch["finish_reason"]
            if evt.get("usage"):
                usage = evt["usage"]
            if evt.get("timings"):
                timings = evt["timings"]
    wall = time.perf_counter() - t0
    return {
        "text": "".join(parts), "wall_s": round(wall, 3), "ttft_s": round(ttft or wall, 3),
        "prompt_tokens": usage.get("prompt_tokens", timings.get("prompt_n", 0)),
        "completion_tokens": usage.get("completion_tokens", timings.get("predicted_n", 0)),
        "decode_tps": round(timings.get("predicted_per_second", 0.0), 1),
        "prefill_tps": round(timings.get("prompt_per_second", 0.0), 1),
        "finish": finish,
    }
