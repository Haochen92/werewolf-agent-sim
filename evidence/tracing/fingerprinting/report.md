# Experiment Provenance — How It Works

**Scope:** the configuration, runtime fingerprint, and artifact-manifest mechanisms that identify
what produced a game or evaluation result.

**Current-state audit:** 2026-07-23. This report describes the implementation as it exists now,
including known gaps. The chronological reasoning is in [`experiment_log.md`](experiment_log.md).

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
- Principal model IDs, temperature, thinking settings, backend, and embedding settings are
  recorded.
- Batch game records carry the resolved runtime fingerprint.
- Experiment folders record the resolved run configuration and fingerprint in `config.json`.
- Evaluation manifests make it possible to detect when an input file changes while keeping the
  same filename.

### What it does not guarantee

- A dirty run cannot be reconstructed from `git_commit` plus `git_dirty=True`; the diff is not
  stored.
- The current prompt hash does not include nested prompt packages.
- A remote model provider can change serving behavior behind a stable model name.
- The shared artifact manifest does not currently include the complete runtime fingerprint.
- The fingerprint is a run-level declaration. Langfuse generation records remain the source for
  the exact rendered prompt and model call seen at one invocation.

The accurate claim is therefore **drift-evident provenance**, not byte-for-byte reproducibility.

## 2. How the pieces travel through one run

The entry point first resolves the requested settings:

```text
RunConfig
  ├── game rules
  ├── memory/reranking/filtering arms
  ├── persistence settings
  ├── game ID
  └── session ID
```

`build_runnable_config()` converts those settings into LangGraph’s transport:

```text
RunnableConfig
  ├── configurable
  │     └── serialized RunConfig fields
  ├── metadata
  │     └── runtime_fingerprint
  ├── callbacks
  │     └── Langfuse callback
  └── recursion_limit
```

The graph receives the settings under `configurable`. Langfuse receives the fingerprint through
metadata. Separately, `run_batch` writes the same kind of fingerprint into every success or error
record.

For an experiment launched with `--experiment`, the output folder is:

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

## 3. Runtime fingerprint: the execution-bundle label

`Agents.run_fingerprint.runtime_fingerprint()` combines three groups of fields.

### 3.1 Source identity

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
| Unknown commit | Git was unavailable or the command failed |

Untracked files do not set `git_dirty`. This avoids marking ordinary result artifacts as source
changes, but it also means an untracked Python module can affect execution without appearing in
this signal.

`git_revision()` is cached once per process. A long-running process keeps the same source label even
if someone commits or edits files afterward. Normally Python has already imported the running code,
but the cache is still part of the contract.

### 3.2 Prompt-source identity

`prompt_bundle_hash()` currently:

1. Lists top-level `Agents/prompts/*.py` files.
2. Sorts them.
3. Hashes each filename and its raw bytes with SHA-256.
4. Stores the first 16 hexadecimal characters.

Conceptually:

```python
digest = sha256()
for file in sorted(top_level_prompt_files):
    digest.add(file.name)
    digest.add(file.bytes)
prompt_bundle_hash = digest.hex()[:16]
```

Including filenames prevents two differently named source layouts with identical bytes from
receiving the same bundle hash. Hashing raw source also catches uncommitted edits to covered files.

This is a source hash, not a rendered-prompt hash. A comment-only change alters it even though the
model sees the same text. Runtime data can also change rendered prompts without changing the source
hash; that variation belongs to the game record and individual Langfuse generation.

#### Current coverage gap

The discovery pattern is non-recursive. It does not include:

```text
Agents/prompts/extraction/*.py
Agents/prompts/memory/*.py
```

The dedicated prompt hash is therefore narrower than the whole prompt surface. Git still detects
committed changes and marks tracked uncommitted changes as dirty, but `prompt_bundle_hash` itself
does not change for those nested files.

### 3.3 Model environment

`runtime_fingerprint()` imports defaults from `Agents.llm_factory` and resolves selected environment
variables. It currently records:

| Field | Meaning |
|---|---|
| `llm_backend` | `vertex` or `google`, as inferred by `_use_vertex()` |
| `game_model` | Main game model |
| `temperature` | Shared generation temperature |
| `game_thinking_level` | Main game reasoning setting |
| `summary_thinking_level` | Day-summary reasoning setting |
| `judge_thinking_level` | Lightweight judge reasoning setting |
| `pro_model` | Higher-capability model |
| `pro_backup_model` | Backup higher-capability model |
| `embedding_model` | Embedding model constant |
| `embedding_dims` | Vector dimensions |
| `vertex_location` | Vertex region when Vertex is selected |

This mirrors the central model factory for the original Google/Vertex paths. It is not yet a
complete description of every newer path:

- NIM and Mistral models are selected by model-name prefixes, but `llm_backend` still resolves only
  Google versus Vertex.
- Dedup and some study models have their own per-run settings.
- Per-call overrides are not discovered automatically.

The safe maintenance rule is: **when model construction gains a new behavioral input, either add it
to the fingerprint or record it in the literal run/evaluation configuration.**

## 4. RunConfig: what the experiment requested

`RunConfig` is deliberately separate from the runtime fingerprint.

It contains:

- `GameConfig`;
- memory-enabled roles;
- reranking, filtering, and retrieval-type settings;
- memory persistence settings;
- strategy-point tiering flags;
- `game_id`;
- `session_id`.

These values answer questions such as:

- Was memory enabled for villagers?
- Which store was seeded?
- How many vigilante bullets did the game start with?
- Which game ID seeded deterministic scheduling?

Those are experimental choices, not source-code identity.

`build_runnable_config()` serializes nested Pydantic models to plain dictionaries because graph
nodes read `config["configurable"]` directly. Callbacks and fingerprint metadata are injected by
the caller, keeping the configuration package independent from tracing.

The older `Agents.tracing.build_game_config()` remains as a compatibility wrapper. New code should
prefer the explicit composition:

```python
run = RunConfig(...)
config = build_runnable_config(
    run,
    callbacks=[create_langfuse_handler()],
    metadata={"runtime_fingerprint": runtime_fingerprint()},
)
```

## 5. Artifact manifests: linking outputs to concrete inputs

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

## 6. What a fingerprint can and cannot prove

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
distinguished by `prompt_bundle_hash`; other code edits are not reconstructable.

The correct interpretation is “known to have drifted,” not “exactly reproducible.”

### Same fingerprint, different provider behavior

A remote provider can update the implementation behind a stable model ID. Timestamps and
interleaved A/B arms reduce this risk, but the local code cannot hash a provider’s private serving
stack.

The target is therefore statistically comparable reruns from a drift-checked setup, not identical
tokens.

## 7. Verification currently in the repository

| Contract | Current verification |
|---|---|
| Root runnable config retains its historical serialized shape | `tests/test_run_config_contract.py` |
| Child configs preserve opaque LangGraph fields | `tests/test_child_config_unit.py` |
| Nested subgraph interrupts pause and resume | `tests/test_subgraph_interrupt.py` |
| Input-file content changes alter artifact hashes | `tests/test_manifest.py` |
| Manifest config hashes are deterministic | `tests/test_manifest.py` |
| Loop records reject a different fingerprint on resume/append | `tests/test_loop_invariants.py` |
| Fingerprint reaches runtime metadata | Indirectly checked by the run-config contract; historically live-smoked |

What is missing is just as important:

- no focused tests for `git_revision()`;
- no prompt-bundle coverage or determinism tests;
- no test comparing fingerprint model fields with instantiated model settings;
- no carrier test proving one fingerprint reaches both a trace and a batch record.

## 8. Maintenance guide

### When adding or moving prompt files

1. Confirm that prompt discovery includes the new path.
2. Add a test that changes that file and observes a new bundle hash.
3. Record a hash-definition transition if coverage changes without model-visible text changing.

The preferred future implementation is recursive and path-aware:

```python
for path in sorted(prompts_dir.rglob("*.py")):
    relative = path.relative_to(prompts_dir).as_posix()
    digest.update(relative.encode())
    digest.update(path.read_bytes())
```

### When adding a model or backend

1. Identify the canonical code that resolves the backend and model.
2. Make the fingerprint consume that resolved representation rather than reimplementing the rules.
3. Add a test for the new selection path.
4. Never record credentials or API keys.

### When changing the fingerprint definition

Add an explicit schema version before relying on comparisons across the change:

```json
{
  "fingerprint_schema": 2
}
```

Without a schema version, a reader cannot distinguish “prompt content changed” from “the hashing
algorithm began covering more files.”

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

## 9. Known gaps

Severity considers likelihood, impact, and how easily the problem is detected.

### Nested prompt packages are omitted — severity: high

**Verified open 2026-07-23.** The code uses `glob("*.py")`, while prompt source exists in
`prompts/extraction/` and `prompts/memory/`. A nested prompt change does not update the dedicated
prompt hash. Git gives a secondary signal, so the failure is detectable but easy to misread.

### Dirty runs are not reconstructable — severity: medium-high

**Verified open 2026-07-23.** Dirty status is recorded but the diff is not. Detection is strong;
reconstruction is absent. A `--require-clean` policy for citable batches is likely simpler than
serializing arbitrary source changes.

### Backend/model resolution can drift from the factory — severity: medium-high

**Verified open 2026-07-23.** The fingerprint independently reads environment variables and private
factory helpers. New NIM/Mistral support demonstrates how duplicated resolution logic can become
incomplete.

### Artifact manifests omit the full runtime fingerprint — severity: medium

**Verified open 2026-07-23.** The shared manifest carries Git/config/input hashes. Batch experiment
folders carry the richer fingerprint separately. This is usable but not a single uniform contract.

### Fingerprint definition has no schema version — severity: medium

**Verified open 2026-07-23.** Past content-neutral bundle expansions required narrative transition
notes. A schema field would make these changes machine-readable.

### Prompt hash is truncated to 64 bits — severity: low

**Verified open 2026-07-23.** Sixteen hexadecimal characters are sufficient for ordinary accidental
drift detection at this project’s scale, but the field should not be presented as a
collision-resistant archival identifier.

### Remote serving-stack drift is unobservable — inherent

**Verified open 2026-07-23.** A stable provider model name does not freeze the provider’s private
implementation. This is mitigated operationally through timestamps, pinned names where available,
and interleaved comparisons.

## 10. The code, re-derived from the contract

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

The current code is close to this model but does not yet implement every line: prompt-tree
discovery is non-recursive, there is no fingerprint schema field, and shared artifact manifests
carry only the Git subset of the runtime fingerprint.

That difference is intentional in this report. The pseudocode is the target contract; the gap list
states exactly where today’s implementation falls short.
