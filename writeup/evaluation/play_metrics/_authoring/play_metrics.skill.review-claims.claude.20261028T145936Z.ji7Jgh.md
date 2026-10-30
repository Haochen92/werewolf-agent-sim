<!-- claims review of writeup/evaluation/play_metrics/play_metrics.skill.md by claude (claude-opus-5-5), 2026-10-28T14:59Z -->

The page holds up on most of what it claims. I found two claims that conflict with the record, two whose scope needs tightening, and several smaller wording fixes.

## 1. Findings

- **Claim:** "Ten seats are dealt from twelve roles, so every role is missing from some games, leaving too few games per role to choose scores that way." (*Does a good move go with winning?*)
  - **Source checked:** `Agents/schemas/roles.py:88-109` (`FIXED_SEATS`, `ALL_LINEUPS`); log 2026-10-24, "The vigilante" ("Dealt in all 78 games"); report §2, "How the approach changed".
  - **Verdict:** conflicts with source.
  - **Why:** Eight of the ten seats are dealt in every game. Only the lone-killer seat (serial killer or necromancer) and the neutral seat (Speculator or Fortune Teller) are drawn. The report says only "too few games per role"; "every role is missing from some games" is the page's own addition, and it is false.
  - **Suggested scope:** "Ten seats are dealt from twelve roles: two seats switch between pairs of roles, and several new roles act rarely, which leaves too few games per score to choose scores that way."

- **Claim:** "I considered a richer alternative, making every agent write down what it believed about each player and scoring those beliefs, and turned it down. Requiring that output would change how the agents play…" (*Grading a decision by the rules*)
  - **Source checked:** report §1, "Two other designs were tried and turned down (June 2026)"; report §6, "Read Brier score" ("Before each decision a seat writes a *read* of every other player… The Brier score measures how well the committed reads matched").
  - **Verdict:** unclear (needs the owner).
  - **Why:** The rejection is in the June record. But from July the agents did write a read of every other player before each decision, and the project scores those reads with a Brier score (report §6; log B2 "nine-seat July 2026"). Without a date and scope, a reader who sees the reads elsewhere will think the page contradicts the system. The page also offers "change how the agents play" as the reason, which the later design appears to have accepted.
  - **Suggested scope:** Date it and limit it to its use, e.g. "In June I turned down scoring the agents' stated beliefs as the measure for comparing versions…". Either note that reads were added later and scored separately for a different question, or remove the paragraph.

- **Claim:** "Code grades each vote and night action against the true roles… and turns those grades into scores for each game." (Opening)
  - **Source checked:** report §6 ("Two scorers, both code": per-game metrics in `Agents/ten_seat_metrics.py`, per-decision grades in `Agents/memory/consolidation/grading.py`); code of both.
  - **Verdict:** wrong mechanism.
  - **Why:** The per-game scores are computed straight from the night and day records by `ten_seat_metrics.py`, not from the grades in `grading.py`. The two are separate scorers. The page's own closing says the check "tested the per-game scores, not the table that grades every turn", which contradicts "turns those grades into scores". The nine-player scores the June check tested came before the grade table, which was built on 2026-10-13.
  - **Suggested scope:** "Code reads each vote and night action from the record, judges it against the true roles by the game's rules, and computes scores for each game, such as the share of lynches that removed a threat."

- **Claim:** "The core town scores carried over in this sample, so they remain the scores a comparison can lean on." (*What the scores can support*). Section 1 also uses "the share of town votes cast against a threat" as its example score.
  - **Source checked:** report Quick view ("Town vote accuracy… 🟡 on ten seats, weak in two flash-lite batches"); report §4 "Carries over" rows; data README (`town_vote_accuracy` memory off +0.24, p = 0.095).
  - **Verdict:** overstated.
  - **Why:** The page's only worked example of a decision score is the town's vote share. On ten seats that score is not in the report's "carries over" group: +0.24 with memory off, and weak in two batches. "Core town scores" leaves the reader to assume it carried over. The rows that did carry over are the lynch scores, power roles lost at night and the lone killer lynched.
  - **Suggested scope:** Name them: "The town's lynch scores and its losses at night carried over in this sample." If the vote share stays as section 1's example, add that it was weaker on ten players.

- **Claim:** "In these games, what mattered was not the find but turning it into a vote." (*Does a good move go with winning?*)
  - **Source checked:** report §3 and §5.1; log Part A L2 (`investigator_find_to_lynch_rate` +0.396); Level 2 prompt, CAUSAL AND EVIDENTIAL PRECISION.
  - **Verdict:** overstated.
  - **Why:** These are correlations. A find that is later lynched is partly the town's winning step itself (removing a threat), so it sits close to the outcome. "What mattered" claims a cause the check cannot show, and the page's own caveat ("associations, not causal effects") comes only later.
  - **Suggested scope:** "In these games, what went with winning was not the find but its conversion into a lynch."

- **Claim:** "A score for a game divides by the chances a player had." (*Grading a decision by the rules*)
  - **Source checked:** report §2 ("**A rate** divides by the chances a player had"); data README (counts such as `power_roles_killed_by_evil`, `mislynches`, `sigilist_hits`, `sentinel_watches_naming_evil`).
  - **Verdict:** overstated.
  - **Why:** Only the rate scores divide by chances. Several scores, including the "players with night abilities killed at night" count the page cites later, are plain counts.
  - **Suggested scope:** "A rate score divides by the chances a player had."

- **Claim:** "…so in the first 28 ten-player games they read zero even when the event happened." (*When the game expanded*)
  - **Source checked:** `Agents/compute_metrics.py:575-579` ("every one of 28 ten-seat balance games, 2026-10-11"); report §4 / log 2026-10-24 (41 phase-3 games on 2026-10-09 and 10).
  - **Verdict:** conflicts with source (minor).
  - **Why:** The source says 28 *balance* games, not the *first* 28. At least 41 ten-player games came before the port.
  - **Suggested scope:** "in the 28 ten-player balance games checked, they read zero even when the event happened."

- **Claim:** "The record names three changes for the next version of the game: …" (*What the scores can support*)
  - **Source checked:** report, "What we would do differently next time" (five rows).
  - **Verdict:** overstated (minor).
  - **Why:** The record names five changes, and the page picks items 1, 2 and 4. It also drops item 3, "run the check against winning on the first batch", which the brief had planned to include.
  - **Suggested scope:** "Among the changes the record names for the next version: …"

- **Claim:** "The town, made up of ordinary villagers and players with night abilities, tries to vote out hidden evil players: a pack of wolves, and a lone killer… Both kill at night." (*Grading a decision by the rules*)
  - **Source checked:** `Agents/schemas/roles.py:76-95` (villager retired with the nine-seat deal; a neutral seat in every game; necromancer's action is "borrow").
  - **Verdict:** wrong mechanism (minor).
  - **Why:** The ten-player game deals no ordinary villagers, and it has a neutral seat the page never mentions; the town vote grade treats a vote on that seat as bad. The necromancer kills only through a borrowed body. As a description of both games together, the cast is off for the game the healer section depends on.
  - **Suggested scope:** Say the town is "players with abilities (and, on the original game, ordinary villagers)". Mention that a neutral seat plays for its own goal.

- **Claim:** "With 30 games for each version, only a difference of about 36 percentage points in win rate would reliably show… a change of about 0.18 in that share would reliably show." (*Why the win alone is not enough*)
  - **Source checked:** `evidence/evaluation/experimental_controls/report.md`, "What pairing bought".
  - **Verdict:** unclear (needs the owner); low priority.
  - **Why:** The figures match the source. But they were sized on the June nine-player games, and the page gives them as general facts with no sample context. EVIDENCE DISCIPLINE asks for that context near the number.
  - **Suggested scope:** Add "estimated on the original nine-player games", or rely on the Fair comparisons link if the owner thinks that is enough.

## 2. Checked and supported

- The win carries the luck of the deal and of everyone's play, and a modest effect needs more games than the project could afford (report §1).
- The game is the unit; each game gives one value per score (`ten_seat_win_check.py` description in the data README: one score against one win per game).
- The healer save rate is town saves divided by protections that went ahead. A roleblocked night counts neither way, and no protection gives no score rather than zero (`Agents/ten_seat_metrics.py:62-63, 87-93`, `_safe_div` returns None). The illustrative table is consistent with this.
- A save is a protected player who was attacked and lived (log 2026-10-24, "The healer").
- Grading removes what happened afterwards but not the luck inside a decision (report §2).
- A town vote on a threat is graded good and on a townsperson bad (`grading.py` `vote_grade`). A healer save of a townsperson is graded positive (`_grade_healer`).
- The check correlates each game's score with its own side's win, and is also read on memory-off games (report §2; log Part A L1).
- Nine players: lynch score +0.65 over 50 games and +0.64 over the 30 memory-off games (`evidence/metrics/proxy_win_monotonicity.md`), and it held at 180 (report §3).
- The investigator's find rate showed no link (−0.09 and −0.14 at n = 44; about zero at 180), while find-to-lynch was +0.40 at 180 (log Part A L2; report §3).
- 48 candidate scores were tried and 11 kept. Credit needed a grade for every decision from game one; the owner's table puts rules first (report §2, "How the approach changed"). "I set out a table" matches "the owner's table".
- The scorers were rewritten to read the full night record and take sides from the role registry (log B1; `ten_seat_metrics.py` docstring and `_side`).
- 78 games, 49 memory off; three readings; within batch means each batch's mean is taken out of both score and win; 95% intervals (data README; report §4).
- Table values: +0.49 (+0.30 to +0.64), +0.55, +0.48. Healer −0.03 (−0.26 to +0.20) over 75 games and +0.36 over 50 on nine players (data README; `proxy_win_monotonicity.md:26`).
- Power roles lost at night carry over under all three readings: −0.55, −0.55, −0.43 (data README). In ten-seat code it counts town players killed by evil at night, and every ten-seat town role has a night ability.
- Vigilante: fired in 19 of 78 games, +0.29 (−0.19 to +0.66); "untested, not failed" (log 2026-10-24, the vigilante entry and the owner's reading).
- New-role directions were not written down in advance, and the Chanteuse real-block score of +0.31 is exploratory (log 2026-10-24; data README).
- Healer records: 1.07 / 1.03 saves a game; 3.25 / 2.48 protection nights; 220 = 79 + 141; 56 saves with no death that night; 36 saved players died later; 23 saves with another death that night (log 2026-10-24).
- "My reading" is labelled as untested and matches the owner's reading in the log. The "two killers" clause is correctly avoided.
- The direct comparison makes chance an unlikely explanation but cannot give a cause, and it crosses game version and models (`metric_transfer.md:132-135`; report §3 Gemini vs §4 mostly Haiku).
- No score is marked validated (`compute_metrics.py:729`, `VALIDATED_ON_TEN_SEAT_METRICS = frozenset()`); that is the owner's decision (report §4).
- 32 scores examined, so one or two could pass by chance; the grade table as a whole is untested against winning (report §4, §6).
- Nothing from the Handle-with-care list or other off-page bookkeeping reached the page copy: no test authorship, no uncommitted runner, no registry-switch timing.

## 3. Not checked

- **"So I measured decisions instead" (first person on the nine-player score design):** the records attribute the grade table and the method reading to the owner, but not who designed the June per-game scores. The authorship memory covers orchestration, the solver and tests, not the metrics.
- **The healer direct-comparison p-values:** these exist only on `metric_transfer.md`, computed for that page; no evidence-folder record or script to recompute from. I relied on the brief's note that the owner approved them there.
- **"held on the later 180" for the lynch score specifically:** the report says "All held again on the 180 July games" for the town row. I did not open the July audit logs in `evidence/metrics/metrics_audit/` for the per-score 180-game value.
- **Whether the nine-player `healer_town_save_rate` denominator matches the ten-player one exactly:** nine-player code divides by `healer_action_nights`. With no blocker in that game this is probably the same thing, but I did not trace how that count was built.
