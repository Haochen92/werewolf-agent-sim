# The cache key that crossed games

*Level 3 · parent: [Adding a human in the loop](human_in_the_loop.md), “Replaying a step must preserve the right result” · third version, 2026-10-28 · for the owner's review.*

## Page copy (draft)

An AI turn cache was meant to preserve decisions when a game resumed after a human player's pause.
Its key recognised equal turn inputs, but did not identify which game they belonged to. Because the
server shared one cache across games, a matching turn in another game could retrieve the stored
result without making its own model call.

The investigation attributed one hosted game's failed opening to this mechanism. A separate
controlled reproduction demonstrated cross-game reuse and checked the fix: adding game identity
while preserving reuse after a pause.

### Equal inputs did not mean the same turn

The [parent page](human_in_the_loop.md) explains why resuming a human turn can repeat completed AI
turns in the same round. Caching those results avoids asking the agents again when their inputs have
not changed. This is an answer cache: it stores the completed turn's result, rather than merely
reducing the cost of processing a prompt.

LangGraph looks up that result using the node—the execution step being run—and a key computed from
the turn's input, or **payload**. The server's compiled graphs share a cache across games. Before the
fix, neither the game's ID nor the model was included in the payload used for the key.

Vote inputs contained the discussion so far, making matches between games less likely. That was
incidental protection, not an explicit boundary. The opening round exposed the difference. Before
any discussion or night action, two games could give a seat the same role, public lineup and other
input values. Those turns belonged to different games but produced the same cache key.

The cache also retained fallback results. If an opening's model call and retries failed, the turn
returned a legal pass marked “generation failed”. From the cache's perspective, that was a completed
result like any other. A later matching turn could therefore inherit the failure without attempting
a fresh call—even if its game used a different model.

### A failed opening appeared in another game

In the first game, model calls failed and the opening turns became fallback passes. Nine minutes
later, a second game using another model dealt the same public lineup. One AI seat had the same role
in both games. Its opening was again a “generation failed” pass, but the second game's records
showed no corresponding model call.

Three records supported the diagnosis:

| Record from the second game | What it showed |
|---|---|
| Prompt capture | Opening prompts for eight of the nine AI seats; none for the affected seat |
| Event log | The affected seat passed with “generation failed” |
| Usage ledger | No failed model calls in the game, although failures are counted |

A cache hit bypasses the code that calls the model and captures its prompt. Reusing the earlier
fallback explains why a failure appeared without a new prompt or failed call, at the seat whose
input matched the earlier game.

There was no explicit cache-hit event confirming that historical replay. The attribution rests on
the matching inputs and these records together. The [observability
report](../../../evidence/tracing/report.md) describes how the records were compared; the controlled
reproduction below checks the failure mechanism separately.

### Separate possible collisions from actual impact

An offline check dealt 12 games and computed their day-1 opening keys without calling a model.
Among the 66 pairs of games, seven pairs shared at least one opening key. This demonstrated that
ordinary dealt inputs could collide. It did not measure how often hosted games actually reused
another game's result.

Actual reuse also required the earlier answer to remain in the same server process's cache. Its
six-hour lifetime and server restarts limited that opportunity. Other potentially matching hosted
games showed no identifiable copy, but restart times were not checked and prompt captures were
available for only 11 of 68 hosted games. The records therefore support one attributed incident;
the total number of affected games remains unknown.

### Add game identity without breaking resume reuse

The game ID already existed in execution configuration, but the cache key read only the payload.
Saving checkpoints under separate game IDs did not automatically separate their cached answers.
I changed the nodes that invoke the subgraphs to copy the ID into their inputs, so each cached
turn's payload includes its game identity.

The lookup boundary changed as follows:

| | What distinguishes a cached result |
|---|---|
| Before | Node and turn-input values |
| After | Node and turn-input values, including the game ID |

This needed to preserve an earlier fix. The default cache key had used a serialized object
representation that changed after checkpoint reload, even when the input values stayed equal.
The replacement key uses **canonical JSON**: the values serialized in a consistent order.
Adding game identity must keep that stability while separating different games.

The regression checks cover both requirements:

- **Same game, reloaded input:** saving and reloading a payload through the checkpoint serializer
  retains its key.
- **Different games, matching turn inputs:** adding their distinct IDs separates their opening keys.
  The isolation test fails when the game ID is omitted.

Tests also check that the day and wolves' night wrappers pass the game ID into their payloads. The
ID must reach the actual cached turn; its presence elsewhere in the system is insufficient.

To test the fix through execution, two games were run back to back in one process with a shared
cache. Their deals were chosen to give six seats the same roles. A scripted model supplied responses
without live model calls, allowing the same setup to run before and after the fix.

| Code version | Second game's openings reused from the first game's cache |
|---|---:|
| Before the fix | 5 |
| After the fix | 0 |

Two further games on the same deals, using a real model on the fixed code, each made all ten opening
calls. A pre-deployment check also confirmed separate opening keys for two freshly dealt games
inside the production image. I deployed the fix on 2026-10-26. These checks establish the separation
in the tested cases; the five-to-zero comparison is the direct before-and-after control.

### What the fix guarantees—and what it assumes

Game identity is now an explicit part of the key. Identical turn inputs from different game IDs no
longer rely on incidental details, such as a distinctive transcript, to keep their cached results
separate. Within a game, checkpoint reload still preserves the key needed to reuse a completed turn.

The model remains outside the key. Reuse therefore assumes that answer-affecting settings outside
the payload stay unchanged during a game. Adding the game ID also does not make the in-memory cache
survive a restart; the parent page explains that persistence limit.

The opening-round change exposed the missing boundary because its inputs differed from those of
the votes that had motivated caching. Extending the pattern to another turn type requires checking
both properties again: intended retries must match, and unrelated turns must remain separate.
Those checks must include fallback results, which are reusable answers from the cache's perspective.

**Evidence.**

- [Orchestration report](../../../evidence/gameplay/orchestration/report.md), decision 12 and “What is not established”: mechanism, incident, collision check and controlled reproduction.
- [Server incident record](../../../frontend/docs/server_encountered_challenges.md), §§3–5: repeated execution, answer caching and key stability after checkpoint reload.
- [Observability report](../../../evidence/tracing/report.md), “The cross-game node cache”: the records supporting the historical attribution.
- [Deployment log](../../../frontend/docs/deploy_log.md), 2026-10-26: deployment and production-image check.

<!-- Authoring note, 2026-10-28
Third version requested as cache_key_revision.md; cache_key.md is unchanged. Written independently
without the portfolio skill, following the outline approved in the conversation. This is an
editorial rewrite with targeted source checks, not a fresh code audit or new execution experiment.
The original page retains the full drafting brief and historical source mapping.

Source mapping:
Opening/mechanism: evidence/gameplay/orchestration/report.md decision 12, “Failure mechanism”,
“Recorded incident”, “Fix”; frontend/docs/server_encountered_challenges.md §§3–5.
Opening adoption: 2026-10-07; key scopes by node and payload, not checkpoint thread. Canonical JSON
addresses changed object metadata after checkpoint serialization, not uniqueness between games.

Historical case: 14926d10 (2026-10-17 07:44, Haiku 5.5) → 51226f24 (nine minutes later, GPT-6 Luna).
Matching seat: player_9, Serial Killer. Evidence/tracing/report.md “The cross-game node cache”:
8 of 9 AI opening prompts captured, no affected-seat prompt; generation_failed event; usage ledger
142 calls and none failed. No explicit cache-hit record; attribution rather than direct capture.

Reach: orchestration decision 12: 7/66 pairs among 12 games, 8 matching seats in total. Other 19
potentially matching hosted-game pairs showed no copy. Restart times unchecked; 11/68 prompt
captures. For uncaptured games a copied pass is detectable only when its carried private note is
distinctive. Report records no lost opening calls in recorded batch/capture runs. These details
bound detection; they do not provide an incident-rate estimate.

Fix/tests: orchestration decision 12 and “What is not established”; original page source map points
to tests/engine/test_turn_cache_key.py for serializer round-trip, wrapper propagation and opening
isolation across the 12 dealt games. Two controlled deals shared six seat roles; scripted comparison
5 reused openings before, 0 after. Real-model check: same two deals, Haiku 5.5, all ten opening calls
each on fixed code (2026-10-26). Deploy log: 2ecec0cc, preflight key separation in production image.
No statement is made about games served since deployment.

Remaining assumptions: orchestration “When to revisit the design”, process-wide cache keyed by
payload and game ID; within-game model/settings remain stable if absent from key. Six-hour cache
is in process memory. Previous page's five-choice history is condensed here into necessary context;
it remains in cache_key.md and the linked source records.
-->
