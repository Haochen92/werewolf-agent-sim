# `v5_0_nethorizon` — net-horizon outcome framing: implementation spec

**Status:** design frozen, build delegated. Free echo-read gate **PASSED** (see `experiment_log.md`
§"Step-3 echo read") → this build is warranted. Frozen `v5_0` is the control and stays untouched.

## 1. Hypothesis & why this is freeze-clean

The wolf/SK day-leak (memory-on wolves dissent more → lynched more → win flat/negative) traces to
**myopic outcome framing**: extraction credits the immediate result in the lead clause and defers the
cost to a subordinate "However…" clause. A skimming agent absorbs the headline (action → survived
today) and under-weights the concession (it cost the game). Two failure modes, two fixes:

- **×137-type (reading failure):** the cost IS recorded, but in the weak trailing clause → fix by
  **net-first composition** (lead with the verdict).
- **×75-type (recording failure):** the cost was never traced (extractor stopped at the next-day
  effect, or N=1 it genuinely never backfired) → fix by a **required end-of-game verdict field** the
  extractor must commit to before writing anything.

**Freeze-clean** because (a) it's a **config-flag store variant** — default `v5_0` untouched, frozen;
and (b) it is **not a play-prompt change** — extraction runs post-game, so there is no
game-generation epoch shift. The stored wording becomes agent-visible at retrieval, but that is the
*treatment* of a controlled A/B (same seeds, same epoch, `v5_0` vs `v5_0_nethorizon`), not an
uncontrolled confound. Adoption posture: **adopt-if-win BEFORE Phase B labels are minted** (obs
rerank uses the full entry → outcome wording is label-visible → adopt-then-label, never mix).

## 2. Schema change — `Agents/schemas/memory.py`, `Observation` (model-visible, @ :41)

Replace the single `outcome` **field** (:99–104) with two REQUIRED model fields + a derived
composer. `Observation` is FROZEN/model-visible: keep `Field(description=)`, **no class docstring**
(it would leak into the JSON schema).

```python
impact_on_final_game_outcome: str = Field(
    description=(
        "The NET effect of this approach on THIS role's win condition, judged from the END "
        "of the game (you know the final result). An action that helped in the moment but "
        "contributed to this role's later elimination or the faction's loss is a NET NEGATIVE "
        "— say so explicitly. Name the causal chain (what it led to). If the net effect is "
        "genuinely untraceable, write 'unclear' and say why. 1-2 sentences."
    )
)
immediate_response: str = Field(
    description="How others responded in the moment — the immediate, same-turn/next-turn effect. 1 sentence."
)
```

**The composer — make `outcome` a `@computed_field` property, net-first** (this is the zero-ripple
move, see §5):

```python
@computed_field  # appears in model_dump (back-compat) but NOT in the structured-output input schema
@property
def outcome(self) -> str:
    return _compose_outcome(self.impact_on_final_game_outcome, self.immediate_response)
```

Add a module-level `_compose_outcome(impact, immediate)` mirroring `_compose_situation` (:22), net
first: `f"{impact} {immediate}"` (or `impact` alone when `immediate` is empty). **Reading order =
composition order = net first.** `StoredObservation` (:248) is UNCHANGED — its `outcome: str` is
populated from `observation.outcome` (now the composed string) at write time.

> **Verify (one line each):** `with_structured_output(Observation)` does **not** include `outcome` in
> the schema sent to the model (computed fields are output-only — if your pydantic/langchain version
> leaks it, fall back to a plain `@property` named `composed_outcome` and swap the §5 sites instead);
> and `model_dump()` still carries an `outcome` key (so the generic `serialization.py:17` dumper and
> any sidecar shape stay back-compatible).

## 3. Prompt change — `Agents/prompts/extraction.py` (three live spots)

The outcome bullet appears in **three** blocks; the per-role one is what v5 runs. Change all three,
keep the wording near-identical to the `Field(description=)` text above:

- **`:107`** (general block) — `outcome:` bullet.
- **`:328`** (per-role block; the LIVE v5 path: `ROLE_EXTRACTION_PREFIX` + `ROLE_EXTRACTION_TAIL` @
  :408, also `ROLE_PHASE_EXTRACTION_TAIL` @ :434) — `outcome:` bullet.
- **`:522`** (the "Scenario → Approach → Outcome" formatting block) — the `Outcome:` line.

Replace each "What resulted — how others responded and the downstream consequences" with the split:
an **impact_on_final_game_outcome** bullet carrying the end-of-game judgment rule (net-first;
helped-today-but-eliminated-later = net negative; untraceable → "unclear" + why; name the chain) and
an **immediate_response** bullet. Also update the **PERSPECTIVE-RULE** lines that name `outcome` by
field (`:112`, `:120`, `:333`–`:337`) to reference the two new fields. The current "downstream
consequences" wording *permits* myopia (it doesn't force the horizon) even though the extractor is
omniscient with `GAME OUTCOME` in context (:67/:288/:499) — that permissiveness is the bug.

## 4. Metadata (NOT injected to the agent — one treatment per arm)

Add to the extraction output / entry metadata (NOT into the embedded text, NOT into the composed
prose the agent reads):

- **`net_verdict`** enum: `positive | negative | mixed | unclear`. Entry metadata only. Its
  **unclear-rate is a free extraction-reliability metric**; `unclear` is a first-class value (honors
  genuine N=1 ambiguity instead of forcing a false positive — this answers the user's "maybe the LLM
  genuinely doesn't know" point). Injecting a verdict *tag* to the agent is a **separate follow-up
  arm**, deliberately not bundled here.
- **`source_game_winner`** (+ `role_faction_won: bool`): copied at **dump time** by an objective
  `game_id → batch-record winner` join (no LLM). **Soft-signal / analysis & soft-rerank only — NEVER
  a hard filter** (role-won ≠ action-good).

## 5. Accessor blast radius (resolved by the `@computed_field` choice)

`Observation.outcome` is read at these PRE-STORE sites. With the `@computed_field` `outcome` above,
**all keep working unchanged** (they read the composed string):

- `Agents/memory/deduplication/store_ops.py:192` — the KEEP-path store write.
- `Agents/memory/deduplication/dedup_agent.py:102` — `new_outcome=observation.outcome`.
- `Agents/memory/deduplication/prefilter.py:75` — prefilter content string.
- `Agents/memory/deduplication/pipeline.py:74` — dedup pipeline dict.

Sites reading off `StoredObservation` / `RetrievedObservation` (e.g. `rerank_agent.py:102`) already
read the stored composed string — untouched either way. **If** you fall back to a plain
`composed_outcome` property (because computed_field leaked into the input schema), the four sites
above must swap `.outcome → .composed_outcome`; everything else is unchanged.

## 6. Build the variant store (option 1: re-extract from frozen source games)

Re-extract the SAME frozen games that built `v5_0`, changing ONLY the extraction prompt — full role
coverage (NOT the namespace-scoped augment path). Reuse the offline harness:

- Source: `extraction_v5_0.jsonl` frozen cases (the 20-game seed set; one extraction prefix per
  game). `Agents/memory/extraction/inputs.py::extraction_inputs_from_frozen_case` rebuilds the
  extraction input offline.
- Extractor: the canonical per-role `Agents/memory/extraction/extraction_agent.py` (the v5 path), now
  carrying the new prompt. Do **not** use `augment_agent.py` (that's namespace-targeted).
- **Mirror the v5_0 seeding pipeline exactly** — same dedup config, same flow (see
  [[project-v5-seeding-and-seedability]] / `scripts/`), changing only the prompt — so the store
  differs from `v5_0` in outcome framing and nothing else. Output → `memory_stores/v5_0_nethorizon/`.
- Cost ~$2–5 (prefix-caching fan-out).

## 7. Validity diagnostic — situation-sim (NON-BLOCKING, recorded)

Demoted from a gate to a recorded diagnostic (decision 2026-06-12): a positive arm result means "this
store helps" regardless; the sim number only governs whether we can additionally claim "the *framing*
is why," and — more importantly — lets us **interpret a null** (drift can spuriously help OR mask a
real effect, so a null without the sim is uninterpretable). Do NOT block the arm on it.

- Per entry, cosine of the **situation embedding** (`composed_situation`), `v5_0` vs
  `v5_0_nethorizon`, paired within `(game_id, role, action_phase)` buckets by nearest match. (Approach
  sim as a secondary single-treatment check — approach isn't embedded so it can't move retrieval, but
  it IS in the read entry.)
- **Set the threshold by a noise floor, not a guess:** re-extract a few games with the *unchanged*
  prompt and measure entry-to-entry situation sim — that distribution is extraction's own
  non-determinism. Bar = nethorizon sim ≥ that floor.
- Cheap: `v5_0` situations are already embedded (cached in the store); only embed nethorizon + the
  null run. Likely sits ~0.97+ (same task/transcript, one field's instruction changed).

Report line shape: `situation-sim mean X (null-floor Y)` → positive+stable = clean "framing helps";
positive+drift = "store helps, framing caveated"; null → read against the sim.

## 8. The arms — pre-registration (wolf + SK, one store serves both)

One re-extraction produces all roles → `v5_0_nethorizon` serves both arms. Same 30-id seed set, same
epoch, `--no-memory-dump` consumption mode, observations-only, top_k=5 — i.e. the exact paired-A/B
treatment, swapping only the store.

- **Wolf arm.** PRIMARY = `wolf_unconditioned_blending_rate` (validated; now in `compute_metrics`),
  PREDICT recovers toward **0.84** (baseline) from the wolf-mem 0.64. Secondaries:
  `wolf_elimination_rate` → ~0.227 (down from 0.29–0.34), `wolf_power_role_targeting_rate` stays
  elevated (the night gain must NOT be sacrificed), wolf win directional. Compare vs BOTH the
  same-epoch baseline (off) and the `v5_0` wolf arm (raw memory) — the latter is the key contrast
  (framing vs no-framing-fix, same retrieval).
- **SK arm.** PRIMARY = `sk_exit_method` lynched-rate back toward baseline (from 78%), `sk_nights_
  survived` held, SK win directional. NOTE the SK echo read is a separate **day_discussion-content**
  cut (the solo SK has no vote-pile to blend with) — flagged as a lighter secondary, not a blocker;
  the SK arm rides the shared store.

Frame & discipline: one line per arm in the plan before unblinding; primary = the validated proxy,
win rate = underpowered directional co-read (N=30). All other cuts exploratory.

## 9. Sequencing checklist

1. Schema split + `_compose_outcome` + `@computed_field outcome` (+ verify the two one-liners in §2).
2. Prompt: all three blocks + PERSPECTIVE-RULE lines + matching `Field(description=)`.
3. Metadata: `net_verdict` (extraction output → entry metadata); `source_game_winner` join at dump.
4. (Opportunistic, cosmetic) `perspective` description still lists only "wolf, villager, healer,
   investigator" (`Observation` :44, `StrategyPoint` :136) — predates the 9p SK/vigilante set. The
   `field_validator` (:116) already enforces against canonical `roles`, so this is doc-only; fix in
   the same schema pass.
5. Build `memory_stores/v5_0_nethorizon/` (re-extract frozen cases, mirror v5_0 pipeline).
6. Validity diagnostic (situation-sim + null floor) — record, don't block.
7. Pre-register the two arms (one line each) → run wolf + SK, N=30 paired, in-epoch.
8. Analyze (extend `analyze_ab.py`); if win → adopt the prompt into the default extraction path
   BEFORE any Phase B labels exist; one-line note in this folder + the seeding memory.

## Pointers

- Echo-read gate (PASSED): `echo_read.py` / `echo_read_decisions.json`.
- Proxy + blending instruments: `diagnose_wolf_sk_proxies.py`, `diagnose_wolf_blending.py`;
  `wolf_unconditioned_blending_rate` now in `Agents/compute_metrics.py`.
- Seeding flow & footguns: [[project-v5-seeding-and-seedability]]; offline re-extraction:
  `Agents/memory/extraction/{inputs,extraction_agent}.py`.
