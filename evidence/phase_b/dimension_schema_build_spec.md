# Dimension Schema Build Spec — per-cell situation standard, composable schema + prompt

**Status:** DESIGN LOCKED PENDING SIGN-OFF — no code written. This is the build spec for the
role×phase dimension expansion (Phase B lead-in; the rewrite that **predates** all labelling, so it
must land before any gold labels are conditioned on entry text). Crystallized 2026-06-15 from the
2026-06-13 design discussion (decision_replay `experiment_log.md` cheap-lever ladder → dimension
design; embedding-limits discussion; reranker-fork discussion).

**Fork context:** chosen path = **#2 dimensions-first then freeze**. This spec covers exposing the
fields + composable schema/prompt + the cheap-first screen. The FT-cross-encoder fusion USP
(§7) is explicitly **fork-#3 / deferred** — the schema *exposes* the fields it would need, but
building the fusion+benchmark is not in this build.

---

## 0. The one rule that generates every verdict

> **A field is a hard gate only when crossing it makes a lesson INVALID. Everything else is soft.
> Among soft fields: EMBED the high-entropy free-text (near-miss is useful); EXTRACT to a
> structured field anything you want exact, ordinal, or relational (where approximation is the bug).**

- Validity boundary → **hard gate** → namespace.  (role crosses → a wolf lesson poisons a villager.)
- Degree / applicability → **soft** → stays retrievable, reranker sorts it out.
- Within soft: free-text → **embed**; number/sign/level → **out of the vector**.

Why "out of the vector" is forced, not a preference (bi-encoder = one pooled vector, committed
before the query arrives): mean-pooling **dilutes** low-entropy fields (criticality drowns under the
situation prose); tokenizers are **not magnitude-aware** (`sim("4","8") > sim("4","5")` is possible —
the digits aren't at metric distance 1); embeddings **smear relational direction** ("confirms" vs
"contradicts" share nearly all their words). None of these are fixed by a stronger embedding model —
they're paradigm limits. A stronger model (gemini-embedding) only buys semantic/paraphrase/domain
fidelity + a higher length ceiling.

---

## 1. The embed ledger (per-field verdict)

| field | storage form | in embed string? | rationale | limit type |
|---|---|---|---|---|
| `situation` | free-text | **yes** | highest-entropy, the legit recall driver | model-improvable |
| `information_landscape` | free-text | **yes** | observable, real signal | model-improvable |
| `consensus_text` (D) | free-text | **yes** | descriptive prose of the room | model-improvable |
| `consensus_direction` (aligns/opposes my-read) | **enum + phrased into `consensus_text`** | **yes (content) + enum out** | minimal-pair sign smears → enum for exact rerank, BUT phrase the direction INTO the embedded text ("converging on the player I also suspect" vs "…someone I think is innocent") so recall isn't direction-blind | paradigm (bare enum); content embeds fine |
| `my_position` (driving / voting-with-majority / lone-holdout) | **free-text** (+ optional enum mirror) | **yes** | three values are DISTINCT CONTENT, far apart in embedding space — NOT a minimal-pair polarity flip, so the collapse argument doesn't apply; enum is belt-and-suspenders for the reranker, not load-bearing | model-improvable |
| `heat_now` (suspicion on me + basis) | free-text | **yes** | every role incl. villager (mis-accused villager has real heat) | model-improvable |
| `forward_exposure` (cost of the move I'm weighing) | free-text | **yes** | conceal / observable-act profiles only | model-improvable |
| `bullets_left` (vigilante scarce-resource) | **numeric** (vigilante) | **no** → reranker | the scarce *count* is the signal, smears like player counts; the binary "irreversible" is near-constant within vigilante-night → does no retrieval work, dropped | paradigm |
| `target_landscape` (E) | free-text | **yes** | candidate reads + evidence-vs-behavior basis | model-improvable |
| `public_private_text` (G) | free-text | **yes** | the gap narrative | model-improvable |
| `divergence_sign` (confirms/contradicts) | **enum + phrased into `public_private_text`** | **yes (content) + enum out** | same as consensus_direction: enum for exact rerank, but phrase the direction into the embedded text ("names the same suspect the public does" vs "names someone the public cleared") so recall sees it | paradigm (bare enum); content embeds |
| **criticality**: `players_alive` (int), `distance_to_parity` (int), `is_swing` (bool) | **numeric** | **no** → reranker | low-entropy + tokenizer non-monotonic | paradigm |
| player IDs | canonicalize away | n/a | similarity ≠ identity | paradigm |
| `action` / objective-function | payload | **never matched** | gated in by namespace | — |
| outcome (`impact_on_final_game_outcome`, `immediate_response`), `net_verdict` | payload + metadata | no | net_verdict → reranker valence | — |
| horizon (immediate/mixed/net) | metadata | no | collinear with the role gate | — |

**Composed embedding string** = prefix-joined free-text dims only:
`situation · information_landscape · consensus_text · my_position · heat_now · [forward_exposure] · [target_landscape] · [public_private_text]`
— with the **directional content folded into `consensus_text` / `public_private_text`** so recall is
not direction-blind. The standalone `consensus_direction` / `divergence_sign` enums and the numerics
(`players_alive`, `distance_to_parity`, `is_swing`, `bullets_left`) are the only fields NOT in the string.

### Criticality fields, defined
- `players_alive` — living-player count; the denominator (a vote's weight scales as it shrinks).
  Fully observable by all.
- `distance_to_parity` — `village_side_alive − wolves_alive`, the integer gap that must close to 0
  for a wolf win (start 6 v 2 → 4). Faction-relative; the SK is a separate "last-standing" pole.
  **Hidden-faction-dependent** → encode at the role's certainty (a villager estimates, a wolf knows
  exactly), same discipline as `EPISTEMIC_STATUS_RULE`.
- `is_swing` — whether THIS decision flips the game state (removes last wolf / pushes to parity) vs a
  slack move with room to be wrong. Decision-level, hidden-dependent → role-certainty encoded.

These three replace the coarse `game_phase` bucket: two boards that both read "endgame" can have
opposite criticality; encoding the drivers lets retrieval match decisions that *matter the same
amount*, not games that are roughly the same age.

---

## 2. Composable per-cell schema (the mixin DAG)

One `SituationSchema` per `(role × action_phase)` cell, built by multiple inheritance so each modular
dimension is **declared once** (the matrix's "common spine, role-relative content" expressed as
classes):

```
BaseSituation              : situation, information_landscape,
                             players_alive, distance_to_parity, is_swing
  WithConsensus      (D)   : consensus_text, my_position, consensus_direction[enum]   # day cells; my_position EMBEDS
  WithHeat           (F-a) : heat_now                                                  # day cells, ALL roles
  WithTargetLandscape(E)   : target_landscape                                          # vote + night
  WithForwardExposure(F-b) : forward_exposure                                          # conceal / observable-act
  WithPublicPrivate  (G)   : public_private_text, divergence_sign[enum]                # inv / healer / wolf / SK
  (vigilante night also carries bullets_left[int] — scarce-resource numeric, reranker path, like criticality)
```

The `[enum]` fields (`consensus_direction`, `divergence_sign`) are dual: their **direction is phrased
into the embedded `*_text`** for recall, and the bare enum rides to the reranker for exact comparison.
`my_position` embeds as content (distinct values, not a minimal pair) with an optional enum mirror.

Concrete cells multiply-inherit their profile (F/G written once, not on six roles):

| cell | mixins beyond Base |
|---|---|
| villager · day_discussion | Consensus, Heat |
| villager · day_vote | Consensus, Heat, Target |
| healer · day_discussion | Consensus, Heat, ForwardExp, PublicPrivate |
| healer · day_vote | Consensus, Heat, Target, ForwardExp, PublicPrivate |
| healer · night | Target |
| investigator · day_discussion | Consensus, Heat, ForwardExp, PublicPrivate |
| investigator · day_vote | Consensus, Heat, Target, PublicPrivate |
| investigator · night | Target, PublicPrivate |
| vigilante · day_discussion | Consensus, Heat, ForwardExp |
| vigilante · day_vote | Consensus, Heat, Target, ForwardExp |
| vigilante · night | Target, ForwardExp · `bullets_left`[int→reranker] |
| wolf · day_discussion | Consensus, Heat, ForwardExp, PublicPrivate |
| wolf · day_vote | Consensus, Heat, Target, ForwardExp, PublicPrivate |
| wolf · night | Target, ForwardExp |
| serial_killer · day_discussion | Consensus, Heat, ForwardExp, PublicPrivate |
| serial_killer · day_vote | Consensus, Heat, Target, ForwardExp, PublicPrivate |
| serial_killer · night | Target, ForwardExp |

**Night cells settled by one principle** (no edges left): a mixin attaches iff its dimension is a
*decision input for that cell's action*. Consensus + heat are DAY phenomena (no live consensus at
night; `heat_now` is a discussion read) → **no night cell carries `WithConsensus`/`WithHeat`**.
`WithForwardExposure` attaches at night only where the act is OBSERVABLE and patterns back to you
(wolf kill, vigilante shot — yes; investigator/healer private acts — no). `WithPublicPrivate` at night:
investigator yes (the gap drives who to check), wolf/SK no (the kill is driven by target value +
pattern-risk, not the narrative gap). ⇒ `WolfNight = SKNight = Base+E+ForwardExposure`;
`VigilanteNight = Base+E+ForwardExposure(+bullets_left)`; `InvestigatorNight = Base+E+PublicPrivate`;
`HealerNight = Base+E`.

Villager is the only role with no PublicPrivate and no ForwardExposure — spine + Consensus + Heat
(+ Target on the vote). That simplicity is *why* immediate-framed memory works cleanly for it and why
it's the **cheap-first validation cell** (§8).

---

## 3. The composition function (generic prefix serializer)

`_compose_situation` stops taking positional args. It walks the instance's fields, keeps those marked
`embed=True` (a per-field marker — `json_schema_extra={"embed": True}` or a `ClassVar[frozenset]` of
embed names), prefix-labels each **present** field, and joins:

```
"<situation>  Information landscape: <…>  Consensus: <…>  Heat: <…>  Targets: <…>  …"
```

The composed string **auto-tailors per cell because the field set does** — no per-cell composition
code. Criticality numerics + the three enums are `embed=False`, so they never enter the string.

---

## 4. Single source of truth (the load-bearing symmetry)

The per-cell `SituationSchema` drives **three things at once**:

1. post-game **extraction** output fields (the `Observation` body),
2. live **situation-summary query** output fields (`SituationEntry`),
3. the **embedding composition** (§3).

`Observation` = `SituationSchema` + `approach` + outcome fields; the live `SituationEntry` **is**
`SituationSchema`. Query and storage compositions then *physically cannot diverge* — which is the
constraint that makes one-vector-per-cell safe (every row in a namespace is the same subclass: same
field set, same label structure, same rough length → always comparing like with like, so the
cross-cell length/weight asymmetry never arises). **Lock this before splitting the schema.**

> Caveat inheritance does NOT buy: it shares the field *definitions*, not the stored *rows*. A
> role-invariant table-read ("this bandwagon shape reads as wolf-amplified") still gets re-extracted
> into every namespace that needs it. Mitigation isn't a shared pool (per-cell siloing is the
> deliberate, coherent choice — the prescription differs per cell); it's keeping extraction cheap
> (the cached prefix already does) and accepting role-invariant reads are relearned per cell.

---

## 5. Composable prompt (kills the repeated dimension blob)

Today the dimension guidance is written ~3×: the `SITUATION_SUMMARY` SUFFIX, the extraction prompt,
and referenced again in the dedup prompt. Make the prompt composable like the schema, from one source:

- **Each dimension owns its guidance once.** For the two structured-output paths (extraction +
  situation-summary) the guidance **is** the Pydantic `Field(description=)` on the mixin — both get it
  free from the shared schema, and it cannot drift between them.
- For the **dedup** prompt (compares composed strings, not a structured emit of `SituationSchema`),
  assemble the same fragments from a registry / read them off the schema field descriptions
  programmatically.
- Result: adding/editing a dimension is a **one-place change** propagating to extraction, query, and
  dedup — same single-source discipline as the schema, less repeated prose, no description skew.

---

## 6. Outcome horizon (role-aware `_compose_outcome`)

`outcome` becomes role-aware (the computed field already has `self.perspective`). Concretely a
**2-bucket flip** (mixed deliberately stays net-first so the irreversible check/shot keeps the long
view):

- **immediate-first** → villager, healer
- **net-first** (current) → investigator, vigilante (mixed), wolf, SK

*Open micro-decision:* whether "mixed" (inv/vig) gets its own third ordering instead of collapsing to
net-first. Default = net-first 2-bucket.

---

## 7. Reranker fork — why the structured fields exist (fields IN scope; fusion DEFERRED)

The pulled-out numerics/enums serve a **dual purpose** and are kept regardless of reranker choice:

| | reasoning judge (flash-lite/gemini at rerank) | FT cross-encoder + deterministic fusion |
|---|---|---|
| ordinal (criticality) | handled in-model (reasons over text) | **can't** (architectural) → external `\|Δ\|` |
| direction (sign) | handled in-model | weak → external exact enum-match |
| fusion / weights | none | yes (fit once on dev set for the claim; defaults untuned for deploy) |
| pitch | simplest | **the USP**: `[FT-CE + deterministic ordinal/direction]` ≈ flash-lite, exact where it's approximate, far cheaper |

So the externalization was load-bearing for the *cheap-CE* path, not for a reasoning judge — a
thinking model does numbers + negation fine. It's only *required* if the FT-CE-beats-flash-lite claim
is published (the reranker-training portfolio asset; CE v4 already NDCG@5 0.882). **This build only
EXPOSES `criticality` ints + direction enums on the schema** (cheap, future-proofs both paths). The
deterministic-fusion layer + the system-vs-system benchmark `[CE+fusion]` vs `[flash-lite]` (recall
held constant) + weight-fitting = **fork-#3, deferred.**

### Recall is the one stage no reranker touches → an asymmetry
The reranker only ever sees the bi-encoder's top-k. At recall (no reasoning model, embedding smears):

- **Direction/sign** → a flipped sign pulls an *actively wrong* neighbor ⇒ **rephrase the sign into
  the embedded prose** (consensus_text written so "the room is turning *against* my read" embeds
  differently from "*confirms* my read") AND keep the enum for rerank.
- **Criticality/ordinal** → a wrong-criticality neighbor is merely *less applicable* (reranker
  downranks) ⇒ **accept recall-invisibility**, don't phrase counts into prose, just **gate + generous
  top-k** so the pool spans the criticality range the reranker reasons over.

(This amends the §1 "enum, NOT embedded" for the directional fields: enum for rerank **+** sign
phrased into content for recall.)

---

## 8. Old → new field mapping (concrete diffs)

`Agents/schemas/memory.py` `Observation` / `StrategyPoint` (model-visible/FROZEN) and
`Agents/schemas/output.py` `SituationEntry` (model-visible + live runtime):

| current (5 optional/required dims) | becomes |
|---|---|
| `situation` | `situation` — keep (spine) |
| `game_phase` | **deleted** → `players_alive` + `distance_to_parity` + `is_swing` (criticality, numeric, `embed=False`) |
| `information_landscape` | keep (spine) |
| `consensus_texture` | `consensus_text` (embed) + `my_position` (embed) + `consensus_direction`[enum, also phrased into text] (D) |
| `agent_exposure` | split → `heat_now` (universal) + `forward_exposure` (text) + `bullets_left`[int→reranker, vigilante] (F, profile-gated) |
| — | add `target_landscape` (E) |
| — | add `public_private_text` + `divergence_sign`[enum] (G, private-info roles) |

Single positional `_compose_situation(situation, info, game_phase, consensus, exposure)` → generic
set-field serializer (§3). `outcome` computed field → role-aware (§6).

---

## 9. Modules / prompts touched + downstream ripple

| file | change | sensitivity |
|---|---|---|
| `Agents/schemas/memory.py` | per-cell `SituationSchema` mixin DAG; `Observation`/`StrategyPoint` rebuilt on it; `_compose_situation` generic; `_compose_outcome` role-aware | **model-visible/FROZEN** |
| `Agents/schemas/output.py` | `SituationEntry` = per-cell `SituationSchema`; vote field-order flip (`updated_strategy` before `vote_target`) | **model-visible + live runtime** |
| `Agents/prompts/extraction.py` + `memory/extraction/inputs.py` | per-(role×phase) tail + horizon framing | model-visible |
| `Agents/memory/extraction/extraction_agent.py` | fan-out 6 → ~17, bind cell schema per call, merge | plumbing |
| `Agents/memory/enrichment/situation_agent.py` | live query emits the cell's `SituationSchema` | **live runtime** |
| `Agents/prompts/memory.py` | dimension-guidance registry (§5); composable per cell | model-visible + live |
| `Agents/prompts/day.py` | vote contract field-order flip | live runtime |

**Downstream (consequences, not edits):**
1. `_compose_situation` signature change → every caller updates (situation_agent, dedup
   prefilter/dedup_agent/store_ops/pipeline, `SituationEntry.composed`, auto_dedup_dataset_builder).
2. **Dedup thresholds** (0.93/0.81/0.96/0.935) were tuned on the old composed string → new dims shift
   the embedding → may under/over-fire. We're freezing (not re-tuning); the screen reads **retrieval**,
   not dedup quality. Note only.
3. **Reranker** input shifts, but rerank≈raw shipped → screen runs **raw obs-only top-k**, sidesteps it.
4. **Stores become legacy** → fresh re-extraction (the real cost) → new `v5_x` store; old `v5_0*`
   frozen as record.
5. **Leak checks** → F/G hold private info, but stores are per-role namespaced + the query feeds only
   the same agent → no cross-agent leak; still run a `check_*` pass on the new fields.
6. **Tests** → schema-shape + determine_winner/dedup-threshold guards may need updating.
7. **Screen harness** (`evaluation/src/experiments/decision_replay.py`) already reads `SituationEntry`;
   gains the criticality-conditioned-vs-flat arm.

---

## 10. Build order (gate the re-extraction bill behind a signal)

Per "validate cheap-first":

1. Stand up `BaseSituation` + `WithConsensus` + `WithHeat` + `WithTargetLandscape`; build
   **villager×day_vote only** (criticality numerics + consensus enrichment; no F/G).
2. Re-extract **only that cell**.
3. Run the screen: criticality-conditioned vs flat, town day_vote, **stratified by day** (falsifiable
   prediction = beats flat AT DAY-2). Paired, one sitting/pinned model, per-stratum read. ~3 draws ×
   ~50–60/stratum; reads **direction + causal-flip-rate, not significance** (effect is small, ~12–16%).
4. Only if the lever shows → roll the full DAG (F/G earn their keep on wolf×day_vote) + re-extract the
   rest.

Interview framing = the **ladder + method** (paired / stratified / drift-immune / judge-free; triage
not verdict; "$2 screen kills dead levers before the $18 powered arm"), NOT a big N quoted as proof.

---

## 11. Open items before implementation
1. ~~Edge cells~~ — **RESOLVED** (§2): night cells settled by the decision-input principle (no
   `WithConsensus`/`WithHeat` at night; `WithForwardExposure` iff observable act; `WithPublicPrivate`
   at night = investigator only).
2. ~~`reversibility` form~~ — **RESOLVED**: replaced by `bullets_left`[int] on the reranker numeric
   path (same family as criticality); the near-constant "irreversible" binary is dropped.
3. **"mixed" outcome order** (§6) — net-first 2-bucket (default) vs its own third ordering. STILL OPEN.
4. **Fork-#3 decision (deferred):** pursue the FT-CE-fusion USP benchmark, or expose-fields-and-freeze
   after the screen.

## 12. Pointers
- Design narrative: `evidence/memory_system/effectiveness/decision_replay/experiment_log.md`
  (cheap-lever ladder, the dimension matrix, embedding-limits + reranker-fork discussion).
- Phase B plan: `evidence/phase_b/plan_review.md`.
- Screen layer report: `evidence/memory_system/effectiveness/decision_replay/report_screening_layer.md`.
- Roadmap memory: `project-ship-roadmap` (fork + framing correction + screen-test design).
