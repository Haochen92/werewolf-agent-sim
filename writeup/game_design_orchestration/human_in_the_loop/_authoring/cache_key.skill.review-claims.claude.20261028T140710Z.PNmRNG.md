<!-- claims review of writeup/game_design_orchestration/human_in_the_loop/cache_key.skill.md by claude (claude-opus-5-5), 2026-10-28T14:07Z -->

I found nine problems on the page. One contradicts the page's own case; the rest are wording that claims more than the records show, plus two points only you can settle. I edited nothing.

## 1. Findings

**1.**
- **Claim:** "Every recorded batch game and every captured game made all of its own day-1 calls." (What remains unknown)
- **Source checked:** `evidence/gameplay/orchestration/report.md` decision 12, "Extent and remaining uncertainty" ("No recorded batch or capture game lost a day-1 call"); `evidence/tracing/report.md` "Batch and capture runs" and "The cross-game node cache".
- **Verdict:** conflicts with source
- **Why:** In the records, "capture game" means the offline capture runs, which are a separate kind of run from hosted games. The page puts this sentence right after "11 of the 68 hosted games have prompt captures", so a reader takes "captured game" to mean those 11. That set includes the later game, `51226f24`, which per the tracing report has a capture and did not make its Serial Killer seat's call.
- **Suggested scope:** "Every recorded batch game and every offline capture run made all of its own day-1 calls."

**2.**
- **Claim:** "Tests and a before-and-after check show that games no longer share cached turns" (opening)
- **Source checked:** decision 12, "Fix" and "Extent"; "What is not established", bullet 5; `tests/engine/test_turn_cache_key.py`.
- **Verdict:** overstated
- **Why:** The tests check how the key is built and the day-1 openings of 12 dealt games. The control covers day-1 openings on two deals. The report also says no served-game check after the fix is recorded. That games no longer share any cached turn follows from the design: the id is now in every cached input. The checks did not show it. The page's own scope sentence ("These checks cover how the key is built and day-1 openings on two deals") is the accurate version.
- **Suggested scope:** "Tests and a before-and-after check show that the key now separates games."

**3.**
- **Claim:** "a game on a different model … received one of those failed passes at one seat instead of making its own call." (opening)
- **Source checked:** decision 12, "Recorded incident" ("The record identifies this as replay"); tracing report ("no explicit cache-hit record").
- **Verdict:** overstated
- **Why:** The opening states the replay as an observed fact. Section 4 then correctly calls it "an inference from records consistent with the mechanism, not an observed cache hit". A reader who stops after the opening gets the stronger version.
- **Suggested scope:** Add a short qualifier in the opening, for example "…the records show it received…" or "…by every record, received…".

**4.**
- **Claim:** "Matching roles do not guarantee matching inputs, since a wolf's input names its partners." (Adding the game to the key)
- **Source checked:** "What is not established", bullet 5; brief ruling 3 and open question 1; `Agents/nodes/day/flow.py::_private_fields`.
- **Verdict:** unsupported (as an explanation)
- **Why:** The sentence is true of the code. Placed right after "six seats' roles … five of the second game's openings", it reads as the recorded reason why only five of the six matched. The record does not say which seat differed or why. The brief flags this same risk.
- **Suggested scope:** Remove the sentence, or say "the record does not say which seat's input differed" and leave out the wolf clause.

**5.**
- **Claim:** "The model is not in the key, so switching a game's model partway through would break that assumption." (What remains unknown)
- **Source checked:** orchestration report, "When to revisit the design", row 3; `interview_prep/langgraph_langfuse_issues.md` §7.4 and §10.1.
- **Verdict:** unclear (needs the owner)
- **Why:** The interview notes say the deployed stall rescue already moves a game to the rescue model for 300 s after two stalls in a row (deployed 2026-10-01), and that "the rescue switches the model mid-game outside the cache key". So the condition already arises in live games. "Would" makes it sound hypothetical. Whether that matters in practice (a replayed answer from the original model) is not recorded.
- **Suggested scope:** Either "the stall rescue can switch a game's model partway through, and the key does not see that", or keep "would" if you judge the rescue path out of scope.

**6.**
- **Claim:** "For nearly three weeks, that cache could also give a turn from one game to another." (opening)
- **Source checked:** sources comment (2026-10-07 to 2026-10-26, 19 days); `frontend/docs/deploy_log.md` 2026-10-04, 2026-10-11 and 2026-10-26.
- **Verdict:** unclear (needs the owner)
- **Why:** The 19 days run from the date the opening-round caching was committed. The hosted server ran the 2026-10-04 build until 2026-10-11 ("72 commits since the last deploy"; `:prev` = the 2026-10-04 images). So hosted games could hit this from 2026-10-11 at the earliest, about two weeks. I could not confirm that commit `b66ce7b4` was in the 2026-10-11 build because I had no git access. The paragraph opens on a human's pause, which frames it as hosted games. On the other hand, by the page's own link 5, the gap existed in a less reachable form since 2026-08-19.
- **Suggested scope:** "For about two weeks in hosted games…", or name what is being counted ("from the day the opening round was cached").

**7.**
- **Claim:** "Its input holds the seat, its role, the set of roles in play and the rules" (link 5)
- **Source checked:** `Agents/nodes/day/flow.py::fan_out_day` `base_payload`; `Agents/config/langgraph.py::build_runnable_config`.
- **Verdict:** wrong mechanism
- **Why:** The game rules (`game_config`) reach the node through the run's settings, not the input. The input holds the seat, role, lineup, role counts, the list of seats, the day and round flags, and an empty transcript. This matters a little because link 3 has just said the key sees only the input.
- **Suggested scope:** "Its input holds the seat, its role, the set of roles in play and the list of seats."

**8.**
- **Claim:** "The deployed build was checked the same way before it went live" (Adding the game to the key)
- **Source checked:** `deploy_log.md` 2026-10-26 pre-flight.
- **Verdict:** overstated
- **Why:** The pre-flight compared opening keys between two freshly dealt games, like the 12-game test. The paragraph just before it describes games actually played back to back, which is a different check.
- **Suggested scope:** "The deployed build was checked before it went live: in the production image, two freshly dealt games shared no opening key."

**9.**
- **Claim:** "Three tests check the key. … The day and night wrappers put the game's id on the inputs they build." (Adding the game to the key)
- **Source checked:** `tests/engine/test_turn_cache_key.py`
- **Verdict:** conflicts with source (minor)
- **Why:** The file has five tests. The two not described (`test_key_separates_different_turns`, `test_key_separates_games`) are also key checks. The wrapper test covers the day and wolves'-night wrappers only, not the solo night phases. Those are not cached, but "night wrappers" could be read as all of them.
- **Suggested scope:** "The tests check the key…" and "the day and wolves'-night wrappers…".

## 2. Checked and supported

- Resuming re-runs the wrapper and the whole interrupted round, because the hand-built input is the privacy boundary: `server_encountered_challenges.md` §3; orchestration report decision 8.
- The node cache returns the stored result for a repeated input, and humans go through an uncached copy because their answer comes from the person: §4; decision 12.
- Link 3: the default pickle key changed after a checkpoint reload, and the value-based key stays stable: §5; `turn_cache_key` docstring.
- The game id lives in the run's settings, not the input: interview §2.3; `build_runnable_config`; `game_id_from_runnable`.
- The model is not in any cached input: confirmed in `fan_out_day` `base_payload`, `build_speaker_send` and `pack.py::_pack_payload`.
- The cache is keyed by node and key only; the compiled subgraphs and in-memory cache are shared by every game in the process: decision 12; interview §7.3; `TURN_CACHE_TTL_SECONDS` comment.
- Before the opening round, only votes were cached, and a vote's input carries that game's transcript; a day-1 opening comes before any night or speech: decision 12; interview §7.3; parent-graph diagram.
- A wolf's day input names its pack: `_private_fields` (`surviving_wolves`, `pack_roles`).
- The root cause is the key's missing scope, and the other four links would have been harmless with the game in the key: interview §7.3 ("links 1, 2, 4 and 5 harmless"); map block 115.
- Found while reading the code for a report, with neutral wording: interview §7.3 "If asked"; brief ruling 1.
- 7 of 66 pairs among 12 fresh deals, 8 seats, described as reachable collisions and not a rate: decision 12.
- The conditions for a hosted hit (same process, six-hour lifetime, no restart): `TURN_CACHE_TTL_SECONDS = 6 * 3600`; orchestration "Human seats".
- A failed model call becomes a `generation_failed` pass and is cached like an answer: `Agents/turn/agent_player.py:169`; decision 12.
- The two-games table (all of the earlier game's calls failed; nine minutes later; same lineup; Serial Killer the only matching seat; no captured prompt): decision 12 "Recorded incident".
- The three records (8 of 9 AI seats captured, the pass in the event log, 142 calls with none failed, a cache hit skips the logged part of the turn) and the inference wording in section 4: tracing report.
- The fix copies the game id into each phase's state, so every cached input carries it: decision 12 "Fix"; `flow.py` and `pack.py` payloads.
- The isolation test fails without the fix: decision 12; interview §7.3.
- The control (scripted model, five reused openings before the fix and none after; the real-model games made all ten calls each): "What is not established", bullet 5; gameplay hub "Execution reliability".
- The scripted model fills any answer without a model call: orchestration "How it was checked", row 1.
- Extent (one case; 19 other pairs with no copy; restart times not checked; 11 of 68 games captured; a copy visible only when its content gives it away): decision 12 "Extent"; "What is not established", bullet 3.
- Off-page items are kept out: no AI-written or unaudited tests, no commit hashes or image ids, no deploy bookkeeping, and no claim about hosted games since the deploy.

## 3. Not checked

- Whether `b66ce7b4` was part of the 2026-10-11 server build. I had no git access in this session; the deploy log only implies it (finding 6).
- Whether the earlier game (`14926d10`) had a human seat. If it did, "each player's opening turn became a fallback pass" (opening) is slightly broader than the record's "each opening".
- Whether two identical openings in one game still reuse the cache after the fix. The key-level claim rests on the reload test and the design; no recorded game after the fix exercised a resume.
- Whether the two hosted games ran in the same server process. This is inferred from the mechanism, with no process or restart record (brief, open question 4). The page does not assert it, so no finding.
- What "potentially matching" means for the 19 pairs. The record does not define it; the page's "could have matched" adds no definition of its own.
