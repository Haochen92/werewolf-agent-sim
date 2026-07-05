# `instrument_validation/` — do the rulers measure what they claim?

The **class-3** evaluation home. The pipeline has three kinds of self-checking code, one question each:

| package | question | re-run cadence |
|---|---|---|
| `audits/` | is the **system** behaving as recorded? | regression check on any new batch |
| `studies/` | (concluded) which **design** did we ship? | frozen — one-shot, kept for provenance |
| **`instrument_validation/`** | do the **rulers** measure what they claim? | standing — re-run to re-certify a ruler |

A "ruler" is a measurement instrument: a de-luck proxy, the credit ledger, the discussion tagger, a
situation dimension. This package validates the instruments, not the agents.

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

- **`proxies/`** — de-luck proxy validation.
  - `metrics_common.py` — shared N=180 v6ab loader + pre-registered 50/50 game_id split (used by the
    three rescue runners; import target `evaluation.src.instrument_validation.proxies.metrics_common`).
  - `proxy_win_monotonicity.py` — each de-luck proxy's point-biserial vs its own faction's win; a
    wrong-sign/~zero proxy shouldn't carry a win-rate narrative. (Promoted 2026-07-04 from
    `evidence/metrics/proxy_win_monotonicity.py`, which remains the dated record.)
  - `proxy_rescue.py` — rescue pass on the muted wolf-night / wrong-sign investigator proxies,
    conditioning on `sk_lynched` + game-length; split-half confirmed.
  - `accusation_metrics.py` — town accusation-graph proxies (precision / first-accuser / conversion).
  - `claim_conversion.py` — investigator find → next-round vote-convergence join.
  - `diagnose_wolf_sk_proxies.py` — wolf/SK proxy revalidation (point-biserial vs own-faction win,
    pooled + baseline-only) + the SK day-social harm channel, on the paired-A/B corpus. (Promoted
    2026-07-04 from `evidence/memory_system/effectiveness/paired_ab/`, which keeps the narrative.)
  - `leverage_anchor_separation.py` — validates the deterministic **leverage anchor** (`is_swing` /
    `distance_to_parity`): does the decision→outcome coupling concentrate at high-leverage boards? This
    is the pivotalness ruler the diagnosis sampler and extraction selection lean on. (Promoted
    2026-07-04 from `evidence/v7_final/`, which keeps the record.)
- **`credit/`** — credit-signal validity (does the loop's per-decision credit carry real signal, not
  the outcome halo?). `heldout_credit_reproduction.py`, `windowed_credit.py`, `g3a_verdict_validity.py`,
  and `g2_separability.py` (the G2 precondition — is a decision's outcome attributable ABOVE luck at
  all? re-run per epoch, promoted 2026-07-04 from `evidence/v7_final/`). Standing: these re-run after
  the planned §0.5 credit fixes.
- **`tagger/`** — discussion-tagger validation. `tagger_validation.py` is the config-driven apparatus
  (modes accuracy | skill | deleak) behind the `eval-tagger` console entry (thin CLI stays in
  `cli_runner/discussion_tagger_eval.py`). `tagger_effectiveness.py` is the standing halo /
  floor-redundancy + night read-quality de-luck check.
- **`dimensions/`** — v6 situation-dimension validation. `dimension_audit.py` ($0 fill-accuracy vs the
  case's own board), `dimension_gating_screen.py` (does soft dimension-gating cut retrieval waste? —
  concluded negative, RE-OPENED by the audit, so standing-again).
- **`power/`** — the pre-registered power / MDE gate (compounding plan §0.1). `mde_simulation.py` resamples
  the existing per-game de-luck scores (run-1 / v2 / v6ab), injects a known linear-in-generation effect, and
  reports detection rate + MDE across N∈{4,5,10,20}/gen × G∈{6,8,10} gens. $0, deterministic. Its dated
  readout lives at `evidence/execution_plan/power_analysis/mde_table.md`. Standing gate: no paid compounding
  run without a current MDE table.

## How to invoke

All runners are package modules; run from the repo root.

| runner | command | cost |
|---|---|---|
| proxy monotonicity | `poetry run python -m evaluation.src.instrument_validation.proxies.proxy_win_monotonicity` | $0 |
| proxy rescue | `poetry run python -m evaluation.src.instrument_validation.proxies.proxy_rescue` | $0 |
| accusation proxies | `poetry run python -m evaluation.src.instrument_validation.proxies.accusation_metrics` | $0 |
| claim conversion | `poetry run python -m evaluation.src.instrument_validation.proxies.claim_conversion` | $0 |
| wolf/SK proxy revalidation | `poetry run python -m evaluation.src.instrument_validation.proxies.diagnose_wolf_sk_proxies` | $0 |
| leverage-anchor separation | `poetry run python -m evaluation.src.instrument_validation.proxies.leverage_anchor_separation` | $0 |
| G2 separability | `poetry run python -m evaluation.src.instrument_validation.credit.g2_separability` | $0 |
| held-out credit | `poetry run python -m evaluation.src.instrument_validation.credit.heldout_credit_reproduction` | $0 |
| windowed credit | `poetry run python -m evaluation.src.instrument_validation.credit.windowed_credit` | $0 |
| verdict validity (G3a) | `poetry run python -m evaluation.src.instrument_validation.credit.g3a_verdict_validity` | $0 |
| dimension audit | `poetry run python -m evaluation.src.instrument_validation.dimensions.dimension_audit` | $0 |
| dimension gating screen | `poetry run python -m evaluation.src.instrument_validation.dimensions.dimension_gating_screen --batch … --store …` | paid (LLM judge) |
| tagger validation | `poetry run eval-tagger --config evaluation/config/template/tagger_eval_example.json` | paid on cache miss |
| tagger effectiveness | `poetry run python -m evaluation.src.instrument_validation.tagger.tagger_effectiveness` | paid (tags flash-lite) |
| power / MDE gate | `poetry run python -m evaluation.src.instrument_validation.power.mde_simulation` | $0 |
