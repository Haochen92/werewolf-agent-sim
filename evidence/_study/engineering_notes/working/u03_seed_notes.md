# U3 seed notes: what today's U0 revision adds to the U3 outline

Not a chapter. The U3 outline in `writeup/_planning/ch7_ch8_syllabus.md` already covers three records
with one authority each, the engine resuming from the checkpoint, the events table not being replayed
into the engine, and the one-step lead. These points came up in the U0 revision on 2026-11-11 and
aren't in the outline. Verified in the code that day.

## The misconception to correct first

I held this picture: "the checkpoint is only used to construct events, and resuming uses the
event log, since the database holds it anyway". The outline's project check ("'recovery replays the
event log' is in a draft; correct it") targets exactly this. Start U3 with it.

## Why the engine resumes from the checkpoint and not the log

The log holds everything *showable*. Private reads (`PlayerReads`), memories consulted
(`MemoryConsulted`) and strategy updates are all events, each with a live audience tier. `OBSERVER` is
"delivered to nobody live; log-only until the game_over unlock" (`server/schemas/events.py`, `Tier`).
The checkpoint holds everything the *engine needs*, including state that is never shown:

- counters and rule state: `uses_left`, `fortune_points`, `no_lynch_streak`, `speculator_pick`
  (`Agents/state/orchestrator.py`);
- the exact input of a paused human turn: the `Send` arg, read back by `GameSession._turn_payload`;
- where the engine is mid-run: `state.next` and the pending interrupts.

Replaying events into the engine would also mean re-running non-deterministic model calls, unless every
reply were recorded. That's the outline's "workflow engines that re-execute code against recorded
history" alternative (Temporal-style), and the reason this project didn't take it.

## Where the server reads the checkpoint (three places only)

1. Restart recovery: `LiveGameRegistry._resume_from_checkpoint`. It re-parks the waiting questions from
   `state.tasks[].interrupts`; an empty `state.next` means the game had in fact finished, so the
   "running" row was out of date.
2. Previewing a paused human turn: `GameSession._turn_payload`.
3. The post-game prompt capture: `GameSession._save_capture`, via `aget_state`.

Events are never built from the checkpoint. They come from the live `updates` and `custom` stream
chunks (`get_stream_writer()` in nodes) through the translator.

## Recovery uses both records, each for its own part

`LiveGameRegistry` restart path: `reload_history(load_events(...), ..., load_cast(...))` rebuilds the
session (what was sent; the send-once guards). Then `_resume_from_checkpoint` restarts the engine. A
human pause uses the checkpoint as well: LangGraph's interrupt + `Command(resume=...)`.

## Timing (one cause of the one-step lead)

Events are written to Postgres after every chunk ("synchronous per chunk: a crash loses at most this
chunk's events", `GameSession` run loop, `_persist_tail`). There is no planned-shutdown flush;
`session.log` is a working copy. The checkpoint is written only when a whole step finishes.

## Store everything once; filter on the way out

The log stores every event with its audience, and the filter (`may_see` in `server/routes/games.py`)
runs per viewer on every send. So one log serves wolves, spectators and the replay, and an audience can
widen at game over. Filtering at write time would have made the unlock impossible. (The detail belongs to
U6/U7; U3 needs only "the client is a projection of the filtered log".)

## Easy to confuse

LangGraph (checkpoints, in our own Postgres via `AsyncPostgresSaver`, `server/graph_runtime.py`) vs
Langfuse (traces; the game never reads them).
