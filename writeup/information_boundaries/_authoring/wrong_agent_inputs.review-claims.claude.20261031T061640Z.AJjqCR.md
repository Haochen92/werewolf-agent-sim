<!-- claims review of writeup/information_boundaries/wrong_agent_inputs.md by claude (opus), 2026-10-31T06:16Z -->

I found six problems on the page, all fixable by narrowing or rewording. The biggest is in the opening sentence; two others need a decision from you. The counts behind the 109 all match the log (38 roster lines, 38 wolf-name lines, 33 Investigator lines), and both log excerpts on the page are copied exactly. I couldn't run git, so I couldn't check anything that depends on commit dates or diffs; section 3 lists what that leaves open.

## 1. Findings

- **Claim:** "gave every speaker one bundle of inputs holding every role's private fields" (opening paragraph).
  **Source checked:** experiment_log.md §2 "Verdict" and §3; report.md §4.
  **Verdict:** overstated.
  **Why:** The record says the shared bundle carried three fields: the wolf roster, the Investigator's results and the Vigilante's shot feedback. The healer's target was not in it (its check flagged nothing). The wolves' night chat was not in the day's inputs at all until July (log §3). "Every role's" tells the reader the leak was much wider than it was.
  **Suggested scope:** "holding the private fields of three roles (the wolf roster, the Investigator's results and the Vigilante's shot feedback)".

- **Claim:** "The next game, with every check active, flagged none" (§ Why it went unnoticed, and the fix). Also "By then the checks needed more than the recorded inputs" (§ The same shape, four months later).
  **Source checked:** experiment_log.md §6 "Problem: three checkers were fed nothing"; §2 "Verification" ("all six checks active").
  **Verdict:** unclear (needs the owner).
  **Why:** The record says the eliminated-player input was added in **May**, and that the batch runner passed only the recorded inputs, the roles and the reads. If the June wiring also left it out, the eliminated-player check, which was probably one of the six, was already getting nothing in the June runs. Then "every check active" overstates the clean June run, and "by then" wrongly dates that input to later. I couldn't open the June wiring commit (e9d30ba) to confirm.
  **Suggested scope:** If the June wiring did leave it out, say "with every check running" or "the next game flagged none", and change "by then" to say one of the extra inputs dated from May. If the wiring passed it, no change.

- **Claim:** "I searched every template for each private placeholder" (§ Did any model see it?). Also "how I established that nothing was rendered" (opening) and "I put the selection back where the bundle is built" (§ fix).
  **Source checked:** experiment_log.md §2 "Severity" and "Fix"; the brief's open question 2; the code-authorship memory (you wrote most of the orchestration; most tests are AI-written).
  **Verdict:** ownership / unclear (needs the owner).
  **Why:** The record doesn't say who ran the template search. The payload fix is orchestration code, which you mostly wrote, so "I put the selection back" is probably fine. The search is less certain: it may have been done in an assisted session.
  **Suggested scope:** Keep "I" only if you ran the search or directed it; otherwise "A search of every template for each private placeholder found…".

- **Claim:** "Each agent turn records the bundle of inputs built for it just before the model is called, one step before those inputs are filled into the prompt text" (§ What the checks found).
  **Source checked:** report.md §3 (the capture point is the prompt-input dict, "layer 3's output") and §2 (layer 3 is the formatter).
  **Verdict:** wrong mechanism (minor).
  **Why:** What gets recorded is the set of prompt variables made from the bundle, not the bundle itself. The page draws exactly that line in its next section ("the code that turns the bundle into prompt variables"). The step from "flag" to "the boundary was crossed" holds only because the formatter passes the bundle's values straight through and the checks look at values, not at whether a key exists. Saying the record is "the bundle" skips that step and contradicts the page's own model.
  **Suggested scope:** "Each agent turn records the prompt variables made from its bundle, just before they are filled into the template; since that step copies the bundle's values unchanged, private content there means the bundle carried it."

- **Claim:** "The private fields rode through every stage" (§ Where the bundle came from).
  **Source checked:** report.md §2 (layer 4) and §4; experiment_log.md §2 "Severity".
  **Verdict:** overstated.
  **Why:** The last stage, the templates, dropped every one of the fields. That is the page's own finding in the next section. As written, the reader is told the fields went all the way through and then told nothing rendered.
  **Suggested scope:** "The private fields rode through every stage up to the templates."

- **Claim:** "In the record's own words: … a check outside the execution path verifies nothing" (§ What this establishes).
  **Source checked:** experiment_log.md §2 "Lessons"; report.md §4 "Lessons".
  **Verdict:** conflicts with source (minor).
  **Why:** The record says "Checks that do not run on every execution decay into false confidence"; log §6 uses the phrase "a correct checker outside the execution path". The page's sentence is a stronger paraphrase but is presented as a quote.
  **Suggested scope:** Quote the record's sentence, or drop "in the record's own words" for that lesson.

- **Claim:** "night-result isolation had had no live check since 3 October; it was held by the input builders and verified in unit tests only" (§ The same shape, four months later).
  **Source checked:** experiment_log.md §5 (day builders unit-tested from 2026-10-07) and §6 (night builders tested by the October fix's own new tests).
  **Verdict:** overstated (minor; the page repeats the record's wording).
  **Why:** Between 3 and 14 October, the night-phase input builders had no unit tests, and the day builders had none until 7 October. So "verified in unit tests" was only partly true over that window.
  **Suggested scope:** "it was held by the input builders, with unit tests covering only part of it".

## 2. Checked and supported

- What the 109 count is (76 = 38 × 2 wolf-identity lines plus 33 Investigator lines): experiment_log.md §2 "Composition"; leakwire_smoke.log counts 109 `LEAK:` lines, 38 "received surviving_wolves", 38 "received wolf identities" and 33 "received investigator_results".
- The "before" exhibit (the two healer lines) is lines 94–95 of leakwire_smoke.log, word for word.
- The "after" exhibit matches leakfix_smoke.log lines 94–98 exactly (an empty block between the banners, then `Batch complete: 1 succeeded, 0 failed` and `EXIT: 0`).
- The Vigilante's feedback was outside the 109, found by inspection, and also reached every voter: experiment_log.md §2 "A third field"; report.md §4.
- A flag means the boundary was crossed, not that a model saw the data; the `LEAK:` label: report.md §3; experiment_log.md §1.
- The checks run after each game the batch runner plays: report.md §3 "Where the checks run". This matches the care list's scope.
- The earlier design built one bundle per role: experiment_log.md §1.
- The comment quoted as "ignores extra keys", and the cause (a subgraph-style boundary that filters fields versus a pass-through dispatch; the declared field list enforces nothing; the formatter passes everything on): experiment_log.md §2 "Cause"; report.md §2 framework note.
- Templates fill only the placeholders they name; each private placeholder appeared only in its own role's templates; nothing rendered on discussion or vote; no game result affected: experiment_log.md §2 "Severity"; report.md §2 layer 4.
- "None rendered" is limited to one search, and the templates have been rewritten since: report.md §5; experiment_log.md §5 (shared-prefix layout).
- The timeline (9 May notebook; 3–4 June rewrite; 6 June wiring and 109 flags; the fix, then 0 flags): experiment_log.md §1 and §2 "How it persisted"; report.md §4.
- What the fix did (private fields attached by role, the vote step cleared, the comment rewritten, a Vigilante check added): experiment_log.md §2 "Fix"; the source note's commit list.
- October: three checks fed nothing; the night-record check replaced the two result-field checks; the eliminated-player check was moved from parsing the game master's text to the death records: experiment_log.md §5–6; report.md §5 "Closed".
- "Early warning" (the checks read the inputs one step before rendering): report.md §3, last paragraph.
- The site-games sentence follows the owner-approved wording exactly (content_plan.md care list, 2026-10-30). It doesn't say whether the job is installed and gives no results from it.
- Items that must stay off the page are absent from the page text: no test or check counts, no CI, no AI-written tests, no deduction engine, no "impossible to leak", no "would have helped the village", no false alarms from the reads check, no code names in the body. The 109 is called "flags", and the run is "the first run with the checks in the batch runner". The run on uncommitted code appears only in the hidden sources comment.

## 3. Not checked

- **Whether the June wiring passed the eliminated-player input** (the second finding): needs the e9d30ba diff, and git wasn't available to me.
- **The full comment sentence quoted from the ef43342 diff:** I checked it against the record's quotation, which matches, but not against the diff itself.
- **"The fix the same day" for October:** the record says found and closed on 2026-10-14; the source note says commit 94304a22 is dated 2026-10-15. I couldn't read the commit time to see whether it's the same working session. This is already the brief's open question 3.
- **Whether the "after" game was literally the next game after the fix:** the record calls it "a post-fix live game". The commit order (fix, Vigilante check, wiring, then the post-fix run at c58e5c8d) couldn't be checked without git.
