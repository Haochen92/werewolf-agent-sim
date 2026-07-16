# Evaluation Metrics — per-role play-performance scoring

> **Supersession banner (2026-07-06).** This is a frozen dated record; read it as history, not as
> current state.
> - **The "DESIGN DISCUSSION, no code yet" header below is the June-6 snapshot.** The v2 metric set was
>   implemented the *same day* (commit `93b1137`; see the §Implementation status section) and
>   monotonicity-validated on 2026-06-11 (the tail section). "No code yet" was true only for the hours
>   before that commit.
> - **The current finalized shape lives in [report.md](report.md)** (new, the how-it-works doc);
>   apparatus trust — which proxies are validated and at what N — is in
>   [`../evaluation/metrics/report.md`](../evaluation/metrics/report.md); the folder map is
>   [README.md](README.md).
> - **Framings that have since died.** "Phase C" no longer exists as a plan; the plan of record for the
>   memory-effect A/B is now `evidence/execution_plan/compounding_measurement_plan.md`. The Phase-B
>   prompt freeze referenced below was *lifted 2026-06-20* (prompts are normal engineering now). And the
>   Batch A/B "70% → 97%" lineage claim cited below was later **demoted to a non-citable historical
>   ceiling** with a multiple-comparison caveat — see
>   [`../memory_system/effectiveness/report.md`](../memory_system/effectiveness/report.md).

**Status: DESIGN DISCUSSION (2026-06-06), no code yet.** Part of Phase A #3 (tracing consolidation;
see `evidence/tracing/`) — "design against the eval needs." The metrics ARE the eval need: they are
the key driver of how we measure the memory system's impact (Phase C win-rate A/B). This log tracks
the audit + the design discussion. Pre-Phase-B-labelling; a prompt freeze was in force during Phase-B
labelling — no main-pipeline prompt changes; lifted 2026-06-20 per the banner above.

## Goal / criteria

Beyond win rate, we want **per-role scores** that:
1. **Objective**, not vague/subjective.
2. Measure **decision quality given the circumstances** (process), not outcomes (which include luck).
3. Ideally **normalized by uncertainty** — judge a choice against the information available at decision
   time (info-starved spot → near-coinflip → low weight; info-rich spot → choosing against the
   evidence is a real, heavily-weighted error). Process-vs-outcome, à la decision theory/poker.

## Metric versioning (v0 → v1 → v2)

This work is **v2**, a refinement — not a from-scratch build. The history matters:

- **v0 — nothing logged.** Early games ran but emitted no structured metrics. Impact could only be
  eyeballed; there was no quantitative signal at all.
- **v1 — the CURRENT eval (the proxy + judge suite below).** Forming this was itself substantial
  progress: deciding *what* to count, building the per-game accumulators (`DayResolutionMetric` /
  `NightResolutionMetric`), the derived rates, and the LLM-judge rubrics. v1 took us from "measure
  nothing" to a working, repeatable proxy basket + memory-pipeline judges. The proxies it defined are
  the foundation we build on — the audit below is a critique *of a real artifact*, not of a blank slate.
- **v2 — this workstream: refine the DETERMINISTIC scores.** De-luck the v1 outcome proxies (condition
  on opportunity), make uncertainty-awareness explicit where feasible, and verify each proxy is
  monotonic in skill. v2 keeps v1's mechanical, fully-objective backbone and sharpens it; it does NOT
  discard v1 or chase a per-decision determinism the system can't honestly support (see discussion).

## Lineage — this extends the v1 memory-effectiveness study

`evidence/memory_system/effectiveness/report.md` is the prior, **v1-era** memory-effectiveness study
(2 batches × ~91 games). It already established the headline — **memory works but is
configuration-dependent** (Batch A villager win 70%→97% all-enabled; Batch B the "same" condition
74%→73%) — and it already specifies the **authoritative paired/seeded A/B statistical design**
(within-pair variance cancellation `Var(on−off)=Var(on)+Var(off)−2·Cov`, **McNemar** for win/loss,
paired-t/Wilcoxon for dense metrics, full seedability incl. the scheduler tie-break). We **defer to
that report** for the A/B statistics — this log does not re-derive them.

That study, however, is the **old game**: 8 players, 2 factions, forced voting, v3/v4 stores. Its
metrics (`correct_elimination_rate`, `healer_save_rate`, `investigator_accuracy`, `wolf_blending_rate`,
`mislynches`) are exactly the ones this v2 work finds **stale for the rebuilt 9-player / 3-faction /
optional-voting game**. So v2 is the proper extension: (a) make that basket **faction-correct** (wolf+SK),
(b) **de-luck** it (lift-over-random, town/friendly-fire save split, opportunity denominators not
`game_length`), (c) **add dense per-role proxies for the new roles** (SK survival gradient, vigilante
shot quality) — the old study has none, (d) add **proxy-vs-win validation** (drop non-monotonic proxies).
This basket feeds that report's "What's Next" validation batch — now **Phase C on v5**, post-rebuild.

(NB: this log's metric **v0/v1/v2** versioning is a different axis from the effectiveness report's memory-
*system* **Phase 0/1/2** (monolithic → RAG → namespace refinement) — don't conflate them.)

## How v1 came to be — provenance & rationale

No design log was ever written for v1; the rationale below is reconstructed from git history
(`1cd5ed7 "Add: runtime memory metrics for evaluation"`, `a299ee2 "Fix: measure wolf blending…"`,
`67e22c3 "Make metrics robust for 3 factions…"`; judge commits `eb23f72`, `50403f5`, `bf9490a`,
`c07dff7`…) and the code itself. Two design pillars:

### Pillar 1 — the LLM-as-judge pipeline (subjective by nature), aimed at "did memory help?"
The judge suite (`evaluation/judges/`) measures the thing win rate can't see directly: **was the
memory useful for *this decision*** — `retrieval_relevance` (were the pulled memories on-point),
`strategy_application` (did the agent actually use them), `action_quality`, `grounding`,
`summary_quality`. Aggregated across memory-on turns, this is the qualitative read of memory
effectiveness, complementing the win-rate A/B.

**Why it's subjective — concretely:** the judge is *itself an LLM* scoring free-text on a 1–5 rubric.
So a score depends on (a) the judge model + prompt phrasing + temperature, (b) the judge's own
interpretation with no ground-truth anchor, (c) the backend — the Google-AI and Vertex backends produce
different outputs even at temperature 0, a standing project finding, and (d) known blind spots — a prior
project finding is that the judge **misses information gain**, plus the
usual verbosity/leniency/position biases. It's reproducible only approximately. That subjectivity is
exactly why v1 *also* shipped the deterministic metrics, and why v2 leans on them.

### Pillar 2 — the deterministic metrics: "score whatever we can extract mechanically"
`compute_metrics.py` was built bottom-up from what the game emits with **zero LLM**: votes, revealed
roles, deaths (`Day/NightResolutionMetric`). **Normalization is already present** — every
`DerivedGameMetric` is a *rate*, normalized by **opportunity** (the denominator), not a raw count:
e.g. `investigator_accuracy = wolves_found / investigations`, `healer_save_rate = saves /
nights_alive`, `wolf_steering_rate = steered / mislynch_days`. So v1 already de-noises by opportunity;
what it does *not* do is normalize by **information/difficulty** (uncertainty). That — not "no
normalization" — is the precise gap v2 targets.

## Accurate limitations (re-checked against `Agents/prompts/roles.py` + the gameplay changes)

The game changed since v1's metrics were written: **voting is now optional** (abstain / plurality, no
forced lynch) and there is a **third faction** (night-immune serial killer + town vigilante). Checking
each metric against the *actual* current roles, some limitations are **real and concrete**, and one of
my earlier critiques was **exaggerated**:

**Real & concrete (gameplay-change-induced staleness — verified in code, not yet fixed):**
- **`mislynches` / `correct_elimination_rate` don't credit lynching the SK.** `mislynches` counts any
  `voted_player_role != "wolf"` ([compute_metrics.py:50](Agents/compute_metrics.py#L50)) and
  `correct_elimination_rate = wolf_eliminations / total` only counts `role == "wolf"`. But the SK
  **can only be removed by a day vote** (roles.py:56) — lynching it is the village's single most
  important day-objective against that faction, yet it scores as a *mislynch*. "Correct" should be
  `role in {wolf, serial_killer}` from the town's perspective.
- **`investigator_accuracy` ignores SK discovery and mismodels the role's objective.** It counts only
  `investigator_target_role == "wolf"` ([compute_metrics.py:74](Agents/compute_metrics.py#L74)), but
  the investigator's stated job (roles.py:21) *also* values **clearing a townie** (narrows the pool)
  and, post-3-faction, **finding the SK** — neither is credited, so a deliberate, skillful
  town-clear or SK-find reads as a "miss."
- **`_exit_method` mislabels SK/vigilante night kills as `"killed_by_wolves"`**
  ([compute_metrics.py:171-174](Agents/compute_metrics.py#L171)) — acknowledged in an in-code comment;
  per-killer attribution deferred to the dense per-role pass.

**Exaggerated in my first pass (correcting for accuracy):**
- **`healer_save_rate` is NOT "pure luck."** It's luck-laden but **monotonic in skill**: a healer that
  reads threats well (roles.py:8) protects likely targets and saves more over many games. It's a
  *valid* proxy — exactly the kind v2 keeps and verifies via proxy-vs-win, not one to discard.
  (Three factions make it noisier — two night killers now — but not invalid.)

**New gaps from optional voting (not bugs, but incompleteness):**
- A **strategic abstain** (good play under uncertainty) is invisible: it just shrinks
  `total_eliminations`, neither rewarded nor penalized. Vote-quality is now an incomplete picture, and
  the lynch-rate denominators are smaller → noisier at low N.

**Net:** the headline v1 weakness for our purposes is **not** the outcome-vs-decision-quality
philosophy — it's that the 3-faction + optional-voting changes left several metrics **semantically
stale** (SK-lynch and SK-discovery uncredited, killer attribution wrong). Those are concrete and
fixable in v2 and matter more than the luck critique.

## Audit of existing metrics (2026-06-06) — this is v1

Two **fully separate** families (condensed here; the per-metric verdicts are the tables below).

### Family 1 — deterministic game/role metrics (`Agents/compute_metrics.py`, `schemas/metrics.py`)
**100% mechanical (votes, revealed roles, deaths) — zero LLM, fully objective. Already normalized by
OPPORTUNITY (rates, not raw counts), but NOT by information/difficulty (uncertainty), and
outcome-based.** They measure *what happened* (luck included, but mostly monotonic in skill — see
"Accurate limitations" above for which are stale vs valid):
- `BaseGameMetrics`: winner, game_length, mislynches, wolf_eliminations, healer_save_count,
  healer/investigator_nights_alive + exit_method, investigator_wolves_found, power_roles_killed,
  wolf_power_role_target_nights, mislynch/wolf-elim day breakdowns (steered/blended/dissented).
- `DerivedGameMetrics` (rates): `correct_elimination_rate` (wolf lynches / lynches),
  `healer_save_rate` (saves / nights — luck-laden but monotonic-in-skill, a *valid* proxy),
  `investigator_accuracy` (wolves_found / investigations — stale: ignores town-clears and SK-finds),
  `wolf_steering/blending/dissent_rate`, `wolf_power_role_targeting_rate`. See "Accurate limitations"
  for which are stale (SK-related) vs valid-but-luck-laden.

### Family 2 — LLM judges (`evaluation/judges/`, `evaluation/core/schemas.py`)
**Decision-quality-oriented and partially uncertainty-aware, BUT subjective (LLM), scoped to the
MEMORY system (not holistic role play), per-action (not aggregated per-role/game).** Judges:
pipeline (summary_quality, retrieval_relevance, strategy_application, grounding), summary
(faithfulness, specificity, retrieval_usefulness, non_redundancy, role_perspective), retrieval
(relevance, unique_lessons, efficiency), application (action_quality, strategy_application, grounding,
adoption_accuracy), day_summary (completeness, accuracy, evidence_type_clarity, village_dynamics,
epistemic_correctness), extraction/per_role_extraction (specificity, epistemic_compliance, grounding,
coverage, diversity, perspective_compliance, strategy_depth, novelty), dedup/batch_dedup.
Uncertainty handling is ad-hoc (e.g. "if relevance ≤2 score neutral"). Frameworks:
`EPISTEMIC_STATUS_RULE` + `SITUATION_STANDARDS` (`Agents/prompts/standards.py`).

### Verdict against the criteria
**The target metric — per-role, decision-quality, uncertainty-normalized, objective — does NOT exist.**
Family 1 is objective but outcome/luck-based. Family 2 is decision-quality-ish but subjective +
memory-scoped + per-action. This is the gap, and it's the dense signal the roadmap always wanted for
the Phase C A/B (win rate alone is too noisy).

## Design discussion — why pure deterministic decision-quality is not feasible now

Attempted a deterministic-first "Vote Decision Quality" (vote vs known roles, uncertainty-weighted).
It collapsed under scrutiny:
- **Mechanical role-knowledge is nearly empty.** The only agents who *mechanically know* another live
  player's role: the **investigator** (own results), the **vigilante** (an immune target = confirmed
  SK, via `vigilante_results`), and **wolves** (allies). No villager ever mechanically knows a role.
  So a deterministic "voted a known wolf / known townie" check fires for ~1–2 agents on a few turns —
  a sanity anchor, not a metric.
- **No A/B-symmetric uncertainty signal.** The situation summary (with `information_landscape`) is
  **memory-arm-only** — it doesn't run in memory-off games (confirmed: memory-off game had 0
  situation_summary / 0 memory_retrieval spans, but 4 day-summaries). A normalizer that exists in
  only one arm biases the comparison. The `day_summary` runs in **both** arms but is **end-of-day,
  village-level, and static** — it can't see intra-day suspicion shifts and isn't per-agent.
- **No captured per-agent, per-player, evolving certainty.** That structured belief signal — which a
  true decision-quality + uncertainty metric needs — is simply not emitted.

### What the existing system DOES capture (both arms, categorical/deterministic-usable)
- The **vote** (per agent/day, validated player_id).
- **Mechanical private knowledge**: investigator_results, vigilante_results, wolf allies.
- **Dynamic behavioral-categorical signals**: `addressed_targets`, `day_summary` `Accusation{target,
  evidence_type}` / `RoleClaim`, full voting records.
- Free-text/dynamic but NOT deterministic: `updated_strategy`, messages, situations (memory-arm only).
- **Not captured**: structured per-agent per-player evolving role-belief/certainty.

### Output-path redesign (force agents to emit a per-player belief vector) — REJECTED
1. It's a **main-memory-pipeline prompt change** → invalidates Phase B labels (freeze rule).
2. It **confounds the A/B** — changing required output changes how agents play, contaminating the
   win-rate/skill signal we are measuring.
3. It's **subjective + circular** — a competent LLM's vote already aligns with its self-reported
   beliefs (belief-vs-vote consistency adds ~no independent signal), and belief-correctness still
   needs ground truth → back to outcome.

## DECISION — proxy-basket approach (statistically honest, freeze-safe)

Keep outcome **proxies**, **de-luck** where cheap, rely on **N (games × days)** to average luck, and
require only that each proxy is **monotonic in skill**. Win rate stays the headline; the proxy basket
is the variance-reducer.

1. **Curate a per-role proxy basket** from data we already emit (investigator targeting, healer
   protect-given-threat, vote-vs-strongest-public-accusation, wolf blend/steer, SK/vig survival+kills).
2. **De-luck each** by conditioning on *opportunity*, not raw outcome (e.g. healer rate only over
   nights a kill occurred and a defensible target existed; investigator accuracy normalized by
   live-wolf density).
3. **Verify monotonicity objectively** — correlate each proxy with its faction's **win** across games.
   Win is the independent ground-truth skill anchor (non-circular). Drop proxies that don't move with
   winning.
4. **Confirm both-arm symmetry + raw-data coverage** for each kept proxy.

Explicitly accept the basket is luck-laden-but-monotonic rather than feigning a per-decision
determinism the system can't honestly support. A richer decision-quality layer, if ever wanted, is a
**post-hoc eval-side judge done AFTER labelling** — never an output-path change.

## v2 metric set — enumeration (PROPOSED 2026-06-06, pending review → then lock → then implement)

**Cross-cutting rules** (apply to every row; stated once):
- **Both-arm:** all deterministic metrics are both-arm-symmetric ✅ (mechanical). The **LLM judges are
  memory-on-only → NOT A/B-comparison metrics**; demoted to *diagnostic* + Phase B labelling.
- **De-luck:** condition the denominator on *opportunity*, not existence.
- **Monotonicity:** correlate each kept proxy with its faction's **win**; drop those that don't move.

Verdict legend: KEEP / FIX / DROP / ADD. Type: D=deterministic, J=LLM-judge.

### Village / outcome
| Metric | Verdict | Type | Note / de-luck |
|---|---|---|---|
| `winner` (per-faction win) | KEEP | D | The headline + the monotonicity anchor for everything else. Variance handled by N + paired/seeded games. |
| `correct_elimination_rate` | **FIX** | D | STALE: only counts wolf lynches. Fix → numerator = lynches of role∈{wolf, **serial_killer**} (both are kill-worthy from town's view; SK can *only* die by day-vote). Denominator stays total eliminations (opportunity). |
| `mislynches` | **FIX** | D | STALE: counts role≠wolf, so SK/vigilante lynches read as mislynches. Fix → mislynch = a **town member** lynched (role∉{wolf, serial_killer}). Lynching the SK is NOT a mislynch. |
| `serial_killer_lynched` | **ADD** | D | Was the SK removed by day-vote (the only way). Key village success vs the 3rd faction. |
| `game_length`, `tie_count`, `no_vote_count`, `total_eliminations` | KEEP | D | Descriptive/context (decisiveness, esp. under optional voting). Not skill proxies on their own. |

### Healer
A "save" = `healer_target` was attacked (∈ {wolves_target, sk_target, vigilante_target}) and survived
(not in `deaths`). With 3 factions a save is **not unconditionally good** — classify by the **faction
of the saved player**. Denominator = `healer_action_nights` (every action-night has live attack
pressure, since wolves/SK always attack — so action-nights is already opportunity-normalized; ruling 3).
Replaces the wolf-only `healer_saved` flag ([nodes.py:561](Agents/nodes.py#L561)), which undercounts
SK/vigilante intercepts.
| Metric | Verdict | Type | Note |
|---|---|---|---|
| `healer_save_rate` (overall) | KEEP+**fix** | D | any save / action-nights. The current flag is wolf-only → undercount. |
| `healer_town_save_rate` | **ADD** | D | saved player is **town** / action-nights. The **good-play / read-overlap** signal (healer's threat model matched a real attack on an ally). |
| `healer_friendly_fire_save_rate` | **ADD** | D | saved player is a **wolf** / action-nights. The **error** signal (protected an enemy). Anti-correlate with village win. |
| `healer_wolf_block_rate` | KEEP (legacy meaning) | D | saved from a **wolf** attack specifically (= the old `healer_saved`). |
| `healer_exit_method` | **FIX** | D | Attribution fix (killed_by_wolves/sk/vigilante vs survived/voted_out). |
| protect-targeting decision-quality | (none) | — | A "predicted kill-target" reference is infeasible deterministically; the town/friendly-fire save split is the read-overlap proxy. |

### Investigator
| Metric | Verdict | Type | Note / de-luck |
|---|---|---|---|
| `investigator_threat_find_rate` | **FIX** (was `investigator_accuracy`) | D | STALE: counted only role=="wolf". Fix → **lift over random** = (wolf+SK finds / investigations) ÷ chance-rate, where chance = `threats_alive / investigable_alive` per night (from `wolves_before`/`town_before`/`sk_before`). De-lucks for pool composition (a late-game threat-rich pool makes hits "free"). Keep a separate `investigator_wolf_find_rate` (wolf discovery has different tactical value than SK). Town-clears are legit info-gain but fuzzy to credit deterministically — known undercount, flagged. |
| `investigator_found_wolf_day` | KEEP | D | Earliness proxy (earlier → better); intent = first-threat-find (incl. SK). |
| `investigator_investigations_total` | KEEP | D | Denominator. |
| `investigator_exit_method` | **FIX** | D | Attribution fix. |

### Wolves (already mostly decision/behavior proxies — relatively well-served)
| Metric | Verdict | Type | Note / de-luck |
|---|---|---|---|
| `wolf_power_role_targeting_rate` | KEEP+**fix denom** | D | Targeting *choice* (de-lucked from heal/immunity). STALE denominator: currently `/ wolf_kill_nights_total` (= night count ≈ `game_length`, an outcome). Fix → `/ nights a power role was alive & targetable` (opportunity), not game length. |
| `wolf_steering_rate` | KEEP+**fix denom** | D | Uses the stale mislynch_days def → apply the town-only mislynch fix to the denominator. |
| `wolf_blending_rate` / `wolf_dissent_rate` | KEEP | D | Social-discipline behavior proxies (vote with the lynched ally = cover). |
| `power_roles_killed_by_wolves`, `wolf_killed_{healer,investigator}_day` | KEEP | D | Wolf-specific outcome/context (correctly wolf-scoped). |

### Serial Killer (NEW faction — no metrics today; the A/B headline subject)
| Metric | Verdict | Type | Note / de-luck |
|---|---|---|---|
| `sk_survival_nights` / `sk_exit_method` | **ADD** | D | SK wins *by* surviving → survival length is the core dense proxy (near-definitional monotonicity = high-fidelity, low-variance signal for the A/B). |
| `sk_kills_landed` | **ADD** | D | Field-thinning; near-always lands so low-discrimination → context, not headline. Rate = /nights-alive. |
| `sk_lynched` | **ADD** | D | = `serial_killer_lynched` above (village's success / SK's failure). |
| kill-target quality ("thin the threat closing in") | (none) | — | Social → infeasible deterministic; possible judge later. |

### Vigilante (NEW — well-served deterministically; we know shot targets' true roles)
| Metric | Verdict | Type | Note / de-luck |
|---|---|---|---|
| `vigilante_correct_shot_rate` | **ADD** | D | Shots hitting a threat (role∈{wolf, serial_killer}) / shots taken. The key spend-quality proxy. (Shooting the immune SK = correct target — confirms it — even though no kill.) |
| `vigilante_friendly_fire` | **ADD** | D | Shots hitting town / shots taken. The error proxy (anti-correlate with village win). |
| `vigilante_shots_taken`, `bullets_unused_at_death`, `vigilante_exit_method` | **ADD** | D | Aggression/waste/exit context. |

### Cross-role — Votes (the chosen first scope)
| Metric | Verdict | Type | Note / de-luck |
|---|---|---|---|
| `town_vote_accuracy` | **ADD** | D | Per town-agent, fraction of real (non-abstain) votes hitting a threat (wolf/SK), aggregated per role. The realized "vote" proxy — **luck-laden but monotonic** (the deterministic uncertainty-weight we wanted isn't capturable; rely on N + monotonicity). |
| wolf vote quality | — | D | Already covered by `wolf_steering/blending_rate` (don't double-count). |

### LLM judges (all of `evaluation/judges/`)
| Verdict | Type | Note |
|---|---|---|
| KEEP as **DIAGNOSTIC**, **DROP from the A/B-comparison basket** | J | Memory-on-only (need situations/retrieval) → not both-arm. Use to diagnose *why* memory helped + as Phase B label targets. action_quality/grounding/day_summary judges *could* run both arms but are subjective → supplementary only, never the primary dense signal. |

## Why dense, de-lucked proxies — the variance argument (the backbone of the claim)

The headline (faction **win**) is ~1 bit per game → **high variance** → an underpowered test needs
hundreds of games to detect a moderate win-rate lift (the roadmap's underpowered-gate lesson). **Dense**
proxies produce many observations *per game* — per-night healer intercepts, per-vote accuracy,
per-investigation lift, the SK **survival-nights gradient** (gradation even among losses) — so their
per-game variance is far lower and the memory effect is detectable at feasible N. **That is the whole
reason to de-luck + densify rather than lean on win rate alone.**

### Statistical analysis plan
The **A/B design itself (paired/seeded, McNemar, paired-t/Wilcoxon, variance cancellation, seedability)
is specified in `evidence/memory_system/effectiveness/report.md` — defer to it, not re-derived here.**
What this metrics work adds on the **proxy side**:
- Report **effect sizes** + **bootstrap CIs** for each de-lucked proxy across the paired games (not just
  means); the per-pair *difference* is the unit (per the report's pairing).
- **Validate every proxy by its correlation with faction win** on the same corpus; **drop** non-movers /
  ambiguous ones before they enter the basket. (This validation step is the v2 addition — the old study
  reported proxies without it.)

### Claim framing — probabilistic triangulation, not deterministic proof
We cannot deterministically score individual decisions from current logs, and we don't claim to. The
defensible claim is conditional: *across repeated games, the memory arm improved faction outcomes **and**
shifted several independent, monotonic, role-relevant proxies in strategically expected directions
(town eliminates more enemies / fewer allies; healers intercept more real attacks on allies;
investigators find enemies above chance; vigilantes spend shots on enemies; wolves target higher-value
enemies while keeping cover) → memory **likely** improved play, subject to hidden-role variance and game
stochasticity.* Win rate alone is too noisy; one proxy is too indirect; **several independent proxies
moving together is the strong story** (triangulation).

## Open judgment calls — RESOLVED 2026-06-06
1. ✅ Correct-elimination = **wolf + SK** (town metric). Clean 3-way: `wolf_elimination_rate` /
   `anti_town_elimination_rate` (wolf+SK) / `town_mislynch_rate`.
2. ✅ Investigator → **lift-over-random** threat-find-rate (wolf+SK), keep `wolf_find_rate` separate; no
   town-clear credit (known undercount, flagged).
3. ✅ Healer denominator = **action-nights** (attacks always happen → already opportunity-normalized);
   split into overall / town-save / friendly-fire-save / wolf-block.
4. ✅ **Keep `town_vote_accuracy`** (dense per-vote complement; luck-laden-monotonic).
5. ✅ Judges = **diagnostic + frozen-set extraction**, out of the A/B-comparison basket. (Deterministic
   first for *scoring*; judges help *curate* the frozen eval set from traces — a tracing requirement.)
6. ✅ SK = **survival-nights gradient** (not the binary win); vigilante = raw shot counts
   (`num_evil_shot` / `num_friendly_fire` / holds / bullets-unused), not-shooting never penalized.

## Implementation status

**✅ IMPLEMENTED 2026-06-06 (commit `93b1137`).** `compute_metrics.py` + `schemas/metrics.py` rewritten
to the v2 set; `analyze_batch.py` metric lists synced. Verified: 25/25 unit assertions + a clean live
memory-off game (SK-lynch credited → `correct_elimination_rate 1.0`; healer save family incl. a non-wolf
block; investigator `lift 2.43`; vigilante friendly-fire captured; SK survival gradient; per-vote
`town_vote_accuracy`). All computed post-hoc from existing trace fields — **no node/prompt changes**, so
it works on existing traces too. **DEFERRED (post-MVP, downstream):** per-killer night attribution
(`who-killed-who` / `deaths_attributed` / killer-resolved `exit_method`) — drafted once then reverted;
`exit_method` currently returns generic `killed_at_night` (no false `killed_by_wolves`).

## Next step — tracing-sufficiency audit
Verify a game emits everything the OTHER evaluation forms need: (1) **LLM-as-judge completeness** — does
each eval span already carry all judge inputs (situations, visible discussion, private context, retrieved
memory+scores, action, adoption)? (2) **fine-tuning / "make it work better" experiments** — pre-rerank
candidate pools, store snapshots, intermediate decisions. Then the proxy-vs-win monotonicity correlation
(needs a real batch) confirms basket strength.

## Monotonicity validation — DONE 2026-06-11

The deferred proxy-vs-win correlation check ran on the existing v5 games (30 memory-off +
20 memory-on, zero new games): point-biserial per proxy vs own-faction win, pooled + OFF-only.
Full table + read: `proxy_win_monotonicity.md` (regenerate via `proxy_win_monotonicity.py`,
which uses `evaluation/src/core/stats.py`). Headline: the town decision-quality basket
(`town_vote_accuracy`, `correct_elimination_rate`, `mislynches`, `serial_killer_lynched`) is
strongly validated (|r|≈0.55–0.65, p<0.01, both views) — use it to power the Phase C A/B. The
investigator rate proxies are NOT validated (~zero or wrong-sign; `investigator_found_wolf_day`
significantly backwards, plausibly game-length confounded). Wolf social proxies are underpowered
on v5 (degenerate sub-Ns), not invalidated.

## Follow-up validation + the mediation reading — 2026-07-07

*(The chronology between the 2026-06-11 section above and this one — the 2026-07-02 N=180 audit that
rescued `wolf_power_kill_rate`, discovered `town_accusation_precision`, and set the current tier
frozensets — lives in [`metrics_audit/proxy_discovery_log.md`](metrics_audit/proxy_discovery_log.md);
the finalized shape it produced is [report.md](report.md).)*

Two pre-registered $0 follow-ups ran on the same N=180 set (runner
`evaluation/src/instrument_validation/proxies/proxy_followup_rescue.py`; full figures in the audit log
§④), each triggered by an owner challenge to the tiering:

- **F1 — does `town_accusation_precision` add win signal beyond `town_vote_accuracy`?** The 2026-07-02
  audit flagged the coupling (r=+0.558) but never partialled it. Answer: **no** — partial r = +0.02
  (p=.76, n=175), halves −0.09 / +0.17; the raw +0.340 reproduced exactly. Diagnostic placement
  confirmed on direct evidence.
- **F2 — does `vigilante_correct_shot_rate` firm up at N=180?** The v5 promise (+0.43, p=.050, n=21
  shooter games) **diluted to +0.18 (p=.20, n=53)** — sign holds, still unvalidated. The vigilante shot
  in only 53/180 games at this epoch (29%, vs 72% in v5 — an unexplained behavior shift, flagged not
  investigated).

**The mediation reading (the insight F1 forced).** For town, the collective day vote is nearly the only
actuator: discussion changes the outcome by *becoming votes*, so `town_vote_accuracy` is a **mediator**
on the causal path, and partialling out a mediator removes the causal route itself. F1's null therefore
reads "no bypass path" — and it *predicts* that any town discussion proxy, however built, partials to
~zero against win at game grain. An independent instrument shows the same structure: the LLM tagger's
discussion verdict, partialled on the vote proxy, gives **+0.02 town** vs **+0.56 wolf / +0.60 SK**
(N=24; different instrument and sample, so qualitative agreement) — deceiver discussion acts on *other
players'* votes, a path its own vote proxy does not mediate. Design consequence, stated once: **measure
downstream (outcome-validated endpoints), teach upstream (reasoning quality as decision-grain credit)**
— and nothing is lost to the ruler, because full mediation means a real discussion improvement *shows
up in* `town_vote_accuracy`. Folded into [report.md](report.md) §3/§5.

**Open question (with the owner, not yet decided):** the vigilante fork. `vigilante_correct_shot_rate`
is *logically anchored* — a landed evil shot IS a threat elimination, the construct the validated
`correct_elimination_rate` (+0.65) expresses — but *statistically underpowered* (a ≤2-bullet rare
event; detecting r≈0.18 at 80% power needs ~240 shooter games ≈ 800+ games at this epoch's 29% shot
rate). Whether the ledger should carry a named "logically-anchored, underpowered" status distinct from
"invalidated", and whether a combined town threat-removal form (lynches + vigilante evil-shots) should
be pre-registered as a candidate, is an open tiering-policy call.

**Resolution (same day).** The owner's requirement is *per-cell coverage*: every (role, phase) decision
cell should have its own readout unless none can exist — coverage being a different property from witness
validity, which the tier system alone expresses. Adopted: a **cell-coverage map** in [report.md](report.md)
§3 (all cells now accounted for: basket, diagnostic, or an explicit reason), and a new
**"logically-anchored decision endpoint"** license for the definitional-sign-but-underpowered class —
`vigilante_correct_shot_rate` is its first member (may read the vigilante-night cell in an A/B via
arm-level pooling; may not carry a headline verdict). The wolf-night cell was found less bare than it
looked: `wolf_power_kill_rate` (diagnostic) plus mirror-validation of the same event family from the town
ledger (`power_roles_killed_by_evil` ★, −0.40). The combined town threat-removal candidate (lynches +
vigilante evil-shots) stays parked, not pre-registered.

## 2026-07-11 — consumer-side supersession: the credit redesign retires the tagger's credit role

A pointer entry, not a metrics change: the read/tactic credit redesign
([`../credit/read_tactic_credit_redesign.md`](../credit/read_tactic_credit_redesign.md))
retires the LLM tagger as a credit source — day-discussion credit adopts the validated day-vote endpoint
(M1, held-out +0.51) plus a move-grain advocacy rule; the night read-quality override is replaced by a
read-partition over the deterministic outcome; the tagger stays as a standing diagnostic. **The ruler this
folder documents is untouched** — every basket proxy and diagnostic reads engine facts (plus the one
stance-tag diagnostic), and `addressed_targets` remains in the live output schema, which the redesign
itself depends on. `report.md` §5 and §7 are stamped in place; wiring is pending.

One forward-looking note for the ledger's dead wolf-discussion family: the redesign's advocacy/first-link
instrument separates *leading* from *joining* deterministically (a stance-tagged accusation on X **before**
the room's votes move to X), which is exactly the semantic question that made `wolf_steering_rate`
uninterpretable. Once built for credit it becomes a win-testable candidate for the wolf-discussion cell —
through the normal gate (empirical-sign class, momentum-adjusted), not the logically-anchored license.
Until that test, the `wolf_steering_rate` lesson stands.
