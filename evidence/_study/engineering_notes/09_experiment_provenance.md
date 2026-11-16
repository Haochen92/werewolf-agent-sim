# U9. Experiment provenance: knowing what a result was made of

**Reading time:** about 35 minutes for Parts 1 to 3 (estimate); Part 5, 5 minutes · **Builds on:** U8 (the records a run leaves) · **Related:** U13 (what a passing test shows) · **Feeds write-up chapter:** 7

**The question:** an evaluation score moved between two runs. How do I know what caused it?

**First answer, before reading on:** two or three sentences, with an example that is not from this
project.

U8 was about the records of what a run did. This note is about the records of what a run was made
of: the code, the prompts, the model and its settings.

**Reading path.** Part 1 is the idea and its three records. Part 3 is my system and where its
records fall short. Part 4 is two design choices. Part 5 is the summary. This note is short on
purpose: the full description of my system's mechanism is a report of its own, named in
Appendix B.

**Core and detail.** The core is three ideas: a result belongs to the things that produced it
(1.1), the three records that name them (1.2), and what such a record can and cannot prove
(1.3). Sections marked **Detail** can wait for a second read.

## The whole idea

```text
A score  =  what the run was made of   +   chance
            (code, prompts, model and settings, inputs, the way it was measured)

Two scores can be compared for one change only if everything else was the same.
A record of what each run was made of is what shows whether it was.
```

Provenance is the record of where a result came from. Without it, a change in a score has no
cause that can be named, and two results cannot be put side by side with confidence.

| Concept | The question it answers |
|---|---|
| What a run is made of | Which things can change a score? |
| The three records | What was asked for, what executed it, and which files went in? |
| What a stamp proves | When can a result be reproduced, and when only shown to have drifted? |
| Using the stamp | What stops two results that should not be compared from being compared? |

---

# Part 1 — Fundamentals

The example is the support assistant from U8. Its answers are scored every week against a fixed
set of 200 questions. Last week the score was 86%. This week it is 79%.

## 1.1 A result belongs to what produced it

Five things can move that score, and only one of them is the thing someone meant to change.

| Ingredient | For the support assistant | How it changes without anyone deciding |
|---|---|---|
| The code | The search step, the reply formatting | A fix merged for another reason |
| The prompts | The instructions the model is given | An edit to one sentence |
| The model and its settings | The model's name, temperature, how much it reasons, which provider serves it | A default changed; the provider updated the model behind the same name |
| The inputs | The 200 questions; the help-centre index | The question file was regenerated; the index was rebuilt |
| The measuring | The judge model, its instructions, the scoring rule | The judge's prompt was tightened |

There is a sixth cause that is not an ingredient: **chance**. A model can answer the same
question differently on two tries, so two runs of an identical setup do not give the same
score. A difference has to be larger than that spread before it means anything, which is why a
comparison needs several runs, and the two versions run close together in time.

So "the score fell 7 points" is not yet a finding. The first question is which of the five
changed.

## 1.2 Three records

Three records between them name the ingredients. They are separate because they answer
different questions, and none can stand in for another.

```text
The run's configuration  =  what was asked for
                            (which question set, memory on or off, how many runs)

The fingerprint          =  what executed it
                            (the code's commit, a hash of the prompts, the model and settings)

The manifest             =  which files went in, and which came out
                            (each input file's path and a hash of its contents)
```

**The fingerprint** is a small set of fields saved with every result at the moment it is
produced.

```json
{"commit": "9aef645", "dirty": false, "prompt_hash": "efd7cd1e423abe60",
 "model": "provider/model-name", "temperature": 1.0}
```

- **The commit** names the exact code. It works only if the code that ran was the committed
  code.
- **The dirty flag** says whether it was: `true` means files had been edited and not committed
  when the run started.
- **The prompt hash** is a short code computed from the text of the prompt files. Any change to
  the text gives a different code, including an edit that was never committed.

**The manifest** uses a hash for the same reason. A file name does not identify a file's
contents: someone can regenerate `questions.jsonl` under the same name. A hash of the contents
changes when the contents do, so an old result can be shown to describe different data.

```json
{"inputs":  [{"path": "eval_sets/questions.jsonl", "sha256": "3fa9…"}],
 "outputs": [{"path": "eval_results/run_12/scores.json", "sha256": "b71c…"}]}
```

A manifest is needed whenever a run's inputs are files that can change between runs.

| Kind of run | Its inputs | Manifest? |
|---|---|---|
| An evaluation over a fixed question set | The question file, the reference answers | Yes |
| Anything that searches documents | The index, and the document set it was built from | Yes: adding documents changes the answers with no change to code or prompts |
| One live request | Whatever the user sent | No: the trace records the input itself |

It is not always called a manifest. Data-versioning tools and experiment trackers keep the same
record as "versioned artifacts", and evaluation tools as a "dataset version" that each run is
linked to.

### Check

This week's run and last week's have the same commit, the same prompt hash and the same model
name. The question file has the same name in both. Is the 7-point fall a real regression?

<details>
<summary>Answer</summary>

Not established. Three ingredients are shown equal and two are not checked: the inputs and the
measuring. The file's name being the same shows nothing; its content hash would. If the manifest
shows a different hash for the question file, the two runs answered different questions and the
scores cannot be compared. The judge's model and prompt need the same check. Chance is the last
candidate: one run each is not enough to rule it out.
</details>

## 1.3 What a stamp can and cannot prove

| The stamp says | What it establishes |
|---|---|
| A commit, and not dirty | The code can be recovered exactly. The strongest case |
| A commit, and dirty | The code had changed from that commit, by an edit that was not saved. Known to have drifted; not recoverable |
| The same model name in two runs | The same name was requested. The provider can change what serves that name, and nothing local can detect it |
| A setting, such as "reasoning: minimal" | The setting that was sent. Not what the model did with it |

So a stamp makes drift **visible**. It does not make a run **repeatable**: the same stamp run
twice gives two different scores, because of chance, and may give different behaviour months
apart, because of the provider. The accurate claim for a stamped result is "the setup is known,
and a rerun under the same setup is comparable", not "this can be reproduced exactly".

**What to do with a dirty stamp.** Only the code is in doubt, and only by the edit that was not
committed. The prompt hash is computed from the files on disk, so it still holds, and so do the
model, the settings and the manifest. What follows depends on what the result is for.

| The result is for | What I do |
|---|---|
| A quick check while developing | Use it as an indication. Dirty is normal here |
| A number I will quote, or one that decides between two designs | Commit, then rerun from the clean commit. The dirty run is not the evidence |
| A dirty run set against a clean one | A difference may come from the uncommitted edit, so it is not a finding |

The habit that removes the question: commit before any run that matters. A commit on a branch
is enough.

## 1.4 Using the stamp

A stamp that is saved and never read prevents nothing. It is used in three ways.

```text
1. Stamp at the moment of the run.   A stamp written later, from memory, is a guess.
2. Refuse to mix.                    Code that combines results checks their stamps first
                                     and stops if they differ.
3. Read the stamps before the story. When a score moves, compare the two stamps field by
                                     field before looking for a cause in the system.
```

The second is the one that matters most, because it does not rely on anyone remembering. A
check that stops a run is worth more than a field somebody could have looked at.

**The 86 to 79 case, start to finish.**

```text
1  Compare the two fingerprints. Commit, prompt hash and model name are equal.
2  Compare the two manifests. The question file's hash differs.
3  The file's history: it was regenerated on Tuesday with 40 harder questions added.
4  So the two scores answer different question sets. The fall is not a regression.
5  What is still not known: whether the assistant changed at all. That needs both versions
   run on one question set, several times each.
```

Without step 2 the team would have spent the week looking for a bug in the assistant.

## 1.5 Designing it for a new system

The sections above read stamps that already exist. For a new system the same ideas become five
questions, asked in this order before the code is written.

| Question | For the support assistant | What the answer decides |
|---|---|---|
| 1. What question must the record answer? | "Is the new prompt better than the old one?" and "what produced this one bad reply?" | How much to record. A comparison needs everything that must be held equal. One case needs a few tags (below) |
| 2. What can change the output? | The five ingredients (1.1) | The list of things to identify |
| 3. Which of them can change without a commit? | The temperature, set in the environment; the question file; the help-centre index; the model behind the provider's name | One field for each. The commit already covers whatever lives in git |
| 4. Where is each value read from? | The model's name comes from the function that builds the model client | Each value is read from the code that acts on it, when the run starts, and saved with the result |
| 5. What reads the stamp? | The script that compares two runs | The check that refuses to mix (1.4). Without one the stamp is decoration |

Questions 1 to 3 are the design. Questions 4 and 5 are where a stamp goes wrong after it is
built: a value worked out separately from the code that uses it can disagree with what ran,
and nothing shows it (3.1 has my own case).

**What one case needs.** For an error or a complaint, the trace already holds the real things:
the text sent to the model, the model that answered, the input and the output. A stamp adds
little there. It matters at the next question, "is this a one-off, or did it start with a
change?", which means grouping many cases. So each trace carries a few short tags.

| Tag on each trace | The question it answers |
|---|---|
| The code's release | Did the complaints start with this deploy? |
| The prompt version | Did they start with this prompt edit? |
| The model | Are they all on one model? |
| The index build, where documents are searched | Was the right document in the index at that time? |

**Four smaller rules.**

- Give the stamp's definition a version number, and raise it when a field's meaning changes.
  Then a change of definition is not read as a change of setup.
- Never put a key or a secret in a stamp. It is saved with every result and shown in reports.
- Hash by a rule over a folder ("every file under the prompts folder"), not by a hand-kept
  list. A list goes stale without anyone noticing, so the files that are hashed should live
  together.
- Match the strictness to the use. A quick check while developing needs no manifest and can be
  dirty. A number that will be quoted needs a clean commit and every input hashed.

---

# Part 2 — What git does, and what my code does

| Responsibility | Git | My code |
|---|---|---|
| Name a version of the code | The commit id | Reads it when a run starts, with whether the tree was dirty |
| Notice an uncommitted prompt edit | Nothing | Hashes the prompt files' contents |
| Record the model and settings | Nothing | Reads the settings in force and saves them with the result |
| Tie an output file to its inputs | Nothing | Writes a manifest with each input's content hash |
| Stop two mismatched results being combined | Nothing | A check in the loop that runs many games |

I keep prompts in git as code, so there is no separate prompt registry. The commit and the
prompt hash together stand in for a prompt version.

---

# Part 3 — My Werewolf system: what a result carries

## 3.1 The stamp, as written today

This is the fingerprint my code produces, run on 2026-11-16 (the commit shortened):

```json
{"fingerprint_schema": 3, "git_commit": "02c20ee4", "git_dirty": true,
 "prompt_bundle_hash": "4f1fb31086c1c5a6", "llm_backend": "anthropic", "game_model": "anthropic/claude-haiku-5-5", "temperature": 1.0,
 "game_thinking_level": "low", "summary_thinking_level": "medium",
 "judge_thinking_level": "minimal", "pro_model": "anthropic/claude-sonnet-5-5",
 "pro_backup_model": "anthropic/claude-haiku-5-5",
 "embedding_model": "qwen/qwen3-embedding-8b", "embedding_dims": 1536}
```

Two things in it were wrong until the day this note was written.

The backend field said `vertex` for a game played on Claude. It was computed by a line that
only chose between Google's two routes and never looked at the model's name. It is now read
from the model's name, the way the model factory routes a call (3.5, gap 2).

The prompt hash covered only the 14 top-level prompt files of 41, so the role cards, the
extraction prompts and the memory prompts were outside it. I had the hash widened on 2026-11-16: it now covers 39 files, each named by
its path inside the prompts folder. The two left out are a snapshot test's fixtures, which no
game code reads. The same change added `fingerprint_schema`, the version of the stamp's
definition, so that an old hash and a new one are not read as a change of prompts. It is a
plain counter, not a hash: 2 for the wider prompt hash, 3 for the corrected backend field. Two
stamps are compared field by field only when their numbers match.

## 3.2 The three records in my system

| Record | What it is here | Holds |
|---|---|---|
| Configuration | `RunConfig` | The game's rules, which roles have memory, the retrieval and filter settings, the deduction mode, the voices, the game id and session id |
| Fingerprint | `runtime_fingerprint()` | The commit and dirty flag, the prompt hash, the models, temperature, reasoning levels and embedder |
| Manifest | `evaluation/src/core/manifest.py` | For an evaluation output: the commit and dirty flag, the evaluation's settings, and each input file's path, hash and row count |

The fingerprint is read once per process and kept, so a commit made while a long run is going
does not change the stamp part-way.

## 3.3 Which results carry a stamp

| Where the game ran | Fingerprint | Anything else |
|---|---|---|
| A batch run | On every game's record, success or error, and in the experiment folder's `config.json` | The commit as the trace's release |
| The command-line game | In the trace's metadata | The commit as the trace's release |
| The memory tick and a model's admission run | In their own records | |
| An evaluation output | The commit and dirty flag only | Its manifest: settings and input hashes |
| A hosted game | None | Its row in the database: the model, whether the player paid, the memory switch, the seats |

**A hosted game carries no fingerprint, and until today no usable version stamp.** The server
builds its run configuration with no metadata. The trace's release, which should name the
commit, said "unknown" on all 14 hosted traces among the latest 30 that I checked on 2026-11-16,
because the server's image has no git history. The build now passes the commit into the image;
that takes effect at the next deploy (U8 section 3.6). Until then a hosted game is tied to its
code only by matching its date to the deploy log.

## 3.4 The check that refuses to mix

The learning loop runs many games across several rounds and compares a memory-on side with a
memory-off side. Before it uses the games, it takes the first game's fingerprint as the
reference and compares every other game's against it. Any difference stops the run with a
message naming the fields that differ.

```text
round 1, game 1   fingerprint A   ← the reference
round 1, game 2   fingerprint A   ok
round 2, game 1   fingerprint B   → stop: "runtime DRIFT within the run: {llm_backend: ...}"
```

It exists because the same model served by two backends does not score the same (Google's own
API and Vertex differ even at temperature 0), so results from the two must never be averaged
together. A run resumed the next day under a different setting would otherwise mix them
silently.

The check covers one run of the loop. **Across two separate runs nothing stops a comparison;**
a person reads the two fingerprints.

## 3.5 Known limitations

| Gap | Consequence | Possible direction |
|---|---|---|
| 1. A result stamped before 2026-11-16 has a prompt hash over the 14 top-level files only. It has no `fingerprint_schema` field, which is how to tell | For those results, the same hash does not show the same role cards, and an old hash cannot be compared with a new one. Model-visible text outside the prompts folder (the output schemas, the deduction engine's lines) is still outside the hash | For old results, compare the commits. For the text outside the folder, decide whether it belongs in the hash |
| 2. A result stamped before 2026-11-16 (`fingerprint_schema` below 3) has a backend field that knows only "vertex" and "google" | Every Claude game from before that date is labelled with one of them. The model's name is right and is the field to read | Fixed for new results on 2026-11-16: the field is read from the model's name. Old results are not re-stamped |
| 3. The rescue model is not recorded | A turn the rescue model played was produced by a model the stamp does not name | Add it |
| 4. A dirty run cannot be recovered | The flag says the code had drifted from its commit, not how | Refuse a run meant to be cited unless the tree is clean |
| 5. A hosted game has no fingerprint | 3.3 | Pass the fingerprint as metadata, as the command-line game does |
| 6. An evaluation's manifest names the commit, not the models | An evaluation output does not say which model setup produced its inputs, unless its settings list it | Put the fingerprint in the manifest |

So the backend field and the prompt hash can be trusted only on results stamped from 2026-11-16
on. A comparison that involves an older run has to read the commit and the model name.

One gap no design closes: a provider can change what serves a model's name. The learning loop
reduces the risk by running its two sides together in time. A comparison made outside the loop
has to be interleaved by hand, and nothing enforces that.

### Check

Two batch runs from October, a week apart, show the same prompt hash and different win rates for the
Investigator. Can the difference be put down to the memory setting that was changed between
them?

<details>
<summary>Answer</summary>

Not from that. Both were stamped before 2026-11-16, so the same prompt hash does not show the
prompts were the same: the Investigator's role card was outside the hash then (gap 1). The commits have to be compared: if they
differ, the role card may have changed, and `git diff` between the two commits on
`Agents/prompts/roles/` settles it. The dirty flag on each run has to be false, or that check
proves nothing. And a week apart means the provider may have changed, which nothing settles; the
sound version of this comparison runs both settings interleaved in one session.
</details>

---

# Part 4 — Design choices

**Where does a prompt's version live?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| In git, as code, with a hash of the files in each result | One history for code and prompts; a prompt change is reviewed like any other | The hash has to cover every prompt file. Mine did not until 2026-11-16 | Yes |
| In a prompt registry, each prompt with a version number | A result can name "prompt X, version 7"; prompts change without a deploy | A second system to keep in step with the code | No |

**What is done about uncommitted changes?**

| Design | Benefit | Cost | My system |
|---|---|---|---|
| Record a dirty flag and carry on | Nothing blocks a quick experiment | A dirty result cannot be recovered | Yes |
| Refuse to run unless the tree is clean | Every result names recoverable code | Slows exploration | No. Worth having as a switch for runs meant to be cited |
| Save the uncommitted diff with the result | Recoverable without blocking | Large, and may hold things that should not be saved | No |

---

# Part 5 — Review

## In 30 seconds

A score is produced by code, prompts, a model and its settings, inputs and a way of measuring,
plus chance. Two scores can be compared for one change only if the rest was the same. Three
records show whether it was: the configuration (what was asked), the fingerprint (what executed
it) and the manifest (which files went in, by content hash). A stamp shows drift; it does not
make a run repeatable. It earns its keep only where code reads it and refuses to mix results
that differ.

## My Werewolf system in one paragraph

Every batch game's record carries a fingerprint: the commit and a dirty flag, a hash of the
prompt files, the models, temperature, reasoning levels and embedder. The learning loop stops
if the fingerprint changes between its games. Evaluation outputs carry a manifest with their
inputs' hashes. The weak points are that the rescue model is not recorded, a hosted game has
no fingerprint at all, and results stamped before 2026-11-16 have a prompt hash that left out
the role cards and a backend field that is wrong for Claude. So I can claim that drift is
visible on the batch path, not that results are reproducible, and a comparison with an older
run has to read the commit and the model name.

## Problems

**Problem A.** A team fine-tunes a classifier every month and reports accuracy on a test set.
This month accuracy rose 3 points. Name four things, other than a better model, that could
explain it, and the record that would rule each one in or out.

**Problem B.** A draft sentence for the write-up: "Every result in this project is
reproducible from its fingerprint." What is supported, what is not, and what is the accurate
wording?

---

# Appendix A — Answers to the problems

**Problem A.** The test set changed (a content hash of the test file). The scoring code changed
(the commit of the evaluation code). The training data changed (a hash of the training set, or
its snapshot id). The settings changed, such as the decision threshold (the saved
configuration). Chance: one training run each, where the spread between two identical runs is
not known (several runs of the same setup). The four records are the manifest, the commit, the
manifest again, and the configuration.

**Problem B.** Supported: a batch game's record names its commit, whether the tree was dirty,
the prompt files by content, and the principal models and settings; and the learning
loop refuses to mix games whose fingerprints differ. Not supported: "every result", since a
hosted game has no fingerprint; "reproducible", since a dirty run cannot be recovered, a model
answers differently on each try, and a provider can change what serves a name; and "from its
fingerprint", since the rescue model is not in it, and for results before 2026-11-16 the role
cards were outside the prompt hash. Accurate wording: "Batch results are stamped with the code
version, a hash of the prompt files and the model settings, so a change of setup between two
runs is visible. The stamp does not cover hosted games, older results' hashes left out the role
cards, and it does not make a run repeatable."

---

# Appendix B — Implementation and evidence reference

*Each claim carries its support: **code** (the file and symbol were read), **run** (executed for
this note), **test** (named, and run on 2026-11-16), **doc** (a written record, not re-read in
the code). Read against the code on 2026-11-16. Paths are from the repository root.*

**The full description.** [`evidence/tracing/fingerprinting/report.md`](../../tracing/fingerprinting/report.md),
re-verified on 2026-10-26, describes the mechanism in detail, with its build history in the
`experiment_log.md` beside it. This note states the parts needed to reason about a comparison
and re-checks them.

**The fingerprint (3.1, 3.2)**

- Fields and how each is read; the commit and dirty flag cached per process: **code**
  [`Agents/run_fingerprint.py`](../../../Agents/run_fingerprint.py)::`runtime_fingerprint`, `git_revision`
- The stamp in 3.1: **run** on 2026-11-16
- The prompt hash covers 39 of 41 prompt files, keyed by path, and leaves out `goldens/`; before
  2026-11-16 it covered the 14 top-level files: **code** `prompt_bundle_hash`,
  `_prompt_source_files`; **run**, both hashes computed on one tree (`6876d34cb388c496` before,
  `4f1fb31086c1c5a6` after); **test** `tests/engine/test_run_fingerprint.py` (five tests);
  no code outside tests imports `goldens/`: **code**, a search
- The backend field is the game model's provider family, or for a Gemini id Vertex or Google:
  **code** `_llm_backend`, `Agents/llm_factory/chat.py`::`_provider_family`; **run** (the stamp
  in 3.1); **test** `tests/engine/test_run_fingerprint.py` (four cases)
- The rescue model is absent from the fingerprint: **code** `runtime_fingerprint`;
  `Agents/llm_factory/accessors.py` (`GAME_FALLBACK_MODEL`)

**Which results carry it (3.3)**

- Batch records and the experiment's `config.json`: **code** `scripts/run_batch.py`
- The command-line game's trace metadata: **code** `Agents/main.py`::`run_game`; **test**
  `tests/engine/test_run_config_contract.py`, `tests/engine/test_child_config_unit.py`
- The memory tick and the admission run: **code** `Agents/memory/consolidation/tick.py`,
  `evaluation/src/cli_runner/model_admission.py`
- Evaluation manifests carry the commit and dirty flag, the settings and input hashes: **code**
  `evaluation/src/core/manifest.py`; **test** `tests/evaluation/test_manifest.py`
- A hosted game passes no metadata: **code** `server/game/game_session.py` (`build_runnable_config(run)`)
- Hosted traces' release was "unknown" on 14 of 14: **checked** in the trace store on 2026-11-16;
  the build change is in `Dockerfile` and `docker-compose.yml`, not deployed

**The check (3.4)**

- The reference fingerprint and the comparison: **code** `evaluation/src/loop/invariants.py`::`arm_fingerprint`,
  `assert_fingerprint_consistent`; called from `evaluation/src/loop/driver.py`; **test**
  `tests/evaluation/test_loop_invariants.py`::`test_assert_fingerprint_consistent_detects_backend_flip`,
  `test_arm_fingerprint_missing_raises`
- Nothing compares fingerprints across separate runs: **doc** the fingerprinting report, section 7
- The loop runs its two sides together, and a comparison outside it is interleaved by hand: **doc**
  the experimental controls report
- What a hosted game's row holds: **doc** the fingerprinting report, section 2

**Not established**

- Whether any past comparison in `evidence/` was made between runs whose role cards differed.
  The prompt hash could not have shown it.
- What a served game's fingerprint would add in practice once the release stamp is deployed.

**Reading**

- The fingerprinting report above, sections 1, 4 and 10: the contract, the fields and the gaps.
- [`evidence/evaluation/experimental_controls/report.md`](../../evaluation/experimental_controls/report.md):
  why two sides of a comparison are run interleaved.
