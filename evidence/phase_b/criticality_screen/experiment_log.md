# Criticality screen — does conditioning retrieval on the v6 criticality regime move villager day-votes?

**Status:** RUN 2026-06-15. Step 3 of the cheap-first dimension build (spec
`evidence/phase_b/dimension_schema_build_spec.md` §9). Triage, not a verdict — reads DIRECTION +
the criticality SIGNATURE + the causal-flip-rate, NOT significance. **Result: initially GO, then
DOWNGRADED to HOLD after a same-game-leakage bug was found and fixed — see the ⚠ CORRECTION below.**
The sections through "Decision" describe the FIRST (contaminated) run; read them through the correction.

## What was tested

The v6 schema pulls criticality (`players_alive` / `distance_to_parity` / `is_swing`) out of the
embedding (the bi-encoder mangles magnitudes) and exposes it as a reranker signal. The screen asks:
if you condition retrieval on the criticality regime, do villager day-votes improve over ignoring it?

- **Store:** `memory_stores/v6_0` — 119 RAW villager·day observations (62 day_discussion + 57
  day_vote), re-extracted from the 20 frozen v5_0 games with the v6 schema (no dedup).
- **Decisions:** 60 villager day-votes from `batch_results/ab_arms_town.jsonl`, day-balanced (the
  screen is stratified by day; late-game villager votes are scarce — 3 villagers, some killed by
  endgame — so a game-first sample would be all day-2).
- **Self-contained retrieval (only the conditioning differs between arms):** both arms rank the SAME
  119-candidate pool with the SAME embedding. **flat** = top-5 by cosine. **cond** = top-5 by
  `cosine − λ·|Δplayers_alive| − ν·|Δdistance_to_parity| + μ·[is_swing match]` (λ=0.02, μ=0.03,
  ν=0.01). **off** = no memory (the floor). Query criticality computed deterministically from the
  frozen board (alive list ∩ true roles) — omniscient, offline, never shown to the agent.
- **Replay:** regenerate the vote under each arm, score against true roles (hit threat / mislynch),
  pair by decision, stratify by day. net-value = +1 hit threat / −1 town mislynch / 0 abstain.

## Result — the signature is textbook

| stratum | n | off | flat | cond | cond−flat | flips→threat / away |
|---|---|---|---|---|---|---|
| all | 60 | 0.367 | 0.300 | **0.417** | **+0.117** | 4 / 0 |
| mid_game (alive>4, no swing) | 44 | 0.591 | 0.500 | 0.568 | +0.068 | 2 / 0 |
| **high_criticality (swing or ≤4 alive)** | 16 | −0.25 | −0.25 | **0.00** | **+0.25** | 2 / 0 |

(net-value; high-crit accuracy 0.375→0.50.)

By day (the falsification axis): day-2 (n=13) cond−flat **+0.077 ≈ null** — conditioning did NOT
spuriously help where regimes barely differ (falsification passed). The recovery shows up late, where
flat struggles: day-7 (n=4) flat −1.0 → cond 0.0 (flip-rate 0.5, 2→threat); day-4 (n=12) +0.167.
Days 3 (all already perfect, no room) and 5/6 flat.

**The three GO criteria, all met:**
1. **Direction:** cond ≥ flat everywhere; cond (0.417) > off (0.367) > flat (0.30) overall — plain
   memory doesn't beat no-memory for town day-vote (consistent with rerank≈raw), but
   criticality-conditioned memory does.
2. **Signature:** the gain is CONCENTRATED in high-criticality (+0.25) and ~null mid-game (+0.068) /
   at day-2 (+0.077). This is the predicted shape: a wrong-regime neighbour is the *opposite* lesson,
   so conditioning bites exactly in the endgame.
3. **Causal flips:** 4 toward threat, **0 away** across 60 decisions — conditioning never once pulled
   a vote off a threat. flip-rate 0.117 overall, 0.188 high-crit.

**Mechanism confirmed:** same-regime entries in the top-5 go flat 2.8 → cond 4.88 overall; for
endgame queries flat lands only 2.56/5 same-regime (it MISSES endgame-appropriate lessons because the
pool is dominated by mid-game entries), and conditioning fixes that. That is the lever doing its job.

## Caveats (it is a triage)

- **Small N where it counts:** high_criticality n=16; individual late-day cells tiny (day-7 n=4).
  McNemar p's are not significant (best 0.125) — but this is explicitly NOT a significance test. The
  basis for GO is direction + signature coherence + flip asymmetry, pre-registered.
- **Single batch, single λ.** λ was hand-set so conditioning re-ranks within semantically-plausible
  candidates rather than pure regime-sort (cosine spread is tight, ~0.08). The flips-toward-only=4/away=0
  asymmetry is λ-robust (conditioning only ever helped), but a confirmatory second batch and a λ-sweep
  would firm the GO before/with the step-4 roll. The step-4 full build is itself gated by the
  mandatory freeze-time regression gate.

## Decision

GO. Roll the full DAG (the two shared profiles, F/G on wolf·day, the conditioners) and re-extract the
rest of the roles (spec §9 step 4). The criticality dimension is a real retrieval lever for villagers,
and its value lives precisely where the schema design predicted — the endgame.

## ⚠ CORRECTION (2026-06-15, same session) — the first GO was contaminated by same-game leakage

The first run (`screen_arms_town_n60.json`) retrieved from ALL 119 v6 candidates including memories
mined from the SAME game the decision came from — and **20 of ab_arms_town's 30 games ARE the v6
source games**. A memory from game G knows G's outcome; production never retrieves same-game memory.
Bug fixed: exclude candidates whose `game_id` == the decision's game. Re-ran:

| read | high-crit cond−flat | mid cond−flat | overall cond / flat / off | note |
|---|---|---|---|---|
| n=60, **contaminated** | +0.25 (n=16) | +0.068 | 0.417 / 0.30 / 0.367 | leak inflated endgame |
| n=90, same-game-excluded (mixed) | +0.087 (n=23) | +0.105 | 0.478 / 0.378 / 0.444 | concentration WASHES OUT |
| n=82, **held-out games only** (store never saw them) | +0.286 (n=7) | +0.04 | 0.256 / 0.195 / 0.024 | concentration RETURNS, n=7 |

**Honest read:**
- **Overall conditioning effect is real but small and robust:** cond ≥ flat in every read (+0.04 to
  +0.10); cond > off everywhere. On the held-out (novel) boards memory matters most — flat 0.195 /
  cond 0.256 vs off 0.024. Flips are consistently net toward threat (7/2 in both larger runs).
- **The criticality CONCENTRATION (the schema's core justification) is NOT robustly established.** It
  is strong in the contaminated run (inflated) and in the clean held-out cut (+0.286) but vanishes in
  the same-game-excluded in-sample cut (+0.087 ≈ mid +0.105). The high-criticality stratum is
  **data-starved** (only ~7–23 endgame villager day-votes EXIST — villagers rarely survive to the
  endgame), and it cannot be cheaply grown: the held-out games are shared across the town batches
  (same boards), and widening to other town roles IS step 4 itself.

**Revised decision: HOLD, not a clean GO.** The lever is directionally positive but modest, and the
specific endgame-concentration that motivated pulling criticality out is underpowered. Options before
committing the full-DAG re-extraction bill: (a) accept the modest overall + held-out signal and roll
(the mandatory freeze-time regression gate is the backstop); (b) strengthen high-crit N first, which
requires new games or the town-faction roll (circular); (c) treat the structural asymmetry as the
finding. The leak-discovery itself is a methodology result worth keeping.

## Pointers

- Run: `screen_arms_town_n60.json`. Code: `evaluation/src/experiments/criticality_screen.py`.
- Store: `memory_stores/v6_0` (`evaluation/src/experiments/reextract_villager_day.py`).
- Schema: `Agents/schemas/memory.py` (VillagerDayObservation). Spec: `../dimension_schema_build_spec.md`.
