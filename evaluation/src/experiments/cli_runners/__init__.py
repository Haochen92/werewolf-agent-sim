"""Thin CLI runners over the frozen-case eval primitives (``judges/`` + ``replay/``).

Each module here is a config/argv-driven command that reads a frozen dataset,
optionally replays a pipeline stage (``replay/``), scores it (an LLM ``judges/``
grader or a deterministic ``audits/`` scorer), and writes JSONL. The logic lives
in the primitive packages; these files only wire config -> data -> primitive ->
output, so they can hold no evaluation logic themselves (that keeps ``judges/``
and ``replay/`` free of the data-plane dependencies a CLI needs).

Naming:
  ``*_judge``                 score frozen (or replayed) cases with an LLM/rubric judge
  ``*_pairwise`` / ``*_rubric``  the two situation-summary judging modes
  ``*_regen``                 regenerate outputs with a different model into a new
                              dataset, no judge (the model-swap A/B tools)
"""
