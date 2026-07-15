# The candidate ledger — every proxy tested against faction win

**What this is.** The full field the validated basket was selected from. The A/B ruler
([`report.md`](report.md)) ships eleven trusted proxies, three diagnostics, and five quarantined
fields; this ledger is the *whole set they came out of* — every proxy ever correlated against faction
win, so a reader can see what was tried and rejected, not only what shipped. **Forty-eight distinct
proxy definitions were win-tested**, across two campaigns: **32** in the 2026-06-11 v5 monotonicity
run (pooled N=50 / memory-off-only N=30) and **16 more** introduced or re-tested in the 2026-07-02
N=180 audit (3-faction v6ab).

**Method (one line).** Point-biserial correlation of each proxy against its *own faction's win*, with
the expected sign pre-registered; proxies flat or backwards against that sign are demoted out of the
basket. Faction win is the one non-circular skill anchor, so it judges the proxies rather than being
one of them.

**How to read an entry.** Each candidate carries its definition, its de-luck denominator, its phase,
and both campaigns' figures where it was tested twice — the **authoritative view (larger-N, current
3-faction epoch) is bold**. Validation shorthand: `v5` = the 2026-06-11 run (two figures = pooled
N=50 / off-only N=30); `N=180` = the 2026-07-02 audit. Sections run **by tier, then by role**
(town / wolves / serial killer). The house label "de-lucked" here reads as *opportunity-normalized* —
a rate over the chances the agent had — and for what that normalization does and does not remove, see
[`report.md`](report.md) §1.

> **Sources.** Figures are lifted, never re-derived, from the two campaign records:
> [`proxy_win_monotonicity.md`](proxy_win_monotonicity.md) (v5, 32 proxies) and
> [`metrics_audit/proxy_discovery_log.md`](metrics_audit/proxy_discovery_log.md) (N=180 audit,
> rescue + discovery). The tier vocabulary and the basket/diagnostic/do-not-use dispositions are the
> code frozensets in [`../../Agents/compute_metrics.py`](../../Agents/compute_metrics.py), lifted here
> from [`report.md`](report.md) §2–§4. Back to the ruler doc: [`report.md`](report.md).

**One pre-registered family is absent because it was never win-testable.** The claim-timing joins
(idea C0 — claim-with-find → next-round convergence, claim → correct elimination) need the persisted
`DaySummary.role_claims` field, which is an A4 (2026-06-20) addition present in **0/180** audit games
and 0/50 v5 games. Both validation epochs predate it, and claims are not deterministically recoverable
from `addressed_targets` (the stance vocabulary has no claim act), so the family produced no
correlation to report. It is unbuildable until a post-A4 batch is itself win-validated.

---

## Validated basket (11)

The trusted core — the `VALIDATED_BASKET_METRICS` frozenset, the proxies that powered the
static-memory proof. Read for independence the eleven collapse to ~six constructs; ★ marks the
pre-registered primary endpoint of each construct (see [`report.md`](report.md) §2).

### Town (8)

- **★ `correct_elimination_rate`** — *day vote* · de-luck: total eliminations. Lynches of a threat
  (wolf+SK) over all lynches. v5 +0.65 (both views); **N=180 +0.65**. The pre-registered primary for
  threat identification and the form the static-memory proof anchored on; the strongest, most stable
  town signal (holds in both pooled and treatment-free OFF views).
- **`town_mislynch_rate`** — *day vote* · de-luck: total eliminations. Lynches of a townmate over all
  lynches. v5 −0.65 (both); **N=180 −0.65**. The **exact complement** of `correct_elimination_rate`
  (both divide `total_eliminations`, and every lynch is anti-town or town, so the rates sum to 1 and
  correlate −1 by construction). One test shown with two signs, kept as a readable sibling, never
  counted as a second witness.
- **`town_vote_accuracy`** — *day vote* · de-luck: non-abstain town votes. Share of real town votes
  that hit a wolf/SK, per vote. v5 +0.62 / +0.57; **N=180 confirmed**. The per-vote grain of the same
  "town identifies threats" construct — correlated with the elimination rates, not identical, because
  votes that never decide a lynch still count.
- **`mislynches`** — *day vote* · count (not a rate). Raw count of townmate lynches. v5 −0.57 / −0.55.
  The raw-count near-duplicate of `town_mislynch_rate`, kept because it was the historically
  pre-registered form; slightly weaker than the rate (−0.57 vs −0.65).
- **★ `serial_killer_lynched`** — *game flag* · 0/1. Did the town remove the SK by day-vote, its only
  exit. v5 +0.64 / +0.85; **N=180 +0.64**. A *subset event* of correct eliminations (an SK lynch is an
  anti-town elimination), so partly coupled to the town cluster — but given its own ★ primary because
  it isolates the distinct third-faction objective.
- **★ `healer_town_save_rate`** — *night* · de-luck: healer action-nights. Intercepts of an attack on
  a townmate. v5 +0.36 / +0.33; **N=180 +0.40**. The good-play half of the healer split; every
  action-night carries live attack pressure by construction, so an action-night *is* an opportunity.
  The undifferentiated `healer_save_rate` was ~zero (see Context) — the town/friendly-fire split is
  what carries signal.
- **★ `power_roles_killed_by_evil`** — *night* · count, per-night victim-deduped. Landed wolf+SK
  night-kills that removed a town power role. **N=180 −0.40** (wolf-only −0.21). The outcome-side
  complement of healer night protection, but a *sixth* independent construct rather than a second
  healer witness because it moves with enemy targeting *and* the healer's reads *and* luck — wider
  causes. The restriction to *power* roles is a design choice: a generic town-night-death count has
  little variance to correlate, since the evils land a kill on most nights by construction.
- **★ `investigator_find_to_lynch_rate`** — *night→day* · de-luck: wolves confirmed. Confirmed wolves
  that reached a later lynch (conversion). **N=180 +0.40** (p<.001, n=117). The only validated
  investigator channel — the seat the investigator earns through *conversion*, not through *finding*,
  because the find-rate proxies did not track wins (Do-not-use tier).

### Wolves (1)

- **★ `wolf_unconditioned_blending_rate`** — *day vote* · de-luck: all living-wolf votes on lynch days.
  Wolf votes aligned with the day's lynch (camouflage). **N=180 +0.27**. The validated wolf-camouflage
  signal — voting with the room's plurality reads as helpful-townie cover. The loop's wolf blend credit
  rule was adopted *because* this validated.

### Serial killer (2)

- **★ `sk_kill_rate`** — *night* · de-luck: SK nights survived. Kills landed per night survived
  (survival-de-lucked offense). **N=180 +0.258**. The basket carries the *rate* rather than raw
  survival because raw SK survival correlates with SK win almost by definition (+0.555); dividing by
  nights survived isolates offense from longevity.
- **`sk_power_roles_killed`** — *night* · count. SK night-kills that removed a town power role.
  **N=180 +0.323**. Coupled to `sk_kill_rate` (power-role kills are a subset of all kills), so it is
  the second form of the SK-offense construct, not an independent witness.

---

## Diagnostic (3)

Win-validated on the N=180 audit, but adopted as *context* rather than independent basket evidence —
each is conditioned on the environment, coupled to a basket proxy, or a refinement of one
(`DIAGNOSTIC_METRICS` frozenset).

### Town (2)

- **`town_accusation_precision`** — *day discussion* · de-luck: all town accusations. Town accusations
  on true threats over all town accusations. **N=180 +0.34** (p<.001, n=175); split-halves +0.30 /
  +0.39. The **first** town-discussion proxy, filling a named hole (no town-discussion metric existed).
  But it covaries r=+0.558 with `town_vote_accuracy` — ~31% shared variance, the discussion-surface
  view of the same "town IDs threats" construct, not a second independent witness. Its value is that it
  measures that construct *upstream*, on the discussion surface, including players who never get to
  vote. **Incremental-validity test (2026-07-07): partial r vs town win given `town_vote_accuracy` =
  +0.02 (p=.76, n=175)**, halves −0.09 / +0.17 — no win signal beyond the vote endpoint; the
  diagnostic placement is confirmed on direct evidence (`metrics_audit/proxy_discovery_log.md` §④).
- **`investigator_find_next_round_convergence`** — *night→day* · de-luck: next-day town votes. Share
  of the next day's votes that land on a wolf found the prior night. **N=180 +0.31** (p=.001, n=117);
  split-halves +0.34 / +0.31. A timing-sensitive refinement of the validated `find_to_lynch_rate` —
  same find→conversion construct family; its extra content is convergence *speed*, not a new signal.

### Wolves (2)

- **`wolf_skconfirm_to_lynch_rate`** — *night→day* · de-luck: SKs confirmed. Wolf whiffs on the
  night-immune SK (the attack fails, confirming the SK to the pack) that reached a later SK lynch —
  the wolf-side mirror of ★ `investigator_find_to_lynch_rate` and of the vigilante's `skconfirm`
  form. **Added 2026-07-14, computed but UNTESTED** — no correlation run yet, and none is possible
  on the archive: the whiff was only disclosed to wolves in the current prompt epoch (commit
  51de191), so pre-epoch games measure a conversion the wolf didn't know it could make. Status:
  diagnostic-at-best pending new-epoch games; never a verdict carrier.
- **`wolf_power_kill_rate`** — *night* · de-luck: power-role-alive-nights. Landed wolf power-role kills
  per opportunity. **N=180 +0.31** (p=.002, n=103, `sk_lynched=1` stratum); split-halves +0.26 /
  +0.38; pooled +0.13 (~null). The **first wolf-night proxy to clear the bar**, rescued from a pooled
  null once conditioned on the environment. Pooled it dilutes to null because the 77/180 games where
  wolves cannot win (the SK wins by default unless lynched) carry zero wolf-skill information;
  conditioning on `sk_lynched=1` removes them. Diagnostic because it only *expresses* conditioned on
  that environment.

---

## Do-not-use (5)

Wrong-sign or uninterpretable against faction win (`DO_NOT_USE_METRICS`); the Langfuse push renames
each with a `dnu_` prefix and a `tier="do_not_use"` tag so it can never be silently averaged into a
verdict.

### Town (4)

- **`investigator_threat_find_rate`** — *night* · de-luck: investigations. Investigations that found a
  threat over all investigations. v5 −0.09; **N=180 −0.00** (n=169). Flat-to-wrong-sign in both
  campaigns — finding threats does not predict town wins; only the conversion (`find_to_lynch_rate`)
  does.
- **`investigator_wolf_find_rate`** — *night* · de-luck: investigations. Investigations that found a
  wolf over all investigations. v5 −0.14; **N=180 −0.03**. Same null-to-negative pattern as
  `threat_find_rate` — part of the rejected find-rate cluster.
- **`investigator_threat_find_lift`** — *night* · find-rate over prior chance. Find-rate lifted over
  the prior base chance of a threat. v5 −0.02. Null in v5, part of the find-rate cluster; not re-tested
  at N=180.
- **`investigator_found_wolf_day`** — *night→day* · day-number (earliness). The day-number a wolf was
  first found. v5 +0.38 (p=.039, wrong-sign scare); **N=180 +0.15 n.s.** (scare dissolved). The v5
  "wrong-sign" scare — later find ↔ more town wins, backwards — **dissolved to +0.15 n.s. at N=180**:
  small-N noise plus mild game-length coupling (villager wins take longer, and the proxy isn't
  length-normalized), not a robust backwards relationship. Quarantine stands, but for the softer
  reason — **null, not wrong-sign**.

### Wolves (1)

- **`wolf_steering_rate`** — *day vote* · de-luck: mislynch days. Mislynch days the wolf plurality
  steered over all mislynch days. v5 −0.06 (n=24) / +0.26 (n=12). Structurally **cannot separate
  leading a bandwagon from joining one** — voting where the town was already headed looks identical to
  driving it. Uninterpretable against win, and the reason wolf day-offense stays effectively
  unmeasured.

---

## Context (validated-but-not-adopted · weak · descriptors) (24)

Validated or descriptive, but not promoted into a code tier — a narrower slice of a basket construct,
an error-companion, a superseded raw count, or a plain game descriptor. Everything here defaults to
`tier="diagnostic"` on push.

### Town (17)

- **`wolf_elimination_rate`** — *day vote* · de-luck: all lynches. Lynches of a wolf over all lynches.
  v5 +0.37 / +0.26. Validated (moves with town win) but a narrower slice of `correct_elimination_rate`
  (wolf-only, excludes SK lynches), so not adopted into the frozenset.
- **`healer_friendly_fire_save_rate`** — *night* · de-luck: healer action-nights. Saves that shielded
  an evil target over action-nights. v5 −0.31 / −0.44. The validated error-companion of the good-play
  save rate (the split works — negative as expected), the error side of the healer construct; not in
  the frozenset.
- **`vigilante_friendly_fire_shots`** — *night* · count. Shots that hit a townmate. v5 −0.29 / −0.36;
  **N=180 −0.29** (audit verdict: weak-but-informative, not promoted). Validated error-companion
  (negative as expected, the dangerous vigilante failure); not in the frozenset.
- **`vigilante_wolf_kills_rate`** — *night* · de-luck: bullet loadout. Landed wolf-kills over the fixed
  bullet loadout. **N=180 +0.16** (p=.035). Validated secondary (weak-but-informative, de-lucked by
  the fixed loadout); not adopted into the frozenset.
- **`healer_save_rate`** — *night* · de-luck: healer action-nights. Undifferentiated saves over
  action-nights. v5 +0.10 / −0.13 (~null). The undifferentiated form is ~zero, exactly as the v2
  design predicted — superseded by the town/friendly-fire split. Kept as the record of *why* the split
  was needed.
- **`healer_wolf_block_rate`** — *night* · de-luck: healer action-nights. Saves blocking a wolf kill
  over action-nights. v5 +0.28 / +0.16. Weak — positive direction but not significant on the OFF-only
  view; a narrower slice than `town_save_rate`.
- **`investigator_wolves_found`** — *night* · count. Count of wolves found. v5 +0.25 / +0.13. Weak — a
  raw count carrying the survival confound; the conversion (`find_to_lynch_rate`) is the validated
  form.
- **`vigilante_correct_shot_rate`** — *night* · de-luck: shots taken. Shots hitting a threat over shots
  taken. v5 +0.30 (n=36) / +0.43 (n=21). Underpowered conditional precision — defined in only 36/21
  games (a vigilante that never shoots is undefined), so directionally promising but too thin to
  validate. **N=180 re-test (2026-07-07): +0.18 (p=.20, n=53)**, halves +0.14 / +0.08 — sign holds,
  still unvalidated; the vigilante shot in only 53/180 games at this epoch, so the defined subset
  stays thin (`metrics_audit/proxy_discovery_log.md` §④). **Status (2026-07-07): logically-anchored
  decision endpoint** — the sign is definitionally safe (shooting evil IS a threat elimination, the
  construct `correct_elimination_rate` validates), so it may read the vigilante-night cell in an A/B
  (arm-pooled), never carry a headline verdict; see the cell-coverage map in `report.md` §3.
- **`vigilante_evil_shots`** — *night* · count. Count of shots hitting evil. v5 +0.15 / +0.15. Weak — a
  raw count, uninformative once de-lucked into the rate forms.
- **`town_first_accuser_credit_rate`** — *day discussion* · de-luck: all town accusations. Correct
  *early* accusations (accuser among the first two of a true threat) over all town accusations.
  **N=180 +0.21** (p=.007; confirm-half only). Weak-real — sign-stable across halves but significant
  only on the confirm half, and sub-Bonferroni for its family.
- **`town_accusation_to_vote_conversion`** — *day discussion→vote* · de-luck: all town accusations.
  Accusations the accuser later votes over all town accusations. **N=180 +0.17** (discover-half null).
  Null / undecidable — holds sign on the full set but ~null on the discover half; the follow-through
  construct is largely already inside `town_vote_accuracy`.
- **`investigator_postfind_accusation_precision`** — *day discussion* · de-luck: post-find investigator
  accusations. Investigator accusation precision on days strictly after a private wolf-find.
  **N=180 +0.19** (coverage 109/180); split-halves +0.19 / +0.19. Suggestive, coverage-limited — a
  consistent-sign hint that the investigator sharpens after a find, but under-powered per half and
  exploratory.
- **`vigilante_bullets_unused`** — *night* · count. Bullets left unfired. v5 +0.16 (context sign). An
  activity descriptor, not a skill proxy — no pre-registered sign.
- **`vigilante_shots_taken`** — *night* · count. Bullets fired. v5 −0.16. Activity descriptor, the
  mirror of `bullets_unused`; no skill interpretation.
- **`game_length`** — *game* · days. Game duration in days. v5 +0.25 / +0.33. A confounder, not a skill
  proxy — longer games correlate with villager wins, which is why non-length-normalized earliness
  proxies (`found_wolf_day`) are suspect. Kept as the confounder to control for.
- **`tie_count`** — *day vote* · count. Count of tied votes. v5 −0.00. A game descriptor with no win
  correlation.
- **`no_vote_count`** — *day vote* · count. Count of no-decision days. v5 — (degenerate). A game
  descriptor; too few defined to correlate.

### Wolves (3)

- **`power_roles_killed_by_wolves`** — *night* · count (scored two ways). Landed wolf power-role kills,
  correlated both vs villager win (protection failure) and vs wolf win (offense). v5 −0.34 vs villager
  win; **N=180 +0.23 vs wolf win** (offense, `sk_lynched=1`). Both views superseded — the town view by
  the victim-deduped `power_roles_killed_by_evil` (basket), the wolf view by the rate
  `wolf_power_kill_rate` (diagnostic). Kept as the raw count both were derived from.
- **`wolf_accusation_on_town_rate`** — *day discussion* · de-luck: all wolf accusations. Wolf
  accusations aimed at town over all wolf accusations. **N=180 −0.33** (p<.001; split-halves −0.31 /
  −0.37). The **pre-registered sign was falsified** — expected + (framing offense should help wolves),
  observed −0.33, both halves significantly negative. The surprise *is* the finding: wolves that spend
  accusations on town lose more, while wolves that accuse a real threat (the SK or the co-wolf) win
  more, because attacking town is visible aggression that exposes and accusing a threat reads as townie
  cover. A blending discovery (the mirror of `wolf_unconditioned_blending_rate`) that must be
  re-registered with the corrected sign before it can be validated as a proxy.
- **`wolf_killed_healer_day`** — *night* · day-index. The day-index a wolf killed the healer. v5 −0.51
  (p=.041, n=16) / +0.00 (n=9). Significant but thin — the pooled figure rests on 16 games and goes to
  exactly null on the treatment-free OFF-only view (n=9). Directionally sensible (kill the healer
  early) but too underpowered to trust.

### Serial killer (4)

- **`sk_killed_wolf`** — *night* · count. SK night-kills that removed a wolf. **N=180 +0.30**.
  Validated companion (positive — the SK benefits from thinning the wolves); not adopted into the
  frozenset.
- **`sk_unconditioned_blending_rate`** — *day vote* · de-luck: all living-SK votes on lynch days. SK
  votes aligned with the day's lynch (camouflage). **N=180 +0.20**. Suggestive — positive and the SK
  analogue of wolf blending, but fails the ~12-test Bonferroni correction, so not adopted.
- **`sk_nights_survived`** — *night* · count. Count of nights the SK survived. v5 +0.31 / +0.17.
  Survival↔win is confounded almost by definition (an SK that survives to the end often wins), so the
  raw count is de-lucked into `sk_kill_rate` rather than used directly.
- **`sk_kills_landed`** — *night* · count. Raw count of SK kills. v5 +0.35 / +0.37. The raw-count form;
  de-lucked into `sk_kill_rate` (kills per night survived), which is the basket form.

---

## Rejected (null / wrong-sign) (2)

Failed on the authoritative view — null once at N, or backwards on a thin sample.

### Wolves (2)

- **`wolf_power_role_targeting_rate`** — *night* · de-luck: wolf targets. Wolf night-targets that were
  power roles over all wolf targets. v5 +0.21; **N=180 −0.02** (still-null). Rejected — **targeting ≠
  killing**. Flat-null everywhere at N=180: a wolf that aims at a power role but the healer saves or it
  misses carries no signal. Intent without conversion.
- **`wolf_killed_investigator_day`** — *night* · day-index. The day-index a wolf killed the
  investigator. v5 +0.33 (n=15) / +0.71 (p=.047, wrong-sign, n=8). Rejected — wrong-sign and
  underpowered; the OFF-only view is +0.71 (later kill ↔ more wolf wins, backwards) on n=8.
  Uninterpretable.

---

## Degenerate-underpowered (3)

Too few defined games to read a correlation at all.

### Town (1)

- **`vigilante_postfind_accusation_precision`** — *day discussion* · de-luck: post-shot vigilante
  accusations. Vigilante accusation precision after a landed shot. **N=180** n=16 (split-halves −0.06 /
  −0.25). Too thin to read — defined in only 16/180 games, and the halves disagree in sign. Undecidable
  at N.

### Wolves (2)

- **`wolf_blending_rate`** — *day vote* · de-luck: wolf votes on wolf-elimination days. Wolf votes
  aligned on wolf-elimination days. v5 — (n=20 / n=14). Degenerate — defined in too few games (wolves
  won only 2/30 OFF), so no correlation is computable. The old-system blending evidence (12%→48% across
  two batches) is unaffected, but v5 cannot confirm it here.
- **`wolf_dissent_rate`** — *day vote* · de-luck: wolf votes on wolf-elimination days. Wolf votes
  dissenting on wolf-elimination days. v5 — (n=20 / n=14). Degenerate — the complement of
  `wolf_blending_rate`, same sub-N problem.

---

*Written 2026-07-06, lifting figures from the two campaign records
([`proxy_win_monotonicity.md`](proxy_win_monotonicity.md),
[`metrics_audit/proxy_discovery_log.md`](metrics_audit/proxy_discovery_log.md)) and the tier
dispositions from [`report.md`](report.md) §2–§4. This ledger is the full field; the ruler doc keeps
only the survivors.*
