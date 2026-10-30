<!-- claims review of writeup/evaluation/fair_comparisons/fair_comparisons.skill_2.md by claude (claude-opus-5-5), 2026-10-29T03:08Z -->

## 1. Findings

- **Claim:** "Since then, the two sides of a comparison run in the same time window." (opening). Also "a whole-game comparison run outside the memory driver is interleaved by hand." (A baseline that moved with nothing changed)
  - **Source checked:** map.md "Handle with care" (never "every comparison runs side by side"); experimental_controls/report.md control table and §1 ("has to be interleaved by hand"); memory_system/effectiveness/report.md §2 (the reranked town arm "ran after the baseline, leaving a timing confound").
  - **Verdict:** wrong status
  - **Why:** The opening states the rule as what happens in every comparison. The records show it is enforced only in the memory driver and in turn replays. At least one June arm ran after its baseline once the rule existed. "Is interleaved by hand" also states a habit as a fact; the source says it "has to be".
  - **Suggested scope:** "Since then, the rule has been that both sides run in the same time window", and "has to be interleaved by hand" in the June section.

- **Claim:** "any difference stops the run, so a run resumed on another model, or one that picked up a prompt edit, cannot mix incomparable games into one result." (Recording the set-up, and enforcing it)
  - **Source checked:** `Agents/run_fingerprint.py` `prompt_bundle_hash` (it only hashes the top-level `prompts/*.py`); tracing/fingerprinting/report.md §4.2 "Current coverage gap"; controls §1 on the prompt golden ("which the fingerprint's prompt hash can miss").
  - **Verdict:** overstated
  - **Why:** The hash skips the role cards (each seat's instructions on the ten-player game), the extraction and memory prompts, the output schemas and the deduction lines. An edit there leaves the hash unchanged. If the tree is already marked as having uncommitted edits, a further uncommitted edit changes nothing either. The sources comment leaves this gap off the page, but here it decides whether the guarantee holds.
  - **Suggested scope:** "a run resumed on another model, on another commit, or after an edit to the hashed prompt files", and "a hash of the main prompt files" in the field list.

- **Claim:** "Both sides of every comparison had used the same level, so the comparisons stayed fair." (Checking the experiment that actually ran)
  - **Source checked:** credit/blindspot_fix/experiment_log.md §⑦ (about the memory runs only); factual_errors/experiment_log.md line 281 (a comparison of "minimal" against "medium": 82 → 27 of 267); controls report table (a thinking-budget replay); map.md Handle with care ("limits the settings the memory findings cover").
  - **Verdict:** conflicts with source
  - **Why:** Some comparisons varied the thinking level itself, and model-admission comparisons put different models side by side. "Every comparison" is therefore false. The record that supports the claim covers the memory comparisons only.
  - **Suggested scope:** "Both sides of every memory comparison had used the same level, so those comparisons stayed fair; what narrowed was their scope."

- **Claim:** "decision scores varied about as much between games on the same deal as between games on different deals: almost all the variation came from how a game played out" (Reading a difference against noise)
  - **Source checked:** experimental_controls/drift_surfaces_and_guards.md "Variance constants" (two memory-off runs sharing 8 deals; one score, town vote accuracy; spread 0.249 within a deal against 0.211–0.262 across deals); game report "What pairing turned out to buy".
  - **Verdict:** overstated
  - **Why:** The finding rests on one decision score and 8 deals each played twice. "Decision scores" in the plural and "almost all the variation" generalise beyond that sample. The Level 3 page already words it more narrowly ("a decision score").
  - **Suggested scope:** "On one decision score, town vote accuracy, eight deals played twice varied about as much within a deal as across deals."

- **Claim:** "What made the June comparison fair was the shared time window, not the shared deals." (Reading a difference against noise)
  - **Source checked:** game report "What pairing turned out to buy"; drift_surfaces "Variance constants" ("pairing … never hurt validity … same-epoch was the load-bearing part").
  - **Verdict:** unsupported inference (the source uses the same wording)
  - **Why:** The variance split shows that matching deals added little precision. It says nothing about fairness, and fairness is the other of the page's two problems. The page itself says matching deals "rules out one side getting easier deals", which is a fairness benefit. "The June comparison" can also be misread as the shifted-baseline comparison just described.
  - **Suggested scope:** "Pairing by deal did little for noise; in the June memory experiment, running both sides in the same window was what guarded against the larger risk, a change underneath."

- **Claim:** "That is why the memory tests rested their verdicts on decision scores" (Planning the test before the games)
  - **Source checked:** effectiveness/report.md §2–§3 (the June and v6 tests report win rates prominently, for example "27% → 43%, p = 0.267", and the v6 table is mostly win differences); game report case 2.
  - **Verdict:** overstated
  - **Why:** Only the final memory test fixed a decision score as its main measure. The earlier memory tests reported wins next to decision scores and often led with wins.
  - **Suggested scope:** "That is why the final memory test rested its verdict on a decision score".

- **Claim:** "A matching fingerprint can still hide the wrong experiment, because it records what was configured, not what each side did with it. … It gave memory to every side, and nothing raised an error" (Checking the experiment that actually ran)
  - **Source checked:** `evaluation/src/loop/invariants.py` `assert_arm_factions` docstring (the ON arm "silently ran `all_enabled` … when the experiment intended `town_only`"); `run_fingerprint.py` (no memory field).
  - **Verdict:** wrong mechanism
  - **Why:** The fingerprint holds no memory setting at all. The arm fault was a run configured differently from what was intended, not a gap between what was configured and what was done. That gap describes only the thinking-level fault. "Every side" also reads as both arms, when the record means every faction on the memory-on side.
  - **Suggested scope:** "A fingerprint records only part of the set-up, and only as configured. … The memory-on side gave memory to every faction, wolves and serial killer included, and nothing raised an error."

- **Claim:** "a fingerprint of its set-up: … the model service and region, the player model" (Recording the set-up, and enforcing it; also the exhibit row)
  - **Source checked:** tracing/fingerprinting/report.md §4.3 ("The backend field is wrong for every non-Google model"; the defaults have been Claude since 2026-10-15; the rescue model is not recorded).
  - **Verdict:** wrong mechanism (for current games)
  - **Why:** In current games the "model service" field records a Google service even when a Claude model plays. Only the model name identifies the provider. The description holds for the June and July memory runs, not for today's games.
  - **Suggested scope:** "the player model (whose name carries its provider)"; drop "model service", or say the service field is reliable only for Google models.

- **Claim:** "A difference smaller than such a floor is not evidence of a change." (Reading a difference against noise)
  - **Source checked:** factual_errors/experiment_log.md line 276 (one re-judging of two arms: 82 → 83, 85 → 87); turn report §2 item 1.
  - **Verdict:** overstated (minor)
  - **Why:** The judge floor comes from a single re-judging of two arms. The 8-of-10 → 1-of-10 swing is one case, not a floor for an aggregate total. "Such a floor" treats both as calibrated cutoffs.
  - **Suggested scope:** "A difference within this range is not evidence of a change; the range was measured once, on this test set."

- **Claim:** "Matching does nothing for this." (opening)
  - **Source checked:** controls "When does a comparison need a fresh baseline?"; the page's own "Matching deals reduced this noise very little".
  - **Verdict:** overstated (minor)
  - **Why:** Pairing is in principle a way to reduce noise, and here it was measured to help very little, not nothing. As written, the opening contradicts the later section.
  - **Suggested scope:** "Matching does little for this."

- **Claim:** "the dealt lineup is known before play, so a comparison could adjust for it and remove real variation." (What still depends on a person)
  - **Source checked:** variance_reduction_levers.md Lever 2 correction 2026-10-23.
  - **Verdict:** unsupported
  - **Why:** The audit establishes that the lineup can be adjusted for without bias. It does not establish that the lineup predicts outcomes, so whether any variation would be removed has not been measured.
  - **Suggested scope:** "so a comparison could adjust for it without bias, which may reduce noise; no comparison has done so yet."

## 2. Checked and supported

- The June case: identical prompts, unchanged play code; a 30-game baseline with 20 town wins; 20 deals reused with recorded winners plus 10 new; the town won 1 of the 10 new games; the record's leading explanation was a change in the hosted model, with chance as the alternative. Sources: paired_ab/experiment_log.md lines 5–16 and 61–67; controls "The case that set the rules".
- Paired re-test: 12 → 7, 7 win→loss, 2 loss→win, p = 0.18 (≈ one time in five); size and cause not established. Sources: controls report; paired_ab log re-test note; the verified output on the L3 page.
- No dated version to pin, and responses echoed only the model's name, so a change could not have shown in the records: paired_ab log "Can we pin or detect the drift?".
- Pinning fixes which model sits behind a name, and one provider says the serving system can still change: controls §1 (provider pages checked 2026-10-25).
- The driver runs both sides in one pool, with game ids paired per round: `driver.py` `_run_arms_parallel` and the `pair_base` code nearby.
- Within-run fingerprint stop: the first game's stamp is stored as the reference and both arms are checked after each round (`driver.py` lines 337–345; `invariants.py` `assert_fingerprint_consistent`). Across runs a person compares: controls §1.
- Arm guard: declare the arm or explicitly waive the check before any game (`assert_arm_declared`); read-back after each round, stopping on a mismatch (`assert_arm_factions`); "plausible wrong number, no error" (invariants docstring); held in the one run since with the four town roles (controls §1; deterministic_audits table).
- Thinking level: "minimal" produced no reasoning tokens and the model reasons from "low"; the scope of earlier results narrows; the factual-error set's runner records reasoning tokens; game records keep only the configured level. Sources: controls §4; blindspot_fix §⑦. The page correctly says "no reasoning tokens", not "no reasoning".
- Rubric split moved another label from 74% to 63% on the same messages, and the redesign's old games were re-read: controls §2; llm_judge/experiment_log.md line 177.
- Re-judging moved totals by 1–2 of 267: factual_errors log line 276. One saved vote turn went 8 of 10, then 1 of 10: turn report.
- Same deal is not the same game; the game id fixes the deal; temperature 1.0: controls §1; levers audit Lever 1 correction.
- With 30 games a side: about 36 points of win rate, about 0.18 vote accuracy, about 100 games a side for 0.10. Source: drift_surfaces "Variance constants" (80% power, two independent arms). The game report says "about 35 points"; this does not conflict with the cited source.
- Simulation: built from memory-off scores already played, a planted improvement, found about 1 in 9 at the previous run's size, the test retired before any spend. Sources: v7 report "Testing the test"; controls §3.
- Final test plan: one main measure (the town's decision score per deal), others secondary, a fixed number of games, null or negative results promised as reported, one written change before any game: game report case 2. The result and the related bookkeeping are correctly kept off the page.
- The final memory test was never checked with the simulation: controls "What we would do differently" row 3; game report case 2. This is not on the Handle-with-care list.
- Off-page items: no retracted numbers, missing scripts, untracked records, test-authorship remarks, costs or model names reached the page copy.

## 3. Not checked

- That the turn-replay tool runs all its versions in one session: taken from the controls report; replay code not inspected.
- `tests/engine/test_seedability.py` contents, and the vote-accuracy definition in `compute_metrics.py`: taken from the sources comment and the controls report.
- The 2026-07-19 run's per-round arm records (loop_history), and the final test's written plan and amendment files in `v7/execution_plan/data/`: read through the reports only.
- The provider's statement about serving changes: external page, relying on the controls report's 2026-10-25 check.
- Ownership: the page uses "I" only for rules and practice, which the brief allows. Who wrote the evaluation guards is not recorded, so any later "I built" wording would need the owner.
- Source inconsistency, not a page problem: deterministic_audits case 5 says the mis-set run's "'control' was really a treatment". The code docstring says the memory-on side ran with memory for every faction, and the page follows the code. The audit report's wording may need a fix.
