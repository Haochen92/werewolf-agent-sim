"""Case sources — obtain raw span dicts, then dispatch them to the converters.

Two implementations of one per-trace contract (``fetch_*_cases(trace_id)``):

- ``sidecar.LocalCaseSource`` — reads ``run_batch``'s local JSONL sidecars; the
  PRIMARY source (no Langfuse read; see the §4 fix in ``evidence/tracing/``).
- ``langfuse`` — fetches from Langfuse traces, the fallback for games predating
  local emission; also carries realized-cost capture.
"""
