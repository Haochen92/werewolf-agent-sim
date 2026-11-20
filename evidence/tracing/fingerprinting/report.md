# Experiment provenance: how it works

**Scope:** the configuration, runtime fingerprint and artifact-manifest mechanisms that identify what
produced a game or evaluation result.

**Version.** Revised on 2026-11-16, when the prompt hash began covering every prompt source file
and the fingerprint gained `fingerprint_schema` (§4.2), and when the backend field began to be read
from the game model's id (§4.3, schema 3). Both changes are commit `26959b87`. The rest was re-verified on 2026-10-26 against the code at
`5d8ea41c`; the first audit was on 2026-07-23. This report describes the implementation as it is now, including its gaps. The
chronological reasoning is in [`experiment_log.md`](experiment_log.md). Results stamped with an older
fingerprint belong to the code that stamped them.

> **The 30-second mental model**
>
> ```text
> RunConfig             = what we asked the experiment to do
> Runtime fingerprint   = which code, prompts, and model environment executed it
> Artifact manifest     = which input files and evaluation settings produced an output file
> ```
>
> A trustworthy result needs all three. None of them is a substitute for the other two.

---

## 1. The current contract

The provenance system makes experiment drift visible. It records enough information to answer
three practical questions:

| Question | Mechanism |
|---|---|
| What behavior did we request? | `RunConfig` and its serialized run record |
| Which implementation and model environment ran it? | `runtime_fingerprint` |
| Which concrete files fed a derived artifact? | artifact manifest with input hashes |

### What it guarantees

- A clean `git_commit` identifies the committed repository snapshot.
- `git_dirty` tells the reader when tracked files differed from that commit.
- The prompt bundle hash identifies the covered prompt-source files by content.
- The principal model IDs, temperature, thinking settings, backend field and embedding settings are
  recorded.
- Batch game records and the capture scripts' manifests carry the resolved runtime fingerprint.
- Experiment folders record the resolved run configuration and fingerprint in `config.json`.
- Evaluation manifests make it possible to detect when an input file changes while keeping the
  same filename.

### What it does not guarantee

- **A served game carries no fingerprint at all** (§2).
- A dirty run cannot be reconstructed from `git_commit` plus `git_dirty=True`; the diff is not
  stored.
- The prompt hash covers the prompt source under `Agents/prompts/` only. Model-visible text that
  lives elsewhere, such as the structured-output schemas, is outside it (§4.2).
- A record stamped before 2026-11-16 carries a prompt hash over the top-level prompt files only (14 of
  them on that date), so it cannot be compared with a newer hash (§4.2).
- A record stamped before 2026-11-16 (`fingerprint_schema` below 3) says `vertex` or `google` in its
  backend field even when the game model is Claude (§4.3).
- A remote model provider can change serving behavior behind a stable model name.
- The shared artifact manifest does not include the complete runtime fingerprint.
- The fingerprint is a run-level declaration. Langfuse generation records remain the source for
  the exact model call at one invocation, and a prompt capture for the prompt input
  ([tracing report](../report.md)).

The accurate claim is therefore **drift-evident provenance**, not byte-for-byte reproducibility.

## 2. What the fingerprint covers on each path

Games run on two paths ([tracing report](../report.md)), and only one is stamped.

| Path | Where the fingerprint is written | What else identifies the run |
|---|---|---|
| `run_batch` games | Every game record, success or error; the experiment folder's `config.json`; the run metadata passed to the Langfuse callback | The commit as the trace's `release` field |
| Capture scripts (`evaluation/experiments/`) | Each game's `<label>.manifest.json` | The same manifest also lists the modified and untracked files and the LangGraph version |
| Learning-loop runs | The game records, through `run_batch` | Checked between games by `evaluation/src/loop/invariants.py::assert_fingerprint_consistent` |
| Served games | Nowhere: `GameSession` calls `build_runnable_config(run)` with no metadata | The `games` row (model, whether the player paid, the memory switch, the seats); the deploy log's image commit, matched by date; from the next deploy, the trace's `release` field |
| Evaluation outputs (artifact manifests) | Only `git_commit` and `git_dirty` | The literal evaluation config and the input hashes (§6) |

**Served games.** The trace's release stamp is set once, when the process builds its Langfuse client
(`Agents/tracing.py::init_tracing`, or `get_langfuse()` on first use; since commit `9a22bfd6` nothing is
built at import). It takes `LANGFUSE_RELEASE` if set, else the commit from git. The deployed server
image holds `Agents/` and `server/` without the repository and sets no `LANGFUSE_RELEASE`, so its stamp
reads `unknown`. This was checked in the trace store on 2026-11-16: of the 30 most recent game traces,
all 14 hosted ones carry `unknown` and all 16 command-line and batch ones carry a commit id.

Since commit `68845870` the image takes the commit as a build argument, `GIT_COMMIT`, and sets it as
`LANGFUSE_RELEASE` (`Dockerfile`, `docker-compose.yml`). A build without the argument still stamps
`unknown`. This takes effect at the next deploy and is not deployed yet. It fixes the trace's release
field only: a served game still carries no fingerprint.

The settings a served game ran with follow from its row and the code at that build
(`server/game/run_config.py::game_run_config`), so the missing piece is which build it was: the deploy
log names each server image's commit and date ("2026-10-26 server rebuilt at `2ecec0cc`"), and a game
is matched to the image live on the day it was created. The log gives dates, not times.

A capture-script manifest shows the batch-side stamp as written. Game `phase3_games/game1` (2026-10-09,
so schema 1: no `fingerprint_schema` field, and a prompt hash over the top-level files only):

```json
{"git_commit": "9aef645780f654e8dcd48096f01a4e1e0e2eec99", "git_dirty": true,
 "prompt_bundle_hash": "efd7cd1e423abe60", "llm_backend": "vertex",
 "game_model": "gemini-3.5-flash-lite", "temperature": 1.0, "game_thinking_level": "medium",
 "summary_thinking_level": "medium", "judge_thinking_level": "minimal",
 "pro_model": "gemini-2.5-pro", "pro_backup_model": "gemini-3.5-flash",
 "embedding_model": "gemini-embedding-2", "embedding_dims": 1536, "vertex_location": "global"}
```

The same manifest lists the 184 paths `git status` reported as modified or untracked at the time; a
`run_batch` record keeps only the `git_dirty` flag.

## 3. How the pieces travel through one run

The entry point first resolves the requested settings:

```text
RunConfig
  ├── game rules
  ├── memory/reranking/filtering arms
  ├── stage filter, deduction mode, persona voices
  ├── persistence settings
  ├── game ID
  └── session ID
```

`build_runnable_config()` converts those settings into LangGraph's transport. On its own it adds no
observability; the entry point injects the callbacks and the fingerprint metadata:

```text
RunnableConfig
  ├── configurable
  │     └── serialized RunConfig fields
  ├── metadata
  │     └── runtime_fingerprint      (added by run_game and the capture scripts)
  ├── callbacks
  │     └── Langfuse callback        (run_game; the server adds its own)
  └── recursion_limit
```

The graph receives the settings under `configurable`. The fingerprint reaches the Langfuse callback as
run metadata. Separately, `run_batch` writes the same fingerprint into every success or error record.

For an experiment (the default layout; `--flat` writes the older flat files instead), the output folder
is:

```text
batch_results/<experiment>/
  config.json
  summary.json
  games/<session>.jsonl
  eval_cases/<session>/<game>.jsonl
```

`config.json` contains the resolved experiment recipe and runtime fingerprint. Each game record
also carries the fingerprint, allowing evaluation code to reject records from a different
execution bundle.

## 4. Runtime fingerprint: the execution-bundle label

`Agents.run_fingerprint.runtime_fingerprint()` combines three groups of fields. Its first field,
`fingerprint_schema`, says which definition of the fingerprint the record follows (§4.2).

### 4.1 Source identity

`git_revision()` runs:

```bash
git rev-parse HEAD
git status --porcelain --untracked-files=no
```

It produces:

```json
{
  "git_commit": "<full commit SHA>",
  "git_dirty": false
}
```

Interpretation:

| State | Meaning |
|---|---|
| Known commit, clean tree | The committed source can be reconstructed exactly from Git |
| Known commit, dirty tree | The commit is a baseline; the executed tree had unrecorded tracked edits |
| Unknown commit | Git was unavailable or the command failed (this is the served image's case) |

Untracked files do not set `git_dirty`. This avoids marking ordinary result artifacts as source
changes, but it also means an untracked Python module can affect execution without appearing in
this signal.

`git_revision()` is cached once per process. A long-running process keeps the same source label even
if someone commits or edits files afterward. Normally Python has already imported the running code,
but the cache is still part of the contract.

### 4.2 Prompt-source identity

`prompt_bundle_hash()`:

1. Lists every `.py` file under `Agents/prompts/`, in all folders, skipping `__pycache__/` and
   `goldens/`.
2. Sorts them.
3. Hashes each file's path inside the prompts folder (for example `roles/healer.py`) and its raw
   bytes with SHA-256.
4. Stores the first 16 hexadecimal characters.

Conceptually:

```python
digest = sha256()
for file in sorted(prompts_dir.rglob("*.py")):     # minus __pycache__/ and goldens/
    digest.add(file.relative_to(prompts_dir).as_posix())
    digest.add(file.bytes)
prompt_bundle_hash = digest.hex()[:16]
```

Including the path prevents two layouts with identical bytes from receiving the same bundle hash.
The path is used rather than the bare file name because names repeat across folders: two files
called `context.py` in different folders must not hash alike. Hashing raw source also catches
uncommitted edits to covered files.

This is a source hash, not a rendered-prompt hash. A comment-only change alters it even though the
model sees the same text. Runtime data can also change rendered prompts without changing the source
hash; that variation belongs to the game record, the prompt capture and the individual Langfuse
generation.

#### Coverage

On 2026-11-16 the hash covers 39 of the 41 `.py` files under `Agents/prompts/`:

```text
Agents/prompts/*.py              14 files: shared rules and layout, day and night templates,
                                 formatters and prompt inputs, voices
Agents/prompts/roles/*.py        14 files: 13 role cards, one per ten-seat role and the pack,
                                 and the package's __init__.py
Agents/prompts/extraction/*.py    7 files: the extraction and day-summary prompts
Agents/prompts/memory/*.py        4 files: the memory lookup's prompts
```

It leaves out `Agents/prompts/goldens/` (2 files). That folder holds the stored texts of a prompt
snapshot test and the script that writes them. Only that test imports it
(`tests/engine/test_game_rules_render.py`); no game code reads it, and its texts are never sent to a
model. The rules it stores are built from the role cards, which the hash already covers.

Model-visible text also comes from outside `Agents/prompts/`: the structured-output schemas
(`Agents/schemas/`) and the deduction engine's rendered lines (`Agents/deduction/render.py`). These
are not in the hash. A change to them moves `git_commit`, or sets `git_dirty` if uncommitted.

#### Before 2026-11-16: top-level files only

Until 2026-11-16 the hash listed only the top-level `Agents/prompts/*.py` files (14 on that date) and keyed
each by its bare file name. The role cards, the extraction prompts and the memory prompts were outside
it, so two runs with the same hash may have read different role cards.

Records stamped before that date carry a hash computed that way. An old hash and a new one therefore
differ for that reason alone, even when no prompt text changed. On the same tree the old definition
gave `6876d34cb388c496` and the new one gives `4f1fb31086c1c5a6`. The `fingerprint_schema` field tells
the two apart: a record with `fingerprint_schema` 2 or higher uses the new definition, and a record with no
such field is schema 1. Compare prompt hashes only between records of the same schema.

### 4.3 Model environment

`runtime_fingerprint()` imports defaults from `Agents.llm_factory` and resolves selected environment
variables. It records:

| Field | Meaning | Default on 2026-10-26 |
|---|---|---|
| `llm_backend` | The service the game model is routed to: its id's prefix (`anthropic`, `deepseek`, `openrouter`…), or for a bare Gemini id `vertex` or `google` | `anthropic` |
| `game_model` | Main game model (`GOOGLE_GENAI_MODEL`) | `anthropic/claude-haiku-5-5` |
| `temperature` | Shared generation temperature | 1.0 |
| `game_thinking_level` | Game turn reasoning setting, from the environment or the model's catalogue row | The model's row, else `minimal` |
| `summary_thinking_level` | Day-summary reasoning setting | `medium` |
| `judge_thinking_level` | Lightweight judge reasoning setting | `minimal` |
| `pro_model` | The offline extraction model | `anthropic/claude-sonnet-5-5` |
| `pro_backup_model` | Its backup | `anthropic/claude-haiku-5-5` |
| `embedding_model` | Embedding model (`MEMORY_EMBEDDING_MODEL`) | `qwen/qwen3-embedding-8b` |
| `embedding_dims` | Vector dimensions | 1536 |
| `vertex_location` | Vertex region, present only when the backend is `vertex` | (absent) |

The defaults have been Claude models since 2026-10-15, when the Gemini credits ran out
(`Agents/llm_factory/accessors.py`, comment at `DEFAULT_GAME_MODEL`). The fingerprint mirrors the
factory's original Google and Vertex paths, and it is not a complete description of the newer ones:

- **In records stamped before 2026-11-16 the backend field is wrong for every non-Google model.**
  `llm_backend` then resolved only Google versus Vertex. Since schema 3 it follows the game model's
  id, as `create_chat_model` routes it. The experiment `v8_demo_0` (Claude Haiku 5.5, 2026-10-14) shows `"backend": "vertex"`
  in its `config.json` overview, and the voice game `voices-01.off` (Claude Haiku 5.5, 2026-10-18)
  records `"llm_backend": "vertex"` in its manifest. The model name, which carries the provider
  prefix, is the reliable field.
- **The rescue model is not recorded.** A seat whose model stalls or keeps breaking the schema hands
  the turn to the rescue model (`GAME_FALLBACK_MODEL`, default Claude Sonnet 5.5).
- **Per-model catalogue settings are not recorded,** apart from the thinking level: for example how a
  model is asked for structured output.
- Dedup and some study models have their own per-run settings, and per-call overrides are not
  discovered automatically.
- **A setting is recorded, not its effect.** On 2026-10-04 a probe found that the "minimal" thinking
  level gave `gemini-3.1-flash-lite` no reasoning at all, while every record said "minimal"
  ([experimental controls](../../evaluation/experimental_controls/report.md) §4).

The safe maintenance rule is: **when model construction gains a new behavioral input, either add it
to the fingerprint or record it in the literal run/evaluation configuration.**

## 5. RunConfig: what the experiment requested

`RunConfig` (`Agents/config/run.py`) is deliberately separate from the runtime fingerprint.

It contains:

- `GameConfig`;
- memory-enabled roles;
- reranking, filtering, and retrieval-type settings;
- the stage filter, the deduction mode (and its per-side override) and the persona voices;
- memory persistence settings;
- strategy-point tiering flags;
- the human seat, if any;
- `game_id`;
- `session_id`.

These values answer questions such as:

- Was memory enabled for villagers?
- Which store was seeded?
- How many vigilante bullets did the game start with?
- Which game ID seeded the deal?

Those are experimental choices, not source-code identity.

`build_runnable_config()` serializes nested Pydantic models to plain dictionaries because graph
nodes read `config["configurable"]` directly. Callbacks and fingerprint metadata are injected by
the caller, keeping the configuration package independent from tracing:

```python
run = RunConfig(...)
config = build_runnable_config(
    run,
    callbacks=[create_langfuse_handler()],
    metadata={"runtime_fingerprint": runtime_fingerprint()},
)
```

**Where the requested settings are written.** Each `run_batch` game record carries the memory,
reranking, filtering, retrieval-type, game and persistence settings. The stage filter, the deduction
mode and the voices are in the experiment's `config.json` only, so a `--flat` run keeps no record of
them. A capture script's manifest holds the whole `RunConfig`. A served game's settings follow from its
row and the code (§2).

## 6. Artifact manifests: linking outputs to concrete inputs

A runtime fingerprint identifies a run. An artifact manifest links a derived file to the exact
files it consumed.

`evaluation.src.core.manifest` records:

```json
{
  "artifact": "path/to/output.jsonl",
  "created_at": "...",
  "git_commit": "...",
  "git_dirty": false,
  "config": {
    "judge_model": "...",
    "seed": 42
  },
  "config_sha256": "...",
  "inputs": [
    {
      "path": "path/to/input.jsonl",
      "sha256": "...",
      "count": 130
    }
  ]
}
```

The path makes the input easy to find. The hash makes the link verifiable. If someone regenerates
the input under the same path, recomputing SHA-256 reveals that the old result described different
bytes.

### Why two manifest carriers exist

- A JSON object already has an envelope, so provenance can be embedded under `_manifest`.
- JSONL is a stream of peer records. Adding a special metadata line would force every reader to
  treat line one differently, so JSONL uses `<artifact>.manifest.json` beside the data file.

### Current boundary

The shared manifest includes `git_commit` and `git_dirty`, but not `runtime_fingerprint`. Model
settings may appear in its literal evaluation config when the caller supplies them. This is not
the uniform full-bundle manifest envisioned by the earlier design rationale.

Batch experiment folders are richer: their `config.json` stores both resolved configuration and
runtime fingerprint. Readers should not assume every `_manifest` or `.manifest.json` has that same
shape.

## 7. What a fingerprint can and cannot prove

### Clean source tree

```text
git_commit = abc123
git_dirty  = false
```

Git can recover the committed repository. The runtime fingerprint then adds a convenient prompt
signal and the principal model environment.

This is the strongest supported case.

### Dirty source tree

```text
git_commit = abc123
git_dirty  = true
```

The code differs from commit `abc123`, but the record does not say how. Covered prompt edits may be
distinguished by `prompt_bundle_hash`; other code edits are not reconstructable. (A capture-script
manifest at least lists which files were modified.)

The correct interpretation is "known to have drifted," not "exactly reproducible."

### Same fingerprint, different provider behavior

A remote provider can update the implementation behind a stable model ID. Timestamps and
interleaved A/B arms reduce this risk, but the local code cannot hash a provider's private serving
stack.

The target is therefore statistically comparable reruns from a drift-checked setup, not identical
tokens.

### A matching fingerprint as a refactor gate

On 2026-06-08 two commits replaced the per-role day and night node functions with factories, a change
meant to alter no behavior. It was accepted on three checks: 95 passing tests, an import sweep with no
failures, and a runtime fingerprint the record calls byte-identical (`prompt_bundle_hash
c35e68e2d0cca9f0`) ([node factory record](../../refactor/node_factory_pattern.md)). Since the fingerprint
includes the commit, two commits cannot match in full; the comparison left the git field out. The
same day's companion commit says so: "runtime_fingerprint (minus git) byte-identical" (`fbe4cff1`).

What the matching fingerprint showed is narrow: the covered prompt files and the model setup were
unchanged, so any change in behavior would have to come from the refactored code, which the tests
covered. The fingerprint cannot see tracing, so the span names were checked separately, by reading the
code that builds them. The case shows the fingerprint used as one gate among several, not as proof of
equivalence on its own.

### Two runs compared by a person

Within one learning-loop run, a change in the fingerprint between games stops the run
(`assert_fingerprint_consistent`). Across runs nothing stops automatically; a person compares the
fingerprints ([experimental controls](../../evaluation/experimental_controls/report.md)). With the
backend field wrong for Claude in records below schema 3, that comparison has to read the model name,
not the backend. The
prompt hash can be compared only when both records carry the same `fingerprint_schema`; for a record
stamped before 2026-11-16 it has to read the commit instead, since the role cards were outside the
old hash.

## 8. Verification currently in the repository

| Contract | Current verification |
|---|---|
| Root runnable config keeps its serialized shape; with injection, the metadata holds only `runtime_fingerprint`; the bare builder injects no observability | `tests/engine/test_run_config_contract.py` |
| Child configs preserve every top-level field, the metadata included | `tests/engine/test_child_config_unit.py` |
| Input-file content changes alter artifact hashes; config hashes are stable and content-addressed; the sidecar and the embedded `_manifest` are written | `tests/evaluation/test_manifest.py` |
| Loop records: the first stamp is read, a missing stamp raises, a backend flip mid-run raises, unstamped records are skipped | `tests/evaluation/test_loop_invariants.py` |
| The experiment overview takes the model, backend and commit from the fingerprint | `tests/evaluation/test_batch_layout.py` |
| The prompt hash is stable over one tree, changes with a nested file, tells same-named files in different folders apart, and ignores `__pycache__/` and `goldens/`; the fingerprint carries `fingerprint_schema` first; the backend field follows the game model's id (added 2026-11-16, on a temporary prompts folder) | `tests/engine/test_run_fingerprint.py` |
| Fingerprint reaches runtime metadata | Indirectly, by the run-config contract; live-smoked in June 2026 |

These tests are largely AI-written and not yet audited.

What is missing is just as important, re-checked on 2026-11-16:

- no focused tests for `git_revision()`;
- no test that the real prompts folder holds no prompt source the hash skips (the tests above use a
  temporary folder);
- no test comparing fingerprint model fields with instantiated model settings;
- no carrier test proving one fingerprint reaches both a trace and a batch record.

## 9. Maintenance guide

### When adding or moving prompt files

Discovery is recursive, so a new `.py` file anywhere under `Agents/prompts/` joins the hash on its
own, except under `goldens/`. Moving or adding a file changes the hash even when no prompt text
changes, because the path is hashed.

1. Keep prompt source under `Agents/prompts/`. Text placed elsewhere is not in the hash.
2. Do not put prompt text a model reads under `goldens/`; that folder is skipped.
3. If the rule for which files are covered changes, bump `fingerprint_schema` (below).

### When adding a model or backend

1. Identify the canonical code that resolves the backend and model.
2. Make the fingerprint consume that resolved representation rather than reimplementing the rules.
3. Add a test for the new selection path.
4. Never record credentials or API keys.

### When changing the fingerprint definition

Bump `FINGERPRINT_SCHEMA` in `Agents/run_fingerprint.py` and add a dated entry to the log. Schema 1
is any record with no such field (prompt hash over top-level files only); schema 2 began on
2026-11-16 (all prompt source, keyed by path); schema 3 began the same day (`llm_backend` read from
the game model's id). Without the bump, a reader cannot tell "prompt content
changed" from "the hash began covering more files".

Within one learning-loop run, the drift guard compares whole fingerprints, so a run resumed across a
schema change stops. That is the intended behavior: restart the run.

### When adding a configuration field

Ask which category it belongs to:

- Requested experiment behavior → `RunConfig` or evaluation config.
- Shared implementation/model identity → runtime fingerprint.
- Input/output relationship → artifact manifest.

Avoid putting a field into all three without a clear reason.

### Before a citable experiment

1. Require or verify a clean Git tree.
2. Save the resolved `RunConfig`.
3. Save the runtime fingerprint.
4. Hash every external input or store snapshot.
5. Keep the input artifacts, not only their hashes.
6. Interleave experimental arms to reduce provider-time drift.

## 10. Known gaps

Each gap was re-checked against the code on 2026-10-26 (first verified 2026-07-23), with its
consequence. On 2026-11-16 the nested-prompt gap and the missing schema version were closed (§4.2),
and the backend field was corrected for new records (§4.3);
the gaps below remain.

### Old records carry the narrower prompt hash

Records stamped before 2026-11-16 (no `fingerprint_schema` field) hash only the top-level prompt
files. **Consequence:** for those records, equal hashes do not mean equal role cards, extraction
prompts or lookup prompts. Read their commit instead. The old records are not re-stamped.

### Prompt text outside `Agents/prompts/` is not hashed

The structured-output schemas and the deduction engine's rendered lines reach the model but sit
elsewhere (§4.2). **Consequence:** a change there moves only the git fields.

### Served games are not stamped

A served game carries no fingerprint. Its trace's release field reads `unknown` today (checked
2026-11-16); the image builds from commit `68845870` onward stamp the commit there, from the next
deploy. **Consequence:** until then a result from a served game can be tied to its code only through
the deploy log's dates (§2), and a game played on a day with two deploys cannot be placed from the
record. After it, the trace names the commit, but the game record still has no model or prompt
fields.

### Backend and model resolution drift from the factory

The fingerprint reads environment variables and private factory helpers on its own. **Consequence:**
neither the rescue model nor a served game's model selection appears in it (§4.3), and a record
below schema 3 labels a Claude game `vertex` or `google`. Since 2026-11-16 the backend field uses the
factory's own reading of the model id; the other fields are still resolved separately.

### Dirty runs are not reconstructable

Dirty status is recorded but the diff is not. **Consequence:** a result from a dirty tree is known to
have drifted from its commit, by an unknown edit. A `--require-clean` policy for citable batches is
likely simpler than serializing arbitrary source changes. The capture scripts' manifests list the
modified files, which narrows the search but does not restore the edit.

### Artifact manifests omit the full runtime fingerprint

The shared manifest carries Git, config and input hashes; batch experiment folders carry the richer
fingerprint separately. **Consequence:** an evaluation output names its commit but not its model setup,
unless its config lists the models.

### Prompt hash is truncated to 64 bits

Sixteen hexadecimal characters are enough to detect accidental drift at this project's scale, but the
field should not be presented as a collision-resistant archival identifier.

### Remote serving-stack drift is unobservable (inherent)

A stable provider model name does not freeze the provider's private implementation. This is mitigated
operationally through timestamps, pinned names where available, and interleaved comparisons.

## 11. The code, re-derived from the contract

An equivalent implementation can be reconstructed from four operations:

```python
def build_provenance(run):
    settings = serialize(run)
    source = read_git_revision()
    prompts = hash_defined_prompt_tree()
    models = read_canonical_resolved_model_settings()

    fingerprint = {
        "fingerprint_schema": CURRENT_SCHEMA,
        **source,
        "prompt_bundle_hash": prompts,
        **models,
    }

    return {
        "run_config": settings,
        "runtime_fingerprint": fingerprint,
    }
```

Derived artifacts add one more operation:

```python
manifest = {
    "config": literal_eval_config,
    "config_sha256": hash_canonical_json(literal_eval_config),
    "inputs": [hash_file(path) for path in input_paths],
    "runtime_fingerprint": fingerprint,
}
```

Since 2026-11-16 the code hashes the whole prompt tree and carries the schema field. It still falls
short in three places: model settings are read beside the factory rather than from it, shared
artifact manifests carry only the Git subset of the runtime fingerprint, and a served game makes no
`build_provenance` call at all.

That difference is intentional in this report. The pseudocode is the target contract; the gap list
states exactly where today's implementation falls short.
