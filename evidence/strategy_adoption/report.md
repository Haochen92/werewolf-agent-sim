# Strategy Adoption Tracking: Phase 1 Report

## Motivation

This project builds a multi-agent Werewolf simulation where AI agents accumulate long-term memory across games. A postgame extraction pipeline pulls strategic lessons ("when under pressure as a wolf, deflect to a quieter target") and stores them as **strategy points** in a vector store. Before each game, agents retrieve relevant strategy points via semantic search based on their current in-game situation.

The gap: **we had no signal on whether any of this actually worked.** The only metadata on each strategy point was `observation_count` — how many times the same lesson was re-extracted. This measures how often a *situation* arises, not whether the *strategy* is effective. A bad strategy for a common situation accumulates a high count and looks important. A great strategy for a rare situation looks disposable.

Before this work, the memory system had no way to distinguish a strategy agents relied on every game from one they consistently ignored. Adoption tracking makes strategy quality observable for the first time, enabling data-driven curation decisions that previously required manual review of game transcripts.

## The Design: Two Phases

### Phase 1 — Lightweight Instrumentation (this report)

Track which strategy points agents claim to follow during gameplay. Two counters on each strategy point:
- `retrieved_count` — how many times agents were shown this strategy
- `used_count` — how many times agents reported it as influential

Derived metric: `adoption_rate = used_count / retrieved_count`. This surfaces deprecation candidates (high retrieval, near-zero adoption), popular strategies (high used_count), and stale strategies (zero retrieval).

### Phase 2 — Postgame Effectiveness Scoring (deferred)

A single pro-model LLM call per game evaluates all adoptions against the full transcript, scoring each as +1 (positive), 0 (neutral), or -1 (negative). This would add `positive_count`, `neutral_count`, `negative_count` to each strategy point. Phase 2 is deferred pending an ablation test on whether strategy points add value beyond observations alone.

## Prompt Iterations and Experiment

Three prompt versions were tested. The game agents run on `gemini-3.1-flash-lite` with minimal thinking budget — a weak model that constrains how much metacognition we can ask for. Each version tested a specific hypothesis about how to elicit accurate self-reporting from this model.

### v1 — Broad "Influenced" Language

**Hypothesis:** Under-attribution (missing real signal) is more costly than over-attribution (noise that can be filtered later). A deliberately broad bar with concrete anchors should help flash-lite understand what counts as influence.

```
If any of the above strategy points influenced your decision — shaped your
reasoning, changed your target, or adjusted your approach — report their
numbers in adopted_strategy_keys (e.g. [1, 3]). An empty list is fine.
```

At this stage, `adopted_strategy_keys` was declared **after** `message`/`vote_target` in the schema — the model generated its action first, then reported which strategies "influenced" it.

**What happened:** The v1 prompt produced a baseline adoption accuracy of 4.00 with 27% of cases showing significant mismatch (scores 1-2). The word "influenced" was too vague — combined with the retrospective schema position, agents over-attributed freely. Any strategy that loosely aligned with the chosen action got claimed, regardless of whether it actually drove the decision. The three anchors ("shaped your reasoning, changed your target, or adjusted your approach") gave agents too many hooks for rationalization rather than constraining them.

### v2 — Behavioral Matching + Schema Reorder

**Hypothesis:** Two problems needed fixing simultaneously. First, generating `adopted_strategy_keys` after the action lets the model rationalize retrospectively — it sees what it already decided and picks matching strategies. Putting it first forces prospective commitment. Second, the language should shift from vague causal claims ("influenced") to behavioral matching ("did you do what the strategy said?").

```
In adopted_strategy_keys, list only strategy points whose advice your action
follows (e.g. [1, 3]). Do not list points you read but acted against. An
empty list is fine if none of the points match your action.
```

Schema change — `adopted_strategy_keys` moved to the **first field**:

```python
# v1: retrospective (adopted_strategy_keys after action)
class DayDiscussOutput(BaseModel):
    message: str | None
    updated_strategy: str
    adopted_strategy_keys: list[int] = Field(default_factory=list)

# v2: prospective (adopted_strategy_keys before action)
class DayDiscussOutput(BaseModel):
    adopted_strategy_keys: list[int] = Field(
        default_factory=list,
        description="Indices of strategy points whose advice your action follows, empty list if none match",
    )
    message: str | None
    updated_strategy: str
```

**What happened:** This was the single largest improvement. Not only did adoption accuracy jump (4.00 → 4.38), but action quality (+0.50) and strategy application (+0.52) improved substantially too. The schema reorder didn't just improve *reporting* — it improved the agent's *actual behavior*. When the model commits to which strategies it will follow before generating the action, the action itself becomes more aligned with the retrieved guidance. The prospective commitment creates a planning effect, not just a reporting effect. This was the most important insight of the experiment: the field ordering in a structured output schema is a prompt engineering lever, not just a formatting choice.

### v3 — Structured DO/DON'T Rules

**Hypothesis:** Structured rules with explicit anchoring on the strategy point's `Action:` field text would improve precision. The DO/DON'T format would give flash-lite clearer boundaries, and anchoring on "the text after Action:" would make the matching criterion unambiguous.

```
In adopted_strategy_keys (e.g. [1, 3]), report which strategy points you followed.
DO: list a point if you took its recommended action (the text after "Action:").
DON'T: list a point you read but acted against.
DON'T: list a point if your action was shaped by observations, not strategy points.
An empty list is fine if none of the points match your action.
```

**What happened:** This failed to improve over v2. At n=120, v3's scores were statistically equivalent to v2 after accounting for one outlier game (see Results). The DO/DON'T format was a poor fit for this model at minimal thinking budget — a lesson that generalizes beyond this feature.

## Results

### Evaluation Setup

An LLM judge (`gemini-2.5-flash`) evaluates frozen game turns on four dimensions plus a diagnostic field added during the experiment:

1. **Action Quality** (1-5): Is the action strategically appropriate for this role and game state?
2. **Strategy Application** (1-5): Does the action use retrieved guidance discriminantly?
3. **Grounding** (1-5): Are all claims traceable to provided context?
4. **Adoption Accuracy** (1-5): Does the self-reported adoption list match observable behavior?
5. **Attribution Direction** (`over` / `under` / `accurate`): Classifies the direction of adoption mismatch. Added during this experiment to distinguish over- from under-attribution.

Each eval set was built from 3 frozen Langfuse game traces (v1: 269 cases, v2: 230 cases, v3: 240 cases). Results were evaluated at both n=30 (initial) and n=120 (final).

### Raw Adoption Rates

The adoption rate stayed stable across versions — the prompt changes affected *accuracy*, not *volume*. Agents consistently claimed ~1.5 of 3 retrieved strategy points per turn.

| Version | Avg Retrieved SPs | Avg Adopted | Adoption Rate | Empty Lists |
|---------|-------------------|-------------|---------------|-------------|
| v1 | 3.0 | 1.4 | 48.0% | 6 (2.2%) |
| v2 | 3.0 | 1.5 | 49.2% | 0 (0.0%) |
| v3 | 3.0 | 1.5 | 51.9% | 3 (1.2%) |

The 0% empty list rate in v2 was a soft signal of over-attribution — every single case claimed at least one strategy point. v3's 1.2% is more realistic.

### Large-Sample Evaluation (n=120)

| Metric | v1 (n=30) | v2 (n=120) | v3 (n=120) | v3 excl outlier (n=70) |
|--------|-----------|------------|------------|------------------------|
| action_quality | 3.97 | **4.47** | 3.99 | 4.41 |
| strategy_application | 4.17 | **4.69** | 4.31 | 4.61 |
| grounding | 4.73 | **4.57** | 4.08 | 4.60 |
| adoption_accuracy | 4.00 | **4.38** | 4.26 | 4.16 |

**One outlier game dominated v3's apparent regression.** Game `888e4e81...` produced 15 of 16 action_quality=1 scores and all 13 grounding=1 scores in v3 — agents in that game hallucinated heavily. Excluding it, v3's action quality (4.41), strategy application (4.61), and grounding (4.60) are statistically equivalent to v2. The regression was game variance, not a prompt effect.

### Attribution Direction (n=120)

| Direction | v2 | v3 |
|-----------|-----|-----|
| Accurate | 87 (72%) | 87 (73%) |
| Over-attribution | 10 (8%) | 17 (14%) |
| Under-attribution | 23 (19%) | 15 (13%) |

v2 and v3 achieve the same accuracy rate (~72-73%). The difference is in failure mode: v2 leans toward under-attribution, v3 toward over-attribution. The v3 DO/DON'T rules reduced under-attribution but introduced more over-attribution — it pushed agents to be more explicit about their claims, but some of those claims were false.

## Key Findings

### What We Got Wrong: The Attribution Direction Assumption

We initially assumed over-attribution was the primary problem — the memory file for this project described agents "claiming adoption but acting contrary to strategy points" as the root cause. We designed the experiment to measure and reduce it.

At n=120, the data told a different story. Both directions are present in roughly equal measure (8-19% each), and the v1→v2 improvement came from reducing *both types simultaneously* via the schema reorder — not from targeting one direction. This reframed our understanding: the problem wasn't that agents were biased toward over-claiming, but that retrospective reporting is inherently unreliable in both directions. The schema reorder fixed the root cause (retrospective rationalization) rather than a symptom (over-attribution specifically).

If we had continued optimizing solely for over-attribution reduction, we would have missed that under-attribution is equally prevalent and arguably more dangerous — it makes useful strategies look unused, potentially leading to their deprecation.

### The v2 Under-Attribution Tradeoff

v2 has the highest under-attribution rate (19% vs v3's 13%). Earlier analysis established that under-attribution is the more dangerous failure mode — it could lead to deprecating effective strategies, a permanent loss of signal.

v2 is still the right choice despite this tension, for three reasons:
1. The schema reorder already substantially reduced both error types from v1's baseline. The remaining 19% under-attribution is the residual after the biggest available fix.
2. 72% accuracy is sufficient for Phase 1's purpose — surfacing broad adoption patterns and identifying clear deprecation candidates, not precise per-strategy metrics. A strategy that's genuinely popular will still show high `used_count` even with some under-reporting.
3. Over-attribution (v3's weakness at 14%) is harder to correct downstream than under-attribution. Over-counted strategies look artificially important and resist deprecation; under-counted strategies can be rescued by cross-referencing with retrieval frequency.

### Prompt Consistency Matters More Than Prompt Precision

The v3 DO/DON'T finding generalizes beyond this feature: for weak models, prompt *consistency* with the rest of the system matters more than prompt *precision* in isolation.

Every other prompt in the system — situation summary, day discussion, voting, tone instruction — uses natural, conversational language. The v3 DO/DON'T format broke that consistency. The dedup prompt also uses structured rules, but it runs at `thinking_level="low"` rather than minimal, which may account for why that style works there.

The lesson: when working with a weak model at minimal thinking budget, match the instruction style to what the model already handles well in the same context. A "better" prompt by human standards can be a worse prompt for the model if it breaks the stylistic contract.

### Schema Field Order as a Prompt Engineering Lever

The v1→v2 improvement demonstrated that structured output field ordering is a meaningful prompt engineering tool. For models generating structured output in field-declaration order, placing a metacognitive field (like `adopted_strategy_keys`) *before* the action fields creates prospective commitment pressure — the model plans before it acts, rather than rationalizing after. This produced measurable improvements not just in the metacognitive field itself, but in the quality of the downstream action.

## Design Decisions

### Integer Indices Over UUIDs

Early prototypes asked agents to report strategy point UUIDs. Flash-lite corrupted 36-character alphanumeric strings ~30% of the time. Integer indices (`[1]`, `[2]`, `[3]`) eliminated this entirely — anything outside `[1..N]` is logged and skipped.

### Indexed Display Format

Strategy points changed from bullet-point format to indexed format with an explicit `Action:` prefix:

```
# Before
- If you have just made a successful save... → Maintain a low profile...

# After
[1] If you have just made a successful save... → Action: Maintain a low profile...
```

### Inline Count Updates

`retrieved_count` and `used_count` are updated inline — immediately after each agent's LLM call. The alternative was accumulating adoption data postgame. Inline is simpler (no replay logic), and the failure mode — overcounting if a game crashes mid-run — is minor noise.

### Graph State Architecture

Adoption records flow upward through the LangGraph hierarchy via explicit state projection with `add` reducers:

```
Agent subgraph → DayGraphState (add reducer) → OrchestratorGraph (add reducer) → postgame
```

Each adoption record is minimal: `(strategy_key, player_id, role, day, round, action_phase)`.

## Decision

**v2 is selected as the production prompt.** It achieves the highest adoption accuracy (4.38), the lowest over-attribution rate (8%), and — critically — the highest action quality (4.47) and strategy application (4.69) scores. The simple language fits flash-lite's capabilities, and the schema reorder provides the structural guarantee that matters most.

```
In adopted_strategy_keys, list only strategy points whose advice your action
follows (e.g. [1, 3]). Do not list points you read but acted against. An
empty list is fine if none of the points match your action.
```

We considered bumping `thinking_level` from minimal to low for the agent calls, which might improve adoption accuracy. This was rejected: thinking level applies to the entire agent call (discussion/vote), not just the adoption field, making it a significant cost increase across every turn of every game for a marginal improvement on one output field.

## What's Next

### The Attribution Ambiguity Problem

This experiment surfaced a deeper question about the memory architecture itself. Agents receive two types of retrieved memory — observations (factual accounts of past game events) and strategy points (prescriptive advice) — and must attribute their actions to strategy points specifically. In practice, agents struggled to distinguish the source of their reasoning. The v3 prompt explicitly tried to address this with the rule "DON'T list a point if your action was shaped by observations, not strategy points." That rule didn't help — agents still misattributed, and the rule itself may have added confusion.

The two memory types often overlap in content. An observation like "healer stayed quiet and survived" and a strategy point like "maintain a low profile as healer" teach the same lesson from different angles. When both appear in the same prompt, the agent has to determine which one "influenced" it — a distinction that may not be meaningful for a weak model at minimal thinking budget. This attribution ambiguity contributes to both over- and under-attribution, and no prompt change can fully resolve it because the ambiguity is structural.

This observation motivates the next experiment:

- **Observations-only ablation:** Test whether strategy points add value beyond what observations already provide, using the new snapshot-based application experiment. Observations are self-correcting — postgame extraction naturally captures "tried X, it worked" vs "tried X, got caught" — and `observation_count` is a direct signal of pattern frequency without needing an adoption tracking pipeline. If action quality holds without strategy points, the adoption pipeline and Phase 2 can be dropped entirely, significantly simplifying the memory system.
- **Phase 2 effectiveness scoring:** Deferred pending the ablation result. If strategy points are retained, Phase 2 would add postgame effectiveness scoring to close the loop on strategy quality.

## Artifacts

All artifacts are co-located in `evidence/strategy_adoption/`.

| File | Description |
|------|-------------|
| `eval_sets/phase1_adoption_v1.jsonl` | 269 frozen cases from v1 games |
| `eval_sets/phase1_adoption_v2.jsonl` | 230 frozen cases from v2 games |
| `eval_sets/phase1_adoption_v3.jsonl` | 240 frozen cases from v3 games (rebuilt from 3 games) |
| `eval_results/captured_eval_20260523_174718.jsonl` | v1 application eval, n=30 |
| `eval_results/captured_eval_20260523_185600.jsonl` | v2 application eval, n=30 (old judge, no attribution_direction) |
| `eval_results/captured_eval_20260524_021749.jsonl` | v2 application eval, n=120 (updated judge) |
| `eval_results/captured_eval_20260524_021750.jsonl` | v3 application eval, n=120 (updated judge) |
| `eval_configs/` | All dataset build and eval configs |

## Implementation Changes

| Area | Files | Change |
|------|-------|--------|
| Schemas | `schemas/memory.py`, `schemas/output.py`, `schemas/evaluation.py` | New count fields, `StrategyAdoption` model, `adopted_strategy_keys` on all agent output schemas |
| Prompts | `prompts/memory.py`, `prompt_inputs.py` | `ADOPTION_INSTRUCTION`, interpolated into memory contexts |
| Formatting | `formatters.py`, `reranker.py` | Indexed `[1]`, `[2]`, `[3]` strategy display |
| State | `state.py`, `graphs/parent.py` | `strategy_adoptions` accumulator with `add` reducer |
| Core | `agents.py` | Index map construction, adoption resolution, inline count updates |
| Dedup | `memory_deduplication.py`, `memory_batch_deduplication.py` | Metadata preservation for count fields during merges |
| Eval | `evaluation/core/schemas.py`, `evaluation/judges/prompts.py` | `adoption_accuracy` + `attribution_direction` judge dimensions |
| Eval | `evaluation/experiments/captured.py`, `evaluation/experiments/application.py` | Application judge integration, snapshot re-retrieval mode |
