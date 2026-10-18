"""Re-render + re-grade a frozen run (spec unchanged) after a shared renderer fix; generation metrics are kept.

  python bench/rerender.py runs/v1.0
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forge import grade  # noqa: E402
from forge.config import BRIEFS  # noqa: E402
from forge.preview import preview  # noqa: E402
from forge.render import render  # noqa: E402


def main(run_root):
    run_root = Path(run_root)
    summary_path = run_root / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    for bid, m in summary["results"].items():
        brief = json.loads((BRIEFS / f"{bid}.json").read_text(encoding="utf-8"))
        if m.get("measured_facts"):  # v1.1 provenance numbers are measured in-run and traceable to telemetry
            brief["facts"] = brief["facts"] + m["measured_facts"]
        d = run_root / bid
        spec = json.loads((d / f"{bid}.spec.json").read_text(encoding="utf-8"))
        strict = m["grade"]["detail"]["structure"]["strict_json"]
        templates = [m["template"]] + (["surface", "surface_ultra"] if bid == "contoso_sales" else [])
        for tpl in templates:
            r = render(spec, tpl, d / f"{bid}-{tpl}.pptx")
            preview(r["path"], d / f"png-{tpl}", label=f"v{m['harness']} local | {brief['client']} | {tpl}")
            if tpl == m["template"]:
                m["grade"] = grade.grade(spec, r["slides"], brief, strict)
                m["render_summary"] = r["slides"]
        (d / f"{bid}.metrics.json").write_text(json.dumps(m, indent=1), encoding="utf-8")
        print(bid, m["grade"]["auto_score"], m["grade"]["auto_grade"], json.dumps(m["grade"]["scores"]))
    summary_path.write_text(json.dumps(summary, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
