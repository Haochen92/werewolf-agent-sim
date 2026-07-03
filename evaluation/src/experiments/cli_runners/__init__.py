"""The runnable eval commands — thin CLIs over the primitives (``judges/`` + ``replay/``).

Each command reads a frozen dataset, optionally replays a pipeline stage (``replay/``),
optionally scores it (an LLM ``judges/`` grader or a deterministic ``audits/`` scorer),
and writes JSONL. The logic lives in the primitive packages; these files only wire
config -> data -> primitive -> output, which keeps ``judges/`` and ``replay/`` free of
the data-plane dependencies a CLI needs.

Runners are grouped into three subpackages by what they do (filed by capability — a
runner that *can* do both lives in ``both/`` even if a config mode exercises only one):

  ``regen/``   regenerate an output, no judge — the model-swap dataset producers
               (``extraction_regen``, ``dedup_regen``)
  ``judge/``   judge a captured output, no regeneration
               (``extraction_judge``, ``dedup_judge``)
  ``both/``    regenerate a stage AND judge/score it — ``turn_eval`` (the merged
               captured/action/e2e runner), ``situation_summary_rubric`` / ``_pairwise``,
               ``retrieval``, ``day_summary_judge``, ``batch_dedup_judge``
"""
