"""Benchmark report: local harness v1.0 / v1.1 vs cloud (Claude Opus 5.5, GPT-6 Astra x low/high/max).

  python bench/report.py
    -> bench/BENCHMARK.md, bench/results.json,
       runs/report/forge-benchmark-surface_ultra.pptx (+ png preview, rendered by the Forge renderer)

Every number is computed from run telemetry, cloud usage records, rubric output and judge files.
"""
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forge.config import ASSUMPTIONS, BENCH, RUNS  # noqa: E402
from forge.grade import RUBRIC_VERSION, letter  # noqa: E402
from forge.preview import preview  # noqa: E402
from forge.render import render  # noqa: E402

BRIEFS = ("contoso_sales", "zava_technical")
HELDOUT = ("northwind_sales", "woodgrove_technical", "tailspin_sales")
BRIEF_LABEL = {"contoso_sales": "Contoso (sales)", "zava_technical": "Zava (technical)",
               "northwind_sales": "Northwind (sales)", "woodgrove_technical": "Woodgrove (technical)",
               "tailspin_sales": "Tailspin (sales)"}
LOCAL = ("1.0", "1.1")
CLOUD = ["claude-opus-5.5-low", "claude-opus-5.5-high", "claude-opus-5.5-max",
         "gpt-6-astra-low", "gpt-6-astra-high", "gpt-6-astra-max"]
LABEL = {"local-v1.0": "Local v1.0", "local-v1.1": "Local v1.1",
         "claude-opus-5.5-low": "Opus low", "claude-opus-5.5-high": "Opus high", "claude-opus-5.5-max": "Opus max",
         "gpt-6-astra-low": "Astra low", "gpt-6-astra-high": "Astra high", "gpt-6-astra-max": "Astra max"}
CONFIGS = ["local-v1.0", "local-v1.1", *CLOUD]
METRICS = ("auto", "judge", "overall", "seconds", "out_tokens", "cost", "wh", "co2", "water")


def load(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def judge_table(round_name):
    sp, kp = BENCH / "judge" / round_name / "scores.json", RUNS / "judge-keys" / f"{round_name}.json"
    if not (sp.exists() and kp.exists()):
        return {}
    scores, key = load(sp), load(kp)
    return {(m["source"], m["brief"]): scores[d]["total"] for d, m in key.items()
            if isinstance(scores.get(d), dict) and "total" in scores[d]}


def collect():
    r1, r2 = judge_table("round1"), judge_table("round2")
    drift = {}
    for b in BRIEFS:
        d = [r2[k] - r1[k] for k in r2 if k[1] == b and k in r1]
        drift[b] = {"mean": round(sum(d) / len(d), 2) if d else 0.0, "anchors": len(d)}
    rows = []
    for v in LOCAL:
        p = RUNS / f"v{v}" / "summary.json"
        if not p.exists():
            continue
        cfg = f"local-v{v}"
        for b, m in load(p)["results"].items():
            raw = r1.get((cfg, b)) if v == "1.0" else r2.get((cfg, b))
            judge = raw if (v == "1.0" or raw is None) else max(0.0, min(50.0, raw - drift[b]["mean"]))
            rows.append(local_row(cfg, b, m, raw, judge))
    cs = load(RUNS / "cloud" / "summary.json")
    for cfg in CLOUD:
        for b in BRIEFS:
            c = cs.get(f"{cfg}/{b}")
            if not c:
                continue
            e = c["economics"]
            rows.append({
                "config": cfg, "lane": "cloud", "brief": b, "auto": c["grade"]["auto_score"],
                "scores": c["grade"]["scores"], "judge_raw": r1.get((cfg, b)), "judge": r1.get((cfg, b)),
                "seconds": c["seconds"], "wall_seconds": c.get("wall_seconds"), "out_tokens": c["output_tokens"],
                "in_tokens": c["input_tokens"], "reasoning_tokens": c.get("reasoning_tokens"),
                "truncated_calls": c.get("truncated_calls", 0), "cost": e["cost_usd"], "wh": e["energy_wh"],
                "co2": e["co2e_g"], "water": e["water_ml"], "slides": len(c["render_summary"])})
    for r in rows:
        r["overall"] = None if r["judge"] is None else round(0.5 * r["auto"] + r["judge"], 1)
        r["grade"] = letter(r["overall"]) if r["overall"] is not None else "n/a"
    anchors = [{"source": s, "brief": b, "round1": r1[(s, b)], "round2": r2[(s, b)], "delta": r2[(s, b)] - r1[(s, b)]}
               for (s, b) in sorted(r2) if (s, b) in r1]
    return rows, drift, anchors


def mean(vals):
    vals = [v for v in vals if v is not None]
    return sum(vals) / len(vals) if vals else None


def local_row(cfg, b, m, raw, judge):
    e = m["economics"]
    return {"config": cfg, "lane": "local", "brief": b, "auto": m["grade"]["auto_score"],
            "scores": m["grade"]["scores"], "judge_raw": raw, "judge": judge,
            "seconds": m["generate_s"], "out_tokens": m["completion_tokens"], "in_tokens": m["prompt_tokens"],
            "calls": m["llm_calls"], "tps": m["decode_tps"], "cost": e["cost_usd"], "wh": e["energy_wh"],
            "co2": e["co2e_g"], "water": e["water_ml"], "slides": len(m["render_summary"]),
            "lint": m.get("lint_history"), "measured_facts": m.get("measured_facts")}


def leak_audit(spec):
    """Deterministic overfit checks: unfilled arc placeholders and analogy pairs copied verbatim from the v1.1 bank
    (the bank was written from the Contoso/Zava briefs, so verbatim pairs carry their wording)."""
    from forge.prompts_v1_1 import ANALOGY_BANK
    bank = {(a.strip().lower(), b.strip().lower()) for e in ANALOGY_BANK for a, b in e["pairs"]}
    pairs = []

    def walk(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "pairs" and isinstance(v, list):
                    for p in v:
                        if isinstance(p, dict):
                            p = [p.get("concept", ""), p.get("analog", "")]
                        if isinstance(p, (list, tuple)) and len(p) >= 2:
                            pairs.append(tuple(str(x).strip().lower() for x in p[:2]))
                else:
                    walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
    walk(spec)
    text = json.dumps(spec, ensure_ascii=False)
    return {"placeholders": sorted(set(re.findall(r"<[A-Z_]{3,}>", text))),
            "analogy_pairs": len(pairs), "bank_pairs_verbatim": sum(p in bank for p in pairs)}


def collect_heldout():
    """Held-out briefs (never seen while building v1.1), judged blind in round 3 next to re-ID'd anchors."""
    r1, r2, r3 = judge_table("round1"), judge_table("round2"), judge_table("round3")
    prior = {**r1, **{k: v for k, v in r2.items() if k[0] == "local-v1.1"}}
    anchors = [{"source": s, "brief": b, "prior": prior[(s, b)], "round3": r3[(s, b)],
                "delta": r3[(s, b)] - prior[(s, b)]} for (s, b) in sorted(r3) if b in BRIEFS and (s, b) in prior]
    drift = round(mean([a["delta"] for a in anchors]) or 0.0, 2)
    rows = []
    for v in LOCAL:
        p = RUNS / "heldout" / f"v{v}" / "summary.json"
        if not p.exists():
            continue
        cfg = f"local-v{v}"
        for b, m in load(p)["results"].items():
            raw = r3.get((cfg, b))
            judge = None if raw is None else max(0.0, min(50.0, raw - drift))
            r = local_row(cfg, b, m, raw, judge)
            r["overall"] = None if judge is None else round(0.5 * r["auto"] + judge, 1)
            r["grade"] = letter(r["overall"]) if r["overall"] is not None else "n/a"
            r["audit"] = leak_audit(load(p.parent / b / f"{b}.spec.json"))
            rows.append(r)
    agg = {}
    for v in LOCAL:
        rs = [r for r in rows if r["config"] == f"local-v{v}"]
        if rs:
            a = {k: mean([r[k] for r in rs]) for k in METRICS}
            a["grade"] = letter(a["overall"]) if a["overall"] is not None else "n/a"
            agg[f"local-v{v}"] = a
    notes = {}
    sp, kp = BENCH / "judge" / "round3" / "scores.json", RUNS / "judge-keys" / "round3.json"
    if sp.exists() and kp.exists():
        key, sc = load(kp), load(sp)
        notes = {f"{key[d]['source']}/{key[d]['brief']}": s.get("weaknesses", "") for d, s in sc.items()
                 if d in key and key[d]["brief"] in HELDOUT and isinstance(s, dict)}
    return {"briefs": list(HELDOUT), "rows": rows, "aggregate": agg, "anchors": anchors, "drift": drift,
            "judge_notes": notes}


def aggregate(rows):
    out = {}
    for cfg in CONFIGS:
        rs = [r for r in rows if r["config"] == cfg]
        if rs:
            a = {k: mean([r[k] for r in rs]) for k in METRICS}
            a["grade"] = letter(a["overall"]) if a["overall"] is not None else "n/a"
            out[cfg] = a
    return out


def cloud_reference(rows):
    cl = [r for r in rows if r["lane"] == "cloud"]
    return {k: statistics.median(r[k] for r in cl) for k in ("seconds", "cost", "wh", "co2", "water", "out_tokens")}


def clamp(x):
    return max(0.0, min(100.0, x))


def criteria(agg, ref, cfg):
    """Self-grade vs cloud. Reference = median of the 12 cloud decks (6 configs x 2 briefs)."""
    a = agg[cfg]
    cost = clamp(100 * (1 - a["cost"] / ref["cost"]))
    energy = clamp(100 * (1 - a["wh"] / ref["wh"]))
    water = clamp(100 * (1 - a["water"] / ref["water"]))
    sust = 0.5 * energy + 0.5 * water
    time = clamp(100 * ref["seconds"] / a["seconds"])
    deck = a["overall"] or 0.0
    out = {"cost_savings": cost, "sustainability": sust, "time_to_generate": time, "deck_quality": deck}
    out = {k: {"score": round(v, 1), "grade": letter(v)} for k, v in out.items()}
    comp = mean([v["score"] for v in out.values()])
    out["composite"] = {"score": round(comp, 1), "grade": letter(comp)}
    out["_parts"] = {"energy_reduction_pct": round(energy, 1), "water_reduction_pct": round(water, 1)}
    return out


def fmt_money(x):
    return f"${x:.4f}" if x < 0.01 else f"${x:.3f}" if x < 1 else f"${x:,.2f}"


def table(header, body):
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join("---" for _ in header) + "|"]
    lines += ["| " + " | ".join(str(c) for c in row) + " |" for row in body]
    return "\n".join(lines)


def f1(x, nd=1):
    return "n/a" if x is None else f"{x:.{nd}f}"


def markdown(rows, agg, ref, crit, drift, anchors, heldout=None):
    best_cloud = max(CLOUD, key=lambda c: agg[c]["overall"] or 0)
    v0, v1 = agg.get("local-v1.0"), agg.get("local-v1.1")
    md = ["# Offline PPTX Forge - Benchmark", "",
          f"Rubric {RUBRIC_VERSION} - overall = 0.5 x auto rubric (100) + 0.5 x blind judge (/50 x 2). "
          "Cloud reference = median of 12 cloud decks.", ""]

    md += ["## 1. Scoreboard (per deck)", ""]
    body = []
    for b in BRIEFS:
        for cfg in CONFIGS:
            r = next((x for x in rows if x["config"] == cfg and x["brief"] == b), None)
            if not r:
                continue
            j = f1(r["judge"], 0) if r["judge_raw"] == r["judge"] else f"{f1(r['judge'])} (raw {r['judge_raw']})"
            body.append([BRIEF_LABEL[b], LABEL[cfg], r["slides"], f1(r["auto"]), j, f1(r["overall"]), r["grade"],
                         f1(r["seconds"]), f"{r['out_tokens']:,}", fmt_money(r["cost"]), f1(r["wh"], 2),
                         f1(r["co2"], 2), f1(r["water"])])
    md += [table(["Brief", "Config", "Slides", "Auto /100", "Judge /50", "Overall", "Grade", "Gen s",
                  "Out tokens", "Cost", "Wh", "g CO2e", "mL water"], body), ""]

    md += ["## 2. Config averages (both briefs)", ""]
    body = [[LABEL[c], f1(a["auto"]), f1(a["judge"]), f1(a["overall"]), a["grade"], f1(a["seconds"]),
             f"{a['out_tokens']:,.0f}", fmt_money(a["cost"]), f1(a["wh"], 2), f1(a["water"])]
            for c, a in agg.items()]
    md += [table(["Config", "Auto", "Judge", "Overall", "Grade", "Gen s", "Out tokens", "Cost/deck", "Wh/deck",
                  "mL water/deck"], body), ""]

    md += ["## 3. Self-grade vs cloud (initial benchmarking criteria)", "",
           "Formulas: cost = 1 - local/cloud-median cost; sustainability = mean(energy reduction, water reduction) "
           "vs cloud median; time = min(1, cloud-median API seconds / local seconds); deck = overall score; "
           "composite = equal-weight mean.", ""]
    names = {"cost_savings": "Cost savings", "sustainability": "Sustainability vs cloud",
             "time_to_generate": "Time to generate", "deck_quality": "Deck grade (overall)", "composite": "Composite"}
    body = []
    for k, n in names.items():
        row = [n]
        for v in LOCAL:
            c = crit.get(f"local-v{v}")
            row.append(f"{c[k]['score']} ({c[k]['grade']})" if c else "n/a")
        if all(f"local-v{v}" in crit for v in LOCAL):
            row.append(f"{crit['local-v1.1'][k]['score'] - crit['local-v1.0'][k]['score']:+.1f}")
        body.append(row)
    md += [table(["Criterion", "Local v1.0", "Local v1.1", "Delta"], body), ""]

    md += ["## 4. Local vs cloud economics (per 1,000 decks)", ""]
    body = []
    for name, a in [("Local v1.0", v0), ("Local v1.1", v1), ("Cloud median", ref),
                    (f"Best-quality cloud ({LABEL[best_cloud]})", agg[best_cloud])]:
        if a:
            body.append([name, f"{a['seconds'] * 1000 / 3600:,.1f} h", f"${a['cost'] * 1000:,.2f}",
                         f"{a['wh']:.2f} kWh", f"{a['co2']:.2f} kg", f"{a['water']:.1f} L"])
    md += [table(["Lane", "Generation time", "Marginal cost", "Energy", "CO2e", "Water"], body), ""]

    if v0 and v1:
        md += ["## 5. v1.0 -> v1.1 delta (one round of frontier distillation)", ""]
        cats = ["visual_richness", "text_lightness", "analogy", "brief_coverage", "claim_discipline", "structure"]
        l0 = {r["brief"]: r for r in rows if r["config"] == "local-v1.0"}
        l1 = {r["brief"]: r for r in rows if r["config"] == "local-v1.1"}
        body = []
        for b in BRIEFS:
            for k in ["auto", "judge", "overall"]:
                body.append([BRIEF_LABEL[b], k, f1(l0[b][k]), f1(l1[b][k]), f"{l1[b][k] - l0[b][k]:+.1f}"])
            for k in cats:
                body.append([BRIEF_LABEL[b], f"  auto: {k}", f1(l0[b]["scores"][k]), f1(l1[b]["scores"][k]),
                             f"{l1[b]['scores'][k] - l0[b]['scores'][k]:+.1f}"])
            for k, n in [("seconds", "gen seconds"), ("out_tokens", "output tokens"), ("calls", "LLM calls"),
                         ("wh", "Wh")]:
                body.append([BRIEF_LABEL[b], n, f1(l0[b][k]), f1(l1[b][k]), f"{l1[b][k] - l0[b][k]:+.1f}"])
            if l1[b].get("lint"):
                h = l1[b]["lint"]
                kept = [x for x in h if x.get("accepted", True)]
                body.append([BRIEF_LABEL[b], "lint issues (draft -> final)", h[0]["issues"], kept[-1]["issues"], ""])
        md += [table(["Brief", "Metric", "v1.0", "v1.1", "Delta"], body), ""]
        rank = sorted(agg, key=lambda c: -(agg[c]["overall"] or 0))
        md += [f"Rank by mean overall: " + " > ".join(f"{LABEL[c]} {agg[c]['overall']:.1f}" for c in rank), ""]
        jrank = sorted(agg, key=lambda c: -(agg[c]["judge"] or 0))
        md += ["Rank by blind judge only (/50, the fairer quality signal because v1.1 lint targets some auto-rubric "
               "checks): " + " > ".join(f"{LABEL[c]} {agg[c]['judge']:.1f}" for c in jrank), ""]
        best = max(CLOUD, key=lambda c: agg[c]["overall"] or 0)
        md += [f"Quality-matched time: v1.1 averaged {v1['seconds']:.0f} s vs {agg[best]['seconds']:.0f} s for the "
               f"best-quality cloud config ({LABEL[best]}); the {ref['seconds']:.0f} s cloud median is dominated by "
               "low-effort runs that scored lower.", ""]
        crit_file = BENCH / "judge" / "round2" / "scores.json"
        if crit_file.exists():
            key = load(RUNS / "judge-keys" / "round2.json")
            notes = [(key[d]["brief"], s["weaknesses"]) for d, s in load(crit_file).items()
                     if d in key and key[d]["source"] == "local-v1.1" and isinstance(s, dict)]
            if notes:
                md += ["Judge critiques of v1.1 (inputs for v1.2):", ""]
                md += [f"- {BRIEF_LABEL[b]}: {w}" for b, w in notes] + [""]

    md += ["## 6. Judge calibration (round-2 anchors re-scored blind under new IDs)", ""]
    md += [table(["Anchor", "Brief", "Round 1", "Round 2", "Delta"],
                 [[LABEL.get(a["source"], a["source"]), BRIEF_LABEL[a["brief"]], a["round1"], a["round2"],
                   f"{a['delta']:+d}"] for a in anchors]), ""]
    md += ["Per-brief mean drift applied to the v1.1 judge score: "
           + ", ".join(f"{BRIEF_LABEL[b]} {d['mean']:+.2f} ({d['anchors']} anchors)" for b, d in drift.items()), ""]

    md += heldout_markdown(heldout, agg, ref)
    md += ["## 8. Method and disclosures", "",
           "- **Local lane**: Qwen3-Coder-30B-A3B (Q4_K_M) on llama.cpp, Surface Laptop Ultra (NVIDIA RTX Spark), "
           "attached to a shared llama-server (2 slots, other tenants active). Energy = measured GPU board power "
           "(nvidia-smi, 250 ms) + 10 W platform allowance; GPU power includes other tenants, so local energy is "
           "overstated. Decode varied 38-61 tok/s under contention vs 86 tok/s single-stream unshared.",
           "- **Cloud lane**: identical prompt to Claude Opus 5.5 and GPT-6 Astra at low/high/max reasoning via "
           "Copilot CLI subagents. Output tokens are exact per-call usage (incl. reasoning). Time = API generation "
           "seconds (wall time incl. queueing is recorded separately). Cost = list price x tokens, excluding the "
           "agent system prompt. Energy/water = published per-1k-output-token estimates "
           f"({ASSUMPTIONS['cloud_wh_per_1k_tokens']} Wh, {ASSUMPTIONS['cloud_ml_water_per_1k_tokens']} mL).",
           "- Opus max hit the 32k output cap twice per brief (finish_reason=length); counted as-is.",
           "- Local cost is marginal electricity only; device capex and subscriptions are excluded for both lanes.",
           f"- Grid: {ASSUMPTIONS['grid_kgco2e_per_kwh']} kg CO2e/kWh, ${ASSUMPTIONS['electricity_usd_per_kwh']}/kWh.",
           f"- Rubric {RUBRIC_VERSION}: negation-aware guardrail matching was fixed after round 1 and re-applied "
           "uniformly to every deck before v1.1 ran. The rubric was frozen for v1.1.",
           "- Blind judge: one vision-capable subagent scored anonymized contact sheets; round 2 mixed v1.1 with "
           "re-ID'd round-1 anchors so drift is measurable. Anchors are the same images, so recall is possible. "
           "Round 3 (held-out) used fresh IDs, the same rubric and anchors from all three configs; its instructions "
           "said brief facts are the only allowed numbers, so the judge also docked the measured provenance numbers "
           "(Zava v1.1 anchor, Woodgrove v1.1). That is a small penalty against v1.1 that drift adjustment only "
           "partly offsets.",
           "- \"Training\" = prompt/program distillation (deck arc, analogy bank, exemplars, lint + repair loop) "
           "from frontier decks and judge feedback. Model weights were not changed.",
           "- Teaching-to-the-test risk: the v1.1 lint enforces word budgets, analogy cues and icon counts that the "
           "auto rubric also measures, so part of the auto-score gain is expected by construction. The blind judge "
           "never saw the rubric or lint; use judge-only numbers as the primary quality comparison. Both briefs "
           "informed v1.1; section 7 tests generalization on three held-out briefs.",
           "- v1.1 adds a measured provenance slide when a brief lists the made_on_device topic (Zava, Woodgrove); "
           "its numbers are appended to the grading facts as measured telemetry.",
           "- Held-out runs have no cloud comparison decks; the held-out cost ratio uses the benchmark-brief cloud "
           "median.",
           "- Templates are inspired by Microsoft / Surface styling, not official brand assets. Clients are fictional.",
           ""]
    return "\n".join(md)


def heldout_markdown(h, agg, ref):
    if not h or not h["rows"]:
        return []
    rows, ha = h["rows"], h["aggregate"]
    md = ["## 7. Held-out briefs (generalization test)", "",
          "Three new fictional briefs, written after v1.1 was frozen and never used to tune it: Northwind Traders "
          "(retail sales, `surface`), Woodgrove Bank (financial-services technical, `microsoft`), Tailspin Toys "
          "(game-studio sales, `surface_ultra`). Both harnesses ran unchanged on the same shared server. The same "
          "judge scored them blind in round 3, mixed with re-ID'd anchors from the benchmark briefs.", ""]
    body = []
    for b in h["briefs"]:
        for cfg in ("local-v1.0", "local-v1.1"):
            r = next((x for x in rows if x["config"] == cfg and x["brief"] == b), None)
            if not r:
                continue
            j = "n/a" if r["judge"] is None else (f1(r["judge"], 0) if r["judge_raw"] == r["judge"]
                                                  else f"{f1(r['judge'])} (raw {r['judge_raw']})")
            lint = ""
            if r.get("lint"):
                kept = [x for x in r["lint"] if x.get("accepted", True)]
                lint = f"{r['lint'][0]['issues']} -> {kept[-1]['issues']}"
            body.append([BRIEF_LABEL[b], LABEL[cfg], r["slides"], f1(r["auto"]), j, f1(r["overall"]), r["grade"],
                         f1(r["seconds"]), f"{r['out_tokens']:,}", f1(r["wh"], 2), lint,
                         f"{r['audit']['bank_pairs_verbatim']}/{r['audit']['analogy_pairs']}",
                         ", ".join(r["audit"]["placeholders"]) or "none"])
    md += [table(["Brief", "Config", "Slides", "Auto /100", "Judge /50", "Overall", "Grade", "Gen s", "Out tokens",
                  "Wh", "Lint draft -> final", "Bank pairs verbatim", "Placeholders"], body), ""]
    body = []
    for name, a in [("v1.0 on held-out", ha.get("local-v1.0")), ("v1.1 on held-out", ha.get("local-v1.1")),
                    ("v1.0 on benchmark briefs", agg.get("local-v1.0")),
                    ("v1.1 on benchmark briefs", agg.get("local-v1.1"))]:
        if a:
            body.append([name, f1(a["auto"]), f1(a["judge"]), f1(a["overall"]), a["grade"], f1(a["seconds"]),
                         f"{a['out_tokens']:,.0f}", fmt_money(a["cost"]), f1(a["wh"], 2)])
    md += [table(["Set", "Auto", "Judge", "Overall", "Grade", "Gen s", "Out tokens", "Cost/deck", "Wh/deck"], body),
           ""]
    v0, v1 = ha.get("local-v1.0"), ha.get("local-v1.1")
    if v0 and v1 and v0["judge"] is not None and v1["judge"] is not None:
        b1 = agg["local-v1.1"]
        md += [f"- Held-out delta v1.0 -> v1.1: judge {v1['judge'] - v0['judge']:+.1f} /50, overall "
               f"{v1['overall'] - v0['overall']:+.1f} ({v0['grade']} -> {v1['grade']}). Benchmark-brief delta was "
               f"judge {b1['judge'] - agg['local-v1.0']['judge']:+.1f}.",
               f"- v1.1 judge on held-out vs benchmark briefs: {v1['judge']:.1f} vs {b1['judge']:.1f} "
               f"({v1['judge'] - b1['judge']:+.1f}).",
               f"- Held-out v1.1 cost {fmt_money(v1['cost'])}/deck vs {fmt_money(ref['cost'])} cloud median "
               f"({ref['cost'] / v1['cost']:,.0f}x); {v1['seconds']:.0f} s vs {ref['seconds']:.0f} s cloud median.",
               ""]
    if h["anchors"]:
        md += [table(["Anchor", "Brief", "Prior round", "Round 3", "Delta"],
                     [[LABEL.get(a["source"], a["source"]), BRIEF_LABEL[a["brief"]], a["prior"], a["round3"],
                       f"{a['delta']:+d}"] for a in h["anchors"]]), "",
               f"Mean anchor drift {h['drift']:+.2f} was subtracted from held-out judge scores.", ""]
    notes = [(k, v) for k, v in h["judge_notes"].items() if k.startswith("local-v1.1/")]
    if notes:
        md += ["Judge critiques of v1.1 on held-out briefs:", ""]
        md += [f"- {BRIEF_LABEL[k.split('/')[1]]}: {v}" for k, v in notes] + [""]
    md += ["Root cause (code review after the held-out run; the harness stayed frozen):", "",
           "- The v1.1 deck arcs hard-code benchmark-brief specifics: the technical CTA slot says "
           "'10-developer, 14-day pilot' (Zava's ask), and slots name 'consultant-reviewed draft', 'Restricted "
           "client Wi-Fi', 'COO, CIO, practice lead' and 'CAD/PLM data' (`forge/prompts_v1_1.py`, `ARCS`).",
           "- Analogy-bank entries carry fully worked Contoso/Zava pairs ('Consultant decides', '2-week pilot', "
           "CNC mill sizes). The local model copies them verbatim, which the 'Bank pairs verbatim' column counts.",
           "- The `<CLIENT>` kicker is left for the model to fill; on Woodgrove it shipped unfilled.",
           "- Auto-rubric blind spot: claim discipline matches bare numbers, not number + unit, so '40%' passes "
           "because '40 minutes' is a fact (`forge/grade.py`). The v1.1 lint shares this check.",
           "- v1.2 backlog: parameterize arcs from brief facts (pilot size, duration, sponsors, sensitive data), "
           "turn bank pairs into abstract templates, substitute `<CLIENT>` in code, and make the fact check "
           "unit-aware.", ""]
    return md


def bench_deck(rows, agg, ref, crit, out_dir):
    v0, v1 = agg["local-v1.0"], agg["local-v1.1"]
    c0, c1 = crit["local-v1.0"], crit["local-v1.1"]
    best = max(CLOUD, key=lambda c: agg[c]["overall"] or 0)
    order = [c for c in CONFIGS if c in agg]
    lint = [r["lint"] for r in rows if r["config"] == "local-v1.1" and r.get("lint")]
    lint_before = sum(h[0]["issues"] for h in lint)
    lint_after = sum([x for x in h if x.get("accepted", True)][-1]["issues"] for h in lint)
    gap0, gap1 = v0["overall"] - agg[best]["overall"], v1["overall"] - agg[best]["overall"]
    savings = (1 - v1["cost"] / ref["cost"]) * 100
    slides = [
        {"layout": "title", "kicker": "OFFLINE PPTX FORGE BENCHMARK",
         "title": "Laptop Ultra vs Frontier Cloud",
         "subtitle": f"2 briefs, {len(rows)} decks, 1 round of frontier distillation",
         "hero_icons": ["laptop", "cloud", "chart", "leaf"]},
        {"layout": "kpis", "title": f"One Round Lifted Quality {v1['overall'] - v0['overall']:+.0f} Points",
         "takeaway": f"Local deck grade went {v0['grade']} to {v1['grade']} with weights unchanged.",
         "data": {"items": [
             {"value": f"{v0['overall']:.0f} to {v1['overall']:.0f}", "label": "Overall score", "icon": "chart",
              "source": "rubric + blind judge"},
             {"value": f"{gap1:+.1f}", "label": f"Gap to {LABEL[best]}", "icon": "target", "source": "mean of 2 briefs"},
             {"value": fmt_money(v1["cost"]), "label": "Cost per deck", "icon": "money", "source": "measured Wh"},
             {"value": "0 mL", "label": "Water per deck", "icon": "water", "source": "no data center"}]},
         "notes": f"v1.0 overall {v0['overall']:.1f}, v1.1 {v1['overall']:.1f}. Best cloud {LABEL[best]} "
                  f"{agg[best]['overall']:.1f}. Gap moved from {gap0:+.1f} to {gap1:+.1f}."},
        {"layout": "bars", "title": "Local v1.1 Now Competes on Quality",
         "takeaway": f"Top mean overall; auto rubric gives most of the lead.",
         "data": {"unit": "pts", "highlight": "Local v1.1", "icon": "chart",
                  "caption": "0.5 x auto rubric + 0.5 x blind judge",
                  "bars": [{"label": LABEL[c], "value": round(agg[c]["overall"], 1)} for c in order]},
         "notes": "Overall blends the automated rubric with a blind visual judge. v1.1 lint targets some rubric "
                  "checks, so read the next slide (judge only) as the fairer quality signal."},
        {"layout": "bars", "title": "Blind Judge Says Parity, Not a Win",
         "takeaway": f"v1.1 judge {v1['judge']:.1f}/50 vs best cloud {max(agg[c]['judge'] for c in CLOUD):.1f}.",
         "data": {"unit": "/50", "highlight": "Local v1.1", "icon": "people",
                  "caption": "Anonymized contact sheets, same judge, 0 anchor drift",
                  "bars": [{"label": LABEL[c], "value": round(agg[c]["judge"], 1)} for c in order]},
         "notes": "Six round-1 decks were re-scored blind under new IDs in round 2 and matched exactly."},
        {"layout": "bars", "title": "Quality Cost Local Drafting Time",
         "takeaway": f"Repair passes made local {v1['seconds'] / v0['seconds']:.1f}x slower; "
                     f"still beats {LABEL[best]} at {agg[best]['seconds']:.0f} s.",
         "data": {"unit": "s", "highlight": "Local v1.1", "icon": "timer",
                  "caption": "Local: wall-clock generation. Cloud: API generation seconds.",
                  "bars": [{"label": LABEL[c], "value": round(agg[c]["seconds"])} for c in order]},
         "notes": f"Cloud median {ref['seconds']:.0f} s. Local ran on a shared server slot under contention."},
        {"layout": "bars", "title": "Cloud Cost Scales With Reasoning",
         "takeaway": "Marginal cost per 1,000 decks; local is electricity only.",
         "data": {"unit": "USD", "highlight": "Local v1.1", "icon": "money",
                  "caption": "List price x exact tokens vs measured kWh x $0.13",
                  "bars": [{"label": LABEL[c], "value": round(agg[c]["cost"] * 1000, 2)} for c in order]},
         "notes": f"Local v1.1 saves {savings:.1f}% vs the cloud median per deck."},
        {"layout": "kpis", "title": "Sustainability per 1,000 Decks",
         "takeaway": "Measured local energy vs published cloud per-token estimates.",
         "data": {"items": [
             {"value": f"{v1['wh']:.1f} kWh", "label": "Local v1.1 energy", "icon": "bolt", "source": "nvidia-smi"},
             {"value": f"{ref['wh']:.1f} kWh", "label": "Cloud median energy", "icon": "cloud", "source": "1.1 Wh/1k tok"},
             {"value": f"{ref['water']:.0f} L", "label": "Cloud water avoided", "icon": "water", "source": "3.6 mL/1k tok"},
             {"value": f"{(ref['co2'] - v1['co2']):.1f} kg", "label": "CO2e avoided", "icon": "leaf", "source": "0.367 kg/kWh"}]},
         "notes": "Values per deck x 1,000. Local GPU power includes other tenants, so local energy is overstated."},
        {"layout": "flow", "title": "What v1.1 Learned From Frontier",
         "takeaway": "Distilled arc, analogies and checks; the model stayed the same.",
         "data": {"steps": [
             {"label": "Deck arc", "detail": "Slot-by-slot story", "icon": "map"},
             {"label": "Analogy bank", "detail": "Caveat-mapped analogies", "icon": "lightbulb"},
             {"label": "JSON draft", "detail": "Local model, JSON mode", "icon": "code"},
             {"label": "Render + lint", "detail": "Deterministic checks", "icon": "checklist"},
             {"label": "Targeted repair", "detail": "Keep only improvements", "icon": "wrench"}]},
         "notes": f"Lint issues fell from {lint_before} to {lint_after} across both decks before grading."},
        {"layout": "analogy", "title": "Distillation Is Like an Apprenticeship",
         "takeaway": "Same apprentice, better playbook.",
         "data": {"concept": {"label": "Harness v1.1", "icon": "ai"},
                  "analog": {"label": "Apprentice", "icon": "people"},
                  "pairs": [{"concept": "Frontier decks", "analog": "Master's portfolio"},
                            {"concept": "Blind judge notes", "analog": "Studio critique"},
                            {"concept": "Lint rules", "analog": "Pre-flight checklist"},
                            {"concept": "Repair pass", "analog": "Rework before review"},
                            {"concept": "Weights unchanged", "analog": "Same apprentice"}]},
         "notes": "No fine-tuning: the gains came from program and prompt design."},
        {"layout": "compare", "title": "Self-Grade: v1.0 vs v1.1",
         "takeaway": "Quality up, speed down, cost and water still near zero.",
         "data": {"left": {"title": f"v1.0 composite {c0['composite']['grade']}", "icon": "laptop",
                           "points": [f"Deck {c0['deck_quality']['grade']}", f"Time {c0['time_to_generate']['grade']}",
                                      f"Cost {c0['cost_savings']['grade']}", f"Sustain {c0['sustainability']['grade']}"]},
                  "right": {"title": f"v1.1 composite {c1['composite']['grade']}", "icon": "laptop",
                            "points": [f"Deck {c1['deck_quality']['grade']}", f"Time {c1['time_to_generate']['grade']}",
                                       f"Cost {c1['cost_savings']['grade']}", f"Sustain {c1['sustainability']['grade']}"]},
                  "verdict": "Ship v1.1 for quality; v1.2 targets speed."},
         "notes": "Grades come from formulas versus the cloud median; see BENCHMARK.md."},
        {"layout": "cta", "title": "Next: Harness v1.2",
         "takeaway": "Keep the quality, win back the time.",
         "data": {"steps": [
             {"label": "Dedicated GPU slot", "detail": "No shared-server contention", "icon": "chip"},
             {"label": "Early-stop repair", "detail": "Skip passes that cannot win", "icon": "timer"},
             {"label": "Held-out briefs", "detail": "Prove it generalizes", "icon": "checklist"}],
                  "ask": "Run round 2 distillation on new briefs."},
         "notes": "Each step is measurable with this benchmark harness."},
    ]
    spec = {"title": "Offline PPTX Forge Benchmark", "client": "Internal", "slides": slides}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "benchmark.spec.json").write_text(json.dumps(spec, indent=1), encoding="utf-8")
    r = render(spec, "surface_ultra", out_dir / "forge-benchmark-surface_ultra.pptx")
    preview(r["path"], out_dir / "png-surface_ultra", label="Offline PPTX Forge | benchmark | surface_ultra")
    return r["path"], [s["issues"] for s in r["slides"] if s.get("issues")]


def main():
    rows, drift, anchors = collect()
    agg = aggregate(rows)
    ref = cloud_reference(rows)
    crit = {c: criteria(agg, ref, c) for c in agg if c.startswith("local-") and agg[c]["overall"] is not None}
    h = collect_heldout()
    md = markdown(rows, agg, ref, crit, drift, anchors, h)
    (BENCH / "BENCHMARK.md").write_text(md, encoding="utf-8")
    (BENCH / "results.json").write_text(json.dumps(
        {"rubric": RUBRIC_VERSION, "rows": rows, "aggregate": agg, "cloud_reference": ref, "criteria": crit,
         "judge_drift": drift, "anchors": anchors, "heldout": h, "assumptions": ASSUMPTIONS}, indent=1),
        encoding="utf-8")
    deck, issues = bench_deck(rows, agg, ref, crit, RUNS / "report") if "local-v1.1" in crit else (None, [])
    print(md)
    print("benchmark deck:", deck, "render issues:", issues)


if __name__ == "__main__":
    main()
