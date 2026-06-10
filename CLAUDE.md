# Werewolf Agent Sim

## Environment

- Always use `poetry run` to execute Python commands (e.g. `poetry run python -c "..."`, `poetry run pytest`).
- Do not use bare `python` or `pip` — the project uses Poetry for dependency management.

## Schema / State Field Docs (IDE hover)

Field-level docs on `Agents/schemas/` and `Agents/state/` use **attribute docstrings** (a bare
`"""..."""` on the line AFTER the field) — Pylance surfaces these on hover; `#` comments and
`Field(description=)` are NOT surfaced. **`use_attribute_docstrings` stays FALSE** (never set it),
so Pydantic ignores docstrings and they can never reach a model. The rule: **docstrings are for
humans, `Field(description=)` is for the model — they never cross.**

- TypedDict states + internal Pydantic schemas → attribute docstrings (internal schemas drop the
  now-unused `Field(description=)`; keep `Field(default_factory=...)` for mutable defaults).
- **Model-visible / FROZEN** (`output.py`; extraction/rerank models in `memory.py`; `AddressedTarget`)
  → keep `Field(description=)`; **NEVER add a class docstring** (it folds into the JSON schema sent to
  the model → leaks). The doc style itself marks the leak boundary.
- `typeCheckingMode` stays **off** — hover/autocomplete don't need it, and `basic` mode surfaces a
  large LangGraph `add_node`-stub error floor on this codebase (not worth it as a gate).

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

## Eval Architecture (`evaluation/` = code · `evidence/` = record · data plane = I/O)

Three layers, one rule each — keeps the authoritative pipeline clean while preserving the iteration
journey. (Full data-flow + folder taxonomy: the **Data plane** section in `evaluation/README.md`.)

- **`evaluation/` is the single home for authoritative eval CODE** — one canonical runner per eval
  kind; this is what v5 runs on. `scripts/` holds ONLY generation entry (`run_batch`, `analyze_batch`)
  + one-off ops — never reusable eval logic.
- **`evidence/<experiment>/` is the RECORD, never a home for code.** Narrative
  (`experiment_log.md` / `report.md`) + data artifacts + a POINTER back to the `evaluation/` code that
  produced it. The provenance manifest's `runtime_fingerprint` (git SHA) + embedded config IS that
  pointer — **store the pointer, not a copy of the function.**
- **The live data plane** (`eval_configs/ eval_sets/ eval_results/ batch_results/`) is just pipeline
  I/O between them.

**Lifecycle.** *Explore* → a thin runner in `evaluation/experiments/` from the start (reusing
`components/`/`judges/`), output to `evidence/<experiment>/`. *Graduate* (becomes the v5 way) → runner
goes config-driven + canonical, README names it, evidence folder points at it. *Supersede* → delete
the old runner (git history keeps it) OR keep it runnable per the Versioning Design Variants policy
above; the old evidence folder is untouched. **The journey is told by records + git history, not by
live dead code** — so `evaluation/` stays clean/singular while the portfolio narrative lives in the
dated `evidence/` folders and commits.

**Existing `evidence/` (pre-standard): FREEZE, don't retrofit.** The accumulated archive is the honest
journey — *including* any study code embedded in it, which is itself a dated artifact of how the eval
was done then. Do NOT bulk-hoist old study code into `evaluation/` (it would pollute the authoritative
pipeline with superseded methods AND erase the record). Promote ONLY code that is still the *current*
authoritative method (rare — `evaluation/` is already mature). Graduation is JUST-IN-TIME: when a
study's method becomes part of v5, its code moves to `evaluation/` as part of building v5, and its
evidence folder gets a one-line "graduated to `evaluation/X`" note. No bulk sweep, no upfront audit.
