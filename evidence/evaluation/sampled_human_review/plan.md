# Plan — harden sampled human review (the case sampler)

**Goal.** Turn rung ② from an ad-hoc habit into a small, repeatable apparatus: a **deterministic case
sampler** that picks *which* cases to review, plus a **recorded** human/pro-LLM review loop so findings
become artifacts, not just judgment. **MVP-shaped** — in service of the v7 diagnosis and the write-up, *not*
a diagnostic platform.

## The shape — four steps, reusing parts that already exist

1. **Select** the candidate cases by two signals, combined — never by outcome:
   - **score-outliers** — cases where the LLM-judge (or a metric proxy) sits at the tails;
   - a **deterministic leverage anchor** — `is_swing` / distance-to-parity / de-luck proxy — as the
     *pivotalness* proxy.
   ⚠️ **Never select on game outcome (won/lost).** That is the `extraction_selection` halo lesson: outcome
   conditioning reproduces "did your side win," not "was this case pivotal." Leverage is structural; outcome
   is a halo.
2. **Cohort** — expand to a balanced set via `evaluation/src/data/sampling.py` (`games_to_sample` +
   stratify by role/phase/action), so the reviewed handful is representative, not convenient.
3. **Replay** — reconstruct each case cheaply through `evaluation/src/replay/*` (rebuild the store, re-run the
   one stage) — no full game re-run.
4. **Surface + record** — present each case to a human and an advanced model, and **persist the verdicts to a
   durable local artifact** (the missing piece today; mirror the tracing eval-capture pattern — local JSONL
   primary, so the review is reproducible and citable).

## What this buys

- **Removes the selection bias** that makes today's eyeballing ungeneralisable (step 1–2).
- **Gives rung ② a record** — its findings become evidence, not just "a person looked once" (step 4).
- **Feeds rung ③** — the same sampled cohort is the front door to a golden set (sample → review → promote
  the worth-labelling ones), so building the sampler upgrades both the human-review and the labeling rungs.

## Discipline / non-goals

- MVP only — outliers + one leverage anchor + stratified cohort + cheap replay + a JSONL of verdicts. No UI,
  no scoring dashboard, no live service.
- The leverage anchor is **deterministic and outcome-blind** by construction; if a future anchor needs the
  outcome, it doesn't ship.

## Sequence

This is the tool the **v5/v6/v7 + eval concurrent review** will run on — so it's built just before / as the
first step of that pass, against the settled store. (Origin: the scoped sampler build green-lit in
[`../source_map.md`](../source_map.md) → *Planned build*.)

*(Plan drafted 2026-06-30. **Built 2026-07-02** — `evaluation/src/diagnosis/sampler.py` +
`evaluation/src/experiments/case_sampler.py` (`eval-case-sample`); smoke artifacts in
[`sampler_smoke/`](sampler_smoke/). See the BUILD section in [`report.md`](report.md).)*
