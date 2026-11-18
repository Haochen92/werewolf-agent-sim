# `audits/` — is the SYSTEM behaving as recorded?

Re-runnable **$0** checks that the system's recorded behavior still holds — regression checks over game
records. Every module here is recompute-only (**ZERO LLM, no network**): given a new `batch_results/`
batch it re-derives the same structural / behavioral fact, so an audit that passed on the frozen epoch
can be re-run as a regression check on any later run.

The identity contrast:

- **`audits/`** — the **SYSTEM** is behaving as recorded (deterministic behavioral facts over records).
- `instrument_validation/` — the **RULERS** measure what they claim (validating the measurement
  instruments themselves).

## Modules

| module | what it checks |
|---|---|
| `dedup_score` | golden-label scorer for the dedup classifier (console `eval-dedup-score`). |
| `batch_dedup_score` | golden-label scorer for the batch (cluster-merge) dedup pass. |
| `embedding_canary` | deterministic embedding-drift check — re-embed pinned strings, compare to `embedding_canary_pins.json`. |
| `role_hallucination_screen` | candidate screen for role-fact hallucinations in agent messages (dead-role misstatement, dead-as-alive, composition counts, claim attribution) vs the structured death/claim timeline; recall-oriented — a confirming read supplies precision (console `eval-role-hallucination`; record: `evidence/gameplay/turn_prompt/validation/`). |

Batch-record loading is shared via `data/sources/batch_records.py`.

Three nine-seat audits (`scheduler_access_audit`, `whiff_conversion_audit`, `recall_flags`) were
removed on 2026-11-18; the annotated git tag `pre-test-cut-2026-11-18` holds them.

## How to run

Package modules, from the repo root:

```bash
poetry run python -m evaluation.src.audits.batch_dedup_score
poetry run python -m evaluation.src.audits.embedding_canary
```

The dedup classifier scorer also has a console entry:

```bash
poetry run eval-dedup-score
```
