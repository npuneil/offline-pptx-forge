"""Harness v1.1 prompt program, distilled from round 1: frontier decks (Claude Opus 5.5, GPT-6 Astra at
low/high/max) plus the blind judge's feedback on what separated the best decks from the weakest.

What changed vs v1.0 (prompt/program distillation, not weight training):
  * narrative arc per pitch type (slot-by-slot plan with layout + intent); open on the problem
  * insight titles, with caveats turned into claims ("Device Speed Is Not Task Success")
  * fact sheet with IDs and an explicit list of numbers the deck may use
  * analogy bank that maps the caveat, not just the nouns; max two analogy slides, more woven into takeaways
  * exemplar slides incl. a connected device-boundary canvas; like-for-like charts; no invented memory blocks
  * guardrails phrased positively (never mention banned terms, even to deny them)
The harness (not the model) inserts a measured "made on this laptop" slide when the brief asks for it.
"""
import json
import re

from .icons import ICON_NAMES
from .prompts_v1_0 import LAYOUT_CATALOG

VERSION = "1.1"

ARCS = {
    "sales": [
        ("title", "title", "Kicker '<CLIENT> PILOT PROPOSAL'. Title = the business outcome in <= 6 words. Subtitle positions the hybrid lane."),
        ("pain", "kpis", "3-4 sourced numbers that show the audience's problem (people, frequency, minutes, connectivity)."),
        ("big_idea", "analogy", "The hybrid idea in everyday terms: bank A8 (hotel safe + concierge). Title states the idea as a claim."),
        ("position", "compare", "Current lane vs recommended hybrid: keep the existing cloud assistant, add a local lane. Right side wins; verdict = the decision."),
        ("architecture", "canvas", "Device-boundary diagram: client files -> local model -> consultant-reviewed draft inside the laptop; existing cloud lane outside. Every box connected. Follow EXEMPLAR canvas."),
        ("routing", "matrix", "Which work goes where: x_axis 'Repetition', y_axis 'Sensitivity'; highlight the high/high quadrant = local lane; other quadrants keep the existing cloud assistant."),
        ("connectivity", "analogy", "Restricted client Wi-Fi explained with bank A9 (offline maps); the pilot validates disconnected use."),
        ("device", "stack", "The device in plain business terms: drafting workflow -> local models -> on-device runtime -> laptop silicon, one fact each. No speed charts for executives."),
        ("value", "flow", "Capacity chain as 5 steps: people x summaries x minutes saved x weeks = hours; last step says 'estimate to validate'."),
        ("pilot", "timeline", "Pilot plan: before launch / week 1 / week 2 / sponsor decision, with what is measured."),
        ("cta", "cta", "3 steps, each naming who acts (COO, CIO, practice lead) + ask that states the exact pilot size and duration."),
    ],
    "technical": [
        ("title", "title", "Kicker 'TECHNICAL BRIEFING FOR <CLIENT> ENGINEERING'. Title = what is proven, <= 6 words."),
        ("why_local", "compare", "Open on the problem: sensitive IP (CAD/PLM data, source code) vs shared AI services. Left = shared services only, right = local lane + cloud for heaviest work."),
        ("stack", "stack", "Silicon -> runtimes -> model catalog -> developer workflows, each layer with one measured fact."),
        ("memory", "kpis", "Three memory views as 3 KPIs (installed, visible to Windows, GPU budget). Title says they are never summed; takeaway uses bank A10 (map zoom levels)."),
        ("throughput", "bars", "Single-stream decode ONLY (tokens/s): the MoE coder model, the other MoE model, and the dense model; highlight the fastest; caption = source + shared-machine caveat. Title: MoE vs dense insight."),
        ("moe_analogy", "analogy", "Why MoE is fast, with bank A4 (specialist team)."),
        ("codegen_rag", "flow", "Code generation + RAG over internal docs: 5 steps from IDE prompt to developer decision; takeaway uses bank A6 (open-book exam)."),
        ("sizing", "analogy", "Model sizing bands with bank A5 (shop machines); bands are planning estimates, not accuracy tiers."),
        ("routing", "canvas", "Hybrid routing: developer -> routing policy; local lane (code, internal docs) inside a dashed device boundary; cloud lane for heaviest reasoning outside. Every box connected. Takeaway uses bank A3 (make-or-buy)."),
        ("cta", "cta", "3 steps for a 10-developer, 14-day pilot (who joins, what runs, what is measured) + ask with exact size and duration."),
    ],
}

ANALOGY_BANK = [
    {"id": "A8", "use": "hybrid: local lane for sensitive work, cloud assistant for everything else",
     "concept": "Hybrid AI lanes", "analog": "Hotel safe + concierge",
     "pairs": [["Local lane on laptop", "Room safe"], ["Sensitive client files", "Passport and valuables"],
               ["Microsoft 365 Copilot", "Concierge for everything else"], ["Consultant decides", "Guest chooses what goes where"]]},
    {"id": "A9", "use": "working where client Wi-Fi is restricted (validated in pilot, never a guarantee)",
     "concept": "Local AI lane", "analog": "Offline maps",
     "pairs": [["Local model on laptop", "Maps downloaded to phone"], ["Restricted client Wi-Fi", "No signal in the tunnel"],
               ["Copilot when connected", "Live traffic when online"], ["2-week pilot", "Test drive before the trip"]]},
    {"id": "A10", "use": "memory views that must never be added (one-line takeaway, not a slide)",
     "concept": "Memory views", "analog": "Zoom levels on one map",
     "pairs": [["128 GB installed", "Whole region"], ["About 64 GB visible to Windows", "City view"],
               ["64,000 MiB GPU budget", "District view"], ["Never add views", "Don't count streets twice"]]},
    {"id": "A2", "use": "local drafting with human review", "concept": "Local drafting", "analog": "Junior writer + editor",
     "pairs": [["Local model", "Junior writer"], ["Client documents", "Source packet"],
               ["Generated draft", "Working copy"], ["Consultant review", "Editor sign-off"]]},
    {"id": "A3", "use": "hybrid routing local vs cloud (manufacturing audience)", "concept": "Hybrid routing",
     "analog": "Make-or-buy decision",
     "pairs": [["Local lane", "Make in-house"], ["Code and internal docs", "Proprietary parts"],
               ["Cloud reasoning", "Buy from outside foundry"], ["Routing policy", "Make-or-buy rule"]]},
    {"id": "A4", "use": "mixture of experts vs dense", "concept": "Mixture of Experts", "analog": "Specialist team",
     "pairs": [["30B total parameters", "Whole team on the roster"], ["About 3B active per token", "Few specialists per task"],
               ["Gate picks experts", "Lead assigns specialists"], ["Dense: every weight fires", "Everyone in every meeting"]]},
    {"id": "A5", "use": "model sizing bands (size = job size, never accuracy)", "concept": "Model sizing bands",
     "analog": "Shop machine sizes",
     "pairs": [["S: 1-4B", "Benchtop mill"], ["M: 7-8B", "Standard CNC mill"], ["L: 14-20B", "Machining center"],
               ["XL: 24-32B", "Gantry mill"]]},
    {"id": "A6", "use": "retrieval over internal docs (RAG)", "concept": "Retrieval (RAG)", "analog": "Open-book exam",
     "pairs": [["Internal docs index", "Your own textbook"], ["Retrieve passages", "Flip to the right page"],
               ["Grounded prompt", "Answer with the book open"], ["Cited sources", "Show your references"]]},
    {"id": "A7", "use": "single vs concurrent streams", "concept": "Concurrent streams", "analog": "Checkout lanes",
     "pairs": [["Single stream", "One open lane"], ["4 concurrent streams", "Four lanes open"],
               ["Aggregate tokens/s", "Shoppers served per minute"], ["Per-stream speed", "Each cashier's pace"]]},
]

EXEMPLARS = [
    {"layout": "kpis", "title": "Field Notes Pile Up on the Road", "takeaway": "Repeated summaries and patchy Wi-Fi slow every site visit.",
     "data": {"items": [{"value": "800", "label": "Field engineers", "icon": "people", "source": "Fabrikam brief"},
                        {"value": "~4", "label": "Reports per week", "icon": "document", "source": "Fabrikam brief"},
                        {"value": "~40%", "label": "Sites without Wi-Fi", "icon": "wifi", "source": "Fabrikam brief"}]},
     "notes": "Open with their reality: many people, repeated reports, unreliable connectivity."},
    {"layout": "bars", "title": "Speed Is a Signal, Not the Outcome", "takeaway": "Measured decode on this device; the pilot measures task time.",
     "data": {"unit": "tokens/s", "highlight": "Model B, 1 stream", "icon": "speed",
              "caption": "Local-AI-Bench, this device, shared machine",
              "bars": [{"label": "Model A, 1 stream", "value": 40}, {"label": "Model B, 1 stream", "value": 75}]},
     "notes": "All bars share one unit. The callout repeats the highlighted bar."},
    {"layout": "canvas", "title": "Sensitive Work Stays on the Laptop", "takeaway": "Files, prompts and drafts stay inside the device boundary.",
     "data": {"elements": [
         {"type": "pill", "x": 0.2, "y": 0.0, "w": 7.8, "h": 0.55, "label": "Surface Laptop Ultra", "icon": "laptop", "tone": "primary"},
         {"type": "line", "x": 0.2, "y": 0.8, "x2": 8.0, "y2": 0.8, "dashed": True, "tone": "accent2"},
         {"type": "line", "x": 0.2, "y": 5.6, "x2": 8.0, "y2": 5.6, "dashed": True, "tone": "accent2"},
         {"type": "line", "x": 0.2, "y": 0.8, "x2": 0.2, "y2": 5.6, "dashed": True, "tone": "accent2"},
         {"type": "line", "x": 8.0, "y": 0.8, "x2": 8.0, "y2": 5.6, "dashed": True, "tone": "accent2"},
         {"type": "box", "x": 0.5, "y": 1.3, "w": 2.2, "h": 1.0, "label": "Site files", "icon": "document", "tone": "accent2"},
         {"type": "arrow", "x": 2.7, "y": 1.8, "x2": 3.0, "y2": 1.8, "tone": "primary"},
         {"type": "box", "x": 3.0, "y": 1.3, "w": 2.2, "h": 1.0, "label": "Local model", "icon": "ai", "tone": "primary"},
         {"type": "arrow", "x": 5.2, "y": 1.8, "x2": 5.5, "y2": 1.8, "tone": "primary"},
         {"type": "box", "x": 5.5, "y": 1.3, "w": 2.2, "h": 1.0, "label": "Reviewed draft", "icon": "check", "tone": "accent1"},
         {"type": "line", "x": 4.1, "y": 2.3, "x2": 4.1, "y2": 3.3, "tone": "muted"},
         {"type": "box", "x": 3.0, "y": 3.3, "w": 2.2, "h": 0.9, "label": "RTX Spark GPU", "icon": "gpu", "tone": "accent4"},
         {"type": "text", "x": 0.5, "y": 4.7, "w": 7.2, "h": 0.6, "label": "Inside the boundary: files, prompts, drafts", "size": "s", "tone": "muted"},
         {"type": "text", "x": 8.6, "y": 0.0, "w": 3.3, "h": 0.55, "label": "Cloud lane", "size": "m"},
         {"type": "box", "x": 8.6, "y": 1.3, "w": 3.2, "h": 1.0, "label": "Existing cloud assistant", "icon": "cloud", "tone": "accent3"},
         {"type": "box", "x": 8.6, "y": 3.3, "w": 3.2, "h": 0.9, "label": "Everyday work", "icon": "chat", "tone": "card"},
         {"type": "arrow", "x": 10.2, "y": 2.3, "x2": 10.2, "y2": 3.3, "tone": "accent3"}]},
     "notes": "Boundary = four dashed lines; labeled boxes with icons; arrows show the path; the cloud lane sits outside."},
    {"layout": "cta", "title": "Approve a Measured Start", "takeaway": "A small, time-boxed pilot decides the next step.",
     "data": {"steps": [{"label": "Nominate 8 users", "detail": "Field engineers with repeat reports", "icon": "people"},
                        {"label": "Run 3 weeks", "detail": "Alongside current tools", "icon": "calendar"},
                        {"label": "Decide on data", "detail": "Task time and quality readout", "icon": "chart"}],
              "ask": "Approve the 8-user, 3-week pilot."},
     "notes": "Three concrete steps, then one sentence ask with size and duration."},
]

SYSTEM = """\
You are Offline PPTX Forge v1.1, a presentation designer that turns a brief into a JSON slide spec.
A deterministic renderer draws every slide as native infographics, so you choose layouts and write
very short, sharp text. Decks are text-light, visual-first, and explain Local AI with accurate analogies.

RULES
1. Return ONLY one JSON object: {"title":str,"client":str,"slides":[...]}. No markdown, no commentary.
2. Follow the ARC exactly: one slide per slot, in order, using the slot's layout.
3. Titles are insights, not labels: a short claim with a verb, <= 7 words. Turn caveats into claims
   (good: "Device Speed Is Not Task Success", "Authorize a Pilot, Not a Rollout",
   "Three Memory Views, Never Summed"; bad: "Throughput", "Memory Views", "Pilot Ask").
4. Text budget: <= 30 visible words per slide in total. takeaway <= 12 words, labels <= 4 words,
   details <= 7 words, KPI sources <= 4 words. Speaker notes: 2-3 sentences, <= 45 words.
5. Numbers: use ONLY numbers from ALLOWED NUMBERS, copied exactly with their unit. Never invent sizes,
   percentages, prices or counts. Prefer words over numbers when unsure.
6. Charts: a bars chart compares like with like: ONE unit and ONE measurement type for every bar
   (never mix counts, hours, GiB and speed; never mix single-stream and aggregate); every bar value is
   an allowed number; "highlight" is exactly one bar label and is the number the slide is about;
   caption gives source + caveat. Never split memory into parts that add up; show memory views as kpis.
   KPI items carry a short "source".
7. Analogies: the best analogies map the caveat, not just the nouns. Use 4 pairs; each pair maps one
   concrete part of the concept to one concrete part of the analog. Use the ANALOGY BANK (adapt the
   wording to the audience). Exactly two "analogy" slides, never back to back; weave more analogies
   into takeaways with "like" or "think of" (e.g. "Like zoom levels on one map: never add them").
   Never say a token is a word; never call system RAM and GPU memory separate spaces.
8. Canvas: 12-20 elements inside the 12 x 6 grid, no overlapping boxes, every box has a label and icon,
   and every box touches an arrow or line (no floating nodes). Mark the device boundary with four dashed
   lines, as in the EXEMPLAR.
9. Guardrails: state the positive version and never mention a banned term, not even to deny it
   (say "disconnected use validated in the pilot", not "works offline").
10. Icons: use only names from ICONS. Every content slide shows at least 3 icons.
11. Do not add a slide about how this deck was generated; the harness adds a measured one when relevant.

""" + LAYOUT_CATALOG + "\nICONS: " + ", ".join(ICON_NAMES) + "\n"

NUM_TOKEN = re.compile(r"(?<![A-Za-z\d.])~?\d+(?:,\d{3})*(?:\.\d+)?(?:\s?(?:%|GB|GiB|MiB|B\b|s\b|minutes|hours|weeks|days|tokens/s|tokens per second))?")


def allowed_numbers(brief: dict) -> list[str]:
    seen, out = set(), []
    for fact in brief.get("facts") or []:
        for m in NUM_TOKEN.finditer(fact):
            tok = m.group(0).strip()
            if tok not in seen:
                seen.add(tok)
                out.append(tok)
    return out


def arc_for(brief: dict) -> list[tuple]:
    return ARCS.get(str(brief.get("pitch_type", "sales")).lower(), ARCS["sales"])


def user_message(brief: dict) -> str:
    arc = arc_for(brief)
    facts = "\n".join(f"F{i + 1}: {f}" for i, f in enumerate(brief.get("facts") or []))
    arc_txt = "\n".join(f"{i + 1}. [{layout}] {slot}: {intent}" for i, (slot, layout, intent) in enumerate(arc))
    topics = list(brief.get("required_topics") or [])
    topics = [t for t in topics if t != "made_on_device"]
    return (
        f"CLIENT: {brief.get('client')}\nPITCH: {brief.get('pitch_type')}\nAUDIENCE: {brief.get('audience')}\n"
        f"OBJECTIVE: {brief.get('objective')}\nCONTEXT: {brief.get('context')}\n\n"
        f"FACT SHEET\n{facts}\n\nALLOWED NUMBERS: {', '.join(allowed_numbers(brief))} (plus small ordinals 1-10)\n\n"
        f"GUARDRAILS\n- " + "\n- ".join(brief.get("guardrails") or []) + "\n\n"
        f"TOPICS TO COVER ON-SLIDE: {', '.join(topics)}\n\n"
        f"ARC ({len(arc)} slides)\n{arc_txt}\n\n"
        f"ANALOGY BANK\n{json.dumps(ANALOGY_BANK, ensure_ascii=False)}\n\n"
        f"EXEMPLAR SLIDES (fictional Fabrikam; copy the structure, not the content)\n"
        f"{json.dumps(EXEMPLARS, ensure_ascii=False)}\n\n"
        f"Return the JSON deck spec for {brief.get('client')} now ({len(arc)} slides)."
    )


def messages(brief: dict) -> list[dict]:
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_message(brief)}]


REPAIR_SYSTEM = """\
You are the repair pass of Offline PPTX Forge v1.1. You receive a JSON deck spec and a list of lint
issues by slide index (0-based). Fix ONLY the listed slides, keeping their intent and layout unless an
issue says to change it. Apply every RULE from the original instructions (word budget, allowed numbers,
one unit per chart, insight titles, 4-pair analogies, guardrails stated positively).
Return ONLY JSON: {"fixes":[{"index":int,"slide":{...complete replacement slide...}}]}"""


def repair_messages(brief: dict, spec: dict, issues: list[dict]) -> list[dict]:
    by_slide = {}
    for it in issues:
        by_slide.setdefault(it.get("slide", -1), []).append(it["msg"])
    lines = []
    for idx in sorted(by_slide):
        tag = "deck" if idx < 0 else f"slide {idx}"
        lines += [f"- {tag}: {m}" for m in by_slide[idx]]
    body = (f"ALLOWED NUMBERS: {', '.join(allowed_numbers(brief))} (plus small ordinals 1-10)\n"
            f"GUARDRAILS\n- " + "\n- ".join(brief.get("guardrails") or []) + "\n\n"
            f"ANALOGY BANK\n{json.dumps(ANALOGY_BANK, ensure_ascii=False)}\n\n"
            f"ISSUES\n" + "\n".join(lines) + "\n\nSPEC\n" + json.dumps(spec, ensure_ascii=False))
    return [{"role": "system", "content": SYSTEM + "\n\n" + REPAIR_SYSTEM}, {"role": "user", "content": body}]
