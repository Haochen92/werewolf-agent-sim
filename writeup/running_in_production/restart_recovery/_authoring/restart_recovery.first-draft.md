# How a Werewolf game resumes after a server crash

*Level 2 · [Running it in production](../running_in_production.md) · Revised draft, 2026-11-22*

## Page copy (draft)

In Werewolf, human and AI players discuss suspects in public, but wolves can also speak privately at night. If a player's browser disconnects during a vote, the game keeps running. When the browser reconnects, it tells the server the number of the last event it received. The server sends the events that player missed and was allowed to see, including private wolf messages if the player is a wolf.

### What the server needs to bring a game back

When the server itself stops, it loses every game it held in memory. On startup, it looks for games marked as running and uses two records in Postgres to recover each one.

- The **event history** records what happened in front of players, including speeches, votes and private messages. The server reloads it so each returning player can catch up.
- A **checkpoint** saves the information the game engine needs to keep playing, including whose turn it is, which abilities players can still use and whether someone owes an answer. The engine resumes from its latest checkpoint.

Rebuilding the engine from events alone would require recording every change to the game, including changes no player sees. More secrets would then depend on the server filtering the event history correctly for each player. The framework that runs the game, LangGraph, already saves checkpoints. Using them lets the engine recover its private state while the event history serves the players. The trade-off is that the database saves the two records separately.

### What a player comes back to

In one manual test, the server process was killed while a solo game was waiting for the player to answer. After the restart, the player saw the same question and asked the AI to take that turn. The game continued. A separate integration test uses scripted AI players and a real Postgres database. It recreates the server components at a pending question, plays to the end and checks the saved history for gaps and duplicate event numbers.

What happens to a particular player depends on what was saved before the crash.

| Before the crash | After the restart |
|---|---|
| The engine saved a question for a human player. | The player can answer it again. A living solo player has no deadline. In multiplayer, the timer starts afresh and can shorten if the player is disconnected. |
| The server confirmed receipt of an answer and still held it only in memory. | The player may need to submit the answer again. |
| The project was paying for AI calls. | The game can resume using the project's credentials. |
| A player supplied an API key to pay for AI calls. | Someone with a seat in the game must supply a key again. Player keys are kept in memory. |
| Players were waiting for the game to start. | They need a new room. The server starts saving a game once play begins. |

### What if the server stops during an AI speech?

A speech can reach a browser before the database saves it. The engine also saves its progress separately. Inspecting the order of those writes identified two possible outcomes. The restart tests exercised a game waiting for a human answer. Neither test interrupted these writes.

**If the speech was saved but the checkpoint still shows the speaker's turn**, the engine can ask the model to speak again. Suppose the first speech accused Alex and the second accuses Sam. The server recognises a speech by its day and its place in the discussion, so it keeps the accusation against Alex in the history players see. The next AI player, however, can receive the accusation against Sam from the engine and respond to it. Suppressing a duplicate in the history still leaves the cost of a second model call. The amount of repeated work on the hosted server has yet to be measured.

**If a player saw the speech before it was saved**, the restored history has no entry for that turn. If the engine repeats the turn, the accusation against Sam can become the saved version even though the player remembers hearing Alex accused. During normal play the server retries failed writes. A crash before the retry loses any events still waiting to be saved.

<!-- Sources
evidence/production/serving_and_restart/report.md §§1.2–1.3, 3–5; evidence/production/session_and_human_turn/report.md §§5–6; manual restart record in commit 5d63349a (question at event 56, delegated turn, continued to event 77).
Supporting detail: startup closes finished games from history and records individual recovery failures before continuing. Wolf messages use day, round and wolf as their identity. Restart loses the in-memory AI decision cache. In a small test graph a top-level parallel step repeated only unfinished tasks, whereas a nested parallel step repeated every task.
-->
