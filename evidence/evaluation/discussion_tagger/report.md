# Discussion Tagger — Evaluation Apparatus Report

> **Scope: the tagger as an extraction-style instrument.** The v7 loop's paid deceiver-skill metric:
> an omniscient end-of-day LLM pass that tags each player's discussion and night play. This spoke
> covers *what it extracts, what depends on it, and how far to trust it* — a companion to the
> [`../loop/report.md`](../loop/report.md) apparatus report, which frames the same tagger inside the
> compounding-slope machinery. Design lineage + current mechanism:
> [`../../discussion_tagger/`](../../discussion_tagger/) (report.md + experiment_log.md);
> frozen design + run records: [`../../v7_final/`](../../v7_final/).
> Lens + skeleton: [`../report.md`](../report.md); ledger: [`../source_map.md`](../source_map.md).
>
> **Verdict: 🟡 a VALIDATED deceiver-skill METRIC, not a memory verdict.** Its holistic discussion
> verdict predicts the win beyond the vote proxy (wolf +0.56 / SK +0.60, N=24), survives blinding and
> a verbosity control, and its outcome-leak is negligible (N=6). But it is correlational, single-epoch,
> uncalibrated at the per-field level, and one residual night-leak is untested.
>
> **2026-07-11 — consumer change (wiring pending):** the read/tactic credit redesign
> ([`../../discussion_tagger/read_tactic_credit_redesign.md`](../../discussion_tagger/read_tactic_credit_redesign.md))
> retires the tagger's credit role — `credit.py::_tagger_ledger` and the night read-quality override
> become diagnostic-only; day-discussion credit moves to the day-vote endpoint + move-grain advocacy.
> The tagger remains exactly what this verdict says it is: a validated deceiver-skill *diagnostic*.
> The trust findings below are unaffected.

## Objective the apparatus targets

Discussion has no deterministic de-luck proxy — weighing framing, credibility, and role-claims into a
merit verdict is the irreducible LLM job. The tagger fills that hole for the v7 credit loop: one
omniscient flash-lite pass over each day, per player, producing a holistic **DISCUSSION** verdict
(positive / neutral / negative — "did this player advance their own faction's win, judged
independently of whether the vote or game went their way") plus a **NIGHT** read-quality verdict
(a skilled read vs a lucky hit). Alongside the coarse verdict it emits the detection lens the verdict
weighs: `framing` (none / legitimate / manipulative), `credibility` (low / medium / high), and
`role_reveal` (none / own_role_claim / challenge_claim), the last anchored on the persisted day-summary
`role_claims` (with a raw-message fallback for pre-A4 records that lack the structured field).

**What depends on it.** The paid credit tier (`credit.py::_tagger_ledger`) rides the tagger to score
deceiver discussion skill and to backfill per-decision credit; the *free* tier instead credits
discussion by the day-vote endpoint. So the tagger is the only instrument that sees wolf/SK discussion
merit the vote proxy is blind to — which is exactly why its trust matters.

## L1 — the instrument

- **Structure** (`evaluation/src/loop/discussion_tagger.py`): `get_llm_pro()` env-pinned to flash-lite,
  `with_structured_output(DayTags)`, an all-required schema (flash-lite drops optional/nullable fields),
  parallel per-day, cached per game. Reasoning inputs (each agent's own `updated_strategy`) are fed for
  **attribution only** — to de-confound a night target and surface a formed-but-unvoiced read — never
  for valence; valence comes only from observable behavior + true roles, because LLMs confabulate.
- **2026-07-02 hardening.** Three silent-failure paths were closed: a per-day LLM failure now logs a
  loud end-of-game `logger.error` counting degraded days, and a new `strict` param re-raises instead of
  returning empty tags; a missing eval-cases sidecar (which empties `role_claims`/`private_reads`) now
  warns once per game; and the tag cache — previously keyed `(game_id, version)` only, which had already
  served one arm's tags to the other — now folds a session/trace provenance slug into the filename and
  asserts a stored `provenance` on read, re-tagging fresh on mismatch.

## L2 — trust

- **✅ The holistic verdict is a validated deceiver metric** (`tagger_skill_retest.py`, N=24 v2 ON
  games). Partial r(discussion verdict, **won** | de-luck, verbosity) = **+0.56 wolf / +0.60 SK /
  +0.02 town**. The verdict predicts the win *beyond* the vote proxy, survives blinding the tagger to
  the outcome, and survives partialling out message verbosity — so it is real deceiver skill the vote
  proxy cannot see, not outcome-leak and not wordiness. The town row (+0.02) is the negative control:
  town discussion merit is already captured by its vote endpoint.
- **✅ Outcome-leak is negligible** (`tagger_deleak_ablation.py`, 2×2, N=6 games). Withholding the day's
  vote result and night deaths moved the discussion-verdict coupling +0.07 town / ~0 wolf/SK, so the
  tagger keeps *showing* the outcome by default (blinding bought a within-noise gain at the cost of the
  night verdict's legitimate lynch context). The 2×2 was needed because a one-armed re-tag confounds the
  outcome axis with the mechanical silent-player axis.
- **Bounds, stated plainly.** N=24, single-epoch, correlational — this validates the **metric**, not a
  memory effect. Converting the tagger's tentative wolf signal into a memory *verdict* needs a direct
  wolf SP/obs A/B, which has never been run. The retracted "+0.556" halo was a *different quantity*
  (undifferenced **town** credit-level), not this wolf/SK correlation-with-win, so there is no
  contradiction; the retest's +0.02 town row agrees with that retraction.
- **⚠️ Per-field accuracy is designed but not persisted.** `evidence/v7_final/discussion_credit/tagger_accuracy.py` cross-
  checks `role_reveal` against a deterministic self-claim detector and the day-summary prose, and prints
  `framing`/`credibility` distributions by faction — but it writes to stdout only, so **no per-field
  accuracy number is on record** and none is cited here. On the v6ab validation epoch the structured
  `role_claims` anchor is also empty (an A4 addition postdating the epoch), so `role_reveal` fell back to
  raw-message judging there — a real caveat on the detection-lens fields.
- **Durability gap on the load-bearing numbers.** The +0.56/+0.60 and the deleak result were long
  stdout-only; the retest/ablation scripts now *also* write `*_results.json`, but only on their next
  (paid) execution — **the JSON artifacts do not yet exist on disk**, and the only durable record of the
  numbers remains `v7_final/experiment_log.md` §12g.

## Gaps, honestly rated (current 2026-07-02)

1. **🟡 Larger-N revalidation queued.** The +0.56/+0.60 rests on N=24 single-epoch; it would piggyback
   on the HELD town-only compounding rerun (~$65) to gain power and a fresh epoch. Severity: **medium**
   (the metric is directional-trustworthy now; a memory *verdict* needs the direct wolf A/B, not just N).
2. **⚠️ Night-verdict residual leak untested.** The night verdict still sees its own kill's death (the
   night analogue of the day leak the ablation cleared); a two-prompt split would fix it if a clean
   deceiver night-metric is ever needed. Severity: **low** (the *discussion* verdict is the load-bearing
   deceiver signal; night credit has a deterministic de-luck proxy underneath it).
3. **⚠️ Per-field accuracy + artifact persistence.** Run `tagger_accuracy.py` and the retest/ablation to
   land durable JSONs and a real per-field number; the `role_claims` anchor is only populated on post-A4
   batches. Severity: **low-medium** (the holistic verdict is validated; the sub-tags are the detection
   lens, not the credit signal).

## The new canonical runner

The tagger's eval runner graduated 2026-07-02 out of the frozen `v2_full/` scripts into
`evaluation/src/cli_runner/discussion_tagger_eval.py` (console `eval-tagger`) — one config-driven entry with
`mode: accuracy | skill | deleak` reproducing the three originals' computations, manifest-stamped
output, 12 stubbed-LLM tests. One disclosed refinement: skill's secondary A statistic now uses a fresh
symmetric outcome-in pass (so A won't bit-reproduce the frozen run); the load-bearing outcome-blind
B/C (+0.56/+0.60) are computation-identical. The frozen retest/ablation scripts stay put as dated
evidence, per the freeze rule.

## Evidence (code + L2 artifacts)

- **Code (at `4b1449e`):** `evaluation/src/loop/discussion_tagger.py` (the live tagger + hardening),
  `evaluation/src/loop/credit.py::_tagger_ledger` (its consumer); tests `tests/test_tagger_inputs.py`
  (forced-failure counter + `strict` re-raise + cache provenance).
- **L2 artifacts (pointed-at, the tagger's KEY proof):**
  [`../../v7_final/runs/v2_full/tagger_skill_retest.py`](../../v7_final/runs/v2_full/tagger_skill_retest.py)
  (N=24 blinded + verbosity retest) and
  [`tagger_deleak_ablation.py`](../../v7_final/runs/v2_full/tagger_deleak_ablation.py) (N=6 2×2);
  the accuracy check [`../../v7_final/discussion_credit/tagger_accuracy.py`](../../v7_final/discussion_credit/tagger_accuracy.py). The durable
  numbers live in `../../v7_final/experiment_log.md` §12g (the `*_results.json` appear on next execution).
  Hardening context: [`../hardening_pass/experiment_log.md`](../hardening_pass/experiment_log.md) §2.3, §4.2–4.4.

*Written 2026-07-02 from the v7_final tagger evidence + hardening pass. Apparatus characterised; whether
wolf/SK memory compounds — the science the tagger would help measure — is open and belongs to the loop
spoke + chapter 3.*
