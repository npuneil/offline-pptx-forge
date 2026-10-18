"""Render, preview and grade every cloud spec with the identical renderer + rubric.

  python bench/cloud_eval.py            # writes runs/cloud/summary.json
Timing: `seconds` = API generation time (sum of the content-generating model calls, exact per-call durations
from the Copilot session store via runs/cloud/usage.json). `wall_seconds` = spec write time - batch launch
(upper bound: includes 12-way concurrency queueing, agent tool calls and file I/O).
Tokens: input = benchmark prompt chars / 4; output = exact output tokens incl. hidden reasoning (usage.json),
else output chars / 4 of the visible JSON.
"""
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forge import economics  # noqa: E402
from forge.config import ASSUMPTIONS, BRIEFS, RUNS, portable  # noqa: E402
from forge.planner import grade_external  # noqa: E402
from forge.preview import preview  # noqa: E402

CLOUD = RUNS / "cloud"


def main(do_preview=True):
    launch = json.loads((CLOUD / "launch.json").read_text())
    t_launch = dt.datetime.fromisoformat(launch["launched_utc"])
    usage = json.loads((CLOUD / "usage.json").read_text()) if (CLOUD / "usage.json").exists() else {}
    cpt = ASSUMPTIONS["chars_per_token"]
    out = {}
    for d in sorted(p for p in CLOUD.iterdir() if p.is_dir() and p.name != "prompts"):
        model = "claude-opus-5.5" if d.name.startswith("claude-opus-5.5") else "gpt-6-astra"
        level = d.name.rsplit("-", 1)[1]
        for bid in ("contoso_sales", "zava_technical"):
            f = d / f"{bid}.json"
            if not f.exists():
                continue
            brief = json.loads((BRIEFS / f"{bid}.json").read_text(encoding="utf-8"))
            template = brief["template_hint"]
            try:
                res = grade_external(f, brief, template, d / "render")
            except Exception as exc:  # unparseable output is a scored failure, not a crash
                out[f"{d.name}/{bid}"] = {"model": model, "level": level, "brief": bid, "error": str(exc)}
                continue
            if do_preview:
                preview(res["pptx"], d / "render" / f"png-{bid}", label=f"{model} {level} | {brief['client']} | {template}")
            mtime = dt.datetime.fromtimestamp(f.stat().st_mtime, tz=dt.timezone.utc)
            in_tok = round(launch[bid]["chars"] / cpt)
            u = usage.get(d.name, {}).get(bid)
            out_tok = u["output_tokens"] if u else round(res["output_chars"] / cpt)
            econ = economics.cloud(model, in_tok, out_tok)
            wall = round((mtime - t_launch).total_seconds(), 1)
            out[f"{d.name}/{bid}"] = {
                "model": model, "level": level, "brief": bid, "template": template,
                "seconds": u["api_seconds"] if u else wall, "wall_seconds": wall,
                "input_tokens": in_tok, "output_tokens": out_tok,
                "reasoning_tokens": u.get("reasoning_tokens") if u else None,
                "truncated_calls": u.get("truncated_calls") if u else None,
                "token_source": "session-store exact usage" if u else "chars/4 of visible JSON (excludes hidden reasoning)",
                "usage": u,
                "economics": econ, "grade": res["grade"], "pptx": portable(res["pptx"]),
                "render_summary": res["render_summary"], "slides": len(res["spec"]["slides"]),
            }
            g = res["grade"]
            print(f"{d.name:22s} {bid:15s} {out[f'{d.name}/{bid}']['seconds']:7.1f}s auto {g['auto_score']:5.1f} "
                  f"{g['auto_grade']:3s} {json.dumps(g['scores'])}")
    (CLOUD / "summary.json").write_text(json.dumps(out, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main("--no-preview" not in sys.argv)
