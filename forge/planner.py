"""Brief -> spec -> PPTX pipelines. Each harness version is kept selectable and frozen."""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import economics, grade, lint, llm, prompts_v1_0, prompts_v1_1, schema
from .config import portable
from .render import render
from .telemetry import PowerMeter


def build_v1_0(brief: dict, template: str, out_dir: Path, log=print) -> dict:
    """v1.0: single-shot JSON spec, lenient parse, one retry on invalid JSON."""
    msgs = prompts_v1_0.messages(brief)
    calls = []
    t0 = time.perf_counter()
    with PowerMeter() as pm:
        res = llm.chat(msgs, max_tokens=8192, temperature=0.4)
        calls.append(res)
        spec, strict, err = schema.parse(res["text"])
        if spec is None:
            log(f"  invalid JSON ({err}); retrying once")
            retry = msgs + [{"role": "assistant", "content": res["text"]},
                            {"role": "user", "content": f"That was not valid JSON ({err}). Return only the JSON object."}]
            res = llm.chat(retry, max_tokens=8192, temperature=0.2)
            calls.append(res)
            spec, _, err = schema.parse(res["text"])
            if spec is None:
                raise RuntimeError(f"model did not return JSON: {err}")
    gen_s = time.perf_counter() - t0
    spec = schema.normalize(spec, brief)
    return _finish(spec, strict, brief, template, out_dir, calls, pm.result(), gen_s, "1.0", log)


def _apply_fixes(spec: dict, fixes) -> dict:
    """Apply repair-pass fixes: {"index": i, "slide": {...}} replaces, {"index": i, "delete": true} removes."""
    slides = [dict(s) for s in spec.get("slides") or []]
    deletes = set()
    for f in fixes if isinstance(fixes, list) else []:
        if not isinstance(f, dict):
            continue
        try:
            i = int(f.get("index"))
        except (TypeError, ValueError):
            continue
        if not 0 <= i < len(slides):
            continue
        if f.get("delete") is True and 0 < i < len(slides) - 1:
            deletes.add(i)
        elif isinstance(f.get("slide"), dict) and f["slide"].get("layout"):
            slides[i] = f["slide"]
    return dict(spec, slides=[s for i, s in enumerate(slides) if i not in deletes])


MODEL_NAMES = {"qwen3-coder-30b": "Qwen3-Coder 30B"}


def _provenance_slide(gen_s: float, tokens: int, wh: float, model: str) -> tuple[dict, str]:
    name = MODEL_NAMES.get(model, model)
    slide = {
        "layout": "kpis", "title": "This Laptop Built This Deck",
        "takeaway": f"{name} wrote it on llama.cpp, no cloud calls.",
        "data": {"items": [
            {"value": "0", "label": "Cloud calls", "icon": "cloud", "source": "harness log"},
            {"value": f"{gen_s:.0f} s", "label": "Drafting time", "icon": "timer", "source": "measured"},
            {"value": f"{tokens:,}", "label": "Tokens generated", "icon": "ai", "source": "llama.cpp"},
            {"value": f"{wh:.1f} Wh", "label": "Energy used", "icon": "bolt", "source": "nvidia-smi"}]},
        "notes": "Proof, not a promise: these numbers were measured while this deck was generated on this "
                 "Surface Laptop Ultra. Drafting time covers the local model passes; energy is GPU plus a platform allowance.",
    }
    fact = (f"Measured during this run on this device: {gen_s:.0f} s drafting time, {tokens:,} tokens generated, "
            f"{wh:.1f} Wh energy, 0 cloud calls.")
    return slide, fact


def build_v1_1(brief: dict, template: str, out_dir: Path, log=print, max_repairs: int = 2) -> dict:
    """v1.1: arc-guided JSON-mode generation -> dry render + lint -> targeted repair passes -> measured provenance."""
    arc = prompts_v1_1.arc_for(brief)
    provenance = "made_on_device" in (brief.get("required_topics") or {})
    reserved = 1 if provenance else 0
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scratch = out_dir / f"_lint-{brief['id']}.pptx"

    def check(s):
        rendered = render(s, template, scratch)
        return lint.lint(s, brief, rendered["slides"], arc, reserved)

    calls, history = [], []
    t0 = time.perf_counter()
    with PowerMeter() as pm:
        msgs = prompts_v1_1.messages(brief)
        res = llm.chat(msgs, max_tokens=8192, temperature=0.4, json_mode=True)
        calls.append(res)
        spec, strict, err = schema.parse(res["text"])
        if spec is None:
            log(f"  invalid JSON ({err}); retrying once")
            res = llm.chat(msgs, max_tokens=8192, temperature=0.2, json_mode=True, seed=11)
            calls.append(res)
            spec, strict, err = schema.parse(res["text"])
            if spec is None:
                raise RuntimeError(f"model did not return JSON: {err}")
        spec = schema.normalize(spec, brief)
        issues = check(spec)
        history.append({"pass": "draft", "issues": len(issues), "codes": sorted({i["code"] for i in issues})})
        log(f"  draft: {len(spec['slides'])} slides, {len(issues)} lint issues")
        for rnd in range(max_repairs):
            if not issues:
                break
            res = llm.chat(prompts_v1_1.repair_messages(brief, spec, issues), max_tokens=6144, temperature=0.3,
                           json_mode=True)
            calls.append(res)
            fx, _, _ = schema.parse(res["text"])
            cand = schema.normalize(_apply_fixes(spec, (fx or {}).get("fixes")), brief)
            cand_issues = check(cand)
            accepted = len(cand_issues) < len(issues)
            history.append({"pass": f"repair{rnd + 1}", "issues": len(cand_issues), "accepted": accepted,
                            "fixed_slides": len((fx or {}).get("fixes") or []),
                            "codes": sorted({i["code"] for i in cand_issues})})
            log(f"  repair {rnd + 1}: {len(issues)} -> {len(cand_issues)} issues ({'accepted' if accepted else 'reverted'})")
            if not accepted:
                break
            spec, issues = cand, cand_issues
    gen_s = time.perf_counter() - t0
    scratch.unlink(missing_ok=True)
    power = pm.result()
    ctok = sum(c["completion_tokens"] for c in calls)
    grade_brief, measured = brief, []
    if provenance:
        slide, fact = _provenance_slide(gen_s, ctok, power["total_wh"], llm_model_name())
        spec["slides"].insert(max(1, len(spec["slides"]) - 1), slide)
        measured = [fact]
        grade_brief = dict(brief, facts=list(brief.get("facts") or []) + measured)
    return _finish(spec, strict, grade_brief, template, out_dir, calls, power, gen_s, "1.1", log,
                   extra={"lint_history": history, "lint_remaining": issues, "measured_facts": measured})


def _finish(spec, strict, brief, template, out_dir, calls, power, gen_s, version, log, extra=None):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    t1 = time.perf_counter()
    rendered = render(spec, template, out_dir / f"{brief['id']}-{template}.pptx")
    render_s = time.perf_counter() - t1
    g = grade.grade(spec, rendered["slides"], brief, strict)
    ptok = sum(c["prompt_tokens"] for c in calls)
    ctok = sum(c["completion_tokens"] for c in calls)
    metrics = {
        "harness": version, "brief": brief["id"], "template": template, "lane": "local",
        "model": llm_model_name(), "llm_calls": len(calls),
        "prompt_tokens": ptok, "completion_tokens": ctok,
        "decode_tps": round(sum(c["decode_tps"] for c in calls) / len(calls), 1),
        "ttft_s": calls[0]["ttft_s"], "generate_s": round(gen_s, 2), "render_s": round(render_s, 2),
        "total_s": round(gen_s + render_s, 2), "power": power,
        "economics": economics.local(power["total_wh"], ptok, ctok),
        "grade": g, "pptx": rendered["path"], "render_summary": rendered["slides"],
    }
    if extra:
        metrics.update(extra)
    (out_dir / f"{brief['id']}.spec.json").write_text(json.dumps(spec, indent=1, ensure_ascii=False), encoding="utf-8")
    (out_dir / f"{brief['id']}.raw.txt").write_text("\n\n=====\n\n".join(c["text"] for c in calls), encoding="utf-8")
    (out_dir / f"{brief['id']}.metrics.json").write_text(
        json.dumps({**metrics, "pptx": portable(metrics["pptx"])}, indent=1), encoding="utf-8")
    log(f"  {brief['id']}: {len(spec['slides'])} slides, gen {gen_s:.1f}s, {ctok} tok @ {metrics['decode_tps']} tok/s, "
        f"{power['total_wh']:.2f} Wh, auto {g['auto_score']} ({g['auto_grade']})")
    return metrics


def llm_model_name():
    from .runtime import loaded_model
    return loaded_model(llm.ACTIVE["port"]) or "unknown"


def grade_external(spec_path: Path, brief: dict, template: str, out_dir: Path) -> dict:
    """Render + grade a spec produced elsewhere (cloud model) with the identical renderer and rubric."""
    raw = Path(spec_path).read_text(encoding="utf-8")
    spec, strict, err = schema.parse(raw)
    if spec is None:
        raise RuntimeError(f"{spec_path}: {err}")
    spec = schema.normalize(spec, brief)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rendered = render(spec, template, out_dir / f"{brief['id']}-{template}.pptx")
    g = grade.grade(spec, rendered["slides"], brief, strict)
    return {"spec": spec, "grade": g, "pptx": rendered["path"], "render_summary": rendered["slides"],
            "output_chars": len(raw)}


HARNESSES = {"1.0": build_v1_0, "1.1": build_v1_1}
