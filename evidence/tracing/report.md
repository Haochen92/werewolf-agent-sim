# Observability: what a game leaves behind

Observability has two jobs in this project: explain what happened in a live game, and preserve the
inputs and decisions needed to evaluate a change later. A trace helps inspect execution; a durable
evaluation record lets a study survive missing traces or a changed tracing service.

The two execution paths meet those needs differently. Batch runs save evaluation cases to local
files and also emit Langfuse traces. Capture scripts save local artifacts without the graph callback
trace tree. Served games save events, checkpoints, usage counts and completed-game prompt captures
to PostgreSQL, but do not persist their in-memory evaluation-case sink.

The main chapter-7 finding is uneven coverage, not a lack of instrumentation:

| Gap | Consequence | Evidence in this review |
|---|---|---|
| Served games have no runtime fingerprint | A result cannot be tied directly to its complete execution configuration | `GameSession` builds config without fingerprint metadata; no server fingerprint writer was found |
| Served evaluation cases have no durable copy outside Langfuse | Loss or absence of trace data can lose those case records, although events and checkpoints remain separate | The session creates and passes `EvalCaseSink` but does not persist its records |
| The fingerprint's backend field still resolves only Google or Vertex | A Claude run can be labelled `vertex`; the field does not identify its actual provider | `runtime_fingerprint()` uses `_use_vertex()` for every model; the original report records two affected Claude runs |

The last gap concerns runs that have a fingerprint, principally batch and capture runs. It does not
mean served Claude games have a fingerprint, or that a `vertex` label proves a call used Vertex.

The records have already helped diagnose a real failure. In the cross-game cache incident, a prompt
capture lacked one seat's opening, the event log showed a `generation_failed` pass, and the usage
ledger showed no failed call. Together with the cache investigation, these supported the finding
that the turn had reused another game's result. Missing telemetry alone would not establish that
cause.

Read [the two paths](#the-two-paths-today) first, then [rebuilding a turn](#rebuilding-a-turn). The
[decision index](#decision-index) gives the reasons and costs; [incidents](#incidents),
[checks](#how-it-was-checked) and [gaps](#what-is-not-recorded-and-what-is-not-read) follow.

**Version and evidence.** The original review describes code at `5d8ea41c` (2026-10-26), with LangGraph 1.1.10
and the Langfuse Python SDK 3.14.6 against a self-hosted Langfuse server. The website ran server image
`2ecec0cc` on that date: the deployed `dd985ebe` plus the cache fix, without the later server commits
([deploy log](../../frontend/docs/deploy_log.md), 2026-10-26). Counts of served games come from a
read-only query of the game database on 2026-10-26. Incidents and measurements belong to the dates and
versions named with them. No alternative recording design was compared; the evidence is the code,
tests, the records themselves and the incidents. This editorial review spot-checked the session,
case sink, fingerprint, release setup, Dockerfile and error-reporting code. It did not query production,
re-read the historical datasets, rerun tests or verify current hosted-service behaviour.

## What has to be visible

Four questions, each with a different consumer:

1. **What did each model call see?** The leak checks need every prompt a seat was given, and a fault
   is often diagnosed by reading the input beside the bad answer.
2. **Can a past turn be run again?** Testing a fix on a failure seen once means rebuilding that turn
   under today's prompt ([turn replays](../evaluation/evaluation_scopes/turn/report.md)).
3. **Which build produced a result?** Interpreting a difference requires knowing the code, prompts,
   models and settings behind each result; provenance alone does not make a comparison controlled.
4. **What failed, and what did it cost?** A crash in a live game has to be found without reading the
   container's log, and each game's cost has to be known per model.

The batch record was first built in June for two more uses. The memory system is a chain of stages
(the day summary, the lookup's query, the lookup, the seat's use of what it found, extraction after the
game), and a win rate cannot say which stage failed, so each stage needed records it could be judged on
by itself. And a corpus of frozen decisions could later be labelled and used for training, such as a
reranker or a dedup classifier, without re-running games.

Two constraints apply to all of them. Evaluation records must be practical to read in bulk; the
original trace-fetch path was not (the [422 incident](#the-422-collapse-2026-06-11)). And nothing written down may hold a player's API
key.

## The two paths today

A **trace** is Langfuse's record of one run: a tree of **spans**, each a step with its input, output
and timing. A **session** groups traces. An **evaluation case** is one gradable unit of work (a seat's
turn, a day summary, a finished game) frozen as a record that a judge or a replay can use without the
game. A **checkpoint** is LangGraph's saved copy of the whole game state after a step.

| Record | Batch and capture runs | Served games |
|---|---|---|
| Langfuse trace | One per game from `run_game`; the capture scripts attach none | One per run of the game's task, grouped by game id |
| Evaluation cases | Local per-game files; traced batch runs also emit them in spans | In memory during the run; Langfuse is the only configured durable sink |
| Every seat prompt and private read | In memory for the leak checks; on disk only from the voice-game runner | Saved compressed when the game ends |
| The game's course | One record per game: result, roles, transcript, summaries, resolutions, metrics | The event log the replays play from |
| Checkpoints | In process memory, gone when the process ends | PostgreSQL, kept |
| Which build ran | Fingerprint on batch records/config and capture manifests, with coverage gaps | No runtime fingerprint; deployment records provide indirect build evidence |
| Model calls and cost | Per call (`calls.json`) and per model (the manifest), capture scripts only | Per model and hour on the game's row |
| Errors | The process's traceback; an error record in the batch file | Sentry |

The rest of this section takes each record in turn, with one real example per path.

### Batch and capture runs

`scripts/run_batch.py` plays games through `Agents/main.py::run_game` and writes them under
`batch_results/<experiment>/`. The capture scripts in `evaluation/experiments/`
(`phase3_capture.py`, `persona_voice_games.py` and others) drive the graph themselves and write files
beside the evidence they serve.

#### The Langfuse trace

`run_game` opens a root span and names the trace; LangGraph's callback (Langfuse's `CallbackHandler`)
then records every graph node and model call as a nested span on its own. A few spans are shaped by
hand at fixed points in the game:

```text
trace "werewolf_game"   session = the run's session id · release = the git commit
                        metadata: game id, memory, rerank, filter and retrieval settings, game config
└─ span "werewolf-game" (the root)
   ├─ graph nodes and model calls            from the callback, named after the nodes
   ├─ agent_action_eval_<seat>_day_<d>_round_<r>_<phase>   one per AI seat turn; output.eval_case
   │    └─ memory_retrieval_<seat>_day_<d>_round_<r>        the lookup, when memory is on
   ├─ day_summary_eval_<game>_day_<d>                       output.day_summary_case
   ├─ day_resolution_day_<d>, night_resolution_day_<d>      the tally and the night's outcome
   └─ postgame_extraction_<game>                            output.extraction_case
scores: one per computed game metric (a dnu_ prefix marks the do-not-use ones)
```

The span names come from one module (`Agents/observability/span_names.py`). The release is the git
commit, set in `Agents/tracing.py` at import, before the Langfuse client exists, because the SDK reads
it once per process. The runtime fingerprint rides in the run's metadata
(`build_runnable_config(run, callbacks=[...], metadata={"runtime_fingerprint": ...})` in `run_game`).
After the game, `Agents/compute_metrics.py::push_scores_to_langfuse` writes each computed metric as a
score on the trace and on the session, with an id derived from the trace and the metric, so pushing
twice does not duplicate it. Langfuse prices each call from model definitions synced from the project's
price table (`Agents/observability/langfuse_prices.py`), and calls made outside LangChain, such as
Claude batch calls, are recorded as generations by `Agents/llm_factory/providers/anthropic.py::_trace`.

The capture scripts pass only their own callbacks (a usage meter and a call log), so their games get
no Langfuse span tree; the voice-game runner's documented command also turns Langfuse tracing off.

#### Evaluation cases, and their local copy

At each gradable step the code builds a case and calls `Agents/observability/case_sink.py::freeze_case`.
It stamps the live span's trace and observation ids onto the case, dumps it once, writes the dump into
the span's output, and appends the same dump to the game's in-process sink (`EvalCaseSink`). The local
record has exactly the shape the Langfuse reader produces from a fetched span, so one set of converters
can read either source, and a case's id (`{trace_id}:{observation_id}`) is the same in both. `run_batch`
writes the sink as one JSONL file per game,
`batch_results/<experiment>/eval_cases/<session>/<game>.jsonl`, and puts its path on the game's record.

Inside a game, three kinds are written today:
- **a turn case** (`EvalCase`) for every AI seat turn, day or night: what the seat saw (today's
  transcript and its private context), the memory lookup and the wider pool it was drawn from before
  reranking, the decision taken, the seat's verdict on each lesson it was shown and its reads of the
  other players, with a `schema_version` (`eval_case_v2`) that gates format changes;
- **a day-summary case** per day: the raw discussion and the summary written from it;
- **the extraction input** once per game: what the offline extraction job will read. Since a ruling on
  2026-10-12 extraction no longer runs inside a game; the dedup pass after it writes its own cases
  (`DedupCase`) wherever it runs.

One real file: game `8d33c5a3` of the `v8_demo_0` run (Claude Haiku 5.5, 2026-10-14) left 134 records,
129 turn cases, 4 day summaries and 1 extraction input. One turn case, abridged (the store path is
shortened, and 22 of the case's 30 fields are left out):

```json
{"kind": "agent_action_eval", "id": "d4b3ca3b8f92c71a",
 "name": "agent_action_eval_player_2_day_1_round_1_night_action",
 "trace_id": "58cf929c293e962a3117eb588dda7a8c",
 "output": {"eval_case": {
   "player_id": "player_2", "player_role": "chanteuse", "day": 1, "round": 1,
   "action_phase": "night_action",
   "agent_night_action": {"role": "chanteuse", "kind": "chat", "target": null,
                          "via": null, "role_named": null},
   "memory_enabled": false, "retrieval_skipped_reason": "day_1",
   "provenance": {"store_dir": ".../memory_stores/ten_seat_v2",
                  "reranking_enabled": false, "filtering_enabled": false}}}}
```

This is a wolf's chat turn in the pack's night. The case records that the turn was a chat, not the line
the wolf wrote: the line is in the span's `resolved_turn` output in Langfuse, and in the next wolf's
case as part of what it saw. `provenance` is the data side of provenance: which store the lookup read
and whether reranking or filtering ran, kept on the case because a frozen case travels without its
trace.

**From case files to test sets.** The builders (`eval-build-*`) read these files, not Langfuse, and
sample cases into *frozen sets* under `evaluation/frozen_eval_sets/`: immutable files with a manifest
that hashes their inputs, so a judge, a replay or a training run always reads the same cases. The
Langfuse reader remains for games that predate the local files: it lists a trace's spans cheaply, then
fetches only the named case span, and a generic span fetch can still mine any retained span into a new
kind of case.

#### The prompt log and the reads log

`Agents/turn/agent_player.py::run_agent`, which every AI seat decision goes through, records each
prompt input before the model is called (`Agents/turn/eval.py::log_prompt`), and each private read the
seat returns (`record_reads`). They go to the game's `TurnCapture`, held in a context variable so two
games in one process never share a list. The prompt input is the dictionary of named fields the
template is filled from (the transcript block, the dead roster, the seat's night records and so on), not
the rendered text.

The batch runner reads both lists in memory after each game to run the nine leak checks, puts the
verdict on the game's record, and writes neither list to disk. The voice-game runner
(`persona_voice_games.py`, whose games also fed the evil-cover screen) saves them as
`<label>.capture.json.gz`, in the server's capture format with a fuller final state. In
`voices-01.off` (2026-10-18, Claude Haiku 5.5) the log holds 98 prompt entries, and the manifest counts
104 model calls: calls made outside `run_agent`, such as the day summary, are not seat prompts. One
entry, its 52 prompt-input keys abridged:

```json
{"player_id": "player_2", "player_role": "sigilist", "output_key": "day_channel",
 "day": 1, "round": 1,
 "prompt_input": {"preamble": "...", "day_channel": "No messages yet.",
                  "dead_roster": "...", "night_actions": "...", "previous_strategy": "..."}}
```

Who may see which field, and the checks that read these lists, are the
[agent boundaries report](../agent_boundaries/report.md)'s.

#### The game record, the manifests and `calls.json`

**The game record.** `run_batch` writes one JSONL line per game: the result and roles, the transcript
and day summaries, the per-day vote tallies and per-night outcomes, the computed metrics, the leak
verdict, the game id, the trace id and the path of the case file. A failed game gets an error record
with its traceback. The capture scripts write the same content as `<label>.record.json`.

**The provenance.** Every `run_batch` record, success or error, carries the runtime fingerprint, and the
experiment folder's `config.json` holds the resolved run settings with the same fingerprint. The capture
scripts write a `<label>.manifest.json`: the commit and the modified and untracked files, the fingerprint,
the LangGraph version, the model, the run settings, the token usage and the cost. What the fingerprint
covers and misses is the [fingerprinting report](fingerprinting/report.md)'s.

**One row per model call.** The capture scripts also attach a call log (`phase3_capture.py::CallLog`)
and save it as `<label>.calls.json`. A real row from `phase3_games/game1` (2026-10-09, gemini-3.5-flash
-lite, 95 calls, $0.4552 by its manifest):

```json
{"node": "round_turn",
 "checkpoint_ns": "DAY_PHASE:bcbf953d-67a9-559e-c348-03575f4d266a",
 "model": "gemini-3.5-flash-lite",
 "started": 1791541908.8565261, "ended": 1791541915.2535865, "ok": true}
```

### Served games

`server/game/game_session.py::GameSession` runs each game as an asyncio task over the same compiled
graph, streaming its output to the browsers. On 2026-10-26 the database held 68 served games, from
2026-08-21 to 2026-10-21; 51 had completed.

#### The event log

Each chunk the graph streams is translated into typed events (`server/game/translate.py`) and appended,
in sequence, to the `events` table right away (`server/storage/game_repository.py::record_events`).
The event log is what a replay plays and what a reconnecting browser catches up from. When the game
ends, `complete_game` derives the winner, days and counts from it and marks the row completed, or marks
it dropped if the log has no clean ending. Evaluation reads served games through the public replay
endpoint, rebuilt into the batch record's shape (`evaluation/src/data/sources/replay_api.py`), so readers
written for batch games take them unchanged. The event at the centre of the cache incident, from game
`51226f24`:

```json
{"day": 1, "seq": 32, "type": "pass_marker", "player": "player_9", "channel_seq": 8,
 "pass_reason": "generation_failed", "gated": false, "gated_candidate": null}
```

#### The prompt capture and the leak audit

When a game ends, `GameSession._save_capture` packs its `TurnCapture` with six fields of the final state
that the leak checks read, compresses it, and writes one row to `prompt_captures`
(`server/storage/prompt_captures.py`): the blob, `n_prompts`, a `partial` flag for a game resumed after
a restart (its earlier prompts died with the old process), and, once audited, `audited_at` and the list
of leaks. The nightly audit (`server/housekeeping/leak_audit.py`) runs the batch runner's nine checks
over every capture not yet audited. It runs from a checkout on the host, because the checks live in
`tests/`, which the server image does not include.

On 2026-10-26, 11 of the 68 served games had a capture, all completed games from 2026-10-16 to
2026-10-21; captures arrived with the 2026-10-15 deploy. None was partial, and none had been audited.
Game `51226f24`'s row: 115 prompts, not partial, captured 2026-10-17 08:02 UTC, `audited_at` empty.

#### Checkpoints

`server/graph_runtime.py::GraphRuntime` compiles the graph over a PostgreSQL checkpointer
(`AsyncPostgresSaver`), one thread per game id. A restarted server resumes each running game from its
last committed step. The replays read the same checkpoints, read-only, to recover the exact state before
a turn (`evaluation/experiments/investigator_claim_replay.py::load_state`). Nothing deletes a finished
game's thread. On 2026-10-26, 49 of the 68 game rows had checkpoint threads.

#### The usage ledger

A `UsageMeter` rides with the game's callbacks (`server/game/usage.py`). It counts each model call's
tokens and wall time per model and UTC hour, because prices change by date and DeepSeek bills peak hours
at a different rate. The session saves the counts on `games.usage` at most every 30 seconds and at the
end, so a restarted game carries on from them. The cost is not stored: `game_cost` works it out from the
counts and the price table whenever a replay is read. 37 of the 68 rows carry counts. Game `51226f24`
(GPT-6 Luna), first of its two hourly buckets:

```json
{"model": "gpt-6-luna", "hour": "2026-10-17T07:00:00+00:00", "calls": 104, "failed": 0,
 "input": 486111, "cached": 294102, "written": 5832, "output": 56478, "reasoning": 21302,
 "seconds": 529.359}
```

A call counts as failed when the provider raises; a failed call adds no tokens.

#### Error reports

`server/error_reporting.py` sends a game that dies, or a request that fails, to Sentry, tagged with the
game id, the model, whether the player paid, and whether the failure came before or after the game's
end. The integration disables collection of request bodies, headers, cookies, query strings, stack-frame
variables and model inputs and outputs. It removes named private fields recursively and scrubs the
supplied game keys from game-failure reports. These are explicit safeguards, not a proof that every
possible exception or breadcrumb is free of sensitive text. It is off unless a
DSN is set, it records no performance traces, and ordinary log lines stay breadcrumbs, so routine
fallbacks do not use the plan's quota. A refused player key is not reported: it is the player's key, not
a bug.

#### Langfuse on the server

The session opens one trace per run of the game's task (`GameSession._run`): root span `werewolf-game`,
trace name `werewolf_game`, session = the game id, metadata the game id, the model, whether the player
paid, and whether this run is a recovery. A game resumed after a restart is therefore a second trace in
the same session. A human seat's draft preview is a trace of its own (`draft_preview`) in that session.
Inside, the graph emits the same spans as on the batch path, eval-case spans included. The server creates
a case sink but never writes it, so **Langfuse is the only configured durable destination for a served game's evaluation cases.
The in-memory copy lasts only as long as its session, and durable availability depends on trace export
and retention.** No scores are pushed.

#### Which build served a game

The inspected served-game path adds no runtime fingerprint: the session calls
`build_runnable_config(run)` without fingerprint metadata. The trace's release stamp is computed from git at import; the server image copies `Agents/`
and `server/` without the repository, and the original review found no production `LANGFUSE_RELEASE` override. Without an override,
`git_revision()` falls back to `unknown` in that image. This is a code-based expectation, not a release
value checked in the live trace store; an explicit environment override takes precedence. What the row does record is the model, whether the player paid, the memory switch,
the seats and the human players. The rest of the run's settings follow from the code
(`server/game/run_config.py::game_run_config`).

The build is therefore identified only from outside the game: the deploy log names each server image by
its commit and date ("2026-10-26 server rebuilt at `2ecec0cc`"), and a game is matched to the image
that was live when it was created. The log gives dates, not times, so a game played on a deploy day is
ambiguous.

## Rebuilding a turn

**The question:** can a turn played weeks ago be run again under today's prompt, to test a fix? The replay tools support discussion and vote reconstruction from four kinds of saved record, subject
to the fields and game version available. They use today's builders by design: reconstructing a
situation is different from reproducing the original prompt or execution.**

The method and its results are the [turn-replay report](../evaluation/evaluation_scopes/turn/report.md)'s.
The part that belongs here is which record supplies the state:

| Saved record | How the turn's state is recovered |
|---|---|
| A batch turn case | Its transcript and private context become the seat's payload (`evaluation/src/replay/situation_summary.py::eval_case_to_agent_payload`) |
| A served game's checkpoints | The checkpoint just before the line is read, read-only (`investigator_claim_replay.py::load_state`) |
| A prompt capture | The prompt input locates the turn: the transcript block the prompt showed is matched to a prefix of the final transcript, and the payload is rebuilt from the final state as of that turn (`deduction_block_census.py::_payload_at`, `_transcript_then`) |
| A capture script's record and stream | The state is rebuilt from the record and the chunk stream (`phase3_turn_cases.py`) |

From that state the engine's own builders make the payload and today's template renders it
(`evaluation/src/replay/hallucination_bench.py::turn_payload`, `turn_template`). Text the engine wrote
in the old state, such as ballot lines, is brought to today's wording; what players and the summariser
wrote stays as it was. On the evil-cover turns the rebuild reproduced all 41 captured seat blocks
exactly.

What a rebuild cannot give back:
- **A guaranteed archive of the exact rendered prompt.** The local prompt capture keeps template
  inputs, not rendered messages. A retained model-call trace may contain messages, but the capture
  format alone cannot reproduce old rendering code or guarantee a complete historical prompt.
- **The provider's state on the day,** or the old model's sampling. The replay calls today's model.
- **What the rest of the day would have done.** The transcript after the turn is frozen.
- **Night turns, on the ten-seat game.** The shared replay bench behind the October screens rebuilds
  discussion and vote turns only. The memory replays of June and July did replay night actions, from
  nine-seat batch cases ([turn replays](../evaluation/evaluation_scopes/turn/report.md) §1).
- **A nine-seat turn under today's prompts.** Its payload builds, but the ten-seat prompts do not
  render it.

---

## The decisions behind it

Each decision gives the choice, what it was chosen over and why, the cost, and the evidence. Where no
record gives the reason, the text says so.

### Decision index

| Question | Decisions | Evidence and remaining uncertainty |
|---|---|---|
| Which tracer, and what is it for? | [1–3](#decision-1): self-hosted Langfuse; cases shaped at decision time; the local record first | The 422 incident; a June check that both copies hold the same case ids |
| How is a record kept consistent? | [4–6](#decision-4): one shape for both copies; span names in one module; per-game accumulators | Unit tests on the sink and the per-game capture |
| How is a result tied to its build? | [7–8](#decision-7): code identity by fingerprint, data identity on the case; release and fingerprint joined by the commit | Batch fingerprints have coverage gaps; served games have no fingerprint and an unverified release stamp |
| How does a served game record itself? | [9–12](#decision-9): one trace per task run; a capture at the end; counts not costs; errors without secrets | Unit tests; the cache incident; no audit has run |
| What was superseded? | [13](#decision-13): Langfuse as the only store; extraction and dedup cases inside the game | Dated |

### Which tracer, and what it is for

<a id="decision-1"></a>

#### 1. Self-hosted Langfuse, chosen over LangSmith and Arize Phoenix (recorded June 2026).

- *Why, as recorded in the June version of this report:* the backend had to run on the project's own
  host, so the trace data is the project's, avoids a hosted per-trace charge, while leaving infrastructure and storage costs, and any old span can later be
  mined into a new kind of case. That ruled out LangSmith, whose self-hosting is a paid tier. Between
  Phoenix and Langfuse, both open source, two needs chose Langfuse: hand-shaped spans that carry a case
  in their output and are read back by name, which Langfuse's SDK is built for while Phoenix leans on
  automatic instrumentation; and LangGraph wiring through Langfuse's standard LangChain callback.
  Scores and sessions, which the pipeline uses, come with it.
- *How firm:* a judgement of fit at the time, not a benchmark or a current feature comparison between the products.
- *Cost accepted:* the project runs and stores the stack itself, and its storage has filled the host's
  disk (the [disk incidents](#disk-full-spans-silently-dropped-2026-06-07-to-2026-10-22)).

<a id="decision-2"></a>

#### 2. Each case is shaped when the decision is made, not derived from the trace later.

- *Instead of:* keeping only the raw trace and building cases from it on demand, which keeps every
  option open.
- *Why:* some fields are available at decision time but are not otherwise guaranteed to be retained: the
  wide pool of memory candidates before reranking cut it down, the private context as assembled for the
  seat, the queries that drove the lookup. And reading heavy traces back in bulk did not scale (the
  [422 incident](#the-422-collapse-2026-06-11)).
- *Cost accepted:* a field not retained in the case or another surviving record cannot be recovered later. The flexibility
  that remains is at the set level (choosing which cases go into a test set) and through Langfuse's
  generic span fetch, which can still mine any retained span.

<a id="decision-3"></a>

#### 3. The local record is primary; the tracer is a secondary archive (2026-06-11).

- *Instead of:* the 2026-06-06 design, in which every evaluation consumer read its cases from Langfuse
  and no local copy was kept ([decision 13](#decision-13)).
- *Why:* the 422 incident. A tracer's read API caps query cost, truncates large outputs and ties every
  build to a service being up; a local file has none of those limits.
- *Exceptions today:* a served game's cases exist only in Langfuse (decision 9); stage fit reads served
  games' traces for event timing (`evaluation/experiments/stage_fit.py`); and the learning loop reads a
  session's cost from Langfuse (`evaluation/src/loop/cost.py`, through
  `evaluation/src/data/sources/langfuse.py::session_cost`).
- *Evidence:* on a throwaway game in June, the case set built from the local file and the one built from
  Langfuse had identical `(trace_id, observation_id)` sets. The local copy also survived the 2026-07-21
  deletion of the trace data, which cost the evaluation record nothing.

### How a record is kept consistent

<a id="decision-4"></a>

#### 4. The local and Langfuse copies of a case have one shape.

The local record is written as the reader's normalised span dictionary, so the `*_case_from_span`
converters and the frozen-set builders read either source unchanged, and a case keeps its id across
both. The rejected alternative was two converters, one per source, which would add a risk of silent format drift.
Test: `tests/evaluation/test_eval_case_sink.py` round-trips sink records through all four converters.

<a id="decision-5"></a>

#### 5. Span names are defined in one module.

Producers and the Langfuse reader import the prefixes and name builders from
`Agents/observability/span_names.py`. Before 2026-06-11 both sides hard-coded the names, so a rename on
one side would leave a builder matching nothing, with no error. The module also names its one sharp
edge: the extraction case's span and its per-role model calls share a prefix, so a reader must pick the
parent span by structure, not by prefix.

<a id="decision-6"></a>

#### 6. Per-game accumulators travel with the game, not in globals or graph state.

The metrics and the case sink are handed to the graph as LangGraph runtime context, so they collect one
game's records with no shared mutable state. The prompt and reads capture followed on 2026-10-14: it had
been one process-wide list, which the server never cleared, so served games' prompts interleaved across
games. It is now a context variable set per game. Test: `tests/engine/test_turn_capture.py` (two games
at once never write into each other's capture).

### How a result is tied to its build

<a id="decision-7"></a>

#### 7. Code identity goes in the fingerprint; data identity goes on the case.

- *The split:* the fingerprint records code identity and selected model and runtime settings. This
  is partial provenance: model services and database catalogue settings are not fully versioned by
  the source commit. Which store a lookup read, and whether reranking or filtering ran, is data, so it is
  stamped on every turn case (`EvalProvenance`). A frozen case is copied out of its trace, so without
  the stamp the store behind a lookup could only be found by joining back to the trace.
- *Why it mattered:* in two unpaired 30-game batches before the v5 rebuild of the game, the village
  with memory on for every role won 29 of 30 games in one batch and 22 of 30 in the next, while two
  things changed at once: the store version, and how finely the store was split by role and phase
  ([effectiveness](../memory_system/effectiveness/report.md)). The record could not say which change
  mattered. The stamp was added in the 2026-06-06 audit of what a game must record.

<a id="decision-8"></a>

#### 8. The release field and the fingerprint, joined by the commit (batch path).

The release is the commit as Langfuse's own filterable field; the fingerprint is the full record; the
same commit in every batch record joins the two. A reader filters traces by release, reads the
fingerprint, and lines it up with the batch records. The detail is the
[fingerprinting report](fingerprinting/report.md)'s. Served games have no fingerprint; their release stamp is expected to be `unknown` without an override (the
[build section](#which-build-served-a-game)).

### How a served game records itself

<a id="decision-9"></a>

#### 9. One trace per run of the game's task, grouped by the game id (September 2026).

- *Instead of:* one trace per game, forced by seeding the trace id from the game id, so that a game
  resumed after a restart would continue its trace.
- *Why:* the seeded id made the SDK treat the root span as the child of a remote parent that did not
  exist, so the trace had no root and lost its name; handing the ids to the callback instead made the
  graph's own chain span a second root, which Langfuse then named the trace after (`GameSession._run`,
  comments). Grouping by session keeps a game findable by its id.
- *Cost accepted:* a resumed game is two traces, and the cases inside them are the only copy (the sink is
  not written; no record says why).
- *Evidence:* `tests/server/test_game_session.py` checks one named root, the session, and no explicit
  ids anywhere.

<a id="decision-10"></a>

#### 10. Save completed-game prompts once; provide an offline audit job (2026-10-14).

- *Why, as recorded in the code:* each prompt repeats the conversation so far, so a game's prompts run
  to megabytes of repeated text, which gzip shrinks many times over. They sit in a table of their own
  because the game listings read whole `games` rows. The audit runs from a checkout on the host because
  the checks live in `tests/`, outside the server image.
- *Cost accepted:* a game that never completes has no capture, a game resumed after a restart has only
  the part after it, and the audit depends on a scheduled job someone has to install.
- *Evidence:* `tests/server/test_leak_audit.py` (below). The cache incident is the first use of a capture
  recorded here.

<a id="decision-11"></a>

#### 11. The ledger stores counts, and the cost is worked out when read.

`server/game/usage.py` says why: a price can change on a date and some providers bill by hour, so counts
are kept per model and hour, and pricing them at read time means a corrected price corrects every game it
applied to. The cost: a model with no price for that date shows no cost at all ("never a guess").
Test: `tests/server/test_usage.py`.

<a id="decision-12"></a>

#### 12. Report exceptions with explicit collection limits and credential redaction (2026-10-17).

`server/error_reporting.py` gives the reasons: a game's creation request carries the player's API key,
and so can a stack frame's local variables, so every collected category is named and turned off; the
model-provider integrations are off because they would report every 401 and 429 the turn already
handles; and only real exceptions become reports, to keep within the plan's quota. Test:
`tests/server/test_error_reporting.py` (off without a DSN; a failure is tagged and never carries the
keys; private fields are dropped at any depth).

### What was superseded

<a id="decision-13"></a>

#### 13. Superseded designs, with dates.

- **Langfuse as the single source of truth** (2026-06-06), replaced by the local-first rule on
  2026-06-11 (decision 3).
- **Extraction and dedup inside the game.** In June a game's last step ran extraction, and the dedup
  pass after it wrote a case per decision into the game's trace. Since a ruling on 2026-10-12 extraction
  is an offline batch job: the game saves only its extraction input, and the dedup cases come from the
  offline job when it runs.

## Incidents

### The 422 collapse (2026-06-11)

**Verdict.** Building a frozen test set from Langfuse failed with HTTP 422 on long games: in one
five-game session, 3 traces built and 2 failed. The builder fetched every span of a trace (hundreds to
thousands per game) and filtered on the client, and the self-hosted server's query-cost guard rejects
that once a trace is large. It was a read-side inefficiency the longer nine-seat games exposed, not a
tracing bug, and not rate limiting. The fix made the local case file the primary source and rebuilt the
Langfuse reader to list a trace's spans cheaply and then fetch only the named case span. Afterwards all
20 games of the seed batch built with no 422, every record's discussion text full length (20,416 to
43,477 characters). One more limit was found live: the SDK's read timeout of about 5 seconds was too
short for listing a fresh 1,439-span trace (about 7 seconds), and it is now 120 seconds.

**What it taught.** For this workload, evaluation needed a bulk-readable source independent of the trace service. Write
the gradable record locally at run time, in the same shape as the tracer's copy. Define span names once.
And test a read path against the largest trace you expect: this one had worked on smaller games. The
forensics (why date bounds, the cheap listing call and a naive name filter each failed) are in
[the issue record](implementation_notes/ISSUE_frozen_set_fetch.md) and its
[plain retelling](implementation_notes/frozen_set_fetch_explained.md).

### Disk full, spans silently dropped (2026-06-07 to 2026-10-22)

The host's disk filled five times, from Docker logs, build caches and, once, the trace data itself. On
2026-07-09 traces appeared with missing heads, a game "starting" in the middle of a night: the object
store behind Langfuse refused writes at its minimum-free threshold, the Langfuse server returned 500s,
and the SDK retried and then dropped the span batches without an error in the game. On 2026-07-21 the
trace data had grown to 43 GB, and the object-store and ClickHouse volumes were deleted, keeping
Langfuse's own PostgreSQL. Traces from before that date are gone, including Langfuse sessions that June
records cite as their evidence; the local records were untouched. The working rule since: when a trace
looks truncated, check the disk first. (Recorded in the project's operations notes, not in `evidence/`.)

### Server traces with no root, or named "LangGraph" (September 2026)

The first served traces were seeded with the game id as trace id, to keep one trace per game across
restarts. The root span then hung under a parent that did not exist, so the trace had no root and no
name; passing the ids to the callback instead made LangGraph's chain span a root, and Langfuse named the
trace "LangGraph" and took the chain's output as the trace's. The fix is decision 9.

### An empty trace was a human, not a stall (2026-08-24)

The first game served through the proxy stopped at "player_2 is thinking", and Langfuse showed no model
call, which pointed at the new model selection. The seat was the human's: the browser had lost its seat
cookie behind the proxy and never received the turn's controls
([server challenges](../../frontend/docs/server_encountered_challenges.md) §7). The absence of a trace
said only that no model was called.

### The cross-game node cache (fixed 2026-10-26)

The engine caches some AI turns in process memory, so that a resume after a human's answer does not pay
for them again. Its key covered the turn's payload but not the game, so two served games with the same
lineup could share a seat's day-1 opening. In game `51226f24` (GPT-6 Luna, 2026-10-17), the Serial
Killer at `player_9` passed with "generation failed", the failure of a game played nine minutes earlier
on Claude Haiku 5.5. Three records, combined with the cache investigation, supported that diagnosis. The capture held day-1 opening
prompts for 8 of the game's 9 AI seats, none for `player_9`. The event log held the `generation_failed`
pass shown above. And the usage ledger recorded 142 calls for the game with none failed, where a real
failed call is counted. A node-cache hit skips the instrumented turn body, so it produces no fresh model call or prompt
capture. There is no explicit cache-hit record here; the investigation had to correlate the other
records. Mechanism, fix and extent:
[orchestration, decision 12](../gameplay/orchestration/report.md#decision-12).

## How it was checked

| What | How | How far to trust it |
|---|---|---|
| The sink and its converters | `freeze_case` stamps the ids and returns the dump; no sink means no copy; sink records round-trip through all four converters (`tests/evaluation/test_eval_case_sink.py`) | Unit tests on the shared shape |
| Building from the local copy | Cases grouped by trace and filtered by kind; the extraction builder builds from local files; a build needs exactly one source (`tests/evaluation/test_local_case_source.py`) | Unit tests |
| Per-game prompt capture | Two games at once never write into each other's capture (`tests/engine/test_turn_capture.py`) | Unit test |
| The served capture and audit | A capture round-trips through its compressed form; the audit finds a saved game clean, flags a planted leak and reads the dead roster from the saved state; concurrent served games save only their own prompts; a capture that cannot be saved never fails the game; the command prints a line per game, records verdicts and fails on a leak (`tests/server/test_leak_audit.py`) | Unit tests; the audit has never run on the 11 real captures |
| The usage ledger | Counts per model, a failed call adds no tokens, cache writes priced at their premium, a restarted game carries on, saved at most every 30 s and at the end (`tests/server/test_usage.py`) | Unit tests |
| Served traces and Sentry | One named root in the game's session with no explicit ids (`tests/server/test_game_session.py`); Sentry off without a DSN, keys never sent (`tests/server/test_error_reporting.py`) | Unit tests with a fake client; nothing checked against the live trace store here |
| What a game must record (June) | The 2026-06-06 audit listed every consumer and the fields each needs, found five gaps and closed four (the candidate pool, the day-summary case, the store stamp, the metrics in the batch record); on a seeded game with every memory option on, 72 of 72 turn cases carried the store stamp, and 46 of 72 the candidate pool (the rest were day-1 skips and roles with no stored lessons) | One nine-seat game; the June trace it was read from no longer exists ([log](implementation_notes/experiment_log.md)) |
| Night turns (June) | Smoke games showed the single-target night roles' cases nested under the root with the right target ([log](implementation_notes/experiment_log.md)) | Three nine-seat smoke games |
| The records on this page | The sidecar, capture, manifest and served rows shown above were read on 2026-10-26 | One example per record; read-only |

The tests are largely AI-written and not yet audited; this page names them and what they assert, never a
count.

## What is not recorded, and what is not read

**Closed or changed since June.**
- *"Wolf-night discussion emits no evaluation case"* (June). Today every turn of the pack's night,
  the chat, the carrier's kill and each wolf's skill, goes through the night pipeline
  (`Agents/turn/pipeline.py::run_memory_informed_night_action`) and writes a turn case, with a `kind`
  that tells the three apart since 2026-10-11. What a chat case still lacks is the line itself (above).
  When the gap closed is not recorded; a dated note in the
  [log](implementation_notes/experiment_log.md) gives what the June files show.
- *"`round` is vestigial"* (June). At night it now numbers the pack's chat rounds and marks the kill and
  skill turns. A day turn's round is always 0, so a seat's discussion turns on one day share one span
  name: in game `8d33c5a3`, 20 span names repeat, one 9 times. The case id is unaffected.
- *Day-summary spans with an empty game id* in games before 2026-06-11: closed that day; old artifacts
  are joined by trace id ([issue record](implementation_notes/ISSUE_frozen_set_fetch.md)).

**What a served game does not record.**
- **Its build.** No fingerprint, and a release stamp that by the code reads `unknown`. A result from a
  served game can be tied to its code only through the deploy log's dates.
- **A durable copy of its evaluation cases outside Langfuse.** The session's sink remains in memory.
  This leaves those cases dependent on trace retention. The report records no routine builder using
  served cases, although a Langfuse reader exists.
- **The prompts of games that did not complete,** or of the part before a restart. Two prompt builders
  are never logged: the memory lookup's query and the human seat
  ([agent boundaries](../agent_boundaries/report.md) §5).
- **An explicit cache hit.** Cached turns skip the prompt/model-call instrumentation, and the server
  drops cached chunks without a cache-hit log line.
- **A hang.** No watchdog notices a game that stops producing output while nothing fails
  ([server design notes](../../frontend/docs/server_design_notes.md) §5c, mode 4).

**What a fingerprint does not reliably identify.**
- **The actual backend for each model.** `runtime_fingerprint()` sets `llm_backend` to `vertex` or
  `google` from a legacy switch, independently of the selected model's provider. The original review
  records Claude examples stamped `vertex`; this pass confirms the code path, not those artifacts.
- **The complete prompt and runtime configuration.** The prompt hash covers only top-level
  `Agents/prompts/*.py`, excluding nested role cards and other prompt packages. The fingerprint also
  omits the rescue model and resolved per-model catalogue settings. An equal fingerprint is therefore
  evidence about covered fields, not proof of identical prompts or execution.

**What a batch run does not record.**
- **Its prompts, on disk.** `run_batch` checks them in memory and keeps no copy; only the voice-game
  runner saves them.
- **Some requested settings, outside the experiment folder.** The deduction mode, the voices and the
  stage filter are in `config.json`, not on each game record ([fingerprinting](fingerprinting/report.md)
  §5).

**Records that are written but not routinely read.**
- **The prompt captures.** None of the 11 has been audited: the nightly job was found not installed on
  2026-10-23 ([deterministic audits](../evaluation/deterministic_audits/report.md), case 1).
- **The Langfuse scores.** The same metrics are in each batch record, which is what evaluation reads; no
  reader of the scores was found in `evaluation/`.
- **The checkpoints.** Kept for every game and read only when a replay needs one. Why 19 of the 68 game
  rows have no checkpoint thread was not checked.

## When to revisit the design

| Choice | Assumption | Evidence that would justify revisiting it |
|---|---|---|
| Served cases only in Langfuse (9) | Trace retention is sufficient for later case retrieval; no rationale for omitting persistence is recorded | Preserve case files or database records when served turns become evaluation inputs |
| No fingerprint on served games | Deployment dates provide enough attribution; no explicit design rationale is recorded | Store build and resolved runtime configuration with the game, especially when comparing served failures |
| Capture at game end only (10) | End-of-game persistence is sufficient despite losing unfinished and pre-restart prompts | A leak suspected in a dropped game, or frequent restarts mid-game |
| Local file primary, tracer secondary (3) | The tracer's read path stays secondary | A new reader that needs span timing or cost from many traces |

## Code and data

| Part | Code |
|---|---|
| The tracer client and the release stamp | `Agents/tracing.py` (`create_langfuse_handler`, `flush`) |
| Cases, the sink, span names | `Agents/observability/` (`case_sink.py::freeze_case`, `EvalCaseSink`; `span_names.py`); `Agents/schemas/evaluation.py` |
| Where cases are written | `Agents/turn/pipeline.py`; `Agents/nodes/day/flow.py`; `Agents/nodes/orchestrator.py::post_game_analysis`; `Agents/memory/deduplication/pipeline.py` |
| The prompt and reads capture | `Agents/turn/eval.py` (`TurnCapture`, `TURN_CAPTURE`, `log_prompt`, `record_reads`) |
| The batch entry and its records | `Agents/main.py::run_game`; `scripts/run_batch.py`; `evaluation/src/data/batch_layout.py` |
| The capture scripts | `evaluation/experiments/phase3_capture.py`, `persona_voice_games.py` |
| Reading cases back | `evaluation/src/data/sources/` (`sidecar.py`, `langfuse.py`, `replay_api.py`) |
| Rebuilding a turn | `evaluation/src/replay/hallucination_bench.py`, `situation_summary.py` |
| The served game | `server/game/game_session.py::GameSession`; `server/storage/game_repository.py`, `prompt_captures.py`; `server/housekeeping/leak_audit.py`; `server/graph_runtime.py`; `server/game/usage.py`; `server/error_reporting.py` |
| Provenance | `Agents/run_fingerprint.py`; contract in [fingerprinting](fingerprinting/report.md) |

The June build records are in [`implementation_notes/`](implementation_notes/experiment_log.md): the
night-turn coverage and the sufficiency audit, the 422 issue record and its plain retelling, and the
smoke-game logs.

*Originally rewritten 2026-10-26 from `5d8ea41c` and historical records, replacing the batch-only
June report. This editorial revision adds targeted code checks and distinguishes configured recording
paths from observed production data. Historical counts and incidents were not independently rechecked.*
