"""Parse, normalize and lint deck specs (model output -> renderer input)."""
from __future__ import annotations

import json
import re

from .icons import ALIASES, ICON_NAMES

FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.M)
TRAILING_COMMA = re.compile(r",\s*([}\]])")


def parse(text: str):
    """Lenient JSON extraction. Returns (spec|None, strict_ok, error)."""
    raw = (text or "").strip()
    try:
        spec = json.loads(raw)
        if isinstance(spec, dict):
            return spec, True, ""
    except json.JSONDecodeError as exc:
        err = f"{exc.msg} at char {exc.pos}"
    else:
        err = "top-level value is not an object"
    body = FENCE.sub("", raw)
    a, b = body.find("{"), body.rfind("}")
    if a >= 0 and b > a:
        chunk = body[a:b + 1]
        for candidate in (chunk, TRAILING_COMMA.sub(r"\1", chunk)):
            try:
                spec = json.loads(candidate)
                if isinstance(spec, dict):
                    return spec, False, err
            except json.JSONDecodeError as exc:
                err = f"{exc.msg} at char {exc.pos}"
    return None, False, err


def fix_icon(name):
    n = str(name or "").strip().lower().replace(" ", "_").replace("-", "_")
    if n in ICON_NAMES:
        return n
    if n in ALIASES:
        return n
    return None


def normalize(spec: dict, brief: dict) -> dict:
    """Minimal, behaviour-preserving cleanup shared by every harness version and every model."""
    spec = dict(spec or {})
    slides = spec.get("slides")
    if not isinstance(slides, list):
        slides = []
    spec["slides"] = [s if isinstance(s, dict) else {"layout": "statement", "title": str(s)} for s in slides]
    spec.setdefault("client", brief.get("client", ""))
    spec.setdefault("title", brief.get("objective", "")[:60])
    return spec


VISIBLE_SKIP = {"layout", "icon", "hero_icons", "tone", "type", "notes", "speaker_notes", "align", "size",
                "highlight", "x", "y", "w", "h", "x2", "y2", "dashed", "verdict_icon", "ask_icon", "unit_icon"}
NUMERIC_CLAIM_KEYS = {"value", "size", "capacity"}


def visible_strings(spec: dict):
    """Yield (slide_index, key, text) for every on-canvas string (and numeric chart values)."""
    def walk(node, idx, key=None):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in VISIBLE_SKIP:
                    continue
                if k in NUMERIC_CLAIM_KEYS and isinstance(v, (int, float)) and not isinstance(v, bool):
                    yield idx, k, f"{v}"
                    continue
                yield from walk(v, idx, k)
        elif isinstance(node, list):
            for v in node:
                yield from walk(v, idx, key)
        elif isinstance(node, str):
            yield idx, key, node
    for i, s in enumerate(spec.get("slides") or []):
        yield from walk(s, i)


def notes_text(spec: dict) -> list[str]:
    return [str(s.get("notes") or s.get("speaker_notes") or "") for s in spec.get("slides") or []
            if isinstance(s, dict)]


NUM = re.compile(r"(?<![A-Za-z\d.])\d[\d,]*(?:\.\d+)?")


def numbers(text: str) -> list[float]:
    out = []
    for m in NUM.finditer(text or ""):
        tok = m.group(0).replace(",", "")
        try:
            out.append(float(tok))
        except ValueError:
            pass
    return out


def brief_numbers(brief: dict) -> set[float]:
    blob = json.dumps({k: brief.get(k) for k in ("audience", "objective", "context", "facts", "guardrails",
                                                   "slide_range")}, ensure_ascii=False)
    return set(numbers(blob))
