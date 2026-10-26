# Strategy Adoption Tracking: Phase 1 Report

## In short

*Added 2026-10-26. The report below is the May 2026 record, unchanged except where marked; the June
section at its end is new.*

- **Question.** When agents are shown strategy points (advice lessons from past games), can they report
  reliably which ones they acted on, and how should the output be shaped so they do?
- **Test.** Three prompt versions for a field listing the points followed, each played in 3 games;
  frozen turns from those games scored 1–5 by one model judge (`gemini-2.5-flash`): v1 on 30 turns,
  v2 and v3 on 120.
- **Answer.** v2 was best: the list placed before the action, with "list only points whose advice your
  action follows". The judge found its list accurate on 72% of 120 turns, over-claiming on 8% and
  under-claiming on 19%. Placing the list before the action also raised the judge's action score
  (3.97 for v1 on 30 turns, 4.47 for v2 on 120).
- **What followed.** In June 2026 a verdict on every lesson shown replaced the list, after a screen
  found the instruction was followed only once it was stated in the prompt body (coverage 0.27 →
  0.97; section below). Today a turn gives each strategy point shown a verdict: follow, override or not
  relevant, with a one-line reason (`Agents/schemas/output.py::StrategyVerdict`, carried on
  `Agents/schemas/turn.py::TurnEffects`). Each follow raises the point's counters and feeds credit;
  `adopted_strategy_keys` survives only as a field derived from the follows on the evaluation record
  (`Agents/schemas/evaluation.py::EvalCase`).

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

A single pro-model LLM call per game evaluates all adoptions against the full transcript, scoring each as +1 (positive), 0 (neutral), or -1 (negative). This would add `positive_count`, `neutral_count`, `negative_count` to each strategy point. Phase 2 is deferred pending an ablation test on whether strategy points add value beyond observations alone. (Never built in this form; see the dated note under What's Next.)

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

**What happened:** This failed to improve over v2. At n=120, once one outlier game is set aside, v3's scores were within a tenth of v2's on three of the four measures (see Results). The additional precision in the prompt didn't translate to additional precision in the output for this model at minimal thinking budget.

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

**One outlier game dominated v3's apparent regression.** Game `888e4e81...` produced 15 of 16 action_quality=1 scores and all 13 grounding=1 scores in v3 — agents in that game hallucinated heavily. Excluding it, v3's action quality (4.41), strategy application (4.61), and grounding (4.60) are within a tenth of v2's (4.47, 4.69, 4.57) on the 1–5 judge scale; no significance test is reported, and the samples differ (70 turns against 120). Its adoption accuracy stays lower (4.16 against 4.38). This points to game variance rather than a prompt effect for the regression.

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

Adding structured DO/DON'T rules and explicit anchoring on the `Action:` field didn't improve attribution accuracy over v2's simpler natural language. After excluding the outlier game, v3 was within a tenth of v2 on three of the four measures. The data supports "v3 didn't improve over v2" but not a stronger causal claim about *why* — we didn't test a conversational-style version of v3's content, so we can't distinguish whether the structured format or the added complexity caused the non-improvement.

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

> **2026-10-26.** v2 was the production prompt from May until 2026-06-16, when a verdict on each
> strategy point shown (follow, override or not relevant, with a one-line reason) replaced the list;
> see the June section below. `adopted_strategy_keys` is no longer in any model's output. It survives
> only on the evaluation record, derived from the follow verdicts and kept for analysis
> (`Agents/schemas/evaluation.py::EvalCase`, filled in
> `Agents/turn/pipeline.py::run_memory_informed_action`; the judge input builder
> `evaluation/src/judges/case_inputs.py::eval_case_to_judge_inputs` still reads it). The
> commitment-before-action lesson carried over: today's turn schema answers in the order reads,
> verdicts, strategy note, action (`Agents/schemas/lineup_output.py::TurnOutput`).

**v2 is selected as the production prompt.** It achieves the highest adoption accuracy (4.38), the lowest over-attribution rate (8%), and — critically — the highest action quality (4.47) and strategy application (4.69) scores. The simple language fits flash-lite's capabilities, and the schema reorder provides the structural guarantee that matters most.

```
In adopted_strategy_keys, list only strategy points whose advice your action
follows (e.g. [1, 3]). Do not list points you read but acted against. An
empty list is fine if none of the points match your action.
```

We considered bumping `thinking_level` from minimal to low for the agent calls, which might improve adoption accuracy. This was rejected: thinking level applies to the entire agent call (discussion/vote), not just the adoption field, making it a significant cost increase across every turn of every game for a marginal improvement on one output field.

## What's Next

> **2026-10-26.** Both next steps are settled. The [ablation](../ablation/report.md) ran: on 120
> replayed turns no condition was better, and observations only was chosen then. Served games now
> retrieve strategy points only (`server/game/run_config.py::game_run_config`), which removes the
> overlap described below; whether that changed attribution accuracy was not measured. Phase 2 was
> never built as a model call. Its role, a positive, neutral or negative count on each strategy point
> from how play went when it was followed, was taken by credit assignment worked out by fixed rules
> from the game records: first in the v7 loop, and today in the credit pass, which needs no model call
> (`Agents/memory/consolidation/tick.py::run_credit_pass`, `Agents/memory/consolidation/credit.py`).

### The Attribution Ambiguity Is Structural, Not Prompt-Solvable

This experiment surfaced a limitation that no prompt iteration could fix. Agents receive two types of retrieved memory in the same context: observations (factual accounts like "healer stayed quiet and survived") and strategy points (prescriptive advice like "maintain a low profile as healer"). Both can teach the same lesson from different angles. When the agent acts on that lesson, attributing the action to one source over the other requires a causal distinction the model may not be capable of making — especially at minimal thinking budget.

The v3 prompt tried to address this directly with the rule "DON'T list a point if your action was shaped by observations, not strategy points." It didn't help. The rule asks the agent to introspect on whether its reasoning came from a descriptive or prescriptive input, which is a harder cognitive operation than the attribution task itself. This likely contributed to both directions of error: agents sometimes claimed a strategy point when the observation was the real driver (over-attribution), and sometimes failed to claim a strategy point because the overlapping observation felt like the "real" source (under-attribution).

The implication is that the ~72% accuracy ceiling may not be a prompt engineering problem at all. It may reflect a structural ambiguity in presenting two overlapping memory types in the same context and asking a weak model to distinguish their influence. Improving beyond 72% likely requires either a stronger model, a separated presentation, or removing the overlap entirely.

### Next Experiments

This finding motivates the next experiment directly:

- **Observations-only ablation:** If observations and strategy points overlap enough to create attribution ambiguity, the question becomes whether strategy points add value beyond what observations already provide. Observations are self-correcting — postgame extraction naturally captures "tried X, it worked" vs "tried X, got caught" — and `observation_count` is a direct signal of pattern frequency without needing an adoption tracking pipeline. If action quality holds without strategy points, the memory system simplifies significantly: one memory type, no adoption tracking, no Phase 2 effectiveness scoring.
- **Phase 2 effectiveness scoring:** Deferred pending the ablation result. If strategy points are retained, Phase 2 would add postgame effectiveness scoring to close the loop on strategy quality.

## June 2026: one verdict per lesson, the step to today's field

*Added 2026-10-26, from the [forced-verdict screen's log](forced_schema_screen/experiment_log.md),
which holds every run and its data files.*

**The question moved.** May asked agents to list the lessons they followed. In June the question
became whether a seat should give a verdict on every lesson shown, before it acts: does the lesson fully
apply, partly apply, or not apply to this board? An earlier probe (2026-06-13;
[decision-replay log](../effectiveness/decision_replay/experiment_log.md)) had found that forcing such
a verdict hurt the vote (0.75 → 0.55). It ran on another day, so the screen re-ran every arm
together instead of comparing with it.

**The test (2026-06-16).** 48 town day votes from 10 games that were never among the v6 store's
sources (days 2–8; villager, healer, investigator), with memory from the same game left out of both
stores. Each vote was regenerated five ways in one run: no memory, and each of two
stores shown either plainly or with a forced verdict per memory. Each memory arm fetched the top 5
observations from its own store. The stores were v5, whose lessons were worded cautiously, and v6,
rebuilt in June to fix that content. The players were flash-lite. The measure is how often the vote
hit a threat.

| Store | Shown plainly | Forced verdict per memory | Forced − plain |
|---|---|---|---|
| v5 | 0.625 | 0.521 | −0.104 |
| v6 | 0.604 | 0.625 | +0.021 |

With no memory: 0.667.

**Forcing a verdict hurt the vote on v5 content and was neutral on v6 content.** The earlier
probe's harm repeated within one run on v5 and did not appear on v6, which points to the cautious v5
content rather than to the forced verdict.

**Missing verdicts were a delivery problem, not a limit of the model.** In this run the model gave a
verdict for only about a third of the memories shown (148 and 145 verdicts for 240 memories; a full
row of verdicts 0.33–0.35 of the time). Two follow-ups on 60 decisions ruled out two causes: the model
was not dropping the low-ranked memories (coverage was flat across ranks 1–5), and numbering the
memories did not help. The instruction had sat only in the output schema's field description. Stating
it in the prompt body as well raised the verdicts from 168 to 302 for 300 memories (a full row 0.27 →
0.97 of the time, every rank covered); fixing the list's length in the schema gave 300 of 300. Neither
padded the rows: no decision gave every memory the same verdict, and every reason was distinct. Full
coverage did not hurt the v6 vote (0.617 with the instruction in the schema only, 0.60 in the prompt
body, 0.65 with the length fixed). A check on 40 discussion turns with the v6 store gave 200 verdicts
for 200 memories; 34 of the 40 seats spoke and 6 passed, and the messages read as natural.

**How sure we are.**
- 48 votes, with McNemar not significant: a screen, not a verdict. Under forcing, v6 against v5
  flipped 8 votes toward v6 and 3 toward v5 (p = 0.23); shown plainly, 3 against 4 (p = 1.0).
- No memory arm beat no memory (0.667) on this slice. The screen says forcing is safe on v6 content,
  not that memory helped the vote.
- Partial coverage inflated the share of memories judged applicable (v5 0.649, v6 0.697 at n=48).
  Under full coverage it fell from 0.798 to about 0.55, because the memories the model had skipped
  were mostly the ones that did not apply. The v6-against-v5 comparison of that share was not re-run.
- One player model, observations only, single decisions replayed rather than whole games.

**What followed.** The design was locked the same day: the per-memory instruction goes in the prompt
body and the field description stays short (`memory_applicability` on the turn's output schema). The
same delivery replaced `adopted_strategy_keys` for strategy points: one verdict per strategy point
shown, follow, override or not relevant, with a one-line reason, its instruction stated in the prompt
body (`Agents/prompts/memory/context.py::STRATEGY_VERDICT_INSTRUCTION`, added 2026-06-16). The log
covers the observation verdict; it records no screen of the strategy-point verdict itself. That is
today's field (`Agents/schemas/output.py::StrategyVerdict`, on
`Agents/schemas/lineup_output.py::TurnOutput`). Served games show strategy points only, so there the
observation verdict is always empty.

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
| `forced_schema_screen/` | June 2026 forced-verdict screen: log and `run_*.json` results |

## Implementation Changes

Paths as of May 2026; the code has since been reorganised. Today's count write-back is
`Agents/turn/adoption.py::process_strategy_adoption`.

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
