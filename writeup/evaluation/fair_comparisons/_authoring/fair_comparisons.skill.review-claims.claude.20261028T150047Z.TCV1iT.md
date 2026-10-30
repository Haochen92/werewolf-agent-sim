<!-- claims review of writeup/evaluation/fair_comparisons/fair_comparisons.skill.md by claude (claude-opus-5-5), 2026-10-28T15:00Z -->

## 1. Findings

- **Claim:** "The plan changed once, from three versions on 20 deals to two on 30, in writing and before any game." Also "fixed how it would be read before any game was played" (*Deciding the test before the games*).
  **Source checked:** `evidence/memory_system/v7/report.md` "The pre-registration" (lines 193–203); `v7/execution_plan/data/v7_endpoint_ab/PREREG_AMENDMENT.md`; `v7_compound_town5/loop_history.json`.
  **Verdict:** conflicts with source.
  **Why:** The plan was signed before any game. The change came on 2026-07-20, "after the learning games but before any test game", and the amendment file says "BEFORE any endpoint game". By then the build run's 80 games had been played, and `loop_history.json` holds a memory-on and a memory-off town score for each round. "Before any game" hides the one point where results could have been seen. The game report's case 2 uses the same wrong wording, and the page copied it.
  **Suggested scope:** "The plan changed once, in writing, after the learning games but before any game of the test itself (three versions on 20 deals became two on 30)."

- **Claim:** "The memory experiments' loop runs both sides' games in one shared pool, paired by deal, so neither side runs after the other." (*Keeping both sides in one time window*)
  **Source checked:** `evaluation/src/loop/driver.py` `_run_arms_parallel` (lines 170–192) and `_game_tasks`; `v7_compound_town5/config.json` (`game_concurrency: 3`).
  **Verdict:** wrong mechanism.
  **Why:** The pool is given `on_tasks + off_tasks` in that order, and the thread pool runs them first come, first served. With 3 workers and 10 games a side, all ten memory-on games start before the first memory-off game. Within each round, the off side mostly runs after the on side and overlaps only at the end. Both sides do fall in the same round's block of a few hours, so the same-window claim holds at that scale. The final memory test used a different runner, which started each deal's two games together (`v7_endpoint_ab.log`: "[start] off g0[start] on g0").
  **Suggested scope:** "The loop runs each round's games for both sides as one block in a shared pool, paired by deal, so both sides fall in the same few hours; the final memory test started each deal's two games together."

- **Claim:** The two-readings table, with its caption "Compared deal by deal, the drop could be chance", and "The reanalysis changed the claim…" (*A baseline that shifted with nothing changed*)
  **Source checked:** `writeup/evaluation/fair_comparisons/paired_baseline.md` "Why the readings differ"; `evaluation/experiments/june_baseline_shift_check.py`.
  **Verdict:** overstated (two comparisons merged).
  **Why:** The rows are not two readings of the same games. Row 1 is the 10 new deals; row 2 is the 20 shared deals. So the move from about 3 in 1,000 to about 18 in 100 comes from both a different set of games and pairing. The reanalysis never re-tests the 1-of-10 result. The Level 3 page says the fresh games "remain the strongest evidence of a drop" and that the reanalysis "does not separate the two effects". A reader of this page will assume pairing alone undid the striking result.
  **Suggested scope:** Add one sentence: "The two readings use different games: the paired reading covers the 20 shared deals and does not re-test the 10 new ones, which remain the strongest sign of a drop."

- **Claim:** Exhibit rows "Roles declared to have memory | town roles only" and "Roles that had memory … healer, investigator, vigilante, villager" (*Checking that the run is the one declared*)
  **Source checked:** `v7_compound_town5/config.json` (`"tells": true`); `driver.py` lines 319–322 (`WW_TELL_BOOK` set for every game on the memory side); `Agents/memory/tell_book.py` ("every seat may read it"); `v7/report.md` "The pre-registration" (tells "shown to every seat in the memory games, wolves included").
  **Verdict:** overstated / unclear (needs the owner).
  **Why:** The guard reads only the per-role lesson switch (`memory_config`). In this run, every seat on the memory side, wolves and serial killer included, also read the tell list the loop had learned. The section has just described the June slip of giving memory to the wolves, so "town roles only" invites the reader to assume no evil seat got any learned material.
  **Suggested scope:** Label the rows as the per-role lesson switch, and add a clause that a shared list of public tells was shown to every seat on the memory side by design.

- **Claim:** "…and had code check that each run used the set-up it declared." Also "Since then, both sides of a comparison run in the same time window." (*opening*)
  **Source checked:** `experimental_controls/report.md`, the table "Which controls apply to which comparison", "Quick view" and §1; `writeup/map.md` "Handle with care".
  **Verdict:** overstated.
  **Why:** The memory guard covers only memory runs in the loop driver. The fingerprint stops only loop runs. Same-window running is enforced by code only in the loop and in replays; `run_batch.py` relies on habit. The map rules out wording that says every comparison runs side by side. The opening states both as general practice; the scope only arrives several sections later.
  **Suggested scope:** "…and, in the memory experiments' runs, had code check the set-up it declared"; "Since then, the rule has been that both sides run in the same time window."

- **Claim:** "Two habits followed: running the unchanged version twice, and shuffling all versions into one schedule." (*Reading a difference against noise*)
  **Source checked:** `evidence/evaluation/evaluation_scopes/turn/report.md` §2 item 1 and "What we would do differently", row 1.
  **Verdict:** wrong status.
  **Why:** That report says these habits were "done in the persona line and the AC2 2×2; most screens ran each arm once". It lists building them into every screen as a change for next time.
  **Suggested scope:** "Two habits answer it, used in some later screens: running the unchanged version twice, and shuffling all versions into one schedule."

- **Claim:** "The test was dropped before any money was spent on it." (*Deciding the test before the games*)
  **Source checked:** `v7/report.md` "Testing the test before paying for it" (line 100: "The June runs had been read this way") and line 156 ("before any paid run used it"); `evidence/credit/discussion_tagger/experiment_log.md` §6 (the paid June run).
  **Verdict:** conflicts with source (the records disagree).
  **Why:** The previous paid run, 24 games over six rounds and about $15, had already been read with this trend test. What the simulation prevented was another paid run built on it. The controls report uses the same wording as the page.
  **Suggested scope:** "The test was dropped before another paid run relied on it."

- **Claim:** "Every game record carries a runtime fingerprint: the code version, the prompt files and the model settings" and the exhibit row "Hash of the prompt files" (*Checking that the run is the one declared*)
  **Source checked:** `evidence/tracing/fingerprinting/report.md` §1 "What it does not guarantee", §2 and §4.2.
  **Verdict:** overstated.
  **Why:** Games played on the site carry no fingerprint. The prompt hash covers only the top-level prompt modules, and since the ten-player game the role cards sit outside it. A reader would conclude that any prompt edit would show up. For a run, a committed change does still move the commit field.
  **Suggested scope:** "Every experiment game record carries…, including a hash of the main prompt files."

- **Claim:** "The memory runs have a second guard." Also, in the closing, "in memory runs the roles with memory are declared before the run and read back during it."
  **Source checked:** `experimental_controls/report.md` "Quick view" ("Memory runs in the loop driver only"); `driver.py` `run_loop`.
  **Verdict:** overstated.
  **Why:** The guard lives only in the learning-loop driver. Memory runs launched through `run_batch.py`, such as the June paired A/B, had no such check.
  **Suggested scope:** "The learning-loop memory runs have a second guard."

- **Claim:** "Every game until then had run at 'minimal'" and "The turn-replay runner now records reasoning tokens for each sample." (*Checking that the run is the one declared*)
  **Source checked:** `evidence/credit/blindspot_fix/experiment_log.md` §⑦ (checked run by run for the memory runs only); `experimental_controls/report.md` §4.
  **Verdict:** overstated (minor).
  **Why:** The run-by-run check covered memory-experiment games. The token recording is in the factual-error test set's runner (`3e05e8a7`), not every replay tool.
  **Suggested scope:** "Every memory-experiment game until then…"; "The factual-error test set's replay runner now records…"

## 2. Checked and supported

- Comparisons are about 30 games a side or a few dozen turns, at temperature 1.0 (controls "Why controls").
- Two kinds of variability, each needing its own remedy (controls "When does a comparison need a fresh baseline?").
- A game id fixes the deal and a test checks it; the same deal is not the same game; a pair is two plays of one start (controls §1; game report "How a whole-game comparison is set up").
- A replay rebuilds the turn from saved state (controls §1).
- One judge for both sides in one run; the rubric split moved another label from 74% to 63% on the same messages; the old games were re-read (controls §2; `evidence/gameplay/discussion_evidence.md` lines 461–465).
- Code scores outcomes where it can (controls §2).
- A fingerprint change stops a loop run, and across runs a person compares (`invariants.py` `assert_fingerprint_consistent`; `driver.py` lines 333–343).
- The June memory slip: all roles had memory when town only was intended, giving a plausible wrong number with no error (`invariants.py` `assert_arm_factions` docstring; discussion_tagger log §6, dated 2026-06-22).
- Declare or waive before the start; read back after each round and stop on a mismatch (`assert_arm_declared`, `driver.py` lines 257 and 323–326).
- Exhibit values match `run_meta.json`: commit a010dc68…, no uncommitted changes, hash fcb194406952618f, gemini-3.1-flash-lite, temperature 1.0, thinking level minimal. `config.json` has `expect_factions` town_only and `unchecked_arm` false. `loop_history.json` reads back the four town roles in rounds 1–4, ten games per round.
- The thinking-level probe: "minimal" gave no reasoning tokens, both sides ran at the same level, so the results' scope narrows and the page uses the "no reasoning tokens" wording (blindspot log §⑦; controls §4).
- The June case: byte-identical prompts, unchanged play code, 1 of 10 against 20 of 30, drift suspected or chance, a model name with no dated version that the service echoed, and the 20 deals re-run (paired_ab log lines 5–38 and 61–67).
- The paired counts: 12 → 7, 7 deals win to loss and 2 loss to win, 11 unchanged, about 18% (`june_baseline_shift_check.py`; paired_baseline.md verification note).
- "Changed the claim, not the rule" (controls revision note; paired_baseline.md).
- `run_batch.py` does not alternate configurations game by game (controls §1).
- Pinning removes one source of drift but not serving-stack changes; two backends differ even at temperature 0 (controls §1).
- Noise levels: 1–2 of 267 on re-judging; 8 of 10 then 1 of 10 on one vote prompt; about 6 points at 70 samples (controls §3; turn report §2).
- Pairing bought little: 0.25 within a deal against 0.21–0.26 across, nine-player game only, and running both sides in the same window was what mattered (game report "What pairing turned out to buy").
- Detectable sizes: about 36 points of win rate, 0.18 of vote accuracy, about 100 games a side for 0.10 (controls §3).
- The simulation: 15 memory-off games, +0.15 planted, 24 games, about 1 in 9, false alarms 2–3%, no model calls (v7 report).
- Final memory test method: main measure, secondary measures, a fixed number of games, the promised wording for a null, and its self-checks (game report case 2; v7 report). The paired design was never sized (v7 report "The tradeoff").
- Closing: strong where code enforces, weak where a person must remember; the four next steps (controls "Bottom line" and "next time" rows 1–4).
- No item from the map's Handle-with-care list reached the page copy.

## 3. Not checked

- **Replays run all versions in one session** (*Keeping both sides in one time window*): this rests only on the controls report. I did not check it against the replay tool's code; the brief also lists it as open. The turn report's note that most screens ran each arm once suggests interleaving was not universal.
- **Whether the 20 reused deals were among the earlier 30 games:** `seed_set.json` says they are "recovered baseline game_ids" from an extraction batch file, and I did not reconcile that file with the original 30. The page's "20 of those deals" depends on this.
- **Whether the declare-or-waive gate existed when the July run started (2026-07-17):** inferred only from `unchecked_arm: false` in that run's config. I could not run git history in this read-only session.
- **The provider's pinning statement and the temperature-0 backend difference:** taken from the controls report. I did not open the external provider pages or `drift_surfaces_and_guards.md`.
- **Using the dealt lineup on the ten-player game to reduce noise:** `variance_reduction_levers.md` not read.
- **The underlying reports for the 1–2 of 267 and about 6 points figures:** `factual_errors/report.md` and `model_admission/report.md` not opened; taken from the controls report, as the owner's no-audit rule for numbers allows.
