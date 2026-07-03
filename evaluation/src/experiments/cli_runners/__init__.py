"""The runnable eval commands — thin CLIs over the primitives (``judges/`` + ``replay/``).

Each module is a config/argv-driven command that reads a frozen dataset, optionally
replays a pipeline stage (``replay/``), optionally scores it (an LLM ``judges/`` grader
or a deterministic ``audits/`` scorer), and writes JSONL. Replay and judge are both
optional per runner — a runner may do one, the other, or both. The logic lives in the
primitive packages; these files only wire config -> data -> primitive -> output, which
keeps ``judges/`` and ``replay/`` free of the data-plane dependencies a CLI needs.

Modules:
  ``turn_eval``               one runner over a frozen turn: --replay {none|action|all}
                              x --judge {off|application|pipeline} (was captured/application/e2e)
  ``situation_summary_rubric`` / ``situation_summary_pairwise``  the two summary judging modes
  ``retrieval``               replay retrieval from a snapshot, judge relevance/redundancy
  ``*_judge``                 judge a component's frozen/replayed output (extraction/dedup/day_summary/batch_dedup)
  ``*_regen``                 regenerate a component with a different model into a new
                              dataset, no judge (the model-swap A/B tools)
"""
