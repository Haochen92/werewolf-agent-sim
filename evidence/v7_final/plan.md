# v7 — the final memory-architecture iteration (plan + pre-registered stopping rule)

*Folder regrouped 2026-07-05 (runs/ + purpose subfolders); artifact paths below predate the regroup — see README.md for the current layout.*

**Date:** 2026-06-17 (reframed 2026-06-18) · **Status:** CHEAP-SCREEN CAMPAIGN COMPLETE; binding
constraint REFRAMED to CONTENT (§1a). Built+validated: investigator de-cap (default), query-enum
instrumentation, soft dimension-gating (validated → NEGATIVE, parked off). Retrieval precision =
localized + exhausted. The compounding LOOP is the one remaining live test — NOT YET RUN (awaiting
green-light). Consolidates round-7 + round-8 (§10) + the round-9 cheap-screen campaign (§1a, §5).
**Decision:** v7 is the **final memory-RESEARCH iteration**. Build the best complete, principled
instrumented system we can, run one final measured run, and **pre-commit to a stopping rule**: if it
doesn't lift the verified proxies, the instrumentation localizes *why*, and the remaining fix is
either too hard to build or too costly to verify — we **stop** (then freeze → ship/frontend). "Stop"
= stop iterating on the memory architecture, NOT stop the repo.

> Reads alongside: the literature v7 report (external, literature-grounded — keep its synthesis, apply
> the corrections below); `evidence/phase_b/procedural_memory_experiment.md` (other agent's
> overlapping design); `evidence/memory_system/effectiveness/decision_replay/` (the harness);
> `evidence/prompt_claims_audit/` + `evidence/extraction_selection/` (this session's findings).

---

## 1. Why v7 exists — the two failure modes the static measurement could not surface

Everything to date measured a **static, one-shot-extracted store**: the v6 A/B ran `--no-memory-dump`,
seeding read-only from a frozen store mined from 20 fixed memory-OFF games. That is **not a learning
system** — it's a retrieval index. So "memory doesn't help / SP trends harmful" is a verdict on a
*non-learning* store. Two structural failure modes follow, and the real premise of memory (that it
*compounds*) was never on trial:

1. **No adaptivity / compounding.** The store never updates during the eval → bad lessons never
   de-rank or stale out; the agent keeps repeating the failure captured by old memories.
2. **Single-game extraction bias.** Extraction sees one transcript at a time → can't tell good play
   from bad (no cross-game outcome signal). The only cross-game step is dedup (redundancy), not "which
   lesson correlates with winning."

Plus an **orthogonal, prompt-authored cap**: the investigator concealment steer capped the town's
highest-value channel — **now de-capped by default** (§2, §5-G1). A perfect store can't fix a capped
substrate, which is why this had to be fixed at the prompt, not in memory.

---

## 1a. ⭐ REFRAME (2026-06-18) — the cheap-screen campaign relocated the binding constraint: CONTENT, not retrieval

The full cheap-screen campaign (§5: G1–G3 + gating-efficacy + leverage-anchor + the BUILT-and-VALIDATED
soft dimension-gating) localized where v7 lives or dies — and it is **not retrieval**:

- **Retrieval precision = LOCALIZED + EXHAUSTED → PARKED.** Every retrieval-side lever is closed or
  neutral: rerank ≈ raw (reordering the top-k doesn't move outcomes); the LLM reranker *already* judges
  the top 10/15's relevance, so "precondition matching at retrieval" is the same family, already-tried;
  structured dimension-gating is **flat (Δ−2% not_relevant, LLM-judge replay n=24)**; and the agent
  *already* judges applicability inline (`memory_applicability`) while full-coverage doesn't hurt — the
  noise is already handled. Surfacing/ranking is not the cap. **No more retrieval-side screens.**
- **The decisive tell:** following the *relevant* (agent-deemed-applicable) memory STILL doesn't improve
  decisions (G3a; the v6 headline). If even applicable content doesn't help, the cap is **CONTENT
  QUALITY** — the store is mined from bottleneck-capped play, so retrieving it *better* only surfaces
  capped lessons faster.
- **→ The binding constraint is the STORE'S CONTENT** (failure modes #1 no-compounding + #2 single-game
  extraction bias), which is exactly what the **compounding loop** targets: self-correcting content via
  realized-outcome credit + decay, on-policy on the de-capped substrate. That is the one remaining LIVE
  test; retrieval precision is a closed negative chapter.
- **What v7 keeps** (the content levers, all upstream of retrieval): credit by realized OUTCOME, not the
  agent's override (G3a); extraction SELECTION anchored on leverage-DECISIVENESS so fewer capped/
  incidental lessons enter the store at the SOURCE (leverage-anchor screen); the offense/discussion
  channel is creditable (G3b). Retrieval stays RAW — the `dimension_gating` knob exists but stays OFF
  (screened ~null). The loop's whole job is to improve CONTENT.
- ⚠ **NOT YET RUN (user, 2026-06-18):** the compounding loop IS the paid test; cheap evidence is
  exhausted, but it awaits green-light. Do not launch it.

This sharpens, not contradicts, §1b: the trust stack's layer 2 (extraction selection) + layers 3–4
(credit + consolidation) ARE the content machinery; the campaign just showed layer-0/retrieval is sound
enough and the action is all in content. Read §1b's build order with "retrieval precision" struck out.

---

## 1b. The TRUST STACK (first-principles) — why the build order is what it is

The three things v7 must earn trust in — **credit assignment**, **extraction (the right memories)**,
and **consolidation** (promote/reinforce · demote/decay · evict/forget stale · surface relevant by
recency+utility) — are NOT independent. They are a **dependency stack** under one **transverse
precondition**. You cannot trust a layer until the one beneath it holds. We can't "trust" the current
system mostly because two of the three *don't exist yet*, the one that does is half-validated, and the
precondition is unverified.

- **0. PRECONDITION — is there signal above noise?** Is a single decision's outcome attributable above
  luck? If the game is luck/competence-dominated at the decision level, NO credit signal exists, NO
  extraction selection can be validated, NOTHING can be correctly promoted — regardless of build
  quality. This is **G2 (separability)** — now TESTED: **PASS** (§5-G2), every faction ≥1 separable
  channel; it's a DIAGNOSTIC that localizes prompt caps, not a channel-pruner (§10 guards prevent
  spiraling). It gates all three at once.
- **1. SUBSTRATE — what's mined.** Extraction faithfully mines whatever happened; if the prompt caps
  the play (investigator concealment), you mine capped play. Garbage-in sits BELOW extraction.
  *Status: fix SHIPPED — the neutral investigator block is the DEFAULT substrate (2026-06-18); the
  capped version is behind `WW_INVESTIGATOR_PROMPT=baseline`. v7 generates on the de-capped substrate.*
- **2. EXTRACTION — the right memories.** Half trustworthy: **labeling is faithful** (`net_verdict`
  calibrated to outcome, +0.84), but **selection is not** — it's an OUTCOME HALO (can't separate a
  pivotal winning move from one that rode the win), **single-game** (can't see which lessons recur),
  and **quota-distorted** (fixed 4–8/role). *Status: labeling ✓, selection ✗.*
- **3. CREDIT ASSIGNMENT — did this memory help?** Mostly DOESN'T EXIST yet: we HAVE the usage signal
  (EvalCase verdict→memory join) + the deterministic per-decision reward (decision_scoring + join), but
  nothing materializes decision→outcome, writes it back, or uses it. And even once built, an
  **endogeneity confound** remains (follow/override is the agent's choice → mixes memory-quality with
  agent-skill; matched adopt-vs-not reduces, doesn't kill). *Status: parts ✓, loop ✗ — the credit
  OBJECTIVE (what "helped" means) + the applicability split are specified in §10 (round-8).*
- **4. CONSOLIDATION — promote/demote/decay/evict.** Entirely OPEN-CIRCUIT: the count fields exist but
  nothing POPULATES them from live outcomes (store frozen by `--no-memory-dump`), retrieval never READS
  them to rank, and there is NO decay / eviction / recency window (why stale wolf memory just sat
  there). And it **can't be trusted until #3 is** — you can't promote/demote on a confounded signal.
  *Status: does not exist.*

**The stack IS the build/trust order, bottom-up:** G2 (signal?) → fix substrate (prompt) → fix
extraction selection (leverage-anchor + cross-game) → build credit loop (join + handle endogeneity) →
build consolidation (decay/promote/evict on the credit signal). This is why the read-side block leads
with **G2 + the credit-join instrumentation**: G2 checks the precondition; the join is the first honest
measurement of whether credit has recoverable signal before consolidation is built on top of it.

---

## 2. What this session VALIDATED (the findings v7 builds on)

- **Prompt-claims audit** (`evidence/prompt_claims_audit/`): the hand-authored PLAYSTYLE tactics were
  never held to the facts-only bar. Tested two: **investigator "conceal / let consensus build" =
  FALSIFIED** (caps the investigator→lynch transmission chain; provenance-suppression watched
  directly); **wolf "blend with majority" = VALIDATED** (r=+0.20 p=.003 n=220 prior; +0.16 p=.07 v6ab).
  → **investigator de-cap is now the DEFAULT substrate** (2026-06-18): the neutral block ships by
  default; the old capped version is runnable via `WW_INVESTIGATOR_PROMPT=baseline`. This is a
  CORRECTNESS FIX (removing a falsified steer), NOT a treatment — we do NOT A/B it standalone and do
  NOT assume it changes concealment; whether the agent conceals more/less is for MEMORY to learn from
  outcomes. ⚠️ It changes generated play → **do NOT seed v7 from the old capped-play memory** (stale, same as the wolf
  threat-brief). v7 doesn't re-mine a static store — the **loop rebuilds the store on-policy** on the
  de-capped substrate (observations extracted per game as it runs). Reframe: garbage-in
  root is one layer upstream — **prompt tactic → play → extraction → memory**.
- **net_verdict = OUTCOME HALO** (`evidence/extraction_selection/`): extraction's hindsight verdict is
  strongly calibrated to `role_faction_won` (sep +0.84, every role) — so outcome-conditioning is real,
  but it's "did your side win?" stamped on every action, NOT "did THIS move matter?" Validates
  *labeling*, not pivotalness *selection*. → steer **selection** with a deterministic leverage anchor;
  never content; don't turn-scope (see §4).
- **Procedural channel = `strategy_points`, already wired**; the v6 A/B tested **single-game** SP
  (undeduped v6_1) → SP-alone *hurt* the deceiver, synergy (obs cross-check) rescued. **Cross-game
  synthesized SP is untested.** SP is a distillation OF observations → inherits substrate bias.
- **Credit data mostly exists, the loop does not.** `EvalCase` already carries the verdict→SP join
  (`strategy_verdicts` + `strategy_index_to_key`), the action, the board, the candidate pool.
  Deterministic per-decision reward is computable by **joining EvalCase → batch record** (roles,
  resolutions) via `decision_scoring`. Missing: (a) materialize decision→outcome utility per memory,
  (b) write it back, (c) use it in retrieval rank + synthesis (strengthen/decay/evict).
- **MMR exists** (`Agents/memory/retrieval/filters.py`) — a disabled knob, not a gap. Reconcile-on-
  merge **dedup fix** already landed (`operations.py`).

---

## 3. The v7 system (the build)

**A. Instrumentation (the read) — mostly have it.**
- `EvalCase` (per-decision information set + retrieval + verdicts + action) — built.
- `decision_scoring` deterministic per-decision proxy (vote correctness, target-removed, parity,
  survival) — built; join to batch record.
- **Deterministic leverage signal** per turn (de-luck proxy / `is_swing` / `decision_scoring`) — the
  outcome-independent pivotalness measure.
- **Discussion act-detectors** (new, small library — see §6): parse acts, score by vote consequence.

**B. Credit assignment (as good as we can).**
- **Votes / night actions:** deterministic matched adopt-vs-not reward (followed-vs-overrode at similar
  boards) — the clean, free signal. Replaces `net_verdict` (single-game hindsight) with cross-window
  measured utility.
- **Discussion:** lagged, collective downstream vote outcome — honestly the noisiest channel; credit
  it via the day/vote it feeds (the act-detectors do this per act).
- **Valenced-delta reward** (other agent's procedural-memory doc, its §10a — not this plan's §10): cheap subset is game-state-derived
  (target-removed / survival / parity) → free; LLM-read dims (heat/standing) = medium tier.

**C. Self-learning loop (the premise test).**
- **Observations = continuous episodic:** extract per game → dedup into store → available next game.
- **SP = periodic procedural:** synthesize from accumulated obs clusters **every 5 games**
  (`cluster_synth`), re-distilled over the growing base. Retrieved every decision (synthesis is the
  slow clock, retrieval is continuous).
- **Credit feeds back:** utilities up/down-rank rules at retrieval AND drive synthesis decisions
  (strengthen / insert low-trust / decay / evict). This is what makes bad memories stale out
  (failure mode #1) using an objective cross-window signal (failure mode #2).
- Rolling recent-window for non-stationarity.
- ⭐**Synthesis-as-built is HALO-KEYED (eyeballed 2026-06-19, `sp_synthesis_quality_check.py` + manual
  read of `v6_1_sp_cluster`):** cluster-synth weights directives by the cluster's outcome spread, but the
  outcome is the obs' haloed `net_verdict` → it optimizes the halo, not de-luck lift. Result is
  **faction-split**: synth FLIPPED the town passive-loser ("abstain"→"force a resolution") but REPRODUCED
  the SK passive-loser ("blend/abstain", a −0.30/79-follow credited directive) — self-corrects where
  halo≈de-luck (town), fails where they decouple (wolf/SK). ⇒ the loop's (a)+(b) de-luck credit is MOST
  needed on **deceiver cells**; a go/no-go should watch them specifically. This is the concrete change the
  loop makes: feed de-luck credit into synthesis/prune, *replacing* the halo-weighting.
- ⭐**CREDIT-AWARE SYNTHESIS VALIDATED (2026-06-19, `synth_deluck_ab.py`, pro, READ):** feeding the realized
  de-luck track record (ledger) into synthesis + asking for a CONDITIONED directive BEATS both halo-synthesis
  (which reproduces the SK −0.30 blend loser) and pure-prune (the unconditioned top survivor) on the
  decoupled SK day_vote cell; neutral on night (no decoupling). The de-luck signal MUST be realized credit,
  not an LLM "decision-quality" re-judge (unvalidatable for deceivers). ⇒ synthesis-beyond-prune earns its
  keep via the conditioning, on the deceiver cells where halo⊥de-luck.
- ⚠**PRODUCTION-COST (loop-design requirement):** pro synthesis ≈40s/call; full-store SERIAL ≈30-60 min,
  every 5 games = untenable. The loop's synthesis MUST be **incremental** (only cells with new obs) +
  **concurrent** (independent calls → ~3-5 min at 16 workers, proven) — pro per-call but FEW, PARALLEL
  calls. ⭐**RESOLVED: flash-lite synthesis ≈ pro** (full A/B, both SK cells: same active gradient on the
  decoupled day_vote, avoids the blend loser; ~3× faster). ⇒ pro is NOT needed at synthesis (marginal
  top-up only); **loop synthesis = flash-lite + incremental + concurrent → seconds/cycle, cost concern
  dissolved.** (True followed-and-helps still = the loop.)
- ⚠**EPOCH-stability caveat:** all credit verdicts (incl. the deceiver-split above + the b1 prune) are
  **v6ab-conditional, not laws** — held-out +0.54 proves SAMPLE-stability, NOT epoch-stability. Board-
  observable variation → carry the condition (C-ii) + slice credit; hidden epoch variable (model vintage)
  → re-credit per epoch (the rolling window). The b1 prune is epoch-PROVISIONAL (kept reversible); a v6ab
  validation does NOT transfer free → the loop must **re-validate in-epoch**, treating prior credit as a
  hypothesis it re-tests on-policy, never a fixed prior.

**D. Extraction selection — anchor, don't rewrite.** Keep the whole-game omniscient pass (validated
labeling + multi-day causal chains); inject the deterministic leverage signal as **anchors** and swap
the 4–8 per-role quota for a **leverage-derived budget**. Steer selection by facts, never the lesson.
GATE: extraction prompt conditions Phase B gold labels → deliberate versioned experiment, sequenced
with labeling, not a casual tweak.

**D-anchor — SETTLED (2026-06-19): leverage = soft prior, NOT a budget, NOT a whitelist.** ⭐**Screen
result (`extraction_quota_screen.py`, RAW v6_1): the quota is NON-BINDING — mean 2.78 obs/game-cell,
max 6, 98% BELOW the 6-floor, 0 near-restatements. The extractor UNDER-delivers; there is no padding.**
So the anchor's job narrows to ONE thing: **kill the self-judged-pivotal halo** — replace the extractor's
outcome-based sense of "pivotal" with a FACT-based one (do-or-die = P(win|miss) floor). The
budget/anti-padding rationale is DROPPED (no padding to fix); if anything, push **recall** (must-cover the
do-or-die turns) since the model errs too-few. It must NOT become a turn-scoped whitelist ("only explain these N turns") —
that re-imposes §344 (loses the multi-day causal-chain pass) and gates discovery. Keep the **whole-game
omniscient read**; flag do-or-die turns as **must-cover** while **explicitly inviting un-flagged lessons**.
- **Why recall, not precision:** the credit loop (a/b) prunes over-extraction (commission = recoverable)
  but can NEVER credit a lesson that was never extracted (omission = permanent). ⇒ extraction errs
  high-recall; the loop mops up excess.
- **Reinforced by signal incompleteness:** leverage is validated on town day-votes only (§ leverage-anchor);
  night / discussion-framing / omissions are blind to it — a whitelist would blank-out exactly the channels
  c aims to improve.

**D′. (c) EMISSION redesign — the de-halo, and what it must NOT throw away.** The verdict the extractor
writes today (`impact_on_final_game_outcome` = "judged from game end"; `net_verdict`; `outcome` =
net-effect-first) imports the game's LUCK: `corr(net_verdict, role_faction_won) = +0.45` (§6 halo-load).
c strips that luck. BUT the net-effect-first ordering was **deliberately adopted** and is validated — so
the de-halo has three hard constraints from the prior record:
- **C-i — de-halo ≠ de-condition.** The value of the final-outcome lead was never the luck; it was that
  it surfaced the **cost / the causal chain** the immediate framing hid. Evidence: net-horizon framing
  REMOVED the SK harm (`sk_lynched` 0.80→0.63, win 20%→37%, `paired_ab/report_nethorizon.md` 2026-06-12)
  precisely because success/immediate-framed SK entries were **cost-blind**. ⇒ c drops the *luck*
  (faction-won contamination) but KEEPS the **cost + multi-day causal chain + the condition** — write
  "this kill exposed you → lynched 2 days later," NOT "and your faction lost." (This is the de-luck≠de-delay
  point: §6's clean⊥delayed⊥free triangle — keep delay, drop dice.)
- **C-ii — no blanket outcome-horizon; the content must carry the CONDITION.** Outcome-framing is
  **situation-dependent** (`decision_replay` 2026-06-13): for town, net/cautious HELPS when info-starved
  (day-2 +0.167) but cautious was the *game-level* problem → no single horizon wins everywhere. ⇒ c must
  emit the precondition (cautious-when-info-starved vs act-when-threat-clear), not pick one global framing.
  This is the §10c situation-conditioning lever.
- **C-iii — the wolf residual is ADHERENCE, not extraction.** Net-horizon left wolf blending FLAT
  (+0.03, p=0.75) — the wolf ignores the correct lesson (an injection-layer / Phase B item), so c must
  NOT try to fix the wolf via framing. Leave it to the application-adherence work.
- **Success metric** (unchanged): `corr(net_verdict, faction_won)` drops below +0.45 while the
  cost/causal-chain/condition structure fields populate.
- **C-v — RECALL is first-order, de-halo is second (user, 2026-06-19).** De-luck credit/synthesis/prune
  act only on what extraction captured; **omission is unrecoverable** → "did we capture what's NEEDED"
  gates everything de-halo does. Free reads: extractor is THIN (median 3 obs/cell) but NOT temporally blind
  (spans early/late/parity). "Captures what's needed" is a counterfactual → not free-measurable. ⇒ the
  extraction A/B to run is a **RECALL test** (capture-rate of leverage-flagged turns), NOT de-halo framing,
  **+ a model-capability arm** (2.5-pro vs 3.5-flash vs 3.1-flash-lite — the loop re-extracts every game so
  extraction-model cost dominates its bill). Full spec + kill-tests + small-slice pre-gate:
  `extraction_coverage_ab_spec.md`. ⚠ flash-lite breaks on `str|None` dims (all-required variant needed);
  recall metric scoped to town day-votes (leverage validated there only); epoch-conditional + freeze-gated.
- **C-iv — CONSUMPTION MODEL changed → split the de-halo by surface.** The agent is now fed the
  **synthesized SP as the directive** and **observations as fact-check / case evidence** that correct or
  `override` the rule (`Agents/prompts/memory/context.py` synergy instruction: "let the specific evidence
  in the observations correct the general rule"). The framing experiments (`decision_replay`) were
  measured when *observations were the directive* — that regime is GONE, so:
  - **Steering de-halo + situation-conditioning (C-ii) migrate UP to SP SYNTHESIS** (b2 / the loop's
    synthesis prompt) — the SP is what steers now, and it inherits the halo from the obs it's distilled
    from. De-halo + "carry the condition" is mainly a synthesis-prompt job.
  - **C-i (cost + causal chain) STAYS on the observation emitter and gets MORE important** — an obs's job
    is now to let the agent check "does this rule's premise hold on my board, and did it backfire?"; that
    `override`-triggering evidence is worthless without the cost/causal-chain.
  - **Observation C-ii de-emphasizes** to: accurate **situation dimensions** (board-matchability) + clean
    facts. The obs no longer has to win the framing fight; it has to be a precise, matchable, cost-aware
    case.
  - ⚠ The `decision_replay` framing result is therefore a **re-validate target under the new regime**, not
    a transferable given.

**D″. (c) ↔ discussion tagger — one project, likely two calls.** The (d) per-round discussion tagger is
the **discussion slice of c's emission** (same omniscient-hindsight job), NOT a separate effort — but it
likely stays a **separate cheaper (flash-lite) call that FEEDS the extractor**, because of the granularity
(per-round vs whole-game-per-cell) + model-tier mismatch. Rule: **don't pay for two omniscient reads of
the same game** — the tagger's structured discussion output is an INPUT to the extraction pass. Lock the
one-call-vs-two fork inside c's build, not now.

**E. Dedup + reranking (proper).** Reconcile-on-merge dedup (landed) so structured fields survive;
re-enable MMR + reranker as **tested knobs** (screen on frozen eval-cases first). Cross-game dedup
gives SP the cross-game basis single-game SP lacked.

---

## 4. The final run (experiment design)

- **Arms:** `off` (memory-off, **parallel/cheap**, concurrent same-epoch fixed baseline) · `ob-loop`
  (sequential) · `ob+sp-loop` (sequential + periodic synth). Only the loop arms are sequential — that's
  the real cost; baseline is cheap. Run baseline at **matched cadence** so it sees the same epoch
  trajectory (de-confounds within-arm drift — the slope difference, not the level, is the result).
- **Lead with `ob-loop vs off`** (the premise: does compounding help on the non-harmful substrate?).
  `ob+sp-loop vs ob-loop` = SP's marginal value (the rescue question, secondary). Don't let SP gate the
  premise.
- **Measure the SLOPE on VERIFIED MONOTONIC proxies** (town decision-quality basket; wolf-blend) —
  per-decision → many points/game → a slope-to-plateau detectable at **~50–60 games/branch** where
  win-rate would need hundreds. Win-rate is confirmatory only.
- Same-epoch concurrent; raw + then MMR as a screened knob.

---

## 5. Pre-registered GATES (cheap, before the expensive sequential run)

Run these first; only commit the loop if they pass. None is confounded by SP quality.
- **G1 — investigator de-cap = DONE (now the default substrate), NOT an A/B.** It's a correctness fix
  (false steer removed); the neutral prompt ships by default (`WW_INVESTIGATOR_PROMPT=baseline` runs the
  old one for comparison). No standalone run — and **no re-mine step**: the loop builds the store on-policy on the de-capped
  substrate from cold (§2), so G1 leaves nothing to prep. Conversion lift, if any, is measured
  as part of the memory run via the conversion metrics, on the de-capped substrate.
- **G2 — separability / signal-to-noise** (the report's Gate 0, channel-agnostic): is per-decision
  outcome attributable above luck at all? If decision-level outcomes are pure noise, no loop on any
  channel gets traction → stop here.
  → **RESULT (2026-06-18, `g2_separability.py`, 180 v6ab games, zero spend): PASS per-faction, but
  CHANNEL-SPECIFIC — G2 is a channel SELECTOR, not just go/no-go.** Each channel = a role's de-luck
  decision proxy vs ITS faction's outcome, game grain, permutation luck-null. SEPARABLE (signal to
  compound on): town day-vote r=+0.56 (p=5e-5; decision grain r=+0.33, threat-hit vote → P(win) .55 vs
  .20, Δ+35pp), healer-night block-a-kill r=+0.42 (p=5e-5), SK-night kill-lands r=+0.26 (p=6e-4), wolf
  day-blend r=+0.22 (p=3e-4). NULL: **investigator-night find-evil r=+0.00 (p=1.0)** — the transmission
  bottleneck quantified (finding ≠ winning; credit investigator via the DAY find→lynch, never the night
  find); wolf-night hit-power r=−0.11 (targeting is luck/noise; wolf's signal is day concealment, not
  night kill); vigilante-night (n=53) + SK-anti-wolf underpowered. **G2 is a DIAGNOSTIC that
  localizes PROMPT CAPS, not a selector that prunes channels (user, 2026-06-18). KEEP ALL channels in
  the loop — it's the only signal each role has.** Underpowered (vigilante-night, SK-anti-wolf) = keep,
  the loop generates more games to resolve. NULL ≠ noise: investigator-night r=0.00 is a TRANSMISSION
  cap (a find that's never acted on) → fix at the PROMPT (the de-cap, cap-removal facts-not-tactics),
  after which the signal materializes; wolf-night-targeting null → same, a prompt-cap question, not a
  reason to drop wolf night memory. The §10 guards (offense floor / applicability funnel / leverage
  weighting) — NOT channel-pruning — are what keep a misleading signal from spiraling (§10d), so all
  channels stay in safely. Endogeneity caveat stands (permutation rules out "no relationship," not full
  causation; matched adopt-vs-not in the credit loop handles it). ⭐**LIVE-MIGRATION SMOKE PASSED same day:** 1 all_enabled game on the v6
  live write-path wrote 36 fresh obs, all with `dimensions` + gate enums (932→968 in throwaway store) —
  `extract_postgame_per_cell` validated end-to-end.
- **G3 — free read-side checks on v6ab dumps:** verdict-validity (does override beat follow at matched
  boards → is the decay signal real?); target-advocacy detector (is town discussion steering votes
  toward threats at all?); **retrieval applicability/precision** (re-retrieve frozen eval-cases with
  dimension-aware gating + rerank/MMR → does the v6-measured ~50% not-relevant rate drop? — the #1
  waste, see §10b). Mechanism preconditions, not premise tests.
  → **G3a RESULT (2026-06-18, `g3a_verdict_validity.py`, v6ab eval-cases, zero spend): decay-on-override
  is DEGENERATE, not weak.** Per-SP verdict distribution across ALL arms: override **0–5%** (1% typical;
  5% only in the skboth synergy arm *designed* to drive overrides), not_relevant **30–62%** (town
  day-vote 69%), agents follow ~99% of *applicable* SPs. Verdict-validity is untestable — no override
  variance (town day-votes: 3 override decisions vs 334 follow). Consequences: **(1)** decay-on-override
  not viable → the credit/decay signal must be the realized de-luck OUTCOME of FOLLOWED decisions
  (`decision_scoring`), NOT the agent's override choice — rewrites §3B (matched adopt-vs-not needs
  adopt-variance we don't have). **(2)** §10b confirmed/sharpened: not_relevant DOMINATES → retrieval
  precision is the #1 lever, upstream of content credit; most retrieved SPs never reach the content
  stage. **(3)** follow-bias (~99% follow of applicable) despite v6 showing SP HURTS → agents don't
  catch bad advice via override → §10d spiral risk; the guard is grading by realized outcome, not follow.
  → **G3b RESULT (`g3b_target_advocacy.py`, 180 v6ab, zero spend): the OFFENSE channel is REAL,
  creditable, separable.** Town advocacy (`addressed_targets.stance=accusation`) → lynch 58% vs 12%
  unadvocated (Δ+0.46, p≈1e-80); advocated-and-lynched were threats 72% vs 61% base (Δ+0.11, p<0.01);
  per-game town advocacy-precision ↔ town_won r=+0.45 (p=2.5e-9). → v7 can credit DISCUSSION via the
  deterministic advocacy shadow; the §10a offense term works. (SCOPE: structured advocacy only;
  investigator reveal-before-death needs the §6 reveal act-detector — deferred.)
  → **G3c RESULT (`g3c_retrieval_applicability.py`, v6ab eval-cases, zero spend): retrieval precision is
  NOT a knob — the v7 bottleneck.** 7534 SP retrievals, 58% not_relevant; embedding SCORE is BLIND to
  applicability (not_relevant 0.827 vs applicable 0.828, r=−0.04; even top-1 → 48% not_relevant). →
  similarity ≠ precondition-match (rerank≈raw at the applicability level); threshold/similarity-rerank
  cannot cut the dominant waste. **Fix must be STRUCTURED dimension-gating on the v6 enums (like the
  dedup gate) — NOT wired into retrieval yet (v6 left retrieval soft).**

**G3 SYNTHESIS (⚠ SUPERSEDED by §1a — kept for the journey):** signal exists (G2) + offense
creditable/separable (G3b) → v7 has traction; this paragraph then concluded the binding constraint was
RETRIEVAL PRECISION (G3a #1 lever / G3c not-a-knob) and that v7 hinged on wiring structured
dimension-gating into retrieval. **That conclusion was OVERTURNED:** the gating tool was built and the
LLM-judge replay came back flat (Δ−2%, default-OFF), the LLM reranker already judges top-k relevance
(rerank≈raw), and the agent already judges applicability inline — so retrieval is sound-enough and
PARKED. Per §1a the real binding constraint is CONTENT, fixed by the compounding loop, not retrieval.
Read the rest of this G3 block as the (closed) retrieval-precision investigation that led to that pivot.
  → **GATING EFFICACY (`g3c_gating_efficacy.py`, zero spend): structured gating BEATS similarity, but
  criticality alone is modest.** Per-dim marginal not_relevant reduction (matched vs mismatched —
  per-dim, NOT an all-dim conjunction, per the soft-retrieval / don't-hard-gate-everything rule):
  alive_bucket −5pp, is_swing −6pp (both HELP, vs similarity score Δ≈0), dist_parity −2pp (flat, skip).
  So the v6 dims carry applicability signal the embedding doesn't (validates the schema's retrieval
  value), BUT even matched still 56% not_relevant → criticality shaves, doesn't solve. **The bigger
  lever = the SEMANTIC gates (exposure_class / info_landscape_class), untested because the QUERY enum
  isn't persisted. ACTIONABLE (cheap, no LLM): persist the query's structured enums into the EvalCase in
  the live retrieval path → semantic-gating efficacy becomes a FREE screen.** Then (if it gates) wire
  selective soft-gating into retrieval; the paid re-retrieval is the last-resort confirm.
  → **BUILT + VALIDATED → NEGATIVE (2026-06-18).** Built the soft selective gating
  (`Agents/memory/retrieval/dimension_gating.py`, wired in `pipeline.py`/`gating.py` behind a default-off
  knob, 308 tests) + the query-enum instrumentation. Validated via LLM-judge replay
  (`dimension_gating_screen.py`, n=24 held-out town day-votes, regen query → wide retrieve from v6_1 →
  ungated vs gated top-5 → forced applicability judge): gating reordered 23/24 top-5 sets but
  **does_not_apply 38%→36% (Δ−2%, flat), fully_applies 15%→16%, vote_hit 0.33 both.** Even the SEMANTIC
  gate doesn't cut the waste — **dim-match ≠ applicability** (the judge weighs finer preconditions than
  the coarse enums). Knob stays default-OFF (screened ~null, not shipped). **Retrieval precision = a
  LOCALIZED CAP** (G3c bottleneck + gating-efficacy modest + this flat): NOT fixed by structured gating.
  Remaining untested levers: precondition-level matching (= the LLM judge itself, expensive), better
  extraction SELECTION at the source (leverage anchor → fewer noise-prone stores), cross-game
  GENERALIZATION (SP synth). Per the stopping rule: this localizes WHY; strong honest portfolio finding.

- **LEVERAGE-ANCHOR separation** (extraction-selection viability, §2/§3D/§4 — `leverage_anchor_separation.py`,
  180 v6ab town day-votes, zero spend): **the anchor IS viable — via DECISIVENESS (floor), not marginal Δ.**
  decision→outcome coupling Δ=P(win|hit)−P(win|miss) is FLAT across leverage strata (is_swing T/F
  +0.35/+0.37; dist≤1/≥3 +0.35/+0.41) → criticality does NOT rank town-votes by marginal impact (echoes
  the criticality-screen null; town votes are uniformly pivotal-by-Δ). BUT the **P(win|miss) FLOOR drops
  0.23→0.00** at high leverage → a miss is fatal there → leverage cleanly separates DO-OR-DIE turns. So
  extraction anchors on leverage to mine the **decisive** turns (low miss-floor = the decision determined
  the game), independent of who won → fixes the net_verdict halo in the IRREVERSIBILITY sense, not by
  impact-ranking. Caveat: town day-votes only; night channels + de-luck per-decision leverage untested.

- **QUERY-ENUM INSTRUMENTATION shipped** (2026-06-18, eval-only, freeze-safe, 303 tests): the live
  retrieval path persists the query-side structured dims into `EvalCase.situation_dimensions` (parallel
  to `situations`) → the semantic-gating efficacy screen (exposure/info_landscape query↔SP match →
  not_relevant) becomes FREE on future games. Not retroactive (existing v6ab dumps lack it).

**CHEAP-SCREEN CAMPAIGN COMPLETE (2026-06-18, all zero-spend on existing dumps):** G1 ✅ substrate ·
G2 ✅ signal exists (channel-specific diagnostic) · G3a ✅ decay→realized-outcome (override degenerate) ·
G3b ✅ offense channel creditable+separable · G3c ✅ retrieval precision = the bottleneck (similarity
blind) · gating-efficacy ✅ criticality modest / semantic untested · leverage-anchor ✅ viable via
decisiveness. **Net: the v7 premise is viable (signal + creditable channels + a workable extraction
anchor); the binding constraint is RETRIEVAL PRECISION, whose semantic-gate fix is now instrumented for
free.** The gates turned "does memory work?" into one sharp build bet.

---

## 6. Discussion judging — the measurement frontier

Discussion is the bulk of day strategy but resists scoring (diffuse / lagged / collective /
counterfactual — same root as town-memory flatness). **Don't score it intrinsically; score it by the
vote it feeds.** Principle: **parse acts (cheap, low-judgment), score by deterministic consequence,
NEVER ask an LLM "was this message good"** (plausibility bias). Tiers:
1. Whole-day attribution (free): day-talk → that day's lynch correctness.
2. **Act-detector library** (high-ROI, generalize the transmission metric): role-claim,
   confirmed-read assertion (built), target-advocacy (advocated→lynched & was-threat?),
   defense-under-pressure, herd-vs-lead. Parse `{advocated_target, claimed_role, asserted_read}` per
   message, score by downstream. Most discussion is non-load-bearing — score only the vote-moving acts.
3. Counterfactual whole-day replay (causal, expensive): snapshot, remove/alter a message, resample the
   vote. **Out of scope for v7 (future work)** — reserve for specific high-stakes validation only.
4. LLM-judge: last resort, only where no deterministic shadow, always validated vs a deterministic
   anchor.
Discussion turns inherit the **leverage of the day they feed** for the extraction anchor.
**Per-message credit determination (social-state transition × act × seq, good-enough scope) → §10e.**

---

## 7. Scope discipline — what v7 does NOT do

- No turn-scoped extraction rewrite (loses validated causal-chain pass).
- No content-steering of lessons (facts-not-tactics; same line as the registry threat-brief).
- No big-N win-rate chase (epoch drift killed cross-run comparability — the Phase C wall). The slope is
  measured WITHIN one epoch vs a concurrent baseline; **flat = the answer**, NOT a cue to escalate to
  hundreds of games.
- No LLM intrinsic quality judge for discussion.

---

## 8. The pre-registered STOPPING RULE (the agreement)

- **WORKS** → positive slope on a verified monotonic proxy vs the flat concurrent baseline, gates
  passed. Then: dedup/rerank tuned, freeze, ship.
- **DOESN'T WORK** → flat slope despite gates passing. Then the instrumentation must **localize the
  cap** (substrate / transmission residual / no recoverable credit signal / content ceiling). If the
  remaining fix is **structural-and-too-hard-to-build OR too-costly-to-verify**, we **STOP** iterating
  the memory architecture and write the negative result as the finding (with the mechanism). We do NOT
  escalate N or spin a v8.
- **The portfolio story is strong either way:** "built a static index → proved it's not a learning
  system → built+measured the real compounding loop with proper credit assignment and instrumentation →
  here's whether it compounds, and if not, exactly why." That beats "memory helped/didn't."

---

## 9. Coordination + sequencing for tomorrow

- **Heavy overlap with the other agent's active phase_b work** (`procedural_memory_experiment.md`,
  `decision_replay`, `criticality_screen`) on this branch — v7 is the *integrating* plan, not a
  competing one. Sync before building so credit-loop / SP-synth / criticality aren't duplicated.
- **Sequence:** G1 (prompt fix) + G2 (separability) + G3 (free checks) → decide → build the credit
  loop on **observations first** → final run (slope) → SP arm → stopping-rule decision.
- **Already in `main`-ish (this branch):** reconcile-on-merge dedup, registry threat-brief, dead-channel
  removal + verdict→SP join, faction_survivors, transmission metric, investigator de-cap (neutral = DEFAULT; baseline behind `WW_INVESTIGATOR_PROMPT`).

---

## 10. Round-8 refinement (2026-06-18) — the memory VALUE FUNCTION (what a strategy update optimizes)

Sharpens §3B (credit) and §6 (discussion). Round-7 named the credit LOOP (join → write-back →
consolidate); this names the **objective the loop optimizes** — what a `strategy_point` update is graded
*against* — plus two failure modes the binary follow/override framing misses. Motivating evidence: the
static 20-game store distilled **passive SK** and tanked win-rate (wolf/SK null-to-negative,
[[project-episodic-memory-remaining-work]]) — a worked example of optimizing the wrong signal.

**The spine (one signal, four guards — each guard = a named failure). The whole design is small under
the sprawl:**
- **Signal:** grade a memory by its **de-lucked proxy contribution**, never win/loss. (Win/loss = the
  §2 halo + a 1-bit/high-variance label at N≈5–10 + no credit assignment.)
- **Guard 1 — offense/defense basket + floor** → defends against the **passive-SK Goodhart**.
- **Guard 2 — applicability funnel** → defends against **blaming content for a retrieval failure**.
- **Guard 3 — leverage weighting** (§3A/§4) → defends against **crediting trivial moments**.
- **Guard 4 — cross-window persistence + decay + on-policy** → defends against **small-N overfit +
  off-policy mismatch**. (The 20-game run was off-policy: distilled from memory-OFF play, injected into
  memory-ON play — the credit signal never saw the behavior it steered. The loop must re-generate
  on-policy each round; §3C's rolling window is the non-stationarity half of this.)

### 10a. Guard 1 — the offense/defense basket (sharpens §6's act-detectors)
A discussion move lives on two axes, and the credit signal needs **both** so it can't collapse to
silence. The §6 act-detectors slot onto them:
- **Offense / influence** — did the move steer the room: target-advocacy (advocated→lynched & was a
  threat), investigator conversion (find→lynch), herd-vs-lead.
- **Defense / concealment** — did it manage heat: `suspicion_drawn`, SK `unconditioned_blending`,
  defense-under-pressure.

**`suspicion_drawn` is the passive trap, formalized.** It is literally "don't draw heat"; as a solo
minimize-target it **re-derives passive SK by construction.** It enters only **bracketed**: (1)
offense-paired in one basket (going silent tanks the offense term), (2) leverage-weighted (shedding heat
at a dead moment ≈ 0), (3) **contrastive** — matched-board follow-vs-override strips its two standing
caveats (opponent-contamination of heat, and the survival↔win tautology).

**Weights: fit, don't guess.** Regress each role's de-luck composite on its offense-component vs
defense-component → the coefficients ARE the per-role weights (villager offense-heavy; wolf ~balanced;
SK *descriptively* defense-heavy).

⚠ **REVISED 2026-06-19 — NO offense floor (dropped; it imposes a prior).** A hard "offense must be
non-zero / non-compensatory" rule forces the agent off the true optimum *if passivity genuinely wins* —
the outcome-halo sin pointed the other way. The v6 passive-SK came from crediting a **surrogate**
(`suspicion_drawn` / survival), NOT from the absence of a floor → the guard belongs on the **metric, not
the policy.** Three mechanisms catch the collapse WITHOUT a prior: (1) credit anchored on the de-luck
**OUTCOME** proxy, never `suspicion_drawn` solo; (2) **leverage-weighting** — regime-sensitive:
passive-early scores neutral, passive-into-a-pivotal-spot-and-lynched scores negative; a flat floor is
regime-blind; (3) the **maturity gate** — no separable signal → neutral, don't penalize. G2 backs this:
the SK's separable winning channel is **kill-lands (offense, r=+0.26)** → a lean toward acting THERE is
data-found, not our bias; SK day-discussion was NOT separable → no signal → **impose nothing** (forcing
balance on a no-signal channel invents the signal we fear faking). **Offense/defense is DEMOTED to a
DIAGNOSTIC** — a lens to catch "is a heat surrogate being optimized instead of the outcome?", NOT a
constraint on play. The defense-only-cluster flag survives only as that diagnostic, never an automatic
penalty.

**Granularity:** `suspicion_drawn` is a game-level aggregate → too coarse to credit one point. The
**per-point credit grain is the localized `exposed→safe` transition** (per-day exposure tag +
addressed_targets/seq); the game-level `suspicion_drawn` becomes the validator a synthesized
heat-shedding rule must correlate with.

⚠ **DENSITY GUARD (2026-06-19) — keep credit COARSE; this per-point dimensional grain stays OFF for now.**
Two different things hide in §10a and only one survives the data we have (median ~3 follows/SP):
- **Aggregate weight-fit ("Weights: fit, don't guess") = ON.** Regress a role's de-luck composite across
  ALL its decisions (hundreds of points) → the per-role offense/defense weights. Pools the big pile,
  ignores any single SP → reliable. These weights set the **drop/revise thresholds** (§3B / consolidation).
- **Per-point credit at dimensional grain (this paragraph) = OFF until thick.** Grading ONE point on its
  offense-vs-defense (or any dimensional) sub-reason = slicing ~3 follows into ~1 per dimension → noise.
  This is the **same per-SP subdivision the consolidation design cut (T2 dimension-split)**; letting it back
  in re-introduces exactly that overfit through a different door (you'd "discover" 1-follow coincidences and
  drop/rewrite good advice for a made-up reason). Doubly blocked anyway: the `exposed→safe` grain is the
  **discussion/defense axis** → needs **(d)** the tagger to exist AND many loop cycles for density.

**One-line rule:** set the general weights from the big pile (fine); score each SP as ONE overall number
via those weights (fine); **never grade a single SP on sub-reasons until it has been used enough times to
earn it** (not for many loop cycles). So §10 and the simplified consolidation triggers AGREE — as long as
per-advice grading stays coarse.

### 10b. Guard 2 — the applicability funnel (sharpens §1b.3 / §3B: "useless" ≠ "overridden")
The follow/override binary conflates two failures with two different owners and two different fixes:

| Verdict | Means | Blames | Fix |
|---|---|---|---|
| **not-relevant** | the situation didn't hold here | retrieval / situation-scoping | re-scope the situation field or stop retrieving it — **NOT** the lesson |
| **override** | held, agent beat it | content | correct / decay the rule |
| **followed → outcome** | held, taken | realized value | promote / keep |

Lumping **not-relevant into "didn't follow → bad advice" is a second Goodhart** — you'd down-weight or
"correct" good advice against a *retrieval artifact*. **Applicability must gate ahead of any content
credit:**
```
retrieved → applicable? —no→ retrieval/scoping problem (NOT a content verdict)
              │ yes
           followed?    —no→ content suboptimal (override → correct the rule)
              │ yes
           pivotal?     —no→ useless-by-triviality (leverage ≈ 0; why Guard 3 stays in the loop)
              │ yes
           proxy delta  ——→ the only place the rule earns realized credit
```
The schema already carries the split (`not_relevant_count` / `override_count` / `follow_count` on
`StoredStrategyPoint`, labeled by the agent's `memory_applicability` verdict); the gap is that the credit
signal must **consume** it — round-7 §3B's "matched adopt-vs-not" reads as binary. Caveat: applicability
is **agent self-report**, so not-relevant can mean *agent-blindness* rather than a true scoping miss —
don't auto-prune on not-relevant alone; cross it with the situation field's specificity (high
not-relevant + a tightly-scoped situation ⇒ blindness, not mis-filing).

**Deeper limit — not-relevant is itself a 1-vs-3 conflation; the table's "not-relevant → retrieval/scoping"
is the right *default*, not a clean read.** Refusing to blame content (the second Goodhart, above) is
correct, but the leftover bucket still merges two observationally-identical causes — both render as "the
situation didn't hold": **(1) genuinely inapplicable** — an endgame SP correctly declined in the opening,
exactly what a broad repertoire SHOULD do = HEALTH, not waste; and **(3) a retrieval false positive** —
semantically near, never applicable, the actual precision bug. So **the 58% not-relevant rate (G3a/G3c) is an
UPPER BOUND on retrieval waste, not the waste itself** — the correct-decline share is uncounted, and
"retrieval precision is the #1 lever" is sized against an inflated denominator. Offline, the only separator
is the same situation-specificity cross (a tightly-scoped situation that still goes not-relevant ⇒
false-positive/blindness; a broad situation ⇒ plausibly a correct decline); a clean (1)-vs-(3) split needs
the precondition-level applicability judge (the expensive LLM, the parked retrieval lever). Until then read
the not-relevant rate as *retrieval-waste + healthy-breadth, undifferentiated* — never as pure waste.

### 10c. Net effect on the build order
No new layer — these tighten §3B/§3C/§6: (i) the credit reward is the **de-luck OUTCOME proxy** (the
offensive acts that have signal feed it); the fitted offense/defense basket is a **diagnostic
decomposition, NOT the reward** (REVISED 2026-06-19 — no offense floor; see §10a); (ii) **applicability
is a precondition gate** before content credit (a new branch in the join, cheap — the fields exist);
(iii) the **rule-level passivity flag** is a synthesis-time **diagnostic, not a penalty**. All three are
read-side / offline-validatable on the v6ab dumps before the sequential loop, so they fold into the
**G3** free checks, not a new expensive run.

### 10d. Why the credit signal is central, not downstream — compounding is double-edged
v6's passive-SK was *bounded* because the store was static: the bad "go quiet" SP made the SK passive at
a FIXED rate, never worse round-over-round. The v7 loop removes that ceiling — a self-improving store
**amplifies the credit signal's quality in BOTH directions.** A clean signal converges UP; a mis-credit
("drew no heat → good") drives the SK *more* passive each round — a **vicious spiral a static store
cannot produce.** So the §10a/§10b guards are not layer-3 tuning deferred behind the gates; inside the
loop they are the **safety rails that decide virtuous vs. vicious.** They still ride on the gate
preconditions — **G2** (signal above luck → is there anything to compound on?) and
**applicability/precision** (so the credit telemetry isn't the v6-measured ~50% noise) — those decide
whether the spiral *can* climb; the guards decide which way it actually goes.

### 10e. Discussion credit — the per-message determination (good-enough scope)
For discussion the per-decision signal IS a state-change — the **social** state, not the board, which the
v6 dims already discretize: `consensus_direction` (`opposes → aligns_with_my_read`) is the **offense**
transition, `exposure_class` (`exposed → safe`) the **defense** transition (the §10a axes). The analog of
"the target died" is "the room moved to your read / you shed the heat."

It rides on the **G2-confirmed separable channel**: discussion has no separable *intrinsic* proxy, but the
**day-vote it feeds is separable** (§5-G2: town day-vote r=+0.56 game / +0.33 decision). So per-message
credit is anchored on that downstream vote, never on "was the message good."

Attribute a transition to one message with **only what we already persist** — no new machinery:
- **act** — `{advocated_target, claimed_role, asserted_read, stance}` (stance is in `addressed_targets`);
- **local window** — the social-state delta in the next K turns, not the whole day (partly excludes the room);
- **seq ordering** — did the move PRECEDE the shift (lead, causal-ish) or follow it (blend)? the cheap causal proxy;
- scored **role + ground-truth conditioned** — a villager shedding *undeserved* heat ≠ a wolf escaping *deserved* heat.

**Deliberately good-enough, not perfect:**
- **Counterfactual replay** (remove the message, resample the day — the only *true* causal isolation) is
  **out of scope for v7 / future work**, not the default (§6 tier 3).
- **Grain follows the signal:** if per-message is below noise (likely — discussion is the noisiest
  channel), fall back to **per-act-type / per-day** aggregate. Don't chase per-message precision.
- **One dependency:** the social state must be tagged **per-turn/window** (the dedicated tagger over
  `day_channel`, NOT the selection-gated extractor) to have before/after endpoints.

If discussion credit stays below noise even at the coarse grain, that's a **documented limitation** (§8) —
not a cue to build the counterfactual machine. Take it as far as the cheap proxies reach and stop.

### 10f. Credit SOURCING — the clean⊥delayed⊥free triangle, and how to weight an LLM (2026-06-19)
Three ways to source credit, no two-of-three-free combination:
- **De-luck immediate** (what's built): score the choice vs true roles at that turn. CLEAN (no halo), FREE,
  but MYOPIC — blind to delayed (blend today → caught tomorrow) and omission (had info, died unrevealed).
- **Multi-step deterministic**: extend the credit window to future game events (n-step return). Captures
  DELAY without an LLM, but LUCKIER (de-luck and delay are in tension; window-length = the myopia↔halo dial;
  the terminal extreme = "who won" = the full halo). ⚠ **TESTED + REJECTED (2026-06-19,
  `windowed_credit.py`):** survival-window credit is ORTHOGONAL to immediate decision quality
  (imm↔surv1 +0.14) and DRIFTS to halo with window length (surv1→surv2→terminal = +0.14→+0.37→1.0) — the
  free delayed signal trades cleanliness for delay, confirming the triangle. Don't wire a deterministic
  window; the clean delayed/causal source is the LLM (c2) — and that case is usually a discussion SP →
  (d)-blocked anyway.
- **LLM hindsight**: the only source for causal/omission cases — but its **VALENCE is circular BOTH ways**
  (outcome-aware → halo; outcome-blind → mirrors the agent's own prior = the G3a degeneracy). PAID.

So **never let the hindsight LLM supply raw valence.** Instead:
- **LLM STRUCTURE/FACTS** (omission, causal swing, influence chain) = genuinely additive → **high weight,
  as FEATURES** feeding deterministic credit.
- **LLM VALENCE** = **low, empirically-set weight, de-haloed** — regress out the outcome, keep the residual;
  trust it MORE where it disagrees with the outcome (unambiguously additive), LESS where it agrees.
- ⭐**HALO-LOAD MEASURED (2026-06-19, zero spend, `net_verdict` vs `role_faction_won`, v6_1's 932 obs):**
  corr **+0.45** (moderate — NOT pure halo); P(positive|won)=64% vs P(positive|lost)=21% = **43pp halo gap**;
  but **~22% residual disagrees with outcome** (11% positive-in-loss, 11% negative-in-win) = the additive
  de-haloed signal. → use the residual, not raw, not zero; apply selectively (pivotal/ambiguous decisions).
