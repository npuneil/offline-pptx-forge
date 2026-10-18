"""Deterministic deck lint for harness v1.1. Produces targeted, per-slide repair instructions.

Every check is something a careful human reviewer would flag; the checks come from the round-1 learnings
(frontier decks + blind judge) and from the brief itself (facts, guardrails, required topics).
"""
from __future__ import annotations

import re

from .grade import GUARDRAIL_PATTERNS, ORDINAL_OK
from .schema import brief_numbers, numbers, visible_strings

WORD_BUDGET = 32
CONTENT_SKIP = {"title", "cta", "section"}
EXTRA_BANNED = {"unhedged offline claim": r"works (fully )?offline|runs (fully )?offline|no internet (needed|required)"}
CUE = re.compile(r"\b(like|think of|imagine|as if)\b", re.I)
BOX_TYPES = {"box", "pill", "circle", "hexagon", "chevron"}


def _num(v, d=0.0):
    try:
        return float(v)
    except (TypeError, ValueError):
        return d


def _words(s) -> int:
    return len(str(s or "").split())


def _floating_boxes(elements: list) -> list[str]:
    """Boxes that no arrow/line endpoint touches (within 0.35 grid units of the box edge)."""
    ends = []
    for e in elements:
        if isinstance(e, dict) and str(e.get("type", "")).lower() in ("arrow", "line"):
            x, y = _num(e.get("x")), _num(e.get("y"))
            ends += [(x, y), (_num(e.get("x2"), x + 2), _num(e.get("y2"), y))]
    out = []
    for e in elements:
        if not isinstance(e, dict) or str(e.get("type", "box")).lower() not in BOX_TYPES:
            continue
        x, y, w, h = _num(e.get("x")), _num(e.get("y")), _num(e.get("w"), 2), _num(e.get("h"), 1)
        m = 0.35
        if not any(x - m <= px <= x + w + m and y - m <= py <= y + h + m for px, py in ends):
            out.append(str(e.get("label") or "?"))
    return out


def lint(spec: dict, brief: dict, render_summary: list[dict], arc: list[tuple] | None = None,
         reserved_slides: int = 0) -> list[dict]:
    slides = spec.get("slides") or []
    layouts = [str(s.get("layout", "")).lower() for s in slides]
    allowed = brief_numbers(brief) | ORDINAL_OK
    rs = {r["index"]: r for r in render_summary}
    issues = []

    def add(idx, code, msg):
        issues.append({"slide": idx, "code": code, "msg": msg})

    # Deck-level
    lo, hi = (brief.get("slide_range") or [8, 12])[:2]
    n = len(slides) + reserved_slides
    if not lo <= n <= hi:
        add(-1, "count", f"deck must have {lo - reserved_slides}-{hi - reserved_slides} slides (has {len(slides)}); "
                         f"delete or merge the weakest slide by returning it with \"delete\": true")
    if layouts[:1] != ["title"]:
        add(0, "first", "slide 0 must use layout 'title'")
    if layouts[-1:] != ["cta"]:
        add(len(slides) - 1, "last", "last slide must use layout 'cta'")
    an = [i for i, l in enumerate(layouts) if l == "analogy"]
    if len(an) < 2:
        add(-1, "analogy_count", "deck needs exactly two 'analogy' slides; convert the best-fitting slide using the ANALOGY BANK")
    for a, b in zip(an, an[1:]):
        if b == a + 1:
            add(b, "analogy_adjacent", "two analogy slides are back to back; make this one a different layout or move the analogy into a takeaway")
    cue_slides = [i for i, s in enumerate(slides) if layouts[i] not in ("analogy", "title")
                  and CUE.search(f"{s.get('title', '')} {s.get('takeaway', '')}")]
    if len(cue_slides) < 2:
        cands = [i for i, l in enumerate(layouts) if l in ("kpis", "flow", "canvas", "bars", "stack", "matrix", "compare")
                 and i not in cue_slides][:2 - len(cue_slides)]
        for i in cands:
            add(i, "woven_analogy", "weave a short, accurate analogy into the takeaway using 'like' (<= 12 words)")
    vis = " ".join(t for _, _, t in visible_strings(spec)).lower()
    for topic, kws in (brief.get("required_topics") or {}).items():
        if topic == "made_on_device" and reserved_slides:
            continue
        if not any(k.lower() in vis for k in kws):
            add(-1, "topic", f"topic '{topic}' is not visible on any slide; work one of these words into a fitting "
                             f"slide's label or takeaway: {', '.join(kws[:4])}")

    # Slide-level
    for i, s in enumerate(slides):
        lay = layouts[i]
        r = rs.get(i, {})
        data = s.get("data") if isinstance(s.get("data"), dict) else {}
        if arc and len(slides) == len(arc) and lay != arc[i][1]:
            add(i, "arc_layout", f"use layout '{arc[i][1]}' for the '{arc[i][0]}' slot")
        if lay in ("memory", "hub", "statement"):
            add(i, "layout_banned", f"replace the '{lay}' layout ({'use kpis' if lay == 'memory' else 'use a layout that encodes the idea'})")
        if r.get("words", 0) > WORD_BUDGET:
            add(i, "words", f"{r['words']} visible words; cut to <= 28 (shorter details, fewer items)")
        if r.get("overflows", 0) or r.get("shrunk", 0):
            add(i, "fit", "some text does not fit its shape; shorten the longest labels/details")
        tw = _words(s.get("title"))
        if tw > 7:
            add(i, "title_long", f"title has {tw} words; <= 7")
        elif lay not in ("title",) and tw <= 2:
            add(i, "title_label", "title reads as a label; rewrite as an insight claim with a verb (<= 7 words)")
        if _words(s.get("takeaway")) > 14:
            add(i, "takeaway_long", "takeaway <= 12 words")
        bad = []
        for _, _, text in visible_strings({"slides": [s]}):
            for v in numbers(text):
                if v not in allowed and round(v) not in allowed:
                    bad.append(f"{v:g}")
        if bad:
            add(i, "numbers", f"numbers not in ALLOWED NUMBERS: {', '.join(sorted(set(bad)))}; replace with allowed "
                              f"numbers or words")
        texts = [t for _, _, t in visible_strings({"slides": [s]})] + [str(s.get("notes") or "")]
        blob = " ".join(texts)
        for name, pat in list(GUARDRAIL_PATTERNS.items()) + list(EXTRA_BANNED.items()):
            m = re.search(pat, blob, re.I)
            if m:
                add(i, "guardrail", f"remove '{m.group(0)}' ({name}) from slide and notes; state the positive version")
        if not str(s.get("notes") or "").strip():
            add(i, "notes", "add 2-3 sentences of speaker notes (<= 45 words)")
        if lay not in CONTENT_SKIP and r.get("icons", 0) < 3 and lay not in ("bars", "analogy"):
            add(i, "icons", "show at least 3 icons (add icon names to items)")
        if lay == "bars":
            bars = [b for b in (data.get("bars") or []) if isinstance(b, dict)]
            labels = [str(b.get("label", "")) for b in bars]
            if len(bars) < 2:
                add(i, "bars", "a bar chart needs 2-6 bars of the same unit")
            if data.get("highlight") not in labels:
                add(i, "bars_highlight", "'highlight' must equal one bar label exactly")
            single = any(re.search(r"\b1 stream|single", l, re.I) for l in labels)
            multi = any(re.search(r"\b[2-9] streams|concurrent|aggregate", l, re.I) for l in labels)
            if single and multi:
                add(i, "bars_mixed", "chart mixes single-stream and aggregate throughput; keep one measurement type")
        if lay == "analogy":
            pairs = data.get("pairs") or []
            if len(pairs) < 4:
                add(i, "analogy_pairs", "use 4 concept/analog pairs")
        if lay == "canvas":
            els = [e for e in (data.get("elements") or []) if isinstance(e, dict)]
            if len(els) < 10:
                add(i, "canvas_sparse", f"canvas has {len(els)} elements; build a connected diagram with 12-20 (see EXEMPLAR)")
            floating = _floating_boxes(els)
            if floating:
                add(i, "canvas_floating", f"boxes not touched by any arrow/line: {', '.join(floating[:5])}; connect them "
                                          f"(arrow endpoints on the box edge) or remove them")
            out = [str(e.get("label") or e.get("type")) for e in els
                   if _num(e.get("x")) + (_num(e.get("w"), 2) if str(e.get("type", "")).lower() not in ("arrow", "line") else 0) > 12.05
                   or _num(e.get("y")) + (_num(e.get("h"), 1) if str(e.get("type", "")).lower() not in ("arrow", "line") else 0) > 6.05]
            if out:
                add(i, "canvas_bounds", f"elements outside the 12 x 6 grid: {', '.join(out[:4])}")
        if lay == "cta":
            if len(data.get("steps") or []) < 3:
                add(i, "cta_steps", "CTA needs 3 steps")
            if not str(data.get("ask") or "").strip():
                add(i, "cta_ask", "CTA needs an 'ask' sentence with the exact pilot size and duration")
    return issues


def per_slide_counts(issues: list[dict]) -> dict:
    out = {}
    for it in issues:
        out[it["slide"]] = out.get(it["slide"], 0) + 1
    return out
