"""Eval data plane — the build-time read side (see ``evidence/tracing/``).

- ``converters/``   span-dict → one typed ``*Case`` (pure, no I/O)
- ``sources/``      obtain raw span-dicts: ``sidecar`` (primary) | ``langfuse`` (fallback + cost)
- ``frozen_sets``   frozen eval-set record schemas + JSONL read/write
- ``sampling``      stratified subset selection for compact eval sets
- ``batch_layout``  write-side ``batch_results/`` output layout (generation side)
"""
