"""The live command-line eval layer — one runnable entry per eval kind, grouped by what it does.

  ``regen_replay/``          frozen-case runners, filed by capability: ``regen/`` (regen-only) ·
                             ``judge/`` (judge-only) · ``both/`` (regenerate a stage AND score it)
  ``diagnosis/``             the case-sampler CLI (command wiring over the ``evaluation.src.diagnosis``
                             logic package — mirrors the ``regen_replay/judge`` ↔ ``judges/`` split)
  ``graduate_run``           promote a keeper eval run from scratch into the ``evidence/`` record
  ``discussion_tagger_eval`` validate the deceiver-side discussion tagger (accuracy / skill / deleak)

These are thin: each wires config → data → a ``replay/``/``judges/``/``audits/`` primitive → JSONL,
holding no eval logic itself. Concluded one-shot apparatus lives off this surface in ``../studies/``.
"""
