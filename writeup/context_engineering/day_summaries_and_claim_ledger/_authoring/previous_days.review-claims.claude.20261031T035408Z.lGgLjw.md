<!-- claims review of writeup/context_engineering/day_summaries_and_claim_ledger/previous_days.md by claude (opus), 2026-10-31T03:54Z -->

## 1. Findings

- **Claim:** "On 89 replayed turns from earlier games, attributing every claim moved bad samples from 36% to 31% of 267, with 24 cases better and 14 worse" (*How a carried-forward error cascades*, case 1).
  **Source checked:** `evidence/gameplay/discussion_evidence.md` §6.4 (R-a to R-h), §6.5 (the three-arm table), §6.6; `evidence/gameplay/turn_prompt/report.md` decision 3; `writeup/context_engineering/explicit_game_information/facts.md` (page 1).
  **Verdict:** unsupported inference (several changes were made at once, and the page credits the result to one of them).
  **Why:** The "before" arm is the code at `fidelity-baseline`. The "after, re-summarised" arm adds the whole fidelity pass: the rules on silent night events, a private night record for each night actor, the labelled blocks, the "voted to eliminate" wording, the vote turn seeing its own note, and the v3 summary. Decision 3 and page 1 credit the same 97 → 82 to that whole pass. The only arm that isolates the summary rewrite is "after" (new code with the games' own summaries, 86/267) against "after, re-summarised" (82/267), which is 32% → 31%. The page also puts attribution and the dropped story section into one rewrite. They were separate: v3 on 2026-10-03, which still had "village dynamics", and v4 on 2026-10-04. So the bench number measured a summary that still contained the story section the page says was removed. (Report §6's first bullet has the same bundling.)
  **Suggested scope:** Say that the whole fidelity pass, of which the attributed summary was one part, moved bad samples from 36% to 31% (a direction, not an established effect), and that re-summarising earlier days with the attributed version on top of the other changes moved them only from 32% to 31%. Alternatively, drop the number and give the dates of the two rewrites separately.

- **Claim:** "What the town acts on is mostly **claims**, a player's statements about its own role and its nights … (why claims carry the talk is told on chapter 1's evidence-design page)" (*Why earlier days cannot simply be replayed*).
  **Source checked:** `writeup/game_design_orchestration/evidence_design/evidence_design.md` (page copy); `discussion_evidence.md` §2.1; content plan §2, section 2; `l2_outlines.md` row for page 2.
  **Verdict:** unsupported (the only measurement found points the other way).
  **Why:** The chapter-1 page does not say that claims carry the talk. It describes a ten-seat redesign meant to give the town claims and partial observations to test against each other. The only measurement found is §2.1 (nine-seat game, 194 accusations): behaviour and voting carried about three-quarters of accusations and concrete claims about one-fifth. I found no measurement for the ten-seat game. The page's main argument for using fields (claims span days and must be set against the record) holds without "mostly".
  **Suggested scope:** Something like "The game is built so that role claims and claimed night results can be tested against each other and against what the engine announces, and those tests span days", with the link described as explaining why the roles were designed that way.

- **Claim:** "Each summary that went wrong in a ten-seat game was frozen as a **replay case**" (*How it is checked, and how it runs*).
  **Source checked:** `evidence/gameplay/data/phase3_summary_replay/README.md` (case selection); `discussion_evidence.md` §8.4 ("summary errors 22" in ten audited games).
  **Verdict:** overstated.
  **Why:** The cases were selected in two ways: five games read by hand, plus a scan of 31 games for two specific error patterns (a self-targeted action, and the copied record check). Denial and roleblock cases were added later. The audit counted 22 summary errors, mostly omissions and distortions, and there is no record that each one became a case. (Report §6 uses the same "each".)
  **Suggested scope:** "Summary failures found in the ten-seat games (the self-block, the copied record check, dropped denials, misfiled roleblocks) were frozen as replay cases."

- **Claim:** "a stall or error goes to the game's rescue model, a different model assigned to the game, and if that fails too the day is stored as the raw transcript" (*How it is checked, and how it runs*).
  **Source checked:** `evidence/extraction/day_summary/report.md` §5; `Agents/nodes/day/summary_agent.py` (lines 75–102).
  **Verdict:** overstated (wrong mechanism for the default case).
  **Why:** The report says "If there is no rescue model, or it fails too", and notes that the house default, Claude Haiku 5.5, has no rescue model in the catalogue as seeded in code. So on the default model a stall goes straight to the raw transcript unless the player has added a backup key. The code also treats a missing rescue model as "no rescue". The page implies every game has one.
  **Suggested scope:** "… goes to the game's rescue model where one is assigned, and if there is none or it fails too, the day is stored as the raw transcript."

- **Claim:** "On day 4 three town players, who had seen only this summary, treated the survived attacks as fact." Together with the heading "A premise returned as narration" and "The guard was attribution", this presents the summary as the cause (*How a carried-forward error cascades*, case 1).
  **Source checked:** `discussion_evidence.md` §6.4, "Likely causes".
  **Verdict:** unsupported inference (minor).
  **Why:** The record lists the summary's narration as a *likely* cause of item 3. It lists a second cause beside it: the rules never said that a failed attack on the serial killer is not announced. In §6.5's pinned case, the wolf still stated the survived attacks as fact after the rule fix.
  **Suggested scope:** Keep the facts, but call the summary the likely route ("most likely accepted it from the summary"), or add one clause noting that the unannounced failed attack was a second gap, fixed in the rules.

- **Claim:** "The ledger reads those first and the summary's transcription only for a player who filled no field that day" (*Why judging left the model*).
  **Source checked:** `Agents/rules/claim_ledger.py::build_claim_ledger` (lines 180–249); report §4 ("no field *of that kind*").
  **Verdict:** overstated (small difference in mechanism).
  **Why:** The fallback works separately for each kind of field. The summary's role is used when the speaker set no role field, and its night actions are used when the speaker set no action field. A player who filled a role field but no action field still gets the summary's actions.
  **Suggested scope:** "… and the summary's transcription only where a player filled no field of that kind that day."

- **Claim:** "with a model judging each summary against the transcript and the record … Both models were flawed in 18 of 30 summaries" (*Why judging left the model*).
  **Source checked:** `evidence/gameplay/deduction/experiment_log.md` §3, including the 2026-10-24 note.
  **Verdict:** unclear (needs the owner); this is the brief's open question 3.
  **Why:** The judge was Sonnet 5.5, one of the two models compared. The log's note explains why the equal 18-of-30 result and the 27-of-27 finding still hold (any self-preference would have favoured Sonnet). So the conclusion is supported, but "a model judging" hides a known limit on how the result was checked.
  **Suggested scope:** Optionally add "the judge was the stronger of the two models, which if anything would favour it", or leave as is if the owner accepts the omission.

- **Claim:** "The summary is continuity within a game, not memory: it is rebuilt from that game's days and never stored across games" (*What is not established*).
  **Source checked:** report §1–§3; `Agents/schemas/game_events.py` (`DaySummary`), as cited in the report.
  **Verdict:** wrong mechanism (wording).
  **Why:** The summary is written once per day and stored with that game. The ledger is the part that is rebuilt for every prompt. Saying the summary is "rebuilt" mixes the two up, after the page explained the difference correctly in section 3.
  **Suggested scope:** "it is written for each day of one game and never carried into another."

- **Claim:** the before/after table rows, with "After the fix" as clean results (*How it is checked, and how it runs*).
  **Source checked:** `phase3_summary_replay/README.md`, the "Claim retention" and "Roleblocks" tables.
  **Verdict:** overstated (minor; optional).
  **Why:** The same replays also tracked true claims lost on control cases. After the denial fix, Flash-Lite lost 2 of 20 controls where it had lost 0 (the README says this is possibly a cost of the longer instructions, not established). Luna lost 8 of 20 before and 6 of 20 after. The table shows only the targeted failure, so a reader may assume the fixes had no side cost.
  **Suggested scope:** Add one clause: the same replays checked that true claims were kept, and the denial fix may have cost a few of them (not established at five samples).

## 2. Checked and supported

- One call per day, before the vote; two lists; at most 30 words a field; fixed action and result words; plans in their own list; "claimed"/"retracted"; no vote tally or night outcomes; every statement attributed; the prompt forbids stating a claim as fact. Sources: report §2; `Agents/schemas/output.py` (`RoleClaimV4.planned_actions`, `DaySummaryOutputV4`); experiment_log ③ 2026-10-04.
- The day-2 rendered summary and the day-3 "Previous days" block match report §2 and §3.
- Three blocks with three authors: the engine writes the game master's record; code builds the ledger; the accusations go straight from the summary into the prompt. Sources: report §3; discussion_evidence §6.6.
- The ledger's checks (revealed role, investigation against revealed role, save against announced saves); it says nothing where the record fits more than one reading (the shot player who lived); it is never stored and is rebuilt for every prompt; a claim the record cannot contradict stays a claim. Sources: report §3 and §8; §6.6.
- The labelled headers came from the 2026-10-03 code review, which found engine facts and a model's summary looking the same once rendered, in the same pass that added each night actor's private record. Source: turn_prompt/report.md decision 3.
- Case 1 facts: nine-seat game `46355b89`, early October; a wolf argued from the failed attack on the serial killer; two villagers called it fabricated; the wolf was voted out; the summary line is verbatim; the premise is stated as fact. Sources: §6.4; experiment_log ③.
- Case 2 (e06): both lines verbatim; a town player opened day 3 on the claim; the Investigator accepted it ("to draw fire"); voted out 7 to 1 while holding a correct Suspicious result; the Necromancer won; the speaker's field was empty, so the ledger fell back on the summary. Sources: report §7; §8.4.
- The e06 fix: the instruction, plus a ledger rule that drops self-targeted "done to me" actions and drops the role only for a Chanteuse claim resting on a self-block (also conditioned on no role field that day). Sources: `Agents/rules/claim_ledger.py` lines 49 and 226–237; commit `6248fc58` per report §7.
- The broader first rule lost a true Vigilante ("held my fire" written as shooting itself); the replay caught it before it shipped. Source: phase3_summary_replay README, "Reading".
- "In 10 replayed samples of that day, before and after the fix, the invented claim never recurred": 0 of 5 on each arm, 10 in total. A unit test pins the rule: `tests/engine/test_claim_ledger.py` line 330 onward (the e06 fixture). Source: README.
- The 5-of-5 → 0-of-5 later-speaker figure is correctly kept off the page. Source: §8.4.
- Verdicts in v3 ("supported/contradicted/unverified"): nearly all "unverified"; the field was dropped from the claim record; "supported" was a subjective call (owner's ruling); replaced by the ledger the next day. Sources: §6.6; experiment_log ③ 2026-10-04.
- The record check stayed for accusations; 66 summaries judged (60 test plus 6 live); 27 written, all 27 judged wrong, none a real conflict; 18 of 30 flawed for each model; the summary stayed on the game's model; the check was removed on 2026-10-16. Sources: deduction/experiment_log §3; report §6.
- Speaker fields since mid-October (role field 2026-10-09, actions 2026-10-18); a human seat has no fields; accusations, retractions and plans come from the summary alone. Sources: decision 13; experiment_log ③; ledger code.
- Table row 1 (denials 30/30 → 7/30 and 0/30) and row 2 (Luna 15/15 → 0/15; "the model that showed it" matches §8.4's own wording). Sources: README; §8.4.
- The bench seats reported no reasoning tokens; turning reasoning on cut bad samples from 31% to 10%, more than any summary change. Source: §6.7.
- Runtime: the game's own model, medium thinking by default, 90-second wait. Source: `Agents/llm_factory/accessors.py` lines 40–41.
- What is not established: the summary was never compared with the full transcript, and why the summary stays anyway; no error rate for today's prompt and model; the May judge scores sections no longer written. Sources: report §8; experiment_log ④.
- Off-page items: none from the brief's "Elsewhere" list or the chapter outline's "stays off" column reached the copy. No model family names in prose. "Judged wrong" is used throughout, never "wrong".

## 3. Not checked

- **The 97% figure:** I could not find its source in chapter 1's page, the map or the outlines. I only confirmed that it is not on the page.
- **Exhibits byte for byte:** the `2f19d908` summary against `summaries.jsonl` and the "Previous days" block against `AC2_before_note.txt`. I checked them against report §2 and §3 only.
- **The rescue model for Haiku:** I took the report's statement that Haiku has no rescue model in the seeded catalogue as given; I did not read `catalog.py`.
- **Unit tests:** I did not run them. The claim that the ledger and the rendering tests pass rests on report §6 (passed at `c0732f88`).
- **"I rewrote the summariser":** the records I read do not say who wrote that prompt. I did not check the authorship memory or the commit authors for the prompt changes.
- **Game details:** the claim that the Chanteuse is "the wolf that blocks a player's night action", and the e06 cast details beyond report §7, were not checked against the role sheet.
