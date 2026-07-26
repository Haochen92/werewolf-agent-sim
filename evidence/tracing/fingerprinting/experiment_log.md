# Experiment Provenance — Build Journey

> **What this is.** This is the chronological record of how the project learned to identify what
> produced an experiment result. It follows the work from the original tracing gap, through runtime
> fingerprinting and artifact manifests, to the ownership audit on 2026-07-23.
>
> Later entries supersede earlier claims. In particular, the first implementation was correct for a
> flat prompt directory, but later prompt-package refactors created a coverage gap. That gap is kept
> in the story rather than edited away.
>
> **Companion document.** [`report.md`](report.md) describes the current system destination-first:
> what it records, where it records it, and what it still cannot guarantee.

---

## 1. The gap: results existed without a complete production label (2026-06-06)

The project already recorded useful experiment information. A game record contained its result,
session, memory arm, and game settings. Langfuse recorded individual model calls. This was a
defensible starting point: it was enough to debug a single run while the code and model environment
were still fresh in memory.

It was not enough for comparisons made weeks later. Two JSONL records could look comparable while
having been produced by different:

- source code;
- prompts;
- model names;
- temperatures or thinking settings;
- API backends.

The backend difference was not theoretical. The project had observed that Google AI and Vertex
could return different outputs even with temperature set to zero. A result therefore needed more
than a game configuration. It also needed a label for the implementation and model environment
that executed that configuration.

The root problem was simple: **the experiment recipe and the execution environment were recorded
in different places, and some parts were not recorded at all.**

## 2. Choosing prompts-as-code over a second prompt registry (2026-06-06)

The first investigation considered Langfuse prompt management. It provides named prompt versions
and can link a generation to a managed prompt. That is useful when prompt text lives in Langfuse.

This project’s prompts did not. They were Python modules assembled from shared rules, role text,
formatters, and runtime inputs. Moving them into a separate prompt registry would have created two
sources of truth:

1. Python code that assembled the prompt.
2. A second copy managed in Langfuse.

The project therefore kept Git as the source of truth for prompts.

This decision accepted a tradeoff. Langfuse would not provide a convenient prompt-version number
or playground round-trip. In return, the prompt text and the code that assembled it would remain
versioned together.

## 3. Deriving the first runtime fingerprint (2026-06-06)

Git already answered part of the question:

```text
git commit → exact committed repository snapshot
```

But a commit alone was insufficient during development. An experiment could run from a modified
working tree before those edits were committed. The initial design therefore added two source
signals:

```text
git_commit         = the current Git commit
git_dirty          = whether tracked files differ from that commit
prompt_bundle_hash = a content hash of the prompt modules
```

The prompt hash served a narrower purpose than the Git commit. It made prompt changes easy to spot
and changed for uncommitted edits inside the covered prompt directory. It did not replace Git.

The model environment formed the other half of the fingerprint. The implementation read the same
environment variables and default constants used by the model factory:

- game model;
- temperature;
- game, summary, and judge thinking levels;
- pro and backup models;
- Google or Vertex backend;
- Vertex location when applicable;
- embedding model and dimensions.

The resulting mental model was:

```text
runtime fingerprint
    = source identity
    + prompt-source identity
    + resolved model environment
```

### Alternatives rejected

**Git commit only.** Rejected because it could not identify uncommitted prompt edits and did not
record model/backend settings.

**Prompt hash only.** Rejected because prompts are not the whole program. State handling, schemas,
retrieval, and graph wiring can all change behavior.

**Copy every rendered prompt into the fingerprint.** Rejected because prompts vary by player and
game state. Langfuse already records individual model inputs; the fingerprint’s job is to label the
shared execution bundle.

**Move prompts into Langfuse.** Rejected because the prompts were compositional Python and Git was
already their authoritative store.

## 4. Implementing and attaching the fingerprint (2026-06-06)

Commit `31b2e8e` added `Agents/run_fingerprint.py` and wired its output into tracing and batch
records. The file contained three small functions:

1. `git_revision()` read the current commit and dirty status.
2. `prompt_bundle_hash()` hashed prompt-module filenames and bytes.
3. `runtime_fingerprint()` combined those values with resolved model settings.

The same work added two carriers:

- Langfuse received the Git commit through its first-class `release` field and the full fingerprint
  through runnable metadata.
- `run_batch` resolved a fingerprint once and wrote it into successful and failed game records.

This was metadata plumbing. It did not change the text sent to a model.

### Verification performed at the time

The original implementation record reported:

- a live fingerprint resolved from the environment;
- a zero-cost traced runnable whose Langfuse trace carried the release and metadata;
- the fingerprint appearing in batch output;
- the then-current test suite remaining green apart from pre-existing live harness errors.

These checks established that the stamp travelled through the intended paths. They did not prove
that every future prompt or model refactor would remain covered.

### Decision

The runtime fingerprint was adopted as the execution-bundle label. A result with a different
fingerprint was treated as belonging to a different experimental epoch unless someone established
that the difference was content-neutral.

## 5. Expanding the prompt surface to include rendering code (2026-06-10)

The first prompt hash covered the prompt modules but not all of the code that rendered runtime data
into model-visible text. A formatter edit could change what the model saw without changing the
prompt hash.

The formatter and prompt-input modules were moved into the flat `Agents/prompts/` directory. Since
the hash covered `Agents/prompts/*.py`, those modules then entered the bundle automatically.

This caused two content-neutral hash changes:

1. The files entered the covered directory.
2. One formatter file was renamed, and filenames participate in the hash.

The model-visible prompts were unchanged, but the bundle hash changed. Recording this transition
was important because a hash difference normally signals a prompt-surface difference.

The lesson was broader than this move: **a content hash only means something together with a stable
definition of which files it covers.**

## 6. Extending provenance from runs to artifacts (2026-06-10 onward)

The runtime fingerprint answered:

> Which implementation and model environment produced this run?

It did not answer:

> Which exact dataset did this evaluation result consume?

A filename was not sufficient. A file such as `sampled_v2.jsonl` could be regenerated under the
same name. An old result would still point to the path even though the bytes had changed.

The artifact-lineage design added content hashes:

```text
output artifact
    ├── literal configuration
    ├── configuration hash
    ├── Git revision
    └── input files
          ├── path
          ├── SHA-256
          └── record count
```

JSON objects could embed this information under `_manifest`. Envelope-less JSONL datasets used a
neighboring `.manifest.json` file so existing readers did not need to skip a special header line.

This design was subsequently implemented in `evaluation.src.core.manifest` and adopted by dataset
builders and evaluation-study scripts.

One intended connection did not fully land: the shared artifact manifest records the Git revision,
configuration, and input hashes, but it does not currently embed the complete runtime fingerprint.
The batch experiment folder does store the full fingerprint in `config.json`, and game records
store it directly. The two mechanisms are related, but they are not yet one uniform manifest
format.

## 7. Later refactors exposed assumptions in the first design (2026-06-16 onward)

The original prompt hash used:

```python
Agents/prompts/*.py
```

At the time, the important prompt modules were flat files in that directory. On 2026-06-16,
`extraction.py` and `memory.py` were split into nested packages:

```text
Agents/prompts/extraction/*.py
Agents/prompts/memory/*.py
```

The hash implementation continued using a non-recursive glob. Changes inside those packages no
longer changed `prompt_bundle_hash`.

Git still provided partial protection:

- A committed nested-prompt change changed `git_commit`.
- An uncommitted tracked change set `git_dirty=True`.

But the dedicated prompt identity no longer represented all prompt source. The old documentation’s
claim that it covered “all of `Agents/prompts/`” had become false.

Other changes created similar drift risks:

- The model factory added NIM and Mistral, while the fingerprint still reports only Google or
  Vertex as the backend.
- Some specialized model settings are supplied per call or per experiment and are not part of the
  shared fingerprint.
- Structured-output schemas affect model behavior but live outside the prompt directory.

No single later change was unreasonable. The failure was that the fingerprint’s coverage contract
existed only in prose; no focused tests failed when the surrounding architecture changed.

## 8. Separating run settings from runtime identity (current working tree, 2026-07-23)

The configuration refactor introduced a clearer split:

```text
RunConfig             = what this simulation was asked to do
runtime fingerprint   = which implementation/model bundle executed it
RunnableConfig        = the LangGraph transport carrying both
```

`RunConfig` contains game rules, memory-arm settings, persistence settings, and run identity.
`build_runnable_config()` serializes those settings into LangGraph’s `configurable` bag.
Observability injects the runtime fingerprint separately as metadata.

This is an improvement over the older `build_game_config()` function, whose name suggested game
rules while it also constructed callbacks, tracing metadata, IDs, and framework settings.

The old `build_game_config()` entry point remains as a compatibility wrapper. That is useful during
migration, but the conceptual ownership is now clearer:

- configuration owns requested behavior;
- fingerprinting owns execution identity;
- tracing transports and observes both.

## 9. Ownership audit and present decision (2026-07-23)

The ownership pass re-read the implementation rather than trusting the earlier “exact bundle” and
“airtight” descriptions.

### What remains sound

- A clean Git commit is a strong identifier for committed project source.
- Batch records and experiment configs carry a useful execution-bundle label.
- Explicit backend/model/temperature fields make many silent comparison errors visible.
- Content hashes are the right way to detect an input file changing under the same path.
- Keeping RunConfig separate from runtime identity is the correct boundary.

### What needs correction

- Prompt discovery must become recursive or be replaced by an explicit maintained file set.
- The hash definition should have a schema/version field so coverage changes are distinguishable
  from prompt changes.
- Backend resolution should come from the same canonical resolver used to instantiate the model.
- Fingerprint behavior needs direct tests.
- Citable dirty-tree runs should either be rejected or carry enough source information to
  reconstruct the exact tree.
- Artifact manifests should either embed the runtime fingerprint or state clearly that their Git
  stamp is narrower.

### Decision

Keep the feature, but narrow its claim until the gaps are fixed:

> The current runtime fingerprint is a useful drift detector and provenance label. It exactly
> identifies committed source only when the working tree is clean. Its dedicated prompt hash
> currently covers top-level prompt modules, not nested prompt packages.

This documentation rewrite does not silently change the implementation. It establishes an honest
contract from which the next code-and-test pass can be derived.

## 10. Lessons

**A fingerprint is a contract about coverage, not merely a hashing function.** The original hash
algorithm kept running after the directory layout changed. Without tests for the covered file set,
the code looked healthy while its meaning drifted.

**Configuration and provenance answer different questions.** A complete record needs both what was
requested and what executed it. Combining them in one loosely named dictionary obscures ownership.

**A clean source identifier is more valuable than a detailed dirty warning.** `git_dirty=True`
detects unreproducibility but does not cure it. For citable runs, preventing dirty execution may be
simpler and stronger than trying to serialize arbitrary working-tree changes.

**Record current truth separately from the journey.** Historical decisions explain why the design
exists. A reference report must still be refreshed against the implementation, because reasonable
later refactors can invalidate an earlier guarantee.

## Sources

- Runtime fingerprint implementation: `Agents.run_fingerprint`
- Run configuration and LangGraph adaptation: `Agents.config`
- Langfuse composition: `Agents.tracing`
- Batch carriers: `scripts.run_batch` and `evaluation.src.data.batch_layout`
- Artifact manifests: `evaluation.src.core.manifest`
- Fingerprint drift guard: `evaluation.src.loop.invariants`
- Original implementation commit: `31b2e8e`
- Original analysis commit: `6011dd1`
- Rendering-layer move: `b206747`
- Prompt-package splits: `815f014`, `c871e80`

