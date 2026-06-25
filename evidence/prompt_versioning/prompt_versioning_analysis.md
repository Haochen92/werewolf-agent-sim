# Prompt Versioning & Model Tagging — Claims Analysis + Implementation

**Date:** 2026-06-06
**Branch:** `feature-tracing`
**Trigger:** External advice claiming (a) prompt engineering is model-specific, so the unit of
reproducibility is the bundle *prompt version + pinned model + generation params*; (b) Langfuse
prompt management is built around exactly this (auto-versioning, config-with-prompt, trace
correlation). Task: verify the claims against our versions, decide what applies to our
prompts-as-code setup, implement the minimal defensible fix.

---

## 1. Claims verification

### Claim: "Langfuse versions prompts with model+config, correlates with traces" — TRUE for our versions, with a load-bearing caveat

Verified against the installed stack (Python SDK 3.14.6, self-hosted OSS server v3.155.1):

- The SDK has full prompt management: `create_prompt` / `get_prompt` / `update_prompt` with
  auto-incrementing versions, labels (`production` etc.), tags, commit messages, and a `config`
  field that versions model + params together with the prompt text (SDK `client.py:3798-3851`).
- Prompt management is MIT-core in OSS — not enterprise-gated. (Since June 2025 all Langfuse
  product features are MIT; the EE list is admin-ware: SCIM, audit logs, RBAC, *protected* prompt
  labels.)
- Prompt→trace correlation is mechanically real in our stack: the installed
  `langfuse/langchain/CallbackHandler.py:416` reads a `langfuse_prompt` metadata key and links
  generations to a prompt version; the observation schema has `promptId/promptName/promptVersion`
  fields (confirmed present, and null, on our live generations).

**The caveat:** linking requires passing a `PromptClient` from `get_prompt()` — it only works if
prompts *live in Langfuse prompt management*. The "manage model+config in one place" story assumes
prompts-as-managed-artifacts. It does not apply automatically to prompts-as-code.

### Claim: "Pin the model API version explicitly" — already maximally satisfied for the game model; one real violation found

Queried Vertex directly (`client.models.list/get`):

- `gemini-3.1-flash-lite` (game model): **no dated snapshot exists** for the 3.x series — the GA
  ID is the most specific identifier Google exposes (only a floating `-preview` sibling exists).
  The `gpt-4o` → `gpt-4o-2024-11-20` analogy does not transfer to Vertex; there is nothing more
  pinned to switch to.
- `DEFAULT_PRO_BACKUP_MODEL = "gemini-pro-latest"`: **a genuine floating alias**, used as the
  post-game extraction backup (`extraction.py:110`). That's the memory pipeline — the one that
  conditions Phase B gold labels. Google can retarget the alias silently mid-labelling.

### Claim: "MCP lets AI interact with Langfuse directly" — exists, prompt-management-centric

Official MCP server is built into the Langfuse server at `/api/public/mcp` (streamableHttp): list/
get prompts, `createTextPrompt`, `updatePromptLabels`; limitation: only `production`-labeled
prompts are served. Community MCPs exist for trace querying. None of this changes the
prompts-as-code calculus — our scripts already use the full REST API via `lf.api`, which is
strictly more capable.

---

## 2. Audit: what was recorded before this change

| Layer | Recorded | Missing |
|---|---|---|
| Per-generation (auto, langchain callback) | model name, temperature, langgraph node | thinking level |
| Trace metadata (`build_game_config`) | game_id + all game/memory/rerank/filter configs | model, params, backend, git SHA, prompt version; `release` field unused (null) |
| `run_batch` JSONL | configs, winner, transcript, metrics, timestamps | model, params, backend, code version — **a January record vs a June record could be different models and nothing in the file would show it** |

That last cell was the glaring eval hole: batch JSONLs (the input to win-rate A/Bs) were not
self-describing. The backend gap compounds it — Google AI vs Vertex give different outputs at
temp=0 (established project lesson), backend is decided by env sniffing, and it was recorded
nowhere.

---

## 3. Decision: runtime fingerprint, not Langfuse prompt management

Our prompts are compositional Python: `build_system_prompt(PREAMBLE, ROLE_CORE_STRATEGY, identity,
TONE, FORMAT)` assembled per node, 9 roles × day/night/vote/memory-pipeline templates across 8
modules in `Agents/prompts/`. Migrating to Langfuse PM's flat-template model would be a large
refactor, would create a second source of truth alongside git, and collides with the prompt freeze.
Git already versions the prompts with full fidelity — what was missing was the **runtime stamp
linking each result to the bundle**, not a prompt store.

Strongest argument against this choice: we forgo the Langfuse UI's per-prompt-version filtering and
the playground round-trip. Accepted because (a) the `release` field gives commit-level filtering in
the UI, which is the granularity we actually compare at (we change prompts via commits, not via UI
edits), and (b) PM can be revisited at the v5 rebuild for the few *flat* templates if UI iteration
ever becomes the workflow.

---

## 4. What was implemented (plain language + exact mechanics)

All changes are metadata-only plumbing — zero effect on any prompt or model output (except the
backup-model pin, which only changes behavior on a path that previously pointed at a floating
alias). Prompt-freeze safe.

### 4.1 `Agents/run_fingerprint.py` (new)

One module, three functions:

- `git_revision()` — current commit SHA + a `git_dirty` flag. Dirty counts **modified tracked
  files only** (`git status --porcelain --untracked-files=no`); untracked evidence/logs don't
  invalidate the SHA as a code version. Cached per process so a mid-run commit can't change the
  stamp.
- `prompt_bundle_hash()` — SHA-256 over `Agents/prompts/*.py` contents (sorted, name+bytes),
  truncated to 16 hex chars. This is the prompt surface *as content*: it changes on any prompt
  edit, including uncommitted ones the git SHA alone would miss. Together, `(git_commit,
  git_dirty, prompt_bundle_hash)` make prompt provenance airtight.
- `runtime_fingerprint()` — resolves the full generation bundle the same way the model factories
  do (same env vars, same defaults, **imported** constants — so the stamp can't drift from
  behavior): game/pro/backup model IDs, temperature, three thinking levels, backend
  (vertex/google), vertex location, embedding model + dims.

Example output:

```json
{
  "git_commit": "6262eb28…", "git_dirty": true, "prompt_bundle_hash": "f2183cbab31d0534",
  "llm_backend": "vertex", "game_model": "gemini-3.1-flash-lite", "temperature": 1.0,
  "game_thinking_level": "minimal", "summary_thinking_level": "medium",
  "judge_thinking_level": "minimal", "pro_model": "gemini-2.5-pro",
  "pro_backup_model": "gemini-3.5-flash", "embedding_model": "gemini-embedding-001",
  "embedding_dims": 1536, "vertex_location": "global"
}
```

### 4.2 Wiring

- **Langfuse traces** (`Agents/tracing.py`): `LANGFUSE_RELEASE` is set to the git SHA before the
  client initializes (the OTel resource is created once per process; `setdefault` preserves
  explicit overrides) → every trace gets the first-class, UI-filterable `release` field. The full
  fingerprint goes into the `metadata` key of the `RunnableConfig` returned by
  `build_game_config` → lands in trace metadata as `runtime_fingerprint`.
- **Batch records** (`scripts/run_batch.py`): fingerprint resolved once per batch, printed at
  start, written into every success *and* error record as `runtime_fingerprint`.
- **Embedding constants** (`Agents/llm_factory.py` + `Agents/memory.py`):
  `DEFAULT_EMBEDDING_MODEL` / `DEFAULT_EMBEDDING_DIMS` hoisted to the factory; `memory.py` and the
  fingerprint both reference them. The vector store index is only valid for the embedding model
  it was built with, so this is part of the bundle.

### 4.3 Pin the floating alias (`Agents/agents.py`)

`DEFAULT_PRO_BACKUP_MODEL`: `"gemini-pro-latest"` → `"gemini-3.5-flash"`. Decision trail:
`gemini-3.1-pro-preview` (the alias's likely current target, class-matched) was considered and
rejected — preview tier means no SLA, silent behavior changes, and retirement risk, and this
project has already blacklisted one preview for API instability. `gemini-3.5-flash` is stable GA,
pro-comparable quality (project model notes rate it a toss-up with `gemini-2.5-pro`), and a
different model family/quota pool than the primary — so it remains a genuine fallback. Also
hoisted `DEFAULT_PRO_MODEL = "gemini-2.5-pro"` from an inline literal.

### 4.4 Verification (all live)

- Fingerprint resolves correctly under `.env` (output above; `git_dirty: true` correct for the
  feature branch in progress).
- Zero-cost trace smoke test (a `RunnableLambda` invoked through `build_game_config`'s config — no
  LLM calls): fetched back via API, trace shows `release = 6262eb28…` and the full
  `runtime_fingerprint` in metadata.
- Test suite: 27 passed. (5 errors in `tests/leak_test.py` are pre-existing on a clean tree — it's
  a live-game harness expecting a `prompt_log` fixture, unrelated.)
- `run_batch --dry-run` works; fingerprint import is deferred past dry-run exit.

---

## 5. Limitations and future options

Known gaps, in rough priority order; none block Phase B/C:

1. **Old data is unstamped.** Every existing trace and batch JSONL predates the fingerprint.
   Backfill is impossible (env state is gone). Mitigation: `batch_results/` is already flagged as
   mixed legacy data; treat fingerprint presence as the "citable" marker going forward.
2. **The fingerprint records *defaults as resolved at run time*, not per-call reality.** If a
   future code path overrides a model per-call (e.g. a one-off judge), the stamp won't see it.
   Per-generation Langfuse records (model, temp — auto-captured) remain ground truth at call
   granularity; the fingerprint is the *bundle declaration*. Acceptable while all factories route
   through the env-var pattern it mirrors.
3. **Thinking level still isn't in Langfuse `model_parameters`** (the langchain integration doesn't
   forward it). It IS now in the trace-level fingerprint, which is where comparisons happen.
   Per-generation thinking capture would need callback surgery — not worth it.
4. **Serving-stack drift is unobservable.** Even a pinned GA ID can shift behavior when Google
   updates the serving stack (same mechanism that invalidates caches — see
   `evidence/caching/report.md`). Uncontrollable; `started_at` timestamps
   make temporal confounds at least diagnosable. Operational rule: A/B arms run interleaved, not
   weeks apart.
5. **Dirty-tree runs are stamped but not blocked.** `git_dirty: true` + `prompt_bundle_hash` tell
   you exactly when a run isn't reproducible from a commit, but nothing stops such a run. A
   `--require-clean` flag on `run_batch` would be a 5-line follow-up if citable batches start
   getting polluted.
6. **Langfuse PM revisit-point = v5 rebuild.** If prompt iteration ever moves to UI-driven (e.g.
   for labelling-cycle prompt tuning), registering the few flat templates (extraction, judges) in
   PM and passing `langfuse_prompt` would light up the per-version trace filtering for those. The
   compositional game prompts should stay as code regardless.
7. **Structured-output schemas are part of the prompt surface** (`with_structured_output` Pydantic
   models shape behavior) but are not in `prompt_bundle_hash` — they live outside
   `Agents/prompts/`. They're covered by `git_commit` + `git_dirty`; folding schema modules into
   the hash is possible if schema-only edits ever become common.

## 6. The one-sentence position (for write-ups)

> Prompts are code, versioned in git; every trace and batch record carries the commit SHA, a
> prompt-bundle content hash, the pinned model IDs, sampling params, and API backend — because a
> result is only meaningful relative to the exact bundle that produced it. Langfuse prompt
> management was evaluated and deliberately skipped: our prompts are compositional code, and a
> runtime fingerprint gives the same reproducibility guarantee without maintaining a second source
> of truth.
