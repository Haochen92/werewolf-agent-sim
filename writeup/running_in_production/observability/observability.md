# Tracing and investigating a hosted game

*Level 2 · [Running it in production](../running_in_production.md)*

## Page copy (draft)

A hosted game can finish successfully even when some AI decisions do not come from the game's primary model. A rescue model might take over after a failure, the server might apply a fallback rule, or a cached result might be reused without making a new model call. To the viewer, these can all look like ordinary game actions.

This makes unexpected decisions difficult to investigate. The game history shows what happened, but not necessarily how a decision was produced. To find out, an investigator needs to connect the visible action with the information available to the AI and the operations that actually ran.

The system records these details in several places. Traces help investigate execution, while the game's own records preserve its events, decision inputs and substitutions. The same decision context is also captured for later evaluation, allowing revised prompts to be tested without reconstructing the original situation from traces.

### What the system records

The game uses Langfuse for execution traces, PostgreSQL for game records, and Sentry for error reporting. Each provides a different part of an investigation.

| Record | What it shows |
|---|---|
| **Game events** | What happened during play, including the actions viewers saw |
| **Prompt captures** | What information was prepared for each AI seat when making a decision |
| **Langfuse traces** | Which engine operations and model calls were recorded, along with their inputs, outputs and timing |
| **Rescue and fallback records** | Which turns used a replacement model or a rule-based action |
| **Usage ledger** | How many model calls were made or failed, aggregated by model and hour |
| **Sentry reports** | Which game tasks or server requests failed with an exception |

A trace groups the operations recorded during one run of the game engine. Each recorded operation, such as an engine step or a model call, is called a *span*. This makes it possible to follow execution and inspect individual model calls, rather than relying only on the final actions recorded in the game.

Langfuse is self-hosted. It was chosen over LangSmith because it is open source and has no licence fee for this deployment. It also keeps tracing data on the project's own server, at the cost of operating the service and providing storage.

PostgreSQL holds the game's events, checkpoints, prompt captures, usage records and information about rescue and fallback turns. These are the game's own records, and they exist whether or not a trace was kept.

Sentry handles failures that raise exceptions, rather than every unsuccessful AI decision. Request bodies and stack variables are excluded from its reports because they could contain a player's provider API key.

### Investigating an unexpected decision

Suppose a viewer asks why an AI seat voted for a particular player.

The event history identifies the vote, the seat and the point in the game when it happened. But it cannot explain whether the AI had a particular clue or whether the vote came from the primary model.

The next step is to check the **prompt capture**. For a completed game, this contains the named inputs prepared for each AI seat, including its private information. An investigator can check whether a clue was available to the voter, although the capture does not include the final rendered prompt or establish whether the model actually used that clue.

The **Langfuse trace** provides a different view. It shows the recorded steps through the engine, including model calls and their responses. This helps determine which operations ran and where execution time was spent.

However, these records do not always tell the whole story. If the primary model failed, another model or a fallback rule might have supplied the action. The server records these substitutions separately, identifying the affected seat and turn.

The usage ledger can help establish whether model failures occurred during a game, but its totals are aggregated by model and hour. It cannot reliably connect an individual call to a particular vote.

Together, these records help distinguish what the AI was given, what the engine executed and what ultimately appeared in the game.

### When a decision has no new model call

Some execution paths are especially difficult to investigate because the expected model call never produces the move, or never occurs.

A fallback rule supplies an action when no model gave a usable answer. A cached result bypasses the model entirely. In both cases, the game can continue without raising an exception for Sentry to report.

The server records rescue and fallback turns on the game's own record rather than changing the event format used by browsers and existing replays. Cache usage is also counted, but individual cache hits are not identified by turn.

#### A cached failure that looked like a new failure

One game recorded an opening pass with the reason `generation_failed`. This appeared to indicate that the AI had failed to generate an opening response.

But the other records did not support a new model failure:

- Eight of the nine AI seats had an opening prompt capture. The missing capture belonged to the seat that passed.
- The usage ledger recorded 142 model calls across the game, with no failures.

The explanation came from an earlier game.

Nine minutes before, the same seat in the same lineup had produced a failed opening turn. That failure had been cached. When the later game reached its opening turn, it generated the same cache key and reused the earlier result.

Because the result came from the cache, the engine skipped prompt preparation and the provider call. The game therefore recorded `generation_failed` without generating a new prompt or making a failed model call. This explained the apparent contradiction between the event history, prompt captures and usage ledger.

The investigation also exposed an observability gap: at the time, nothing recorded that a turn had come from the cache. The records only made sense once the earlier game was found. The game's record now counts cache usage, although it still does not identify which turn used the cache. A missing model span alone would not establish a cache hit either, since traces can also be incomplete.

[How the cache key was corrected](../../game_design_orchestration/human_in_the_loop/cache_key.md)

### Following a game across restarts and releases

A hosted game can resume after a server restart because its state is saved in checkpoints. But the original execution trace ends when the process stops. The resumed game starts a new trace.

To keep these records connected, Langfuse groups traces under a session identified by the game ID. An investigator can therefore find execution records from both before and after a restart.

Restarts introduce another problem when the server has been updated between turns. For example, a game might begin with one set of prompts and models, then resume after a release that changes them. If a later vote looks suspicious, the investigator needs to know which configuration produced it.

For each engine run, the server records its start time, trace ID, restart status and a fingerprint covering the build, prompt files, models and selected settings. Game events also carry the time they were written.

Together, these records help associate an action with the execution run and system configuration in use at the time, even when a game spans multiple server processes or releases.

### From investigation to evaluation

Investigating a decision can explain what happened, but it does not show whether a change would produce a better result.

Suppose an AI made a questionable vote after receiving an ambiguous clue. Testing a revised prompt requires the information available to that seat **before it voted**. The final vote and the subsequent game history are not enough to recreate that situation.

The system therefore captures an **evaluation case** while preparing each AI decision, when the seat's context and retrieved lesson candidates are available.

An evaluation case preserves the inputs needed to present that situation to a model again. Evaluation code can use those inputs with a revised prompt and compare the resulting decision with the original. This tests a decision in a saved situation, rather than replaying the entire game.

#### Why evaluation cases are stored separately

The project also runs batch experiments: many games played from the command line to evaluate changes. The earlier evaluation workflow relied on Langfuse traces to recover decision contexts from those games. It retrieved entire traces and searched for the operations containing the required information.

This became expensive because a trace could contain far more data than the evaluation needed. In one five-game batch, two trace queries were refused for being too expensive.

The design was changed so that the batch runner saved evaluation cases directly to a local file for each game. The trace reader was also changed to retrieve only the specific spans it needed, rather than entire traces. In the following batch, all 20 games produced evaluation sets without a refused trace query.

The hosted game follows the same approach. Evaluation cases are assembled as decisions are made and saved to PostgreSQL when the game completes. They can then be exported in the same format as the batch files.

This allows decisions from hosted games to enter the existing evaluation workflow without depending on the availability or completeness of their Langfuse traces. Traces remain useful for investigating how a decision was produced. Evaluation cases serve a different purpose: preserving the situation needed to test that decision again.

[How turn replays are used in evaluation](../../evaluation/replays_and_games/replays_and_games.md)

<!-- Sources
What is instrumented: evidence/tracing/report.md §1 (records map), §4.4 (Sentry collection limits), §7 decision 1 (self-hosted Langfuse over LangSmith; the report also names Arize Phoenix, left off because the owner does not recall weighing it; owner 2026-11-22: chosen because it is open source, free and self-hostable); code: Agents/tracing.py (one client per process, create_langfuse_handler), server/game/game_session.py (the handler attached to each game's run config).
evidence/tracing/report.md §§1–2, 3.1–3.2, 4.1–4.6, 5–6. Game-row versus event marker trade-off: evidence/tracing/reference.md, alternatives considered on 2026-11-20.
-->
