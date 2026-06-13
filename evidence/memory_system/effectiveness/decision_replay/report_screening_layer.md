# Screening Layer — Decision-Replay

*Draft section for the Memory Effectiveness report. It slots after the paired A/B results: the A/B is the
verdict layer, this is the screening layer that explains the mechanism and triages what to build next.*

## Why a second layer

The paired A/B answers *whether* memory helps at the game level. It cannot cheaply answer *why*, or *which*
of a dozen candidate fixes is worth building — each whole-game arm costs ~$15–30 and is exposed to overnight
model drift. Decision-replay is the screening layer: freeze one decision, swap **only** the retrieved-memory
block, regenerate that one action, score it against the true roles. It is paired at the decision (role-luck
cancels), drift-immune in one sitting, and judge-free wherever the target is a role lookup. It trades
statistical power for speed and isolation — a pre-filter that kills dead levers for ~$1 before any reaches a
powered arm.

**What a screen can and cannot claim.** It sees *local* decision quality at a frozen board — direction and
mechanism — not trajectory, magnitude, or win rate. So its findings are reported as **direction + mechanism**,
tiered, and the win-rate headline stays with the A/B. We never headline a screen p-value. A screen earns a
claim two ways, both N-robust: by showing the mechanism in the cell-level decomposition, and by converging
with an independent cut.

## Convergence with the A/B (the validity anchor)

The two layers were built independently and agree:

| | paired A/B (whole-game, N=30) | decision-replay (per-decision) |
|---|---|---|
| town | +17 / +23 pp win (helps) | +0.078 net-value day-2, +0.117 endgame (helps) |
| wolf / SK | null | null |

*Takeaway: town memory helps and deceiver memory is null by both a powered whole-game test and a
drift-immune per-decision test — and both contradict an earlier −40 pp "town collapse" that later proved to
be model drift, not memory.* That agreement is the point: the screen's role is convergent mechanism, not a
standalone verdict, so its small per-cell N never has to carry the headline.

## The cheap-lever ladder

We used the screen to test, in sequence, every cheap way to make the agent *use* memory better — before
paying for an expensive content rebuild. All point the same way.

| lever | what changed | finding | tier |
|---|---|---|---|
| reorder / memory-link | emit the reasoning before the vote | syncs vote↔reasoning 75%→92.5% (N=40) but raises memory engagement ≈0 (judge-free echo, N=150) and can flip a *correct* vote to wrong on bad content | suggestive |
| force applicability | a forced per-memory "does this apply?" verdict | the model genuinely *can* reason applicability — it separates situation-match from lesson-transfer (N=20) — but forcing it *hurts* the vote (0.75→0.55) via over-caution | suggestive |
| outcome framing | rewrite each lesson net-outcome → immediate-outcome | **situation-dependent** (below) | suggestive |

*Takeaway: no single blanket setting — schema, instruction, or framing — wins everywhere; the correct call
flips with the situation.* The capability finding is the one to dwell on: the agent *can* judge which memory
applies, so the bottleneck was never capability. What hurts is forcing the deliberation, which makes a weak
model over-cautious — separating "can it" from "does it help" is what stopped us shipping a plausible-but-harmful fix.

## The assumption that flipped (surfaced as a finding)

Outcome framing first read as a clean null: N=40, immediate − net = +0.025, p=1.0. But that sample came from
day≥3, which the screen had already flagged as the *prompt-ceiling zone* where memory ≈ no-memory for
**everything** — a null there says nothing about framing. Stratified, it flips:

| stratum | net (cautious) | immediate (actionable) | imm − net |
|---|---|---|---|
| day-2, info-starved (N=30) | **+0.10** (vs −0.067 off) | −0.067 | **−0.167** (4 worse / 0 better, p=0.125) |
| day-5+, endgame (N=20) | 0.30 | 0.20 | −0.10 (p=1.0) |

*Takeaway: at day-2 the cautious framing converts would-be mislynches into defensible abstains (mislynch
0.23 → 0.07), and the "actionable" reframe undoes that — pushing the agent to vote when the board has nothing
to hit.* This is **direction + mechanism at N=30, p=0.125 — a suggestive claim, not a proven one.** Its sturdier
half is the *"net helps at day-2"* leg, which independently reproduces the day-2 caution benefit the A/B and
the screen's own stratification already show; the *"immediate hurts"* leg is the new directional bit. We do
**not** pool the strata to manufacture significance — the stratum split *is* the finding, and pooling is what
hid it the first time.

## What it screened to

Every cheap lever is null-or-harmful, and the framing result shows *why*: the optimal lesson is
situation-dependent, so no blanket framing can be right. The only remaining lever is content that carries the
**condition** — be cautious when info-starved, act when the threat is clear. That graduates to a powered step
(conditioned extraction) rather than another cheap patch. The screen did its job: it spent ~$1 per question to
keep us from spending ~$20 confirming a dead lever.

## Lessons

- **A cheap paired screen earns its keep by triage, not significance.** Pairing cancels role-luck and drift,
  so small N buys *direction*; the win-rate burden stays with the powered layer. Build screens to kill levers,
  not to prove them — and report them in that frame so a reader never mistakes a screen for a verdict.
- **Pooling hides structure — we learned it twice.** Pooling days hid the day-2 framing effect; pooling roles
  would hide the cell heterogeneity that is the finding. Stratify, report the cells, and let the cross-cell
  pattern (not any single significant cell) carry the weight.
- **Capability is not adoption.** A model can reason about a memory's applicability when forced to, yet doing
  so degrades the decision. Measuring "can it" separately from "does it help" is what distinguishes a real
  diagnosis from a plausible story.

## Provenance

Game/replay model `gemini-3.1-flash-lite` @ temp 1.0 (replays match the games' model and temperature);
adherence/coherence judges `gemini-2.5-pro` / `gemini-2.5-flash` (used only off the headline path). Driver:
`evaluation/src/experiments/decision_replay.py`. Commits `d335d2c` → `b332550`. Per-finding artifacts in this
folder (`echo_*`, `coherence_*`, `applicability_*`, `framing_*` JSONs); full reasoning trail in
`experiment_log.md`.
