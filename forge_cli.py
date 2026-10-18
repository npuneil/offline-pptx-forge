"""Offline PPTX Forge CLI.

  python forge_cli.py build briefs/contoso_sales.json             # interactive template picker
  python forge_cli.py build briefs/zava_technical.json --template surface_ultra --harness 1.1
  python forge_cli.py render spec.json --template surface --out deck.pptx
  python forge_cli.py preview deck.pptx
  python forge_cli.py themes | server start|stop|status
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from forge import VERSION, runtime
from forge.config import DEFAULT_MODEL, RUNS
from forge.themes import THEMES

TEMPLATE_INFO = {
    "microsoft": "Microsoft - clean white, four-square motif, Fluent blue",
    "surface": "Surface - warm platinum, sapphire accents, soft bloom",
    "surface_ultra": "Surface Laptop Ultra - dark, NVIDIA green glow, RTX Spark styling",
}


def pick_template(hint: str | None) -> str:
    names = list(THEMES)
    print("Choose a template:")
    for i, n in enumerate(names, 1):
        star = "  (suggested by brief)" if n == hint else ""
        print(f"  {i}. {TEMPLATE_INFO.get(n, n)}{star}")
    default = names.index(hint) + 1 if hint in names else 1
    if not sys.stdin.isatty():
        print(f"  -> non-interactive, using {names[default - 1]}")
        return names[default - 1]
    ans = input(f"Template [1-{len(names)}, default {default}]: ").strip()
    return names[int(ans) - 1] if ans.isdigit() and 1 <= int(ans) <= len(names) else names[default - 1]


def main(argv=None):
    p = argparse.ArgumentParser(prog="forge", description=f"Offline PPTX Forge v{VERSION}")
    sub = p.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build", help="brief -> local LLM -> PPTX")
    b.add_argument("brief")
    b.add_argument("--template", choices=list(THEMES))
    b.add_argument("--harness", default="1.1", choices=["1.0", "1.1"])
    b.add_argument("--model", default=DEFAULT_MODEL)
    b.add_argument("--out")
    b.add_argument("--preview", action="store_true")
    r = sub.add_parser("render", help="spec JSON -> PPTX (no LLM)")
    r.add_argument("spec")
    r.add_argument("--template", choices=list(THEMES))
    r.add_argument("--out", required=True)
    pv = sub.add_parser("preview", help="export PNGs + contact sheet via PowerPoint")
    pv.add_argument("pptx")
    sub.add_parser("themes")
    s = sub.add_parser("server")
    s.add_argument("action", choices=["start", "stop", "status"])
    s.add_argument("--model", default=DEFAULT_MODEL)
    a = p.parse_args(argv)

    if a.cmd == "themes":
        for n, info in TEMPLATE_INFO.items():
            print(f"{n:14s} {info}")
    elif a.cmd == "server":
        if a.action == "start":
            print(json.dumps(runtime.start(a.model), indent=1))
        elif a.action == "stop":
            print("stopped" if runtime.stop() else "not running (or not started by forge)")
        else:
            print(json.dumps({"healthy": runtime.health(), "model": runtime.loaded_model()}))
    elif a.cmd == "render":
        from forge.render import render_file
        res = render_file(a.spec, a.template or pick_template(None), a.out)
        print(res["path"])
    elif a.cmd == "preview":
        from forge.preview import preview
        print(preview(a.pptx, Path(a.pptx).with_suffix("")))
    elif a.cmd == "build":
        from forge.planner import HARNESSES
        brief = json.loads(Path(a.brief).read_text(encoding="utf-8"))
        template = a.template or pick_template(brief.get("template_hint"))
        info = runtime.start(a.model)
        from forge import llm
        llm.use_port(info["port"])
        print(f"model {info['model']} ready ({'reused' if info['reused'] else f'loaded in {info['load_s']}s'})")
        out = Path(a.out) if a.out else RUNS.parent / "decks" / f"{brief['id']}-v{a.harness}"
        m = HARNESSES[a.harness](brief, template, out)
        print(m["pptx"])
        if a.preview:
            from forge.preview import preview
            print(preview(m["pptx"], Path(m["pptx"]).with_suffix("")))


if __name__ == "__main__":
    main()
