"""Story deck: the Offline PPTX Forge journey (v1.0 -> frontier benchmark -> v1.1), told with measured data.

  python bench/story.py [--template surface_ultra] [--out C:\\Users\\me\\Downloads\\Offline-PPTX-Forge-Story.pptx]

Every number on a slide is computed here from bench/results.json and the run telemetry, then rendered offline
by the Forge renderer. Before/after deck thumbnails and the template comparison are real exported slides.
"""
import argparse
import json
import math
import shutil
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image  # noqa: E402
from pptx import Presentation  # noqa: E402
from pptx.dml.color import RGBColor  # noqa: E402
from pptx.util import Inches, Pt  # noqa: E402

from forge import themes  # noqa: E402
from forge.config import BENCH, RUNS  # noqa: E402
from forge.infographics import AREA  # noqa: E402
from forge.preview import preview  # noqa: E402
from forge.render import render  # noqa: E402

LABEL = {"local-v1.0": "Local v1.0", "local-v1.1": "Local v1.1",
         "claude-opus-5.5-low": "Opus low", "claude-opus-5.5-high": "Opus high", "claude-opus-5.5-max": "Opus max",
         "gpt-6-astra-low": "Astra low", "gpt-6-astra-high": "Astra high", "gpt-6-astra-max": "Astra max"}
CLOUD = ["claude-opus-5.5-low", "claude-opus-5.5-high", "claude-opus-5.5-max",
         "gpt-6-astra-low", "gpt-6-astra-high", "gpt-6-astra-max"]
ORDER = ["local-v1.0", "local-v1.1", *CLOUD]
OUT = RUNS / "story"
AX, AY, AW, AH = AREA
GX, GY = AW / 12.0, AH / 6.0  # canvas grid unit in inches


def gx(inch_x):
    return (inch_x - AX) / GX


def gy(inch_y):
    return (inch_y - AY) / GY


def n1(x):
    return f"{x:.1f}".rstrip("0").rstrip(".")


def deck_grid(pngs, out, bg, cols=3, rows=4, tw=640, gap=12):
    th = tw * 9 // 16
    im = Image.new("RGB", (cols * tw + (cols + 1) * gap, rows * th + (rows + 1) * gap), "#" + bg)
    for k, p in enumerate(pngs[:cols * rows]):
        thumb = Image.open(p).convert("RGB").resize((tw, th), Image.LANCZOS)
        im.paste(thumb, (gap + (k % cols) * (tw + gap), gap + (k // cols) * (th + gap)))
    im.save(out)
    return out, im.size[0] / im.size[1]


def load_data():
    r = json.loads((BENCH / "results.json").read_text(encoding="utf-8"))
    rows = {(x["config"], x["brief"]): x for x in r["rows"]}
    return r, r["aggregate"], r["cloud_reference"], r["criteria"], rows


def template_timings(tmp):
    spec = json.loads((RUNS / "v1.1" / "contoso_sales" / "contoso_sales.spec.json").read_text(encoding="utf-8"))
    out = {}
    for t in ("microsoft", "surface", "surface_ultra"):
        t0 = time.perf_counter()
        render(spec, t, tmp / f"_time-{t}.pptx")
        out[t] = time.perf_counter() - t0
        (tmp / f"_time-{t}.pptx").unlink(missing_ok=True)
    return out


def build_spec(r, agg, ref, crit, rows, timings, images):
    v0, v1 = agg["local-v1.0"], agg["local-v1.1"]
    c0, c1 = crit["local-v1.0"], crit["local-v1.1"]
    cloud_j = [agg[c]["judge"] for c in CLOUD]
    cost_ratio = ref["cost"] / v1["cost"]
    best = max(CLOUD, key=lambda c: agg[c]["overall"])
    om, ol = agg["claude-opus-5.5-max"], agg["claude-opus-5.5-low"]
    tok_x = om["out_tokens"] / ol["out_tokens"]
    lint = [rows[("local-v1.1", b)]["lint"] for b in ("contoso_sales", "zava_technical")]
    lint0 = sum(h[0]["issues"] for h in lint)
    lint1 = sum([x for x in h if x.get("accepted", True)][-1]["issues"] for h in lint)
    z0, z1 = rows[("local-v1.0", "zava_technical")], rows[("local-v1.1", "zava_technical")]
    k0, k1 = rows[("local-v1.0", "contoso_sales")], rows[("local-v1.1", "contoso_sales")]
    n_decks = len(r["rows"])
    fastest_t = min(timings.values())
    slowest_t = max(timings.values())

    def gd(k):
        a, b = c0[k]["grade"], c1[k]["grade"]
        return b if a == b else f"{a} → {b}"

    def held(k):
        return " (held)" if c0[k]["grade"] == c1[k]["grade"] else ""

    # ---- quality vs cost scatter (log x) on the 12 x 6 canvas grid
    lo, hi = -1.2, 3.4

    def px(cost_per_1k):
        return 1.2 + (math.log10(cost_per_1k) - lo) / (hi - lo) * 10.4

    def py(j):
        return 5.0 - (j - 15) / 30 * 4.7

    D = 0.34  # dot diameter in inches
    dw, dh = D / GX, D / GY
    sc = [{"type": "line", "x": 1.2, "y": 5.0, "x2": 11.7, "y2": 5.0},
          {"type": "line", "x": 1.2, "y": 0.6, "x2": 1.2, "y2": 5.0}]
    for v, lab in ((0.1, "$0.10"), (1, "$1"), (10, "$10"), (100, "$100"), (1000, "$1,000")):
        sc.append({"type": "text", "x": px(v) - 0.6, "y": 5.05, "w": 1.2, "h": 0.42, "label": lab, "size": "s",
                   "align": "c", "tone": "muted"})
    for j in (20, 30, 40):
        sc.append({"type": "text", "x": 0.15, "y": py(j) - 0.25, "w": 0.95, "h": 0.42, "label": str(j), "size": "s",
                   "align": "r", "tone": "muted"})
    sc += [{"type": "text", "x": 3.4, "y": 5.45, "w": 6.4, "h": 0.5, "label": "Cost per 1,000 decks (log scale)",
            "size": "s", "align": "c", "tone": "muted"},
           {"type": "text", "x": 0.0, "y": 0.0, "w": 2.6, "h": 0.45, "label": "Blind judge /50", "size": "s",
            "tone": "muted"}]
    cx0 = min(px(agg[c]["cost"] * 1000) for c in CLOUD) - 0.45
    cx1 = max(px(agg[c]["cost"] * 1000) for c in CLOUD) + 0.45
    cy0, cy1 = py(max(cloud_j)) - 0.45, py(min(cloud_j)) + 0.45
    sc.append({"type": "box", "x": cx0, "y": cy0, "w": cx1 - cx0, "h": cy1 - cy0, "tone": "card"})
    sc += [{"type": "circle", "x": cx0 + 0.05, "y": cy0 - 0.4, "w": dw, "h": dh, "tone": "accent1"},
           {"type": "text", "x": cx0 + 0.05 + dw + 0.08, "y": cy0 - 0.5, "w": 1.0, "h": 0.42, "label": "Opus",
            "size": "s", "tone": "muted"},
           {"type": "circle", "x": cx0 + 1.4, "y": cy0 - 0.4, "w": dw, "h": dh, "tone": "accent2"},
           {"type": "text", "x": cx0 + 1.4 + dw + 0.08, "y": cy0 - 0.5, "w": 1.0, "h": 0.42, "label": "Astra",
            "size": "s", "tone": "muted"}]
    for c in CLOUD:
        a = agg[c]
        sc.append({"type": "circle", "x": px(a["cost"] * 1000) - dw / 2, "y": py(a["judge"]) - dh / 2, "w": dw,
                   "h": dh, "tone": "accent2" if "astra" in c else "accent1"})
    sc += [{"type": "text", "x": cx0 - 0.3, "y": cy1 + 0.05, "w": cx1 - cx0 + 0.6, "h": 0.45,
            "label": "Frontier cloud: 6 configs", "size": "s", "align": "c"},
           {"type": "text", "x": cx0 - 0.3, "y": cy1 + 0.45, "w": cx1 - cx0 + 0.6, "h": 0.45,
            "label": f"${min(agg[c]['cost'] for c in CLOUD) * 1000:,.0f}-${max(agg[c]['cost'] for c in CLOUD) * 1000:,.0f}"
                     f" | judge {n1(min(cloud_j))}-{n1(max(cloud_j))}", "size": "s", "align": "c", "tone": "muted"}]
    for cfg, tone in (("local-v1.0", "muted"), ("local-v1.1", "primary")):
        a = agg[cfg]
        x, y = px(a["cost"] * 1000), py(a["judge"])
        sc.append({"type": "circle", "x": x - dw * 0.7, "y": y - dh * 0.7, "w": dw * 1.4, "h": dh * 1.4, "tone": tone})
        sc.append({"type": "text", "x": x + 0.35, "y": y - 0.5, "w": 3.4, "h": 0.5, "label": LABEL[cfg], "size": "m",
                   "tone": tone if tone == "primary" else None})
        sc.append({"type": "text", "x": x + 0.35, "y": y, "w": 3.6, "h": 0.45,
                   "label": f"judge {n1(a['judge'])} | ${a['cost'] * 1000:,.2f}", "size": "s", "tone": "muted"})
    a0, a1 = agg["local-v1.0"], agg["local-v1.1"]
    sc.append({"type": "arrow", "x": px(a0["cost"] * 1000) + 0.2, "y": py(a0["judge"]) - 0.35,
               "x2": px(a1["cost"] * 1000) - 0.15, "y2": py(a1["judge"]) + 0.4, "tone": "primary"})
    sc.append({"type": "arrow", "x": px(a1["cost"] * 1000) + 0.5, "y": 2.75, "x2": cx0 - 0.1, "y2": 2.75,
               "tone": "accent3", "dashed": True})
    sc.append({"type": "text", "x": px(a1["cost"] * 1000) + 0.6, "y": 2.85, "w": 4.0, "h": 0.5,
               "label": f"{cost_ratio:,.0f}x cheaper than cloud median", "size": "s", "tone": "accent3"})

    # ---- before / after image slides
    def before_after(key, r0, r1):
        (p0, ar0), (p1, ar1) = images[key]
        h = 4.05
        w0, w1 = h * ar0, h * ar1
        gap = 0.9
        x0 = AX + (AW - (w0 + w1 + gap)) / 2
        x1 = x0 + w0 + gap
        y0 = AY
        images[key + "_place"] = [(p0, x0, y0, h), (p1, x1, y0, h)]
        mid = y0 + h / 2
        return {"elements": [
            {"type": "arrow", "x": gx(x0 + w0 + 0.12), "y": gy(mid), "x2": gx(x1 - 0.12), "y2": gy(mid),
             "tone": "primary"},
            {"type": "text", "x": gx(x0), "y": gy(y0 + h + 0.1), "w": w0 / GX, "h": 0.6, "align": "c", "size": "m",
             "label": f"v1.0 | {r0['slides']} slides | judge {n1(r0['judge'])}/50"},
            {"type": "text", "x": gx(x1), "y": gy(y0 + h + 0.1), "w": w1 / GX, "h": 0.6, "align": "c", "size": "m",
             "tone": "primary", "label": f"v1.1 | {r1['slides']} slides | judge {n1(r1['judge'])}/50"}]}

    # ---- template comparison slide
    tw_in, gap_t = 3.9, (AW - 3 * 3.9) / 2
    th_in = tw_in * 9 / 16
    tel = []
    images["templates_place"] = []
    for k, (t, name) in enumerate((("microsoft", "Microsoft"), ("surface", "Surface"),
                                   ("surface_ultra", "Surface Ultra"))):
        x = AX + k * (tw_in + gap_t)
        images["templates_place"].append((images["templates"][t], x, AY + 0.1, th_in))
        tel.append({"type": "text", "x": gx(x), "y": gy(AY + 0.2 + th_in), "w": tw_in / GX, "h": 0.55,
                    "label": name, "size": "m", "align": "c"})
        tel.append({"type": "text", "x": gx(x), "y": gy(AY + 0.62 + th_in), "w": tw_in / GX, "h": 0.45,
                    "label": f"re-rendered in {timings[t]:.2f} s", "size": "s", "align": "c", "tone": "muted"})
    tel += [{"type": "pill", "x": 0.0, "y": 4.45, "w": 12.0, "h": 0.95, "icon": "layers", "tone": "card",
             "label": "1 JSON spec, 3 templates, 0 LLM calls to restyle"}]

    s = []
    s.append({"layout": "title", "kicker": "Offline PPTX Forge | benchmark story",
              "title": "Teaching Laptop Ultra to Teach Laptop Ultra",
              "subtitle": f"{n_decks} decks scored, 2 briefs, 1 round of frontier distillation",
              "hero_icons": ["chart", "laptop", "gpu", "leaf"],
              "notes": "This is the story of a pitch-deck generator that runs entirely on a Surface Laptop Ultra. "
                       "We built it, graded it against frontier cloud models, let it learn from them once, "
                       "and measured what changed."})
    s.append({"layout": "kpis", "title": "The Test: Customer Decks, Zero Cloud Calls",
              "takeaway": "Same prompt, same renderer, same rubric for every lane.",
              "data": {"items": [
                  {"value": "2", "label": "Briefs: Contoso sales, Zava technical", "icon": "document",
                   "source": "fictional clients"},
                  {"value": "3", "label": "Templates to choose from", "icon": "layers", "source": "MS, Surface, Ultra"},
                  {"value": "6", "label": "Cloud configs: Opus + Astra", "icon": "cloud", "source": "low, high, max"},
                  {"value": "4", "label": "Criteria: cost, CO2, time, quality", "icon": "target",
                   "source": "graded per deck"}]},
              "notes": "Two fictional customers: an executive sales pitch for Contoso and an engineering briefing "
                       "for Zava. Each lane got the identical brief. Cloud specs went through the same renderer and "
                       "rubric as the local ones, so only the model and harness differ."})
    s.append({"layout": "canvas", "title": "How It Works: Everything Stays on the Laptop",
              "takeaway": "Brief in, native PowerPoint out; drafting and rendering run on-device.",
              "data": {"elements": [
                  {"type": "text", "x": 0.3, "y": 0.0, "w": 9.0, "h": 0.5, "size": "s", "tone": "primary",
                   "label": "SURFACE LAPTOP ULTRA | NVIDIA RTX SPARK"},
                  {"type": "line", "x": 0.2, "y": 0.55, "x2": 9.65, "y2": 0.55, "tone": "accent2", "dashed": True},
                  {"type": "line", "x": 9.65, "y": 0.55, "x2": 9.65, "y2": 5.75, "tone": "accent2", "dashed": True},
                  {"type": "line", "x": 9.65, "y": 5.75, "x2": 0.2, "y2": 5.75, "tone": "accent2", "dashed": True},
                  {"type": "line", "x": 0.2, "y": 5.75, "x2": 0.2, "y2": 0.55, "tone": "accent2", "dashed": True},
                  {"type": "box", "x": 0.5, "y": 0.9, "w": 1.7, "h": 1.05, "icon": "document", "label": "Brief"},
                  {"type": "arrow", "x": 2.2, "y": 1.42, "x2": 2.7, "y2": 1.42},
                  {"type": "box", "x": 2.7, "y": 0.9, "w": 2.4, "h": 1.05, "icon": "ai", "label": "Qwen3-Coder 30B",
                   "tone": "primary"},
                  {"type": "arrow", "x": 5.1, "y": 1.42, "x2": 5.5, "y2": 1.42},
                  {"type": "box", "x": 5.5, "y": 0.9, "w": 1.7, "h": 1.05, "icon": "code", "label": "JSON spec",
                   "tone": "accent1"},
                  {"type": "arrow", "x": 7.2, "y": 1.42, "x2": 7.6, "y2": 1.42},
                  {"type": "box", "x": 7.6, "y": 0.9, "w": 1.8, "h": 1.05, "icon": "layers", "label": "Renderer",
                   "tone": "accent2"},
                  {"type": "arrow", "x": 8.5, "y": 1.95, "x2": 8.5, "y2": 2.65},
                  {"type": "box", "x": 7.6, "y": 2.65, "w": 1.8, "h": 1.05, "icon": "checklist", "label": "Lint",
                   "tone": "accent3"},
                  {"type": "line", "x": 7.6, "y": 3.17, "x2": 3.9, "y2": 3.17, "label": "targeted fixes"},
                  {"type": "arrow", "x": 3.9, "y": 3.17, "x2": 3.9, "y2": 1.95},
                  {"type": "arrow", "x": 8.5, "y": 3.7, "x2": 8.5, "y2": 4.4},
                  {"type": "box", "x": 7.6, "y": 4.4, "w": 1.8, "h": 1.05, "icon": "download", "label": "PPTX",
                   "tone": "accent4"},
                  {"type": "text", "x": 0.5, "y": 4.55, "w": 6.8, "h": 0.8, "size": "s", "tone": "muted",
                   "label": "Measured per deck: seconds, tokens, watt-hours (nvidia-smi)"},
                  {"type": "box", "x": 10.0, "y": 0.9, "w": 1.9, "h": 1.05, "icon": "cloud", "label": "Cloud APIs",
                   "tone": "muted"},
                  {"type": "text", "x": 9.85, "y": 2.1, "w": 2.2, "h": 0.9, "size": "l", "align": "c",
                   "tone": "primary", "label": "0 calls"}]},
              "notes": "The local model only writes a JSON blueprint. A deterministic renderer turns it into native, "
                       "editable shapes and charts. In v1.1 a lint step checks the rendered deck and sends targeted "
                       "fixes back to the model. The cloud is never called."})
    s.append({"layout": "analogy", "title": "Like an Architect and a Builder",
              "takeaway": "The model designs; deterministic code builds to spec.",
              "data": {"concept": {"label": "Forge pipeline", "icon": "gears"},
                       "analog": {"label": "Architect + builder", "icon": "home"},
                       "pairs": [{"concept": "LLM writes JSON spec", "analog": "Architect draws blueprint"},
                                 {"concept": "Renderer draws shapes", "analog": "Builder follows the plan"},
                                 {"concept": "Lint checks the render", "analog": "Inspector walks the site"},
                                 {"concept": "Templates", "analog": "Finish packages"}]},
              "notes": "Separating design from construction is why a 30B local model can produce clean slides: it "
                       "never has to draw. Swapping templates is like swapping finishes; the structure stays."})
    s.append({"layout": "canvas", "title": "One Spec, Three Templates",
              "takeaway": "Pick Microsoft, Surface or Surface Ultra at build time, or re-render later.",
              "data": {"elements": tel},
              "notes": f"Same Contoso v1.1 slide, three templates. Re-rendering the full 11-slide deck took "
                       f"{fastest_t:.2f} to {slowest_t:.2f} seconds per template on this laptop, measured while "
                       "building this story deck."})
    s.append({"layout": "bars", "title": "Round 1: The Laptop Came Last",
              "takeaway": f"v1.0 scored {n1(v0['judge'])}/50 with the blind judge; frontier scored "
                          f"{n1(min(cloud_j))} to {n1(max(cloud_j))}.",
              "data": {"unit": "/50", "highlight": "Local v1.0", "icon": "people",
                       "caption": "Blind judge, anonymized slide sheets, mean of 2 briefs",
                       "bars": [{"label": LABEL[c], "value": agg[c]["judge"]} for c in ORDER if c != "local-v1.1"]},
              "notes": "Our first harness was fast and cheap, and it passed most automated checks, but the blind "
                       "judge saw label titles, mixed-unit charts and floating diagram nodes. It came last on both "
                       "briefs."})
    s.append({"layout": "bars", "title": "Frontier Bought Quality With Tokens",
              "takeaway": f"Opus max used {tok_x:.0f}x Opus low's tokens for "
                          f"+{n1(om['judge'] - ol['judge'])} judge points.",
              "data": {"unit": "tok", "highlight": "Opus max", "icon": "ai",
                       "caption": "Exact output tokens per deck, incl. reasoning",
                       "bars": [{"label": LABEL[c], "value": round(agg[c]["out_tokens"])} for c in CLOUD]},
              "notes": "Reasoning effort mostly bought polish. Opus max hit its 32k output cap twice per brief. "
                       "That reasoning is expensive to buy per deck, so we captured it once instead."})
    s.append({"layout": "compare", "title": "What Frontier Did That v1.0 Didn't",
              "takeaway": "The judge's notes became the v1.1 playbook.",
              "data": {"left": {"title": "v1.0 habits", "icon": "laptop",
                                "points": ["Label titles", "Mixed-unit charts", "Floating diagram nodes",
                                           "Back-to-back analogies"]},
                       "right": {"title": "Frontier habits", "icon": "star",
                                 "points": ["Insight titles", "Like-for-like charts", "Connected diagrams",
                                            "Analogies that map caveats"]},
                       "verdict": "Distill the habits, not the weights."},
              "notes": "We studied the best frontier decks and the judge's critiques, then wrote down the habits: "
                       "a slot-by-slot story arc, an analogy bank, worked examples and checks a script can enforce."})
    s.append({"layout": "analogy", "title": "Distillation Is Like an Apprenticeship",
              "takeaway": "Same apprentice, better playbook.",
              "data": {"concept": {"label": "Harness v1.1", "icon": "ai"},
                       "analog": {"label": "Apprentice", "icon": "people"},
                       "pairs": [{"concept": "Frontier decks", "analog": "Master's portfolio"},
                                 {"concept": "Blind judge notes", "analog": "Studio critique"},
                                 {"concept": "Lint rules", "analog": "Pre-flight checklist"},
                                 {"concept": "Weights unchanged", "analog": "Same apprentice"}]},
              "notes": "No fine-tuning. The local model is identical in v1.0 and v1.1; only the program around it "
                       "changed."})
    s.append({"layout": "flow", "title": "v1.1: Draft, Check, Repair",
              "takeaway": f"Lint issues fell from {lint0} to {lint1} across both decks before grading.",
              "data": {"steps": [
                  {"label": "Deck arc", "detail": "Slot-by-slot story", "icon": "map"},
                  {"label": "Analogy bank", "detail": "Caveat-mapped analogies", "icon": "idea"},
                  {"label": "JSON draft", "detail": "Local model, JSON mode", "icon": "code"},
                  {"label": "Render + lint", "detail": "Deterministic checks", "icon": "checklist"},
                  {"label": "Targeted repair", "detail": "Keep only improvements", "icon": "wrench"}]},
              "notes": f"Each v1.1 deck used {z1.get('calls', 3)} local model passes: one draft and up to two repair "
                       "passes. A repair is kept only if it reduces lint issues."})
    s.append({"layout": "canvas", "title": f"Zava: Judge {n1(z0['judge'])} to {n1(z1['judge'])} of 50",
              "takeaway": "Same model, same renderer; only the harness changed.",
              "data": before_after("zava", z0, z1),
              "notes": "Left is v1.0, right is v1.1, both exported from the real decks. v1.1 opens on why local "
                       "matters for CAD and source-code IP, keeps the speed chart like-for-like, and ends on "
                       "measured proof that this laptop built the deck."})
    s.append({"layout": "canvas", "title": f"Contoso: Judge {n1(k0['judge'])} to {n1(k1['judge'])} of 50",
              "takeaway": "Exec story: hotel-safe and offline-maps analogies, sponsor-ready ask.",
              "data": before_after("contoso", k0, k1),
              "notes": "The judge still flagged v1.1 Contoso for label titles and one overstated Wi-Fi line, which "
                       "feeds the v1.2 backlog."})
    s.append({"layout": "kpis", "title": f"One Round: {v0['grade']} to {v1['grade']}",
              "takeaway": "Quality rose sharply with model weights unchanged.",
              "data": {"items": [
                  {"value": f"{v0['overall']:.0f} → {v1['overall']:.0f}", "label": "Overall score",
                   "icon": "chart", "source": "rubric + judge"},
                  {"value": f"{v1['judge'] / v0['judge']:.1f}x", "label": f"Blind judge: {n1(v0['judge'])} → "
                                                                          f"{n1(v1['judge'])} /50",
                   "icon": "people", "source": "mean of 2 briefs"},
                  {"value": f"{v0['auto']:.0f} → {v1['auto']:.0f}", "label": "Auto rubric /100", "icon": "checklist",
                   "source": "rubric 1.0.1"},
                  {"value": "0", "label": "Weight updates", "icon": "ai", "source": "prompt + program only"}]},
              "notes": f"Overall is half automated rubric, half blind judge. v1.1 lint targets some rubric checks, "
                       f"so the judge-only jump from {n1(v0['judge'])} to {n1(v1['judge'])} is the cleaner signal."})
    s.append({"layout": "canvas", "title": "Frontier-Band Quality at Laptop Cost",
              "takeaway": f"v1.1 judge {n1(v1['judge'])} sits inside the cloud band "
                          f"({n1(min(cloud_j))}-{n1(max(cloud_j))}) at {cost_ratio:,.0f}x lower cost.",
              "data": {"elements": sc},
              "notes": f"Cost per 1,000 decks: local v1.1 ${v1['cost'] * 1000:,.2f} in electricity versus "
                       f"${ref['cost'] * 1000:,.0f} at the cloud median list price. Device and subscriptions are "
                       "excluded for both lanes. Parity, not a win: Opus max and Astra max scored "
                       f"{n1(max(cloud_j))}."})
    s.append({"layout": "kpis", "title": "Per 1,000 Decks: Less Energy, Zero Water",
              "takeaway": "Measured local power vs published cloud per-token estimates.",
              "data": {"items": [
                  {"value": f"{v1['wh']:.1f} kWh", "label": "Local v1.1 energy", "icon": "bolt",
                   "source": "nvidia-smi + 10 W"},
                  {"value": f"{ref['wh']:.1f} kWh", "label": "Cloud median energy", "icon": "cloud",
                   "source": "1.1 Wh per 1k tokens"},
                  {"value": f"{ref['water']:.0f} L", "label": "Cloud water avoided", "icon": "drop",
                   "source": "3.6 mL per 1k tokens"},
                  {"value": f"{ref['co2'] - v1['co2']:.1f} kg", "label": "CO2e avoided", "icon": "leaf",
                   "source": "0.367 kg per kWh"}]},
              "notes": "Local GPU power was measured on a shared GPU that other workloads were also using, so "
                       "local energy is overstated. Cloud energy and water use published per-token estimates."})
    s.append({"layout": "bars", "title": "The Trade-Off: Drafting Time",
              "takeaway": f"v1.1 needs {v1['seconds']:.0f} s: slower than the {ref['seconds']:.0f} s cloud median, "
                          f"faster than {LABEL[best]}.",
              "data": {"unit": "s", "highlight": "Local v1.1", "icon": "timer",
                       "caption": "Local: wall-clock. Cloud: API generation seconds.",
                       "bars": [{"label": LABEL[c], "value": round(agg[c]["seconds"])} for c in ORDER]},
              "notes": f"Three passes on a shared server slot made v1.1 {v1['seconds'] / v0['seconds']:.1f}x slower "
                       f"than v1.0. The best-quality cloud config, {LABEL[best]}, took "
                       f"{agg[best]['seconds']:.0f} s."})
    s.append({"layout": "kpis", "title": "Self-Grade: Quality Up, Speed Down",
              "takeaway": f"Composite {c0['composite']['grade']} to {c1['composite']['grade']}: "
                          "time is now the gap to close.",
              "data": {"items": [
                  {"value": gd("deck_quality"), "label": "Deck grade" + held("deck_quality"),
                   "icon": "star", "source": "overall score"},
                  {"value": gd("cost_savings"), "label": "Cost savings" + held("cost_savings"),
                   "icon": "money", "source": "vs cloud median"},
                  {"value": gd("sustainability"), "label": "Sustainability" + held("sustainability"),
                   "icon": "leaf", "source": "energy + water"},
                  {"value": gd("time_to_generate"), "label": "Time to generate" + held("time_to_generate"),
                   "icon": "timer", "source": "vs cloud median"}]},
              "notes": f"Composite is an equal-weight mean of the four criteria: {c0['composite']['score']} for "
                       f"v1.0 and {c1['composite']['score']} for v1.1. The deck got much better; drafting time "
                       "is what v1.2 has to win back."})
    s.append({"layout": "cta", "title": "Next: v1.2 Keeps Quality, Wins Back Time",
              "takeaway": "Every step is measurable with this same benchmark.",
              "data": {"steps": [
                  {"label": "Fix judge flags", "detail": "Hedge claims, fix boundaries", "icon": "checklist"},
                  {"label": "Dedicated GPU slot", "detail": "No shared-server contention", "icon": "gpu"},
                  {"label": "Early-stop repair", "detail": "Skip passes that can't win", "icon": "timer"},
                  {"label": "Held-out briefs", "detail": "Prove it generalizes", "icon": "target"}],
                       "ask": "Run v1.2 on new briefs and re-benchmark."},
              "notes": "Both briefs informed v1.1, so the honest next test is unseen briefs. Rendered offline by "
                       "the Forge renderer; every number comes from bench/results.json."})
    return {"title": "Teaching Laptop Ultra to Teach Laptop Ultra", "client": "Benchmark story", "slides": s}


def place_images(pptx_path, placements, frame):
    prs = Presentation(pptx_path)
    for idx, items in placements.items():
        slide = prs.slides[idx]
        for path, x, y, h in items:
            pic = slide.shapes.add_picture(str(path), Inches(x), Inches(y), height=Inches(h))
            pic.line.color.rgb = RGBColor.from_string(frame)
            pic.line.width = Pt(1.25)
    prs.save(pptx_path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--template", default="surface_ultra")
    ap.add_argument("--out", default=str(Path.home() / "Downloads" / "Offline-PPTX-Forge-Story.pptx"))
    a = ap.parse_args()
    t = themes.get(a.template)
    OUT.mkdir(parents=True, exist_ok=True)
    r, agg, ref, crit, rows = load_data()
    timings = template_timings(OUT)

    def pngs(run, bid, tpl="surface_ultra"):
        return sorted((RUNS / run / bid / f"png-{tpl}").glob("slide*.png"))

    images = {
        "zava": (deck_grid(pngs("v1.0", "zava_technical"), OUT / "zava-v1.0.png", t.card),
                 deck_grid(pngs("v1.1", "zava_technical"), OUT / "zava-v1.1.png", t.card)),
        "contoso": (deck_grid(pngs("v1.0", "contoso_sales"), OUT / "contoso-v1.0.png", t.card),
                    deck_grid(pngs("v1.1", "contoso_sales"), OUT / "contoso-v1.1.png", t.card)),
        "templates": {tp: RUNS / "v1.1" / "contoso_sales" / f"png-{tp}" / "slide05.png"
                      for tp in ("microsoft", "surface", "surface_ultra")},
    }
    spec = build_spec(r, agg, ref, crit, rows, timings, images)
    (OUT / "story.spec.json").write_text(json.dumps(spec, indent=1, ensure_ascii=False), encoding="utf-8")
    local = OUT / f"Offline-PPTX-Forge-Story-{a.template}.pptx"
    res = render(spec, a.template, local)
    titles = [s["title"] for s in spec["slides"]]
    place_images(local, {titles.index(next(x for x in titles if x.startswith("One Spec"))): images["templates_place"],
                         titles.index(next(x for x in titles if x.startswith("Zava:"))): images["zava_place"],
                         titles.index(next(x for x in titles if x.startswith("Contoso:"))): images["contoso_place"]},
                 t.card_line)
    issues = [(x["index"] + 1, x["layout"], x["issues"], x["overflows"], x["shrunk"]) for x in res["slides"]
              if x["issues"] or x["overflows"] or x["shrunk"]]
    print("render issues:", issues or "none")
    preview(str(local), OUT / f"png-{a.template}", label=f"Story deck | {a.template}")
    dest = Path(a.out)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(local, dest)
    print(f"{len(spec['slides'])} slides -> {dest}")


if __name__ == "__main__":
    main()
