# Artifact provenance & lineage — design rationale

**Date:** 2026-06-10
**Status:** Design rationale for the eval data-plane reorg (Wave 2). Not yet implemented. Companion
to [structure_audit.md](structure_audit.md) and the plan in `.claude/plans/`.
**Scope:** the *live* eval plane — `batch_results/`, `evaluation/frozen_eval_sets/`, `evaluation/eval_results/`. Not `evidence/`
(which keeps its self-contained experiment-folder convention).

---

## 0. TL;DR

- The data plane stamps lineage **into filenames** today (`dedup_v2_replay_flash_lite_prompt_v9d`).
  That bloats names, caps at whatever fits, and carries **no integrity guarantee** — a name can lie.
- The fix is **content-addressed lineage**: every artifact records its inputs by **sha256**, plus
  the code/config that produced it, in embedded metadata (JSON-object artifacts) or a sidecar
  manifest (envelope-less JSONL). Walk the hashes backward → reach the exact game that produced any
  number, and *detect* if any link silently drifted.
- This is the **gold standard for provenance**, which is a *necessary part* of reproducibility but
  not the whole of it. For an LLM-eval pipeline, full byte-reproduction is unreachable (remote
  models drift behind stable names; temp-0 differs across backends). The achievable, correct target
  is **"re-run from a provably identical, drift-checked setup and get a statistically equivalent
  result."**
- We are **completing, not inventing**: `runtime_fingerprint` already pins the code/prompt/model
  half; the `evidence/` golden labels already hash inputs (`frozen_artifacts {path, sha256, count}`).
  This unifies those two existing halves into one convention across the live plane.

---

## 1. Why this matters *for this project*

The whole point of the rebuild is a defensible **Phase C win-rate A/B** and a portfolio writeup that
claims results are reproducible. Both rest on one question being cheaply answerable for *any* number
we report:

> "This eval_result — which eval_set produced it, from which games, under which code, prompts,
> models, and config?"

Today that answer is reconstructed by **reading the filename and guessing**. That fails in the exact
ways that invalidate an eval:

- **Silent staleness.** A judge result references `dedup_v2_sampled.jsonl`. Someone later rebuilds
  that file (same name, new content). The result now describes inputs that no longer exist, and
  *nothing flags it*. In an A/B, that's a wrong number that looks fine.
- **Unbloatable names.** To make the filename self-describing we keep appending
  (`_35flash_prompt_v9d`). It still omits the git SHA, the backend, the temperature, the source
  games. The name can never hold the full bundle, so it holds an arbitrary, inconsistent subset.
- **No tamper/drift evidence.** Filenames are free-text. Two files named `..._v2` from different
  eras are indistinguishable; a copy with a hand-edited name is treated as authoritative.

The cost lands precisely where it hurts most: a plausible-but-wrong number in the experiment the
whole rebuild exists to run. (Same failure-mode family as the untested eval-critical paths in
[structure_audit.md](structure_audit.md) §3 — silent wrong numbers, not loud crashes.)

---

## 2. The ladder of solutions — simplest first, and what each one still gets wrong

Worth walking the rungs, because the hash isn't obviously necessary until you see what breaks
without it.

### Rung 0 — metadata in the filename (where we are)

`dedup_v2_replay_flash_lite_prompt_v9d.jsonl`

- **Pro:** zero machinery; the name is visible in `ls`.
- **Con:** bloats; truncates the bundle to an arbitrary subset; **no integrity** — the name is a
  human label, not a checked fact. This is the relic we're leaving behind.

### Rung 1 — a manifest that references inputs **by path**

Sidecar/embedded: `{ "input": "evaluation/frozen_eval_sets/dedup_v2_sampled.jsonl", "config": {…} }`

- **Pro:** names shrink to `<purpose>_vN`; the full config + model + git SHA live in structured
  metadata instead of the name. Already a large win for readability and completeness.
- **Con — the silent-drift hole:** a path is a *mutable pointer*. Regenerate the input under the
  same name and the manifest still "points" at it — now describing content that's gone. The link is
  present but **unverifiable**. This is the one failure that most threatens an A/B, and a path-only
  manifest does not close it.

### Rung 2 — reference inputs **by content hash** (the core trick)

`{ "inputs": [{"path": "evaluation/frozen_eval_sets/dedup/sampled_v2.jsonl", "sha256": "c13c…", "count": 130}] }`

- The path stays (human-findable); the **sha256 is the actual link.** To check a result is still
  valid: re-hash the file at that path and compare. Match → the result genuinely describes this
  file. Mismatch → **loud, automatic staleness signal**: "this result was computed against a
  different version of this input."
- **Pro:** drift-evident and tamper-evident. A renamed copy, a silent rebuild, a hand-edit — all
  caught by the hash, none caught by the name or the path. This is the rung that turns "lineage I
  *hope* is right" into "lineage I can *verify*."
- **Con:** the hash is opaque to the eye (you can't read provenance from `ls` anymore) — which is
  exactly why the path field stays alongside it, and why folder structure (not the filename) now
  carries human navigation.

> **This is the same principle as `poetry.lock` pinning a dependency by hash, or git referencing
> parent commits and trees by hash.** Content-addressing is how every serious lineage system
> (git, DVC, MLflow/W&B artifacts) makes "what produced this" tamper-evident rather than trusted.

### Rung 3 — embed the config + runtime fingerprint (re-runnable, not just identifiable)

`{ inputs:[…by hash…], config:{…literal…}, config_sha256, runtime_fingerprint:{git_sha, prompt_bundle_hash, model_ids, backend, params} }`

- **Pro:** the artifact is now not only *traceable* but *re-runnable* — the embedded literal config
  is the recipe; the fingerprint pins the environment. We embed the config **literally**, not as a
  path, because config paths drift too (Rung 1's hole again, one level up).
- **Con:** a few KB of duplicated metadata per artifact. Cheap, and the price of self-description.

We adopt **Rung 3**. Each rung above strictly closes a hole the previous one left; stopping earlier
leaves a known, A/B-relevant failure unguarded.

---

## 3. The chain it builds

```
eval_result ──embeds──▶ { config(literal), config_sha256, runtime_fingerprint,
                          inputs: [{path, sha256, count}] }          ← hashes the eval_set
       ▼
eval_set ──sidecar manifest──▶ { created_from:"<batch session>", runtime_fingerprint,
                                 inputs: [{path, sha256, count}] }    ← hashes / names the games
       ▼
batch_record ──already self-stamped──▶ { runtime_fingerprint, session_id, configs… }  ← the games
```

One hop per stage, each verifiable by re-hashing. Any result answers "what produced you" all the
way down to the raw game and the git SHA — and any broken link announces itself.

---

## 4. Provenance is not the same as reproducibility (the honest boundary)

It's tempting to call hash-linkage "reproducible." Precisely:

| | What it is | Do we get it? |
|---|---|---|
| **Provenance / traceability** | Identify exactly what produced an artifact; detect drift. | ✅ Fully — this is what hash-linkage delivers. |
| **Reproducibility** | Regenerate the artifact. | ⚠️ Partially, and that's inherent. |

Reproducibility needs three things provenance alone doesn't guarantee:

1. **Inputs preserved, not just hashed.** A hash identifies a file you no longer have. We already
   track `evaluation/frozen_eval_sets/` in git on purpose ([structure_audit.md](structure_audit.md) §1) — so inputs
   *are* kept; the hash makes that durable rather than assumed.
2. **Environment pinned.** Model IDs, backend, temperature, prompt bundle, git SHA — all already in
   `runtime_fingerprint`.
3. **Acceptance of irreducible nondeterminism.** LLM eval is **not** byte-reproducible: a remote
   model can change behind a stable name, and we have *measured* that temp-0 outputs differ across
   Google-AI vs Vertex backends. So byte-identity is
   the wrong target; **statistical equivalence from a provably identical, drift-checked setup** is
   the right one.

So: **hash-linked provenance + the existing fingerprint is about as strong as reproducibility gets
for an LLM-eval pipeline.** It guarantees you can always say *what* produced a number and *whether
anything drifted*, and re-run the exact recipe — while being honest that the model's own
nondeterminism, not our bookkeeping, is the floor on byte-identity.

---

## 5. How we implement it here

- **Hybrid embed vs sidecar — driven by whether the artifact has a JSON envelope.**
  - `evaluation/eval_results/*.json` (single object) and `batch_results` records → **embed** top-level keys.
    `batch_results` already does this; results just join the pattern.
  - `evaluation/frozen_eval_sets/*.jsonl` (N line-records, **no envelope**) → **sidecar** `<id>.manifest.json`. A
    header-line embed would force every reader to skip line 0 — a silent-corruption footgun across
    ~10 read-sites — for no gain. The sidecar leaves readers untouched and is already the
    convention (the 8 existing `.manifest.json`).
  - Folder structure (domain subfolders), **not** the filename, carries human navigation now.
- **One writer**, `evaluation/core/manifest.py`, reusing `Agents.run_fingerprint.runtime_fingerprint`,
  wired into the dataset builders (extend) and eval runners (new). Schema **aligns with the
  `frozen_artifacts {path, sha256, count}` shape the `evidence/` golden labels already use** — one
  convention, not a parallel invention.
- **Forward-only.** Legacy artifacts keep their missing lineage; the convention applies to net-new.
  Retrofitting the old corpus is not worth it — those files won't be regenerated, and faking a
  fingerprint for them would be a lie, not a record.
- **Sequencing:** this is **Wave 2** of the data-plane reorg. Wave 1 (folder structure, config
  merge, legacy sweep, script moves) delivers the de-clutter and must land first — it proves the
  domain taxonomy the manifests will reference, and it's prompt-freeze-safe plumbing. The manifest
  machinery rides the v5 generation cycle, where the artifacts that actually *need* it get created.

---

## 6. Lessons (transferable)

- **Lineage that lives in a filename is a label you trust; lineage that lives in a content hash is
  a fact you can check.** The difference only bites when something drifts silently — which is
  exactly the case you can't afford to miss in an A/B.
- **Reference upstream artifacts by content, not by path, at every hop.** A path is a mutable
  pointer; the moment an input can be regenerated under the same name, a path-only link can lie
  while looking healthy.
- **Separate provenance from reproducibility and claim each honestly.** For LLM systems, full
  byte-reproduction is unreachable, so promising it is impact theater. Promising *verifiable
  provenance + statistical equivalence from a pinned setup* is both achievable and exactly what an
  eval needs.
- **Completing two existing half-conventions beats inventing a third.** The fingerprint and the
  golden-label `frozen_artifacts` were already the two halves of this; the work is unifying them,
  not designing something new.
