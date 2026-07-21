# Checkpoint replay — compounding readout

- cases: `batch_results/v7_endpoint_ab/endpoint_on.jsonl` (factions=town, N=100)
- git: `a010dc688cb6242c61520e1959ecdd336bb8b635` (dirty)
- retrieval: loop production read path (raw, non-wide) (top_k=5, keep=3, rerank=off)
- case-set hash: `b95957cd85cbee4b`

## Curve (per-arm, identical case set — both verdict-mapping readouts)

accuracy = positive-rate (the McNemar correctness convention: night neutral/
negative count as not-correct); mean value = raw −1/0/+1 verdict mean
(VERDICT_VALUE convention), which keeps friendly-fire regressions visible.

| arm | N | accuracy | mean value (−1..+1) |
| --- | --- | --- | --- |
| empty | 100 | 0.31 | 0.13 |
| full_store | 100 | 0.27 | 0.04 |
| legacy_pruned | 100 | 0.32 | 0.12 |
| fixed_pruned | 100 | 0.33 | 0.14 |
| fixed_resynth | 100 | 0.31 | 0.1 |

## PRIMARY — loop growth (gen-final vs gen-1, paired McNemar)

- fixed_resynth helped=4, hurt=0 → p=0.125

## SECONDARY — static store (empty vs gen-1, paired McNemar)

- gen1 helped=1, hurt=5 → p=0.2188
