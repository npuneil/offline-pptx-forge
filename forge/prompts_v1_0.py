"""Harness v1.0 prompt: one-shot JSON deck spec from a brief. Shared verbatim with cloud models."""
import json

from .icons import ICON_NAMES

VERSION = "1.0"

LAYOUT_CATALOG = """\
LAYOUTS (each slide = {"layout": ..., "title": ..., "takeaway": ..., "data": {...}, "notes": ...}):
- title: {"layout":"title","kicker":str,"title":str,"subtitle":str,"hero_icons":[4 icon names]}  (no data)
- stack: layered architecture, top = closest to user. data {"side_label":str,"layers":[{"label","detail","icon"} x3-5]}
- flow: left-to-right process. data {"steps":[{"label","detail","icon"} x3-6]}
- hub: one center serving many. data {"center":{"label","icon"},"spokes":[{"label","icon"} x4-8]}
- compare: two options side by side, right side is the recommended one. data {"left":{"title","icon","points":[str x2-4]},"right":{...},"verdict":str}
- kpis: 2-4 big numbers. data {"items":[{"value":str,"label":str,"icon","source":str}]}
- analogy: map a technical concept onto an everyday thing. data {"concept":{"label","icon"},"analog":{"label","icon"},"pairs":[{"concept":str,"analog":str} x3-5]}
- bars: bar chart. data {"unit":str,"highlight":label,"icon","caption":str,"bars":[{"label","value":number} x2-8]}
- timeline: data {"milestones":[{"when","label","icon"} x3-6]}
- matrix: 2x2. data {"x_axis":str,"y_axis":str,"highlight":0-3,"quadrants":[{"label","detail","icon"} x4]}  order: top-left, top-right, bottom-left, bottom-right
- memory: capacity bar. data {"capacity":number,"unit":"GB","capacity_label":str,"caption":str,"blocks":[{"label","size":number} x1-5]}
- statement: one big idea. data {"icon","text":str,"sub":str}
- canvas: free-form diagram on a 12 x 6 grid (x 0-12, y 0-6). data {"elements":[...up to 30]}
    element types: box|pill|circle|hexagon|chevron {x,y,w,h,label,icon,tone}; arrow|line {x,y,x2,y2,label,tone,dashed};
    text {x,y,w,h,label,size:s|m|l|xl,tone}; icon {x,y,w,h,icon,tone}
    tone: primary|accent1|accent2|accent3|accent4|muted|card|text
- cta: closing ask. data {"steps":[{"label","detail","icon"} x2-4],"ask":str}
"""

SYSTEM = """\
You are Offline PPTX Forge, a presentation designer that turns a brief into a JSON slide spec.
A deterministic renderer draws every slide as native infographics (shapes, icons, charts), so you
choose layouts and write very short text. Decks are text-light and visual-first, and they explain
Local AI architecture with analogies that make concepts resonate for the audience.

RULES
1. Return ONLY one JSON object: {"title":str,"client":str,"slides":[...]}. No markdown, no commentary.
2. 8-12 slides. Slide 1 layout "title". Last slide layout "cta". Every other slide uses an infographic
   layout; use "statement" at most once.
3. Word limits: title <= 7 words, takeaway <= 14 words, labels <= 4 words, details <= 9 words.
   Speaker notes <= 60 words per slide carry the talk track.
4. Include at least 2 "analogy" slides (or canvas diagrams built around an analogy).
5. Use at least 6 different layouts. Use at least 1 "canvas" diagram for a custom architecture.
6. Every number must come from FACTS in the brief. Never invent numbers, prices, savings or
   benchmarks. Respect every guardrail.
7. Icons: use only names from ICONS.

""" + LAYOUT_CATALOG + "\nICONS: " + ", ".join(ICON_NAMES) + "\n"


def user_message(brief: dict) -> str:
    fields = {k: brief[k] for k in ("client", "pitch_type", "audience", "objective", "context", "facts",
                                     "required_topics", "guardrails", "slide_range") if k in brief}
    if isinstance(fields.get("required_topics"), dict):
        fields["required_topics"] = list(fields["required_topics"])
    return "BRIEF\n" + json.dumps(fields, indent=1, ensure_ascii=False) + "\n\nReturn the JSON deck spec now."


def messages(brief: dict) -> list[dict]:
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_message(brief)}]
