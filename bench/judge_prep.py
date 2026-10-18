"""Build anonymized contact sheets for the blind visual judge.

  python bench/judge_prep.py round1 runs/v1.0 runs/cloud
  python bench/judge_prep.py round2 runs/v1.1 runs/v1.0 runs/cloud/gpt-6-astra-max runs/cloud/claude-opus-5.5-max
      # v1.1 mixed blind with re-ID'd round-1 anchors so judge drift between rounds is measurable
  python bench/judge_prep.py round3 runs/heldout/v1.0 runs/heldout/v1.1 runs/v1.0 runs/v1.1 runs/cloud/gpt-6-astra-max
      # held-out briefs + anchors from both benchmark briefs
"""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from forge.config import BENCH, RUNS  # noqa: E402
from forge.preview import contact_sheet  # noqa: E402


def _cloud_decks(d: Path):
    for bid in ("contoso_sales", "zava_technical"):
        png = d / "render" / f"png-{bid}"
        if png.exists():
            yield {"source": d.name, "brief": bid, "png_dir": png}


def collect(sources):
    decks = []
    for src in sources:
        src = Path(src)
        if src.name == "cloud":
            for d in sorted(p for p in src.iterdir() if p.is_dir() and p.name != "prompts"):
                decks.extend(_cloud_decks(d))
        elif src.parent.name == "cloud":  # a single cloud run used as a calibration anchor
            decks.extend(_cloud_decks(src))
        else:
            summary = json.loads((src / "summary.json").read_text(encoding="utf-8"))
            for bid, m in summary["results"].items():
                decks.append({"source": f"local-v{m['harness']}", "brief": bid,
                              "png_dir": src / bid / f"png-{m['template']}"})
    return decks


def main(round_name, *sources):
    out = BENCH / "judge" / round_name
    out.mkdir(parents=True, exist_ok=True)
    decks = collect(sources)
    rng = random.Random(f"forge-{round_name}")
    ranges = {"round1": range(10, 99), "round2": range(100, 1000)}
    ids = rng.sample(ranges.get(round_name, range(1000, 10000)), len(decks))
    key = {}
    for deck, n in zip(decks, ids):
        pngs = sorted(Path(deck["png_dir"]).glob("slide*.png"))
        contact_sheet(pngs, out / f"deck-{n}.png", label=f"Deck {n}")
        key[f"deck-{n}"] = {"source": deck["source"], "brief": deck["brief"]}
    hidden = RUNS / "judge-keys"
    hidden.mkdir(parents=True, exist_ok=True)
    (hidden / f"{round_name}.json").write_text(json.dumps(key, indent=1), encoding="utf-8")
    by_brief = {}
    for k, v in key.items():
        by_brief.setdefault(v["brief"], []).append(k)
    (out / "manifest.json").write_text(json.dumps({b: sorted(v) for b, v in by_brief.items()}, indent=1), encoding="utf-8")
    print(json.dumps({b: sorted(v) for b, v in by_brief.items()}))


if __name__ == "__main__":
    main(sys.argv[1], *sys.argv[2:])
