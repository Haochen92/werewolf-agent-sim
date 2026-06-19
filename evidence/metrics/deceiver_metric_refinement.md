# Deceiver metric refinement — wolf + SK signal pass (2026-06-18)

First-principles pass on the deceiver proxies (all 180 v6ab games; wolf win 39, SK win 77 — SK-favored
epoch, so wolf correlations run on half the positive base → modest power). Companion to
`town_metric_refinement.md`. Same de-luck/denominator discipline + an added **outcome-proximity** lens.

## Framework

Deceiver value = **concealment** (don't get caught: blend + low detectability) + **offense**
(night-kills/steering that advance the win). Win condition shapes which axis matters:
- **Wolf wins by PARITY** (numbers) → concealment-driven; needs the SK *gone*.
- **SK wins by being LAST** (elimination) → concealment + offense + survival.

**Outcome-proximity lens (the key discipline):** a metric's correlation with win can come from being
*upstream* (a skill that causes wins) or *downstream* (≈ the win restated). The win-correlation gate
can't tell them apart, so we add **proximity = corr(metric, survival-backbone)**: low = upstream skill,
high = outcome-echo. The ideal proxy is high corr-with-win AND **low** corr-with-survival.

## Results (× faction win)

```
WOLF
  blending (unconditioned)        +0.270 p<.001    concealment, VALIDATED, upstream
  suspicion_drawn                 −0.404 p<.001    HELD (denominator + tautology + opponent-coupled, see below)
  power_roles_killed (night)      +0.104 p=.166    night-offense null (rate −0.10 → not a denominator artifact)
  steering_rate                   +0.173 p=.086    BROKEN metric (lead/blend conflation) — not evidence either way
  [environmental] sk_lynched      +0.455 p<.001    the wolf's BIGGEST correlate — not a wolf action

SK
  suspicion_drawn                 −0.714 p<.001    HELD (most outcome-proximate; ≈ "got lynched" = "lost")
  nights_survived                 +0.555 p<.001    core but survival↔win TAUTOLOGY → power, not skill
  power_roles_killed (offense)    +0.323 p<.001    VALIDATED offense
  kill_rate (kills/nights)        +0.258 p<.001    de-lucked offense (raw kills +0.61 is survival-confounded)
  unconditioned_blending          +0.196 p=.019    SUGGESTIVE only (fails ~12-test Bonferroni .004)
  killed_wolf (cross-faction)     +0.334 raw / +0.303 partial|survival   VALIDATED SKILL (de-confounded)
```

## Findings

1. **Wolf = concealment-validated; offense is night-null + day-UNMEASURED (not "null").** Night-kill
   offense genuinely doesn't convert (rate −0.10; structurally it feeds the SK — `town_mislynch ×
   wolf win = −0.04` but `× SK win = +0.61`). BUT the wolf's *actual* offensive lever is **day-side
   steering**, and `wolf_steering_rate` **cannot distinguish leading a bandwagon from joining it**
   (voting where town already headed = blending). So we have *no clean wolf day-offense instrument* —
   the +0.17 is a lead/blend mixture, not evidence offense is null. Reframe honestly: **night-offense
   null, day-offense unmeasured.** (The fix is a real build — §Builds.)
2. **The wolf is the most environment-dependent faction.** Its biggest win-correlate is `sk_lynched`
   (+0.455) — *the town removing the SK for it* — larger than any wolf action.
3. **SK offense is real and the cross-faction skill is the keeper.** `sk_killed_wolf` survives the
   survival control (partial +0.30; within long-survivors 85% vs 53% win): the lone SK must address
   the pack or face a 2v1 at parity. This is the one finding with a *mechanism*, not just an r, and
   it's low-proximity (corr-with-survival only +0.15) → genuine upstream skill.

## CAVEATS the critique tightened (carried into the set)

- **`suspicion_drawn` is HELD, not shipped** — three problems: (a) **outcome-proximate** (for the
  night-immune SK, votes-at-SK is the precursor to its only removal → ≈ "lost"; same status as
  survival, NOT a cleaner signal — do not rank above survival); (b) **opponent-coupled** — it's
  `town_vote_accuracy` from the other seat, so "town voted well" and "SK concealed poorly" are ONE
  event, never two pieces of evidence; (c) **denominator underspecified** (the vigilante trap again):
  wolf is a 2-member team vs solo SK → needs **per-living-member, alive-window** normalization
  (`votes-at-member / total-votes-while-that-member-alive`, per member) or it inherits team-size +
  attrition-survival confounds. **Spec the denominator before computing.**
- **`sk_unconditioned_blending` = SUGGESTIVE** (p=.019 fails Bonferroni .004); kept for
  parallel-construction prior plausibility, not co-equal "validated."
- **"SK detrimental to wolf" is the FLAT average** (+0.455). It's really **situational** — the SK
  helps the wolves *early* (adds chaos/cover) and hurts them *late* (competes for parity). Timing
  slice pending (same interaction logic as the SK→wolf-kill timing).
- **Wolf power-kill could be effect-modified** (strong but situation-flipping → averages to ~0); only
  3 power roles/game so the count is coarse (0–3). The flat r isn't proof of null.

## Implemented (freeze-safe, recompute-verified — `compute_metrics` + `schemas/metrics`)

Ship-now (deterministic, denominator-clean): `sk_power_roles_killed` (+0.32), `sk_kill_rate` (+0.26),
`sk_unconditioned_blending_rate` (suggestive tag), `sk_wolf_kills` → `sk_killed_wolf` (+0.30
de-confounded). `wolf_power_roles_killed` already exists as `power_roles_killed_by_evil`'s wolf
component (`power_roles_killed_by_wolves`) — descriptive. All reproduce their prototype r via the real
`compute_game_metrics` path.

## Follow-ups executed (2026-06-18, same session)

- **`suspicion_drawn` SHIPPED** with the per-member alive-window denominator (`votes-at-member /
  total-votes-on-days-member-alive`, mean over members). Holds (WOLF −0.350, SK −0.654 — attenuated
  from the dirty whole-game −0.404/−0.714, not collapsed). **KEEP — it's the EFFECT-side of the
  concealment axis** (`blending` = the upstream cause; same axis, so represented ONCE in any aggregate
  but both kept for diagnosis), and one of our **few discussion-surface signals** (reflects blend +
  redirect). It is **composite**: low suspicion = vote-blend + verbal-redirect + not-caught-in-a-lie
  [skills] + not-a-priority-target + weak opposing town [noise] — so it's a **stand-in for the
  unbuilt discussion-action metrics**, and decomposing its causes IS the discussion-metric program.
  Per-faction scoring dissolves the cross-seat `town_vote_accuracy` mirror (they never co-occur in one
  faction's aggregate). Tier: composite + opponent-coupled; see `score_tier_design.md`.
- **Wolf lead-vs-blend day-offense — BUILT, result = null (so "concealment-dominated" is now MEASURED).**
  Using `addressed_targets.stance=='accusation'` + msg `seq`, a wolf "led" a mislynch if it was in the
  earlier half of the victim's accusers. `wolf_led_mislynch × wolf win = +0.05 (p=.49, null)`; led-≥1
  win 0.29 vs never-led 0.20 (NS). Even cleanly isolated from blending, wolf day-offense doesn't convert.
  Descriptive datum: **town mislynches itself — 109/169 mislynch days had NO wolf among the accusers.**
- **Wolf-attacks-SK = a 4th "confirm-only" lever, COMPLETELY unconverted.** A failed wolf night-kill on
  the immune SK is a private SK-confirm (like inv-finds-SK / vig-shoots-SK). But `corr(wolf_attacked_sk,
  sk_lynched) = +0.005` — attacking the SK has ZERO effect on its removal (lynch rate 0.58 vs 0.57). The
  wolf gets its highest-value info free (exposing its own win-blocker) and never acts on it. **Capability
  gap → a memory/strategy-teaching target**, not a metric. (binary × wolf win +0.02 null; the +0.47
  "attacker & SK-lynched-after" is just the known SK-removal effect, not attack-causation.)
- **⭐ SK-lynch = the KEYSTONE event of the game.** SK never lynched → TOWN 0.00 / WOLF 0.00 (SK wins by
  default, since only a vote removes it). Optimal timing is faction-split: **town wants it EARLY** (≤d3:
  town 0.68 vs late 0.59), **wolf wants it LATE** (≥d4: wolf 0.41 vs early 0.32 — let the SK thin the
  town first). Confirms "SK helps the wolf early (thinning), hurts late (parity)" — the situational form
  of "SK detrimental to wolf."

## HELD / Builds (not this batch)

- **HELD — `wolf_suspicion_drawn` / `sk_suspicion_drawn`:** decide the per-member alive-window
  denominator first (spec above), ship with the tautology+opponent caveat.
- **BUILD — clean wolf day-offense (lead vs blend):** use `addressed_targets.stance` + message `seq`
  (CONFIRMED present in records) — did the wolf's accusation against the eventual mislynch victim
  *precede* the bandwagon (leadership) vs land after it formed (blending)? Separates steering from
  blending deterministically. This is the only thing that converts "wolf is concealment-dominated"
  from absence-of-evidence into a measured claim.
- **Situational slices (the real frontier):** timing cuts for cross-faction targeting ("did the SK
  kill a wolf before night N?", SK-early-help/late-hurt-wolf) — stop averaging over situations, slice
  by them. `sk_killed_wolf` is the first; the general "right target given board state" is situational
  decision-quality (criticality eval territory), not a flat proxy.
