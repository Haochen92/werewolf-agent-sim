# Explanation prototype: Running it in production

Page: `writeup/running_in_production/running_in_production.md` · Level 1 · Purpose: chapter overview,
with the first section explained as a mechanism · Date: 2026-11-20
Checkpoint: waived by the owner on 2026-11-22 (full draft first; a different model reviews and
revises it; the owner then reads the revised version). The four sections and the three Level 2
pages were agreed in conversation on 2026-11-18 to 2026-11-20.

Authoring material, not page copy. Topics and sources: [`content_plan.md`](../content_plan.md),
revised by the 2026-11-20 agreement recorded under "Elsewhere" below.

## Reader and explanation

- **Reader outcome:** the reader can say what changed when a game that ran from the command line
  was put in front of people: what a restart can repeat, what a timeout bounds, how one apparent
  model failure was diagnosed from the records, and what the server does with a player's key and
  a player's words.
- **Starting knowledge:** chapters 1 to 6 supply the game, the engine, the agent turn and the
  human turn. New here: a web server that holds many games; two saved records (events and
  checkpoints); a timeout per attempt and a rescue model; the records a hosted game leaves.
- **Concept order:** blocking step and worker thread → event history against checkpoint → what a
  restart reads from each → a provider that waits instead of failing → records that disagree →
  a key held in memory, and words that enter other seats' prompts.
- **Likely confusion:** that "resumes after a restart" means nothing is repeated. The page says
  what is repeated and that a stop in the middle of a write has not been reproduced.
- **Section order:**
  1. *Opening.* A player closes the tab and the server restarts: two questions, two records. Sets
     up the diagram.
  2. *Keeping a game running.* Follow one speech: worker thread, event saved, checkpoint saved
     separately; what a reconnecting browser and a restarted server each read; what can run again.
     Why threads, and that capacity is unmeasured. Link to Level 2 A.
  3. *When a provider stops answering.* A rescue existed and a player still waited five minutes,
     because the provider waited instead of failing. Timeout per attempt, rescue where the game
     has one, otherwise a legal default; a whole turn has no deadline. Link to Level 2 B.
  4. *Finding out what happened.* One seat passed with "generation failed", the ledger counted no
     failed call and the prompt copy held no prompt for that seat. What each record showed; the
     cause is on chapter 1's page. What the server does not record or notice. Link to Level 2 C.
  5. *Handling what a player supplies.* The key: held in memory for one game, checked before the
     game opens, a database test that found a route through a provider's error text. The words:
     code enforces a legal vote and cannot make a voter know who spoke; quoting reduced the
     effect and did not remove it.

## Sample passage

The opening and the first section, as page copy. The diagram is specified, not drawn.

> ### Running it in production: hosting the game for other people
>
> A player closes the tab halfway through a game. When they come back, they should see what
> happened while they were away. If the server also restarted in that time, there is a second
> question: which turn should the engine play next? The browser and the engine need different
> records to answer.
>
> Running a game from the command line let me inspect a failure and start again. Hosting it
> for other people meant four things: keeping a game running while browsers come and go, deciding
> what happens when a model provider stops answering, keeping records that can explain a turn
> afterwards, and handling what a player supplies, which is an API key and typed messages.
>
> **Exhibit:** one hosted game. A boundary around the server process holds the game session and
> the game engine. Outside it: the browser, the model provider, the Postgres database. Four
> arrows: the engine asks the provider for a move; the session streams events to the browser;
> the session writes the event history; the engine writes a checkpoint. The last two are drawn
> as separate writes into the same database.
>
> *The browser catches up from the event history. The engine continues from a checkpoint.*
>
> #### Keeping a game running
>
> One step of a game can wait seconds for a model and minutes for a person, and during that
> wait the server still has to answer every browser. The engine was written as ordinary
> blocking code, and the command line, the batch runner and the tests all call it that way. I
> kept it, and the server runs each blocking step on a worker thread so that the wait does not
> hold up anyone else. Rewriting the engine as asynchronous code would have broken those
> callers.
>
> When an AI player speaks, the server saves two things at different moments. The speech goes
> to every viewer and into the game's event history, which is what a returning browser catches
> up from and what a replay plays. The engine separately saves a checkpoint: the private state
> it needs to continue, such as roles and night targets.
>
> After a restart, the server rebuilds each running game from its event history and resumes
> the engine from its latest checkpoint. If the server stopped after a speech was saved and
> before the checkpoint that follows it, the engine plays that turn again, and the model may
> write a different line. Viewers keep the first line while the engine continues with the
> second. So a restart can repeat a turn; it does not lose the game.
>
> I checked recovery by killing the server while a game waited for a person, and an automated
> test now does the same against a real database. Neither stops the server in the middle of a
> write, so the repeated speech is known from reading the code and has not been reproduced.
> How many games one server can hold at once has not been measured.
>
> **Link:** What survives a server restart? (Level 2 A)

## Evidence and scope

- **Sources:** `evidence/production/serving_and_restart/report.md` (sections 1, 2, 4, 5);
  `dependency_failures/report.md`; `keys_and_input/report.md`; `evidence/tracing/report.md`
  ("The cross-game node cache"); `evidence/agent_boundaries/forged_speaker/report.md`.
- **Claim and limits:** mechanism and decisions, with two incidents (the 301-second draft, the
  cross-game cache) and one test finding (the key in a checkpoint). Limits kept on the page:
  a turn can run again; no deadline on a whole turn; no record of a cache hit at the time of the
  incident (a count of cached steps is saved from image `3c2430d7` on, not yet seen on a real
  game); capacity unmeasured; quoting leaves a gap.
- **Elsewhere:** Level 2 pages in order A restart, B stalled call, C observability. Later: keys
  and input, the human turn, the planted-key and thread-pool investigations. The cache
  mechanism stays on chapter 1's `cache_key.md`. The fingerprint is one clause at most. Off the
  page per the content plan's care list: CI, test authorship, the hosted-game audit job, hosted
  game counts.
- **Open questions:**
  1. Closed 2026-11-22. The reports' headers already read "as of server image `087812dd`"
     (2026-11-19), and each now carries a dated line saying the server has run `3c2430d7` since
     2026-11-20. That release changed only what a hosted game records; the observability report
     (`evidence/tracing/report.md`) describes it. The page describes the deployed state as of
     2026-11-20, with no game yet played on that image.
  2. Whether the house model has a rescue in the live database is still unchecked, so the page
     says "where the game has one".

## Review resolution

| Finding | Action and reason | Whole-section recheck |
|---|---|---|
| | | |

## Trial record

Draft snapshots: none kept. The first draft and its same-day revision (2026-11-22, Claude Fable 5.2
in Claude Code) were deleted at the owner's request once the merged version replaced them. The
skill's two fresh-context reviews were not run.
Owner direction 2026-11-22: a second model outside Claude Code rewrote the draft; the owner
preferred its title, its requirement-first introduction, its section order (requirement, design,
incident, limit), its sub-headings and its standard terms (dual-write problem, failover, circuit
breaker, execution provenance, trust boundary, prompt injection). The page copy now follows that
structure, with these differences from the second model's text: no first-person pronoun anywhere
(owner's ruling); the 0-of-33 row is labelled as the comparison case, not a fix; "mitigation" is
not used for prompt injection (care item 5); the turn deadline (120 s, 30 s after a disconnect)
is kept; the closing is one short paragraph; the link to chapter 1's cache key page is kept.
Framing, 2026-11-22 (owner's idea, refined by the second model): the application is a stateful,
turn-based game with people in it and a multi-agent system that decides through external model
calls; each brings its own problems and the combination adds more (a replayed turn may get a
different model answer; a failed call still needs a move; a valid move can hide a failure). The
introduction and the four section openings were rewritten around it; the four sections and the
closing are unchanged. Not used: any contrast with "an ordinary web application", and the second
model's bold summary sentence.
Level 2 pages, 2026-11-22 (owner: write the Level 2 pages and shorten the Level 1 page; a Level 1
section that stays long gets a short Level 2 page): four pages drafted without a separate brief
or checkpoint, at the owner's instruction, and without the skill's reviews: `restart_recovery/`,
`stalled_model_call/`, `observability/`, and the short `keys_and_player_messages/` (not in the
2026-11-20 agreement, which listed keys and input under "later"). The Level 1 page lost: the
recovery-test detail and the numbered crash steps (to restart recovery); "What remains
unbounded", the sample's caveat and the second-provider incident (to the stalled model call);
most of "Recording which path produced a turn" (to observability); the five-provider fragment
check and the experiment's detail (to keys and player messages).
Model and owner interventions: section selection agreed with the owner 2026-11-18 to 2026-11-20,
after a second agent's proposal; the owner asked for observability as a third Level 2 page and for
the thread and capacity sentences in the first section.

| Owner change | Kind | Explanation redesigned or local edit? |
|---|---|---|
| | | |
