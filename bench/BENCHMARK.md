# Offline PPTX Forge - Benchmark

Rubric 1.0.1 - overall = 0.5 x auto rubric (100) + 0.5 x blind judge (/50 x 2). Cloud reference = median of 12 cloud decks.

## 1. Scoreboard (per deck)

| Brief | Config | Slides | Auto /100 | Judge /50 | Overall | Grade | Gen s | Out tokens | Cost | Wh | g CO2e | mL water |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Contoso (sales) | Local v1.0 | 11 | 84.9 | 21 | 63.5 | D | 54.8 | 2,238 | $0.0001 | 0.73 | 0.27 | 0.0 |
| Contoso (sales) | Local v1.1 | 11 | 92.4 | 37 | 83.2 | B | 179.9 | 9,976 | $0.0004 | 2.77 | 1.01 | 0.0 |
| Contoso (sales) | Opus low | 11 | 83.9 | 35 | 77.0 | C+ | 27.5 | 3,283 | $0.072 | 3.61 | 1.32 | 11.8 |
| Contoso (sales) | Opus high | 12 | 83.8 | 40 | 81.9 | B- | 79.0 | 8,562 | $0.178 | 9.42 | 3.46 | 30.8 |
| Contoso (sales) | Opus max | 11 | 80.4 | 41 | 81.2 | B- | 581.9 | 69,334 | $1.39 | 76.27 | 27.99 | 249.6 |
| Contoso (sales) | Astra low | 10 | 84.0 | 39 | 81.0 | B- | 51.9 | 3,067 | $0.169 | 3.37 | 1.24 | 11.0 |
| Contoso (sales) | Astra high | 11 | 85.8 | 37 | 79.9 | C+ | 119.6 | 6,494 | $0.341 | 7.14 | 2.62 | 23.4 |
| Contoso (sales) | Astra max | 12 | 86.4 | 41 | 84.2 | B | 249.7 | 12,892 | $0.660 | 14.18 | 5.21 | 46.4 |
| Zava (technical) | Local v1.0 | 12 | 88.1 | 18 | 62.0 | D | 72.6 | 2,229 | $0.0001 | 0.87 | 0.32 | 0.0 |
| Zava (technical) | Local v1.1 | 11 | 93.8 | 41 | 87.9 | B+ | 302.3 | 9,044 | $0.0005 | 3.57 | 1.31 | 0.0 |
| Zava (technical) | Opus low | 12 | 86.6 | 37 | 80.3 | B- | 28.7 | 3,489 | $0.077 | 3.84 | 1.41 | 12.6 |
| Zava (technical) | Opus high | 12 | 83.2 | 40 | 81.6 | B- | 97.4 | 11,131 | $0.230 | 12.24 | 4.49 | 40.1 |
| Zava (technical) | Opus max | 12 | 78.9 | 40 | 79.5 | C+ | 630.8 | 73,028 | $1.47 | 80.33 | 29.48 | 262.9 |
| Zava (technical) | Astra low | 12 | 86.5 | 40 | 83.2 | B | 61.4 | 3,752 | $0.205 | 4.13 | 1.51 | 13.5 |
| Zava (technical) | Astra high | 12 | 87.2 | 41 | 84.6 | B | 154.1 | 8,534 | $0.444 | 9.39 | 3.44 | 30.7 |
| Zava (technical) | Astra max | 12 | 83.7 | 40 | 81.8 | B- | 285.3 | 14,775 | $0.756 | 16.25 | 5.96 | 53.2 |

## 2. Config averages (both briefs)

| Config | Auto | Judge | Overall | Grade | Gen s | Out tokens | Cost/deck | Wh/deck | mL water/deck |
|---|---|---|---|---|---|---|---|---|---|
| Local v1.0 | 86.5 | 19.5 | 62.8 | D | 63.7 | 2,234 | $0.0001 | 0.80 | 0.0 |
| Local v1.1 | 93.1 | 39.0 | 85.6 | B | 241.1 | 9,510 | $0.0004 | 3.17 | 0.0 |
| Opus low | 85.2 | 36.0 | 78.7 | C+ | 28.1 | 3,386 | $0.074 | 3.72 | 12.2 |
| Opus high | 83.5 | 40.0 | 81.8 | B- | 88.2 | 9,846 | $0.204 | 10.83 | 35.4 |
| Opus max | 79.7 | 40.5 | 80.3 | B- | 606.3 | 71,181 | $1.43 | 78.30 | 256.2 |
| Astra low | 85.2 | 39.5 | 82.1 | B- | 56.6 | 3,410 | $0.187 | 3.75 | 12.3 |
| Astra high | 86.5 | 39.0 | 82.2 | B- | 136.8 | 7,514 | $0.392 | 8.27 | 27.0 |
| Astra max | 85.1 | 40.5 | 83.0 | B | 267.5 | 13,834 | $0.708 | 15.22 | 49.8 |

## 3. Self-grade vs cloud (initial benchmarking criteria)

Formulas: cost = 1 - local/cloud-median cost; sustainability = mean(energy reduction, water reduction) vs cloud median; time = min(1, cloud-median API seconds / local seconds); deck = overall score; composite = equal-weight mean.

| Criterion | Local v1.0 | Local v1.1 | Delta |
|---|---|---|---|
| Cost savings | 100.0 (A+) | 99.9 (A+) | -0.1 |
| Sustainability vs cloud | 95.7 (A) | 83.1 (B) | -12.6 |
| Time to generate | 100.0 (A+) | 45.0 (F) | -55.0 |
| Deck grade (overall) | 62.8 (D) | 85.6 (B) | +22.8 |
| Composite | 89.6 (B+) | 78.4 (C+) | -11.2 |

## 4. Local vs cloud economics (per 1,000 decks)

| Lane | Generation time | Marginal cost | Energy | CO2e | Water |
|---|---|---|---|---|---|
| Local v1.0 | 17.7 h | $0.10 | 0.80 kWh | 0.29 kg | 0.0 L |
| Local v1.1 | 67.0 h | $0.41 | 3.17 kWh | 1.16 kg | 0.0 L |
| Cloud median | 30.1 h | $285.09 | 9.40 kWh | 3.45 kg | 30.8 L |
| Best-quality cloud (Astra max) | 74.3 h | $708.32 | 15.22 kWh | 5.58 kg | 49.8 L |

## 5. v1.0 -> v1.1 delta (one round of frontier distillation)

| Brief | Metric | v1.0 | v1.1 | Delta |
|---|---|---|---|---|
| Contoso (sales) | auto | 84.9 | 92.4 | +7.5 |
| Contoso (sales) | judge | 21.0 | 37.0 | +16.0 |
| Contoso (sales) | overall | 63.5 | 83.2 | +19.7 |
| Contoso (sales) |   auto: visual_richness | 21.0 | 23.0 | +2.0 |
| Contoso (sales) |   auto: text_lightness | 20.0 | 14.4 | -5.6 |
| Contoso (sales) |   auto: analogy | 6.0 | 15.0 | +9.0 |
| Contoso (sales) |   auto: brief_coverage | 12.9 | 15.0 | +2.1 |
| Contoso (sales) |   auto: claim_discipline | 15.0 | 15.0 | +0.0 |
| Contoso (sales) |   auto: structure | 10.0 | 10.0 | +0.0 |
| Contoso (sales) | gen seconds | 54.8 | 179.9 | +125.2 |
| Contoso (sales) | output tokens | 2238.0 | 9976.0 | +7738.0 |
| Contoso (sales) | LLM calls | 1.0 | 3.0 | +2.0 |
| Contoso (sales) | Wh | 0.7 | 2.8 | +2.0 |
| Contoso (sales) | lint issues (draft -> final) | 17 | 14 |  |
| Zava (technical) | auto | 88.1 | 93.8 | +5.7 |
| Zava (technical) | judge | 18.0 | 41.0 | +23.0 |
| Zava (technical) | overall | 62.0 | 87.9 | +25.9 |
| Zava (technical) |   auto: visual_richness | 18.1 | 22.7 | +4.6 |
| Zava (technical) |   auto: text_lightness | 20.0 | 16.1 | -3.9 |
| Zava (technical) |   auto: analogy | 10.0 | 15.0 | +5.0 |
| Zava (technical) |   auto: brief_coverage | 15.0 | 15.0 | +0.0 |
| Zava (technical) |   auto: claim_discipline | 15.0 | 15.0 | +0.0 |
| Zava (technical) |   auto: structure | 10.0 | 10.0 | +0.0 |
| Zava (technical) | gen seconds | 72.6 | 302.3 | +229.7 |
| Zava (technical) | output tokens | 2229.0 | 9044.0 | +6815.0 |
| Zava (technical) | LLM calls | 1.0 | 3.0 | +2.0 |
| Zava (technical) | Wh | 0.9 | 3.6 | +2.7 |
| Zava (technical) | lint issues (draft -> final) | 13 | 10 |  |

Rank by mean overall: Local v1.1 85.6 > Astra max 83.0 > Astra high 82.2 > Astra low 82.1 > Opus high 81.8 > Opus max 80.3 > Opus low 78.7 > Local v1.0 62.8

Rank by blind judge only (/50, the fairer quality signal because v1.1 lint targets some auto-rubric checks): Opus max 40.5 > Astra max 40.5 > Opus high 40.0 > Astra low 39.5 > Local v1.1 39.0 > Astra high 39.0 > Opus low 36.0 > Local v1.0 19.5

Quality-matched time: v1.1 averaged 241 s vs 268 s for the best-quality cloud config (Astra max); the 108 s cloud median is dominated by low-effort runs that scored lower.

Judge critiques of v1.1 (inputs for v1.2):

- Contoso (sales): Many label titles, '30% sites without Wi-Fi' and an unhedged 'works where Wi-Fi is restricted' overstate the brief, the 2x2 highlights the cloud quadrant and inverts the sensitivity axis, and the 'traffic jam' and 'specialized team' analogies are throwaways.
- Zava (technical): The routing diagram puts 'Cloud Reasoning' inside the device boundary with no link to the cloud lane, the 'no cloud calls' title subtitle conflicts with hybrid routing, and several titles are labels.

## 6. Judge calibration (round-2 anchors re-scored blind under new IDs)

| Anchor | Brief | Round 1 | Round 2 | Delta |
|---|---|---|---|---|
| Opus max | Contoso (sales) | 41 | 41 | +0 |
| Opus max | Zava (technical) | 40 | 40 | +0 |
| Astra max | Contoso (sales) | 41 | 41 | +0 |
| Astra max | Zava (technical) | 40 | 40 | +0 |
| Local v1.0 | Contoso (sales) | 21 | 21 | +0 |
| Local v1.0 | Zava (technical) | 18 | 18 | +0 |

Per-brief mean drift applied to the v1.1 judge score: Contoso (sales) +0.00 (3 anchors), Zava (technical) +0.00 (3 anchors)

## 7. Held-out briefs (generalization test)

Three new fictional briefs, written after v1.1 was frozen and never used to tune it: Northwind Traders (retail sales, `surface`), Woodgrove Bank (financial-services technical, `microsoft`), Tailspin Toys (game-studio sales, `surface_ultra`). Both harnesses ran unchanged on the same shared server. The same judge scored them blind in round 3, mixed with re-ID'd anchors from the benchmark briefs.

| Brief | Config | Slides | Auto /100 | Judge /50 | Overall | Grade | Gen s | Out tokens | Wh | Lint draft -> final | Bank pairs verbatim | Placeholders |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Northwind (sales) | Local v1.0 | 11 | 86.6 | 18.7 (raw 18) | 62.0 | D | 102.3 | 2,151 | 1.42 |  | 0/3 | none |
| Northwind (sales) | Local v1.1 | 11 | 90.5 | 29.7 (raw 29) | 74.9 | C | 472.8 | 9,105 | 6.17 | 16 -> 12 | 8/8 | none |
| Woodgrove (technical) | Local v1.0 | 11 | 90.4 | 20.7 (raw 20) | 65.9 | D | 54.8 | 2,192 | 0.77 |  | 0/6 | none |
| Woodgrove (technical) | Local v1.1 | 11 | 91.0 | 27.7 (raw 27) | 73.2 | C | 447.7 | 9,400 | 6.11 | 12 -> 11 | 8/8 | <CLIENT> |
| Tailspin (sales) | Local v1.0 | 10 | 82.4 | 19.7 (raw 19) | 60.9 | D | 47.8 | 1,710 | 0.66 |  | 0/3 | none |
| Tailspin (sales) | Local v1.1 | 11 | 87.7 | 30.7 (raw 30) | 74.5 | C | 390.2 | 9,422 | 4.80 | 17 -> 16 | 8/8 | none |

| Set | Auto | Judge | Overall | Grade | Gen s | Out tokens | Cost/deck | Wh/deck |
|---|---|---|---|---|---|---|---|---|
| v1.0 on held-out | 86.5 | 19.7 | 62.9 | D | 68.3 | 2,018 | $0.0001 | 0.95 |
| v1.1 on held-out | 89.7 | 29.3 | 74.2 | C | 436.9 | 9,309 | $0.0007 | 5.70 |
| v1.0 on benchmark briefs | 86.5 | 19.5 | 62.8 | D | 63.7 | 2,234 | $0.0001 | 0.80 |
| v1.1 on benchmark briefs | 93.1 | 39.0 | 85.6 | B | 241.1 | 9,510 | $0.0004 | 3.17 |

- Held-out delta v1.0 -> v1.1: judge +9.7 /50, overall +11.3 (D -> C). Benchmark-brief delta was judge +19.5.
- v1.1 judge on held-out vs benchmark briefs: 29.3 vs 39.0 (-9.7).
- Held-out v1.1 cost $0.0007/deck vs $0.285 cloud median (385x); 437 s vs 108 s cloud median.

| Anchor | Brief | Prior round | Round 3 | Delta |
|---|---|---|---|---|
| Astra max | Contoso (sales) | 41 | 41 | +0 |
| Astra max | Zava (technical) | 40 | 41 | +1 |
| Local v1.0 | Contoso (sales) | 21 | 20 | -1 |
| Local v1.0 | Zava (technical) | 18 | 19 | +1 |
| Local v1.1 | Contoso (sales) | 37 | 34 | -3 |
| Local v1.1 | Zava (technical) | 41 | 39 | -2 |

Mean anchor drift -0.67 was subtracted from held-out judge scores.

Judge critiques of v1.1 on held-out briefs:

- Northwind (sales): Contoso carryover ('Consultant decides', 'Sensitive client files', client Wi-Fi), an analogy row saying '2-week pilot' that contradicts the 3-week brief, a 2x2 that highlights the cloud quadrant, and no mention of supplier cost sheets or the 1-in-4 Wi-Fi fact.
- Woodgrove (technical): Unfilled '<CLIENT>' placeholder, a final ask of '10 developers, 14 days' contradicting the 12-analyst / 3-week title, Zava carryover (IDE, developer workflows, sizing bands), unsupported self-proof numbers (448 s, 9,400 tokens, 6.1 Wh) and no loan files, notebooks or 1,800-document library.
- Tailspin (sales): Invents '40% sites without Wi-Fi', reuses Contoso wording ('Sensitive client files', 'Consultant decides', client Wi-Fi, 'summaries'), mentions embargo only on the cover, and never brings up offsite playtests or conventions.

Root cause (code review after the held-out run; the harness stayed frozen):

- The v1.1 deck arcs hard-code benchmark-brief specifics: the technical CTA slot says '10-developer, 14-day pilot' (Zava's ask), and slots name 'consultant-reviewed draft', 'Restricted client Wi-Fi', 'COO, CIO, practice lead' and 'CAD/PLM data' (`forge/prompts_v1_1.py`, `ARCS`).
- Analogy-bank entries carry fully worked Contoso/Zava pairs ('Consultant decides', '2-week pilot', CNC mill sizes). The local model copies them verbatim, which the 'Bank pairs verbatim' column counts.
- The `<CLIENT>` kicker is left for the model to fill; on Woodgrove it shipped unfilled.
- Auto-rubric blind spot: claim discipline matches bare numbers, not number + unit, so '40%' passes because '40 minutes' is a fact (`forge/grade.py`). The v1.1 lint shares this check.
- v1.2 backlog: parameterize arcs from brief facts (pilot size, duration, sponsors, sensitive data), turn bank pairs into abstract templates, substitute `<CLIENT>` in code, and make the fact check unit-aware.

## 8. Method and disclosures

- **Local lane**: Qwen3-Coder-30B-A3B (Q4_K_M) on llama.cpp, Surface Laptop Ultra (NVIDIA RTX Spark), attached to a shared llama-server (2 slots, other tenants active). Energy = measured GPU board power (nvidia-smi, 250 ms) + 10 W platform allowance; GPU power includes other tenants, so local energy is overstated. Decode varied 38-61 tok/s under contention vs 86 tok/s single-stream unshared.
- **Cloud lane**: identical prompt to Claude Opus 5.5 and GPT-6 Astra at low/high/max reasoning via Copilot CLI subagents. Output tokens are exact per-call usage (incl. reasoning). Time = API generation seconds (wall time incl. queueing is recorded separately). Cost = list price x tokens, excluding the agent system prompt. Energy/water = published per-1k-output-token estimates (1.1 Wh, 3.6 mL).
- Opus max hit the 32k output cap twice per brief (finish_reason=length); counted as-is.
- Local cost is marginal electricity only; device capex and subscriptions are excluded for both lanes.
- Grid: 0.367 kg CO2e/kWh, $0.13/kWh.
- Rubric 1.0.1: negation-aware guardrail matching was fixed after round 1 and re-applied uniformly to every deck before v1.1 ran. The rubric was frozen for v1.1.
- Blind judge: one vision-capable subagent scored anonymized contact sheets; round 2 mixed v1.1 with re-ID'd round-1 anchors so drift is measurable. Anchors are the same images, so recall is possible. Round 3 (held-out) used fresh IDs, the same rubric and anchors from all three configs; its instructions said brief facts are the only allowed numbers, so the judge also docked the measured provenance numbers (Zava v1.1 anchor, Woodgrove v1.1). That is a small penalty against v1.1 that drift adjustment only partly offsets.
- "Training" = prompt/program distillation (deck arc, analogy bank, exemplars, lint + repair loop) from frontier decks and judge feedback. Model weights were not changed.
- Teaching-to-the-test risk: the v1.1 lint enforces word budgets, analogy cues and icon counts that the auto rubric also measures, so part of the auto-score gain is expected by construction. The blind judge never saw the rubric or lint; use judge-only numbers as the primary quality comparison. Both briefs informed v1.1; section 7 tests generalization on three held-out briefs.
- v1.1 adds a measured provenance slide when a brief lists the made_on_device topic (Zava, Woodgrove); its numbers are appended to the grading facts as measured telemetry.
- Held-out runs have no cloud comparison decks; the held-out cost ratio uses the benchmark-brief cloud median.
- Templates are inspired by Microsoft / Surface styling, not official brand assets. Clients are fictional.
