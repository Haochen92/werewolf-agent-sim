# Authoring brief: The cache key that crossed games

Page: `writeup/game_design_orchestration/human_in_the_loop/cache_key.skill.md` · Level 3 · started 2026-10-28 · checkpoint: approved in conversation

Authoring material, not page copy. The cold editorial reviewer never sees this file.

Trial run of the `write-portfolio-page` skill (steps 1–3), written without reading the baseline
`cache_key.md`. Inputs read: the three `writeup/portfolio-*` guides, the skill's references, the
chapter's `content_plan.md` (page 5 brief, Level 3 "Selected", boundaries), `editorial_notes.md`,
`map.md` blocks 105–106, 110, 114–116, 163, 165 and "Handle with care", the parent
`human_in_the_loop.md`, the copied original brief and sources comment, and the sources it cites:
orchestration report ("Human seats", decision 12, "How it was checked", "What is not established",
"When to revisit the design"), `server_encountered_challenges.md` §3–5, `tracing/report.md` "The
cross-game node cache", `deploy_log.md` 2026-10-26, the gameplay hub "Execution reliability",
`interview_prep/langgraph_langfuse_issues.md` §2.1, §2.3, §6.2, §7.1–7.4, `Agents/config/langgraph.py`
(`turn_cache_key`, `game_id_from_runnable`, `TURN_CACHE_TTL_SECONDS`), `Agents/nodes/day/flow.py`
(`fan_out_day` payload), `tests/engine/test_turn_cache_key.py`.

## Frame

- **Primary page type and level:** incident and reliability case study, Level 3 (failure mechanism →
  observed impact → fix → verification → remaining exposure).
- **Secondary mode, if needed:** section 2 borrows *design decision* mode (each of the five choices
  is given its own reason, so the chain reads as reasonable choices, not carelessness). Section 4
  borrows *diagnostic investigation* mode for one job only: how a replay was attributed when no
  record of a cache hit exists.
- **Existing outline approval:** approved in conversation, 2026-10-28 (Frame and Argument outline
  approved as proposed, with four rulings on the open questions; see "Owner rulings" below).
- **Reader's question:** How did a cache built to keep a human's pause from re-running the AI players
  end up giving one game's failed turn to another game, played on a different model?
- **Central answer:** The cache's key described a turn by its input alone, while one cache served every
  game in the server process; that was harmless while only votes were cached, because a vote's input
  carries its own game's discussion, but once the day-1 opening round was cached, two games with the
  same lineup could produce identical inputs at a seat, and one recorded game received another
  game's failed opening. Adding the game's id to every cached input separates games; tests and a
  before-and-after control check that, and how many served games were affected before the fix is
  unknown.
- **Distinctions the reader needs:**
  1. *A repeat of the same turn within one game* (reuse wanted: that is the cache's job) vs *an equal
     turn in another game* (reuse wrong). The key has to do both: match the first, refuse the second.
  2. *What the key sees* (the turn's input, built per seat) vs *where the game's id and the model
     live* (the run's configuration, which the key never read).
  3. Three kinds of evidence, never merged: *reachable* (an offline count of matching keys among
     freshly dealt games), *observed* (one served game, the replay attributed from three records, not
     a recorded cache hit), *fixed* (key tests and a scripted before-and-after control). None of them
     measures how often served games were affected.
- **What the evidence establishes:** the mechanism (cache scoped by node and key; key from input values
  with no game id; one cache per process; day-1 opening inputs can be identical across games); that
  collisions were reachable (7 of 66 game pairs among 12 fresh deals, 8 seats); one served case whose
  records are consistent with replay and with no other explanation offered; that the fix separates
  the keys (tests, including one that fails without the id) and stops cross-game reuse in a scripted
  control (5 reused openings before, 0 after) while real-model games still make every opening call.
- **What stays uncertain:** how many served games were affected (19 other candidate pairs show no copy;
  restarts may have cleared the cache, restart times not checked; 11 of 68 served games have prompt
  captures; elsewhere a copied turn is visible only when its content gives it away). The served
  replay is inferred, not directly recorded. The cache still assumes nothing outside the input (such
  as the model) changes an answer within one game.
- **Stays off the page:** who wrote or audited the tests (never mentioned either way); deploy
  bookkeeping (unpushed build, detached worktree, other undeployed commits); any statement about
  served games since the deploy, either way (owner rule, 2026-10-26); commit hashes and image ids
  (source notes only); the uncommitted-diff provenance of the interview note. Also kept off as
  belonging elsewhere: the capture/event/ledger side-by-side exhibit (chapter 7, block 163), the
  provider prompt cache (chapter 6), the checkpoint-thread reuse safeguard in `run_batch`.

## Evidence selection

| Material (source) | Role | What it helps the reader understand or assess |
|---|---|---|
| Why AI turns are cached at all: resuming re-runs the paused round because each phase is called from a wrapper that builds its input (the information boundary); a node cache returns the stored result; humans go through an uncached copy (parent; `server_encountered_challenges` §3–4; decision 12) | essential (short recap) | A direct arrival needs the cache's purpose before its key can be judged; sets up "the key decides what counts as the same turn" |
| Failure mechanism: key = canonical JSON of the input's values; LangGraph keys the cache by node and key only, not by game or checkpoint thread; compiled phases and their in-memory cache serve every game in the process; no game id in the input; the model not in the key (decision 12; interview §7.3; `turn_cache_key` docstring) | essential | The core of "how": why equal inputs from two games met one stored answer |
| The five-link chain, each with its reason and its consequence (map 115; interview §7.3; source map CK-chain) | essential | The page's added value: reasonable choices composing into a cross-game key; the root is the key's missing scope, the design choices contribute |
| Vote input vs day-1 opening input: a vote's input carries the game's discussion; a day-1 opening comes before any night and before anyone speaks, so it holds seat, role, lineup and rules (decision 12; `flow.py::fan_out_day`; parent graph: day 1 precedes the first night) | essential | Why the gap stayed harmless until openings were cached, and then became reachable |
| A fallback pass is an ordinary result, so it was cached like an answer (decision 12; agent-turn page's retry → legal fallback) | essential | Why the thing copied was a *failure* |
| Recorded case: game A on one model, every call failed, openings became fallback passes; game B nine minutes later on another model, same lineup, every opening call made except at the one seat whose role matched, which returned the failure pass (decision 12; deploy log) | essential | The observed consequence; the two-games table (CK-two-games) |
| Attribution without a cache-hit record: a hit skips the instrumented turn body; capture held openings for 8 of 9 AI seats, none for that seat; the event log held the failure pass; the usage ledger counted 142 calls, none failed, where a real failure is counted (tracing report) | essential | Lets the reader assess "attributed, not directly recorded" |
| The fix: wrappers copy the game id from the run configuration into each phase's state, so every cached input carries it; reuse within a game is preserved (decision 12; `game_id_from_runnable`) | essential | What changed and why it keeps the cache's original job |
| Before-and-after control: two deals sharing six seats' roles, back to back in one process; scripted model, pre-fix code: 5 of the second game's openings served from the first game's cache; fixed code: 0; the same deals on a real model with the fix: all ten opening calls in each game (orchestration "What is not established" b5; gameplay hub) | essential | The strongest verification; needs its setup before its numbers |
| Extent: one case identified; 19 other candidate pairs show no copy; restarts possible, times not checked; 11 of 68 served games captured; a copied turn visible only when distinctive; no batch or capture game lost a day-1 call (decision 12 "Extent"; "What is not established" b3) | essential | The limit that sits beside "fixed" |
| Offline collision count: 7 of 66 pairs among 12 freshly dealt games, 8 seats (decision 12; test docstring) | supporting | Shows the collision was easy to reach, with its unit and what it does not measure |
| Regression tests: key stable through the checkpoint serializer; wrappers put the id on day and pack inputs; 12 dealt games share no opening key, failing without the id (`test_turn_cache_key.py`) | supporting | What the code-level checks cover |
| Pre-flight in the production image: two freshly dealt games share no opening key (deploy log) | supporting | Deployed build checked before going live; one clause |
| Residual assumption: nothing outside the input changes an answer within a game; a mid-game model switch would break it (interview §7.4; "When to revisit") | supporting | Remaining exposure of the same kind |
| Found by reading the code for a report, confirmed offline by dealing 12 games, then one case found in served games (interview §7.3 "If asked") | supporting | Explains why the case was found after the fact and why no alert existed; one sentence |
| Lesson: a key must name the cache's scope; re-check what a key captures whenever a cached pattern is reused on a new kind of turn; a cached fallback replays like an answer (map 115; interview §7.3) | supporting | The transferable point, stated once at the end |
| Pickle key and pydantic fields-set detail; the 20-ballot verification game | optional → parent | Answers "why a value key", the parent's question |
| LangGraph `CacheKey((CACHE_NS_WRITES, identifier, node), xxh3(key))` | optional → source note | Supports "keyed by node and key only"; not needed in prose |
| Dates, commit hashes, server image ids, model names beyond the two-games table | optional → source notes | Dates change no interpretation except "nine minutes" (within one process and the six-hour lifetime) |

Left out, and where it lives instead:
- The capture / event / ledger records shown side by side: chapter 7's exhibit (block 163); this page
  names the three records in prose.
- `run_batch` refusing paired game ids across configs (a checkpoint-thread collision, not a cache
  hit): orchestration report decision 12, "Related checkpoint safeguard".
- The uncached twin's crash on resume, the toy graph, the six-hour lifetime vs checkpoint table: the
  parent page.
- The 2026-08-24 empty-trace story: chapter 7.

## Argument outline

Structure: **mechanism first, then the case, then the fix and its limits.** The page opens with the
recorded case in one sentence (the concrete hook and the central answer), but explains the mechanism
before presenting the case's evidence, because that evidence (a missing prompt, a failure pass, a
ledger with no failures) only reads as a cache hit once the reader knows that a hit leaves no record
and that a fallback is cached like an answer. This is not the discovery order (code reading →
offline count → search of served games); the page states that order in one sentence rather than
following it. The chain is the centrepiece because it is the page's added value over the parent; it
is a numbered list (frame, then parts: "five choices, each reasonable alone") with the reason and the
consequence of each link, so the reader sees the composition rather than five separate facts.
Target length about 1,300–1,500 words.

| # | Section (working heading) | Question it answers | Main point | Carried by (example / finding) | Why the next section follows |
|---|---|---|---|---|---|
| 0 | *(opening, no heading)* | What happened, and why does it matter? | The engine stores AI players' finished turns so a human's pause doesn't make them answer again. For nearly three weeks that store could hand one game's turn to another: its key described the turn, not the game. One recorded game received another game's failed opening, made on a different model. Adding the game's id fixed it; tests and a before-and-after control check the fix; how many games were affected before it is unknown. | The case in one sentence; the central answer | To see how a game-level store crossed games, the reader first needs what it stores and what its key must do |
| 1 | What the cache is for | Why cache AI turns, and what must the key do? | When a human pauses inside a phase, resuming re-runs that round's AI turns, because each phase is called from a wrapper that builds its input (where I control what each seat may see). A node cache returns the stored result when a turn repeats; humans are never cached. So the key decides what counts as "the same turn": it must match a repeat within one game and match nothing else the cache holds. | Brief recap from the parent; the key's two jobs (distinction 1) | Whether the key did its second job depends on what it was built from and what the cache was shared by |
| 2 | Five choices, one key for two games | How did a key meant for one game's repeats match turns from different games? | Five choices, each sound for its own reason, composed: (1) phases called from a wrapper, so a resume re-runs the round; (2) AI turns cached, so a key now defines sameness; (3) the key built from the input's values, so it survives a checkpoint reload, and sees only what the input holds; the game's id and the model live in the run's configuration; (4) LangGraph keys the cache by node and key only, and one compiled phase and one cache serve every game in the process, so the key alone must separate games; (5) the day-1 opening round given the same cached pattern: unlike a vote, whose input carries its game's discussion, an opening before any night and any speech holds only seat, role, lineup and rules. The root is the key's missing scope; the other choices made it matter. | Numbered chain (CK-chain); the vote-vs-opening contrast | Link 5 is the one that made it reachable: how easily? |
| 3 | How easily two openings matched | Was a collision a rare edge case? | Easy to reach: in an offline check of 12 freshly dealt games, 7 of the 66 pairs had at least one seat with an identical opening key (8 seats). That counts possible matches among deals; a served replay also needs both games in one server process within the cache's six-hour lifetime, so it is not a rate of affected games. Found this way: reading the code, confirmed by this count, then the served games were searched. | CK-collisions; unit stated (game pairs, seats) | A possible match is not an observed one: what did the served games show? |
| 4 | The game that received another game's failure | What happened in served games, and how is it known without a record of the hit? | Game A: every model call failed, each opening became the fallback pass (a legal "say nothing" a turn returns when the model fails), and that pass was cached like an answer. Game B, nine minutes later on another model with the same lineup, made every opening call except at the one seat whose role matched; that seat returned the failure pass. A cache hit skips the instrumented turn, so it leaves no record of its own; three records agree instead: no captured prompt for that seat (8 of 9 AI seats captured), the failure pass in the event log, and a usage ledger of 142 calls with none failed, where a real failure is counted. The replay is attributed from records consistent with the mechanism, not directly observed. | CK-two-games table; the three records in prose (CK-three-records) | The mechanism and the case point to one change: give the key the game |
| 5 | Adding the game to the key | What changed, and how was it checked? | The wrappers copy the game's id from the run configuration into each phase's state, so every cached input carries it: a repeat within a game still matches, equal turns in two games no longer do. Checks: the key stays stable through checkpoint reload; the wrappers put the id on day and night inputs; 12 dealt games share no opening key (the test fails without the id). Control: two deals chosen to share six seats' roles, played back to back in one process; with the scripted model (a test stand-in that fills any answer without a model call), pre-fix code served 5 of the second game's openings from the first game's cache, fixed code 0; the same deals on a real model with the fix made all ten opening calls in each game. Deployed after the same key check passed in the production image. | Tests; CK-control (two-row table + sentence); pre-flight in one clause. No statement about served games since. | The fix closes the gap; it does not say how far the gap reached, or what else the key leaves out |
| 6 | What is still unknown, and what the cache still assumes | How many games were affected, and what remains exposed? | One case identified. 19 other candidate pairs show no copy; restarts may have cleared the cache, but restart times were not checked; 11 of 68 served games have prompt captures, and elsewhere a copied turn shows only when its content gives it away. Every batch and capture game made all its own day-1 calls. The key still assumes nothing outside the input changes an answer within one game: the model is not in it, so a mid-game model switch would break that. Lesson, once: a cache key must name the cache's scope, and needs re-checking whenever a cached pattern is reused on a new kind of turn; a cached fallback replays like a real answer. | "Extent" bullets; "When to revisit" row; map 115 lesson | — |

**Outline check (main points read in order):** purpose → how five choices produced a shared key →
reachable → observed → fixed and checked → unknown reach and residual assumption. That answers the
frame's question (how) and bounds what is known. Term order: "fallback pass" is defined in section 4
where first needed; "lineup" and "opening round" in section 2; "scripted model" in section 5;
"capture" and "usage ledger" in section 4. Section 3 uses "key collision" from section 2. No section
needs a later section's result.

## Owner rulings (checkpoint, 2026-10-28)

Frame and Argument outline approved. Rulings on the open questions:

1. **Who found it:** neutral wording ("the bug was found while reading the code for a report"). No
   first-person claim of finding it.
2. **The August key change:** drop the "a fix that makes a key stable can widen it" lesson. Decision
   12 does not make that claim (only the interview notes do), and under the pickle-based default two
   freshly built identical openings would likely have matched too. Link 3 stays neutral: the key is
   built from the input's values, so it sees only the input. One lesson: a cache key must name the
   cache's scope, plus a cached fallback is replayed like a real answer.
3. **Six shared roles, five reused openings:** no recorded explanation. Check the opening-turn
   payload code once; if a seat's opening input can differ between deals with the same role, give
   that as one plain clause, otherwise state the five without comment. **Checked:**
   `Agents/nodes/day/flow.py::_private_fields` gives a wolf's day input the pack's roster
   (`surviving_wolves`, `pack_roles`) and the surviving villagers, so a wolf seat's opening input
   differs between deals even when its role matches. Given as one clause that does not claim it is
   the cause of the specific gap (the record does not say which seats differed). The question stays
   open below.
4. **The 19 candidate pairs:** the report calls them "potentially matching" and does not define the
   criterion. Say no copy was found in them, restart times were not checked, and only 11 of 68 served
   games have prompt captures. No invented definition.

## Open questions

**For the owner (flagged from the claims review, not decided):**

1. **The stall rescue and the model assumption** (claims #5). The interview notes (§7.4, §10.1) say
   the deployed stall rescue already moves a game to a rescue model after two stalls in a row, and that
   this switch is outside the cache key. If so, the within-game assumption is already crossed in live
   games, and whether a replayed answer from the original model ever matters is not recorded. Page
   wording for now ("What remains unknown" and the fix section): the cache *assumes* the model does not
   change between a turn and its repeat; the model is not in the key. It says nothing about whether the
   assumption is ever broken. Owner to decide: name the rescue as a known case, or keep the rescue path
   out of scope.
2. **How long the gap was open for hosted games** (claims #6). The opening round's caching was
   committed 2026-10-07; the server ran the 2026-10-04 build until a 2026-10-11 deploy, so hosted games
   may have been exposed for about two weeks rather than 19 days, depending on which build first
   carried `b66ce7b4` (not confirmed). Page wording for now ties the window to its events ("once the
   day's opening round was added to that cache, and until the fix") and gives no length.

**For the verifier:**

3. **Six shared seats' roles, five reused openings** (ruling 3): which seat's opening did not match
   in the control, and why? The page says the record does not say, and offers the wolf-roster
   clause only as a possibility.
4. **How the control detected a reuse** (a missing scripted call, the capture, or the event stream)?
   Section 5 says "served … from the first game's cache" as the record does.
5. **The 19 candidate pairs** (ruling 4): the criterion for "potentially matching" is undefined in
   the record. The page states the count without a definition.
6. **No restart in the nine minutes between the two hosted games:** the server hosts all games in one
   process, but whether it restarted between them was not checked. The page now says so in section 4.
7. **Visible impact in the later game:** the Serial Killer's opening became a pass. Was anything
   else affected (e.g., a "generation failed" marker shown to players)? The page states only the pass.
8. **Whether the earlier game had a human seat** (claims "not checked"). The page now says "each AI
   seat's opening", which holds either way.

Resolved since drafting: the model is not part of any cached turn's input (claims review checked
`base_payload`, `build_speaker_send`, `_pack_payload`).

## Drafting notes (step 4, 2026-10-28)

- **Changes from the approved outline:** headings reworded (section 2 "Five choices that gave two
  games one key"; section 5 "Adding the game to the key"; section 6 "What remains unknown"). Model
  names and game ids moved to the sources comment: the table says "one model / a different model",
  because the point is that the copy crossed models, not which ones. Added a short **Evidence** link
  list after the copy, as the parent has. No section added, dropped or reordered.
- **Skim (headings, opening sentences, caption):** three sections opened on setup rather than their
  point ("What the cache is for" opened on what LangGraph is; "How easily two openings matched" on
  how the bug was found; "The game that received another game's failure" on how fallbacks work).
  Each now opens with its point. After the fix, the opening sentences read in order: the cache keeps
  AI turns; one case; the cache exists because resuming re-runs AI turns; five reasonable choices;
  matching openings were easy to produce; one hosted game shows it, and it copied a failure; the fix
  puts the game in the input; three tests; the before-and-after check; the deployed build checked;
  the fix doesn't show the earlier reach; the remaining assumption; the lesson.
- **Watch in review:** the wolf clause in section 5 sits beside the five-of-six result and could be
  read as its recorded cause (ruling 3 allows the clause; the cause is not recorded).

## Step 7 (skipped in this trial): what would change in other files

- `editorial_notes.md`: a dated entry (explanatory path: purpose → five-link chain → reachability →
  recorded case → fix and control → unknown reach; what moved out: pickle detail and 20-ballot game to
  the parent, the three-record exhibit to chapter 7, the thread-reuse safeguard to the report; claim
  changes, if any, after review; "editorially revised" is not "factually verified").
- The page's italic header line: status and date.
- `content_plan.md`, Level 3 table: the anchoring subsection is named "A stable cache key also needs a
  game boundary", which no longer exists in the parent (the link now sits in "Replaying a step must
  preserve the right result"). Would flag to the owner rather than edit, since the plan is theirs.
- `human_in_the_loop.md`: no change expected (title and question unchanged); recheck its link sentence
  only if the page's scope changes after review.
- `exhibits/source_map.md`: CK rows' status, once the exhibits are drafted. CK-chain stays a numbered
  list; CK-two-games is now a table without model names; CK-three-records is prose; CK-control has no
  table (prose only).
- `.agents/skills/write-portfolio-page/scripts/review.sh` (for the owner, not this trial): the
  extractor drops only a *line* starting with `*Level N`, so a wrapped header line leaks its
  continuation lines into the editorial reviewer's page copy (the cause of editorial #9). Either note
  "keep the header on one line" in SKILL.md step 4, or drop the whole italic paragraph.
- Step-7 claim changes for `editorial_notes.md`: the replay is now worded as attributed throughout;
  "games no longer share cached turns" narrowed to "the key now separates games"; the pre-flight
  narrowed to the id check; "every captured game" corrected to the offline capture runs; "the rules"
  removed from the opening input; the window and the model assumption reworded pending the owner
  (open questions 1–2).

## Review resolution

Reviews: `cache_key.skill.review-editorial.claude.20261028T140515Z.jolcKx.md` (E) and
`cache_key.skill.review-claims.claude.20261028T140710Z.PNmRNG.md` (C), both read in full, 2026-10-28.
The editorial reviewer's stated argument matched the frame (purpose → five choices → reachable →
observed → fix → unknown → lesson), so the structure stood; the findings were about scope, missing
context and a self-contradiction.

| Reviewer | Finding (passage) | Action: fixed / declined (why) / flagged | Recheck needed? |
|---|---|---|---|
| E1 + C1 | "every captured game made all of its own day-1 calls" contradicts the case (the later game was captured) | **Fixed.** In the record "capture" means offline capture runs, not the 11 captured hosted games. Now "every recorded batch game, and every offline run that captured prompts"; added that batch games share one process and cache, so their clean record means something | Rechecked the paragraph: the 11-of-68 sentence now refers only to hosted games |
| E2 | The game is never introduced; "dealt the same set of roles" reads as coincidence | **Fixed.** Opening now names the game first (Mafia-style, AI agents, ten seats, hidden roles, a person may take a seat) and says each day starts with an opening round, and that on day 1 a seat's opening input depends only on the deal. No further rules | Rechecked link 5: consistent with the new intro |
| E3 + C3 | Replay stated as fact in the opening and section opener, an inference later; same-process / no-restart not addressed | **Fixed.** "The records point to one case"; "the records indicate that this seat received…"; section opener "records point to a collision". Section 4 now says the no-restart condition was not checked for this pair | Opening and section 4 read consistently |
| E4 + C8 | Pre-flight "two freshly dealt games shared no opening key" shows little (most fresh pairs never matched) and is not "the same way" as the played control | **Fixed.** Kept only the meaningful half of the deploy-log check: the production image puts the game's id on every cached input. Dropped "the same way" | — |
| E5 | "Hosted" and "batch" games undefined; unclear whether batch shared the cache | **Fixed.** Opening: "games hosted on the project's web server"; section 3: the server runs all games in one process; section 6: a batch plays its games one after another in one process with one cache | — |
| E6 | Seat counts unclear (9 AI seats vs ten calls) | **Fixed.** Intro gives ten seats and that a person may take one; the control says every seat was played by the scripted model; table says "every AI seat" | — |
| E7 | Model's absence raised as part of the bug, but the fix adds only the game; reads as incomplete | **Fixed** with cautious wording because of C5: the fix section says separating games does not need the model, and that within one game the cache assumes the model does not change, pointing to the next section | Worded so it is not wrong whichever way open question 1 is decided |
| E8 + C6 | "Nearly three weeks": no start/end events; hosted exposure may be about two weeks | **Flagged** (owner, open question 2). Page now ties the window to its events, with no length | — |
| E9 | Trial metadata reads as a fragment inside the page copy | **Fixed.** Header put on one line above `## Page copy (draft)`, which the reviewer's extractor drops (checked with the extractor's logic). The page copy has no authoring status. Cause recorded under Step 7 | — |
| E10 (taste) + C4 | Wolf clause sits after the result and reads as the recorded cause of six → five | **Fixed.** Moved straight after "five", introduced by "The record does not say why the sixth shared role produced no reuse". Kept the clause (owner ruling 3) as a possibility only | — |
| E11 (taste) | "The record" ambiguous; sounds like an independent authority | **Fixed (agree).** "The records point to…" for the logs; "the incident analysis attributes this…" for the conclusion | — |
| E12 (taste) | Lesson and assumption crowd the "unknown" section; fallback point repeated three times | **Partly applied.** Lesson moved to its own short closing section, "What a cache key must name". The fallback point now appears twice: as mechanism in section 4 and once in the lesson (the owner ruled it part of the lesson); the extra mention in section 4 was cut. The model assumption stays in "What remains unknown": it is remaining exposure, not lesson | — |
| E13 (taste) | "142 calls" has no reference point | **Fixed (agree, lightly).** "142 calls over the whole game and no failures"; kept the count because it gives the size of the clean ledger | — |
| C2 | "Games no longer share cached turns" claims more than the checks show | **Fixed.** "Show that the key now separates games." The fix-section scope sentence stays | — |
| C5 | Stall rescue already switches the model mid-game; "would break" reads as hypothetical | **Flagged** (owner, open question 1). Reworded to state the assumption and that the model is not in the key, with no claim either way about it being broken | — |
| C7 | "The rules" are not in the opening input (they come through the run's settings) | **Fixed.** "The seat, its role, the set of roles in play and the list of seats" | Rechecked intro ("depends only on the deal"): still true of the input |
| C9 | Five tests, not three; "night wrappers" could mean all nights | **Fixed.** "The tests check the key in four ways", adding the different-turns / different-games check; "day and wolves'-night wrappers" | — |
| Own recheck | "first day's opening round was added" was wrong: every day's opening is cached; only day 1's can collide | **Fixed.** "the day's opening round" | — |

**Second review?** Not needed on the rules in step 6. The structure is unchanged apart from the lesson
becoming its own short section. The central claim is the same, now scoped more carefully (attributed
replay, a key that separates games). Re-review after the owner rules on open questions 1–2 only if
the stall-rescue ruling adds a claim.
