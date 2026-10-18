"""Run the local harness over a brief set and preview the decks.

  python bench/run_local.py 1.0                  # benchmark briefs -> runs/v1.0
  python bench/run_local.py 1.1 --set heldout    # unseen briefs (briefs/heldout) -> runs/heldout/v1.1
"""
import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forge import llm, runtime  # noqa: E402
from forge.config import BRIEFS, RUNS, portable  # noqa: E402
from forge.planner import HARNESSES  # noqa: E402
from forge.preview import preview  # noqa: E402
from forge.render import render  # noqa: E402

BRIEF_SETS = {
    "bench": (BRIEFS, ["contoso_sales", "zava_technical"], ""),
    "heldout": (BRIEFS / "heldout", ["northwind_sales", "woodgrove_technical", "tailspin_sales"], "heldout"),
}


def main(version="1.0", brief_set="bench"):
    brief_dir, brief_ids, sub = BRIEF_SETS[brief_set]
    alt_templates = brief_set == "bench"
    info = runtime.start()
    llm.use_port(info["port"])
    print(f"harness v{version} | {brief_set} | model {info['model']} on :{info['port']} "
          f"({'attached' if info['reused'] else 'loaded'})")
    out_root = (RUNS / sub if sub else RUNS) / f"v{version}"
    results = {}
    for bid in brief_ids:
        brief = json.loads((brief_dir / f"{bid}.json").read_text(encoding="utf-8"))
        template = brief["template_hint"]
        m = HARNESSES[version](brief, template, out_root / bid)
        t = time.perf_counter()
        preview(m["pptx"], out_root / bid / f"png-{template}", label=f"v{version} local | {brief['client']} | {template}")
        m["preview_s"] = round(time.perf_counter() - t, 1)
        if alt_templates and bid == "contoso_sales":
            spec = json.loads((out_root / bid / f"{bid}.spec.json").read_text(encoding="utf-8"))
            for alt in ("surface", "surface_ultra"):
                r = render(spec, alt, out_root / bid / f"{bid}-{alt}.pptx")
                preview(r["path"], out_root / bid / f"png-{alt}", label=f"v{version} local | {brief['client']} | {alt}")
        results[bid] = m
    recorded = {bid: {**m, "pptx": portable(m["pptx"])} for bid, m in results.items()}
    (out_root / "summary.json").write_text(json.dumps({"server": info, "results": recorded}, indent=1), encoding="utf-8")
    for bid, m in results.items():
        g = m["grade"]
        print(f"{bid:16s} auto {g['auto_score']:5.1f} {g['auto_grade']:3s} | gen {m['generate_s']}s | "
              f"{m['completion_tokens']} tok | {m['power']['total_wh']} Wh | {json.dumps(g['scores'])}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("version", nargs="?", default="1.0")
    ap.add_argument("--set", dest="brief_set", default="bench", choices=sorted(BRIEF_SETS))
    a = ap.parse_args()
    main(a.version, a.brief_set)
