# The cache key that crossed games

*Level 3 · [Game design and orchestration](../game_design_orchestration.md) · parent: [Adding a human in the loop](human_in_the_loop.md), "A stable cache key also needs a game boundary" · status: page copy drafted 2026-10-26 with the level prompts; for the owner's review.*

## Brief

Copied from [`../content_plan.md`](../content_plan.md), "Level 3 candidates", "Selected" (agreed with the
owner 2026-10-26), condensed; the plan keeps its copy until the owner moves it.

**Reader question:** how did a cache built to make a human's resume free end up serving one game's failed
turn to another game, on another model?

**Added value:** readers will learn how five choices, each reasonable alone, composed into a cross-game
key: privacy-first wiring, cached re-runs, a value-based key, one process-wide cache, and an opening
payload with nothing game-specific in it. Also how a collision count, a recorded incident and a
before-and-after control bounded what is known.

**Why separate:** the chain, the 7-of-66 collision analysis, the two games side by side and the 5 → 0
control need sustained attention. The parent's argument is how the game pauses for a human.

**What stays on Level 2:** the bug in one paragraph (a payload with no game id, the incident, the fix,
deployed 2026-10-26, one recorded case, extent unknown) and the lesson: a cache key must name its scope.

**Rules:** say what the fix does and how it was verified; make no statement either way about served
games since the deploy. The second game's replay is attributed by the record, not directly captured:
say what the evidence is.

**Tags:** cache-key design, memoization, LangGraph.

Exhibits for this page are listed in [`../exhibits/source_map.md`](../exhibits/source_map.md) once its
rows (CK-…) are added.

---

<!-- Drafted 2026-10-26 from the sources listed at the end. Editorially drafted, not independently
verified; the questions for the verifier are in the drafting notes (NOTES_l3.md). -->

## Page copy (draft)

This page follows one bug. A cache I built so that a human player's pause would cost nothing ended up
handing one game's failed turn to another game, played on a different model. No single choice caused
it: five choices, each reasonable on its own, added up to a cache key that matched across games. I
found it while reading the code for a report, fixed it by putting the game's id into every cached turn,
and checked the fix with a before-and-after control.

First, the setting, which the [parent page](human_in_the_loop.md) explains in full. A person can take
one of the ten seats. When it is their turn, the game pauses, saves a checkpoint and waits. When they
answer, LangGraph, the framework that runs the game as a graph of steps, resumes the game, and because
of how I wired the graphs, it re-runs the whole paused step, including AI turns that had already
finished. So I cache each finished AI turn. The cache stores the turn's answer under a *key* computed
from the turn's input, its *payload*. When a re-run turn produces the same key, the cache returns the
stored answer and no model is called.

The key therefore decides what counts as "the same turn". This one said too little.

### Five choices, each reasonable alone

Each link solved a real problem, and each made the next one possible.

1. **The day and the wolves' night run as subgraphs called from inside a node.** Each is a smaller
   graph of its own, a *subgraph*. I call each from a node that builds its input by hand, because that
   hand-built input is where I control what each seat may see. The consequence: LangGraph treats the
   call as one step, so a resume re-runs the whole step.
2. **Finished AI turns are cached.** A cache hit returns the earlier answer, so a resume neither pays
   for the turn again nor lets an AI player change its vote. The consequence: a key now decides which
   turns are the same.
3. **The key is built from the payload's values.** LangGraph's default key never hit after a resume:
   a payload reloaded from the checkpoint looked different to it, even with every value equal. I
   changed the key to the payload's values written in a fixed order. The consequence: two payloads with
   equal values get the same key, wherever they come from.
4. **One cache serves every game in the process.** The subgraphs, and the cache with them, are built
   once and shared by every game the server hosts. LangGraph files a cached answer under the node and
   the key, not under the game's checkpoint. The consequence: equal payloads from two games meet in the
   same cache.
5. **The day-1 opening round adopted the same cached pattern.** Until then only votes were cached, and
   a vote's payload holds that game's discussion so far, which no other game shares. An opening is each
   player's first line on day 1, before anyone has spoken and before any night. Its payload holds the
   seat, its role, the lineup (the public list of roles in play) and the day: nothing particular to its
   game.

The payload had no game id. While only votes were cached, links 1 to 4 did no harm, because vote
payloads never matched across games. Link 5 made a match easy: two games with the same lineup and the
same role at the same seat now asked their model the same question.

Two more properties made a shared answer a damaging one. The model is not in the key either, so a game
on one model could be served another model's answer. And a failure is cached like any answer: when a
turn's model call and its retries fail, the turn falls back to a legal move, for an opening a pass, and
that pass is the turn's result, so the cache keeps it.

<!-- Diagram CK-chain goes here: the five-link chain (see NOTES_l3.md). -->

### Two games, one answer

The record holds one case. The first game's model calls all failed, so every seat's opening became a
pass. Nine minutes later, a second game on another model dealt the same lineup.

| | First game (`14926d10`) | Second game (`51226f24`) |
|---|---|---|
| Model | Claude Haiku 5.5 | GPT-6 Luna |
| When | 2026-10-17, 07:44 | nine minutes later |
| Day-1 openings | Every model call failed; every opening became a pass marked "generation failed" | A model call made for every AI seat's opening but one |
| The Serial Killer at seat 9, the one seat whose role matched | A "generation failed" pass | A "generation failed" pass, with no prompt captured |

<!-- Diagram CK-two-games goes here, or replaces the table (see NOTES_l3.md). -->

The replay in the second game was not observed directly. A cache hit skips the code that records a
model call, so it leaves no record of its own. Three records point to it. The game's prompt capture
holds a day-1 opening prompt for 8 of its 9 AI seats, and none for seat 9. Its event log holds seat 9's
pass, marked "generation failed". And its usage ledger counts 142 model calls and no failed ones, though
the ledger counts a failed call. So seat 9 failed without a failed call and without a prompt, at the one
seat whose role matched a game played minutes earlier on the same lineup, where that seat had failed.
The record attributes the pass to a replay from the shared cache. How those records were read together
is told in chapter 7.
<!-- Link spec: chapter 7 (serving and observability), the cross-game cache diagnosis from the records
(map block 163). Not yet drafted; no URL. -->

### How far it could reach

One case shows the bug happened. Two counts bound how often it could.

**Collisions are reachable with an ordinary deal.** In an offline check with no model calls, 12 games
were freshly dealt and every day-1 opening key computed. Of the 66 pairs of games, 7 shared at least one
key, 8 seats in all, each matching on seat, role and lineup. The unit is a pair of dealt
games, so this shows how easily two games could collide. It is not a rate of reuse in served games,
which also depends on which games ran in the same process within the cache's six-hour lifetime.

**One replay is recorded among served games.** Nineteen other pairs of served games could have matched,
and none shows a copy. Restarts empty the in-memory cache and could explain that, but I did not check
the restart times. Detection is limited too: only 11 of the 68 served games have prompt captures. For
the rest, a copied turn shows only when the private note it carries is distinctive. Batch runs also
play games one after another in one process, and no game in my recorded batch runs, or in the runs
whose prompts were captured, lost a day-1 opening call. How many served games crossed before the fix
is not known.

### The fix, and how it was checked

LangGraph sets this cache's scope: an entry is filed under the node and the key, and nothing else. A
cache bounded by the game's checkpoint would have been the natural boundary, but it is not on offer. So
the boundary had to go into the key. Every run already carries its game id in the run's configuration,
which LangGraph passes to each node; the key, though, reads only the payload. The nodes that call the
subgraphs now copy the game id from the configuration into the subgraph's input, so every cached
turn's payload carries it. A resume of the same game still finds its own turns. A matching turn from
another game no longer does.

The cost I accepted: every cached payload must carry the id, so any new cached turn must carry it too.
And the model is still outside the key, so the cache assumes that nothing outside the payload, such as
a switch of model, changes a turn's answer during one game.

The regression tests check both sides of the key. A payload saved and reloaded through the real
checkpoint serializer keeps its key. The nodes that call the day and the wolves' night put the game id
on their payloads. And the 12 freshly dealt games of the offline check, now with their ids, share no
opening key; that test fails without the fix.

The control tests the fix where the bug lived: two games back to back in one process, sharing one
cache. It used two deals chosen so that six seats had the same roles, and the test suite's scripted
model, a stand-in that fills in whatever answer it is asked for without calling a model.

| Code | Second game's openings served from the first game's cache |
|---|---|
| Before the fix | 5 |
| After the fix | 0 |

Two games on the same deals with Claude Haiku 5.5, on the fixed code, each made all ten day-1 opening
calls, so with a real model too, the second game's openings were its own. Before the deploy, a check
inside the production image found that two freshly dealt games share no opening key. I deployed the fix
on 2026-10-26.

### The lesson

A cache key must name its scope: the game, and anything else that changes the answer, not only the
turn's input. The earlier fix made the key stable across a checkpoint, and by the same move made it
equal across games. A fix that makes a key stable can widen it. The bug became reachable only when a
working pattern was reused on a new kind of turn, so reusing a cached pattern means checking again what
its key captures. And a cache replays a fallback as faithfully as a real answer.

**Evidence.**

- [Orchestration: how a game runs as a graph](../../../evidence/gameplay/orchestration/report.md),
  decision 12 ("The cross-game cache bug") and "What is not established".
- [Server: encountered challenges](../../../frontend/docs/server_encountered_challenges.md), §3–5 (the
  re-run, the cache and its uncached twin, the key that never hit).
- [Observability: what a game leaves behind](../../../evidence/tracing/report.md), "The cross-game node cache" (the three
  records).
- [Deploy log](../../../frontend/docs/deploy_log.md), 2026-10-26 (the fix's deploy and pre-flight).

<!-- Sources for the page copy (drafted 2026-10-26):
Opening: content plan "Level 3 candidates", Selected (reader question, added value); "found it while
reading the code for a report": interview_prep/langgraph_langfuse_issues.md §7.3 "If asked" ("Reading the
code for a report; confirmed offline by dealing 12 games").
Setting: human_in_the_loop.md (page 5) "Reusing the AI players' decisions"; server_encountered_challenges
§3 (black box, re-run the whole node), §4 (cache, twin, six hours).
Chain: map block 115; interview_prep §7.3 "How it traces back to the design" (links 1–5, "a key with the
game in it, or a cache scoped to the thread, would have made links 1, 2, 4 and 5 harmless");
orchestration report decision 12 "Failure mechanism" (key from values, no game id; scoped by node and key,
not by checkpoint thread; compiled subgraphs serve every game in the process; across models); link 3:
server_encountered_challenges §5 (pickle, fields set, canonical JSON); link 5: decision 12 ("a day-1
opening can contain no information unique to its game"; adopted 2026-10-07, b66ce7b4); interview_prep
§7.3 (same seat, role and lineup, nothing said yet; batch runs one after another in one process; the
model not in the key). Day 1 before any night: source_map L1-loop / discussion report "A day today".
Fallback cached: decision 12 "Recorded incident" ("a fallback result had been cached just like a
successful answer"); content plan page 4 subsection 5 (retries, then a legal fallback; a pass for
discussion).
Two games: decision 12 "Recorded incident" (14926d10, 2026-10-17 07:44, Haiku 5.5, every call failed,
generation_failed passes; 51226f24 nine minutes later, GPT-6 Luna, same lineup, every opening call except
one, player_9 Serial Killer the one seat whose role matched, no captured prompt; "the record identifies
this as replay"); deploy_log 2026-10-26 (same lineup, same role at an AI seat). "Same server process":
inferred from the mechanism (a hit needs one process) — verifier item.
Three records: evidence/tracing/report.md "The cross-game node cache" (8 of 9 AI seats captured, none for
player_9; pass_marker event; ledger 142 calls, none failed, a real failed call is counted; a hit skips
the instrumented turn body; no explicit cache-hit record); map block 163. Chapter 7 owns the diagnosis
(content plan "Deferred": block 163).
Reach: decision 12 (7 of 66 pairs among 12 freshly dealt games, 8 seats; "reachable key collisions, not
how often served games reused an answer"); "Extent and remaining uncertainty" (19 other pairs, restarts
possible, restart times not checked; 11 of 68 captures; no recorded batch or capture game lost a day-1
call); "What is not established" bullet 3 (copied pass visible only when its private note is
distinctive). Six-hour lifetime: TURN_CACHE_TTL_SECONDS.
Fix: decision 12 "Fix" (wrappers copy the game id from the run config into subgraph state); interview_prep
§2.3 (run-scoped values ride config; anything keyed on the payload alone does not see them) and §7.3
(LangGraph keys a Send task's cache by node and key, checked in installed 1.1.10 source); turn_cache_key
docstring. Cost: interview_prep §7.4; orchestration "When to revisit the design" row 3.
Tests: tests/engine/test_turn_cache_key.py (round-trip through JsonPlusSerializer with the allowlist;
wrappers carry the game id on day and pack payloads and _pack_payload; 12 games share no opening key);
decision 12 ("the isolation test fails without the game id").
Control: "What is not established" bullet 5 (two Haiku games back to back in one process, 2026-10-26,
deals chosen to share six seats' roles, each made all ten opening calls; the same deals with the scripted
model on pre-fix code served five of the second game's openings from the first game's cache; fixed code
none); gameplay hub report "Execution reliability". Scripted model: orchestration "How it was checked"
row 1 ("fills whatever schema it gets").
Pre-flight and deploy: deploy_log 2026-10-26 (2ecec0cc; pre-flight in the new image with production
settings: two freshly dealt games share no opening key). No statement about served games since (rule).
Lesson: map block 115; interview_prep §7.3 "The lesson" and "If asked" (re-check what a key captures
whenever a cached pattern is reused; a cached fallback is replayed like a real answer). -->
