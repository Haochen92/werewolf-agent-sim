<!-- claims review of writeup/evaluation/play_metrics/play_metrics.skill.md by claude (claude-opus-5-5), 2026-10-29T01:57Z -->

I found one claim that contradicts its source and three smaller problems. Nothing from the Handle-with-care list has reached the page copy, and no file was edited.

## 1. Findings

**1. The vigilante is given as an example of a new role**
- **Claim:** "Most scores for the new roles cannot be read either way yet. The vigilante, a town role that may shoot a player at night, fired in only 19 of the 78 games." (When the game expanded)
- **Source checked:** `evidence/evaluation/metrics/report.md` §3 ("How sure we are": the vigilante's correct-shot score went from +0.43 to +0.18 across the two nine-player batches); `data/ten_seat_win_check/README.md` (`vigilante_correct_shot_rate` has June direction "+", not "new"); `evidence/metrics/candidate_ledger.md` (vigilante re-test at N=180).
- **Verdict:** conflicts with source.
- **Why:** The vigilante was already in the nine-player game, and the June check recorded a direction for its score. Putting it under "the new roles" also suggests the next paragraph covers it ("expected directions were also not written down"), but it does not.
- **Suggested scope:** Introduce it as a rare role, not a new one, for example "Rare actions stay hard to read even for an existing role: the vigilante … fired in only 19 of the 78 games." Or use a new role (Sentinel +0.12, −0.11 to +0.33) as the example.

**2. Section 1 assumes the decision score needs fewer games, and departs from its cited source**
- **Claim:** "how many fewer games it needs than the win depends on how strongly a given change moves it, which has not been measured" (What decision scores buy)
- **Source checked:** `evidence/evaluation/experimental_controls/report.md` §3 ("What pairing bought"); `evidence/evaluation/metrics/report.md` §1; brief, open question 8.
- **Verdict:** unclear (needs the owner).
- **Why:** "How many fewer" takes for granted that it needs fewer. The brief's own reasoning (OQ8) says the two detectable sizes (0.18 in vote accuracy, 36 points in win rate) are the same fraction of each measure's spread, so the record does not show that. That reasoning also depends on a spread figure ("within one deal 0.25") whose metric the source does not name. Separately, the Evidence list cites report §1, which says the opposite ("an effect shows at a game count the project can afford"). Reader and source now disagree with nothing on the page or in the record to settle it, and the owner has not ruled on OQ8.
- **Suggested scope:** "Whether it needs fewer games than the win for a given change has not been measured." Settle OQ8 so that report §1 and the page agree.

**3. "Each score is exact" covers one score that does not read the engine's record**
- **Claim:** "Code reads these moves from the game record, the engine's own account of every vote, night action and result. … so each score is exact and needs no model call." (Scoring decisions by the rules)
- **Source checked:** `evidence/evaluation/metrics/report.md` §2 ("What goes in": one supporting score reads the agents' own accusation tags, written by the playing model, "so it sits a step lower"); `data/ten_seat_win_check/README.md` (`town_accusation_precision` is one of the 32 scores).
- **Verdict:** overstated (minor).
- **Why:** At least one of the 32 scores counts labels the playing model wrote, not moves the engine recorded. It is an exact count of those labels, not of what happened in the game. The page's main scores (eliminations, healer, night kills) are not affected.
- **Suggested scope:** "The scores the page relies on read only what the engine recorded …", or add "one supporting score also reads the players' own accusation labels".

**4. The healer comparison assumes the nine- and ten-player rates measure the same thing**
- **Claim:** The table row "Healer's saves of townspeople per protection that went ahead | +0.36 (50 games) | −0.03 …", and "A direct comparison of the correlations … makes chance alone an unlikely explanation for the drop." (When the game expanded; A good move that decides fewer games)
- **Source checked:** `evidence/metrics/candidate_ledger.md` (`healer_town_save_rate`, nine-player denominator "healer action-nights"); `Agents/ten_seat_metrics.py:87-93` (denominator: protections that "went ahead", blocked ones excluded); `metric_transfer.md` (p ≈ 0.03 and ≈ 0.001).
- **Verdict:** unclear (needs the owner).
- **Why:** The nine-player figure divides by action nights, and the row label gives the ten-player definition. The brief (N4) argues the two probably match because the nine-player game had no blocker, but nobody has traced that. The direct comparison depends on the two being the same measure. Against the 50-game estimate it rests on p ≈ 0.03 for a score singled out after 32 were examined, so the +0.40-at-180 comparison (p ≈ 0.001) does most of the work.
- **Suggested scope:** Keep the claim, but get the owner to confirm the two definitions match, or label the nine-player cell "per protection night".

**5. "Making saves did not" rests on two averages**
- **Claim:** "Survival went with winning; making saves, counted per game, did not." (A good move that decides fewer games)
- **Source checked:** `experiment_log.md` 2026-10-24, "The healer" (1.07 vs 1.03 saves a game; protection nights +0.29 as a correlation).
- **Verdict:** overstated (minor).
- **Why:** Survival has a correlation on record. Saves per game have only the two group averages, with no correlation or test, so the two halves of the sentence are not supported equally.
- **Suggested scope:** "…; saves per game were about the same in won and lost games."

## 2. Checked and supported

- Opening: the elimination score kept its link on both games, the healer's rate lost it, and the nine- and ten-player games used different models. Sources: report §3 vs §4; data README batch table.
- About 36 percentage points at 30 games a side, estimated on June nine-player data; "at 30 games a side it too shows only large changes". Source: experimental_controls report §3 ("only large effects… about 0.18 in vote accuracy, or 36 points").
- The game is the unit, one value per score per game. Source: `evaluation/experiments/ten_seat_win_check.py` (`score_game`, `check_score`).
- Town vote good on an evil player, bad on a townsperson. Source: `grading.py:335-338` (`vote_grade`; a vote on a neutral is also bad, and the page does not deny it).
- The save mechanism, the rate's denominator (protections that went ahead), a blocked night counting neither way, and no protection giving no score rather than zero. Sources: `ten_seat_metrics.py:37-38, 62-63, 87-93`; log 2026-10-24.
- Luck after the decision is removed but luck inside the decision stays. Source: report §2.
- The check correlates each score with its own side's win; the memory-off reading exists; a weak link may not show at 50 games. Sources: report §2 (about 190 games for 0.2); `ten_seat_win_check.py`.
- Nine-player elimination score: +0.65 over 50 games, +0.64 on the 30 memory-off games, +0.65 over 180. Sources: `evidence/metrics/proxy_win_monotonicity.md:18`; `candidate_ledger.md:48-49`. The page's +0.64 is the primary figure; report §3 rounds it to "+0.65 in both readings".
- The 180 games are a separate batch (the v6ab audit) from the June 50. Source: `candidate_ledger.md:9, 19`.
- The nine-player investigator learns a role: `role_revealed` in `metrics_audit/scheduler_bias_log.md:112`. Its find rate showed no link in either check (−0.09/−0.14, then about 0 at 180), while find-to-lynch was +0.40 at 180 games. Source: `candidate_ledger.md:80, 153-157`.
- The scorer rewrite is told as caught and fixed (old fields read zero; rewritten to read night records and sides). Source: report §6.
- 78 games, 49 memory off, 32 scores, three readings, the within-batch definition and 95% intervals. Sources: data README; `summary.json` (32 entries); `ten_seat_win_check.py:268-292, 341`.
- Table values +0.49 (+0.30 to +0.64), +0.55, +0.48; healer −0.03 (−0.26 to +0.20, 75 games). Source: data README rows 42 and 50.
- Town players killed at night (−0.55/−0.55/−0.43) and the lone killer voted out (+0.38/+0.40/+0.43) kept direction in all three readings. Sources: data README; `ten_seat_metrics.py:132-139`, which counts every town player killed at night by an evil attacker, so "town players" is right on ten seats.
- Vigilante 19 games, +0.29 (−0.19 to +0.66); new-role directions not fixed beforehand; Chanteuse real blocks +0.31. Source: log 2026-10-24.
- Healer records: 1.07/1.03 saves, 3.25/2.48 protection nights, +0.29, 220 = 79 + 141, 56 of 79 with no death, 36 died later, 23 with another death that night. Source: log 2026-10-24; the group means reconcile to 79 and 220.
- "My reading" is labelled as untested, and the cross-model caveat is kept. Sources: log 2026-10-24 (owner's reading); report §3 vs §4.
- "A table I set out": report §2 and §6 ("the owner's table"). Grades feed memory credit and a saved townsperson is graded good: `grading.py:295-301`.
- No score is marked validated for the ten-player game. Source: `Agents/compute_metrics.py:729` (`VALIDATED_ON_TEN_SEAT_METRICS = frozenset()`).
- Limits: 32 scores so one or two may pass by chance; the carried-over rows pass by more and match their nine-player direction; the grade table is untested against winning. Sources: report §4 and §6.
- The next-version changes match report "What we would do differently" items 1–4.
- Off-page items: none in the page copy. AI-written tests, the uncommitted runner and the morning-of-check registry switch appear only in the sources comment.

## 3. Not checked

- "There are no matching nine-player counts to compare them with" (the healer's protections and saves). This is a claim that something is absent; I did not search every nine-player audit log for protection counts.
- The p-values behind "chance alone an unlikely explanation" (≈0.03, ≈0.001). They exist only on `metric_transfer.md`, computed for that page, and I did not recompute them. See finding 4 for the assumption they rest on.
- Whether the 0.25 per-game spread in experimental_controls §3 belongs to a decision score or to the win. The source does not say, so finding 2 is left with the owner.
- That "most ten-player games" used models not used on the nine-player game. The ten-player models are recorded, but I did not trace the exact nine-player model names beyond "Gemini models of the time".
