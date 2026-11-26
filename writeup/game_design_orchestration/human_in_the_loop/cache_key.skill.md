# The cache key that crossed games

*How a cache meant for one game's repeated turns gave a turn to a different game, and what the fix
and its checks establish.*

*Level 3 · beneath [Adding a human in the loop](human_in_the_loop.md) · status: trial draft written with the write-portfolio-page skill, 2026-10-28; revised after the editorial and claims reviews; brief: [`_authoring/cache_key.skill.brief.md`](_authoring/cache_key.skill.brief.md).*

## Page copy (draft)

The game in this project is a Mafia-style game played by AI agents: ten seats, each dealt a hidden
role, and a person may take one of them. When that person pauses to think, the engine keeps the AI
players' finished turns in a cache, so that resuming does not make them answer again. Once the
day's opening round was added to that cache, and until the fix, the cache could also give a turn
from one game to another. Its key, which decides which stored answer belongs to a turn,
described the turn but not the game it came from.

Each day starts with an opening round, in which every living player speaks or passes. On the first
day nobody has spoken yet, so a seat's opening input depends only on the deal. The records point to
one case. In one game every model call failed, so each AI seat's opening became a fallback pass.
Nine minutes later, a game on a different model, dealt the same set of roles, made its own opening
call at every AI seat but one; the records indicate that this seat received the earlier game's
failed pass from the cache. The fix adds the game's id to every cached turn. Tests and a
before-and-after check show that the key now separates games. How many games hosted on the
project's web server were affected before the fix is unknown.

### What the cache is for

The cache exists because resuming after a human's pause re-runs AI turns that had already finished.
The game runs on LangGraph, a framework that executes it as connected steps called nodes. The day
and the wolves' night are each a smaller graph of their own, a subgraph, which a wrapper node calls
after building its input by hand. That hand-built input is where I control what each seat may know.
Its cost appears when a human pauses inside one of these phases: resuming re-runs the wrapper, and
with it the whole interrupted round, including AI turns that had already returned. [Adding a human
in the loop](human_in_the_loop.md) explains how that was found.

So I cache the AI turns in those rounds. When a turn runs again with the same input, LangGraph's
node cache returns the stored result instead of calling the model. Human turns go through an
uncached copy of the same node, because their answer must come from the person.

The cache finds a stored result by its key, computed from the turn. The key therefore decides what
counts as "the same turn", and it has two jobs. It must match a repeat of a turn within one game,
and it must match nothing else the cache holds.

### Five choices that gave two games one key

Each of five choices was reasonable for its own purpose. Together they let equal turns from
different games share one stored answer.

1. **Phases called from a wrapper,** to keep the information boundary in one place. So a resume
   re-runs the interrupted round.
2. **AI turns cached,** so the re-run reuses their answers instead of calling the model again. So a
   key now decides which turns are the same.
3. **A key built from the input's values.** LangGraph's default key changed when an input was
   reloaded from the saved game state, so it missed exactly when a repeat needed it; a key built from
   the values stays the same. So the key sees only what the input contains. The game's id lived in
   the run's settings, which the key never read, and the model was not in the input either.
4. **One cache for every game.** LangGraph keys a node's cache by the node and the key alone, not by
   game. The phases and their in-memory cache are shared by every game the process runs. So the key
   alone had to keep games apart.
5. **The day-1 opening round given the same cached pattern.** Until then only votes were cached, and
   a vote's input carries that game's discussion, which makes equal votes in two games unlikely. An
   opening on day 1 comes before any night and before anyone has spoken. Its input holds the seat,
   its role, the set of roles in play and the list of seats; a wolf's also names its pack partners.
   So two games dealt the same set of roles, with the same role at a seat, can give that seat
   identical inputs.

The root cause is the key's missing scope: it never named the game, although the cache spanned
every game. The other choices are why that gap mattered. With the game in the key, the other four
would have been harmless.

### How easily two openings matched

Matching openings turned out to be easy to produce. The bug was found while reading the code for a
report, not from an alert, and the first check was offline: deal 12 fresh games without calling a
model, and compare their opening keys. Of the 66 possible pairs of games, 7 had at least one seat
with an identical key, 8 seats in all.

That count shows how easily the deal produces matching openings; it is not a rate of affected
games. The web server runs all its games in one process, so a hosted game could receive another's
turn whenever both fell within the cache's six-hour lifetime with no restart between them. The next
question was whether that had happened in the games the server had hosted.

### The game that received another game's failure

One hosted game's records point to a collision, and what it copied was a failure. A turn whose
model call fails does not stop the game. After its retries, it returns a legal fallback: for an
opening, a pass marked as a failed generation. To the cache, a fallback is an
ordinary result, stored like any answer.

| | Earlier game | Later game, nine minutes after |
|---|---|---|
| Model | one model | a different model |
| Day-1 opening calls | every call failed; each AI seat's opening became a fallback pass | a call made at every AI seat except one |
| The seat dealt the same role in both | a fallback pass | a failed-generation pass, with no prompt recorded |

*Both games were dealt the same set of roles; only one seat, the Serial Killer's, held the same role
in both.*

A cache hit leaves no record of its own, because it skips the part of the turn that is logged. The
attribution therefore rests on three records that agree. The later game's prompt capture, a
per-game copy of every prompt sent, held opening prompts for 8 of its 9 AI seats and none for that
seat. Its event log held the failed-generation pass. Its usage ledger, which counts every model call
including failed ones, recorded 142 calls over the whole game and no failures. A pass from a real
failure would have appeared there as a failed call; this one came with no call at all.

The incident analysis attributes this to a replay of the earlier game's failed turn. It is an
inference from records consistent with the mechanism, not an observed cache hit, and one of the
mechanism's conditions was not checked for this pair: that the server did not restart in the nine
minutes between the games. The visible effect was small: that seat's day-1 opening was a pass.

### Adding the game to the key

The fix puts the game into the input. The game's id was already in the run's settings; each wrapper
now copies it into its phase's state, so every cached turn's input carries it. A repeated turn within
one game still produces the same key; equal turns in two games no longer do. Separating games does
not need the model in the key. Within one game, the cache assumes the model does not change between
a turn and its repeat; the next section returns to that assumption.

The tests check the key in four ways. An input saved and reloaded through the game-state serializer
keeps its key. Different turns, and the same turn in two games, get different keys. The day and
wolves'-night wrappers put the game's id on the inputs they build. And the 12-game deal is repeated
as a test: no two games may share an opening key, a test that fails without the fix.

A before-and-after check tested the behaviour itself. Two deals chosen to share six seats' roles
were played back to back in one process, every seat played by the scripted model, a test stand-in
that fills in any answer without calling a model. On the code before the fix, five of the second
game's openings were served from the first game's cache. The record does not say why the sixth
shared role produced no reuse; a shared role does not always mean a shared input, since a wolf's
input also names its pack partners. On the fixed code, no opening was reused. The same two deals,
played with a real model on the fixed code, made all ten opening calls in each game.

Before the deployed build went live, a check in the production image confirmed that it puts the
game's id on every cached input. Together, these checks cover how the key is built and the day-1
openings of two deals.

### What remains unknown

The fix closes the gap; it does not show how far the gap reached before. One case is identified
among the hosted games. No copy was found in 19 other pairs of hosted games that could have matched,
but the server may have restarted between them, clearing the cache, and restart times were not
checked. Detection is limited too: only 11 of the 68 hosted games have prompt captures, and without
one, a copied turn shows only when its content gives it away. The experiments' batch games were
exposed in the same way, since a batch plays its games one after another in a single process with
one cache. Every recorded batch game, and every offline run that captured prompts, made all of its
own day-1 calls.

The cache still assumes that, within one game, nothing outside a turn's input changes its answer.
The model is one such thing: it is not in the key.

### What a cache key must name

The key named the turn, but the cache it served was shared by every game, so the key had to name
the game too. A cache key must name the cache's scope. And a cache stores whatever a step returns:
a fallback is replayed as faithfully as a real answer.

**Evidence.**

- [Orchestration: how a game runs as a graph](../../../evidence/gameplay/orchestration/report.md),
  decision 12 ("The cross-game cache bug") and "What is not established".
- [Tracing report](../../../evidence/tracing/report.md), "The cross-game node cache" (the three
  records).
- [Server: encountered challenges](../../../frontend/docs/server_encountered_challenges.md), §3–5
  (why AI turns are cached, the uncached copy, the value-based key).

<!-- Sources for the page copy (trial draft, 2026-10-28; write-portfolio-page skill):
Opening: orchestration report decision 12 "Failure mechanism" and "Recorded incident". The window is
tied to its events ("once the opening round was added to that cache, and until the fix") rather than a
length: openings cached in commit 2026-10-07 (b66ce7b4), fix 2026-10-26 (fd07c0f8), 19 days; which
server build first carried b66ce7b4 is unconfirmed (deploy log suggests 2026-10-11, about two weeks
for hosted games) — flagged to the owner, brief open question 2. Game in one sentence: chapter page
(Mafia-style, ten seats, hidden roles, a person may take a seat); day flow: map block 117 (each day
starts with the opening round). The two games: 14926d10 (2026-10-17 07:44, Claude Haiku 5.5) and
51226f24 (GPT-6 Luna); "same set of roles" = the record's "same lineup"; "each AI seat's opening"
because whether 14926d10 had a human seat is not recorded. "The records indicate" (claims review #3).
"The key now separates games" (claims review #2: the checks show the key, not every cached turn).
Unknown extent: "What is not established" bullet 3.
What the cache is for: parent human_in_the_loop.md "Why resuming changed the AI votes", "Reuse
completed AI decisions"; server_encountered_challenges §3 (black box, re-run the node, the privacy
boundary), §4 (cache, uncached twin); orchestration "Human seats" (cached nodes: round_turn, vote,
CARRIER_KILL, PACK_SKILL). Wolves' night = the pack's subgraph.
Five choices: map block 115; interview_prep/langgraph_langfuse_issues.md §7.3 "How it traces back to
the design" (links 1–5; "A key with the game in it, or a cache scoped to the thread, would have made
links 1, 2, 4 and 5 harmless"); decision 12 "Failure mechanism" (key from values, no game id; scoped
by node and key, not checkpoint thread; compiled subgraphs and cache serve every game in the process;
across models). Link 3: server_encountered_challenges §5 (pickle; values). Game id in config, not
state: interview §2.3; Agents/config/langgraph.py::game_id_from_runnable. Model not in key: interview
§7.3, §7.4. LangGraph cache key: CacheKey((CACHE_NS_WRITES, identifier, node), xxh3(key)), checked in
installed 1.1.10 source (interview §7.3). Link 5: decision 12 ("Vote payloads include the game's
transcript"; "a day-1 opening can contain no information unique to its game"); day 1 precedes the
first night: orchestration "The parent graph". Opening input fields: Agents/nodes/day/flow.py
fan_out_day base_payload (seat, role, lineup, cast_role_counts, surviving_players, empty channel) and
_private_fields (a wolf's pack roster: surviving_wolves, pack_roles). The rules (game_config) reach a
node through the run config, not the input, so "the rules" is not listed (claims review #7). The
"widened key" lesson is
deliberately omitted (owner ruling 2026-10-28; decision 12 does not make it).
How easily: "found while reading the code for a report": interview §7.3 "If asked" (neutral wording,
owner ruling); 7 of 66 pairs among 12 freshly dealt games, 8 seats, "reachable key collisions, not
how often served games reused an answer": decision 12; offline, no model calls: interview §7.3.
Six-hour lifetime: TURN_CACHE_TTL_SECONDS = 6 * 3600. One process: interview §7.3 (the server hosts
all games in one process).
Received failure: fallback after retries (a pass for discussion): agent_turn page / content plan
page 4 subsection 5; "a fallback result had been cached just like a successful answer": decision 12.
Table: decision 12 "Recorded incident" (every call failed, generation_failed passes; nine minutes
later, same lineup, every opening call except one; player_9 Serial Killer, the one seat whose role
matched; no captured prompt). Three records: evidence/tracing/report.md "The cross-game node cache"
(8 of 9 AI seats captured, none for player_9; generation_failed pass event; ledger 142 calls, none
failed, a real failed call is counted; a hit skips the instrumented turn body; no explicit cache-hit
record). "The record identifies this as replay": decision 12 (the page says "the incident
analysis"). Same process: the server hosts all games in one process (interview §7.3); no restart in
the nine minutes is a condition not checked for this pair (stated on the page; brief open question 6).
"142 calls over the whole game": tracing report ("recorded 142 calls for the game").
Fix: decision 12 "Fix" (wrappers copy the game id from the run config into subgraph state; every
cached turn's payload carries it; preserves reuse within a game); flow.py base_payload comment.
Model not needed to separate games; within-game model assumption: interview §7.4 and "When to revisit"
row 3, worded without saying whether it is ever broken (brief open question 1).
Tests: tests/engine/test_turn_cache_key.py, five tests in four groups
(test_key_survives_a_checkpoint_round_trip through JsonPlusSerializer with the allowlist;
test_key_separates_different_turns and test_key_separates_games;
test_the_subgraph_wrappers_and_payload_builders_carry_the_game_id on day and pack inputs and
_pack_payload — the day and wolves'-night wrappers only; solo nights are not cached;
test_two_games_never_share_a_day_one_opening_key); "the
isolation test fails without the game id": decision 12. Control: "What is not established" bullet 5
(scripted model, pre-fix code, five of the second game's openings from the first game's cache; fixed
code none; two Claude Haiku 5.5 games back to back in one process on the same deals, each made all ten
day-1 opening calls, 2026-10-26); gameplay hub report "Execution reliability". Scripted model:
orchestration "How it was checked" row 1 ("fills whatever schema it gets"). Six versus five: no
recorded explanation; the wolf clause is from _private_fields, offered as a possibility only (owner
ruling 3; brief open question 3), now introduced as "the record does not say why" (claims review #4).
"Every seat played by the scripted model": the control's games made "all ten" opening calls.
Pre-flight: deploy_log.md 2026-10-26 (server image 2ecec0cc; in the new image with production
settings, "the wrappers put the game id on every cached payload, and two freshly dealt games share
no opening key"). The page keeps only the first half: two unmatched fresh deals would share no key on
the old code too in most pairs (editorial review #4). No statement about served games since the
deploy (owner rule 2026-10-26).
Remains unknown: decision 12 "Extent and remaining uncertainty" (one replay identified; 19 other
potentially matching served pairs show no copy; restarts possible, restart times not checked; 11 of
68 served games captured; no recorded batch or capture game lost a day-1 call — "capture" there means
the offline capture runs, a separate kind of run from served games: tracing report "Batch and capture
runs"; batch games share one process and one cache: interview §7.3 "batch runs games one after
another"); "What is not
established" bullet 3 (a copied pass is visible only when its private note is distinctive). The
criterion for "potentially matching" is not defined in the record (owner ruling 4). Residual
assumption: interview §7.4; orchestration "When to revisit the design" row 3 (a mid-game model
switch).
Lesson (own closing section, editorial review #12): map block 115 ("a cache key must name its
scope"); interview §7.3 "The lesson" (first and last sentences only: a cached fallback is replayed
like a real answer). The "re-check whenever a cached pattern is reused" clause was dropped to keep
the owner's one lesson. -->

