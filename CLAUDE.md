# Werewolf Agent Sim

## Environment

- Always use `poetry run` to execute Python commands (e.g. `poetry run python -c "..."`, `poetry run pytest`).
- Do not use bare `python` or `pip` — the project uses Poetry for dependency management.

## Commit Patterns

- When committing, break changes into incremental commits in logical dependency order — commit the foundation first, then what builds on it.
- Even if many files changed together, group them into commits by what was done, not by when it was done.
- Each commit should represent one coherent step that makes sense on its own.

## Versioning Design Variants (config flag vs worktree-on-tag)

This is an iteration-heavy eval project — many versions of many components. To keep an old design
*runnable for comparison*, pick the tool by the shape of the difference. (Git history preserves old
designs for free; this is about *running* them, not preserving them.)

- **Config flag (DEFAULT).** Use when variants COEXIST in production, are compared REPEATEDLY, and
  differ INCREMENTALLY (small surface). E.g. reranker v4/v5, per-role memory on/off, `top_k`. Select
  the implementation behind a stable interface via config; one harness runs both → fair A/B.
- **Git worktree on an annotated tag.** Use when the variant will be DELETED (not production-bound),
  the comparison is ONE-SHOT/occasional, and the difference is STRUCTURAL (graph/schema/prompt
  rewrite). E.g. concurrent↔sequential discussion. Don't force structurally divergent dead code to
  coexist in main just to delete it after one comparison.
  - `git tag -a <name>-baseline <commit>` BEFORE merging the redesign (annotate with backend; the
    committed `poetry.lock` travels with the tag — the env is fragile, so an old checkout must still
    install). Tag, not branch, for a frozen point.
  - `git worktree add ../ww-<name> <name>-baseline` to run it; `git worktree remove` when done.

- **Fair-comparison rule:** "never compare across harnesses" is about the MEASUREMENT harness, not the
  GENERATION harness — the variants ARE the generation harness and are supposed to differ. Judge both
  output sets with ONE judge (from main), post-hoc, pinning everything except the design
  (model/backend/temp/seeds/N). Structural redesigns are a fresh-generation A/B, not a frozen replay.
