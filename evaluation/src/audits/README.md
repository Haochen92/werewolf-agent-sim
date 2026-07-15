# `audits/` — is the SYSTEM behaving as recorded?

Re-runnable **$0** checks that the system's recorded behavior still holds — regression checks over game
records. Every module here is recompute-only (**ZERO LLM, no network**): given a new `batch_results/`
batch it re-derives the same structural / behavioral fact, so an audit that passed on the frozen epoch
can be re-run as a regression check on any later run.

The identity contrast:

- **`audits/`** — the **SYSTEM** is behaving as recorded (deterministic behavioral facts over records).
- `instrument_validation/` — the **RULERS** measure what they claim (validating the measurement
  instruments themselves).
- `studies/` — concluded one-shot design screens.

## Modules

| module | what it checks |
|---|---|
| `scheduler_access_audit` | does the role-blind scheduler starve specific roles' floor access? |
| `whiff_conversion_audit` | does an attacker convert a silent SK night-immune whiff into action? |
| `recall_flags` | deterministic pivotal-turn flagger (recall attention anchor). |
| `dedup_score` | golden-label scorer for the dedup classifier (console `eval-dedup-score`). |
| `batch_dedup_score` | golden-label scorer for the batch (cluster-merge) dedup pass. |
| `embedding_canary` | deterministic embedding-drift check — re-embed pinned strings, compare to `embedding_canary_pins.json`. |
| `role_hallucination_screen` | candidate screen for role-fact hallucinations in agent messages (dead-role misstatement, dead-as-alive, composition counts, claim attribution) vs the structured death/claim timeline; recall-oriented — a confirming read supplies precision (console `eval-role-hallucination`; record: `evidence/generation_prompt/validation/`). |

All are pytest-covered; batch-record loading is shared via `data/sources/batch_records.py`.

## How to run

Package modules, from the repo root:

```bash
poetry run python -m evaluation.src.audits.scheduler_access_audit
poetry run python -m evaluation.src.audits.whiff_conversion_audit
poetry run python -m evaluation.src.audits.recall_flags
poetry run python -m evaluation.src.audits.batch_dedup_score
poetry run python -m evaluation.src.audits.embedding_canary
```

The dedup classifier scorer also has a console entry:

```bash
poetry run eval-dedup-score
```
