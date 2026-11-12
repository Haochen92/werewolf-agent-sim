# U5 seed notes: moving games to workers

Not a chapter. Points from the U0 revision on 2026-11-11 (U0 Part 4's redesign), kept so U5 covers
them. No unit puts the "engine in workers" redesign together; U5 is the natural home because "pause,
save, resume on any worker" is its subject. U4 covers the redelivery pieces (`u04_seed_notes.md`).

## Split GameSession by its three jobs

| GameSession's job today | Where it goes when games move to workers |
|---|---|
| Drives the engine | → a game worker |
| Sends output to everyone watching | Stays with the API servers (they hold viewers' connections). The worker publishes events and the API servers pass them on. dota2pred's `PubSubHub` (one subscription per process, fanned out to viewers) is the pattern |
| Holds a human's question until they answer | Becomes a record: the game pauses at the interrupt, its checkpoint is saved, the worker is freed. The answer goes through the API server into the queue ("resume game 51 with this answer"), and any free worker loads the checkpoint and carries on |

This answers U0 Part 4's first question ("how does a human's answer reach the worker running their
game?"): while a game waits, no worker is running it. Durable checkpoints make the workers close to
stateless too.

## Scaling means more games, not a bigger game

- Add workers to run more games at once. Each game advances on **exactly one worker at a time**; two
  workers advancing the same game corrupt it.
- Within a turn, the ten AI players' calls already run side by side inside one worker (they're I/O
  waits), so spreading one game across machines gains nothing.
- Over its lifetime a game can move between workers (pause → checkpoint → resumed by any free worker).

## Many games per worker, or one?

Decided by whether the work computes or waits. Werewolf mostly waits (model calls take seconds,
humans take minutes), so one async worker process runs many games, the way the FastAPI process does
today. CPU-bound work (transcoding, training) runs one job per worker or per core.

## What a worker is

A role: a long-running process that takes jobs from a queue and does them. Usually a Python process
(Celery, a Prefect worker, a custom loop) inside a container; scale out by running more containers of
the same image. dota2pred: the Prefect worker inside `live-orchestrator-app`, taking runs from
`dota-work-pool`. The other style, a fresh container per job (Kubernetes Jobs, Modal), fits heavy
isolated jobs like training. It's poor for games: start-up takes seconds, and a game is many short
steps.

## Tracking which worker has which game: a claim that expires

You track a claim on the game, not the worker:

1. **Lease in the database.** `games.claimed_by` + `lease_expires_at`. The worker renews the lease while
   it runs the game (a heartbeat). If the worker dies, the lease runs out and another worker may claim
   the game.
2. **The queue does it.** The job goes to one consumer; if it doesn't acknowledge in time, the job is
   handed to another. dota2pred's `XCLAIM` in `stale_match_service` takes over jobs from silent
   consumers this way.

Without an expiry, a dead holder blocks everything. dota2pred's zombie Prefect run held the
`concurrency_limit=1` slot until `_crash_orphaned_runs` was added (see `u04_seed_notes.md`).

## The trade, for the interview

| | Today (one process) | Workers |
|---|---|---|
| A restart | Stops every game; they resume from checkpoints | Stops one worker's games; others resume them |
| Copies of the API | Impossible (games live in memory) | Free (stateless API servers behind Caddy) |
| A human's answer | A function call in the same process | A queue message that can be lost or doubled (U4) |
| Live output | Direct, in memory | Worker → pub/sub → API server → browser |
| New things to run | None | A queue, a pub/sub channel, game claims |

At hundreds of games the workers design wins; at a few games and one operator the current one does.

## The future a parked seat waits on (from the U2 walkthrough, 2026-11-11)

- U2 (1.1 and 3.3) covers what a future is and gives this case one table row. U5 owns the detail.
- Why I create this future myself, when a model call or a database call needs only `await`: a
  human's answer does not come back on a connection the game holds open. It arrives as a new
  request, handled by a different task. Only my game's rules link "a turn for seat 4 of game A" to
  the task that is waiting, so my code stores the future by seat and the route fills it.
- In the code today: `_pending_answers` holds one future per parked seat, `submit_turn` calls
  `set_result`, `_collect_answers` gathers them.
- My older Heptabase card "Asyncio: Pattern-Level" compares four designs for this (Event, Condition,
  Queue, per-seat Future). The history, from git on 2026-11-12: the first runtime (`42854d75`,
  2026-08-18) used one queue, `_resume_q`, for a single human seat. One day later (`30f8a9ac`,
  2026-08-19) it became one write-once future per seat, because a step that runs seats in parallel
  can ask several human seats at once; `gather` waits for all of them. The Event and Condition
  versions were never in the code. The card is corrected to say so.
- The future lives in one process's memory, so it is lost on a restart and invisible to a second
  process. That is the link to "pause, save, resume on any worker" above.

## One process per game (from the U2 walkthrough, 2026-11-12)

- A third arrangement beside "several processes in one container" and "one process per container":
  a process (or container) started when a game starts and ended when it finishes.
- Buys the strongest isolation, a clean release of everything at the end, and capacity that follows
  demand. Costs seconds of start-up per game, the whole program's memory per game, and something to
  start, watch and clean up the processes. The communication with the API server is the same as for
  long-lived workers.
- It fits heavy calculation or untrusted code. My games mostly wait, so "a few workers, each running
  many games, more added with load" gives the same scaling for far less memory. U2 section 3.8 has
  the table of isolation steps this belongs to.

## When a nested step's prompt reaches the server (from the U2 walkthrough, 2026-11-12)

- A LangGraph specific that U2 section 3.1 only uses as a diagnosis story; U5 owns the mechanism.
- Commit `2814776d` (2026-10-17) measured it on langgraph 1.1.10 with the server's stream settings:
  a parallel step at the top level surfaces its interrupt at once; one nested in a subgraph
  surfaces it only when the step ends. A human wolf's prompt therefore waited for the other wolf's
  model call.
- The fix: the step announces the human's prompt itself at its start (`pack_fan_out_skills`), as the
  vote, the rounds and the solo night roles already did. Design record:
  `frontend/docs/server_client_transport.md` section 8b (options considered, invariants).
- U5 should say what "announce" means here, why an early answer has to be held, and how the
  interrupt that ends the step adopts the already-open question instead of asking again.
- Sources in the repository to read before writing U5 (found 2026-11-12; only their headings read
  so far): `evidence/gameplay/orchestration/report.md` ("Orchestration: how a game runs as a
  graph", the chapter 2 evidence report); `frontend/docs/server_encountered_challenges.md` (eight
  LangGraph problems met while building the server, among them interrupts arriving twice, why the
  engine redoes work after a human answers, and the events table running ahead of the checkpoint);
  and the write-up page `writeup/game_design_orchestration/human_in_the_loop/human_in_the_loop.md`.
  What these already establish should be cited, not re-derived. Several of the eight also bear on
  U3.
- Two Heptabase cards may already cover the library side: "LangGraph's Engine: How It Actually Runs
  Your Graph" and "Parallelization in LangGraph". Not read yet.

## A solo game waits for its absent player (moved out of U2 section 3.4, 2026-11-12)

- U2 section 3.3 keeps only the mechanism: the game's task pulls the engine's output a chunk at a
  time, and the library starts the next step only when asked. U5 owns the behaviour built on it.
- The behaviour: in a game with one human seat, after each chunk, if that player is alive and has no
  stream open, the task stops reading and waits until their browser connects again
  (`server/game/game_session.py`, `_wait_for_absent_player` and the module docstring).
- Details U5 should carry, all from that docstring: there is no grace period (a short drop suspends
  and resumes at no cost, since the step in flight runs either way); the smallest unit that can be
  held back is one step, and a whole day's talk up to the player's next turn is one step; a
  suspended game counts as parked, so the sweeper gives it up after the same shelf life.
- It is a pause by not reading, with no queue limit and nothing refused. U2 says so and does not
  call it backpressure in the 1.4 sense.
