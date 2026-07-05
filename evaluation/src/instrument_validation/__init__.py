"""Class-3 evaluation home: do the RULERS measure what they claim?

Distinct from ``audits/`` ("is the SYSTEM behaving as recorded" — re-runnable $0 checks over game
records) and ``studies/`` (concluded one-shot design screens). This package validates the MEASUREMENT
instruments themselves — the de-luck proxies, the credit ledger, the discussion tagger, the situation
dimensions — and reserves the power/MDE gate.

Two governing rules (see README):
  1. Standing vs dated = "would you run it again on purpose?" Standing validation methods live here and
     must import cleanly against current code; dated one-shots stay in ``evidence/`` as records.
  2. Adoption promotes the COMPUTATION; discovery stays as the RECORD. When a validation method becomes
     the current way we re-certify a ruler, its code graduates here; the evidence folder that
     discovered it keeps the narrative + a one-line graduation pointer.

Subpackages: ``proxies`` (de-luck proxy monotonicity/rescue), ``credit`` (credit-signal validity),
``tagger`` (discussion-tagger accuracy/skill/deleak + effectiveness), ``dimensions`` (v6 dim accuracy +
gating screen), ``power`` (pre-registered power/MDE gate, no code yet).
"""
