# Step-1 validation — blind-spot fix pair (sensitivity / specificity / false-penalty)

Rule columns: legacy = abstain neutral, no conversion; fixed = deadlock_negative + conversion term. `removed` = pruned OR evicted in the simulation.

## corpus: loop_run

| flagship | follow | legacy lift | fixed lift | conv n | conv lift | removed legacy→fixed |
| --- | --- | --- | --- | --- | --- | --- |
| harmful_silence_healer | 0 | — | — | 0 | — | False→False ❌ |
| good_engage_healer | 21 | +0.13 | +0.25 | 0 | — | False→False ✅ |
| harmful_silence_inv | 0 | — | — | 24 | +0.00 | False→False ❌ |
| good_convert_vig | 0 | — | — | 0 | — | False→False ✅ |
| harmful_abstain | 19 | +0.00 | -0.62 | 0 | — | False→True ✅ |
| good_comm_vig | 4 | +0.36 | +0.43 | 0 | — | False→False ✅ |

- caution family removed: legacy 0/89 → fixed 1/89
- prune stats legacy: {'pruned': 0, 'evicted': 0, 'kept': 168, 'spared': 7} | fixed: {'pruned': 1, 'evicted': 0, 'kept': 167, 'spared': 7}
- abstain census: 165 town abstains — new rule penalizes 160 (no-lynch days), spares 1 defensible (room mislynched) — {'no_lynch': 160, 'lynched_threat': 4, 'lynched_town': 1}

## corpus: endpoint

| flagship | follow | legacy lift | fixed lift | conv n | conv lift | removed legacy→fixed |
| --- | --- | --- | --- | --- | --- | --- |
| harmful_silence_healer | 0 | — | — | 0 | — | False→False ❌ |
| good_engage_healer | 24 | -0.06 | +0.17 | 0 | — | False→False ✅ |
| harmful_silence_inv | 0 | — | — | 6 | -0.03 | True→True ✅ |
| good_convert_vig | 0 | — | — | 0 | — | False→False ✅ |
| harmful_abstain | 31 | -0.11 | -0.83 | 0 | — | False→True ✅ |
| good_comm_vig | 8 | -0.08 | +0.05 | 0 | — | False→False ✅ |

- caution family removed: legacy 9/89 → fixed 19/89
- prune stats legacy: {'pruned': 14, 'evicted': 2, 'kept': 152, 'spared': 9} | fixed: {'pruned': 25, 'evicted': 1, 'kept': 142, 'spared': 5}
- abstain census: 117 town abstains — new rule penalizes 111 (no-lynch days), spares 2 defensible (room mislynched) — {'lynched_town': 2, 'no_lynch': 111, 'lynched_threat': 4}

## Verdict

- flagship checks passed: 9/12
  - ✅ endpoint/good_comm_vig
  - ✅ endpoint/good_convert_vig
  - ✅ endpoint/good_engage_healer
  - ✅ endpoint/harmful_abstain
  - ❌ endpoint/harmful_silence_healer
  - ✅ endpoint/harmful_silence_inv
  - ✅ loop_run/good_comm_vig
  - ✅ loop_run/good_convert_vig
  - ✅ loop_run/good_engage_healer
  - ✅ loop_run/harmful_abstain
  - ❌ loop_run/harmful_silence_healer
  - ❌ loop_run/harmful_silence_inv
