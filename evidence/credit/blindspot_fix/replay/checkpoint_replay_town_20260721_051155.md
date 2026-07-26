# Checkpoint replay — compounding readout

- cases: `batch_results/v6ab_townsp.jsonl` (factions=town, N=100)
- git: `a010dc688cb6242c61520e1959ecdd336bb8b635` (dirty)
- retrieval: loop production read path (raw, non-wide) (top_k=5, keep=3, rerank=off)
- case-set hash: `e08c0491bc6c5125`

## Curve (per-arm, identical case set — both verdict-mapping readouts)

accuracy = positive-rate (the McNemar correctness convention: night neutral/
negative count as not-correct); mean value = raw −1/0/+1 verdict mean
(VERDICT_VALUE convention), which keeps friendly-fire regressions visible.

| arm | N | accuracy | mean value (−1..+1) |
| --- | --- | --- | --- |
| empty | 100 | 0.4 | 0.28 |
| full_store | 100 | 0.38 | 0.23 |
| legacy_pruned | 100 | 0.39 | 0.26 |
| fixed_pruned | 100 | 0.38 | 0.25 |

## PRIMARY — loop growth (gen-final vs gen-1, paired McNemar)

- fixed_pruned helped=7, hurt=7 → p=1.0

## SECONDARY — static store (empty vs gen-1, paired McNemar)

- gen1 helped=5, hurt=7 → p=0.7744
