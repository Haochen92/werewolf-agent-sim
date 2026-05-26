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

Derived metric: `adoption_rate = used_count / retrieved_count`. These counters could eventually surface deprecation candidates (high retrieval, near-zero adoption), popular strategies (high used_count), and stale strategies (zero retrieval) — but no deprecation logic is implemented in Phase 1. The counters are captured; acting on them is future work.

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

**What happened:** This failed to improve over v2. At n=120, v3's scores were statistically equivalent to v2 after accounting for one outlier game (see Results). The additional precision in the prompt didn't translate to additional precision in the output for this model at minimal thinking budget.

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

The 0% empty list rate in v2 is notable — every single case claimed at least one strategy point. This looks like a signal of over-attribution, but the attribution direction data (below) shows v2 has the *lowest* over-attribution rate (8%). The reconciliation: 0% empty lists means agents always found at least one matching strategy point, but it doesn't mean the claimed points were wrong. An agent can correctly adopt 1-2 of 3 retrieved points every turn while the judge still finds most attributions accurate. The 0% is a necessary-but-not-sufficient condition for over-attribution — suspicious in isolation, but not contradicted by the judge scores.

### Large-Sample Evaluation (n=120)

Note: v1 was evaluated at n=30 only (the attribution direction diagnostic was added after v1, so rerunning v1 at n=120 with the updated judge was not prioritized). The sample size difference means v1 scores have wider confidence intervals — treat them as directional, not directly comparable to v2/v3.

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

The experiment's measurement approach evolved mid-flight. The initial application judge measured only `adoption_accuracy` — a single 1-5 score for how well the self-reported adoption list matched observable behavior. This told us *how wrong* the attributions were, but not *in which direction*.

At n=30, we inspected low-scoring cases manually. The pattern that jumped out was over-attribution: agents claiming strategy points that loosely aligned with their action but didn't demonstrably drive it. This matched our prior assumption — the project memory file described agents "claiming adoption but acting contrary to strategy points" as the primary problem. We designed v2 and v3 with over-attribution reduction as the explicit goal.

After v2 showed strong improvement at n=30, we added `attribution_direction` as a diagnostic field on the judge to get systematic data rather than relying on case-level impressions. At n=120 with this new field, the picture shifted: v2's error distribution leaned toward *under*-attribution (19%) more than over-attribution (8%). The manual impressions at n=30 had been misleading — either because the small sample over-represented over-attribution cases, because human reviewers are better at spotting false claims than missing ones, or both.

This reframed the problem. The v1→v2 improvement didn't come from targeting over-attribution specifically — the schema reorder reduced both error types simultaneously by fixing the root cause (retrospective rationalization) rather than a symptom. Retrospective reporting is unreliable in both directions: the model sometimes claims strategies it didn't follow, and sometimes fails to report strategies it clearly did.

### The v2 Selection Tension

The attribution direction data creates an awkward situation for the v2 decision. We argued earlier that under-attribution is the more dangerous failure mode — it makes effective strategies look unused, which would produce false deprecation signals if the counters are ever used for curation. But v2 has the *highest* under-attribution rate (19% vs v3's 13%).

Meanwhile, v3 — which was designed to reduce over-attribution — actually made over-attribution *worse* (14% vs v2's 8%) while inadvertently improving under-attribution (13% vs v2's 19%). The DO/DON'T rules pushed agents to be more explicit about their claims, which reduced omissions but introduced more false claims. Neither version optimized the metric we said mattered most.

v2 is still the right choice, but not because of any single metric. The case rests on the full picture: highest overall adoption accuracy (4.38 vs 4.26), highest action quality (4.47 vs 3.99/4.41), and the simpler prompt being a better fit for flash-lite at minimal thinking. The 19% under-attribution is the accepted cost — a strategy that's genuinely popular will still accumulate high `used_count` even with some under-reporting, making the counters useful for broad pattern detection if not precise per-strategy measurement.

### Judge Model Limitation

All attribution direction data comes from `gemini-2.5-flash`. Independent spot-checks with Claude Opus were directionally consistent — Opus agreed with flash's accuracy assessments on the cases reviewed — but no systematic pro-model evaluation was run. Whether the under/over-attribution distribution holds under a stronger judge is an open question. This is acceptable for Phase 1, where the counters are informational. If Phase 2 effectiveness scoring is implemented and the direction data feeds into retrieval ranking, validating with a pro-model judge becomes a prerequisite.

### Prompt Precision Doesn't Guarantee Model Precision

Adding structured DO/DON'T rules and explicit anchoring on the `Action:` field didn't improve attribution accuracy over v2's simpler natural language. After excluding the outlier game, v3 was statistically equivalent to v2 on most metrics. The data supports "v3 didn't improve over v2" but not a stronger causal claim about *why* — we didn't test a conversational-style version of v3's content, so we can't distinguish whether the structured format or the added complexity caused the non-improvement.

The simpler explanation is sufficient: for flash-lite at minimal thinking budget, the simpler instruction was enough — additional precision in the prompt didn't translate to additional precision in the output. Whether this reflects a general property of weak models at low thinking budgets or is specific to this task is an open question.

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

### The Attribution Ambiguity Is Structural, Not Prompt-Solvable

This experiment surfaced a limitation that no prompt iteration could fix. Agents receive two types of retrieved memory in the same context: observations (factual accounts like "healer stayed quiet and survived") and strategy points (prescriptive advice like "maintain a low profile as healer"). Both can teach the same lesson from different angles. When the agent acts on that lesson, attributing the action to one source over the other requires a causal distinction the model may not be capable of making — especially at minimal thinking budget.

The v3 prompt tried to address this directly with the rule "DON'T list a point if your action was shaped by observations, not strategy points." It didn't help. The rule asks the agent to introspect on whether its reasoning came from a descriptive or prescriptive input, which is a harder cognitive operation than the attribution task itself. This likely contributed to both directions of error: agents sometimes claimed a strategy point when the observation was the real driver (over-attribution), and sometimes failed to claim a strategy point because the overlapping observation felt like the "real" source (under-attribution).

The implication is that the ~72% accuracy ceiling may not be a prompt engineering problem at all. It may reflect a structural ambiguity in presenting two overlapping memory types in the same context and asking a weak model to distinguish their influence. Improving beyond 72% likely requires either a stronger model, a separated presentation, or removing the overlap entirely.

### Next Experiments

This finding motivates the next experiment directly:

- **Observations-only ablation:** If observations and strategy points overlap enough to create attribution ambiguity, the question becomes whether strategy points add value beyond what observations already provide. Observations are self-correcting — postgame extraction naturally captures "tried X, it worked" vs "tried X, got caught" — and `observation_count` is a direct signal of pattern frequency without needing an adoption tracking pipeline. If action quality holds without strategy points, the memory system simplifies significantly: one memory type, no adoption tracking, no Phase 2 effectiveness scoring.
- **Phase 2 effectiveness scoring:** Deferred pending the ablation result. If strategy points are retained, Phase 2 would add postgame effectiveness scoring to close the loop on strategy quality.

## Artifacts

All artifacts are co-located in `evidence/memory_system/strategy_adoption/`.

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
