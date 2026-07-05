"""Re-runnable $0 checks that the SYSTEM is behaving as recorded — regression checks over game records.

Every module here is recompute-only (ZERO LLM, no network): given a new ``batch_results/`` batch it
re-derives the same structural / behavioral facts, so an audit that passed on the frozen epoch can be
re-run as a regression check on any later run. Distinct from ``studies/`` (concluded one-shot design
screens) and from ``instrument_validation/`` (validating that the RULERS measure what they claim —
these audits ask only whether the system's recorded behavior still holds).

The per-module inventory + how-to-run lives in README.md.
"""
