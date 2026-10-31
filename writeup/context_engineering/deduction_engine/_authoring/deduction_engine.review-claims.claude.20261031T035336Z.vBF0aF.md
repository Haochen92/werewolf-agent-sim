<!-- claims review of writeup/context_engineering/deduction_engine/deduction_engine.md by claude (opus), 2026-10-31T03:53Z -->

I checked the page's consequential claims against the deduction report, experiment log and catalogue, the Sentinel and cover records, the counter-claim screen, and the code (`seat_view.py`, the hidden-role tests, `pack.py`). I edited no files. There are 15 findings below; the first two are the most important because they affect the page's central argument.

## 1. Findings

1. **Claim:** "The engine is a substitute for that slower or costlier configuration on a step of this kind, not a general gain." (What changed in replayed decisions)
   - **Source checked:** `evidence/gameplay/deduction/experiment_log.md` §8, "What it shows" and "Not established".
   - **Verdict:** overstated
   - **Why:** All of the model and thinking comparisons come from one frozen turn with 10 samples per setting. The log lists "anything beyond this one turn" as not established, so "a step of this kind" stretches one case into a category.
   - **Suggested scope:** "On this turn, the engine stood in for the slower or costlier configuration; whether that holds for other missed steps is untested."

2. **Claim:** "an injected line is taken up almost every time … It would be a false premise in every game where the line's conditions hold" (How strongly can the conclusion be stated?)
   - **Source checked:** experiment_log.md §4 (10 of 10 against 0 of 10 notes; enforced output mode, 2026-10-16); report.md §2 uses the same wording.
   - **Verdict:** unsupported inference
   - **Why:** The evidence is 10 samples of one line on one turn, in the enforced mode. The source repeats the general wording, but one replay can't give a general uptake rate. The step from "taken up" to "in every game" also goes further than the sample allows.
   - **Suggested scope:** "On the one turn replayed, every note recorded the line's conclusion and none did without it. A wrong certain line could be taken up the same way, as a false premise the player reads as its own result."

3. **Claim:** "An earlier replay of the same turn in the enforced output mode found the line taken up every time and no sample speaking" (results table, row 1, limits cell)
   - **Source checked:** experiment_log.md §4 (0 of 10 spoke, 2026-10-16) and §8 Result 1 (the 2026-10-30 enforced-mode re-run with the engine on: 5 of 10 spoke); the outline's "Handle with care".
   - **Verdict:** off-page item
   - **Why:** The outline says the silence result must carry both its mode and its date; the page gives the mode but not the date. Beside the live-mode row, it also suggests the output mode explains the silence. But the 2026-10-30 enforced-mode re-run with the full engine had 5 of 10 samples speaking, so the mode alone doesn't account for it.
   - **Suggested scope:** Date it ("a 2026-10-16 replay, with the schema enforced and only the one line injected") and leave the explanation to the Level 3, or note that the 2026-10-30 enforced re-run spoke in 5 of 10.

4. **Claim:** "The only whole-game comparison bundled the engine's cover facts with revised evil cards … the two changes cannot be separated" (What changed in replayed decisions)
   - **Source checked:** `evidence/gameplay/roles/report.md`, "The games: a bundle, eight pairs".
   - **Verdict:** conflicts with source
   - **Why:** The two sets of games differ by the card text, *two* engine changes (implied role claims and the covers line) and everything else committed between the two builds. "The two changes" makes the bundle look smaller than it was.
   - **Suggested scope:** "…bundled revised evil cards with two engine changes and everything else committed between the builds; the engine's share cannot be separated."

5. **Claim:** "a summary of what each rival claimant had said moved one case's votes toward the named player in a small screen, the kind of steering the engine must not do" (What the engine may know…)
   - **Source checked:** `evidence/gameplay/data/counter_claim_votes/README.md`; report.md §5.
   - **Verdict:** conflicts with source
   - **Why:** The line named both claimants. The source records it as a true fact, dropped because it didn't move votes toward the truth: 12/16 → 12/17 pooled, and in its own case real-claimant votes rose from 4 to 7. The likely cause given is name order (the real claimant was named first), not advice. Calling it "steering" puts a factual line under "advice", which the record doesn't support.
   - **Suggested scope:** "One further true line was tried and dropped: a summary of what each rival claimant had said did not improve votes in a small screen and, in its own case, moved votes toward the real claimant."

6. **Claim:** "One table of role traits answers those questions, checked against the game engine's own behaviour rather than written by hand." (From visible facts to a conclusion)
   - **Source checked:** report.md §3, "Translate game mechanics into constraints", and §4.
   - **Verdict:** wrong mechanism
   - **Why:** The table is written by hand: a new role "is declared there". It is then checked against resolved nights. "Rather than written by hand" suggests it is generated from the engine.
   - **Suggested scope:** "One hand-written table of role traits answers those questions, and a test checks it against the game engine's behaviour on resolved nights."

7. **Claim:** "never connecting the block to the one role that could have made it" (What the engine is responsible for)
   - **Source checked:** experiment_log.md §4 "The failure"; catalogue AC1 "What the seat did".
   - **Verdict:** overstated
   - **Why:** The healer drew no conclusion in its three day-2 turns. It did reach "likely the chanteuse" in a private note on night 2, but never said it.
   - **Suggested scope:** "…and, through all three of its day-2 turns, not connecting the block to the one role that could have made it (it got there only in a private note that night and never said so)."

8. **Claim:** "Most of the engine's lines come from a solver that keeps, for each player … the set of roles it could still hold." (From visible facts to a conclusion)
   - **Source checked:** report.md §3 (eight levels; the solver is "central"); `data/deduction_block_census/census.json` (no breakdown of lines by level).
   - **Verdict:** unsupported
   - **Why:** No record counts lines by source. Several levels (own results, public events, joins, comparisons, evil-seat facts) are separate rules, and the healer's own two lines don't use the solver.
   - **Suggested scope:** "At the engine's centre is a solver that keeps…"

9. **Claim:** "the public record (the announcements, the dead with the roles revealed at death, the votes and the dealt cast)" (The seat's view)
   - **Source checked:** `Agents/deduction/seat_view.py` and `Agents/schemas/deduction.py` (`SeatView`, `PublicRecord`); catalogue §0.
   - **Verdict:** conflicts with source
   - **Why:** The page describes current behaviour. The built seat view has no votes field: it holds the cast counts, dead roster, announcements, read-out wills, living players and claims. "Votes" comes from the catalogue's specification, written before the build. Being voted out appears only as a death in the roster.
   - **Suggested scope:** "the public record (the announcements, the dead with the roles revealed at death, the read-out wills and the dealt cast)".

10. **Claim:** "And a true report does not establish the reporter's role: a wolf can report a visit that really happened." given as one of "two things" that stop naming player_7 (How strongly can the conclusion be stated?)
    - **Source checked:** catalogue AC1 "Must not say" (the only reason given: a second visitor); experiment_log.md §4 (the trailseer-honesty correction); report.md §2 repeats the pairing.
    - **Verdict:** unsupported inference
    - **Why:** Whether the trailseer is honest bears on whether player_3 is the Trailseer, not on whether player_7 is the Chanteuse. The line is conditional because the visit rests on claims, and it lists alternatives because a second visitor is possible. The acceptance case gives only the second-visitor reason.
    - **Suggested scope:** "The visit rests on two claims, so the line is conditional on them; and another visiting role could also have come, so it lists both branches. (Separately, a true report does not establish the reporter's role.)"

11. **Claim:** "A conditional line comes from running the solver again with the named claim assumed true" (How strongly can the conclusion be stated?)
    - **Source checked:** report.md §3, the "Joins" and "Conditionals" levels; catalogue Table F, row F2.
    - **Verdict:** overstated
    - **Why:** Some claim-qualified lines are joins (F2), which set the seat's own result against a claim, not solver reruns. The healer's own second line is one of these.
    - **Suggested scope:** "Some conditional lines come from running the solver again…; others join the seat's own result with a named claim, as the healer's second line does."

12. **Claim:** "In each case the lines changed what the first speaker did." (What changed in replayed decisions)
    - **Source checked:** roles/report.md decision 11 and "Limits"; visit_wording_ab README, Arm C.
    - **Verdict:** overstated
    - **Why:** The cover row is exploratory: its arms were labelled by different judges, and differences "can reflect judging as well as behaviour". The Sentinel row is 6 against 2 of 40 in a small screen.
    - **Suggested scope:** "In each case the first speaker's output moved in the intended direction; the cover counts are exploratory."

13. **Claim:** "A Sentinel misreading its own watch | Report lines relying on a false rule fell from 6 of 40 to 2 of 40" (results table, row 2)
    - **Source checked:** `evidence/gameplay/data/visit_wording_ab/README.md`, "Cases" and "Arm C".
    - **Verdict:** overstated
    - **Why:** The 40 report samples cover 8 report turns from several games, including Trailseer reports, not just the Sentinel's. Arm C also bundled a bug fix in `joins/reports.py` with the two new rows.
    - **Suggested scope:** In the limits cell: "8 report turns (watch and follow reports) and 11 replies, 5 samples each; the new lines came with a fix that let one follow reach the engine."

14. **Claim:** "game continuation (a hidden body cannot have held a role that would have ended the game earlier)" (Narrowing the possible roles)
    - **Source checked:** report.md §3, rule 4.
    - **Verdict:** overstated (minor)
    - **Why:** The rule excludes *combinations* of hidden-body roles that would have ended the game at an earlier win check. It doesn't rule out single roles taken one at a time.
    - **Suggested scope:** "game continuation (hidden bodies cannot have held roles that, together, would have ended the game earlier)".

15. **Claim:** "The engine, solver included, was written by an AI coding assistant; my part was the requirement, the grading rule, the acceptance cases from real failures and the experiments." (Scope and remaining questions)
    - **Source checked:** the brief's open question 1; the owner's authorship record (2026-10-26: "framing, requirements, experiment choices and reviewed judgements").
    - **Verdict:** unclear (needs the owner)
    - **Why:** The owner hasn't confirmed the sentence. "The experiments" is broader than the recorded "experiment choices": several runs and judgements were carried out by AI subagents.
    - **Suggested scope:** Owner to confirm; for example "…my part was the requirement, the grading rule, the acceptance cases from real failures, and the design of the experiments."

## 2. Checked and supported
- The failure class: premises present, first step missed (report.md §1 cause table; experiment_log §4).
- The healer's view: the night-1 record (tried to protect player_5, roleblocked), the trailseer's report and player_7's admission (catalogue AC1 "Knew").
- The engine never reads hidden roles, and claims arrive as claims (`seat_view.py` module docstring; `SeatView.claims`; catalogue §0).
- Only the Chanteuse blocks in this cast, and a block is a visit (experiment_log §4; AC1).
- The traits named (blockable, night-immune, reads Suspicious, visits under own name) (report.md §3).
- Candidate sets start from unaccounted copies; the A/B/C illustration and its reading; repeat until a pass removes nothing; stops because sets are finite and only shrink; each removal keeps its rule and events (report.md §3).
- Both printed lines verbatim, and their placement in the night record and under player_7's entry (report.md §2; catalogue AC1 "As built").
- The acceptance-case definition (must say / must not say; four cases) and "eight levels" (catalogue "Acceptance cases"; report.md §3).
- The three grades and their definitions, grade in the wording, partial conclusions not printed, "never state as absolute" (catalogue §0).
- The conditional example line (report.md §2); the assumption stays out of the baseline sets (report.md §3 "Keep assumptions separate").
- A contradiction gives no candidate result (report.md §3).
- The hidden-role test as described: hold the visible information fixed, vary hidden roles, require identical output. Such tests exist across levels (`test_candidates.py`, `test_joins.py`, `test_conditionals.py`, `test_comparisons.py`, `test_covers.py`, `test_evil_seat.py`, `test_own_results.py`); the scope "independence on cases tested, not correctness" is kept.
- Correctness checked against actual roles and a search over every role assignment the seat's information allows (report.md §4).
- The cover line text (report.md §3 level table) and the card sentence (`Agents/prompts/roles/pack.py:30–31`, quoted faithfully as an excerpt).
- Row 1: 8 of 10 against 2 of 10 read, 7 against 3 spoke; live mode; "without" restores the original night record, so one line is not isolated (experiment_log §8 Results 1–2 and scope note).
- Row 2: 6 → 2 of 40, replies 17 of 55 unchanged, 19 turns × 5, downstream effect unresolved (visit_wording_ab README, Arm C).
- Row 3: claims 36 → 44, denials 4 → 0, 41 pressured turns × 2, different judges (roles/report.md decision 11).
- Limits: low setting without the engine 2 of 10; high 9 of 10 at 17.4 s against 6.3 s (≈2.8×); larger models 9 and 10 of 10; $2.30 against $0.12, so "roughly twenty times" holds (experiment_log §8, §2).
- Wolves 3 of 8 against 0; not attributable (roles/report.md).
- Out-of-set games get no lines, with the second-blocker example (report.md §3 "Modes"; `deduction_mode_for` in `seat_view.py`).
- One level never fired in 278 turns; no town-side whole-game A/B and no post-engine error rate (report.md §5).
- "Read" gloss: the turn asks for a structured read per living player, with a suspected role (`Agents/schemas/lineup_output.py:84`).
- Off-page items: no test authorship, no "proved", no ~3% rate, no model family names, no commit or uncommitted-tree bookkeeping on the page.

## 3. Not checked
- "A conclusion computed once in code supplies the step at the live setting's speed": no turn time was recorded for the live-mode run with the engine on (§8 gives times only with the engine off). The engine's own runtime (≈0.45 ms solve, 10.5 ms block build) suggests little added time, but turn latency with the engine on wasn't measured.
- That pages 1 and 3 tell the earlier levers' results, and that the chapter 1, chapter 2, chapter 6 and Evaluation code-checks links point to pages that exist and say what the page says they do. Those pages weren't opened.
- Whether "the standard twelve roles" matches `Agents/deduction/verified.py`'s verified set exactly; I relied on the catalogue's §0.1 "The twelve roles" heading and the report's "Modes" paragraph.
- Whether the live-mode uptake of the injected line into notes (rather than reads) was measured; §8 records reads and speech only, so the page's uptake claim rests on the enforced-mode run alone (see finding 2).
