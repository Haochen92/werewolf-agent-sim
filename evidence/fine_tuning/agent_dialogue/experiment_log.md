# Fine-Tuning: Agent Dialogue Distillation

## Motivation

Current werewolf agents running on flash-lite ($0.193/game) produce functional but bland, repetitive dialogue. They tend to get aggressive early, harp on tone/style rather than substance, and lack conversational variety. Upgrading to flash-3.5 would improve quality but costs $1.16/game (6x more).

Fine-tuning an open-source model on a serverless provider (Together AI, Fireworks AI) could match or exceed flash-lite quality at significantly lower inference cost, while potentially improving dialogue quality through distillation from a stronger model.

## Token Budget (measured from Langfuse)

Actual production numbers per LLM call (averaged across game phases):
- **Input:** ~4,492 tokens/call
- **Output:** ~199 tokens/call
- **Calls/game:** ~160 (varies by game length, ~85% of day-3-round-3 peak)
- **Per game:** ~0.611M input, ~0.027M output

Output is structured (Pydantic schema), not free text:
```python
class DayDiscussOutput(BaseModel):
    adopted_strategy_keys: list[int]   # which memories to apply
    message: str | None                # the dialogue text
    updated_strategy: str              # internal strategy update
```

The model must produce valid structured output — `message` plus `adopted_strategy_keys` plus `updated_strategy`. This is harder than pure dialogue generation.

## Cost Analysis

### Inference cost per game

| Model | $/game | vs flash-lite | Tunable | Notes |
|-------|--------|---------------|---------|-------|
| **GPT-OSS 20B** (Together) | $0.036 | **-81%** | Yes | Cheapest viable option |
| **GPT-OSS 20B** (Fireworks) | $0.051 | **-74%** | Yes | Slightly pricier |
| **Qwen3.5 9B** (Together) | $0.065 | **-66%** | Yes | Smallest, cheapest to train |
| **GPT-OSS 120B** (Together/Fireworks) | $0.108 | **-44%** | Yes | Best capacity/cost balance |
| **Gemma 4 31B** (Together) | $0.136 | **-30%** | Yes | Good middle ground |
| Gemini 3.1 Flash-Lite | $0.193 | baseline | No | Current production |
| Gemini 3.5 Flash | $1.162 | +500% | No | Quality upgrade baseline |

Pricing: Together AI and Fireworks AI serve fine-tuned LoRA adapters at base model serverless rates with no hosting fee. Prices as of 2026-05-28.

### Training cost (one-time, per run)

Together AI LoRA fine-tuning rates: ≤16B $0.48/1M, 17-69B $1.50/1M, 70-100B $2.90/1M.

| Dataset size | Qwen3.5 9B | Gemma 4 31B | GPT-OSS 120B |
|---|---|---|---|
| 500 ex × 3 epochs | $3 | $11 | $20 |
| 1,000 ex × 3 epochs | $7 | $21 | $41 |
| 2,000 ex × 3 epochs | $14 | $42 | $82 |

### Breakeven

| Model | Saving/game | Training cost (500 ex) | Breakeven |
|-------|-------------|----------------------|-----------|
| GPT-OSS 20B | $0.157 | ~$7 | ~45 games |
| GPT-OSS 120B | $0.085 | ~$20 | ~235 games |
| Gemma 4 31B | $0.057 | ~$11 | ~193 games |

## Model Selection

### Why not 8B

The original analysis proposed 8B as sufficient for the "constrained werewolf domain." Revised assessment is more cautious:

- Input context is ~4.5K tokens — within an 8B's nominal window but at the edge of its effective range
- Output requires structured JSON with correct field values, not just natural text
- The model must reference specific memory indices (`adopted_strategy_keys`) and produce coherent strategy updates
- 8B models' reasoning quality degrades noticeably with complex structured output tasks

### Recommended: GPT-OSS 120B

Best balance of capacity and cost:
- 120B dense — strong enough for 4.5K context + structured output + strategic reasoning
- $0.108/game (44% cheaper than flash-lite)
- $20/training run at 500 examples — cheap to iterate
- Tunable on both Together AI and Fireworks AI
- 128K context window — more than sufficient

### Fallback: start with Qwen3.5 9B

If the approach is uncertain, start with Qwen3.5 9B at $3/run to validate the pipeline works before committing to 120B training. If 9B produces garbage, the task is likely too hard for fine-tuning at any reasonable size. If 9B is mediocre but shows signal, scale up.

## Two Separable Problems

1. **Dialogue style (easier):** Teach natural, human-like werewolf speech patterns — accusations, deflections, coalition-building. Trainable via distillation from a powerful model. Output is somewhat subjective.

2. **Decision quality (harder):** Strategic reasoning — who to vote for, how to deflect suspicion, when to reveal information. Fine-tuning can't exceed the base model's reasoning capacity. Better addressed via pipeline improvements (memory, retrieval, prompts).

Recommendation: fine-tune for style, improve decisions via pipeline.

## Dataset Requirements

### What each training example looks like

A single game turn with full context:
- **Input:** role prompt + dialogue history + retrieved memories + game events (~4.5K tokens)
- **Output:** structured JSON with message, adopted_strategy_keys, updated_strategy (~200 tokens)

### Volume needed

| Target | Examples | Coverage |
|--------|----------|----------|
| Minimum viable | 500 | 4 roles × ~3 game phases × ~40 situations |
| Good coverage | 1,000-2,000 | Includes edge cases, memory integration, early/mid/late game |

### Sources

1. **Distillation from strong model:** Run games with flash-3.5 or Claude, extract (context → response) pairs. Most scalable but costs $1.16/game for flash-3.5.
2. **Existing game logs:** Rewrite current flash-lite dialogue using a stronger model. Cheaper — only the rewrite call, not full game simulation.
3. **GCP free trial credits:** $300/account can generate 150-300 games with flash-3.5 at $1.16/game. Best source of high-quality training data.

### Memory integration coverage

The fine-tuned model needs examples covering:
- Turns with relevant memory → model correctly applies it
- Turns with irrelevant memory → model correctly ignores it
- Turns with no memory retrieved → model reasons from game state alone

This maps to existing evaluation infrastructure:
- Strategy attribution pipeline → labels which strategies agents used
- Win/loss tracking → filters for winning turns with correct application
- Memory retrieval traces → constructs (context + memories → action) pairs

## Risks

1. **Catastrophic forgetting:** Fine-tuning for style can degrade reasoning. Must monitor decision quality (win rate, strategy attribution) alongside dialogue quality.
2. **Evaluation is subjective:** No F1 score for "sounds natural." Need LLM judge or human eval, both noisy.
3. **Structured output failures:** Model may produce invalid JSON, wrong field types, or hallucinated memory indices. Need validation layer.
4. **Overfitting:** 500-2000 examples with a 120B model risks memorization. May need to tune epochs carefully (1-2 instead of 3).

## Validation Before Training

Before committing to dataset creation, run a few game turns through the **base** GPT-OSS 120B (no fine-tuning) to check:
- Can it produce valid structured output matching the Pydantic schema?
- Does it handle the 4.5K context without quality degradation?
- What's the baseline dialogue quality vs flash-lite?

If the base model can't even produce valid structured output, fine-tuning it for this task is unlikely to work.

## Status

Exploratory. Depends on:
- Dedup fine-tuning results (Projects 1-2) — proves the fine-tuning workflow
- Base model validation — confirms GPT-OSS 120B can handle structured output
- Dataset creation investment — bottleneck is generating high-quality training examples
