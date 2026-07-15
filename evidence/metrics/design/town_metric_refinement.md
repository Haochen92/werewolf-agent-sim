# Town metric refinement — de-luck / denominator audit + 3-faction generalization (2026-06-18)

Refines the validated proxy set (`proxy_win_monotonicity.md`) against the **current 3-faction** games
(all 180 v6ab; the monotonicity table was v5, partly older rules). Question per metric (user's frame):
is it **de-lucked**, is the **denominator right**, or is it **not skill at all** — then finalize.

Taxonomy: **K** keep (de-lucked, monotonic) · **D** denominator/numerator wrong (fix exists) · **L**
luck-contaminated raw count (use the rate) · **S** causally severed (metric fine, outcome-link broken
by a substrate cap — can't be de-lucked into monotonicity until the cap is fixed) · **C**
context/activity (descriptive only).

## Cheap checks (point-biserial vs villager win, n=180 unless noted)

```
1. found_wolf_day:  win +0.15 | x game_length +0.15 | length x win +0.22  → S+D length-confounded
2. investigator:    threat_find_rate -0.00 | wolf_find_rate -0.03         → S (generalizing doesn't rescue = the cap)
3. vigilante:       evil_shots/bullets +0.131 | wolf_shots/bullets +0.130
                    wolf_KILLS/bullets +0.157 p=.035 | sk_shots/bullets +0.043 p=.57
4. healer:          wolf_block +0.415 | evil_block DIRTY +0.322 | evil_block CLEAN(town) +0.395 | town_save +0.395
5. power roles:     killed_by_wolves -0.211 | killed_by_evil -0.402 | LYNCHED -0.380
                    mislynch_rate/lynches -0.424 | survival_rate +0.654(confounded)
                    town_mislynch_rate (generic) -0.597
```

## Findings

**Generalization (wolf→evil) is METRIC-SPECIFIC — it helps only where the SK is a real part of that
metric's threat, and dilutes where it isn't:**
- **Power roles (#5): generalize — DOUBLES the signal** (−0.21 → −0.40). The SK kills power roles too;
  wolf-only missed half. **Adopt `power_roles_killed_by_evil`.**
- **Healer (#4): do NOT generalize — it dilutes** (+0.42 → +0.32 dirty). The apparent weakness was a
  **bug** (my `evil_block` counted the healer protecting the SK's target *even when that target was a
  wolf* — saving a wolf = anti-town); cleaning to town-only recovers +0.395 ≈ wolf-block. Residual gap
  (wolf +0.415 > evil_clean +0.395) is the real, small "SK-block converts less." **Keep
  `healer_town_save_rate` (+0.40).**
- **Investigator (#2): moot — the cap.** The threat-generic version already exists and is equally dead
  (−0.00). Confirms find ≠ convert; **HOLD → G1**.

**Vigilante (#3): the SK shot is confirm-only (night-immune → no removal), so it must be split off.**
`sk_shots/bullets` is dead (+0.04, transmission-dependent like the investigator find); `wolf_KILLS/
bullets` is the only significant one (+0.157 p=.035); lumped `evil_shots` dilutes. **Adopt
`vigilante_wolf_kills_rate` (landed wolf-kills / bullet supply)** — captures *use-your-ammo AND hit-a-
removable-target* in one de-lucked number. `correct_shot_rate` (+0.18, n=53) = underpowered conditional
precision → descriptor.

**Power-role decomposition (#5):** `power_roles_killed_by_evil` is **multi-causal** (healer + targeting
+ concealment), NOT a healer-proxy. Town bleeds power roles ~equally through the **night door**
(killed_by_evil −0.40) and the **day door** (lynched −0.38). The day door is already covered better by
the generic `town_mislynch_rate` (−0.60) — power-role-specific mislynch (−0.42) and per-role binary
(−0.20s) are **sparser and weaker**, so they're DIAGNOSTIC (which role town threw away), not outcome
proxies. `power_role_survival_rate` (+0.65) is survival↔win confounded → descriptive.

## Unifying insight — the "confirm-only" class

The SK's night-immunity creates an action class that is **private certainty needing public reveal**, and
it's transmission-capped *identically* to the investigator find: **investigator-finds-SK** AND
**vigilante-shoots-SK** both confirm-without-removing. So the `day_summary` reveal metric (planned)
should cover *any* private-confirmation → public-reveal, not investigator only. One build, both channels.

## Deceiver split (for the deceiver pass, not now)

The same night-kill events, re-attributed to the **killer**, become deceiver-offense metrics:
`wolf_power_roles_killed` vs `sk_power_roles_killed` (`wolf_power_role_targeting_rate` already exists; the
SK one is its parallel). Town view = combined-evil (protection); deceiver view = split-by-killer (offense).

## FINALIZED town outcome set

- **PRIMARY (de-lucked, |r|≈0.6):** `town_vote_accuracy`, `correct_elimination_rate`,
  `town_mislynch_rate`, `serial_killer_lynched`.
- **SECONDARY (de-lucked):** `wolf_elimination_rate`, `healer_town_save_rate` (+0.40),
  **`vigilante_wolf_kills_rate`** (+0.16, NEW), **`power_roles_killed_by_evil`** (−0.40, NEW, replaces
  the wolf-only relic), **`investigator_find_to_lynch_rate`** (+0.40, NEW — the CONVERSION metric that
  rescues the investigator channel; also the bottleneck gauge + G1 before/after hook).
- **HOLD → G1:** investigator find-*rate* cluster (descriptive — finding isn't the proxy, converting
  is), `found_wolf_day` (length-normalize). The day-summary reveal/led metric (LLM) is the diagnostic
  for conversion's "luck" cell (unbuilt).
- **Promising but underpowered:** `vigilante_skconfirm_to_lynch_rate` (n≈9).
- **DESCRIPTIVE only:** activity counts, exit methods, lumped `healer_save_rate`,
  `vigilante_correct_shot_rate`, `power_role_survival_rate` (confounded), per-role mislynch (diagnostic).

## Conversion metrics — the find/shot → LYNCH join (deterministic, no LLM)

A private night-confirmation only matters if it reaches a public removal. Join the confirmed PLAYER ID
(not role — crediting any-wolf-lynched would over-count) to `voted_player` on a later day:
- **`investigator_find_to_lynch_rate` (+0.396, p<0.001, n=117) — VALIDATED.** This is the metric the
  find-rate failed to be: `investigator_wolf_find_rate × win` is **dead (−0.03)** because finding ≠
  winning; *converting* the find to a lynch is what wins. The rate also **gauges the bottleneck
  directly**: baseline ~0.60 = 40% of confirmed wolves never lynched. **Promotes the investigator from
  HOLD→severed to a validated SECONDARY proxy + the G1 before/after gauge** (the prompt fix should
  raise it above 0.60). Caveat: conversion doesn't *isolate* the agent's causal role (a coincidental
  lynch still counts) — the day-summary reveal/led metric (LLM, unbuilt) does that.
- **`vigilante_skconfirm_to_lynch_rate` (0.78, r=+0.48, n=9) — promising, underpowered** (SK-shot is
  rare). Descriptive.

**Conversion (deterministic outcome) vs reveal/led (LLM causal) — the 2×2:** conversion-HIGH ×
reveal-LOW = lynched by luck; conversion-LOW × reveal-HIGH = revealed but disbelieved; conversion-LOW
× reveal-LOW = found-but-never-revealed (the agent's failure). Conversion is buildable now; reveal is
the diagnostic that disambiguates conversion's "luck" cell.

## Implemented (freeze-safe, measurement-only — `compute_metrics` + `schemas/metrics`)

`power_roles_killed_by_evil`, `vigilante_wolf_kills` + `vigilante_wolf_kills_rate`,
`investigator_find_to_lynch_rate`, `vigilante_skconfirm_to_lynch_rate`. **Two sanity-caught bugs:**
1. `power_roles_killed_by_evil` double-counted a power role co-targeted by BOTH wolves and the SK on one
   night → fixed by per-night victim dedup (180/180 match the deaths-based prototype, r=−0.402).
2. `vigilante_wolf_kills_rate` denominator `shots_taken + bullets_unused` **collapsed to `shots_taken`
   on recompute** — `vigilante_bullets` is persisted in 0/180 records (the stored `bullets_unused` was
   non-zero only because computed *live*), so the rate silently dropped to n=53 (the held-bullet games
   excluded — the very ones the supply denominator exists for) and degenerated into `correct_shot_rate`.
   **Fixed: denominate by the constant LOADOUT** (`GameConfig.vigilante_bullets` default = 2; supply is
   constant per game), and `bullets_unused` recomputed as `loadout − shots` (recompute-stable). → n=180,
   r=+0.157, p=.035 reproduced via the real path.

Reproduce all via `compute_game_metrics` over `batch_results/v6ab_*.jsonl` (rebuild Metrics from the
record's night/day resolutions).
