"""Automated 100-point deck rubric. Thresholds fixed before any model output was graded.

Rubric 1.0.1 (applied retroactively to every deck, local and cloud): guardrail checks are
negation-aware and the Copilot+ rule targets 'Copilot+ PC/certification' claims. Version 1.0 matched raw
substrings, so compliant disclaimers ('not an air-gap claim') and 'M365 Copilot plus a local lane' were penalized.
"""
from __future__ import annotations

import re

from .infographics import INFOGRAPHIC
from .schema import brief_numbers, notes_text, numbers, visible_strings

RUBRIC = {
    "visual_richness": 25, "text_lightness": 20, "analogy": 15, "brief_coverage": 15,
    "claim_discipline": 15, "structure": 10,
}
WORDS_TARGET, WORDS_ZERO = 30.0, 60.0
ANALOGY_CUES = re.compile(r"\b(like|think of|imagine|as if|analogy|works as|acts as|is your)\b", re.I)
GUARDRAIL_PATTERNS = {
    "air-gap claim": r"air[- ]?gap",
    "TOPS claim": r"\bTOPS\b",
    "Copilot+ PC claim": r"copilot\s?(\+|plus)\s?(pc|certif)",
    "dollar figure": r"\$\s?\d",
    "ROI claim": r"\bROI\b",
    "replacement claim": r"replac\w*\s+(microsoft 365 |m365 )?copilot|replac\w*\s+(the )?subscription",
    "dedicated VRAM claim": r"dedicated vram|128\s?gb (of )?vram|192\s?gb",
    "certified offline claim": r"certified offline|fully offline guaranteed",
}
NEGATION = re.compile(r"\b(not|no|never|without|nor|isn't|aren't|doesn't|don't|avoid|instead of|rather than)\b", re.I)


def affirmative_hits(pattern: str, texts: list[str]) -> list[str]:
    """Matches that are asserted, not negated: compliant statements like 'not an air-gap claim' are skipped."""
    hits = []
    for t in texts:
        for sentence in re.split(r"(?<=[.!?;])\s+", t):
            for m in re.finditer(pattern, sentence, re.I):
                if not NEGATION.search(sentence[:m.start()]):
                    hits.append(sentence.strip()[:90])
    return hits


RUBRIC_VERSION = "1.0.1"
ORDINAL_OK = {float(i) for i in range(0, 11)}


def letter(score: float) -> str:
    for cut, g in ((97, "A+"), (93, "A"), (90, "A-"), (87, "B+"), (83, "B"), (80, "B-"), (77, "C+"),
                   (73, "C"), (70, "C-"), (67, "D+"), (60, "D")):
        if score >= cut:
            return g
    return "F"


def grade(spec: dict, render_summary: list[dict], brief: dict, strict_json: bool) -> dict:
    slides = spec.get("slides") or []
    n = len(slides)
    layouts = [str(s.get("layout", "")).lower() for s in slides]
    content = [i for i, l in enumerate(layouts) if l not in ("title", "cta", "section")]
    detail = {}

    # Visual richness (25)
    infog = [i for i in content if layouts[i] in INFOGRAPHIC]
    share = len(infog) / max(1, len(content))
    variety = len({layouts[i] for i in content if layouts[i] in INFOGRAPHIC})
    icons = [r["icons"] for r in render_summary if r["index"] in content]
    icon_avg = sum(icons) / max(1, len(icons))
    canvases = [s for s in slides if str(s.get("layout")).lower() == "canvas"
                and len(((s.get("data") or {}).get("elements") or [])) >= 5]
    vr = 8 * share + 7 * min(1.0, variety / 6) + 5 * min(1.0, icon_avg / 4) + (5 if len(canvases) >= 2 else 3 if canvases else 0)
    detail["visual_richness"] = {"infographic_share": round(share, 2), "distinct_layouts": variety,
                                 "icons_per_slide": round(icon_avg, 1), "canvas_diagrams": len(canvases)}

    # Text lightness (20)
    words = [r["words"] for r in render_summary]
    avg_words = sum(words) / max(1, len(words))
    tl = 20 * max(0.0, min(1.0, (WORDS_ZERO - avg_words) / (WORDS_ZERO - WORDS_TARGET)))
    detail["text_lightness"] = {"avg_words_per_slide": round(avg_words, 1), "max_words": max(words or [0])}

    # Analogy (15)
    n_analogy = layouts.count("analogy")
    cue_slides = 0
    for i, s in enumerate(slides):
        if layouts[i] == "analogy":
            continue
        head = " ".join(str(s.get(k) or "") for k in ("title", "takeaway"))
        data = s.get("data") if isinstance(s.get("data"), dict) else {}
        head += " " + str(data.get("text") or "")
        if ANALOGY_CUES.search(head):
            cue_slides += 1
    an = (10 if n_analogy >= 2 else 6 if n_analogy == 1 else 0) + min(5, 2.5 * cue_slides)
    detail["analogy"] = {"analogy_slides": n_analogy, "analogy_cue_slides": cue_slides}

    # Brief coverage (15)
    vis_blob = " ".join(t for _, _, t in visible_strings(spec)).lower()
    note_blob = " ".join(notes_text(spec)).lower()
    topics = brief.get("required_topics") or {}
    hit, miss = 0.0, []
    for topic, kws in topics.items():
        if any(k.lower() in vis_blob for k in kws):
            hit += 1
        elif any(k.lower() in note_blob for k in kws):
            hit += 0.5
            miss.append(topic + " (notes only)")
        else:
            miss.append(topic)
    bc = 15 * hit / max(1, len(topics))
    detail["brief_coverage"] = {"covered": round(hit, 1), "topics": len(topics), "missing": miss}

    # Claim discipline (15): every on-canvas number traceable to FACTS; guardrails respected
    allowed = brief_numbers(brief) | ORDINAL_OK
    found, untraced = [], []
    for idx, key, text in visible_strings(spec):
        for v in numbers(text):
            found.append(v)
            if v not in allowed and round(v) not in allowed:
                untraced.append({"slide": idx + 1, "value": v, "text": text[:60]})
    trace = 1 - len(untraced) / len(found) if found else 0.6
    all_texts = [t for _, _, t in visible_strings(spec)] + notes_text(spec)
    violations = []
    for name, pat in GUARDRAIL_PATTERNS.items():
        hits = affirmative_hits(pat, all_texts)
        if hits:
            violations.append({"rule": name, "text": hits[0]})
    cd = max(0.0, 15 * trace - 4 * len(violations))
    detail["claim_discipline"] = {"numbers_on_canvas": len(found), "untraceable": untraced[:12],
                                  "guardrail_violations": violations}

    # Structure (10)
    lo, hi = (brief.get("slide_range") or [8, 12])[:2]
    noted = sum(1 for t in notes_text(spec) if t.strip())
    fallbacks = sum(1 for r in render_summary for i in r["issues"] if i.get("kind") == "fallback")
    overflows = sum(r["overflows"] for r in render_summary)
    st = (2 if strict_json else 0) + (2 if lo <= n <= hi else 0) \
        + (1 if layouts[:1] == ["title"] else 0) + (1 if layouts[-1:] == ["cta"] else 0) \
        + 2 * min(1.0, noted / max(1, n) / 0.8) + (1 if fallbacks == 0 else 0) + (1 if overflows == 0 else 0)
    detail["structure"] = {"strict_json": strict_json, "slides": n, "notes_slides": noted,
                           "fallbacks": fallbacks, "overflows": overflows,
                           "shrunk_texts": sum(r["shrunk"] for r in render_summary)}

    scores = {"visual_richness": vr, "text_lightness": tl, "analogy": an, "brief_coverage": bc,
              "claim_discipline": cd, "structure": st}
    scores = {k: round(v, 1) for k, v in scores.items()}
    total = round(sum(scores.values()), 1)
    return {"auto_score": total, "auto_grade": letter(total), "scores": scores, "detail": detail}


def combine(auto_score: float, judge_total_50: float | None) -> dict:
    """Overall = 50% automated rubric + 50% blind visual judge (5 criteria x 10)."""
    if judge_total_50 is None:
        return {"overall": auto_score, "grade": letter(auto_score)}
    overall = round(0.5 * auto_score + 0.5 * judge_total_50 * 2, 1)
    return {"overall": overall, "grade": letter(overall)}
