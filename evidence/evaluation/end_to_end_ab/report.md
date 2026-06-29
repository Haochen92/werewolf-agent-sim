# End-to-End A/B — Evaluation Apparatus Report

> **Scope: the apparatus, not the verdict.** Covers *how we run a fair "did memory help?" A/B* and *how far
> to trust that machinery* (L1 + L2) — NOT whether memory helped (that's the ch.3 verdict pass over the same
> folders). Evidence stays in [`../../memory_system/effectiveness/`](../../memory_system/effectiveness/).
> Lens + skeleton: [`../report.md`](../report.md); ledger: [`../source_map.md`](../source_map.md).
>
> **Verdict: 🟡 — trustworthy and unusually self-aware, with two honestly-disclosed limits** (win-rate
> structurally underpowered; pairing buys ~0 variance reduction).

## Objective the apparatus targets

Run two arms (memory on vs off) on the same boards, same epoch, and decide whether the on-arm does better —
de-lucked, drift-controlled, and honest about power.

## L1 — the instrument

> ⚠️ **The source_map code pointer is wrong** (`synth_deluck_ab.py` / `e2e.py` are NOT the game-level A/B —
> see corrections). The real apparatus is the chain below.

- **Generation** `scripts/run_batch.py`: arms paired by a **frozen `game_id` set** (`--game-ids-file`;
  `game_id → crc32 → role-draw`, reproduces 20/20). Same 30 ids per arm; treatment held constant
  (`--retrieval-types observations_only --reranking rerank_disabled --filtering filter_disabled`, top_k=5,
  `--no-memory-dump` so the frozen store can't grow). Arms run as parallel read-only batches, paired post-hoc.
- **Analysis** `paired_ab/analyze_ab.py` (+ `regenerate_stats.py` for older unpaired batches): pairs off vs
  arm by `game_id` → win via `mcnemar_exact`, each validated proxy via `wilcoxon_paired`.
- **De-luck transform (proxy-level — what the A/B relies on):** opportunity-conditioned denominators in
  `Agents/compute_metrics.py`, validated by point-biserial monotonicity vs faction-win. Removes setup luck
  (rates over *opportunity*, not existence). Validated basket: `town_vote_accuracy`,
  `correct_elimination_rate`, `town_mislynch_rate`, `serial_killer_lynched` (|r|≈0.55-0.65, p<0.01).
- **Stats** `core/stats.py` (all two-sided, **no auto-Bonferroni** — hand-applied): Clopper-Pearson CIs,
  Fisher exact (unpaired), exact McNemar (paired win), Wilcoxon signed-rank (paired proxies), point-biserial
  (proxy validation).
- **Decision-replay SCREEN** `experiments/decision_replay.py`: off-policy — freeze one decision, swap only
  the retrieved-memory block, regenerate that action, score vs true roles. Judge-free where the target is a
  role lookup. Self-labelled **off-policy, ±5-9pp, triage-not-verdict** ("we never headline a screen p-value").
- **`measure.py`** (loop): LLM-free per-faction de-luck slope *points* (the OLS slope is computed downstream).

## L2 — trust

- **Power / MDE (recomputed, confirms the apparatus's own claims):** win-rate MDE at N=30/arm, 80% power ≈
  **35pp** (matches the doc's ~36pp) → **win is structurally underpowered**; only a Batch-A-scale effect
  (70→97) clears it. Vote-accuracy MDE ≈ **0.18-0.21pp** (d≈0.53). The headline town
  `town_vote_accuracy +0.149` (d≈0.37) is itself **below the single-proxy MDE** → p=0.053. **What carries the
  verdict is convergence across 4 town arms + the basket, not any single test.**
- **⚠️ Pairing buys ~0 variance (the sharpest finding — a self-refutation the apparatus owns).** A
  same-seed/same-config/same-epoch canary decomposed the noise: **seed (role-draw) effect ≈ ZERO**
  (within-seed sd 0.249 ≈ across-seed 0.211-0.262). All variance is in temp>0 trajectories, none in the
  board draw → "**pairing on game_id adds ~no power; same-epoch was the load-bearing part of 'paired/seeded'.**"
  The report's `Var(on−off)=…−2Cov` motivation assumed a board-luck term that empirically isn't there. This
  doesn't invalidate the p-values (they embed the true noise) — it reframes what the design buys (drift
  control, not variance cancellation).
- **De-luck transform IS validated** (proxy-level): the basket clears point-biserial monotonicity vs win at
  |r|≈0.6, p<0.01; de-lucking is what caught + corrected the investigator find-rate denominator artifact.
- **Screen CONVERGES with the paired A/B** (the validity anchor): town +17/+23pp win ↔ +0.078 net-value day-2
  / +0.117 endgame; wolf/SK null ↔ null; both contradict an earlier −40pp "town collapse" that proved to be
  **model drift, not memory**.
- **Drift control (the strongest move):** original baseline discarded after a detected epoch shift (Fisher
  **p=0.0028**) → mandatory same-epoch fresh baseline + a $3 memory-off canary gate + pre-registered called
  shots. **The system caught its own confound.**
- **Null-ladder methodology:** the wolf/SK null was worked as a free→paid diagnostic ladder (validate a
  deceiver instrument on owned data → retrieval-precision → adherence → harm-channel), landing on "the wolf
  null may be a **measurement gap** (town-centric validated basket), not a true ceiling."

## Verdict + cheapest upgrade

**🟡 — the A/B harness is sound and self-aware** (same-`game_id` pairing + same-epoch baseline + epoch-drift
detection + canary + pre-registered called shots + correct paired tests + a convergent screen + an honest
null-ladder). It is trustworthy **even though the wolf result is inconclusive** — the wolf null is correctly
diagnosed as channel/measurement-limited. The 🟡 (not ✅) is for the two disclosed limits: win-rate
structurally underpowered (MDE ~36pp), and pairing ≈ no variance power.

**Cheapest upgrade (from the apparatus's own audit):** **CUPED is N/A** (no pre-treatment covariate — all
variance is temp=1.0 sampling). So: (1) **bootstrap / beta-binomial CIs** at analysis time (~20 lines, deps
present); (2) **more total N on the town arm via fresh seeds** (since pairing adds no power), N≈60-100/arm to
push proxies past Bonferroni — though the doc notes the **per-decision screen is the more power-efficient
follow-up** than buying win-rate games. NOT more pairing, NOT CUPED.

## Evidence (code + L2 artifacts)

- **Code:** `scripts/run_batch.py`, `evidence/.../paired_ab/{analyze_ab.py,regenerate_stats.py}`,
  `evaluation/src/core/stats.py`, `evaluation/src/experiments/decision_replay.py`,
  `evaluation/src/loop/measure.py`, `Agents/compute_metrics.py`.
- **L2 artifacts:** live A/B data = **point-at** `batch_results/ab_*.jsonl` (data plane; `analyze_ab.py`
  reads it); the older does-memory-help batch is colocated (`../../memory_system/effectiveness/batch_results/`);
  screen artifacts colocated (`../../memory_system/effectiveness/decision_replay/*.json`); seed sets +
  analyzers in `../../memory_system/effectiveness/paired_ab/`.

## Colocation call (JIT, 2026-06-28)

**Stays put — two-axis (also the ch.3 memory verdict).** Live A/B data is data-plane (point-at per CLAUDE.md);
the effectiveness/ folders are load-bearing for the memory chapter, so no physical move.

*(Inspected 2026-06-28. Apparatus characterised, not the memory verdict.)*
