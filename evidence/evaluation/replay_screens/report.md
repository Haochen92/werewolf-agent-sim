# Replay Screens — Evaluation Apparatus Report

> **Scope: the apparatus, not the memory verdict.** Covers the two off-line replay instruments that
> sit *below* the whole-game A/B — the per-turn **decision-replay screen** (built, validated) and the
> per-**day** replay (design-only) — and how far each can be trusted. The design conclusions the
> screen fed into (which cheap levers were dead) live in
> [`../../memory_system/effectiveness/decision_replay/`](../../memory_system/effectiveness/decision_replay/);
> the per-day spec is [`../../memory_system/effectiveness/day_replay/design.md`](../../memory_system/effectiveness/day_replay/design.md).
> Lens + skeleton: [`../report.md`](../report.md); ledger: [`../source_map.md`](../source_map.md).
>
> **Verdict: ✅ per-turn screen sound as a TRIAGE tool · ⏸ per-day replay is design-only.** The screen
> is a validated pre-filter for *direction and mechanism* at a frozen board; it is off-policy and
> cannot claim trajectory, magnitude, or win-rate. Its 2026-07-02 hardening closed the one coverage
> hole that mattered — it could not replay a deceiver decision, exactly where the open questions live.

## Objective the apparatus targets

A whole-game paired arm costs ~$15–30 and is exposed to overnight model drift, so it cannot cheaply
answer *why* memory helped or *which* of a dozen candidate fixes is worth building. The replay layer
answers that at a fraction of the cost: freeze one recorded decision, swap only the retrieved-memory
block, regenerate that one action, and score it against the true roles. It is paired at the decision
so role-luck cancels, and it is drift-immune because both arms run in one sitting.

## L1 — the per-turn decision-replay screen

- **Mechanism.** For a frozen board it regenerates a single action under memory-ON vs memory-OFF and
  scores it deterministically (`hit_threat` against the true roles). Judge-free wherever the target is
  a role lookup; two off-headline judges (adherence, coherence) run only on side probes.
- **What it can claim.** Direction + mechanism only. It sees *local* decision quality at a fixed
  history, never trajectory, magnitude, or win rate. Findings are reported tiered as
  direction-plus-mechanism, and the win-rate headline always stays with the paired A/B. A screen
  p-value is never headlined; per-cell N is small (±5–9pp), so a claim earns its keep two ways, both
  N-robust: the cell-level mechanism decomposition, and convergence with an independent cut.
- **Coverage after the 2026-07-02 fix.** The screen was structurally blind to the deceiver side: wolf
  day-votes were excluded, and the action specs lacked vigilante and serial-killer day-votes. The
  hardening pass added those specs, added a `REPLAYABLE_DECEIVER_ROLES` set plus a deceiver lens
  (`wolf_vote_is_good` = a vote that induces a town mislynch, the mirror of town `hit_threat`), and a
  `--lens {town,wolf}` flag so a wolf/SK run scores on its own win condition. One assumption was
  corrected in place: night-kill replay, listed as an open frontier, was already fully wired — only
  the day-vote side was missing.
- **Two apparatus corrections shipped alongside.** Diverse-case selection was rewritten to round-robin
  across days, removing a day-2-first weighting that early-loaded pooled aggregates; and the lexical
  echo proxy was formally retired (it tracked its judge at only Spearman rho=0.14, and is kept runnable
  only so that invalidation stays reproducible).

## L2 — trust (the screen)

- **✅ Validated as a screen, by convergence.** Built independently of the paired A/B, the two agree:
  town memory helps and deceiver memory is null on *both*. Whole-game (N=30): +17 / +23pp town win,
  wolf/SK null. Per-decision: +0.078 net-value day-2 and +0.117 endgame for town, wolf/SK null. Both
  also contradict an earlier −40pp "town collapse" that later proved to be model drift, not memory —
  the convergence is the validity anchor, not the small per-cell N.
- **The cheap-lever ladder screened clean.** Every cheap way to make the agent *use* memory better
  came back null-or-harmful, tier *suggestive*: emitting reasoning before the vote synced
  vote↔reasoning 75%→92.5% (N=40) but moved engagement ≈0 (echo, N=150); a forced per-memory
  "does this apply?" verdict showed the model genuinely *can* reason applicability (N=20) yet *hurt*
  the vote via over-caution (0.75→0.55); outcome framing was situation-dependent.
- **An assumption that flipped, surfaced as a finding.** Outcome framing first read as a clean null
  (pooled N=40, immediate − net = +0.025, p=1.0) — but that sample sat in the day≥3 prompt-ceiling
  zone where memory ≈ no-memory for everything. Stratified, it flips: day-2 info-starved (N=30) shows
  immediate − net = **−0.167** (4 worse / 0 better, p=0.125), the cautious net framing converting
  would-be mislynches into abstains (mislynch 0.23→0.07). This is direction + mechanism at N=30,
  p=0.125 — a **suggestive** claim, not proven; the strata are reported, never pooled to manufacture
  significance.
- **Bounds to state plainly.** Off-policy (a frozen context, one decision, no propagation); small
  per-cell N; a triage tool, not a verdict. Its role is to kill dead levers for ~$1 before any reaches
  a ~$20 powered arm — which is what it did (all cheap levers screened out, graduating the question to
  conditioned-content extraction).

## L1/L2 — the per-day replay (design only)

- **Status: ⏸ DESIGN — NOT BUILT (2026-07-02).** An execution-ready spec; no `day_replay.py` exists.
  It fills the ladder rung between the off-policy per-turn screen and the full paired A/B: re-run a
  *single* day k≥2 of a recorded game under a swapped condition, **on-policy within the day** (real
  scheduler, real utterances, live votes), with the prior days frozen as history. It reuses the
  production day subgraph, so replay drift can only come from the reconstructed entry state, never a
  divergent harness.
- **Cost + niche.** ~$0.10–0.15 per day-replay ≈ 20–30% of a full game; a 30-pair campaign plus the
  acceptance gate is a ~$10–17 decision, not ~$60. Sourced from memory-OFF recordings so the OFF arm
  is on-policy by construction; day 2 is the primary stratum; no multi-day chaining in v1.
- **The honest part is the acceptance gate.** Before any ON-vs-OFF number is trusted, an
  unchanged-condition replay of 10–15 game-days must be statistically indistinguishable from the
  recorded days (distributional, never transcript-equality, because the scheduler is content-reactive).
  The measured self-agreement *becomes* the harness's cited noise floor, and any later effect inside
  that floor is "not distinguishable from replay noise." A hard-fail survivor-set cross-assert guards
  state fidelity (never warn-and-continue).
- **What it can and cannot answer.** It answers the within-day causal effect of a condition given a
  fixed prefix. It explicitly **cannot** answer the game-outcome or compounding effect — that stays
  with the paired A/B. The open v7 compounding question is not something a day replay can close.
- **Corrections the code-verification forced on the design** (kept in place, not laundered):
  `vigilante_results` is sidecar-only (absent from the batch record top level); the utterance cap is
  `max(min, ceil(3·N))` (cap(9)=27), not the ~25-flat first estimated — dollar figures survive, the
  constant is corrected; night deaths are stamped with the *concluding* day, so the naive `day < k`
  prefix filter is correct only for a non-obvious reason, now documented.

## Verdict + cheapest upgrade

Per the header. The per-turn screen is a validated triage instrument whose one real weakness (no
deceiver coverage) is now fixed; the per-day harness is a costed, gated design.

**Cheapest upgrades, both HELD (spend not yet approved):**
- **Wolf replay screen (~$3–5)** — now *enabled* by the deceiver-coverage fix; it de-risks any future
  wolf-direct A/B (~$60–70, itself unscheduled) before that spend.
- **Gating re-screen (~$10–15)** — substitutes deterministic dims into the frozen cases; authorized by
  the dimension-audit RE-OPEN (see [`../dimension_extraction/report.md`](../dimension_extraction/report.md))
  and must run before any prompt surgery on the enums.

The per-day harness's cheapest first step is fixed by its own design: build the acceptance gate before
trusting a single ON-vs-OFF number.

## Evidence (code + L2 artifacts)

- **Code (at `4b1449e`):** the study runner `evaluation/src/experiments/studies/decision_replay.py`
  (`--lens`, `--night`); the shared decision-screen engine lives at
  `evaluation/src/replay/decision_screen/` (cases/replay/schemas/stats/screens — extracted verbatim
  2026-07-02, golden byte-diff clean) atop `evaluation/src/replay/` (`application.py`,
  `retrieval.py`); deceiver lens in
  `evaluation/src/loop/decision_scoring.py` (`REPLAYABLE_DECEIVER_ROLES`, `wolf_vote_is_good`).
- **L2 artifacts (pointed-at):** the screen's reasoning trail plus
  [`report_screening_layer.md`](../../memory_system/effectiveness/decision_replay/report_screening_layer.md)
  and [`experiment_log.md`](../../memory_system/effectiveness/decision_replay/experiment_log.md)
  (per-finding `echo_*`/`applicability_*`/`framing_*` JSONs colocated there); provenance model
  `gemini-3.1-flash-lite` @ temp 1.0, commits `d335d2c`→`b332550`. The per-day spec:
  [`day_replay/design.md`](../../memory_system/effectiveness/day_replay/design.md). Hardening context:
  [`../hardening_pass/experiment_log.md`](../hardening_pass/experiment_log.md) §2.2, §3, §4.5–4.7.

*Written 2026-07-02 from the hardening pass + the decision-replay evidence. Apparatus characterised;
the memory verdict (town helps, deceiver null) belongs to chapter 3.*
