# v8 memory: the ten-seat cast — launch scope, seeding and batch updates

Written 2026-10-10; revised 2026-10-11 after the owner discussion and code review. Part of **v8**
(everything from the ten-seat iteration on; folder `evidence/memory_system/v8/`, see `README.md`).
How the rulings were reached is in `decisions.md`; what was run is in `experiment_log.md`.

**Status:** planning document, not a record of implemented changes. **The final plan is §9**,
which overrides §2 and §8 where they differ. In short:
- town memory is retrieved at night only; town day is extracted for owner review;
- the town information roles still choose when to share (no forced disclosure);
- evil and neutral roles get day/night memory.

D2 and D3 are ruled in §9.1. The later rulings of 2026-10-11 (extraction model, the day split,
counterfactual handling, the credit port) are §9.5 and §9.6.

Updating this document does not authorize paid runs or claim that the new pipeline has been
validated.

The earlier all-role/all-phase seeding plan is superseded by this scope. Resolve the write-affecting
choices before bulk extraction. First prove one complete extraction → synthesis → retrieval → replay
path; do not leave discovering an unusable store until after seeding.

## 0. Purpose and evidence boundary

- The ten-seat game draws from twelve roles. The memory cell registries still cover the old cast;
  new roles can silently extract nothing. Start with the role sheet
  (`evidence/game_play_enhancement/role_sheet.md`) and census §5
  (`evidence/game_play_enhancement/phase3_wiring_census.md`), then check current code: the census
  contains historical paths and assumptions.
- This effort makes the current demo's memory mechanism usable and inspectable. It is **not a new
  effectiveness experiment**. The research closure is
  `evidence/credit/blindspot_fix/experiment_log.md` §⑥: no certified current-epoch benefit.
  Historical benefits and failures retain their original game/model/prompt scope.
- A narrower decision space is easier to maintain and test, not evidence of stronger play.
  Fixed policies are product constraints, not established optimal strategies.
- Seed a fresh store. Do not merge nine-seat stores into the new ruleset. Preserve the old stores,
  code and experiment records for historical reproducibility.
- The previous plan recorded about $120 credit expiring around 2026-10-16. This was an owner-provided
  estimate, not a verified current balance. Credit is a spending ceiling, not a target.

## 1. What exists now, and what is separate

### During a served game

`server/game/run_config.py` enables strategy-point retrieval for memory-on games, disables store
dumping, and enables post-game extraction for display. The retrieval path
(`Agents/memory/retrieval/pipeline.py`) generates a situation, searches role/phase namespaces,
applies configured filters/reranking/caps, and supplies advice to the actor. The current policy skips
day 1. Not every optional retrieval feature is enabled in a served game.

`Agents/turn/pipeline.py` emits the retrieved lessons and this decision's verdicts for the replay.
A "follow" verdict is primarily the actor's self-report, not proof of causal contribution.

### After a game

`extract_postgame_per_cell` defaults to **observations only**. Served-game observations are displayed
but not admitted to the shared library. Eligible store-building runs can deduplicate and persist
them. Existing extraction/credit guards exclude human-involved games from teaching the store;
"sample completed games" does not override that policy.

Observations are accounts of past events. Strategy points are reusable prescriptions synthesized
from observations. Since served games retrieve strategy points only, **observation seeding alone
does not produce a usable demo library**.

### Between batches

Basic path: eligible records → extraction → observation deduplication/clustering → strategy synthesis
→ strategy deduplication → review → versioned snapshot.

The fuller `Agents/memory/consolidation/tick.py` path additionally computes credit/conversion
signals, ages observations, uses track records in synthesis and prunes/evicts strategies. The inspected
server code does not schedule this command automatically. A timer or completed-game threshold is
separate operational wiring, not evidence that the batch process is already running.

**Tell book:** implemented, not hypothetical. `Agents/memory/tell_book.py` is wired into day/night
prompts, with build/fold code under `evaluation/src/loop/`. It renders nothing without
`WW_TELL_BOOK`; its environment switch is independent of the ordinary memory toggle. Runtime
activation was not verified. Latest discussion: leave it outside the current demo scope; describe it
as an experimental channel deferred for this deployment, not "unimplemented".

## 2. Latest working scope and open decisions

### D1. Narrow the memory decision space

Owner proposal: town night-only; evil and neutral day/night. The preferred simplification discussed
was **no town day extraction/retrieval of lessons**, rather than retaining day advice but removing
the credit mechanism intended to challenge bad advice.

| Group | Proposed lesson scope | Limits |
|---|---|---|
| Town | Night actions only | Day discussion/vote still run normally, without retrieved town-day advice. |
| Evil (wolves and lone killers) | Day discussion, day vote, night actions | Cover, counterclaims and deception remain useful targets, but their credit is still difficult to attribute. |
| Neutral | Owner proposed day/night | Define each role's useful decisions and objective separately; do not inherit evil credit rules by default. |

Retain full daytime evidence as context for extracting **night** lessons. "No town day observations"
means no lessons intended for town day decisions, not deleting the day transcript. Enforce the policy
at extraction, synthesis and retrieval boundaries; a per-role memory boolean alone cannot express it.

### D2. Fixed disclosure policy for town information roles

The owner proposed assuming prompt disclosure instead of learning its timing. Candidate wording:
"At the next available discussion opportunity, accurately report newly received findings and their
limitations." Exact wording remains to be settled before seeding, since it changes play.

- This is a bounded policy choice, not a finding that immediate disclosure is always optimal.
- Apply it to information roles, not every town action: disclosing intended protection is a different
  decision. Avoid repeated announcements when nothing new was learned.
- Investigator results are Suspicious / Not suspicious; the latter is not confirmed town.
- An unconcealed town death publishes earlier night records. A concealed death publishes none, and
  no result is received for the night the actor dies. Timing still matters before disclosure.
- Wills reduce one information-loss problem but do not automatically validate the old conversion
  metric. Do not reward disclosure advice for an automatic engine disclosure.

### D3. Shared cell schemas, restricted to supported role/phase pairs

Recommendation remains shared day/night schemas with validated role/phase routing and role-specific
rules, instead of twelve copies of near-identical schemas. Extract only roles actually present and
supported phases; allow no useful observation when no relevant decision occurred.

Do not force every new ability into the old fields. Account for limited uses, borrowed actions and
neutral objectives. Preserve compatibility needed by historical experiments; old schemas are not
disposable solely because new games no longer deal those roles.

### D4. Retrieval frequency first; retrieval redesign optional

Owner's cost goal: stop generating a fresh situation and retrieving on every discussion call.
Specify the refresh interval precisely: per round versus opening-round-for-the-day are different
policies. Voting and night decisions need separate treatment. Under D1 town day does not retrieve.

Cache selected lessons, **not** the entire actor payload or its verdicts. Scope any cache to the game,
actor, phase, interval and store version, plus the chosen invalidation conditions. Do not share
private context merely because two actors have the same role. Discussion can change materially after
a claim; define whether that invalidates the cache. Measure savings before adding more machinery.

Metadata-only retrieval remains an option, not an approved/equivalent replacement:

- `dedup_gate.gate_key` packages (is_swing, alive bucket, consensus_direction); it does not derive
  all three from the census. Consensus direction is currently a model interpretation.
- `board_clocks.py` assumes revealed deaths permit exact subtraction. Concealed deaths break that
  assumption; unknown criticality must not be filled from hidden engine truth.
- Similar average embedding scores for applicable/inapplicable items do not prove semantic candidate
  selection has no value. Check representative saved situations before removing it.
- Fresh memory-off seeding supplies no follow-based track record. Existing proven-first ordering is
  not a complete ranking policy for an uncredited store.
- Conservative first pass: retain situation/semantic retrieval, reduce frequency, and use only
  actor-knowable deterministic filters. If local metadata lookup later replaces it, reconsider
  whether interval caching is still worth its complexity.

### D5. How much authority should credit have?

Unresolved. Do not silently treat the complete credit system as either required or removed.

| Option | How bad advice is challenged | Tradeoff |
|---|---|---|
| Reviewed batch synthesis without credit | Owner reviews candidate updates and source evidence | Less scoring machinery; ongoing manual responsibility |
| Credit as a diagnostic | Report proposed removals/revisions, review before publishing | Retains feedback without automatically trusting attribution |
| Full credit-guided updates | Credit influences synthesis and pruning | Requires updated role rules, adequate data and validation of selection behaviour |

The historical "withhold findings to survive" failure is why credit exists. Deduplication cannot
remove bad reasoning just because it is bad; more observations can reinforce it. Removing credit
must mean replacing its quality-control responsibility with review, not assuming synthesis will
self-correct. Town night-only scope removes that particular day-advice pathway, not every possible
bad strategy.

## 3. Extraction and synthesis: what to preserve, what to test

The current `Agents/prompts/extraction/cell.py` says:
"if the lesson is about something that happened TO the {role}, reframe it as what the {role} did
that led there." Review identified a **possible** pressure toward unsupported causal attribution.
This is not a demonstrated extraction defect; no comparative quality test was run in this discussion.

Latest proposed evidence rule (not yet applied to prompts):

> Include only observations with a supported, strategically relevant takeaway. When a candidate
> lesson depends on a causal connection the record does not establish, omit that candidate. Sequence
> alone is insufficient evidence of causation. Fewer observations, including none, are acceptable.

Remove/qualify the earlier causal reframing instruction rather than relying on a later instruction
to negate it. Preserve supported causal explanations and useful descriptive evidence.

Examples:
- "Revealed, then died" does not establish that disclosure caused targeting or was bad for town.
- Wolves explicitly discussing the reveal as their reason supports the targeting explanation,
  but still does not establish that withholding would improve town outcomes.
- A behaviour exhibited by a wolf in one game is an observation, not an established general tell.
  Behavioural evidence may support night-targeting lessons; assess counterexamples and distinct-game
  support before generalizing it into a role-identification rule.

Proposed robustness changes, to implement proportionately:
- Retain source game/event references as audit metadata; do not expose old player IDs or hidden
  post-game truth as current-game evidence.
- Separate what the actor knew, chose and observed from the extractor's interpretation.
- Preserve supporting and conflicting examples for synthesis; dedup is not independent corroboration.
- Prefer conditional advice, record the rules version, and permit synthesis to add nothing.
- Use engine records for facts, AI for bounded interpretation, and review uncertain conclusions.

Validation need not be a new game campaign. First inspect existing outputs; optionally compare old
and new extraction on a few saved role/phase cells. Include a supported causal link, ambiguous
sequence and externally caused outcome. Check both fewer unsupported claims and preservation of
useful lessons. Without such a comparison, label the wording change unmeasured, not improved.

## 4. Credit, sparsity and evaluation boundaries

### What current credit computes

The main path joins a reported "follow" to a predefined decision/event grade (+1, 0, -1), averages
scored uses, subtracts the corresponding memory-off baseline, then shrinks by n/(n+5).
It does not simply reward a game win. Multiple followed strategies can receive the same grade.

Current production defaults (`Agents/memory/consolidation/config.py`):
- Follow-based pruning: at least 8 scored uses and adjusted credit below -0.15.
- Synthesis track record: at least 5 scored uses.
- Positive protection: positive adjusted credit with at least 2 scored uses.
- Never-followed eviction: at least 8 presentations, with overrides dominating or tying
  not-relevant verdicts and at least one override.
- Conversion channel: separate retrieval-based attribution, at least 5 observations before its
  negative score can prune; subject to positive protection.
- Retrieval exploration can surface an unproven candidate, but guarantees neither discovery of
  every stored strategy nor a follow. Synthesis normally limits growth at 12 unproven strategies
  per role/phase, with replenishment exceptions.

These are code defaults, not newly validated thresholds. Credit is recomputed over the supplied
window; counts do not necessarily accumulate forever. Scored uses within one game are not independent
games. Record both counts. Sparse evidence remains sparse despite shrinkage.

### Baseline and arms-race correction

Production `compute_base_rates` pools memory-off decisions by role/phase; it does **not** require a
same-seed counterpart for every memory-on game. Same-seed pairing belongs to the selected experiment
design, not a mandatory one-for-one production cost.

All-on versus all-off can evaluate the whole-game memory configuration if appropriately controlled.
It does not isolate an individual strategy's contribution: better opponents can depress town scores,
and better teammates can raise them. More baseline data reduces noise, not that attribution problem.
All-on games remain legitimate source material for synthesis; an arms race does not make them useless.

Treat credit as an association under a recorded configuration until validated for its intended use.
The desired future test of credit is credit-guided library updates versus an appropriate alternative,
not merely memory-on versus memory-off. That test is not a launch prerequisite.

**Migration blocker for automatic credit:** old threat-role lists and action grading do not cover
the new game. In particular, the Investigator reads wolves as Suspicious and an effective attacking
Necromancer as Suspicious, while the Serial Killer reads Not suspicious. "Checked a true threat" is
not equivalent to receiving actionable threat evidence. Missing baseline/unsupported channels should
be explicitly unscored, not silently treated as baseline zero or a default town rule.

### Investigator diagnostics: separate actor decisions from team outcomes

| Stage | Evidence / subject | Attribution limit |
|---|---|---|
| Information obtained | Attempt, completion, actual delivered result, block/death status | A useful negative result is not automatically a bad check |
| Information communicated | Investigator's words and available speaking opportunities | Accuracy/timing can be assessed; persuasion is not established by a later elimination |
| Information published automatically | Engine will disclosure and its contents | Not an investigator communication action |
| Information acted upon | Subsequent town discussion, votes, elimination | Team response, not solely investigator performance |

These are diagnostic stages, not three automatic investigator credit scores. With town day memory
excluded, retain relevant diagnostics without rebuilding an elaborate day-credit system. Deceiver
and neutral channels still require separate objectives and explicit limits.

## 5. Bounded implementation and seeding order

1. Set D1–D5's launch choices; record what is deferred. A documentation update is not paid-run approval.
2. Extend the selected role/phase cells and end-to-end scope gating. Keep full transcripts as context.
   Confirm extraction can run with retrieval off; current role filtering/fallback behaviour deserves
   an explicit check rather than relying on an old batch command.
3. Set disclosure wording and extraction prompt; record model, thinking setting, rules and prompt
   versions. Review one complete extraction → dedup → synthesis → load → retrieval → replay example
   before bulk spending. Cover all four lineups across a small pilot, not one game alone.
4. Inspect reusable ten-seat captures first. Verify they contain extraction inputs (private records,
   pack discussion, strategy notes as required), and retain their original rule/prompt provenance.
5. Seed with memory retrieval OFF, extraction ON and store output ON. Freeze the extraction settings
   for a batch. Generate only enough content for useful role/phase coverage; count distinct games.
6. Explicitly synthesize strategy points and deduplicate/review them. Reserve budget for this step:
   per-game extraction defaults to observations only.
7. Publish `memory_stores/ten_seat_v1` with a manifest and recoverable checkpoint. Subsequent updates
   produce new reviewed snapshots; use one identified library version per game.
8. Implement the retrieval cadence and validate replay fidelity and information boundaries. Ship only
   selected, verified credit channels if D5 calls for them. No need to port the entire research loop.

Seeding footguns retained from `evidence/memory_system/effectiveness/v5_seeding_plan.md`:
- DISTINCT output JSONL per batch; output appends.
- Dumping writes the in-process store. Load accumulated state on later batches and checkpoint first.
- Do not race shared store writes. Use sequential games or separate directories with a deliberate merge.
- Start with at most two concurrent games based on prior quota failures; concurrency of extraction
  calls is a separate load control.
- Count eligible appearances/opportunities per role/phase; a game seats ten, not all twelve roles.

Budget: the earlier $0.72 play cost and $1.50–$2 total/game were historical measurements/estimates,
not a priced guarantee for this build. Measure the pilot, including extraction, embedding, dedup,
synthesis, retries and review-related calls. At N games, always-present roles appear N times and each
drawn alternative roughly N/2 times, before survival/action eligibility. No fixed 60–80-game target.
Credit/pruning are local computations; extra baseline games, if needed, create model spend.
Running identical work concurrently does not inherently increase token cost, though retries/load can.

Focused acceptance checks:
- Selected role/phase coverage; absent roles and town day cells cannot leak back into the store/prompt.
- Exact received results and public/hidden information boundaries, including concealment and death.
- Cache isolation/refresh and per-decision verdict fidelity.
- Store reload/checkpoint integrity and source/snapshot provenance.
- Credit-disabled mode really disables dependent behaviour: `credit=False` alone retains counters
  and does not turn off pruning, eviction, or credit-informed synthesis.
- Prompt quality checks distinguish supported causation from coincidence and preserve useful lessons.

## 6. Frontend coordination and presentation

- The previous frontend pass is committed. **Tell the frontend session before any wire change** to
  `server/schemas/events.py`, `server/game/translate.py`, or regenerated
  `frontend/src/types/contracts/`; coordinate regeneration and typechecking.
- Reducing lookup frequency does not automatically mean fewer `memory_consulted` events:
  the event also carries this decision's judgments of the lessons. Preserve that meaning on cache hits.
- Show extracted observations as candidate material, not automatically accepted strategies.
  Explain that the shared library is updated between batches, not immediately after this game.
- A recorded or static real example can show source observations → synthesized strategy → retrieval
  in a later game. No separate interactive pipeline demo is required for launch.
- Keep tell-book and current-effectiveness claims out of the deployed feature description unless
  their actual status supports them. Preserve historical results with their original scope.
- Presentation option discussed: report the historical memory experiments while deploying the newer
  game as a beta/research prototype. State the tested ruleset, seat/role configuration, model, prompt
  and store versions beside the results; verify these from the run manifests (the older stores here
  are documented as nine seats/six role types, not the current ten-seat/twelve-role pool).
  The site should separately state supported memory phases, whether batch updates are active, and
  that historical results do not validate this build. Keep unsupported paths unavailable rather than
  relying on a blanket beta label. This is a presentation option, not a newly approved launch state.

## 7. Artifacts and next handover

This file is the current plan. Historical research reports are unchanged.
Record actual rulings, prompt/model versions, pilot reads, costs, role/phase coverage, batch counts,
synthesis output and acceptance checks in `experiment_log.md`, `prompt_versions/`, `data/` and
the eventual folder `README.md`. Do not create a benefit claim from seeding or mechanism checks.

No implementation, prompt, scoring or paid experiment changes were made by the 2026-10-11
documentation update.

## 8. Rulings of 2026-10-11 (second discussion): evaluation, metrics, prompts, retrieval gate

Each item is marked **ruled** (the owner decided), **proposed** (Claude's recommendation, not yet
ruled) or **parked** (to discuss later). The owner plans to allow memory-on games after this seeding,
so the evaluation work below is needed for launch, not only for research.

### 8.1 What a game must record before seeding (ruled)

Metrics are a free recompute over saved games, so the derived scores can be written after seeding.
What a seeding game does not save is lost for that game. Before the first paid game:

- **The night's resolved outcome.** `NightResolutionMetric` (`Agents/schemas/metrics.py`) keeps
  the choices, the deaths and the pack's target. The night-resolution node already computes the rest
  (`NightOutcome`: blocked, blocks without effect, concealed, Suspicious reads, settled bets, verdicts,
  visits) and discards it. Copy it into the record. The old per-role fields (`investigator_target`
  and the rest) are nine-seat only and are always empty now. This is why the conversion channel finds
  nothing: it still reads `investigator_target`, while the check sits in `choices`.
- **Every actor's private night record** (`night_actions` in game state, with its result word) is
  not saved in the batch game record (`scripts/run_batch.py`). Save it.
- **The kind of each night decision on the eval case.** `NightAction(role, target)` cannot tell a
  carrier Chanteuse's kill from its block, and a conceal (target None) looks like doing nothing.
  Add the kind. The `night_action` phase tag is shared by chat, kill and skill.
- Claims are already saved: each day message carries its `claim` field.

### 8.2 Threat sets and fixed roles (ruled)

- The `wolf` role is retired. The pack is the Chanteuse and the Illusionist; the lone killer is the
  Serial Killer or the Necromancer. Town's threats are the pack and the lone killer. Take the sides
  from the role registry, not from literal role names (`decision_scoring.THREAT_ROLES`,
  `credit_rules`, `credit.DECEIVER_ROLES`, `conversion.py`, `compute_metrics.py` still hold the
  nine-seat sets).
- An Investigator's find is a delivered "Suspicious". A check on the Serial Killer is not a find.
- Fixed roles keep their nine-seat grades, ported to the side-based sets. In particular:
  - a Vigilante shot on any evil role (the Necromancer from night 2) is good;
  - the Healer's attackers come from every attack, not only the pack's;
  - a declined use ("no check", holding fire) is neutral.

### 8.3 New roles (ruled unless marked)

| Role | What to grade or track |
|---|---|
| Chanteuse | Tiered blocks. **Critical:** the blocked action would have saved the pack's victim, struck the carrier with a sigil, shot a wolf, read a wolf Suspicious, or shown a wolf's visit to a Sentinel or Trailseer. **Real:** any other town action cancelled. **Wasted or negative:** blocked a teammate or a target with no action. "Would have hurt the pack" counts fellow wolves only, not all evil, because the lone killer is the wolves' rival (ruled 2026-10-11, §9.5). |
| Illusionist | Track two things: the conceal hid a town role that had a record to read out, and the conceal landed on a town role. Claim space (a wolf later claiming the hidden role) is **left out**: whether the claim is made and survives is day play, not attributable to the night action. |
| Necromancer | Nights survived and win/loss as the proxies. Grading by what the borrowed body's action achieved is **deferred**: rewarding kills alone would push it to kill every night. Both proxies are per game, so neither can credit a single lesson. |
| Speculator | The pick is graded at game end: the picked side won, lost, or it died unpicked. Pick day is tracked as a descriptive number. Day votes after the pick are graded as a member of the picked side. Day votes before the pick are unscored. |
| Fortune Teller | Points per bet. Day votes unscored (lynches never score for it). |
| Sentinel, Trailseer, Sigilist | Results that named an evil visitor (Sentinel, Trailseer); hits per sigil spent (Sigilist). Ruled 2026-10-11, §9.5. |

Every proxy starts as unvalidated. The nine-seat validations do not carry over. The seeding games,
played with memory off, are the data for re-validating them.

- **D2 disclosure needs a judge** (ruled). Whether a finding was accurately reported at the next
  opportunity is a question about meaning; a string screen cannot answer it.
- **Night namespace** (ruled): one `night_action` namespace per role, as every role has now. Pack
  chat, kill and skill share it. The Chanteuse and the Illusionist have separate extraction cells.
- **D5 credit authority** stays open. Proposed: credit as a diagnostic for the first library. Credit
  needs follow verdicts from AI-only memory-on games, which seeding (memory off) does not produce.

### 8.4 Which eval code the ten-seat game uses (ruled)

- **Frozen:** the nine-seat research harness (`evaluation/src/loop/`, `studies/`, `audits/`,
  `instrument_validation/`, `checkpoint_replay`, `read_ledger`). Production imports nothing from
  `loop/`; its credit, synthesis and pruning moved to `Agents/memory/consolidation/` on 2026-07-21.
  It returns only if the plan §4 test (credit-guided updates against an alternative) is ever run.
- **Ported:**
  - `compute_metrics.py` and `analyze_batch.py`;
  - `Agents/memory/consolidation/` (credit rules, decision scoring, conversion);
  - `eval-replay`: its situation rebuild (`evaluation/src/replay/situation_summary.py`) still uses
    the four-role legacy prompts, not the production cell path;
  - `eval-retrieval`: served games use `top_k=5`; the judge prompt has a healer example.
- `ComputedGameMetrics` is pushed to Langfuse at game end (`Agents/main.py`) and saved in the batch
  record. On ten-seat games, several metrics read 0.0 when the event happened (`sk_kill_rate`,
  `vigilante_wolf_kills_rate` and others). Until ported, they must return None (not pushed). The
  "validated" tier drops to diagnostic until re-validated on ten-seat games.

### 8.5 Prompts: settle before seeding

- **Extraction prompt** (`Agents/prompts/extraction/cell.py`; the shared epistemic rule in
  `Agents/prompts/standards.py`):
  - concealment exception and the GM-read record (the rule now says "an elimination reveals the
    eliminated player's role");
  - naming examples on ten-seat roles.
  The extractor already receives the ten-seat rules, the pack chat and every night record.
- **Parked, one experiment:** the causal reframing line (plan §3), and the observation and
  strategy-point counts. The counts are "6-12" observations, "3-8" strategy points and synthesis
  "1-3". Forced padding goes (ruled). The owner worries a zero floor is too low, so test a hard
  floor, soft guidance ("usually a few; fewer or none when no decision mattered") and zero on a few
  saved ten-seat cells. Look at how often a cell comes back empty, and whether the empty ones had a
  lesson worth keeping (owner read).
  - The same discussion covers the **judgment fields of an observation**:
    - `impact_on_final_game_outcome`: "judged from the END of the game … name the causal chain";
    - `net_verdict`: positive, negative, mixed or unclear;
    - the horizon text in `cell_prompt.py`.

    Observations were meant to record what happened. These three are the extractor's judgment, and
    they drive synthesis directly: each observation reaches synthesis tagged with its `net_verdict`,
    and synthesis is told to weight by the outcome spread, turning a mostly backfiring move into its
    corrective. Of the outcome fields, `immediate_response` (what happened the same or next turn)
    is the nearest to fact.
- **Driver lines** for the eight new roles (`Agents/prompts/cell_prompt.py`). The Investigator's
  line also needs updating now that checks are limited. Drivers reach both the post-game
  extraction and the live situation query (`compose_cell_guidance` builds both, so a live situation
  matches the way stored lessons describe situations), so they are frozen before seeding.
- **Synthesis gets the ten-seat rules block** (ruled). `CELL_SP_SYNTHESIS_PROMPT` receives only the
  cluster's observations and the field list. With no rules, it generalizes from the model's idea of
  classic Werewolf (every death reveals a role). Pass it the same `rules_block(lineup)` that
  extraction gets.
- **D2 disclosure wording** in the Investigator, Sentinel and Trailseer game prompts: a new prompt
  epoch.
- **Read side, before the gate's pilot:** situation-summary prompts for the new roles
  (`Agents/prompts/memory/situation_summary.py`; every new role falls back to the villager's).
- **Not a prompt, but feeds the prompts:** `board_clocks.py` parity and swing after a conceal.

### 8.6 Defects found in review (to fix, no ruling needed)

- **Replay drops later day turns.** Day turns carry no round (`Agents/turn/pipeline.py`, default
  0). The translator passes one `memory_consulted` and one `player_reads` per (player, day, round,
  phase) (`server/game/translate.py`). So only the first discussion turn of each day reaches the
  wire. Play is unaffected. Wire-adjacent: tell the frontend session.
- **The server takes `memory: true`.** The UI switch is disabled, but `.env.production` still points
  `WW_MEMORY_STORE_DIR` at the nine-seat `demo_gen1` store. Refuse memory-on until a ten-seat store
  is configured.

### 8.7 Deployment gate and demo split (proposed)

**The gate** is the go/no-go before allowing memory-on games. Its pass marks are set before running.
It asks whether retrieval fetches the right lessons safely and cheaply, not whether memory improves
play. Seeding runs with retrieval off, so no ten-seat situations exist yet. The gate needs a small
AI-only memory-on pilot after the store is built: about 4 games, one per lineup.

| Check | How |
|---|---|
| Coverage | Every supported role and phase has strategy points; town day, absent roles and the old `wolf` namespace are empty |
| Relevance | `eval-retrieval` on the pilot's situations, plus an owner read of a sample (judge ceiling about 80%) |
| Information boundary | The situation prompt is leak-checked (never logged today); no concealed role stated as fact; no old player IDs or game details in strategy points |
| Replay fidelity | One `memory_consulted` per decision, after the round fix; verdicts stay per decision when a cached lookup is reused |
| Cost and latency | Situation calls per game before and after the D4 cadence change; p50/p95 per decision; dollars per game, memory on vs off |
| Verdict mix | Follow, override and not-relevant rates, descriptive only |

**Demo:**
- the toggle on the ten-seat store;
- the Lessons tab with verdicts;
- the Findings tab labelled as candidate material;
- one static example (observations → strategy → retrieved in a later game);
- a ten-seat replay replacing landing card 1, which is hard-coded to nine-seat game `9369a5c1`.

No credit numbers, no effectiveness claims, no tell book.

**Write-up only:**
- the research arc, at original scope: the June A/B and its "+17pp p=0.013" correction, the negative
  v7 result, the credit-rewards-concealment diagnosis, the zero-reasoning scope;
- the proxy validation history;
- the credit design;
- the gate's results;
- the reasoning behind D1 and D2.

Stale front doors to stamp or update: the root `README.md` ("Static memory helps") and
`evidence/v7_final/report.md` ("compounding question OPEN").

## 9. Final plan (2026-10-11, end of the second discussion)

Where this section differs from §2 or §8, this section wins. **Owner's constraint:** no extra
judge, no new model calls, no new pipeline stage. Every change below is a text edit or a small code
change. Anything larger goes to the report's limitations and future work (§9.4), and is not built.

### 9.1 Scope changes (ruled)

- **D1, revised.** Town day is **extracted and synthesized but never retrieved in play**.
  - Extraction covers town day and night. Retrieval covers town night, plus evil and neutral day
    and night.
  - Retrieval needs a per-phase switch: today `memory_config` is per role only.
  - The gate checks that town day lessons are never retrieved, not that the namespace is empty.
- **Town day advice is material for review (option A).** The owner reads the synthesized town day
  strategies. Chosen lines become fixed role-prompt text, optionally with a condition the prompt
  states itself ("if you hold a Suspicious result…"). This is the same mechanism as D2; each change
  is a prompt epoch. Code that selects advice by game state is future work.
- Town day lessons are never followed in play, so they never earn credit. Owner review is their
  only quality check.
- **No new judge.** The D2 disclosure metric (§8.3) moves to future work.
- **D2: no forced disclosure.** The town information roles keep "your call" in their discussion
  prompts, so the prompts are unchanged and there is no new epoch.
  - In the 28 saved ten-seat balance games under those prompts, the role reported the next day
    almost every time: Investigator after Suspicious 13 of 13; after Not suspicious 25 of 28;
    Sentinel 42 of 42 claimed or named the target; Trailseer 44 of 44. These are rough counts
    (the `claim` field, or a plain text match on the target).
  - D2 existed to stop memory teaching withholding. Town day lessons no longer reach play, so that
    pathway is closed.
  - If the option A review shows a disclosure problem, a prompt line can be added then.
- **D3: map the new roles onto the existing cell shapes**, with no per-role fields:

  | New role | Reuses the shape of |
  |---|---|
  | Sentinel, Trailseer | Investigator day; the shared town-power night cell |
  | Sigilist | Vigilante |
  | Chanteuse, Illusionist | The old wolf cells |
  | Necromancer | Serial Killer |
  | Speculator, Fortune Teller | Built from existing field groups |

  The only new piece is a small "uses left" field group for the limited-use roles. It sits beside
  the Vigilante's `bullets_left`, which is not renamed, so old stores still load.

  Choices without a field of their own stay in the free text (`situation`, `approach`): the
  Necromancer's body, the Fortune Teller's bet, the Speculator's pick.

### 9.2 Before seeding

1. **Extraction prompt and observation fields** (text edits only):
   - the concealment rule in the shared epistemic rule (`Agents/prompts/standards.py`), with the
     GM-read record of a revealed town player; naming examples on ten-seat roles;
   - the causal reframing line is replaced by the §3 evidence rule: keep only takeaways the record
     supports; a sequence is not a cause; fewer observations, or none, are fine;
   - `approach` drops "or failed to do" (it invites a move that was not played);
   - `impact_on_final_game_outcome` states the end-of-game effect only when something in the game
     supports the link, and says what in the same sentence; otherwise "unclear". No new field;
   - the "net" horizon text (`cell_prompt.py`) drops "name the causal chain", same rule;
   - "6-12" observations becomes soft guidance ("usually a few; fewer or none when no decision
     mattered").
2. **Synthesis prompt** (`CELL_SP_SYNTHESIS_PROMPT`, `strategy_synthesis.py`):
   - the ten-seat rules block;
   - never infer that the opposite of an unsuccessful move is good; emit a corrective only when the
     evidence or the game's mechanics support it, otherwise nothing;
   - an "unclear" verdict says nothing about whether the move helped (more observations will be
     unclear after change 1);
   - "Emit 1-3" becomes "0-3";
   - `_format_cluster` shows the immediate and end-of-game outcomes on separate lines (both are
     already stored separately).
3. **Driver lines** for every supported cell, the eight new roles included, town day back in
   (§9.1).
   - Town night cells use the immediate horizon.
4. **Code:**
   - cells for the new roles, mapped per D3 (§9.1), plus the "uses left" field group;
   - the per-phase retrieval switch;
   - `board_clocks.py` parity and swing after a concealed death.

### 9.3 Then, in order

5. **Pilot** (done 2026-10-11, `experiment_log.md`): one game per lineup, extraction and an offline
   synthesis. It led to §9.5: a cheaper extraction model, the day split, the death-night fix.
6. **Port the metrics** (done 2026-10-11, `e5763cd1`; §8.2, §8.3; no model cost).
7. **Bulk seeding** (done 2026-10-11, `experiment_log.md`): 12 games, 553 observations, every
   retrieved cell from 5–12 games; no top-up needed.
8. **Synthesize, review, publish** `ten_seat_v1`. The owner's review is v1's quality check (D5:
   credit as a diagnostic). Town day strategies are read for option A.
   - Synthesized 2026-10-11 on flash-lite (150 points, 9% wrong rule), then 2026-10-12 on Sonnet
     5.5 with a revised prompt (176 points, 11% wrong rule, `experiment_log.md`). Published as
     `memory_stores/ten_seat_v1`: the Sonnet points without the 19 the rule screen flagged (157).
     Open: the owner's read of the rest; the de-halo pass turned 26% of verdicts, a few over-corrected.
9. **Retrieval cadence (D4)** and the situation-summary prompts for the new roles.
10. **The gate** (§8.7), with existing tools only: coverage, the existing `eval-retrieval` judge
    updated for the ten-seat cast, leak checks, cost. Then deploy, with `WW_MEMORY_ENABLED` set and
    `WW_MEMORY_STORE_DIR` pointing at `ten_seat_v1`.
11. **After launch:** port the credit grades as a diagnostic.

### 9.4 Limitations and future work (report only, not built)

- An evidence-verification judge, and audit references to transcript events (the de-halo pass
  checks verdicts only, not facts).
- Extraction on Claude (Sonnet 5.5 wrote the least halo; about $0.85 a game with working caching):
  it would need its own path, with the output schema placed after the cached prefix.
- Counterfactual testing: branching a saved game at a decision, matching similar games.
- Counting distinct source games in code. A stored item keeps one `game_id` (its first source
  game); the duplicates merged into it keep only a count, not their games.
- Separate immediate and net verdict fields in the schema.
- Per-role cell fields (e.g. the Necromancer's available bodies, the Fortune Teller's points).
- Batch extraction (Vertex batch, 50% off): worth it once the store is updated regularly. About
  250–350 lines. On Vertex the cache and batch discounts do not stack. Whether batch can use an explicit
  cache is unverified (experiment_log.md, 2026-10-11).
- Full credit-guided library updates.
- Code-selected town day advice (option B), metadata-only retrieval, the tell book.
- Necromancer grading by what the borrowed body achieved; Illusionist claim space; neutral day votes
  before the pick; the D2 disclosure judge.
- Fixed policies (D1, D2, option A lines) are product choices, not proven optimal play.

### 9.5 Rulings and changes later on 2026-10-11 (after the pilot)

Records: `experiment_log.md` (pilot, model comparison, day split) and `decisions.md` (the discussion).

- **Extraction model: gemini-3.8-flash** at its default thinking (medium); backup gemini-2.5-pro
  (ruled).
  - Re-extracting two pilot games: about $0.34 a game against 2.5-pro's $1.17, no player IDs, as
    well grounded.
  - The price is a promotion ($0.75/$3.75 per 1M) to 2026-12-31, then double.
  - Vertex prices are not confirmed.
- **The day is two extraction calls, discussion and vote** (ruled). One shared day call filed nearly
  every day observation under the vote. Re-extracting one game: 0 → 16 discussion lessons, for
  about $0.18 more a game.
- **The extractor sees a role's last night, marked "never told"** (defect fixed). Game state drops
  a dying actor's record; extraction now reads each night's full record.
- **Synthesis provenance** for the portfolio's worked example (ruled):
  - each strategy point keeps `source_observations`;
  - each synthesis call's input and output goes to `synthesis_log.jsonl`;
  - the tick's snapshot keeps the log;
  - a dedup survivor keeps only its own list, which is enough for a showcase.
- **Counterfactual conclusions: option A** (ruled). The extraction wording stays as §9.2 left it.
  About 6 of 66 observations in the pilot read still drew counterfactual or hindsight conclusions.
  The guards are synthesis's "no opposite of a failure" rule and the owner's review of strategy
  points. Stronger wording (option B) risked dropping supported, mechanically checkable lessons.
- **A de-halo pass after extraction** (ruled, `395cfa7f`; `experiment_log.md`, the smoke game):
  - Claude Haiku 5.5 rewrites verdicts the game record does not support.
  - It is configurable (`ExtractionConfig.dehalo`, `MEMORY_DEHALO_*`) and costs about $0.006 a game.
  - The extraction prompts also gained outcome-is-not-credit and skip-majority-votes rules
    (`de4134b2`).
  - It is an exception to the no-extra-judge constraint, and the pipeline's first Claude dependency.
- **New-role proxies** (ruled): the Chanteuse's critical blocks count fellow wolves only; Sentinel
  and Trailseer results naming an evil player; Sigilist hits per sigil. Built in `e5763cd1`.
- **Seeding** (ruled):
  - 12 AI-only games via `run_batch --configs extract_only --cycle-lineups`, 3 per lineup; retrieval
    off, extraction on, fresh store;
  - about $1.40 a game (about $0.9 play, about $0.5 extraction), so about $17;
  - synthesis offline with `consolidate()` (credit, prune and evict off) on a copy of the store,
    not the tick (see §9.6).
- **Demo and portfolio direction** (agreed):
  - one worked example on the portfolio: source observations (expandable, "N of M shown") →
    synthesized strategy → its later use with the agent's verdict, from the seeding plus the gate
    pilot;
  - the app shows a small teaser linking to it, and the memory inspector links "How was this
    strategy created?";
  - a credit-informed example is the optional second, traced from the v7 records (deferred; owner
    KIV);
  - none of it is a claim that a strategy improved play.

### 9.6 What the credit system needs before it runs (after launch, D5: diagnostic first)

The per-game metrics are ported (`e5763cd1`). Credit runs on per-decision grades in
`Agents/memory/consolidation/`, which need their own port:

1. **Decision grades by side** (`credit_rules.py`, `decision_scoring.py`, `credit.py`):
   - votes: the pack by blending with the room; the lone killer as the serial killer was; town as
     before; the Speculator after its pick as its picked side; before the pick, and the Fortune
     Teller always, unscored;
   - nights per §8.2 and §8.3 (the investigator on a delivered Suspicious; the vigilante by side;
     the healer against any attacker; the Chanteuse's tiers; ...); the Necromancer per game only;
   - the evil roles' concealment rule extended to the new evil roles.
2. **A followed pack-chat lesson is graded by the pack's kill that night** (ruled). Chat, kill and
   skill share the `night_action` namespace; each eval case carries its turn kind.
3. **Drop the conversion channel.** It credits strategies retrieved on town day turns, which no
   longer happen.
4. **A missing baseline reads unscored, not 0.** The seeding games, graded by the same new rules,
   serve as the memory-off baseline.
5. **The tick on its own database.** The Postgres in `WW_POSTGRES_DSN` holds the nine-seat
   `demo_gen1` store at generation 1 (723 records); a ten-seat tick would fold onto it. Use a
   separate database (`--dsn`) or archive and reset. Point `--bootstrap-store` at the ten-seat store,
   not the default `v7_fixed`.
6. **Data:** AI-only games with memory on (retrieval on, extraction off). A strategy needs 5
   scored follows before its track record enters synthesis, and 8 before it can be pruned.
7. **Validate the thresholds** (prune at −0.15 with ≥8 follows, protect with ≥2) on the ten-seat
   game before credit gains authority.

Additional limitation, kept for the report: on Vertex, the cache discount and the batch discount do
not stack (§9.4, batch extraction).
