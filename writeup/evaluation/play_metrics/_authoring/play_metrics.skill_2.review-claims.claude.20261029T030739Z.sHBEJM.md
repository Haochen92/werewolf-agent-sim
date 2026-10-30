<!-- claims review of writeup/evaluation/play_metrics/play_metrics.skill_2.md by claude (claude-opus-5-5), 2026-10-29T03:07Z -->

## 1. Findings

- **Claim:** "The expanded game adds new information roles, a wolf-side role that can block another player's night action, and a third side, the lone killer, who wins alone." (*When the game expanded*)
  - **Source checked:** `evidence/evaluation/metrics/experiment_log.md` Part A (the "3-faction refinement"; the serial killer as a third side on nine seats); report §3 (Wolves and serial killer row); `evidence/credit/report.md` (ten-seat sides).
  - **Verdict:** conflicts with source
  - **Why:** The nine-player game already had a third side that wins alone: the serial killer. The expanded game kept that slot, made it one of two roles (serial killer or necromancer), and added a fourth, neutral side. A reader would take the lone killer as one of the changes that might explain the healer's drop.
  - **Suggested scope:** "…and a fourth, neutral side; the lone-killer seat, held on nine players by the serial killer, can now also be a necromancer."

- **Claim:** "…and with the wolves and the lone killer both attacking at night, one save decides the game less often." (*When the game expanded*, the owner's reading)
  - **Source checked:** log 2026-10-24, "Owner's reading"; report §3 (the serial killer's night kills on nine seats); `evidence/credit/report.md` (the necromancer borrows a dead player's ability from night 2; only the serial killer "attacks every night").
  - **Verdict:** unsupported inference
  - **Why:** The page offers this as a reason the healer's link with winning dropped. But two killers attacking at night was also true of the nine-player game, where the link held, so it cannot explain the change. In necromancer games the lone killer does not attack every night, so the ten-player game can have fewer night attackers, not more. The sources comment notes the nine-player game "also had two killing sides", but the rephrased sentence still presents the two killers as part of the explanation.
  - **Suggested scope:** Keep the reading to what changed (more information roles worth protecting, so whom to guard is a harder guess). Or say plainly that two night killers existed on both games and so do not explain the difference.

- **Claim:** "The expanded game deals ten seats from twelve roles, so each role is absent from some games, leaving too few games per role to choose scores by correlation." (*Checking that good moves win games*)
  - **Source checked:** `writeup/game_design_orchestration/evidence_design/evidence_design.md` l.312 ("Eight seats are the same every game"); log 2026-10-24 (the vigilante "dealt in all 78 games"); data README (the healer is scored in 75 of 78 games).
  - **Verdict:** wrong mechanism
  - **Why:** Only two seats change between games: the lone killer and the neutral seat. The six town roles and both wolves are dealt every game. The thin data per score comes from those two seats, from rare actions (vigilante shots in 19 games, investigator finds in 20) and from few evil-side wins (17 and 15). It does not come from every role going missing. The report's own sentence is loose in the same way, and the earlier claims review of `play_metrics.skill.md` flagged this same wording.
  - **Suggested scope:** "Two seats change between games, several new roles act rarely and the evil sides win few games, which leaves too few games per score to choose scores by correlation."

- **Claim:** "A per-game score is a rate: good outcomes divided by the chances a player had." (*Grading a decision by the rules*)
  - **Source checked:** `Agents/ten_seat_metrics.py`; the data README score list.
  - **Verdict:** overstated
  - **Why:** Several of the 32 checked scores are plain counts with no denominator: `mislynches`, `sentinel_watches_naming_evil`, `chanteuse_blocks_real`, `sk_power_roles_killed`, `vigilante_evil_shots`. That includes the page's own "+0.12" example in the next-to-last section, which is the Sentinel count. The report says "a rate divides by the chances", not that every score is a rate.
  - **Suggested scope:** "Where a score depends on how long a player was in the game, it is a rate: good outcomes divided by the chances the player had."

- **Claim:** "Graded decisions carry less of that luck… Averaging many such grades gives each game a steadier number…" followed by the owner's grading table and "A per-game score is a rate…" (*Why grade decisions instead of wins*; *Grading a decision by the rules*)
  - **Source checked:** report §6 (two separate scorers: per-game metrics in `ten_seat_metrics.py`, per-decision grades in `grading.py`); log B1.
  - **Verdict:** unclear (needs the owner)
  - **Why:** In these sections a reader would take the per-game scores to be averages of the table's good/neutral/bad grades. In fact they come from a separate scorer that counts outcomes, and the table's grades are used by memory's credit. The final section's "tested per-game scores, not the table" fixes this only at the end. The check's results do not validate the table, and the early wording blurs that.
  - **Suggested scope:** Add one clause where the table is introduced saying that the per-game scores the check tests are computed separately from the same kinds of outcomes, not by averaging the table's grades.

- **Claim:** "…several scores read zero in the first 28 ten-player games even when the event happened." (*When the game expanded*)
  - **Source checked:** report §6 ("every one of the 28 ten-seat balance games"); `compute_metrics.py` comment as quoted in log B1; report §4 (41 phase-3 games on 2026-10-09 and 10).
  - **Verdict:** conflicts with source (minor)
  - **Why:** The source names 28 ten-seat balance games. They are not identified as the first 28, and the 41 phase-3 games from the same days were the earliest ten-seat records.
  - **Suggested scope:** "…in all 28 ten-player balance games scored before the rewrite…"

- **Claim:** "That rate did not go with town wins (−0.09 for finds of any evil player, −0.14 for wolves)… What did was… +0.40 over 180 games." (*Checking that good moves win games*)
  - **Source checked:** log Part A, L2 (−0.09 and −0.14 at n=50; "N=180 confirms the dead floor"; find-to-lynch +0.396); report §3.
  - **Verdict:** overstated (minor: mixed samples)
  - **Why:** The two failing numbers come from the 50 June games and the passing one from the 180 July games. The page sets them side by side with only one sample size, so it reads as one comparison on one sample. The conclusion still holds, because the find rates also stayed near zero at 180.
  - **Suggested scope:** Give the 50-game sample for the find rates, or say they stayed near zero over the 180 games too.

- **Claim:** "Code applies that table exactly…" (*What the checks do not establish*)
  - **Source checked:** report §6 "How far checked"; log B1 (the table's rows are pinned only by AI-written, unaudited tests).
  - **Verdict:** overstated (minor)
  - **Why:** Deterministic code applies the table the same way every time. That it matches the table "exactly" rests on tests that are unaudited, and those tests stay off the page.
  - **Suggested scope:** "Code applies that table to every decision the same way every time, but…"

- **Claim:** "One new role's score correlated +0.12, with an interval from about −0.10 to +0.33." (*When a result is too weak to read*)
  - **Source checked:** `summary.json` (−0.106 to 0.333); report §4 table and log (−0.11); report §2 (−0.10).
  - **Verdict:** conflicts with source (trivial)
  - **Why:** The report's §2 rounding disagrees with its own §4 and with `summary.json`; "about" covers it, but the two pages may disagree.
  - **Suggested scope:** "−0.11 to +0.33".

## 2. Checked and supported

- The 35-point win-rate difference detectable at 30 games per version (80% power, nine players): `evaluation_scopes/game/experiment_log.md` detectable-effect table.
- Sources of luck in a win, and the town vote counting as good even when the town loses: report §1–§2.
- One score and one result per game is the unit of the check: `ten_seat_win_check.py` `check_score`, `within_batch_correlation`.
- The owner ruled a good/neutral/bad table for every kind of turn: report §2; log B1 (plan §9.6). The first-person "I ruled" is supported.
- No model call; same result every time: report header and §2.
- Healer table rows: `ten_seat_metrics.py` l.87–93. Protections count only if they went ahead (not role-blocked). The town-save rate divides by protections that went ahead. `_safe_div` gives no score rather than zero. The "saved" verdict is `night.py` l.200–206. A blocked night counts neither way: log 2026-10-24.
- A save is still graded good: `grading.py` `_grade_healer` (a saved townsperson is graded positive).
- Weighting by certainty was rejected because the situation summary existed only in memory-on games: report §1.
- The check method (correlation with its own side's win; memory-off reading on both games; within-batch reading on ten seats only): report §2; data README; runner.
- Lynch share +0.65 over 50 games and over the 30 with memory off, holding on 180: report §3; log Part A L2.
- 48 candidates tried, 11 kept; rules first on ten seats: report §2 "How the approach changed".
- Scorer rewrite to night records and sides from the role registry: report §6; log B1.
- 78 games, 49 with memory off, mostly different models: data README.
- Table values +0.49 (+0.30 to +0.64), within batch +0.55, memory off +0.48; healer +0.36 over 50 games (the same metric, `healer_town_save_rate`, in `proxy_win_monotonicity.md` l.26); healer −0.03 (−0.26 to +0.20, 75 games): data README; log; report §4.
- "Chance an unlikely explanation for the drop": my own Fisher-z recomputation agrees (z ≈ 2.17, p ≈ 0.03). It is stated in words only; it is not in the evidence record (see section 3).
- Healer records (220 = 79 + 141; 56 of 79; 1.07 against 1.03; 3.25 against 2.48; 23): log 2026-10-24.
- The reading is labelled as the owner's and not tested, with the cross-model caveat: log "Owner's reading"; report §3 against §4.
- About 190 games to see 0.2; evil sides need more; a score fails only when its interval rules out a worthwhile size: report §2. Wolves won 17 and the lone killer 15: report §4.
- Vigilante: 19 games, 16 of 22 shots on evil players, +0.29 (−0.19 to +0.66): log 2026-10-24.
- Information roles: 60% of named evil players later voted out; +0.19 (p = 0.12, 66 games) and +0.09: log; report §4.
- Rule-fixed rare scores may report on their own decision but not decide a comparison: report §2, July row.
- 32 scores (`summary.json` has 32 entries); chance passes; carried-over rows well past that; new-role directions not written in advance: report §4; log 2026-10-24.
- The table as a whole is untested against winning: report §6. Next steps: report "What we would do differently", items 3–4.
- Off-page check: the uncommitted runner, the tests, the 119-game first count, `VALIDATED_ON_TEN_SEAT_METRICS` and memory results do not appear in the page copy. "Memory can raise both…" is a guard, not a claim that memory helps.

## 3. Not checked

- **The direct comparison of the healer correlations:** it exists only in `metric_transfer.md` (computed for that page, owner-approved), not in `evidence/`. I recomputed the 50-game comparison arithmetic but did not rerun it against the data.
- **"Averaging many such grades gives each game a steadier number than its win or loss":** the report states this, but I found no measured comparison of variance in the cited sources. I did not open `experimental_controls/drift_surfaces_and_guards.md` to confirm one exists.
- **"Its saves were still counted correctly"** on ten players: the only record is a hand check against one pilot game (report §6). I did not look at that check.
