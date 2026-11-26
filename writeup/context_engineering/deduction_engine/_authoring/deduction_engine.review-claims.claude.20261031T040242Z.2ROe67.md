<!-- claims review of writeup/context_engineering/deduction_engine/deduction_engine.md by claude (opus), 2026-10-31T04:02Z -->

I found eight problems; the four that matter most are in sections 1 and 5 of the page. The biggest: the page presents "cost, not necessity" as why the engine was chosen, but the evidence for "not necessity" came about two weeks after the engine was built. And the results table describes two of its three rows as engine on against engine off when they weren't. Nothing was edited.

## 1. Findings

- **Claim:** "For that kind of failure I chose to work out a selected set of consequences in code… The reason is cost, not necessity… The same model at a high thinking setting makes the healer's connection on its own, and so do two larger models." (*What the engine is responsible for*)
  - **Source checked:** `experiment_log.md` §8 Question and Result 2 (dated 2026-10-30); §2 Question; §4 Setup and table; catalogue header (built 2026-10-16 to 10-19).
  - **Verdict:** unsupported inference
  - **Why:** The high-thinking and larger-model results come from a 2026-10-30 run. That is after the engine was built, and §8 says "no larger model had been tried on a player turn" before then. At the time, the reasons on record were narrower: Sonnet was ruled out on cost (§2), and medium thinking left this turn at 3 of 10 (§4, enforced mode). So the page gives a later finding, from one turn, as the reason for the choice. It also states it generally ("for that kind of failure… makes").
  - **Suggested scope:** Separate the two times: at the time, a larger model was ruled out on cost and medium thinking left this turn at 3 of 10. A later check on the same turn found high thinking or a larger model makes the step alone, so on this turn the engine is the cheaper route, not the only one.

- **Claim:** "The levers tried before it, repairing the inputs, rewording the prompt and raising the thinking effort, each helped somewhere…, and none removed this failure at the setting the live game runs on" (*What the engine is responsible for*)
  - **Source checked:** `experiment_log.md` §4 "The design", §5, §6 Setup, §8 Result 2 scope note; `report.md` §1.
  - **Verdict:** unsupported inference
  - **Why:** Only thinking effort was tried on this turn before the engine (§4, which is also the injection run). Repairing the input was never tried alone: the record's false "you learned nothing tonight" clause was replaced only together with the engine's line, and §8 says the run "does not isolate the one certain line against a neutral record". The prompt rewrite (§6) came after the engine. "None removed this failure" suggests all three were tried on it and failed.
  - **Suggested scope:** Keep "each helped elsewhere"; for this failure, say only that medium thinking left it at 3 of 10, and that the record's misleading clause was replaced only together with the engine's line.

- **Claim:** "Each screen replays frozen turns with the engine's lines and without them" and the column "With the engine's lines, against without" (*What changed in replayed decisions*, rows 2 and 3)
  - **Source checked:** `gameplay/data/visit_wording_ab/README.md` "Arm C"; `roles/report.md` decision 11.
  - **Verdict:** wrong mechanism (a comparison mislabelled)
  - **Why:** Only row 1 compares engine on against engine off. Row 2's arms are "A (visit, no rows)" against "C (visit + A56/E19)": two added lines plus a fix, on top of the existing engine. The tag snapshot couldn't be inspected because shell access was off; the arm names imply the rest of the engine was on. Row 3's arms all had "the deduction blocks re-rendered by the engine"; only the covers line, in its fixed version, differs. A reader will take all three rows as whole-engine effects.
  - **Suggested scope:** Name what each row adds: row 1 the engine against engine off; row 2 two Sentinel/Trailseer lines (with a fix) added to the engine; row 3 the covers line added, with the card and the other lines the same in both arms.

- **Claim:** "In each row the seat receiving the lines moved in the intended direction, within those limits" (*What changed in replayed decisions*, closing paragraph, applied to row 3)
  - **Source checked:** `roles/report.md` decision 11 table ("Card, covers off" against "Covers, fixed").
  - **Verdict:** overstated
  - **Why:** In the same arm, claims a careful town could show false rose from 0 of 36 to 3 of 44; the source puts these down to seats departing from the line. Claims contradicting a reported sighting fell from 4 to 1. Reporting only claims and denials, then saying "each row moved in the intended direction", leaves out the one measure that went the other way. Cover quality is the point of that row.
  - **Suggested scope:** Either add "claims a careful town could show false rose from 0 to 3, seats departing from the line", or narrow the sentence to "claims and denials moved in the intended direction".

- **Claim:** "On this turn the engine stood in for the slower or costlier configuration" (*What changed in replayed decisions*)
  - **Source checked:** `experiment_log.md` §8 Results 1–2 and "What it shows" ("the engine buys most of the gap").
  - **Verdict:** overstated
  - **Why:** With the engine, the read was 8 of 10 and 7 of 10 spoke. Opus reached 10 and 10, and Sonnet 9 and 10. "Stood in for" suggests the results were equal; the log says "most of the gap".
  - **Suggested scope:** "On this turn the engine closed most of the gap to the slower or costlier configurations."

- **Claim:** "the second costs money, a game's ten seats at about $2.30 against $0.12, roughly twenty times" (*What the engine is responsible for*)
  - **Source checked:** `experiment_log.md` §8 Result 2 cost bullet and §2 Question.
  - **Verdict:** overstated (the figure covers only part of what it is applied to)
  - **Why:** $2.30 is the Sonnet seat cost only. "The second" refers to both larger models, and Opus is priced higher.
  - **Suggested scope:** "the cheaper of the two larger models costs about $2.30 a game against $0.12".

- **Claim:** "every note recorded the Chanteuse's visit once the line was present" (*How strongly can the conclusion be stated?*) and "only this one line added" (row 1's limits)
  - **Source checked:** `experiment_log.md` §4 "The design" (the injected text); catalogue AC1 "As built" (current wording, owner's ruling 2026-10-18).
  - **Verdict:** conflicts with source (minor)
  - **Why:** The 2026-10-16 replay used an earlier wording: "Only the Chanteuse can roleblock in this game, and blocking is a visit, so the Chanteuse, a wolf, visited you that night." It also replaced the record's line rather than being added beside it. The page's "the line" and "this one line" point to the current printed line quoted just above.
  - **Suggested scope:** "an earlier wording of the first line, replacing the original night record".

- **Claim:** "The card's: 'Plan your cover before you need it. Your worked-out lines list the roles you can claim without contradicting the public record.'" (*What the engine may know…*)
  - **Source checked:** `Agents/prompts/roles/pack.py:30-33`.
  - **Verdict:** conflicts with source (minor)
  - **Why:** The card's sentence continues ", and a role no living player holds, or one whose holder died with its role hidden, cannot be counter-claimed truthfully. Choose one…". The page ends the quoted sentence with a full stop as if it were complete.
  - **Suggested scope:** End the quote with "…public record…" (an ellipsis).

- **Claim:** "my part was the requirement, the grading rule, the acceptance cases from real failures and the experiments" (*Scope and remaining questions*)
  - **Source checked:** memory `project-code-authorship-split.md` (the owner's claim is "framing, requirements, experiment choices and reviewed judgements"); `experiment_log.md` §6 ("The owner and Claude drafted"), §8 (subagent harness, owner-asked runs).
  - **Verdict:** unclear (needs the owner)
  - **Why:** "The experiments" reads as running them. The record supports choosing and directing them; the runs and judging were done by AI agents. This is still the brief's open question 1.
  - **Suggested scope:** "the choice of experiments" (or "experiment design"), pending the owner's confirmation.

## 2. Checked and supported

- The healer's failure, its three passed turns, and "likely the chanteuse" reached only in a night-2 private note: `experiment_log.md` §4 "The failure"; case register R1.
- The seat's view (announcements, dead roster, read-out wills, cast counts, own records, pack for a wolf, claims kept as claims; no votes field; never the hidden roles): `Agents/schemas/deduction.py` SeatView; `report.md` §3; catalogue §0.
- "Unless a wolf concealed it": catalogue §0.1 (the Illusionist is a wolf).
- The trait table is "declared by hand and tested against the game engine's own behaviour": `Agents/schemas/role_traits.py` module docstring (declared there; `test_role_traits.py` resolves real nights).
- Only the Chanteuse blocks in this cast, and a block is a visit: catalogue §0.1, AC1.
- Solver: candidate sets for players and concealed bodies, the starting sets, the A/B/C illustration, the four kinds of rule, termination, traceability, no result on contradiction: `report.md` §3.
- The two healer lines are verbatim, with their placement (night record; seat block, player_7's entry), and come from the own-results and joins stages, not the solver: catalogue AC1 "As built"; `report.md` §2–§3.
- The acceptance-case definition (must say / must not say; four cases): catalogue "Acceptance cases".
- Eight kinds of line: `report.md` §3 level table.
- The three grades, their definitions, and the alternatives listed under a named claim: catalogue §0 (R9); `report.md` §2.
- "player_7 is the Chanteuse" must not be printed because a second visitor is possible: catalogue AC1 "Must not say"; log §4.
- The conditional example line is an engine output: `tests/engine/deduction/test_acceptance.py:93`, `test_conditionals.py:58`; catalogue AC2 (rendered verbatim on a discussion turn).
- Conditionals come from rerunning the solver with the claim assumed and stay out of the baseline sets: `report.md` §3 "Keep assumptions separate".
- Notes recorded the visit 10 of 10 with the injected line against 0 of 10 without, enforced mode, 2026-10-16: log §4.
- The hidden-information test checks independence on tested cases, not correctness: `test_candidates.py:367` plus the matching tests in the joins, conditionals, comparisons, explanations, covers, evil-seat and own-results test files; `report.md` §4 table.
- Correctness is checked separately against actual roles and a brute-force oracle: `report.md` §4.
- Consequences, not advice; the card gives the advice; the cover line's wording: `report.md` §3 and its level table; catalogue R11; roles decision 11.
- "A wolf, or a lone killer with no pack" covers the evil-seat roles (Serial Killer and Necromancer are both lone killers): catalogue §0.1; `report.md` §3.
- Row 1 numbers and their scope (8 of 10 against 2 of 10 read; 7 against 3 spoke; live mode; engine off restores the original record): log §8 Results 1–2 and the scope note.
- Row 2 numbers, unit and limits (6 of 40 → 2 of 40; 17 of 55 unchanged; 8 report turns and 11 replies × 5; the gain on b77857/cb1f34; the bundled fix; downstream effect not shown): `visit_wording_ab/README.md` Arm C.
- Row 3 numbers and the judge caveat (36 → 44 claims, 4 → 0 denials, 41 turns × 2, different judges): `roles/report.md` decision 11.
- Model and thinking comparison (2 of 10; 9 of 10 at 17.4 s against 6.3 s; 9 and 10 of 10; all engine off): log §8 Result 2.
- The bundled whole-game comparison (cards, two engine changes, everything else between builds; wolves 3 of 8 against 0): `roles/report.md` "The games: a bundle, eight pairs".
- Scope (the standard roles and limits; no lines outside them; the second-blocker example), the explanations line that never fired in 278 turns, no town-side whole-game A/B, no post-engine error rate: `report.md` §3 "Modes", §4, §5; catalogue §0 "Configuration scope".
- Engine and solver written by an AI assistant: memory `project-code-authorship-split.md`. Test authorship is not mentioned (follows the handle-with-care list).
- Off-page items: no model family names, no ~3% or 0.14%, no p-values, no "proved".

## 3. Not checked

- The $2.30 Sonnet per-game figure. It is lifted from log §2 and §8, and its derivation is not in those sections. The $0.12 Haiku figure dates from the cached setup of mid-October; whether it still holds in live output mode, which uses more reasoning tokens a call (§9: about 1,440 against 852 output tokens a vote), was not checked.
- "Supplies the step at the live setting's speed": turn latency with the engine on in live mode was not recorded (the brief notes this). Only the engine's own runtime, in milliseconds, is measured.
- Whether row 2's arm A had the rest of the engine on at tag `1371b5e5`. I inferred it from the README's "no rows" naming because shell access was off and I couldn't inspect the tag; the finding on row 2's label rests on that inference.
- *The roleblocked healer* and the Evaluation code-checks page, both linked: the first is planned and not yet written; the second was not read.
