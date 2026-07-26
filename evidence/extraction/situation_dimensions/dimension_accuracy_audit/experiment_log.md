# v6 Dimension-Accuracy Audit — journey log

> **What this is.** The chronological record of Phase 1 of the 2026-07 eval-hardening pass: a $0,
> fully-deterministic audit of whether the v6 query-side situation dimensions are actually filled
> correctly, where "correct" is computable from the frozen board without any LLM. It exists to
> decide whether the production retrieval-gating null is a real *content* verdict or an
> *uninformative* one riding on inaccurate fills.
>
> **Companion docs.** The finding that motivates it:
> [`../../../evaluation/hardening_pass/experiment_log.md`](../../../evaluation/hardening_pass/experiment_log.md)
> §2.1 (do not duplicate — read it there). The reliability ledger this feeds:
> [`../../../evaluation/source_map.md`](../../../evaluation/source_map.md).
>
> **Provenance.** Runner `evaluation/src/experiments/dimension_audit.py`; review commit `4b1449e`
> on `feature-dimension-schema`, 2026-07-02. Inputs + git SHA + case counts are stamped into every
> JSON artifact under `data/`.

## §1 · Motivation — the finding under test

The hardening review's biggest new finding (§2.1 of the pass log): **every v6 situation dimension is
LLM-filled, and no filled value has ever been checked against ground truth** — even where truth is
deterministically computable from the board. This is load-bearing because production retrieval
*gating* (`Agents/memory/retrieval/dimension_gating.py`) keys on `players_alive`(bucketed) /
`is_swing` / `exposure_class` / `info_landscape_class`, and both the gating and criticality screens
returned ~0/negative. **If the fills are inaccurate, those screens tested noise and their nulls are
uninformative, not negative** — a materially different conclusion than the one currently recorded.
A $0 deterministic audit of the query-side fills distinguishes those two worlds; that audit is this
phase. (One paragraph by design; the full finding lives in the pass log.)

## §2 · Audit design

**Data.** Query-side `situation_dimensions` are persisted **only** in the loop-era eval-case
sidecars (`batch_results/{town_only_run1,town_only_run2,v2_full,legacy}/eval_cases/**`, span-wrapped
at `output.eval_case.situation_dimensions`). The batch records that carry the true role map and the
night/day resolutions live in `evidence/v7_final/<run>/gen*_{on,off}.jsonl`; each game is joined by
`trace_id`. Only cases with a non-empty `situation_dimensions` participate; each of a case's 1–2
situation objects is scored as its own row against the case's single board truth.

**Truth, from the case's OWN frozen state (never the outcome):**
- `players_alive` = `len(private_context.surviving_players)` — the roster the agent was shown.
- `distance_to_parity`, `is_swing` via the shared `decision_scoring.query_criticality` (lifted this
  pass out of `criticality_screen.py` into `evaluation/src/loop/decision_scoring.py` so the screen
  and the audit compute criticality truth identically; the screen re-imports it, behavior
  unchanged). Wolf-faction parity, town-lensed, omniscient.
- `bullets_left` (vigilante) = loadout − count of nights with `day < case.day` carrying a non-null
  `vigilante_target`. DAY precedes NIGHT within a day number (parent graph
  `DAY_PHASE → DAY_RESOLUTION → night`), so this counts exactly the shots already fired. `game_config`
  is not persisted in the records, so the loadout defaults to `GameConfig.vigilante_bullets` (2), the
  same assumption `compute_metrics.py` makes.
- `ally_revealed` (wolf) — **two variants, both reported**: PRIMARY = a wolf partner absent from
  `private_context.surviving_wolves` (dead/eliminated; a wolf tracks partner liveness directly);
  SECONDARY = a wolf partner lynched with its role revealed on a prior day (`day_resolutions`).

**The mandatory epistemic split.** A mismatch means different things per dimension, so the report
never pools across the split:
- **Agent-knowable → pure fill error.** `players_alive`, `bullets_left`, `ally_revealed` are all in
  the agent's own information set. Any mismatch is the LLM mis-filling a value it was handed.
- **vs-omniscient → conflated.** `distance_to_parity` / `is_swing` are scored against an omniscient
  wolf-parity truth. For **town roles** (and the serial killer) a mismatch conflates fill error with
  the agent's *epistemic limit* — a villager cannot know the wolf count — so it is reported as
  "vs-omniscient disagreement", NOT as fill accuracy. For **wolf roles** it is ~true fill accuracy
  (a wolf knows the wolf count), with the caveat that the parity metric itself ignores the serial
  killer, which wolves also cannot see.

**Outputs.** Per-dimension exact accuracy, MAE + signed bias (numerics), confusion tables
(booleans), each split by role × phase × day × run; PLUS the two gating-granularity numbers the
verdict turns on — `_alive_bucket` accuracy (reusing the gate's own bucket fn) and `is_swing`
agreement (wolf-side true vs town-side vs-omniscient). The semantic enums
(`exposure_class`/`info_landscape_class`/`consensus_direction`/…) have **no deterministic ground
truth**; the audit reports only their value *distributions* and defers their accuracy to the Phase-3
human + pro-LLM spot-check.

## §3 · PRE-REGISTERED decision rule (written before running on real data)

Verbatim from the approved plan (Phase 1). This block is frozen once results exist below.

- **CONFIRM** the negative gating verdict (the null is a genuine *content* verdict) **iff**
  `alive-bucket acc ≥ 0.90` **AND** wolf-side `is_swing acc ≥ 0.8` **AND** the enum kappas ≥ 0.6.
  The enum-kappa clause comes from the **Phase-3** human+pro-LLM spot-check and is **PENDING** — so
  this deterministic arm can at most return a *provisional* CONFIRM on its two computable conditions,
  with the kappa clause explicitly outstanding.
- **RE-OPEN** (the null was uninformative) **if any gated dim < 0.80 bucket-accuracy** (or, later,
  an enum kappa < 0.4). Next step then = substitute the deterministic `players_alive` / offline
  `is_swing` into `dimension_gating_screen.py` and re-screen (~$10–15) **before** any prompt surgery.
- **MIDDLE BAND** (neither fired) → the verdict stands but carries a **quantified attenuation
  caveat**: a dimension filled with error rate ē attenuates any true retrieval tilt by roughly
  `1 − 2ē`, so a screen that measured ~0 under noisy fills would under-state a true effect by that
  factor (reported, not used to overturn the null).

Structural corollary recorded regardless of branch: `players_alive` should never be LLM-filled at
query time — `len(surviving_players)` is free and exact; `is_swing` can only be made exact in an
offline screen (the live agent genuinely cannot know it). Scope honesty: the criticality screen's
*query* side was already deterministic, so this audit speaks to **gating** and to query-fill quality
generally; the *stored* (extraction-time) side is not offline-truth-computable and is only **bounded**
here by internal-consistency checks (`|distance_to_parity| ≤ players_alive`, `players_alive ∈ [3,9]`).

---

## §4 · Results

Run at `4b1449e`, artifact `data/dimension_audit_20260702_105203.json`. 20,284 situation-rows from
6,275 cases-with-dims across three runs (legacy carries none — see coverage). All numbers below are
copied from that artifact; the pre-registered rule in §3 is unchanged.

### §4.0 · A catch, fixed in place before scoring

The first run scored every wolf case's `players_alive`/criticality against `len(surviving_players)`,
which dragged wolf `players_alive` to 0.71 (bias +2) and wolf alive-bucket to 0.74. Inspection showed
the cause was **not** a fill error: **wolf `night_action` cases do not persist
`private_context.surviving_players`** (176 cases in v2_full, empty roster → truth read as 0). Scoring
a fill against a bogus 0 is a truth-computation artifact, not a finding. The runner now **skips the
three criticality dims when the roster is empty** (counting them as `no_roster`) rather than corrupt
the wolf numbers; `bullets_left`/`ally_revealed` are unaffected (they don't need the roster). The
corrected wolf `players_alive` is 0.97 and wolf alive-bucket 0.995. This is logged as the discipline
requires — the raw wrong number is not laundered away, it is explained.

### §4.1 · Coverage per run (cases-with-dims / total)

| Run | cases w/ dims / total | coverage | games | no-roster (criticality uncomputable) |
|---|---|---|---|---|
| town_only_run1 | 1013 / 3915 | 25.9% | 30 | 0 |
| town_only_run2 | 2997 / 12122 | 24.7% | 100 | 0 |
| v2_full | 2257 / 5354 | 42.2% | 24 | 176 (wolf night) |
| legacy | 0 / 564 | 0.0% | 5 | — |

`legacy` is **honestly zero**: those five v6 smoke runs predate the `situation_dimensions` capture —
the field is absent from the case entirely (not empty), so they contribute nothing and are excluded.
Query-dims only ever fill for the retrieving (memory-ON) arm and only for roles that retrieved, so
the ~25% coverage on the town-only runs (ON town roles only) and 42% on v2_full (ON, all factions)
is the expected structural ceiling, not a defect. The audit is **well-powered** for every gated
deterministic dim: alive-bucket n=6099, wolf-side `is_swing` n=439, `bullets_left` n=1109,
`ally_revealed` n=439.

### §4.2 · Per-dimension accuracy, with the epistemic split

| Dimension | epistemic | n | exact acc | MAE | signed bias |
|---|---|---|---|---|---|
| `players_alive` | agent-knowable | 6099 | **0.970** | 0.031 | +0.01 |
| `alive_bucket` (gate key) | agent-knowable | 6099 | **0.990** | — | — |
| `ally_revealed` (partner-absent) | agent-knowable (wolf) | 439 | **0.975** | — | — |
| `ally_revealed` (lynched-w/-reveal variant) | agent-knowable (wolf) | 439 | 0.758 | — | — |
| `bullets_left` | agent-knowable (vig) | 1109 | **0.164** | 0.836 | −0.68 |
| `is_swing` — wolf-side (≈true) | ~true fill (SK caveat) | 439 | **0.606** | — | — |
| `is_swing` — town-side | vs-omniscient | 5282 | 0.469 | — | — |
| `distance_to_parity` — wolf-side (≈true) | ~true fill (SK caveat) | 439 | 0.091 | 1.68 | −1.62 |
| `distance_to_parity` — town-side | vs-omniscient | 5660 | 0.052 | 2.09 | −2.02 |

**Agent-knowable dims (pure fill error):**
- `players_alive` — 0.970 exact, and **alive-bucket 0.990** (villager 0.995, wolf 0.995 after the
  §4.0 fix). The gate's *primary* key is filled well. But this is a value the agent was literally
  handed: 3% of fills are still wrong for no epistemic reason. **The structural corollary is
  vindicated** — `players_alive` should be `len(surviving_players)` at query time, free and exact,
  never an LLM fill.
- `bullets_left` — **0.164 exact**, MAE 0.84, and the fill systematically *under-counts* remaining
  bullets (bias −0.68). By day it is damning: day-2 accuracy is **0.0** (every vigilante with 2
  bullets unspent reports 1), climbing only to ~0.35 by day 4. This is a fully agent-knowable count
  and it is mostly wrong — a clean, unambiguous fill-quality failure.
- `ally_revealed` (partner-absent) — 0.975. Wolves track partner liveness reliably. The
  lynched-with-reveal *variant* is lower (0.758) only because it is a stricter truth (a partner who
  died to a night-kill is "gone" but not "lynched") — the partner-absent variant is the
  faithful one; the gap between the two is a definitional artifact, not a fill error.

**vs-omniscient / ~true dims (the conflated ones):**
- `is_swing` is the finding. Wolf-side (≈true accuracy, the cleanest read) is **0.606** — but the
  wolf `is_swing_true` base rate is only 0.173, so a constant "always False" would score **0.827**.
  **The fill is materially *worse than a constant*** (it over-fires "swing": 173 false-positives vs
  76 true-positives). Town-side is 0.469 (conflated with the villager's genuine inability to know the
  wolf count, so not a fill verdict). For **gating** the cause doesn't matter: the gate keyed on a
  query-side value that is unreliable-to-anti-informative on both the clean (wolf) and conflated
  (town) reads.
- `distance_to_parity` — near-zero exact everywhere (0.05 town, 0.09 wolf), MAE ~2, and even the wolf
  ~true read is off by ~1.6 (under-counting). It is excluded from production gating already; the
  audit confirms that exclusion was correct.

### §4.3 · Decision-rule branch: **RE-OPEN**

Gated deterministic dims: **alive-bucket = 0.990** (≥0.90 ✓) but **wolf-side `is_swing` = 0.606**,
which is **< 0.80** → the pre-registered RE-OPEN condition ("any gated dim < 0.80 bucket-acc") fires.
The enum-kappa clause (`exposure_class`/`info_landscape_class`) is **PENDING Phase 3** and cannot
lift this to CONFIRM regardless; but it doesn't need to — the deterministic arm alone re-opens.

**What this means (bounded honestly):** the gating null is at least partly **uninformative, not a
clean content verdict.** The gate keys on `players_alive`(bucket) + `is_swing` + two enums.
`players_alive`-bucket is trustworthy, so half the gate's key was sound; but `is_swing` is
unreliable-to-anti-informative, and the two enums are unvalidated — so a null gating result was
measured through a partly-noisy filter. Mean gated error rate ē = 0.202 ⇒ **tilt attenuation
1 − 2ē ≈ 0.60**: a true retrieval tilt would be attenuated to ~60% of its strength by fills this
noisy, so a screen reading ~0 could be masking a real but smaller effect. Per the plan, the next step
this authorizes (not run here) is to substitute deterministic `players_alive` + offline `is_swing`
into `dimension_gating_screen.py` and re-screen (~$10–15) **before** any prompt surgery.

### §4.4 · Semantic enums — distributions only (accuracy is Phase 3)

`exposure_class`/`info_landscape_class`/`consensus_direction`/`divergence_sign`/`my_position` have no
deterministic ground truth, so the audit reports only their value counts (in the artifact). They are
heavily skewed — e.g. villager `exposure_class` is 2164 `safe` vs 134 `exposed` (94% one class) —
which is exactly why the Phase-3 spot-check must **force ~half predicted-`exposed`/`info_rich`** for
off-diagonal power; a naive random sample would be almost all majority-class and measure nothing.

## §5 · Limitations

- **This audits the QUERY side only.** The *stored* (extraction-time) fills are not offline
  truth-computable (no frozen board travels with a stored observation), so they are only **bounded**
  by internal consistency: on `memory_stores/v6_1` (n=932 obs with criticality), `|distance_to_parity|
  ≤ players_alive` holds 100% and `players_alive ∈ [3,9]` holds 100%. These are weak bounds — they
  would pass even under a systematic fill bias, as long as values stay in range — so they rule out
  gross corruption, not the query-side-style error this audit found. The stored side's real check is
  the Phase-3 sampled review of stored observations.
- **Scope of the re-open.** The criticality *screen*'s query side was already deterministic
  (`query_criticality`), so this audit does **not** re-open that screen — it re-opens **gating** (whose
  query-side dims are LLM-filled) and speaks to query-fill quality generally. Said plainly rather than
  overclaimed.
- **`is_swing` wolf-side carries an SK caveat.** "≈true accuracy" for wolves is an upper bound on the
  epistemic problem: the parity metric ignores the serial killer, which wolves also cannot see, so
  part of the 0.606 is genuine wolf epistemic limit, not pure fill error. This does not weaken the
  gating conclusion (an unreliable query value is unreliable to gate on whatever the cause), but it
  means 0.606 is not a pure fill-quality number.
- **Vigilante loadout assumed = 2.** `game_config` is not persisted in the batch records, so
  `bullets_left` truth uses the `GameConfig.vigilante_bullets` default (2), the same assumption
  `compute_metrics.py` makes. If any run overrode it the `bullets_left` truth would shift — but the
  day-2-always-reports-1 pattern is loadout-independent evidence of under-counting.
- **Enum accuracy is entirely deferred** to Phase 3; nothing here validates the two enum gate keys,
  so even the RE-OPEN is conservative (it fires on the deterministic dims alone).
- **N is a decision count, not a game count** — 100 games in town_only_run2 but decisions are
  correlated within a game; the per-dim n's are decisions. Adequate for the fill-accuracy point
  (fills are per-decision), noted for anyone reading the n's as independent.

## §6 · The structural fix — deterministic query-side dims (done 2026-07-02)

The direct, $0 consequence of §4.3's RE-OPEN and the structural corollary in §3: the three
**agent-knowable** query-side dims are now **computed from game state, never trusted from the LLM's
structured output.** This closes the fill-quality half of the RE-OPEN at the source (the offline
gating re-screen — separate, ~$10–15, pending spend sign-off — remains the other half).

**What changed, where.** The override runs at query time in
`Agents/memory/enrichment/situation_agent.py` (`_override_deterministic_dims`, applied to each parsed
cell before dims/embeds are composed):
- `players_alive` ← a shape-robust living-player count (`_computed_players_alive`): wolf payloads sum
  the faction rosters (`surviving_wolves + surviving_villagers`); single-actor NIGHT payloads list
  every living player *except* the actor, so the actor is added back via a membership check; day
  payloads carry the full role-blind roster including self. (Fixes the 3%-wrong-for-no-reason fill.)
- `bullets_left` ← the vigilante's live remaining-shot counter `vigilante_bullets`. The night payload
  already carried it; the **day** payload (a `VillagerDayState`) did not, so it is now **threaded**
  minimally into the vigilante's day payload (`Agents/nodes/day/flow.py` `build_speaker_send` /
  `fan_out_day`; seeded through `Agents/graphs/parent.py::day_phase` and a new
  `DayGraphState.vigilante_bullets` field). This is the fix that matters most — the LLM fill was 0.164
  exact (day-2 accuracy 0.0).
- `ally_revealed` ← `len(surviving_wolves) < initial_wolf_count`, where `initial_wolf_count` is derived
  from the game's true role map at the day-payload builder (a scalar count only — no wolf identity
  rides the payload, so the leak boundary is untouched) and threaded into the wolf day cell. This is
  the audit's validated *partner-absent* truth (§4.2, 0.975). It was already accurate as an LLM fill,
  so the override mostly hardens it against drift rather than correcting a large error.

`distance_to_parity` / `is_swing` are deliberately **left LLM-filled**: they require the true role map
the live agent cannot see, so no partial wolf-side computation was attempted this pass (that is the
offline re-screen's job). The corrected numerics carry **no `_Embed` marker**, so overriding them
changes the gating dims (`situation_dimensions` → `dimension_gating.reweight`, which buckets
`players_alive`) **without** touching the composed embed string — retrieval matching is unchanged, only
the gating filter is de-noised. An override that actually corrects a value debug-logs the LLM-vs-computed
delta, so future runs surface residual LLM fill error for free.

**Residual-inconsistency caveat (accepted, flagged).** Only the numeric/bool dims are corrected — the
LLM's *prose* fields (`criticality_stakes` etc.), which it derived from its own possibly-wrong numbers,
are **not** re-derived (that needs a second LLM call, out of scope). So a corrected
`players_alive`/`bullets_left` may now disagree with the prose in the same object. Noted in a code
comment at the override site and here.

**Stored records remain uncorrected.** This fix is query-time only: **only future queries benefit**.
The already-stored observations keep their extraction-time fills (the extraction path is untouched —
those fills have no pinned board moment and are out of scope). The pending gating re-screen would apply
deterministic substitution to the *frozen* cases separately; it is not this change.

Tests: `tests/test_situation_dim_override.py` (10 cases over `_override_deterministic_dims` /
`_computed_players_alive` with synthetic payloads — day roster, self-excluded night, wolf rosters,
vigilante counter day+night, partner-gone/alive, and each "ingredient missing → keep LLM fill"
fallback). Suite 421 → 431 passed.

## Sources

- Runner: `evaluation/src/experiments/dimension_audit.py`; truth fn `query_criticality` lifted to
  `evaluation/src/loop/decision_scoring.py`; gate bucket reused from
  `Agents/memory/retrieval/dimension_gating.py::_alive_bucket`.
- Data: loop-era sidecars under `batch_results/{town_only_run1,town_only_run2,v2_full,legacy}`;
  batch records under `evidence/v7_final/{town_only_run1,town_only_run2,v2_full}` +
  `batch_results/legacy/*.jsonl`.
- Motivating finding: `../../evaluation/hardening_pass/experiment_log.md` §2.1. Unit test:
  `tests/test_dimension_audit.py`.
- §6 fix (query-side deterministic override): `Agents/memory/enrichment/situation_agent.py`
  (`_override_deterministic_dims` / `_computed_players_alive`); threading in
  `Agents/nodes/day/flow.py` (`_initial_wolf_count` + vigilante/wolf day-payload keys),
  `Agents/graphs/parent.py::day_phase`, `Agents/state/day.py` (`DayGraphState.vigilante_bullets`).
  Corrected dims consumed by `Agents/memory/retrieval/dimension_gating.py::reweight`. Unit test:
  `tests/test_situation_dim_override.py`.
