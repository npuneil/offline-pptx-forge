# Offline PPTX Forge v1.1

Fully offline PowerPoint generator for Surface Laptop Ultra (NVIDIA RTX Spark). A local LLM
(Qwen3-Coder-30B-A3B on llama.cpp) writes a JSON deck spec. A deterministic python-pptx renderer then
draws every slide as native, editable infographics: architecture stacks, flows, canvas diagrams,
analogy maps, KPI tiles, charts, 2x2s and timelines. Decks are text-light and built around Local AI
architectures and analogies.

## Quick start

Requirements: Windows, Python 3.13 (tested), a llama.cpp `llama-server` with
Qwen3-Coder-30B-A3B (GGUF), and desktop PowerPoint for PNG previews only.

```powershell
pip install -r requirements.txt
.\forge.ps1 themes                                            # list templates
.\forge.ps1 build briefs\contoso_sales.json                   # interactive template picker
.\forge.ps1 build briefs\zava_technical.json --template surface_ultra --preview
.\forge.ps1 build briefs\contoso_sales.json --harness 1.0     # original single-shot harness
.\forge.ps1 render runs\v1.1\zava_technical\zava_technical.spec.json --template microsoft --out deck.pptx
.\forge.ps1 server start|stop|status
```

Templates (any spec renders in all three):

| Template | Look |
|---|---|
| `microsoft` | Clean white, four-square motif, Fluent blue |
| `surface` | Warm platinum, sapphire accents, soft bloom |
| `surface_ultra` | Dark, NVIDIA green glow, RTX Spark styling |

The templates are inspired by Microsoft and Surface styling. They are not official brand assets.

`build` writes to `decks\<brief>-v<harness>\`. The `runs\` folder holds frozen benchmark artifacts.
If a llama-server already serves the model on 8811, 8090 or 8080, the harness attaches to it.
Otherwise it starts one from `%USERPROFILE%\Local-AI-Bench` (override with `FORGE_LLAMA_HOME`).
Preview export (`--preview`) needs desktop PowerPoint.

## Brief format

`briefs\*.json`: `id`, `client`, `audience`, `pitch_type` (sales|technical), `objective`, `context`,
`facts` (the only numbers a deck may use), `required_topics` (topic -> keywords), `guardrails`,
`slide_range`, `template_hint`.

## Harness versions

| | v1.0 | v1.1 |
|---|---|---|
| Generation | Single shot, layout catalog | Slot-by-slot deck arc (sales or technical), analogy bank, fictional exemplars, JSON mode |
| Checks | Lenient parse + 1 retry | Render, then deterministic lint (`forge/lint.py`), then up to 2 targeted repair passes; keeps only passes that cut issues |
| Provenance | None | Measured "This Laptop Built This Deck" slide when the brief asks for it |

## Benchmark

```powershell
python bench\run_local.py 1.1                          # both briefs, previews, alt templates
python bench\run_local.py 1.1 --set heldout            # 3 unseen briefs (briefs\heldout) -> runs\heldout\v1.1
python bench\cloud_eval.py                             # render + grade the cloud specs in runs\cloud
python bench\judge_prep.py round2 runs\v1.1 runs\v1.0 runs\cloud\gpt-6-astra-max runs\cloud\claude-opus-5.5-max
python bench\judge_prep.py round3 runs\heldout\v1.0 runs\heldout\v1.1 runs\v1.0 runs\v1.1 runs\cloud\gpt-6-astra-max
python bench\report.py                                 # bench\BENCHMARK.md, bench\results.json, benchmark deck
python bench\story.py                                  # 18-slide story deck from results.json -> Downloads
```

- Overall = 0.5 x auto rubric (`forge/grade.py`, rubric 1.0.1) + 0.5 x blind visual judge (/50 x 2).
- Economics constants are in `forge/config.py` (`ASSUMPTIONS`).
- Results and disclosures are in [bench/BENCHMARK.md](bench/BENCHMARK.md). The benchmark deck is at
  `runs\report\forge-benchmark-surface_ultra.pptx`.

Headline (two briefs: Contoso sales, Zava technical):

- v1.1 raised the local deck from D (62.8) to B (85.6) overall. The blind-judge score rose from 19.5 to 39.0 /50.
- On the blind judge, v1.1 is at parity with Opus 5.5 and GPT-6 Astra (36.0-40.5). On overall score
  it ranks first, but part of that lead comes from the auto rubric, which v1.1's lint targets.
- Cost per 1,000 decks: about $0.41 of electricity locally, versus $285 at the cloud median. Local
  water use is 0 L.
- The trade-off is time. v1.1 takes 241 s on average, versus 64 s for v1.0 and a 108 s cloud median.
  That still beats the best-quality cloud configuration (Astra max, 268 s).
- "Training" means program and prompt distillation. Model weights were not changed.

Held-out test (3 unseen briefs: Northwind retail sales, Woodgrove Bank technical, Tailspin Toys sales;
harness frozen; judged blind in round 3 against anchors, drift -0.67):

- v1.1 still beats v1.0 on unseen briefs: judge 19.7 to 29.3 /50, overall D (62.9) to C (74.2).
- It does not hold its benchmark quality: judge 29.3 on held-out vs 39.0 on Contoso/Zava (-9.7), so about
  half of the round-1 gain was specific to the two training briefs.
- Overfitting found: every v1.1 held-out deck copies all 8 analogy pairs verbatim from a bank written from
  Contoso/Zava ("Consultant decides", "Restricted client Wi-Fi"). The technical arc hard-codes Zava's
  "10-developer, 14-day pilot", and Woodgrove shipped an unfilled `<CLIENT>` kicker. Tailspin invented a "40%" that the
  auto rubric missed because its fact check ignores units.
- Cost stays negligible ($0.0007/deck). v1.1 took 437 s/deck on the shared server (v1.0: 68 s).
- v1.2 backlog: parameterize arcs from brief facts, make bank pairs abstract, substitute `<CLIENT>` in code,
  and make the fact check unit-aware. Details are in section 7 of [bench/BENCHMARK.md](bench/BENCHMARK.md).
