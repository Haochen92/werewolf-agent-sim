"""The v7 generational compounding-loop harness (play → extract → credit → consolidate → measure).

A generational A/B — memory-ON vs a flat memory-OFF baseline — that asks whether an agent learning from
its own games slopes UP across generations. One harness, every lever toggleable via ``LoopConfig``. See
README.md for the cycle diagram, the per-module roles, and the go-live seam: the memory-pipeline half
(``consolidate`` store ops, the ``credit``/``credit_backfill`` logic, ``merge``, ``discussion_tagger``)
graduates to ``Agents/memory/``; the eval half (``driver``/``measure``/``invariants``/``cost``) stays.
"""
