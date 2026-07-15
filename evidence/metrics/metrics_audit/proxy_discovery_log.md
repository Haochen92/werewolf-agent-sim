# Metrics Audit — Workstream 1: proxy rescue & discovery

> **What this is.** The chronological log of the proxy-expansion exploration opened 2026-07-02:
> could some rejected proxies be real-but-muted, and can new deterministic proxies fill the known
> role × action-space holes? Later entries supersede earlier ones. Sibling workstream:
> [`scheduler_bias_log.md`](scheduler_bias_log.md) (whether the discussion scheduler *causes* some
> of these holes). Companions: the original validation record
> ([`../proxy_win_monotonicity.md`](../proxy_win_monotonicity.md),
> [`../design/town_metric_refinement.md`](../design/town_metric_refinement.md),
> [`../design/deceiver_metric_refinement.md`](../design/deceiver_metric_refinement.md)), the apparatus verdict
> ([`../../evaluation/metrics/report.md`](../../evaluation/metrics/report.md)), and the hardening
> pass that re-verified and tiered the basket
> ([`../../evaluation/hardening_pass/experiment_log.md`](../../evaluation/hardening_pass/experiment_log.md) §2.4–2.5, §4.8).
>
> **Status: Ideas A/B/C run (2026-07-02, all $0/ZERO-LLM, N=180 v6ab).** Headlines — A2
> `wolf_power_kill_rate` RESCUED (first wolf-night proxy to clear the bar, once conditioned on the
> `sk_lynched` environment); B1 `town_accusation_precision` DISCOVERED (first town-discussion proxy,
> diagnostic — couples with vote accuracy); C1 find→next-round convergence CONFIRMED; B6 pre-registered
> sign FALSIFIED (a blending discovery); C0 claim-joins BLOCKED (0/180 `role_claims`). Full results,
> tables, and per-candidate verdicts in §3. Ideas D–F not started.

## §1 · Motivation — the accepted state at the start of this exploration

The existing basket was earned honestly: every proxy is computed deterministically from the game
record (no LLM in the computation), validated by point-biserial correlation against its own
faction's win (N=50 pooled, N=180 for the 3-faction set), sign-checked, and tautology-screened.
The 2026-07 hardening pass re-verified those claims in code and enforced the tiering
(`VALIDATED_BASKET_METRICS` / `DO_NOT_USE_METRICS` in `Agents/compute_metrics.py`). This snapshot
is the incumbent — the exploration below is about its *holes*, not its errors.

**Accepted metrics by role × action space (2026-07-02):**

| Role × action space | Accepted metric | r vs own-faction win | Notes |
|---|---|---|---|
| Town (all) · day vote | `town_vote_accuracy` | +0.62 | per-vote, votes on true threats |
| Town (team) · day outcome | `correct_elimination_rate` / `town_mislynch_rate` | +0.65 / −0.65 | the paired-A/B headline basket |
| Town (team) · day outcome | `serial_killer_lynched` | +0.64 | binary |
| Healer · night | `healer_town_save_rate` (ff variant −0.31) | +0.40 | |
| Investigator · night→day | `investigator_find_to_lynch_rate` | +0.40 | conversion ONLY — find-rate cluster rejected (wrong-sign) |
| Vigilante · night | `vigilante_wolf_kills_rate` / `friendly_fire_shots` | +0.16 / −0.29 | weak-but-informative; de-lucked by fixed loadout |
| Town (env.) · night defense | `power_roles_killed_by_evil` | −0.40 | |
| Wolf · day (disc.+vote) | `wolf_unconditioned_blending_rate` | +0.27 | camouflage/defense |
| Wolf · night | *(none)* | — | night offense validated null |
| SK · night | `sk_kill_rate` / `sk_power_roles_killed` / `sk_killed_wolf` | +0.26 / +0.32 / +0.30 | kill_rate de-lucked by nights survived |
| SK · day | `sk_unconditioned_blending_rate` | +0.20 | suggestive only (fails ~12-test Bonferroni) |
| Wolf+SK · discussion skill | the v7 tagger (LLM, omniscient) | partial r +0.56 / +0.60 | validated metric, uncalibrated, N=24 |
| Town · discussion | *(none)* | tagger town ≈ +0.02 | measured only via its vote endpoint |

Quarantined (`dnu_`): the investigator find-rate cluster (`found_wolf_day` +0.38 is significantly
*wrong-sign* from game-length confounding; `threat_find_rate`, `wolf_find_rate`,
`threat_find_lift`), and `wolf_steering_rate` (structurally can't distinguish leading from
joining). Caveated: `wolf/sk_suspicion_drawn` (outcome-proximate tautology — town's vote accuracy
seen from the other seat).

**The holes, named:** no town discussion proxy; no investigator/vigilante day-discussion proxies
(claim timing, revealing a find); no accepted wolf-night proxy; deceiver discussion measurable
only through an uncalibrated LLM tagger.

**Why the wolf-night null may be muted rather than true.** Three compounding mechanisms: (a)
*power* — wolves won 39/180 in the validation epoch, so point-biserial vs a rare binary is noisy;
(b) *environmental dominance* — the biggest wolf-win correlate is `sk_lynched` (+0.455), an event
wolves barely influence, so the SK axis swamps wolf-skill variance and no wolf proxy has been
re-tested conditioning on it; (c) *construct coarseness* — "killed a power role" ignores when and
at what information cost. Two further general muting mechanisms apply basket-wide: game-level
aggregation discards per-decision power (the loop's credit machinery scores per decision and has
never been pointed at proxy validation), and *meta-boundedness* — a proxy can be null in this
epoch simply because current agents never exhibit the behavior (the 109/169 no-wolf-among-accusers
datum), which bounds what is measurable, not what matters. Nulls here are epoch-stamped, not
permanent.

## §2 · Design — the candidate moves, costed

The discovery pattern worth stating once: where a construct needs semantic judgment, have the LLM
*label events* (claims, defenses, accusation types) and compute *deterministic statistics over the
labeled events* — LLM reach, countable metrics, and only the event labels need calibration. The
tagger's deceiver result is the existence proof.

| Idea | Build | Experiment cost | Explainability | Read |
|---|---|---|---|---|
| **A. Rescue pass on muted proxies** — partial on `sk_lynched`, length-normalize, re-run point-biserial on the existing 180 games | small — one stats script over existing records | $0 | high — same method as the incumbent validation | Best first move; directly answers "was wolf-night muted"; no new constructs |
| **B. Accusation-graph proxies** — from `addressed_targets` + stance + `seq`: accusation precision, first-accuser credit, accusation→vote conversion | moderate — parser + ~4 metrics + validation | $0 | high — countable, no LLM | Highest value: the town-discussion hole, plus investigator/vigilante post-find discussion for free; upstream of the already-validated `town_vote_accuracy` |
| **C. Claim-timing conversion joins** — from the extracted `role_claims`: claim-with-find → next-vote convergence, claim → correct elimination | small–moderate | $0 | high | Fills the investigator/vigilante day gaps; mirrors the proven `find_to_lynch` template |
| **D. Deterministic night-read proxies** — heat-aware kill quality (did the wolf kill its top accuser / the most credible townie; did the healer protect the hottest power role) | moderate | $0 | high | The credible path to an accepted wolf-night proxy; de-luck design needs care — condition on knowable heat, never outcome |
| **E. Tagger schema extension** — info-gain tag for town turns + typed claim/defense events, added to the existing once-per-day call | small (prompt+schema) | ~$0 marginal; ~2h human labeling to calibrate | medium — LLM judgment, but events-then-count keeps the metric explainable | Do after B — if deterministic accusation metrics already carry town signal, this may be unnecessary |
| **F. Per-decision proxy validation** — repoint `credit_backfill`/`measure` de-luck machinery at proxy validation | moderate | $0 | medium-high | The power upgrade for everything above; more moving parts to explain |

**Sequencing:** A → B → C (all $0, deterministic, reuse the existing validation harness), then
decide D–F by what A–C leave unexplained.

**Pre-committed discipline (before any result is looked at):** ~30 proxies have already been
tested against win, so mining more raises the false-positive floor. Every new/rescued proxy gets a
pre-registered expected sign; the 180 games are split 50/50 (discover on one half, confirm on the
other) or Bonferroni is applied across the family; nothing outcome-proximate ships (the
`suspicion_drawn` lesson); every verdict is epoch-stamped (re-validate when the meta shifts, e.g.
after any scheduler or disclosure change from the sibling workstream).

## §3 · Implement → verify → decide

### ③.0 Pre-registration (2026-07-02, written BEFORE any correlation was computed)

**Validation set.** N=180 v6ab (`batch_results/v6ab_{baseline,skboth,skobs,sksp,townobs,townsp}.jsonl`,
all `status==success`; winners villagers 64 / wolves 39 / SK 77). This is the 3-faction epoch on which
`sk_lynched +0.455`, the wolf-night null, and the deceiver-refinement results were measured
(`../design/deceiver_metric_refinement.md`), so it is the comparable set for the rescue. `point_biserial` from
`evaluation/src/core/stats.py`; partial correlation added there (residualization, reported with n and df).

**Confirmation protocol.** The 180 games are 30 role-seeds × 6 memory-arms (`game_id` is pinned across
arms). Split on `game_id` by SHA1 parity → a discover half and a held-out confirm half (arm-siblings of
a seed stay together, so no near-duplicate leaks across halves). Every candidate's r is reported on BOTH
halves; a candidate is only called rescued/discovered if it holds sign (and roughly magnitude) on the
held-out half. Secondary check: Bonferroni across each idea's pre-registered family. Signs below are
frozen; a surprise sign IS the finding and will be reported as such, never revised post-hoc.

**Idea A — rescue of muted proxies.** Family A-wolf (vs WOLF win) + A-inv (vs VILLAGER win).

| id | candidate | vs win of | expected sign | conditioning applied |
|---|---|---|---|---|
| A1 | `power_roles_killed_by_wolves` (count) | wolves | **+** | raw · within sk_lynched=0/1 · partial \| sk_lynched · partial \| game_length · partial \| both |
| A2 | `wolf_power_kill_rate` = A1 / `power_role_alive_nights` | wolves | **+** | same as A1 |
| A3 | `wolf_power_role_targeting_rate` | wolves | **+** | same as A1 |
| A4 | `investigator_found_wolf_day` (day #) | villagers | **−** (earlier=better) | raw · partial \| game_length · normalized `found_wolf_day/game_length` |
| A5 | `investigator_threat_find_rate` | villagers | **+** | raw · partial \| game_length |
| A6 | `investigator_wolf_find_rate` | villagers | **+** | raw · partial \| game_length |

A4–A6 are a DIAGNOSIS of the known wrong-sign cluster (does length-normalization flip the sign back?),
NOT an un-quarantine bid — un-quarantine needs the full bar and split-half confirmation.

**Idea B — accusation-graph proxies** (parsed from `day_channel` `addressed_targets` stance=accusation +
`seq`). Primary family B-town (vs VILLAGER win); secondary B-post-find + B-wolf reported but flagged
coverage-limited / exploratory.

| id | candidate | vs win of | expected sign |
|---|---|---|---|
| B1 | `town_accusation_precision` = town accusations on true threats / all town accusations | villagers | **+** |
| B2 | `town_first_accuser_credit_rate` = town accusations that are on a true threat AND the accuser is among the first 2 distinct accusers of that target / all town accusations | villagers | **+** |
| B3 | `town_accusation_to_vote_conversion` = town accusations where the accuser later votes the accused target / all town accusations | villagers | **+** |
| B4 | `investigator_postfind_accusation_precision` (precision on days strictly after a wolf-find) | villagers | **+** (exploratory, coverage-limited) |
| B5 | `vigilante_postfind_accusation_precision` (precision after a landed shot) | villagers | **+** (exploratory, coverage-limited) |
| B6 | `wolf_accusation_on_town_rate` = wolf accusations targeting town / all wolf accusations | wolves | **+** (framing offense; low prior — the lead-vs-blend null) |

**Idea C — claim-timing conversion joins** (vs VILLAGER win).

| id | candidate | vs win of | expected sign |
|---|---|---|---|
| C1 | `investigator_find_next_round_convergence` = fraction of town votes on day d+1 that target a wolf found on night d | villagers | **+** |

C0 (claim-with-find → convergence; claim → correct-elimination) is pre-registered as BLOCKED pending a
coverage check on the persisted `role_claims` field; if coverage is thin it is reported descriptively
(direction only) with no validation claim.

### ③.A Rescue pass on muted proxies (`proxy_rescue.py`, 2026-07-02, N=180 v6ab)

Ran the pre-registered A1–A6 with the two conditionings. **The catch surfaced immediately and it is the
whole story:** the `sk_lynched=0` stratum is DEGENERATE for every wolf proxy (`— (n=77)`) because
**wolves never win when the SK is not lynched** — the SK wins by default (only a day-vote removes it), so
wolf-win is a structural 0 across all 77 `sk_lynched=0` games. All 39 wolf wins live in the `sk_lynched=1`
stratum. That is the mechanism behind the "wolf night-offense null": the flat point-biserial pools 77 games
where a wolf victory is *impossible regardless of play* into the same correlation as the 103 where it is on
the table, diluting any real signal toward zero. Conditioning on `sk_lynched` is not a fishing knob here —
it removes games that carry no wolf-skill information by construction.

Wolf candidates vs wolves-win (r; `sk1:` = split-half of the conditioned signal, discover / confirm):

| id | metric | raw | sk_lynched=1 | partial\|sk | partial\|len | partial\|both | sk1 disc / conf |
|---|---|---|---|---|---|---|---|
| A1 | `power_roles_killed_by_wolves` (count) | +0.104 (p=.166) | **+0.232 (p=.018, n=103)** | +0.178 (p=.017) | +0.110 (p=.143) | +0.192 (p=.010) | +0.266 (p=.037) / +0.183 (p=.253) |
| A2 | `wolf_power_kill_rate` (per opportunity) | +0.130 (p=.082) | **+0.307 (p=.002, n=103)** | +0.222 (p=.003) | +0.103 (p=.170) | +0.190 (p=.011) | +0.259 (p=.042) / +0.382 (p=.014) |
| A3 | `wolf_power_role_targeting_rate` | −0.017 (p=.822) | −0.025 (p=.805) | −0.018 | −0.025 | −0.030 | −0.005 / −0.033 |

*Direction:* A1 and A2 are positive as pre-registered — killing power roles helps the wolf, once the games
where it can't matter are removed. *Magnitude:* the effect is muted-to-moderate (conditioned |r|≈0.23–0.31);
the **rate** form (A2) is the cleaner instrument (per-opportunity de-lucks exposure) and is the one that
holds sign AND significance on BOTH split-halves (+0.26 p=.042 / +0.38 p=.014) and survives partialling out
BOTH `sk_lynched` and `game_length` (+0.190 p=.011). A1 (raw count) is muted-real but split-half-marginal
(confirm +0.18 p=.253 at n=41). A3 is flat-null everywhere — targeting a power role ≠ killing it (healer
saves, misses), so intent without conversion carries no signal.

- **A2 `wolf_power_kill_rate` → MUTED-REAL (rescued).** Signal appears only once conditioned on the
  environmental dominator; direction +, conditioned magnitude ≈+0.31, split-half-stable, partial-robust.
  This is the **first wolf-night proxy to clear the bar**, and it directly reframes
  `deceiver_metric_refinement.md`'s "night-offense genuinely doesn't convert (rate −0.10)" as an artifact of
  **not conditioning on the SK axis** — pooled it's null, but within the games a wolf can win it converts.
  Epoch caveat: rests on 103 in-stratum games / 39 wolf wins → moderate power; re-validate at a larger
  wolf-win base before hard-coding into the basket.
- **A1 `power_roles_killed_by_wolves` (count) → MUTED-REAL, split-half UNDECIDABLE-AT-N** (confirm-half ns).
  Same signal, coarser instrument; the rate (A2) supersedes it.
- **A3 `wolf_power_role_targeting_rate` → STILL-NULL.**

Investigator find-rate cluster (vs villagers-win) — length-normalization diagnosis, NOT an un-quarantine bid:

| id | metric | raw | partial\|game_length | disc / conf half |
|---|---|---|---|---|
| A4 | `investigator_found_wolf_day` (day #) | +0.150 (p=.107, n=117) | +0.114 (p=.225) | +0.144 / +0.146 |
| A4n | `investigator_found_wolf_day_frac` | +0.077 (p=.407) | +0.151 (p=.106) | +0.065 / +0.088 |
| A5 | `investigator_threat_find_rate` | −0.000 (p=.998, n=169) | +0.033 (p=.675) | +0.024 / −0.091 |
| A6 | `investigator_wolf_find_rate` | −0.031 (p=.689) | −0.015 (p=.851) | −0.025 / −0.074 |

*Direction/diagnosis:* the v5 finding was `found_wolf_day` **significantly wrong-sign** (+0.38, p=.039, n=30
— expected − because an earlier find should help the town). At N=180 that inverts the interpretation: the
metric is now **+0.15 and not significant**, and neither length-normalizing (A4n) nor partialling out
`game_length` pushes it toward the expected negative — it stays weakly positive. So the earlier wrong-sign
was **small-N noise plus mild length coupling, not a robust backwards relationship**; the sign confusion
dissolves at N rather than flipping to correct. A5/A6 are flat-null.

- **A4–A6 → STILL-NULL; quarantine STANDS but for a softer reason.** The cluster is not *significantly
  wrong-sign* at N=180, it is *null* — finding wolves (rate/earliness) still does not predict town wins;
  only the already-validated `investigator_find_to_lynch_rate` (the conversion) does. Recommend downgrading
  the `dnu_` rationale from "significantly wrong-sign (length-confounded)" to "null; the earliness sign is
  N-fragile" — the DO_NOT_USE tier itself is unchanged.

### ③.B Accusation-graph proxies (`accusation_metrics.py`, 2026-07-02, N=180 v6ab)

Parsed 2,290 accusation events (`addressed_targets.stance=='accusation'`, ordered by `seq`) into a
per-player graph. Primary town family vs villagers-win, split on `game_id` parity:

| id | metric | full N=180 | discover half | confirm half |
|---|---|---|---|---|
| B1 | `town_accusation_precision` | **+0.340 (p<.001, n=175)** | +0.301 (p=.001) | +0.388 (p=.002) |
| B2 | `town_first_accuser_credit_rate` | +0.205 (p=.007) | +0.158 (p=.096) | +0.270 (p=.032) |
| B3 | `town_accusation_to_vote_conversion` | +0.173 (p=.022) | +0.074 (p=.438) | +0.314 (p=.012) |

*Direction:* all three positive as pre-registered — a town that aims its accusations at real threats,
early, and follows through with a vote wins more. *Magnitude:* B1 is the strong one (+0.34, both halves
p≤.002); B2 holds sign on both halves but is significant only on the confirm half; B3 holds sign but is
~null on the discover half. Bonferroni across the 3-test family (α=.0167): **B1 passes, B2 passes, B3
fails.**

- **B1 `town_accusation_precision` → DISCOVERED (the first town-discussion proxy).** It fills the named
  hole (no town-discussion metric existed). **Coupling catch:** it correlates with the already-validated
  `town_vote_accuracy` at Pearson r=+0.558 — related but NOT redundant (~31% shared variance). Honest
  framing: it partly re-expresses the same "town identifies threats" construct as vote accuracy, so it is
  **not independent evidence** from the vote endpoint; its value is that it measures that construct
  **upstream, on the discussion surface** (a distinct speech act, earlier in the day, including players who
  never get to vote). Accept as a **diagnostic** discussion proxy, not as a second confirmation of a good
  town.
- **B2 → WEAK-REAL (sign-stable, sub-threshold).** B3 → **STILL-NULL/UNDECIDABLE** (discover-half null;
  the follow-through construct is largely already inside `town_vote_accuracy`).

Exploratory / coverage-limited (direction only, no accept claim):

| id | metric | full | disc / conf | coverage |
|---|---|---|---|---|
| B4 | `investigator_postfind_accusation_precision` | +0.190 (p=.047) | +0.192 / +0.187 | 109/180 |
| B5 | `vigilante_postfind_accusation_precision` | +0.326 (p=.219) | −0.064 / −0.250 | 16/180 |
| B6 | `wolf_accusation_on_town_rate` | −0.330 (p<.001) | −0.307 (p=.003) / −0.374 (p=.007) | 141/180 |

- **B4** is a consistent-sign suggestion (both halves +0.19) that the investigator's accusations sharpen
  after a private find — under-powered per half, promising.
- **B5** is too thin to read (n=16) → **UNDECIDABLE-AT-N.**
- **B6 → PRE-REGISTERED SIGN FALSIFIED (the finding).** Pre-registered **+** (framing offense should help
  wolves); observed **−0.330, p<.001, both halves significantly negative.** The surprise IS the result:
  wolves that spend their accusations on *town* lose more, and wolves that instead accuse real threats
  (the SK / the co-wolf) win more. Mechanism = **blending/credibility**, the mirror of the validated
  `wolf_unconditioned_blending_rate` (+0.27): accusing an actual threat reads as helpful-townie cover;
  attacking town is visible aggression that exposes. This is NOT a rescue (sign flipped) — it is a new
  discovery that must be **re-pre-registered with the corrected sign** before it can be validated as a
  proxy. It also corroborates the deceiver-doc `wolf_led_mislynch` null: wolf day-*offense* against town
  doesn't pay; wolf day-*camouflage* does.

**Label-noise spot-check** (`accusation_label_sample.json`, 20 random parsed accusations): the parses are
mostly clean and genuinely accusatory. Residual noise observed: a defensive counter-accusation
("that's a pretty heavy accusation without any proof, why are you pinning this on me?") is labeled
`stance=accusation` toward the person who accused *it* — a defend-by-counter that inflates accusation
counts slightly. Rate looks low in the sample (~1/20) but is uncharacterized; carried to §4.

### ③.C Claim-timing conversion joins (`claim_conversion.py`, 2026-07-02, N=180 v6ab)

**C0 BLOCKED (coverage catch, confirmed in code).** The persisted `DaySummary.structured.role_claims`
field that the claim-conditioned joins require is an **A4 (2026-06-20) addition and is present in 0/180
v6ab games (and 0/50 v5)** — both validation epochs predate it. The claim-with-find → convergence and
claim → correct-elimination joins are therefore **unbuildable on any available validation set**; reported
as blocked, no direction, no validation claim. (Deterministic recovery of claims from `addressed_targets`
is impossible too — the stance vocabulary is {accusation, defense, agreement, neutral}, with no claim act.)

What survives without the claim layer is the deterministic timing refinement:

| metric | full | discover half | confirm half | coverage |
|---|---|---|---|---|
| `investigator_find_next_round_convergence` | **+0.306 (p=.001, n=117)** | +0.339 (p=.004) | +0.308 (p=.037) | 117/180 |

*Direction:* positive as pre-registered. *Magnitude:* +0.31, holds sign AND significance on both halves.

- **C1 `investigator_find_next_round_convergence` → CONFIRMED.** After the investigator finds a wolf on
  night d, the share of town votes that land on that wolf the very next round predicts town wins — a
  tighter, timing-sensitive cousin of the already-validated `investigator_find_to_lynch_rate` (+0.40).
  Same construct family (find→conversion), so it is a **refinement**, not an independent proxy; its extra
  content over find→lynch is the *speed* of convergence. Accept as diagnostic within the transmission
  cluster.

### ③ Verdict summary

| id | candidate | verdict | r (key view) | split-half |
|---|---|---|---|---|
| A2 | `wolf_power_kill_rate` | **MUTED-REAL (rescued)** — first wolf-night proxy to clear the bar | +0.31 (\| sk_lynched=1) | holds (+0.26 / +0.38) |
| A1 | `power_roles_killed_by_wolves` | MUTED-REAL, split-half undecidable | +0.23 (\| sk_lynched=1) | marginal |
| A3 | `wolf_power_role_targeting_rate` | STILL-NULL | −0.02 | — |
| A4–A6 | investigator find-rate cluster | STILL-NULL (quarantine stands; softer rationale) | ~+0.15 / ~0 | — |
| B1 | `town_accusation_precision` | **DISCOVERED (diagnostic)** — first town-discussion proxy; couples w/ vote_accuracy r=.56 | +0.34 | holds (+0.30 / +0.39) |
| B2 | `town_first_accuser_credit_rate` | WEAK-REAL (sub-Bonferroni) | +0.21 | sign holds |
| B3 | `town_accusation_to_vote_conversion` | STILL-NULL/UNDECIDABLE | +0.17 | discover null |
| B4 | `investigator_postfind_accusation_precision` | suggestive, coverage-limited | +0.19 | consistent, ns |
| B5 | `vigilante_postfind_accusation_precision` | UNDECIDABLE-AT-N (n=16) | — | — |
| B6 | `wolf_accusation_on_town_rate` | **SIGN FALSIFIED** (pre-reg + → obs −0.33); blending discovery, re-register | −0.33 | holds (−0.31 / −0.37) |
| C0 | claim-conditioned joins | BLOCKED (0/180 role_claims) | — | — |
| C1 | `investigator_find_next_round_convergence` | **CONFIRMED (diagnostic, transmission cluster)** | +0.31 | holds (+0.34 / +0.31) |

Artifacts: `data/proxy_rescue.json`, `data/accusation_metrics.json`, `data/accusation_label_sample.json`,
`data/claim_conversion.json`. Reproduce: `poetry run python evaluation/src/experiments/{proxy_rescue,accusation_metrics,claim_conversion}.py`.

### ③.D Adoption executed (2026-07-02, follow-up green-lit by user)

The three survivors (A2, B1, C1) were adopted into `Agents/compute_metrics.py` as a **`DIAGNOSTIC_METRICS`
tier** — beside, not inside, `VALIDATED_BASKET_METRICS` — pushing with tier `"diagnostic"` and carrying
their caveats as attribute docstrings (A2's sk_lynched conditioning, B1's r=+0.558 vote-accuracy coupling,
C1's refinement status). Denominators (`power_role_alive_nights`, accusation counts) are now surfaced on
the persisted record so the rates are reproducible without re-parsing. Production `Agents/` mirrors the
runners' definitions with provenance comments rather than importing from `evaluation/` (the dependency runs
eval→Agents, one-way; the runners stay the validation source of record). Basket promotion remains pending a
larger wolf-win N, per the verdict table. 9 new tests; suite 480 green.

## §4 · Limitations known at design time

- Everything validates against the *current* epoch's behavior distribution; a null on a behavior
  agents rarely exhibit (steering) bounds measurability, not importance (§1). Sibling-workstream
  findings may change what exists to measure.
- B–D depend on `addressed_targets` label quality (self-labeled speech acts; the scheduler's known
  mislabel residual) — the labels were tuned for scheduling, not measurement, and their error rate
  as *measurement* input is uncharacterized.
- E inherits the tagger's uncalibrated status until a sampler spot-check runs.
- **NEW (③.A): the flat point-biserial is structurally miscalibrated for wolf proxies.** Wolves cannot win
  when `sk_lynched=0` (SK wins by default), so 77/180 games carry zero wolf-skill information yet are
  pooled into the correlation, diluting real signal to null. Any wolf proxy can only be honestly validated
  *within* `sk_lynched=1` (n=103, 39 wins) → a real power ceiling. Wolf-proxy nulls in the earlier
  refinement docs computed WITHOUT this conditioning should be re-read as "diluted," not "absent."
- **NEW (③.C): the `role_claims` join has a coverage cliff.** The claim-conditioned joins depend on a
  persisted `DaySummary.structured.role_claims` field that postdates (A4, 2026-06-20) both validation
  epochs (0/180 v6ab, 0/50 v5), and claims are not deterministically recoverable from `addressed_targets`
  (no claim stance). The claim program is unbuildable until a post-A4 batch is itself win-validated — a
  chicken-and-egg the audit cannot resolve on existing records.
- **NEW (③.B): discussion proxies partly re-measure the vote endpoint.** `town_accusation_precision`
  couples with `town_vote_accuracy` at r=+0.558 — the discussion-surface and ballot-surface views of "town
  IDs threats" are one construct family, so a discussion proxy is a diagnostic, not independent evidence of
  a good town. The B6 sign-flip shows the converse discipline: a plausible-sounding pre-registered sign can
  be simply wrong, and only the pre-registration makes that legible as a finding rather than a silent flip.
- **NEW (③.B): `addressed_targets` label noise as *measurement* input is still uncharacterized** (the §4
  bullet above, now with data): the 20-row spot-check shows mostly-clean parses but at least one
  defend-by-counter mislabeled as an accusation; a proper error rate needs a labeled sample, not a
  20-row eyeball.

*Opened 2026-07-02 at repo `4b1449e` (uncommitted working tree). ③.0 pre-registration + ③.A/B/C builds
run 2026-07-02 (all $0, deterministic, ZERO LLM; N=180 v6ab). Headlines: A2 `wolf_power_kill_rate`
rescued (first wolf-night proxy), B1 `town_accusation_precision` discovered (first town-discussion proxy),
C1 confirmed; B6 pre-registered sign falsified (a blending discovery); C0 blocked on data.*

---

## ④ Follow-up rescue — the two questions ③ left open (2026-07-07)

Two pre-registered, $0, deterministic re-tests on the same N=180 v6ab set with the same
`game_id`-parity split (runner:
`evaluation/src/instrument_validation/proxies/proxy_followup_rescue.py`; output
`data/proxy_followup_rescue.json`).

| id | question | pre-reg sign | full | disc / conf | verdict |
|---|---|---|---|---|---|
| F1 | does `town_accusation_precision` carry win signal *beyond* `town_vote_accuracy`? partial r(precision, town_won \| vote_accuracy) | + | **+0.024 (p=.756, n=175)** | −0.085 / +0.173 | **NO INCREMENTAL SIGNAL** — diagnostic placement confirmed on direct evidence |
| F2 | does `vigilante_correct_shot_rate` (v5 promise +0.30 n=36 / +0.43 n=21) firm up at this epoch's N? point-biserial vs town win, shooter games only | + | +0.178 (p=.201, n=53) | +0.141 / +0.075 | **STILL-UNVALIDATED** — sign holds, promise diluted |

- **F1 closes the question ③.B's coupling catch raised.** The raw +0.340 reproduces exactly, but
  partialling on the vote endpoint removes all of it: the ~69% of precision variance NOT shared with
  `town_vote_accuracy` carries no detectable win information. The construct-seat question is answered —
  the proxy stays a diagnostic (its value is localization: the same construct read upstream, on the
  discussion surface, including players who never get to vote), not a second witness. The *mediation*
  reading of this null — the vote as town's causal actuator, with the tagger's town/deceiver asymmetry
  as independent confirmation — is recorded in the topic log
  ([`../experiment_log.md`](../experiment_log.md), 2026-07-07 section) and [`../report.md`](../report.md) §3.
- **F2 note — an epoch behavior shift, flagged not investigated:** the vigilante shoots in only 53/180
  v6ab games (29%) vs 36/50 (72%) in the v5 batch, so trebling the game count barely grew the defined
  subset. The selection caveat stands (conditioning on "the vigilante shot" is behavioral selection).
  The vigilante channel remains without a validated positive-skill proxy.

*Run 2026-07-07. Both follow-ups returned null against their pre-registered signs — recorded in place,
per the falsified-in-place discipline, rather than dropped.*
