# Replay screens: testing one change on recorded moments

This page covers the project's cheapest way to test a change: take one recorded moment of a game (a vote,
a spoken line, a night choice, a memory lookup), rebuild it exactly as it was, and run it again with one
thing changed: the memory block, a prompt sentence, a line from the deduction engine, a card's text. It
says how a replay is built, what any replay can and cannot show, what the screens found, and how far each
can be trusted.

The full write-up of every screen, with its mechanism, corrections and code paths, is the
[experiment log](experiment_log.md). Replays whose measure is a factual-error count are in
[factual_errors](../../factual_errors/report.md); replays used to choose a model in
[model_admission](../../model_admission/report.md); whole games in
[whole games](../game/report.md). What each screen led to (which fix shipped,
which idea was dropped) is in its design folder, named in the Sources table. How it all fits together is
in [the hub](../../report.md).

## In short

- **The approach: freeze one turn, then run the controlled experiment on it.** A recorded turn's whole input
  (the board, the transcript so far, the seat's private record, its memory) is rebuilt exactly, and each
  version of the change answers that same input many times. Only the change differs.
- **Why: a clearer effect from fewer samples, at lower cost.** In a whole game the deal, every other
  player's moves and how the day unfolds all vary, and that noise buries a small effect: a 30-game arm cost
  $15–30 in June and could show only large effects. A frozen turn holds all of that fixed, so a difference
  between versions is the change's own effect, and each sample is one model call: a typical screen cost
  under $0.01 to about $0.25. Both versions run side by side in one sitting, so drift in the model service
  hits both alike.
- **This is common practice** for systems whose full runs are long, costly and noisy: replaying recorded
  traffic against a new version, or re-running saved traces of an LLM app under a new prompt or model.
- **What it shows: whether a change reaches a turn, and which way it pushes.** How large the effect is needs
  many cases or a measured noise floor. And because the frozen history was produced without the change, a
  replay cannot show effects that build up later in the day; those need whole games.
- **The biggest limit is single-case noise.** The same vote prompt went to the right player in 8 of 10
  samples on one run and 1 of 10 on the next. Only a shuffled design with 25 samples per arm gave a stable
  rate.
- **It has done real work:** it screened out every cheap way to make memory more useful before a paid run,
  falsified a night-1 fix before a single game ran, and showed that a proposed voting sentence made a
  ballot worse (7 of 10 right to 0 of 10).

## Quick view

| Screen | Trust | Main limit |
|---|---|---|
| Memory decision replay (nine-seat) | ✅ | Direction and cause at one moment; not size, win rate or what follows |
| Night-1 target check | ✅ | Code counts targets and the effect is huge; nine-seat boards, one model |
| October prompt and engine screens on Haiku (evil cover, vote replay, visit wording, persona line, voice rewrite, deduction injection, placement and AC2) | 🟡 | One case sampled ten times can swing from 8 in 10 to 1 in 10; later-in-day effects hidden |
| Stage-filter replay (ten-seat memory) | 🟡 | One store, 96 lookups, uncalibrated fit labels |
| Checkpoint replay | 🟡 | Caught the v7 store's harm only on cases from the same games |
| Tell-book screen, private-note screen, counter-claim vote screen | ⚠️ | Smoke tests: too few cases or too noisy for more than direction |
| Per-day replay | ⏸ | A design only |

✅ sound · 🟡 usable with caveats · ⚠️ smoke test only · ⏸ not built.

---

## 1. The approach: how a replay is built

**The question:** how do you test a fix for a failure seen in one game, without playing dozens of new games?

**Why a replay, not new games.** A whole game is one long chain of random events: the deal, whom the wolves
target, every other player's line and vote. Two versions compared over whole games differ in all of those,
so a small effect needs many games to show: in June a 30-game arm cost about $15–30 and could detect only
large effects. A replay freezes one recorded turn with everything it saw and regenerates only that turn under
each version. Everything except the change is held fixed, so the remaining spread is the model's own
sampling, and an effect shows from tens of samples. Each sample is one call, so a typical October screen
cost from under $0.01 to about $0.25, and both versions run in one sitting, so drift in the model service
hits both alike. The question it answers changed over time: first "does memory help at this moment?"
(June–July), then "does this change fix the failure seen in a live game, without breaking the turns that
were right?" (October).

**Step 1. Freeze a moment.** A *case* is one recorded decision, stored as the state the engine held just
before it. It comes from one of four sources:

| Source | What is frozen | Used by |
|---|---|---|
| Nine-seat batch records | the agent's input at a vote or night action | memory decision replay, checkpoint replay, tell-book screen |
| Checkpoints of live ten-seat games | the day's state just before a line or a vote | deduction screens, private-note screen, Haiku vote replay, visit wording |
| Captured prompts of AI-only games | the input each seat received | evil cover screen, counter-claim screen |
| Recorded lookups and lines | a memory search, or a spoken line | stage-filter replay, voice rewrite |

**Step 2. Rebuild the prompt from today's code.** The engine's own builders rebuild the turn and render
today's template. Text the engine wrote in the old state (ballot lines, the closing call) is updated to
today's wording; text players and the summariser wrote stays as it was. The rebuild reproduced all 41
captured seat blocks exactly on the evil-cover turns.

**Step 3. Change one thing per arm.** Each arm is its own process, usually from its own git worktree on a
tag or commit, because prompt versions are read when the code loads. The best runners check before any
model call that the arms differ only where intended (the placement screen confirmed its seat block
byte-identical between arms).

**Step 4. Measure, in one of three ways, which carry different trust:**
1. **By code:** the vote or night target, a structured field limited to legal targets, against the true
   roles. No judge.
2. **By pattern count:** a regex over the player's reads counts what a vote cites. It finds mentions; it
   does not judge the reasoning.
3. **By blind read:** Claude subagents read shuffled samples with the arm hidden, against a rubric fixed
   before the run (the method is in [sampled review](../../labeling/sampled_reads/report.md)). These readers are
   uncalibrated.

**Where a replay sits.** It is the cheapest rung of three: a frozen turn (this page), a whole replayed day
(designed, not built, §4), and whole paired games ([whole games](../game/report.md)).

## 2. What any replay can and cannot show

Four limits apply to every screen below, and the October screens kept enough records to measure them.

1. **One case sampled ten times is the spread of answers to one prompt, not ten situations.** The same AC2
   vote prompt went to the real Healer in 8 of 10 samples on one run and 1 of 10 on the next. At 25 samples
   per arm, with all arms shuffled into one schedule, it was about one in three in every arm. In the Haiku
   vote replay, adding only true facts to earlier ballots moved single cases from 4 to 9 and from 6 to 2 of
   10, more than any effect under test. The tell-book screen's unchanged arm scored 18 and then 20 of 40 on
   the same cases. **So:** a difference of a few samples on one case is noise. Two habits addressed it:
   running the unchanged arm twice, and interleaving all arms in one shuffled schedule.
2. **A frozen transcript cannot show what a change does later in the day.** The replayed turn inherits a
   discussion generated without the change. The checkpoint replay could not reproduce the v7 store's
   abstain cascade, which lived in the discussion; the visit-wording fix could not stop replies to a denial
   already in the transcript.
3. **The cases must come from the same version of the game as the change.** Drawn from older v6 games, the
   checkpoint replay showed no harm from the v7 store; drawn from the v7 games themselves, it put the full
   store last on every readout.
4. **The record is not always complete.** Several runs used a working tree with uncommitted changes (the
   placement and AC2 records keep a hash of that diff), and some raw samples lived only in the gitignored
   results folder until they were copied into the record on 2026-10-23.

## 3. What the screens found

### Memory (nine-seat, June–July 2026; one ten-seat replay in October)

| Screen | What it tested | What it found | Trust |
|---|---|---|---|
| **Decision replay** | One vote or night action regenerated with memory on and off, scored by code | Town memory helped and deceiver memory was null, in agreement with the June paired games; every cheap way to make agents use memory better came back null or harmful | ✅ as a direction-finder, on one June epoch |
| **Checkpoint replay** | A fixed exam of town decisions re-answered against each memory store | On cases from the v7 games, the full store came last (decision value +0.04 against +0.13 for an empty store; votes on townspeople 46% against 36%); on older cases, no difference | 🟡 direction only (2 to 6 discordant pairs) |
| **Tell-book screen** | 40 votes with and without a block of role tells | Correct votes 20 → 24 (one-sided p ≈ 0.11); the unchanged arm moved 18 → 20 between runs | ⚠️ the channel reaches decisions; nothing about benefit |
| **Stage-filter replay** (ten-seat) | 96 memory lookups searched again, dropping lessons from a different game stage | Lessons that fit rose from 15% of 264 shown to 25% of 114, at the cost of 25 empty lookups; the replay reproduced what seats were shown in 91 of 96 lookups | 🟡 one store; uncalibrated fit labels |

**The decision replay's agreement, corrected.** It was validated because, built independently, it agreed
with the June paired games: town memory helps, deceiver memory is null. The June games' win-rate gains
(+17 and +23 points) were not significant (p = 0.27 and 0.17); what June established was better town
*decisions* (healer saves on the real target 37% → 60%, p = 0.005; lynches on an enemy 47% → 64%, p =
0.028). So the screen agrees with June's decision measures, not a win-rate gain, and both belong to one
epoch: the v6 store did not repeat the gain (+6 points, p = 0.77), and at the July v7 endpoint memory scored 0.147
lower (19 of 30 boards, p ≈ 0.06). **One finding
shows why strata matter:** outcome framing looked like a clean null pooled over 40 cases, but on day 2,
when players know least, it turned would-be mislynches into abstains (mislynch 0.23 → 0.07; 4 worse / 0
better, p = 0.125), a suggestive result that pooling would have hidden.

### Play (mostly ten-seat, October 2026)

| Screen | What it tested | What it found | Trust |
|---|---|---|---|
| **Night-1 target check** (nine-seat) | Where unguided night-1 choices land, 32 boards, 96 calls per arm | Seat 1 took 78 of 96 actions; with an engine-drawn lot offered, 95 of 96 took it and every seat got 6–16. Shuffling the player list first left the target on the lowest-numbered seat in 95 of 96: the model follows the seat number, not the list order | ✅ falsified the first fix before any game |
| **Evil cover screen** | What an accused evil seat says, before and after the "claim, never deny" card | Claims rose from 13 to 33 of 82 samples and denials fell from 21 to 3; with the final cover line, 1 of 42 claims could be shown false | 🟡 different readers per step |
| **Haiku vote replay** | One sentence asking reads to compare the living players, 11 votes from one game | On the target ballot it made things worse: 7 of 10 right without it, 0 of 10 with it (p = 0.003) | 🟡 one game; its own noise floor is large |
| **Visit-wording A/B** | Whether "visit" wording causes arguments about definitions | Mechanics errors stayed about one line in four on DeepSeek and rose slightly on Haiku (19 → 28 of 95, p = 0.51): the wording is not the cause | 🟡 arm A judged twice gave 19 and 23 |
| **Persona line screen** | One sentence of voice in the seat's prompt | Voiced lines judged more natural in 25 of 30 pairs; stance changed in 9 of 30, the same 30% as two plain lines (3 of 10) | 🟡 the noise baseline is only 10 pairs |
| **Voice rewrite screen** | A second call rewriting a line in a persona's voice | Read better (74 of 90), but 19 of 90 changed something a listener could act on; the fact gate caught 1 of those 19 | 🟡 all 19 confirmed by hand |
| **Private-note screen** | A three-part rewrite of the private strategy note | No gain: fact or rule errors rose from 15 to 27 of 56; the healer still passed in 7 of 8 under both | ⚠️ blinding partial; no test |

### Deduction engine (ten-seat, October 2026)

These test lines the deduction engine writes into a seat's prompt, on four acceptance cases from two Haiku
games. The engine's own correctness is checked by code ([deterministic_audits](../../deterministic_audits/report.md)).

| Screen | What it tested | What it found | Trust |
|---|---|---|---|
| **Deduction injection (R1)** | A healer's night record stating that the Chanteuse visited it | The fact reached all 10 low-thinking notes, but the healer still spoke 0 of 10 times; its carried-forward note kept it silent (spoke 3 of 30 with the note as played, 9 of 20 with a neutral note, p = 0.007) | 🟡 one case, one game |
| **Placement and the AC2 series** | The deduction block before or after the seat's note; then three runs on one stubborn vote | About a third of AC2's votes went to the real Healer in every arm at 25 samples each (33 of 100); neither placement nor two removed sentences changed it. The owner kept "before the note" | 🟡 the clearest record of single-case noise |
| **Counter-claim vote screen** | A line setting two rival claimants' results side by side | Votes did not move overall (12 fake / 16 real without; 12 / 17 with); in its target case it made things worse | ⚠️ 10 turns, 3 samples; cannot be rerun at HEAD |

## 4. The per-day replay (designed, not built)

The rung between a frozen turn and a whole game: re-run one whole day of a recorded game under a changed
condition, with the real scheduler, real lines and live votes, and the earlier days frozen as history.
Designed on 2026-07-02 at about $0.10–0.15 a day, a fifth to a third of a game. Its design puts an
acceptance gate first: before any comparison is trusted, an unchanged replay of 10–15 recorded days must be
indistinguishable from what was recorded, and that self-agreement becomes the harness's noise floor. It
would answer what a change does within a day, never the game outcome. It was not built; the October screens
repeatedly hit the gap it targets, effects that live in the rest of the day.

## 5. What the replays taught

1. **Measure the noise before reading the effect.** Run the unchanged arm twice, or shuffle all arms into
   one schedule. The AC2 series showed how far a single case swings without either.
2. **Score by code where the decision is a structured field.** The night-1 check and the vote replays
   needed no judge, and gave the clearest results.
3. **Draw cases from the same version of the game as the change.** The checkpoint replay saw the v7 store's
   harm only on v7 cases.
4. **A frozen turn shows the direct effect only.** Effects that spread through the day (an abstain cascade,
   replies to a denial) need the per-day replay or games.
5. **A reader beside a code gate exposes the gate.** The voice rewrite's readers found 19 changed lines; the
   gate caught one.

## What we would do differently next time

| Stage | Change | What was done | What it would buy |
|---|---|---|---|
| Design | **1. Build the noise floor into every screen**: the unchanged arm twice, all arms in one shuffled schedule | Done in the persona line and the AC2 2×2; most screens ran each arm once | No single-case swing read as an effect |
| Cases | **2. Draw cases from the current version, and enough of them** (dozens, not one case sampled many times) | Several screens rested on one case or one game | A rate across situations, not the spread of one prompt |
| Measure | **3. Prefer a structured field scored by code; when a reader is needed, double-read a slice** | Blind reads by one reader per item | A known agreement rate behind each label count |
| Record | **4. Run from a commit, and copy samples and the model id into the record** | Several runs on uncommitted trees; two screens never recorded the model | Every screen rerunnable and citable |
| Scope | **5. Build the per-day replay's acceptance gate** | Designed in July, never built | A tested way to see effects later in the day without whole games |

**Bottom line.** Replays are the project's workhorse for testing a change cheaply and fairly: one change, one
frozen moment, both versions side by side. They answer whether a change reaches a turn and which way it
pushes, and they have screened out ideas and fixes before any game was spent on them. They cannot give
sizes without a noise floor, and they cannot show what happens later in the day.

## Sources

| Screen | Code | Record |
|---|---|---|
| Decision replay | `evaluation/src/studies/decision_replay.py`; engine `evaluation/src/replay/decision_screen/`; lenses in `Agents/memory/consolidation/decision_scoring.py` | [`decision_replay/report_screening_layer.md`](../../../memory_system/effectiveness/decision_replay/report_screening_layer.md), [`experiment_log.md`](../../../memory_system/effectiveness/decision_replay/experiment_log.md); [log](experiment_log.md), Memory replays |
| Checkpoint replay | `evaluation/src/replay/decision_screen/checkpoint_replay.py` (`eval-checkpoint-replay`) | [`credit/blindspot_fix/experiment_log.md`](../../../credit/blindspot_fix/experiment_log.md) ④–④d |
| Tell-book screen | `evaluation/src/replay/decision_screen/tell_book_screen.py` | [`tell_extraction/experiment_log.md`](../../../extraction/tell_extraction/experiment_log.md) ⑫ |
| Stage-filter replay | `evaluation/experiments/v8_stage_filter_replay.py` | [`memory_system/v8/experiment_log.md`](../../../memory_system/v8/experiment_log.md); `data/gate/stage_filter{,_40games}/` |
| Night-1 target check | `evaluation/experiments/night1_target_bias_check.py` | [`data/night1_target_bias/`](../../../gameplay/data/night1_target_bias/README.md); `discussion_evidence.md` §7.5 |
| Evil cover screen | `evaluation/experiments/evil_cover_screen.py` | [`data/evil_cover_screen/`](../../../gameplay/data/evil_cover_screen/README.md) |
| Private-note screen | `evaluation/experiments/note_prompt_cases.py` | `gameplay/deduction/experiment_log.md` §6; `gameplay/deduction/data/note_prompt/` |
| Haiku vote replay | `evaluation/experiments/haiku_vote_{cases,score}.py`; configs `evaluation/config/hallucination_bench_haiku_vote_compare.json`, `_haiku_game_vote_v2.json` | `discussion_evidence.md` §8.7; `gameplay/data/haiku_vote_replay/`, `data/haiku_sentinel_vote/` (committed `516318c9`) |
| Visit-wording A/B | `evaluation/experiments/visit_wording_cases.py` | [`data/visit_wording_ab/`](../../../gameplay/data/visit_wording_ab/README.md) |
| Persona line screen | `evaluation/experiments/persona_line_screen.py` | [`data/persona_line/`](../../../gameplay/data/persona_line/README.md) |
| Voice rewrite screen | `evaluation/experiments/voice_rewrite_screen.py` | [`data/voice_rewrite/`](../../../gameplay/data/voice_rewrite/README.md) |
| Deduction injection (R1) | `evaluation/experiments/deduction_injection_{cases,score}.py` | `gameplay/deduction/experiment_log.md` §4–§5; `gameplay/deduction/data/deduction_injection/` |
| Placement and AC2 series | `evaluation/experiments/deduction_placement_screen.py`, `deduction_ac2_{ablation,2x2,closing_fixed}.py` | `gameplay/deduction/data/deduction_placement{,_n10}/`, `deduction_ac2_*/` |
| Counter-claim vote screen | `evaluation/experiments/counter_claim_vote_screen.py` | [`data/counter_claim_votes/`](../../../gameplay/data/counter_claim_votes/README.md) |
| Per-day replay (design) | none | [`day_replay/design.md`](../../../memory_system/effectiveness/day_replay/design.md) |
| Shared replay engine | `evaluation/src/replay/hallucination_bench.py` (`turn_payload`, `turn_template`, `hydrate_state`); `evaluation/experiments/haiku_game_turn_cases.py` (`day_states`); `evaluation/experiments/deduction_block_census.py` (`_payload_at`) | [factual_errors](../../factual_errors/report.md) |

*Rewritten 2026-10-24 as a plain summary of the 2026-10-23 write-up, which is kept whole as the
[experiment log](experiment_log.md).*
