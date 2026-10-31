<!-- claims review of writeup/information_boundaries/wrong_agent_inputs.md by claude (opus), 2026-10-31T06:22Z -->

## 1. Findings

- **Claim:** "When the game grew from nine seats to ten on 3 October, one record per night action replaced the Investigator's and Vigilante's result fields, and the new check replaced their two checks. So from that date night-result isolation had no live check at all" (*The same shape, four months later*)
  - **Source checked:** `evidence/agent_boundaries/experiment_log.md` §5 (night records came in `f1b3017b`, 2026-10-03; `check_night_record_isolation` came in `9b729aac`, 2026-10-09). I also checked the dating of the seat change in the project records: the information-fidelity pass built the night record (`NightActionRecord`) on 2026-10-03, in the nine-seat game. The role sheet is dated 6 Oct, Phase 3 (roles) started 2026-10-07, and that day the engine "still deals the 9p set".
  - **Verdict:** conflicts with source
  - **Why:** The night records replaced the result fields on 3 October, but the game did not grow to ten seats that day. That came after 7 October. The log's heading "The ten-seat game (2026-10-03 to 10-14)" covers both events, and the page has merged them. Also, "the new check replaced their two checks" reads as if it happened the same day, but the check arrived on 9 October. The conclusion (no live night-result check from 3 October) still holds.
  - **Suggested scope:** "On 3 October one record per night action replaced the Investigator's and Vigilante's result fields; the check that replaced their two checks followed on 9 October, so from 3 October night-result isolation had no live check at all." Leave out the move to ten seats, or give it no date.

- **Claim:** "how the same gap came back four months later in another form" (opening); "The same shape, four months later" / "The second instance has the same shape" (*The same shape, four months later*)
  - **Source checked:** `experiment_log.md` §6 ("`run_leak_tests` had grown optional arguments for the eliminated players (May), the held candidates (July) and the night records (October)"). Also the page's own source note: `e9d30ba` called `run_leak_tests(prompt_log, roles)` without `eliminated_players`, "so the eliminated-player check ran with an empty input from the first wiring on".
  - **Verdict:** overstated
  - **Why:** In October the gap was *found*, not reborn. One of the three empty checks (eliminated players) had been fed nothing since the June wiring itself, and that includes the June post-fix game the page shows as clean. The held-line check had been empty since July. Only the night-record case began in October. The page hints at this ("an optional input since the checks were first wired in"), but "came back" tells the reader the June fix fully closed the gap and it returned later.
  - **Suggested scope:** "how the same gap was found again four months later, in checks that had been running but were fed nothing, one of them since the June wiring." The heading can become "The same shape, found in October".

- **Claim:** "The Vigilante's feedback was a new field that day, and the change adding it put it into the common part of both builders" (*Where the bundle came from*). Related: "a rewrite of the day's discussion gave every speaker one bundle of inputs carrying three roles' private fields" (opening).
  - **Source checked:** the page's source note (commit `291668f3`, 2026-06-06 02:43 UTC, added `vigilante_results` to the base payload of both `build_speaker_send` and `fan_out_day`); `experiment_log.md` §2 "Verdict" and "A third field".
  - **Verdict:** unclear (needs the owner)
  - **Why:** In the paragraph before, "that day" can only refer back to the 3–4 June rewrite. The source note dates the Vigilante change to 6 June, a separate change hours before the catch. If 6 June is right, the rewrite's bundle at first carried two private fields, the third came later, and the "three days" applies to two fields only. I could not run git to confirm the commit date (shell is disabled in this session).
  - **Suggested scope:** Name the date ("added on 6 June, the morning of the catch, into the common part of both builders"). In the opening, say the shared bundle "came to carry" three fields, or credit the third to the later change.

- **Claim:** the after-fix exhibit `=== Running Leak Tests === / === Leak Tests Complete === / Batch complete: 1 succeeded, 0 failed / EXIT: 0` (*Why it went unnoticed, and the fix*)
  - **Source checked:** `evidence/agent_boundaries/leakfix_smoke.log` lines 94–98.
  - **Verdict:** unclear (needs the owner)
  - **Why:** Line 96 (`Completed leakfix_smoke_all_disabled_001: winner=wolves day=4`) is left out of what is shown as one continuous log excerpt, and nothing marks the gap. The source note explains why, and the claim ("empty between its banners … exits clean") is true. Still, a reader who opens the log will find the quote doesn't match it line for line.
  - **Suggested scope:** Mark the omission with a `…` line, or include the line.

## 2. Checked and supported

- 109 = 38 inputs × 2 lines + 33 × 1. The Vigilante field added 0 because no check covered it and was found by inspection: experiment_log §2 "Composition" and "A third field". Confirmed in `leakwire_smoke.log`: exactly 109 `LEAK:` lines.
- The healer exhibit lines match `leakwire_smoke.log` lines 94–95 word for word.
- "A flag says private data crossed the boundary where access is enforced, not that a model saw it"; the variables copy the bundle's values unchanged: report §3 ("layer 3 just forwards `payload.get(field, default)`"; "may or may not have rendered").
- After each game, the batch runner's checks read the recorded prompt variables: report §3 "Where the checks run"; `tests/leak_test.py` `run_leak_tests`.
- The Vigilante feedback reached every voter, not only the speakers: experiment_log §2 ("`fan_out_day`'s base payload (every voter)"; "not discussion-only").
- The earlier design built one bundle per role: experiment_log §1.
- The comment's "ignores extra keys"; that behaviour belongs to a different way of connecting steps than the one this path used; the declared field list enforces nothing; "the documented justification was the bug": experiment_log §2 "Cause"; report §2 layer 1 and §4. The "two ways of connecting steps" wording is a fair plain-language version of the record's state-channel/subgraph filtering versus a `Send` into a plain node.
- The search of the templates: each placeholder appears only in its own role's templates; nothing rendered on discussion or vote; no game result affected: experiment_log §2 "Severity".
- The "none rendered" finding is scoped to one search, with no standing check of rendered prompts: report §5 "No standing audit of the rendered prompt". "Templates rewritten since": experiment_log §5 (shared-prefix layout, 2026-10-14).
- The timeline: checks written 9 May and run from a notebook; rewrite 3–4 June; wired 6 June; first game 109 flags; a later game 0 flags: experiment_log §1 and §2. "A game played after it" (not "the next game") matches the source note's fingerprint-timing caveat.
- Fix contents (bundle built by role, vote step cleared, comment rewritten, Vigilante check added): experiment_log §2 "Fix (`ef43342`)" and `8008623`.
- October: three checks fed nothing; the batch runner passed only the variables, roles and reads; the fix lifts the three inputs from the final state; unit tests plant a night record; the eliminated-player check moved off the game master's prose onto death records: experiment_log §6; report §5 "Closed"; `tests/leak_test.py` `leak_inputs`.
- "Unit tests covering only part of them" (the builders): experiment_log §5 (day builders pinned 10-07) and §6 (night builders pinned by the October fix).
- The three quoted lessons are verbatim: experiment_log §2 "Lessons".
- "Early warning rather than a silent fault" and "one template edit" away from exposure: report §3, last paragraph.
- Site games save the variables plus the state fields the October fix added: `server/storage/prompt_captures.py` `LEAK_STATE_FIELDS` includes `dead_roster`, `day_channel`, `night_actions` (the three `leak_inputs` sources) along with roles and others. "A nightly job is built" keeps to the owner's ruling to mention it without status.
- Handle-with-care items: no test or check counts, no CI, no test authorship. The uninstalled cron is not stated. Runs from uncommitted trees and the reads-check false alarms are kept off the page. The checkers fed nothing are told as caught and fixed.

## 3. Not checked

- **The date of commit `291668f3` and the pre-fix code at `ef43342^`:** shell and git are unavailable in this session, so the source note's commit dates, line references and the quoted full comment were taken as given. Finding 3 depends on this.
- **First person, "I put the selection back where the bundle is built":** the authorship record says the owner wrote about 90% of the orchestration but doesn't cover this June fix specifically. Brief open question 2 already puts this to the owner.
- **Whether site games save captures today:** project notes say migration 0013 was applied and the site was redeployed on 2026-10-15. I could not confirm in git that the deployed image includes the capture commits, so "Games played on the site save…" is likely true but not checked.
- **The framework behaviour** (a `Send` delivers its payload verbatim; a compiled subgraph filters its input to its schema): taken from the record's framework note for the pinned versions, not re-tested.
