# Decision-replay screen — off-policy causal eval of memory at the decision level

Status: **active record** (2026-06-13). A cheap, drift-immune screen that asks, per frozen decision,
"does swapping ONLY the memory block change what the agent decides, and toward the right answer?" —
the causal counterpart to the echo-read and a pre-filter for the expensive game-replay A/B.

## Why this exists

The game-replay town finding (memory → ~−40pp win, −22pp vote acc) was confounded by overnight model
drift + an un-merged-store volume effect, and the win signal sits under ~0.35 of per-game role-luck.
Decision replay isolates the memory's effect: freeze one decision, swap only the retrieved-memory
block, regenerate just that decision, score it against ground-truth roles. Paired at the decision
(role-luck cancels), drift-immune in one sitting, and the target is memory-independent.

## Method / harness

- **Replay = fresh generation.** For each arm (memory off / as-stored / framing variant) the decision's
  context is frozen (board, transcript, private info from the eval-case) but the memory block is
  swapped and the vote is **regenerated live** by the game model. Scored on the fresh vote, never the
  recorded one. Model = `gemini-3.1-flash-lite` @ temp 1.0 — the SAME model+temp the games used
  (verified in both batches' `runtime_fingerprint`). temp 1.0 ⇒ genuine resampling ⇒ run 3× and pool.
- **Outcome scoring is mechanical, no LLM** (`decision_scoring.py`): town-correct vote = votee ∈
  {wolf, serial_killer}. Decision *value* = hit(+1) − mislynch(−1), abstain neutral(0). `allow_abstain`
  is reconstructed from `day_resolutions` exactly as `fan_out_vote` computes it (the harness otherwise
  defaults it off, which would strip a real choice — 70/354 day-3 cases were correctly abstain-forced).
- **Adherence judge** (`memory_adherence.py`, gemini-2.5-pro, outcome-blind, verdict-aware): per-memory
  followed/contradicted/NA + applied/overrode/ignored. Built + validated on 3 cases; NOT yet run at
  scale (every result below is judge-free mechanical scoring).
- **Reuses**: `evaluation/src/components/application.py` (`run_application_action`, `action_spec_for`),
  `situation_summary.eval_case_to_agent_payload`, `data/local_cases.LocalCaseSource`. Driver:
  `evaluation/src/experiments/decision_replay.py` (parallel, McNemar/sign tests, `--causal --roles
  --min-day --max-day --judge`).

## Findings

**1. Town day-3+ : NULL.** net-first off net=+0.367 → stored +0.361, Δ=−0.006; 9 improved / 11 worsened /
160 tied (180 paired), sign p=0.82. (The first N=20 read of −0.10 was small-N noise — 4 flips; it
vanished at N=180. The screen killed its own false signal.)

**2. Town day-2 : memory HELPS (+0.078), once scored correctly.** Raw abstain effect is huge — memory
raises day-2 abstaining 0.58→0.71, McNemar p≈3×10⁻⁶ (23 induced / 1 removed). But day-2 is
info-starved: when no-memory town votes it hits a threat only 41% of the time, so a day-2 vote is
usually a mislynch. Decomposing the 23 induced abstains by whether a threat was findable (off-arm):
**20 GOOD** (off would have mislynched → memory correctly held back) vs **3 BAD** (a real threat was
findable, memory abstained anyway). With abstain scored neutral, net value goes off=−0.072 →
stored=+0.006 (Δ+0.078): memory cuts the mislynch rate 0.244→0.144. So the day-2 "passivity" is mostly
*correct caution*, not harm — the earlier "harm" read was the hit-rate metric scoring a good abstain
as a mislynch.

**3. Framing (net-first vs immediate-first) : NOT significant at the vote level.** Cross-batch (old
store `ab_arms_town`/`v5_0` immediate-first vs `ab_nh_town`/`v5_0_nethorizon` net-first). Immediate-first
day-3 Δ=+0.066 looks like a lift but sign p=0.19, per-run unstable [+0.22, −0.08, +0.07], 14 improved /
7 worsened. Also confounded: off-baselines differ (0.278 vs 0.367 → old-store boards are simply harder),
so the gap mixes framing with board-difficulty headroom. ⇒ Framing doesn't reliably move the day-vote;
the clean test is the paired framing arm (same boards, reframe the same entries), blocked only because
eval-cases store the composed outcome, not the split halves.

**4. Wolf day-vote : NULL on productivity, but coarse.** Wolves vote a non-wolf ~95% in both arms
(self-incriminate ~4-5%); paired wolf-value sign p=1.0 (1/2/177). BUT memory flips the wolf's *target*
37% (vs town's 11%) — it reshuffles which non-wolf, never the productive/self-incriminate split. The
productivity metric is blind to cover/blending, which is the actual wolf day-harm (A/B: memory-on
wolves get lynched more). So this null is on the wrong instrument for deceivers.

**5. Deceiver NIGHT kills : null (wolf) / n.s. (SK) — the A/B effect does NOT replicate.** Power-targeting
= the kill landed on a town power role (investigator/healer/vigilante), the A/B's wolf night proxy. Wolf
night: pooled 0.328→0.328, paired 19 more / 19 less, McNemar p=1.0 (per-run [−0.05, +0.03, +0.02]). SK
night: 0.333→0.361 (+0.028), 6 more / 1 less, p=0.13 — directional, not significant. The A/B's "wolf
power_targeting 0.459→0.544" does NOT survive the clean causal contrast (another drift/trajectory
confound). Same ceiling: `WOLF_CORE_STRATEGY` already says "Removing the village's most effective players
keeps them disorganized — weigh that against drawing a pattern that points back to you" (`roles.py:49`),
SK strategy likewise (`roles.py:60`). Night-targeting is hard-coded → memory redundant.

**6. Town DISCUSSION stance : null.** Replay each town day_discussion turn off vs as-stored, classify the
regenerated turn's stance (outcome-blind judge: drives/supports suspicion vs passive/hedging/defensive).
Town is ~88% passive in BOTH arms; memory does not raise it (off 0.889 → stored 0.872, paired 9 more / 12
less passive, McNemar p=0.66), and drives-suspicion (0.094 = 0.094) and accuses-a-threat (0.067 → 0.072)
are unchanged. The anti-aggression mechanism does NOT appear at the single-turn level — town's high
passivity is its BASE behavior, not memory-induced, and with no per-turn passivity increase there is
nothing for a trajectory to compound. The last candidate home for the town harm comes up empty.

## ⭐ Unifying principle — the screen measures memory's MARGINAL value over the base prompt

Every null and lift falls out of one rule: **memory helps where the base prompt is THIN and is null where
the prompt is already comprehensive** — and extraction is *built* this way, explicitly excluding
"common-sense fundamentals the base strategy already covers" (`extraction.py:203`).

- wolf day-vote → NULL because `WOLF_CORE_STRATEGY` (`roles.py:47`) hard-codes the key heuristic:
  "Blend your vote with the village majority… a dissenting 'protest vote' leaves a permanent, suspicious
  record" (+ the ally-cover and abstain-cover lines in the wolf vote prompt, `day.py:249-250`). Nothing
  left for memory to add → null by construction, NOT evidence memory is useless for wolves.
- wolf/SK night kill → NULL/n.s. because the prompt hard-codes power-targeting too ("Removing the
  village's most effective players…", `roles.py:49`/`:60`). The A/B's +0.085 was confound.
- town day-3 vote → null (info-rich voting is standard play, prompt-covered).
- town day-2 vote → HELPS (+0.078): early-game abstain judgment is thin in the prompt → memory adds it.

⇒ The nulls are memory correctly NOT duplicating the prompt. The base prompts turn out to cover almost
every decision's key heuristic, so memory's marginal value at the DECISION level is ~null nearly
everywhere — and the lone clean lift (town day-2) is exactly where the prompt is thin (early-game
abstain judgment). The game-replay A/B effects (town collapse; wolf power-targeting) largely do NOT
survive the clean causal contrast → they were mostly drift/trajectory/volume confound. Residual harm,
if any, can only live in the TRAJECTORY (discussion compounding over a game), which off-policy
single-decision replay structurally cannot see.

## ⭐⭐ VALIDITY ANALYSIS + REVISED conclusion (2026-06-13, before finalizing)

Stress-testing the "null everywhere" read surfaced a SAMPLING ARTIFACT that revises it. The per-decision
effect is NOT uniform across game phase — `_select_diverse` round-robins each game's EARLIEST decisions
first (~2/game at N=60), so the pooled day-3+ number was early-weighted and averaged heterogeneous
effects:

| town vote stratum | value effect | 95% CI |
| day-2 (early, info-starved) | **+0.078** | [+0.006, +0.149] — significant |
| day-3 (mid, info-rich) | −0.006 | null |
| day≥5 (endgame, high-stakes) | **+0.117** | [−0.008, +0.241] — suggestive |

⇒ Memory HELPS town where the base prompt is thin and the decision is hard (early caution + endgame),
and is null in standard mid-game. The marginal-value principle holds — but stratified, not pooled.

**⭐ CONVERGENCE with the clean paired A/B (the correction that settles it).** The "−40pp town harm" I
kept citing was the NET-HORIZON epoch-B regression — the DRIFT-confounded cross-day arm — NOT a clean
game-level result. The clean game-level test already exists: the **paired A/B** (`paired_ab/`, N=30,
same-epoch baseline, same seeds, memory on-vs-off, FULL games) showed town memory **HELPS** — villager
win 27%→43% (+17pp) town_only, 27%→50% (+23pp) all-on — and wolf/SK **null**. So two independent methods
converge:

| | paired A/B (whole-game) | decision-replay (per-decision) |
| town | +17 / +23pp (helps) | +0.078 day-2, +0.117 endgame (helps) |
| wolf/SK | null | null |

⇒ Town memory helps, wolf/SK null, by BOTH a full-game paired test and a drift-immune per-decision test.
Both CONTRADICT the −40pp net-horizon regression, confirming it was drift. The decision-replay's role is
therefore CONVERGENT VALIDATION + mechanism (helps where the prompt is thin; null where heuristics are
hard-coded), NOT "a screen that says we need a game-level run" — we already have that run. Memory is not
inert: it moves ~1-in-7 decisions (replay fidelity: stored matches recorded 87–93% vs 84–88% off-vs-stored).
Residual is POWER not existence: the paired A/B win cell was underpowered (p=0.27 / 0.167; significance
came from proxies) and pre-drift — an N≈60 same-epoch re-run on today's model would tighten the magnitude,
but the direction is settled by the convergence.

**Threats checked:** sampling (mattered — stratify, don't pool); power (CIs ±5–9pp → nulls = "no LARGE
effect", not zero); replay fidelity (0.87–0.93, faithful). **Threats open:** off-policy — both arms run
on memory-ON boards, so the screen gives per-decision DIRECTION but cannot pin the compounded game-level
MAGNITUDE; proxy metrics (night power-targeting, the 88%-passive stance judge); retrieval-vs-content;
single store/model; post-hoc prompt-ceiling.

**Revised verdict:** the screen (a) deflated the confounded game-replay point-estimates and (b) established
the true per-decision direction = helpful-not-harmful, concentrated where the prompt is thin. It is a
SCREEN, not the verdict: the compounded magnitude needs a clean game-level replay (pinned model, same
epoch, paired seeds, memory on-vs-off from the start). Everything below this line is the pre-revision
per-screen detail; read it through this stratified lens.

## ⭐⭐ Adoption confound + reorder test — does the agent even FOLLOW the memory? (2026-06-13)

The outcome nulls conflate "memory content unhelpful" with "agent didn't follow the memory." Both tested:

**Step 1 — adherence scan** (40 recorded town day≥3 decisions, 130 memories judged): **59% IGNORED**, 39%
applied, 1.5% overrode. Action aligned 61% / contradicted 20% / NA 19% — but 61%-followed overstates
adoption (77% of memories say "avoid"; default cautious play coincidentally aligns). ⚠️ Judge caveat
(user's catch): the judge reads the agent's STATED reasoning — post-hoc under the vote-first bug — so it
measures STATED engagement, not actual influence, could be primed by the rationalization, and does NOT
judge whether ignoring was CORRECT. The judge-FREE measure is the outcome flip rate (~12–16% of votes
change off→stored); it agrees (low influence). ⇒ the nulls are heavily contaminated by non-adoption.

**Step 2 — judge-free reorder 2×2** (3×N=100): {vote-first, reason-first schema} × {memory off, stored};
reason-first emits updated_strategy BEFORE vote_target. Stable:
- vote-first: off 0.40 → stored 0.35 (memory ≈ −0.05, reproduces day-3 null).
- reason-first: off **0.26** (baseline lift −0.14, stable) → stored 0.11 (memory ≈ −0.15).
- DiD = **−0.10**: memory is MORE negative under reason-first, not less.

**⚠️ Adoption check RETRACTED — single-run noise, did not replicate.** A first N=40 run showed reason-first
applied 0.44→0.51 (consideration up); a SECOND N=40 run FLIPPED it (reason-first 0.42 < vote-first 0.52),
and a strong memory-LINKED variant (the reasoning field reframed to "reason about this vote, link each
memory, weigh-and-can-reject") landed at 0.45. Pooled across runs the judge-measured adoption is FLAT
(~0.46–0.48) across vote-first / reason-first / memory-linked. The judge adoption signal is too noisy at
N=40 (temp 1.0) to claim ANY schema raises consideration; the earlier "+7pp" was noise. ⇒ reordering the
output schema does NOT reliably raise the agent's memory engagement, and even an explicit "engage each
memory" instruction didn't move it here. The only ROBUST result is the judge-FREE outcome: reason-first
degrades the decision process (baseline + memory both worse, 3×N=100). Whether the connection is
strengthenable by mechanical reorder is UNRESOLVED (noisy; best estimate flat) — which itself points to
CONTENT, not field-order, as the lever: the agent engages memory it finds useful and ignores the rest
regardless of output order. (To settle the consideration question would need a judge-free engagement proxy
at scale, or a much larger judge run.)

⇒ Hypothesis (reorder reveals helpful memory) NOT supported — with caveats: (1) only HALF the fix
(reorder, no adoption scaffold) and a WEAK reorder (the strategy NOTE, not a clean "reason about this vote"
step); (2) the net-first (harmful-content) store; (3) day-3 (prompt-covered). **The real signal flips the
priority:** forcing the connection makes the net-first memory drag the vote DOWN → the agent's ignoring was
partly PROTECTIVE (not letting bad memory override a decent gut read). So CONTENT is the bottleneck, not
connection — wiring the agent to follow BAD memory is worse than ignoring it. Order: content-first
(read-conditioned lessons) THEN connection (proper reason+scaffold), tested on GOOD content. Consistent
with the paired A/B (immediate-first content HELPED town +17/+23pp; net-first content is the problem).

## Conclusions

At the individual **vote** level, net-first town memory is **neutral-to-helpful** (null day-3+,
beneficial day-2 caution), and framing doesn't reliably move it. Therefore the game-replay town
collapse is **not in the vote decisions** — it is either (a) the **discussion trajectory** (where
yesterday's anti-aggression transcripts lived; off-policy vote-replay structurally can't see it), or
(b) **mostly the drift/volume confound**. Wolf day-vote is null on the coarse productivity metric; the
real deceiver signal is at **night** (power-targeting, where the A/B found wolf memory HELPS).

## Caveats

- **Off-policy / myopic**: boards were generated under memory-on; the regenerated decision can't
  propagate. Valid as a *local* decision screen, not a trajectory/win measure.
- **temp 1.0 noise** ⇒ all results are 3×60 pooled with paired sign/McNemar tests; single runs swing.
- **Dedup asymmetry is minor**: stores `v5_0_raw` 445 / `v5_0` 431 / `v5_0_nethorizon` 461 town-incl;
  but villager/day_vote = 30 entries in ALL three, so the vote screen's dominant namespace is
  dedup-matched. The board-difficulty confound (finding 3) is the larger one.

## Open frontiers (need harness build)

- **Night-kill replay (deceivers)**: wire night nodes into the replay (different path than `_run_agent`;
  SK + night actions absent from `ACTION_SPECS`). Score wolf kills vs town-power-role targeting, SK
  targets vs survival relevance. This is where the A/B located the deceiver effect.
- **Town discussion screen**: the likely home of the town harm. No clean role-lookup target → needs a
  judge/proxy (does memory make town's discussion less likely to name/build the real threat).

## Artifacts / pointers

- Driver `evaluation/src/experiments/decision_replay.py`; scorers `evaluation/src/components/
  decision_scoring.py` + `memory_adherence.py`.
- Runs: `causal_nh_town_run{1,2,3}.json` (day3+), `causal_nh_town_day2_run*` (day2),
  `causal_arms_town_run*` (old-store day3+), `causal_nh_wolf_run*` (wolf day3+),
  `causal_smoke_nh_town.json` (N=20 noise exhibit).
