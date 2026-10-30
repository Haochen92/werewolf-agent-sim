<!-- claims review of writeup/evaluation/fair_comparisons/fair_comparisons.skill.md by claude (claude-opus-5-5), 2026-10-29T01:58Z -->

## 1. Findings

- **Claim:** "The reanalysis did not gain precision by pairing (the noise section shows pairing bought little); it used the comparison the design actually contained" (*A baseline that shifted with nothing changed*)
  - **Source checked:** `writeup/evaluation/fair_comparisons/paired_baseline.md` "Why the readings differ"; `evidence/evaluation/experimental_controls/drift_surfaces_and_guards.md` "Variance constants" (lines 123–138).
  - **Verdict:** conflicts with source.
  - **Why:** The finding that pairing bought little was measured on the share of town votes cast against an evil player, not on wins. The Level 3 page says outright that it "did not establish how much pairing improves precision for win outcomes". The sources comment cites that same section as support, so it was misread. This page states as fact something its own Level 3 page says is unknown.
  - **Suggested scope:** "How much pairing helps for wins was not measured; the reanalysis's value is that it used the comparison the design actually contained, instead of treating repeated deals as unrelated games."

- **Claim:** "three versions on 20 deals became two on 30 … The main measure and the reading of a null stayed as signed." (*Deciding the test before the games*)
  - **Source checked:** `evidence/memory_system/v7/report.md` "The pre-registration" (lines 195–203).
  - **Verdict:** overstated (leaves out a change).
  - **Why:** The signed main comparison was the final memory against the memory after the first round. The amendment replaced it with the final memory against no memory, and the report says this "changes the question". The change came after the store-building games' memory-on and memory-off scores existed. Listing only what stayed the same lets a reader assume the main comparison stayed the same too, in the section whose point is that the reading was fixed in advance.
  - **Suggested scope:** Add: "The main comparison changed with it, from the final store against the first-round store to the final store against no memory."

- **Claim:** "When the rubric … was revised to split one label into two, the share … moved from 74% to 63%, on the same messages. The older games were therefore re-read with the revised rubric alongside the new ones." (*Giving both sides the same start and the same judge*)
  - **Source checked:** `evidence/gameplay/discussion_evidence.md` §6.1 (lines 451–465); controls report §2.
  - **Verdict:** wrong mechanism (order of events).
  - **Why:** In the record, both sides were re-judged because the rubric changed, and the 74% → 63% move showed up during that re-judging. "Therefore" says the shift came first and caused the re-read, but the shift could only be seen by re-reading.
  - **Suggested scope:** "When the rubric … was revised to split one label into two, both sides were re-read with it, and on the same older messages the share labelled as citing something a player had said moved from 74% to 63%."

- **Claim:** "a standard deviation of 0.25 within a deal, against 0.21–0.26 across deals. Nearly all the variation came from how a game played out." (*Reading a difference against noise*)
  - **Source checked:** `drift_surfaces_and_guards.md` "Variance constants" (two back-to-back memory-off runs, 10 games and 8 shared deals); `evaluation_scopes/game/experiment_log.md` lines 40–51.
  - **Verdict:** overstated (sample not stated).
  - **Why:** The page leans on this result twice: pairing bought little, and the shared time window is what made the June comparison fair. It rests on 8 deals played twice, which a reader cannot tell from the page.
  - **Suggested scope:** Add the sample next to the numbers: "measured on two memory-off runs that shared 8 deals".

- **Claim:** "and checked how large a test needed to be before paying for it" (*opening*)
  - **Source checked:** controls report "Quick view" ("The power gate … Nine-seat trend test only; the paired design that replaced it was never simulated") and "What we would do differently" row 3.
  - **Verdict:** overstated.
  - **Why:** The opening states it as a general practice. In fact one planned test was sized this way, and the design that was actually run was never sized. Section 6 does give that scope, but the opening sets the reader's expectation.
  - **Suggested scope:** "…and, for the learning loop's planned test, checked by simulation whether it was large enough before paying for it."

- **Claim:** Exhibit row "Player thinking level | `minimal` | Recorded correctly on every game, but produced no reasoning tokens" (*Checking that the run is the one declared*)
  - **Source checked:** `evidence/credit/blindspot_fix/experiment_log.md` §⑦; `v7_compound_town5/run_meta.json`.
  - **Verdict:** unsupported as a direct observation (minor).
  - **Why:** The zero-token result comes from an October probe on the test set. These games' records hold only the configured level, which the page itself says two paragraphs later. The row states as observed something that was inferred.
  - **Suggested scope:** "Recorded correctly on every game; a later probe showed this level gives this model no reasoning tokens (see below)."

## 2. Checked and supported

- Comparisons are about 30 games a side or a few dozen turns, at temperature 1.0; two kinds of variability need different remedies (controls "Why controls", "When does a comparison need a fresh baseline?").
- A game id fixes its deal and a test checks it; the same deal is not the same game; a pair is two independent plays of one start (controls §1; game report "How a whole-game comparison is set up").
- Code scores outcomes where it can, with no judge (controls §2).
- Every experiment game record carries the fingerprint: commit, a hash of the main prompt files, model settings (fingerprinting report §1–§2: `run_batch` records and capture manifests; served games excluded, which the "experiment" wording covers).
- The fingerprint check stops a loop run on a mismatch; both arms are compared against round 1's reference (`driver.py` 333–345; `invariants.py` `assert_fingerprint_consistent`); across runs a person compares (fingerprinting §7).
- The June run meant to be town-only gave memory to every role and produced a plausible wrong number with no error (`invariants.py` `assert_arm_factions` docstring).
- Declare or waive before any game; read back after each round; stop on a mismatch (`assert_arm_declared`, `driver.py` 257, 326). Both checks live only in `run_loop`.
- Exhibit values: commit a010dc68…, no uncommitted changes, hash fcb194406952618f, gemini-3.1-flash-lite, minimal (`run_meta.json`); `expect_factions` town_only, `unchecked_arm` false, `tells` true (`config.json`); the four town roles read back in rounds 1–4 (`loop_history.json`). The caption's note on the tell list matches v7 report "The pre-registration".
- Thinking-level probe: "minimal" gave no reasoning tokens and reasoning started at "low". Every memory-experiment game ran at minimal, with both sides at the same level, so the scope narrows. A test-set runner now records tokens; game records do not (blindspot §⑦; controls §4).
- June case: byte-identical play prompts; play code unchanged since b9756960; 1 of 10 against 20 of 30; drift as the leading suspect with chance as the alternative; no dated version and the response echoes the name; the 20 deals re-played (paired_ab log lines 5–38, 61–67).
- Two-comparisons table: Fisher p = 0.0028; 12 → 7, 7 win-to-loss / 2 loss-to-win / 11 unchanged, p = 0.18. The table is labelled as two comparisons on different games, and the 10 fresh deals are named as the strongest sign (paired_baseline.md; controls "The case that set the rules").
- "Changed the claim, not the rule" (controls revision note; paired_baseline.md).
- Same-window enforcement: the loop runs both arms in one pool, paired by id, and `run_batch.py` does not alternate (`driver.py` `_run_arms_parallel`; controls §1). The final test started each deal's two games together (previous review, endpoint log).
- Noise: 1–2 of 267 on re-judging (factual_errors report step 4); 8 of 10 then 1 of 10 on one vote prompt; the two habits used only in some screens (turn report §2 item 1).
- Detectable gaps: about 36 points of win rate, 0.18 vote share, about 100 games a side for 0.10. The criterion is recorded (80% power at p < 0.05, two independent arms of 30; `drift_surfaces_and_guards.md` line 136), so the brief's open question 7 can be answered.
- In June the shared window, not pairing, made the comparison fair; pairing was not re-measured on ten seats (game report lines 71–79; drift_surfaces line 131).
- Decision score definition, −1 to +1, after day 1 (v7 report "The score").
- Simulation: built from 15 real memory-off games with no model calls; 24 games (4 × 6); +0.15 is the middle of the plan's estimate; caught about 1 time in 9; the trend test was dropped (v7 report lines 92–156). "The next paid run used a different design" is true under either reading of the records.
- Final test: signed before any game; one main measure compared deal by deal, with the others secondary; a fixed number of games; the wording for a null set in advance. The change came after the learning games and before any test game, with its two recorded reasons. The replacement design was never sized (v7 report lines 167–203).
- Closing: strong where code enforces, weaker where a person must remember; the four next steps (controls "Bottom line", "next time" rows 1–4).
- Handle-with-care list: none of it reached the page. The canary is not named, the exhibit is a clean-tree record, there is no missing-script or git-ignored-data mention, no "pre-registration" wording, and the thinking-level finding is not grouped with the other two faults.

## 3. Not checked

- **"A turn replay runs its versions in one session":** this rests on the controls report and the map. I did not find the replay runner's code that does it.
- **Whether the 20 reused results are 20 of the original 30 games:** the seed set took them from `extraction_v5_0.jsonl` and was not reconciled with the original 30's records. The counts are consistent with it (12 of the 20 were town wins, against 20 of the 30), but that is not proof.
- **Whether the declare-or-waive gate existed at commit a010dc68 (the July run):** I could not check git history in this session. The exhibit row only says the roles were declared, which `config.json` supports either way.
- **First-person ownership ("I matched…, had code check…"):** the records I read don't say who wrote `evaluation/src/loop/`. The claims are about design decisions, not who typed the code.
- **Using the ten-player lineup to reduce noise:** I did not read `variance_reduction_levers.md`. The page presents it as a next step, not as something done.
