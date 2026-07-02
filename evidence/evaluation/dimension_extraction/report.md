# Dimension Extraction — Evaluation Apparatus Report

> **Scope: the apparatus, not the retrieval verdict.** Covers how the v6 situation-**dimension** fills
> are produced and, for the first time, *audited* against ground truth — plus what that audit re-opened.
> The retrieval/gating design conclusions live in `phase_b/`; this spoke is the measurement of whether
> the fills those screens gated on were even correct. Source of record:
> [`../../phase_b/dimension_accuracy_audit/experiment_log.md`](../../phase_b/dimension_accuracy_audit/experiment_log.md).
> Lens + skeleton: [`../report.md`](../report.md); ledger: [`../source_map.md`](../source_map.md).
>
> **Verdict: ⚠️ the fills were never checked, and the $0 audit found some BROKEN.** `players_alive`
> is sound (bucket 0.990); `bullets_left` (0.164) and wolf-side `is_swing` (0.606, *worse than a
> constant*) are not. This fired the pre-registered **RE-OPEN**: the recorded dimension-gating null is
> partly *uninformative*, not a clean content verdict. The agent-knowable fills are now computed from
> game state; the enum fills remain LLM-filled and unvalidated (kappa spot-check PENDING user labeling).

## Objective the apparatus targets

The v6 memory pipeline attaches structured *situation dimensions* to each stored and retrieved note.
Every dimension is LLM-filled — at extraction time (the extractor's numerics are copied straight into
the store) and at query time (`Agents/memory/enrichment/situation_agent.py`). Production retrieval
*gating* keys on four of them: `players_alive` (bucketed), `is_swing`, `exposure_class`, and
`info_landscape_class`. No tool had ever compared a filled value to ground truth, even where truth is
deterministically computable from the board. If the fills are inaccurate, the gating and criticality
screens tested noise, and their recorded nulls are uninformative rather than negative. The audit exists
to distinguish those two worlds at $0.

## L1 — the instrument

- **The $0 deterministic audit** (`evaluation/src/audits/dimension_audit.py`; the paid `--regen` arm
  hard-refuses pending spend sign-off). It recomputes deterministic truth for every LLM-filled
  query-side dimension in the loop-era sidecars and compares. Coverage: **~6,267 cases-with-dims**
  (20,284 situation-rows) across town_only_run1 (25.9% / 30 games), town_only_run2 (24.7% / 100 games),
  and v2_full (42.2% / 24 games — the only run carrying wolf/SK dims); the 5 `legacy` smoke runs predate
  dimension capture and are excluded, stated not skipped. The ~25–42% rates are the structural ceiling
  (dims fill only on the retrieving memory-ON side), not missingness. Truth home `query_criticality` was
  lifted into `evaluation/src/loop/decision_scoring.py` so the audit and the criticality screen compute
  it identically; 8 unit tests over the truth functions.
- **A mandatory epistemic split** so a mismatch is never mispriced: *agent-knowable* dims
  (`players_alive`, `bullets_left`, `ally_revealed`) are pure fill error; *vs-omniscient* dims
  (`distance_to_parity`, `is_swing`) conflate fill error with the agent's epistemic limit for town roles
  (a villager cannot know the wolf count), so only the wolf side reads as ~true fill accuracy.

## L2 — results, per dimension

| Dimension | class | n | exact acc | read |
|---|---|---|---|---|
| `players_alive` / `alive_bucket` (gate key) | agent-knowable | 6099 | 0.970 / **0.990** | sound — the gate's primary key held |
| `ally_revealed` (partner-absent) | agent-knowable (wolf) | 439 | **0.975** | sound |
| `bullets_left` | agent-knowable (vig) | 1109 | **0.164** | broken — under-counts (bias −0.68); day-2 accuracy 0.0 |
| `is_swing` — wolf-side (≈true) | ~true fill | 439 | **0.606** | **worse than a constant** — always-False scores 0.827 (base rate 0.173) |
| `is_swing` — town-side | vs-omniscient | 5282 | 0.469 | conflated with epistemic limit; not a fill verdict |
| `distance_to_parity` | vs-omniscient / ~true | 439/5660 | 0.09 / 0.05 | unusable as an exact key (matches its default-off status) |

The three agent-knowable numerics are the clean story. `players_alive` is filled well but is a value the
agent was literally handed — 3% wrong for no epistemic reason. `bullets_left` is mostly wrong: every
vigilante with 2 unspent bullets reports 1 on day 2 (accuracy 0.0), climbing only to ~0.35 by day 4.
Wolf-side `is_swing` is the finding: at 0.606 against a 0.173 base rate it *over-fires* "swing" (173
false positives vs 76 true positives), so it is materially worse than a constant.

- **A truth-computation catch, fixed in place (not laundered).** Wolf `night_action` cases persist an
  empty `surviving_players` roster (176 cases); the first pass scored fills against a bogus 0 and
  manufactured a wolf +2 over-count. The runner now counts these `no_roster` and skips criticality truth
  there; corrected wolf `players_alive` = 0.97. A deterministic checker is only as good as its inputs —
  it earned one bug fix before its first real read.

## L2 — the RE-OPEN and what it re-opens

- **The pre-registered rule** (frozen before running): CONFIRM the negative gating verdict iff
  alive-bucket ≥ 0.90 **and** wolf-side `is_swing` ≥ 0.80 **and** the enum kappas ≥ 0.6; RE-OPEN if any
  gated dim < 0.80. Alive-bucket passed at 0.990, but wolf-side `is_swing` at 0.606 fired **RE-OPEN**.
  The enum-kappa clause is PENDING Phase-3 human labeling and cannot lift this to CONFIRM regardless.
- **What it means, bounded honestly.** The gating null is at least partly **uninformative, not a clean
  content verdict**: the gate keyed on one reliable dimension, one anti-informative one, and two enums no
  one has validated. Mean gated error ē ≈ 0.202 implies a true retrieval tilt would be attenuated to
  `1 − 2ē` ≈ 0.60 of its strength, so a screen reading ~0 could be masking a real but smaller effect.
- **Scope of the re-open, said plainly.** It re-opens **gating** only. The criticality *screen*'s query
  side was already deterministic (`query_criticality`), so it is untouched. This authorizes the ~$10–15
  gating re-screen — substitute deterministic `players_alive` + offline `is_swing` into
  `dimension_gating_screen.py` — before any prompt surgery on the enums. That spend is HELD.

## L1 — the computed-fill fix (done 2026-07-02, $0)

The structural corollary, green-lit as free. At query time, after the situation LLM returns,
`Agents/memory/enrichment/situation_agent.py::_override_deterministic_dims` overwrites the three
agent-knowable dims from game state before dims and embeds are composed: `players_alive` from a
shape-robust living-player count, `bullets_left` from the vigilante's live counter, `ally_revealed` from
pack-size vs initial wolf count. `distance_to_parity` / `is_swing` are deliberately left LLM-filled —
they need true roles the live agent cannot see (their offline substitution belongs to the held
re-screen).

- **Two payload bugs surfaced and fixed** (assumption corrections): `players_alive` was never a plain
  `len(surviving_players)` — single-actor night payloads exclude the actor (off-by-one) and wolf payloads
  carry no role-blind roster — which retroactively explains part of the LLM's 3% error as payload
  ambiguity, not model sloppiness; and the vigilante's *day* payload dropped the bullets counter
  entirely, so `vigilante_bullets` had to be threaded through a new `DayGraphState.vigilante_bullets`.
- **Scope guarantees.** The corrected numerics carry no embed marker, so the override changes only the
  gating filter input — the composed embed string and retrieval matching are unchanged. Stored records
  are untouched: query-time only, so only future queries benefit. Named residual: the LLM's *prose*
  (`criticality_stakes`) is derived from its own possibly-wrong numbers and is not re-derived, so
  corrected numerics can disagree with prose in the same object (accepted, flagged in code).

## Gaps, honestly rated (current 2026-07-02)

1. **⏸ The enum fills are entirely unvalidated** (`exposure_class`, `info_landscape_class`,
   `consensus_direction`, …). They have no deterministic ground truth, so the audit reports only their
   value *distributions* (heavily skewed — villager `exposure_class` is 94% one class). The kappa clause
   of the decision rule is PENDING the Phase-3 human + pro-LLM spot-check, which runs on the now-built
   diagnosis sampler and needs ~2h of user labeling (forcing ~half predicted-`exposed` for off-diagonal
   power). Two of the four gate keys therefore remain unaudited; even the RE-OPEN is conservative,
   firing on the deterministic dims alone. Severity: **high** (load-bearing gate keys, uncalibrated).
2. **⚠️ The audit covers the QUERY side only.** Stored (extraction-time) fills are not offline
   truth-computable (no frozen board travels with a stored observation); they pass weak
   internal-consistency bounds 100% on v6_1 (`|distance_to_parity| ≤ players_alive`), which rule out
   gross corruption but not the query-style error found here. Their real check is the same Phase-3
   sampled review. Severity: **medium**.
3. **HELD — the gating re-screen (~$10–15)** converts "uninformative" back into a verdict; authorized by
   the RE-OPEN rule, spend not yet approved. Severity: **medium** (blocks re-closing the gating question).
4. **N is a decision count, not a game count** — 100 games in town_only_run2 but decisions are correlated
   within a game. Adequate for the per-decision fill-accuracy point; noted for anyone reading the n's as
   independent. Severity: **low**.

## Evidence (code + L2 artifacts)

- **Code (at `4b1449e`):** audit `evaluation/src/audits/dimension_audit.py`; truth fn
  `query_criticality` in `evaluation/src/loop/decision_scoring.py`; gate `dimension_gating.py::_alive_bucket`;
  fill fix `Agents/memory/enrichment/situation_agent.py` (`_override_deterministic_dims`,
  `_computed_players_alive`) + threading in `Agents/nodes/day/flow.py`, `Agents/graphs/parent.py`,
  `Agents/state/day.py`. Tests: `tests/test_dimension_audit.py`, `tests/test_situation_dim_override.py`.
- **L2 artifacts (pointed-at):**
  [`../../phase_b/dimension_accuracy_audit/experiment_log.md`](../../phase_b/dimension_accuracy_audit/experiment_log.md)
  (§4 tables, §5 RE-OPEN, §6 fill fix) + `data/dimension_audit_20260702_105203.json`. Motivating finding
  + schema spec: [`../hardening_pass/experiment_log.md`](../hardening_pass/experiment_log.md) §2.1, §5, §6;
  `phase_b/dimension_schema_build_spec.md`.

*Written 2026-07-02 from the dimension-accuracy audit + hardening pass. Apparatus characterised; whether
retrieval gating actually helps is chapter 3, and is now RE-OPENED pending the held re-screen.*
