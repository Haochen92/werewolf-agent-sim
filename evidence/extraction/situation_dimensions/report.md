# Situation Dimensions — how they work today

**Orientation.** The *situation dimensions* are the structured, state-describing fields attached to every
stored observation and every live retrieval query. One per-cell schema drives all three of their jobs at
once:

```
                                   ┌─ embed string (free-text dims) ─▶ semantic retrieval
game state ─▶ per-cell            ─┤
             SituationSchema       ├─ numerics/enums (players_alive, is_swing, …) ─▶ reranker + gating
             (extraction OR query) │
                                   └─ valenced subset (heat, exposure, parity-progress) ─▶ procedural reward
```

A dimension describes *what is true on the board, in the agent's epistemic voice, with zero
should/recommend language* — **"situation = state, never prescription."** The advice ("how to act") is the
retrieved *payload*, never a matching field. That invariant is why the same fields can serve retrieval,
gating, and reward without contradiction: all three *read* the situation. The path that produced this
design is [experiment_log.md](experiment_log.md); how the output is *measured* lives in the apparatus
notes for [retrieval](../../evaluation/llm_judge/agent_decision.md) and
[extraction](../../evaluation/llm_judge/extraction.md).

## What they are (current schema)

The schema is a **mixin DAG → 11 cells**, one per `(role × {day, night})`
([`memory.py`](../../../Agents/schemas/memory.py), `BaseSituation` :306, `cell_situation_schema_for` :635):
`BaseSituation` plus optional mixins compose into one `SituationSchema` per cell, and the 17 role×phase
combinations collapse to **11** because the two day phases share a cell (the discussion *is* the
target-finding for the vote) — **day-vs-night is the only validity-breaking gate**. Not every cell carries
every field (a night cell has no consensus/heat; only the wolf day cell has `ally_revealed`). The fields,
grouped by what they describe — with how each is represented and how far it can be trusted:

| Dimension | What it describes | Representation | Reliability |
|---|---|---|---|
| **A · Spine** — *what is happening* (every cell) | | | |
| `situation` | the core decision the agent faces right now | embed | — semantic¹ |
| `information_landscape` | what is known / claimed / unknown on the board | embed | — semantic¹ |
| **B · Criticality** — *how much is at stake* (the `game_phase` rescope → proxy) | | | |
| `players_alive` | living-player count | computed → gate | ✅ deterministic (LLM fill was 0.99 bucket) |
| `distance_to_parity` | town deaths from a wolf-parity win (others − wolves) | gate-excluded² | ❌ LLM-filled — 0.05–0.09 exact, MAE ≈2 |
| `is_swing` | one swing from decided (distance ≤ 1) | gate key | ❌ LLM-filled — wolf 0.606, worse than always-False (0.827) |
| `criticality_stakes` | the stakes phrased as an implication | embed | — semantic; derived from the numbers³ |
| **C · Consensus** — *where the room stands* (day cells) | | | |
| `consensus_text` | the room's alignment / vote texture | embed | — semantic¹ |
| `my_position` | driving / with-majority / holdout | embed | — semantic¹ |
| `consensus_direction` | the room aligns with vs opposes my read | rerank enum⁴ | ⚠️ unvalidated; hindsight-leak guarded |
| **D · Exposure** — *how visible / at-risk I am* | | | |
| `heat_now` | suspicion currently on me (all roles) | embed | — semantic¹ |
| `forward_exposure` | visibility / cost of a contemplated move | embed | — semantic¹ |
| `exposure_class` | coarse safe vs exposed | gate key (enum) | ⚠️ **UNVALIDATED** — spot-check pending |
| **E · Targets & private info** — *what I can act on / what I know* | | | |
| `target_landscape` | candidate set + role / status / evidence basis | embed | — semantic¹ |
| `public_private_text` | my private-vs-public information gap | embed | — semantic¹ |
| `divergence_sign` | private info confirms vs contradicts public | rerank enum⁴ | ⚠️ unvalidated |
| `info_landscape_class` | coarse info-poor vs info-rich | gate key (enum) | ⚠️ **UNVALIDATED** — spot-check pending |
| **F · Role conditioners** — *regime-flippers* | | | |
| `bullets_left` | vigilante shots remaining (0 → reverts to villager) | computed → gate | ✅ deterministic (LLM fill was **0.164** — the worst) |
| `ally_revealed` | a wolf partner is dead / outed (vote calculus flips) | computed → gate | ✅ deterministic (was 0.975 as LLM fill) |

**Legend.** *Representation* — **embed**: folds into the retrieval string (recall); **gate key / rerank
enum**: a numeric/enum *excluded* from the embed, read by the dimension gate + reranker; **computed**:
overwritten deterministically from game state at query time. *Reliability* — ✅ deterministic/sound · ❌
LLM-filled & unreliable · ⚠️ no deterministic truth (unvalidated) · — semantic free-text.

¹ *semantic* = no deterministic ground truth; quality is graded by the NDCG retrieval golden and the
(deferred) sampled review, **not** the $0 accuracy audit — the audit can only touch the numeric/bool dims.
² `distance_to_parity` is deliberately excluded from the live gate (it screened flat).
³ derived from the LLM's own numbers and *not* re-derived after the numeric override, so it can lag a
corrected `players_alive` (gap 4).
⁴ direction/sign enums are *also* phrased as an implication into the neighbouring embed text (so recall
isn't sign-blind) while the exact enum goes to the reranker.

**Why some dims are prose and some enums.** Not per-field taste — one rule: a low-entropy *sign or regime*
(which a bi-encoder can't recover from a pooled vector) gets an **enum** for the reranker, while its
**prose** sibling carries the same fact as recall narration. Every prose field that has such a signal is
paired with an exact sibling:

| prose (embed · recall) | exact sibling (rerank / gate) |
|---|---|
| `information_landscape` | `info_landscape_class` (enum) |
| `consensus_text` + `my_position` | `consensus_direction` (enum) |
| `heat_now` + `forward_exposure` | `exposure_class` (enum) |
| `public_private_text` | `divergence_sign` (enum) |
| `criticality_stakes` | `players_alive` / `distance_to_parity` / `is_swing` (numbers) |
| `situation`, `target_landscape` | *(none — genuinely open; no minimal-pair signal to lose)* |

So an enum exists only where the embedding *smears* a near-minimal-pair (aligns-vs-opposes,
confirms-vs-contradicts). `my_position` is the one borderline left as prose: its three values are distinct
content the embedding separates on its own, and its directional sign is already `consensus_direction`.

## Guarantee / contract (present-tense)

- **One schema, three consumers, cannot diverge.** The live query and the stored observation are composed
  by the *same* per-cell `SituationSchema` through the *same* serializer (`compose_situation_embed`,
  [`memory.py`:68](../../../Agents/schemas/memory.py#L68)), so a query and the observations it should match
  share vocabulary and structure in embedding space **by construction**, not by a shared prose convention.
  Every row in a namespace is the same subclass — the symmetry that makes one-vector-per-cell safe.
- **State, never prescription.** Every dimension is board state; the objective/advice is payload. This is
  the enforced leak boundary *and* what keeps the embedding state-only.
- **Agent-knowable dims are computed, not trusted from the LLM.** At query time `players_alive`,
  `bullets_left`, and `ally_revealed` are computed from game state and used two ways: **injected into the
  query prompt** (`_known_board_facts`) so the embedded `criticality_stakes` prose is written from the true
  numbers, and **re-asserted on the parsed object** (`_override_deterministic_dims`,
  [`situation_agent.py`:103](../../../Agents/memory/retrieval/situation_agent.py#L103)) so the gating dims
  are exact. Both derive from one `_computed_dims` source, so the number the model is told can never
  disagree with the one it is overridden to.
- **Numbers and signs go to the reranker; their *implication* goes to the embed.** Exact numerics/enums
  are excluded from the embedding (a bi-encoder mangles magnitudes and smears minimal-pair directions) and
  handed to the reranker/gate. A regime or direction is *also* phrased as an implication into the embedded
  text ("every vote decisive," not "endgame"), because a wrong-regime neighbour is the *opposite* lesson
  and recall is the one stage no reranker touches.
- **At most two queries per turn**, each a genuinely distinct decision
  ([`situation_agent.py`:54](../../../Agents/memory/retrieval/situation_agent.py#L54), `min=1, max=2`); a
  summary failure degrades that turn's retrieval, never blocks the decision.
- **What is NOT guaranteed.** `is_swing` / `distance_to_parity` are still **LLM-filled and unreliable**
  (they need hidden roles); the two enum gate keys (`exposure_class`, `info_landscape_class`) are
  **unvalidated**; and every retrieval number predates the live `v6_1` store. See the gaps table.

## The mechanism / model

- **Live query.** `_generate_situations_for_agent`
  ([`situation_agent.py`:139](../../../Agents/memory/retrieval/situation_agent.py#L139)) is **phase-aware**:
  `cell_situation_schema_for(role, action_phase)` returns the v6 cell → V6 prompt → 1–2 structured
  situations → deterministic override → `compose_situation_embed`. A (role, phase) with no v6 cell drops to
  the legacy v5 per-role `SituationSummary` (free prose, no dims). Model: flash-lite, no thinking (runs
  every turn; the model study kept it — the gain from 3.5-flash was modest at 6× cost).
- **Stored side.** Post-game extraction fans out per cell
  (`extract_postgame_per_cell`, [`extraction_agent.py`:290](../../../Agents/memory/extraction/extraction_agent.py#L290);
  cells from `ROLE_UNITS`, [`cell_units.py`:16](../../../Agents/memory/extraction/cell_units.py#L16)),
  binding the same per-cell schema so every stored observation carries the dims. Under v7 the dims ride on
  **observations only**; strategy points are synthesized cross-game.
- **Gating.** `dimension_gating.reweight`
  ([`dimension_gating.py`:58](../../../Agents/memory/retrieval/dimension_gating.py#L58)) is a **soft**
  multiplicative tilt (`WEIGHT = 0.3` → 0.7×–1.3×, never zeroes) over the alignment of **four** keys:
  `players_alive`(bucket) + `is_swing` + `exposure_class` + `info_landscape_class`. `distance_to_parity` is
  deliberately **excluded** (it screened flat). It is **live-wired but default-OFF per role**
  (`dimension_gating_config.get(role, False)`) — a screened knob, not a shipped default.
- **Criticality proxy.** The deterministic truth `query_criticality(surviving_players, roles)`
  ([`decision_scoring.py`:115](../../../evaluation/src/loop/decision_scoring.py#L115)) computes the full
  triple offline (town-lensed wolf parity: `distance_to_parity = others − wolves`, `is_swing = distance ≤ 1`).
  This is the audit's ground truth and the diagnosis sampler's leverage anchor — **it is never shown to a
  live agent**, which is precisely why the live `is_swing`/`distance_to_parity` cannot be computed and stay
  LLM-filled.

## Config / defaults

| Setting | Value | Where |
|---|---|---|
| live query schema | v6 per-cell (embed-aligned with extraction); v5 per-role fallback | `cell_situation_schema_for` (memory.py:635) |
| queries per turn | 1–2 structured situations | `_summary_container` (situation_agent.py:54) |
| agent-knowable dims | computed from game state (`players_alive`, `bullets_left`, `ally_revealed`) | `_override_deterministic_dims` (situation_agent.py:103) |
| `is_swing` / `distance_to_parity` | LLM-filled (need hidden roles) | — |
| dimension gating | soft tilt (WEIGHT 0.3), 4 keys, **default-OFF per role** | dimension_gating.py:58 · retrieval/plan_gating.py:121 |
| current store | `memory_stores/v6_1` (obs-only under v7) | — |
| query model | flash-lite, no thinking | accessors.py |

## Verification

Four instruments measure the dimensions, each answering a different question. **The verdict: the schema's
*retrieval* value is verified, its *conditioning* hypothesis is not, and its LLM-filled numerics are — for
two fields — unreliable.**

| Apparatus | What it certifies | Result | Reliability of the apparatus |
|---|---|---|---|
| **NDCG retrieval golden** | Do the structured dims *retrieve* better than prose? | v4b prompt **+0.061 NDCG** (structured dims, no core-dilemma, lens-fix) | Strongest anchor in the repo (human-graded, offline, $0) — but **v4-store-stale, partly machine-augmented, can't separate query from store** |
| **Criticality screen** | Conditioning on the regime · *and* aligning the query | Conditioning: **No** — the endgame signature (+0.25) was a same-game leak; held-out sign-flipped +0.061 → −0.037 across identical runs (temperature noise). But **aligning the query to v6 dims raised memory's lift over no-memory +0.088 → +0.120** — the rewrite improves retrieval even where conditioning doesn't | Triage, not verdict; n=7–23 in the endgame stratum where villagers rarely survive |
| **Forced-schema screen** | Does forcing per-memory reasoning engage the dims? | Forcing **hurt v5 (−0.104), neutral on v6 (+0.021)**; v6 beats v5 under it → migrated to production | n=48, McNemar not significant; the first engagement rate (0.697) was inflated by partial coverage → true ~0.55 |
| **Dimension-accuracy audit** | Are the *filled values* correct? | `players_alive` 0.990 bucket ✓, `ally_revealed` 0.975 ✓; **`bullets_left` 0.164 ✗, wolf `is_swing` 0.606 (< always-False 0.827) ✗** | $0, deterministic, pre-registered rule; audits the *query* side only (stored side weakly bounded) |

**What none of them can do:** certify that the criticality-*conditioning* hypothesis is dead (the endgame
stratum is data-starved, not disproven — "below the noise floor," not "zero"), validate the two enum gate
keys (no deterministic truth; the spot-check is built but unlabeled), or speak to the stored-side fills
(no frozen board travels with a stored observation).

**Apparatus home.** The two standing rulers now live in
[`instrument_validation/dimensions/`](../../../evaluation/src/instrument_validation/dimensions/):
`dimension_audit.py` (the $0 fill-accuracy audit above) and `dimension_gating_screen.py` (the RE-OPENED
soft-gating screen). Their instrument-trust verdict is
[`evaluation/dimension_extraction/report.md`](../../evaluation/dimension_extraction/report.md).

## Case study — the audit that re-opened a "negative" verdict

**Verdict (skim this, skip the rest).** A 2026-07 review found every v6 dimension was LLM-filled and had
*never* been checked against ground truth, even where truth was free from the board. A $0 deterministic
audit then showed two gated fills were not merely imperfect but **anti-informative** — wolf-side `is_swing`
at 0.606 is *worse* than always guessing False (0.827), and `bullets_left` is right 16% of the time. The
impact was epistemic, not a live crash: the production dimension-gating null had been recorded as a clean
*negative* ("gating doesn't help → default-off"), but a gate keyed partly on noise attenuates any true
signal to ≈0.60 of nominal, so the honest verdict is **"Unknown, not false."** It was fixed at the source
for the agent-knowable half (those dims are now computed, not filled) and bounded for the rest; the paid
re-screen that would settle the `is_swing` half is authorized but held on spend.

*Forensics below — skip unless auditing the number.*

- **Cause.** The `game_phase → criticality` rescope made `is_swing`/`distance_to_parity` *proxy* fields,
  but their derivation was left to the LLM (a design reversal in experiment_log §5, correct for the
  *stored* side where no board moment can be pinned — but the *query* side does have a pinned moment and was
  never given the deterministic treatment it could have had).
- **Composition.** ~20k query-side situation objects across three loop-era runs, scored against each case's
  own frozen board with a mandatory epistemic split (agent-knowable fill error vs vs-omniscient
  disagreement). Pre-registered rule: RE-OPEN if any gated dim < 0.80.
- **Detection & one self-inflicted catch.** Wolf-side `is_swing` = 0.606 fired RE-OPEN. A first pass had
  also dinged wolf `players_alive` to 0.71 — traced not to a fill error but to 176 wolf-night cases that
  persist an *empty* roster (truth read as 0); the runner now skips those (`no_roster`), and corrected wolf
  `players_alive` is 0.97. *Logged, not laundered.*
- **Severity / scope.** Re-opens the **gating** screen only. The **criticality** screen is untouched (its
  query side already computed truth deterministically), and the content-bottleneck conclusion stands (it
  rests on the follow-rate result, not on gating).
- **Fix & verification.** The three agent-knowable dims (`players_alive`, `bullets_left`, `ally_revealed`)
  are now computed from game state at query time — **injected into the prompt** (`_known_board_facts`) so
  the embedded stakes prose is written from truth, and re-asserted post-parse (`_override_deterministic_dims`)
  so the gating dims are exact. `is_swing`/`distance_to_parity` stay LLM-filled pending the offline
  re-screen. Guarded by `tests/test_situation_dim_override.py` (15 cases: override, injected facts, and the
  single-source invariant); the audit truth-fns by `tests/test_dimension_audit.py`; full suite green (507).

## Current-vs-documented gaps (freshness: 2026-07-04)

Ordered by how misleading each is to a reader. Severity weighs likelihood × impact × detectability, not
impact alone.

| # | Gap | State | Severity |
|---|---|---|---|
| 1 | **The gating verdict is "unknown," not negative** | Wolf `is_swing` (0.606) is worse than a constant; the gate keyed on it, so the default-off decision rests on an *uninformative* null. Resolution = the **~$10–15 offline gating re-screen** (deterministic `players_alive` + offline `is_swing` into the frozen cases), authorized by the RE-OPEN rule, **held on spend sign-off**. The single cheapest step that converts "unknown" → verdict. | **High** |
| 2 | **The two enum gate keys are unvalidated** | `exposure_class` / `info_landscape_class` have no deterministic truth; the audit reported only their (skewed) distributions. The spot-check sampler is **built** (`eval-case-sample`, forces ~half off-diagonal); the ~2h human labeling is **pending**. | Med |
| 3 | **Every retrieval number predates the live store** | The NDCG golden + criticality/forced screens ran on `v4`/`v6_0`; the live store is `v6_1`. The golden is also partly machine-augmented and not wired into the live retrieval judge. Free next step: a **v6_1 NDCG re-baseline** before crediting further prompt tuning. | Med |
| 4 | **Parity/swing wording in the stakes prose is still LLM-estimated** | *(the emit-then-overwrite lag is now fixed — 2026-07-04)* The computable dims (`players_alive`/`bullets_left`/`ally_revealed`) are injected into the query prompt (`_known_board_facts`), so the embedded `criticality_stakes` is written from *those* truths. But `distance_to_parity`/`is_swing` cannot be computed live (they need hidden roles), so any part of the stakes sentence that leans on parity/swing still reflects the LLM's estimate. Bounded, not eliminated; the offline substitution belongs to gap 1's re-screen. (The fields can't simply be dropped from output — shared mixins, extraction needs the LLM fill, dedup partitions on them.) | Low |
| 5 | **Stored-side fills are only weakly bounded** | The audit checks the *query* side (pinned board); stored observations pass only internal-consistency bounds (`\|distance\| ≤ alive`, `alive ∈ [3,9]`, 100% on v6_1) that a systematic bias would survive. Real check = the deferred sampled review. | Low-Med |
| 6 | **Player-ID naming violations in night cells** | 22.1% of night-cell observations name a player ID — game-local-meaningless, so they dilute the retrieval embed (no cross-game leak). Accepted + flagged; belongs to a prompt-tuning cycle. | Low |
| 7 | **Dedup over-merges on the composed prose blob** | The shared section-label scaffolding inflates baseline similarity; the fix (an explicit predicate over the structured gate-fields, not a cosine threshold) is designed, not built. | Low |

**Open work.** The credible upgrades — the offline gating re-screen (gap 1), the enum spot-check (gap 2),
and a v6_1 NDCG re-baseline (gap 3) — stay deferred while the binding memory constraint is store *content*
and the investigator-transmission cap, not dimension fidelity. The two verified wins (aligned-query
retrieval, forced-schema safety) already justify the rewrite; the criticality metadata is kept because it
costs nothing and feeds the reranker, gate, and reward channel even though conditioning on it is not a
demonstrated lever.
