"""Class-3 evaluation home: do the RULERS measure what they claim?

Distinct from ``audits/`` ("is the SYSTEM behaving as recorded" — re-runnable $0 checks over game
records). This package validates the MEASUREMENT instruments themselves; since 2026-11-18 only the
situation-dimension checks remain (the proxy, credit, tagger and power subpackages were removed; the
git tag pre-test-cut-2026-11-18 keeps them).

Two governing rules (see README):
  1. Standing vs dated = "would you run it again on purpose?" Standing validation methods live here and
     must import cleanly against current code; dated one-shots stay in ``evidence/`` as records.
  2. Adoption promotes the COMPUTATION; discovery stays as the RECORD. When a validation method becomes
     the current way we re-certify a ruler, its code graduates here; the evidence folder that
     discovered it keeps the narrative + a one-line graduation pointer.

Subpackage: ``dimensions`` (v6 dim accuracy + gating screen).
"""
