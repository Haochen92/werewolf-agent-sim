# `instrument_validation/` — do the rulers measure what they claim?

The **class-3** evaluation home. The pipeline has two kinds of self-checking code, one question each:

| package | question | re-run cadence |
|---|---|---|
| `audits/` | is the **system** behaving as recorded? | regression check on any new batch |
| **`instrument_validation/`** | do the **rulers** measure what they claim? | standing — re-run to re-certify a ruler |

A "ruler" is a measurement instrument: a de-luck proxy, the credit ledger, the discussion tagger, a
situation dimension. This package validates the instruments, not the agents.

**Removed on 2026-11-18.** The `proxies/`, `credit/`, `tagger/` and `power/` subfolders, which
validated nine-seat and v7-loop instruments, were deleted. The annotated git tag
`pre-test-cut-2026-11-18` holds them (see "Removed on 2026-11-18" in `evaluation/README.md`). Only
`dimensions/` remains.

## Two governing rules

1. **Standing vs dated = "would you run it again on purpose?"** A standing validation method — one you
   would re-run to re-certify a ruler after the model, the record set, or the credit logic changes —
   lives here and **must import cleanly against the current code**. A dated one-shot (it settled a
   question once and won't be re-run) stays in `evidence/` as a record. Promotion into this package is
   exactly the act of making the stale-import-carrying evidence script run against current code again.
2. **Adoption promotes the COMPUTATION; discovery stays as the RECORD.** When a validation method
   becomes the current way we re-certify a ruler, its *code* graduates here. The `evidence/` folder that
   *discovered* it keeps the narrative + data + a one-line graduation pointer. We move the computation,
   not the story.

## Subfolder inventory

- **`dimensions/`** — v6 situation-dimension validation. `dimension_audit.py` ($0 fill-accuracy vs the
  case's own board), `dimension_gating_screen.py` (does soft dimension-gating cut retrieval waste? —
  concluded negative, RE-OPENED by the audit, so standing-again). Since 2026-11-18 the gating screen
  does not import: it reused helpers from `studies/` and `replay/decision_screen/`, which were removed.

## How to invoke

All runners are package modules; run from the repo root.

| runner | command | cost |
|---|---|---|
| dimension audit | `poetry run python -m evaluation.src.instrument_validation.dimensions.dimension_audit` | $0 |
| dimension gating screen | does not import since 2026-11-18 (see above) | paid (LLM judge) |
