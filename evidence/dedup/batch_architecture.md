# Batch dedup: how it works (moved)

*2026-10-26.* This page described the mechanics of the whole-store dedup pass
(`Agents/memory/batch_deduplication/`) as of June 2026. Its content now lives in
[the dedup report](report.md), section "5. The batch pass: the fold and the lesson dedup", and in the
batch log; the earlier version is in git history.

One statement on the old page was wrong and is not carried over. It called **two-pass** "a second LLM
pass over the survivors to catch duplicates the first pass missed across cluster boundaries". In the
code, two-pass is a cascade inside each cluster: a cheap model judges every entry, its keeps and
discards stand, and only the entries it marks as merges go to a stronger model, which decides again and
writes the merged text (`Agents/memory/batch_deduplication/cluster_agent.py::_two_pass_cluster_dedup`,
`config.py::TwoPassConfig`). With `skip_verify` set, as the learning tick's fold runs it, the second
model is never called and every proposed merge becomes a keep. The report's section "Built and off"
covers why the merge is off.

Where each part of the old page went:

| Old section | Now |
|---|---|
| The one idea: dedup within a namespace (and, since v6, a gate partition) | report, "2. The gate" |
| The flow (cluster → resolve → apply) | report, "5. The batch pass" |
| Clustering modes, the three-method table | report, "1. Search"; the full table in [batch_dedup/](batch_dedup/experiment_log.md), "Forming the clusters" |
| Applying an operation (survivor, summed counts, fail-safe pick, dry run) | report, "5. The batch pass" |
| Two knobs: two-pass, incremental | report, "Built and off" (both); the incremental mode's diagnosis in [incremental_convergence.md](incremental_convergence.md) |
| How it's verified | report, "How sure we are" |
| Design rationale | report, "The problem", "1. Search", "2. The gate", "5. The batch pass"; its claim that conservative dedup gained "without losing relevance" is corrected there (relevance 4.51 → 4.44, no significance test) |
