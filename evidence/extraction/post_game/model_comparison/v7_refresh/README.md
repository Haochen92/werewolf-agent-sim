# v7 extraction model A/B — generated output (2026-06-19)

The real generated observations from the **v7-era model-capability A/B**, colocated here so the post_game
folder is self-contained with the refresh — the same way it holds the May per-model records one level up. This
A/B re-asked the model question the May bake-off answered, but on the **live v6_1 store** (not the v4-era
stores the May study used), because the v7 consolidation loop re-extracts every game, so the extraction-model
cost dominates the loop's recurring bill.

## Files

Three arms, re-extracted per-cell (v6 schema) on the **same 3-game v6ab slice** — `fa79dc3b` (serial_killer
win), `4999832f` (villagers), `e51e6b3b` (villagers). One JSON record per game, each observation tagged with
its source cell (`_cell_role` / `_cell_phase`).

| File | Model | Store | Obs (3 games) |
|---|---|---|---|
| `pro-2.5_3games_v6ab_20260619.jsonl` | gemini-2.5-pro (current live extractor) | `memory_stores/v6_1` | 144 |
| `flash-3.5_3games_v6ab_20260619.jsonl` | gemini-3.5-flash | `memory_stores/_ab_f35` | 165 |
| `flash-lite_3games_v6ab_20260619.jsonl` | gemini-3.1-flash-lite | `memory_stores/_ab_flite` | 123 |

## What it found (headline)

- **flash-3.5 ≈ pro.** The decisive evidence was a manual read across all three on the same games/cells: all
  identify the same critical observations (the SK's fatal vote-record, the Investigator mislynch), with
  flash-3.5 at 165 obs ≥ pro's 144. **flash-lite is correct but thin** (123 — drops some secondary lessons).
- **The parse-based recall metric was verbosity-confounded and overturned by the read.** It scored flash-lite
  25% vs pro 100% on flagged pivotal turns, but on the heavily-flagged SK night cell flash-lite captured the
  same kill sequence as pro — the metric only credits obs that state a parseable alive-count, which pro's
  verbose situations do and flash-lite's terse ones do not. Trust the read, not the metric.
- **The binding lever is synthesis, not extraction.** Extraction correctly recorded that passivity hurt the SK,
  while the synthesized strategy point inverted it (halo-keyed) — so the loop's real spend belongs on the
  synthesis fix, and the cheaper loop path is flash-3.5 (≈pro), not anchored/amplified flash-lite.

## Provenance and what is NOT copied here

- **Run:** 2026-06-19, Vertex backend, epoch-conditional (flash-lite drifts ~daily; never compare across
  backends). Design, kill-tests, and the full recall/amplify tables:
  [`../../../../v7_final/extraction_coverage_ab_spec.md`](../../../../v7_final/extraction_coverage_ab_spec.md).
  Scripts (study code, stays in `v7_final/`): `extraction_model_ab_compare.py` (model arm),
  `recall_capture_metric.py` (recall arm), `extraction_quota_screen.py` (free volume/distinctness).
- **Not copied:** the recall-lever variant stores (`_ab_flite_anchor`, `_ab_flite_amplify`) — both NULL results
  (the suggestive anchor and the amplify pass did not lift flash-lite's pivotal recall). They remain in
  `memory_stores/` and are pointed-at, not colocated.
- The narrative that cites these records: post_game [`experiment_log.md`](../../experiment_log.md) §8 and
  [`report.md`](../../report.md); the judge/measurement view: the apparatus report
  [`../../../../evaluation/llm_judge/extraction.md`](../../../../evaluation/llm_judge/extraction.md).
