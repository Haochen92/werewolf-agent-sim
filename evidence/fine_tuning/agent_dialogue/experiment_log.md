# Fine-Tuning: Agent Dialogue Distillation

## Motivation

Current werewolf agents running on flash-lite produce functional but bland, repetitive dialogue. They tend to get aggressive early, harp on tone/style rather than substance, and lack conversational variety. Upgrading to flash-3.5 would improve quality but increases cost from ~$0.20 to ~$1-2/game (5-10x), with day discussion accounting for ~80% of the ~160 generation calls per game — making a hybrid approach (strong model for discussion only) nearly as expensive as a full upgrade.

Fine-tuning an open-source 8B model specifically for werewolf dialogue could match or exceed flash-lite quality at ~10x lower inference cost, while avoiding the recurring API cost of a stronger model.

## Feasibility Analysis (2026-05-27)

### Why 8B might be sufficient

The werewolf domain is highly constrained compared to general-purpose language tasks:
- English only (no multilingual)
- Text only (no multimodal)
- 4 roles, 3 game phases, 5-7 players
- Fixed game mechanics, limited action space
- No world knowledge, code, math needed

A fine-tuned 8B with all capacity focused on one game is fundamentally different from a general-purpose 8B. Precedent: 7B models fine-tuned for chess, SQL, medical diagnosis — werewolf dialogue is narrower than any of these.

The reasoning ceiling of 8B is the main risk — the model may speak more naturally but make worse strategic decisions than flash-lite. However, in a game where the "right" move is often ambiguous, the ceiling may not matter as much.

### Two separable problems

1. **Dialogue style (easier):** Teach natural, human-like werewolf speech patterns — accusations, deflections, coalition-building, humor. Trainable via distillation from a powerful model or from real mafia/werewolf game transcripts (forums, Discord, YouTube). Style patterns are learnable and the output is somewhat subjective.

2. **Decision quality (harder):** Improving strategic reasoning. Fine-tuning can't exceed the base model's reasoning capacity — it can only better utilize it within the domain. Better context at inference time (memory pipeline) and better prompts may be more effective than fine-tuning for this.

Recommendation: fine-tune for style, improve decisions via pipeline (memory/retrieval).

### Cost analysis

#### One-time costs

| Component | Cost | Notes |
|-----------|------|-------|
| Dataset generation | ~$0-20 | Use Claude/GPT subscription plans for batch generation |
| Training compute (Together LoRA) | ~$5 | $0.48/1M training tokens for 8B LoRA |
| Human time | 2-4 weeks | Dataset curation is the bottleneck |
| **Total** | **~$5-25** | |

#### Inference cost comparison (500K input / 50K output per game)

| Option | Cost/game | Notes |
|--------|-----------|-------|
| Gemini 3.1 Flash-lite (current) | ~$0.20 | Bland dialogue, functional decisions |
| Gemini 3.5 Flash | ~$1-2 | Better everything, 5-10x cost increase |
| Fine-tuned 8B on Together LoRA | ~$0.10 | $0.18/1M tokens, no hosting fee, no cold starts |
| Fine-tuned 8B on RunPod serverless | ~$0.05-0.09 | Cheapest, but cold starts + operational overhead |
| Dedicated GPU (T4, ~$290/month) | fixed | Only makes sense at 200+ games/month |

**Key distinction:** Cheap per-token rates on Groq ($0.05/1M) and DeepInfra ($0.02/1M) only apply to shared base models. Custom LoRA adapters require either GPU-hour billing (DeepInfra) or aren't supported (Groq). Together AI is the only provider serving custom LoRA adapters at base model per-token rates with no hosting fee, no cold starts, no idle cost.

**CPU hosting is not viable for game dialogue.** At 500K input tokens per game, CPU inference (10-30 tokens/s) would take 6-13 hours per game. CPU VPS ($20/month) only works for small-context tasks like the dedup classifier (~2K input tokens).

#### Breakeven

| Replacing | Savings/game | One-time cost | Breakeven |
|-----------|-------------|---------------|-----------|
| Flash-3.5 | ~$1.40 | ~$25 | ~18 games |
| Flash-lite | ~$0.10 | ~$25 | ~250 games |

Breakeven vs flash-lite is marginal on cost alone — the case is quality improvement, not savings.

### Dataset strategy

**Primary sources for dialogue style:**
- Distillation: have a powerful model (Claude/GPT via subscription) play or rewrite hundreds of werewolf games with natural dialogue
- Real transcripts: mafia/werewolf forum posts, Discord logs, YouTube game transcripts — teach authentic human speech patterns
- Existing game logs: rewrite current agent dialogue with a more powerful model

**For decision quality (if attempted):**
- Would need game state → optimal action pairs, much harder to label
- Better addressed via pipeline improvements (memory, retrieval, strategy application)

**Volume needed:** ~500-1000 game turns with full context (game state, role, other messages) → model response

### Risks

- **Catastrophic forgetting:** fine-tuning for style can degrade reasoning. Need to monitor decision quality alongside dialogue quality.
- **Evaluation is subjective:** no F1 score for "sounds natural." Need LLM judge or human eval, both noisy.
- **Generalization:** training data covers specific game states. Model needs to handle novel situations — over-fitting to training dialogues is a risk.

## What "Good Decisions" Means (2026-05-27)

Decision quality in this system has two distinct capabilities:

**1. Baseline reasoning (no memory):** The model can independently make a reasonable move using only the current game state — role prompt, dialogue history, game events. This is the model's own reasoning floor. A fine-tuned model should match or exceed flash-lite here within the constrained werewolf domain.

**2. Memory-augmented reasoning:** The model can assess retrieved memory inputs, judge their applicability to the current situation, and apply relevant memories to improve its decision — or recognize when memories aren't relevant and fall back to independent reasoning. This is the harder capability and the whole point of the memory system.

### Context the agent works with (at each decision point)

1. **Role prompt (static):** Fixed per role. General high-level play strategy, role-specific guidelines.
2. **Retrieved memories (dynamic):** Observations and strategy points retrieved from the episodic memory store each turn based on situation similarity.
3. **Dialogue and game events (ephemeral):** All messages, votes, eliminations, role reveals from the current game.

Context window size matters — a fine-tuned 8B model has a smaller effective context than Gemini flash models. The training data needs to reflect realistic context lengths, and the model needs to learn which parts of a large context to attend to.

### Implication for training data

The fine-tuned model needs training examples that cover both capabilities:
- Turns with no relevant memory retrieved → model reasons from game state alone
- Turns with relevant memory → model correctly applies the memory
- Turns with irrelevant memory retrieved → model correctly ignores it

This maps directly to existing evaluation infrastructure:
- **Strategy attribution pipeline** → labels which strategies agents used → identifies "good application" examples
- **Win/loss tracking** → ties outcomes to behaviors → filters for winning turns with correct strategy application
- **Memory retrieval traces** → show what context the agent had → constructs (context + memories → action) training pairs

The evaluation pipeline built for Projects 1-2 is effectively a data flywheel for Project 3's training dataset. Each component produces artifacts that become training signal.

## Resource strategy: GCP free trial credits

Google Cloud free trial ($300/account) is best used for:
- **Batch game generation with strong models** — run 150-300 games with flash-3.5 or pro at $1-2/game. This produces the high-quality decision examples that can't be justified at own expense.
- Multiple free trial accounts can be spread across training (one) and game generation (another).
- GCP Vertex AI training with A100 (~$3-4/hr) is available but Modal is simpler for QLoRA.

## Dependencies

- Dedup classifier fine-tuning (Project 1) should be complete first — proves the fine-tuning workflow
- Embedding fine-tuning (Project 2) should be complete or in progress
- Memory pipeline improvements provide better context regardless of dialogue model
- Strategy attribution pipeline maturity — needed to label "good decisions" in training data
- Win/loss tracking — needed to filter training examples by outcome

## Status

Exploratory. No execution planned until Projects 1 and 2 are complete. This analysis scopes feasibility, economics, decision quality framework, and data pipeline connections for planning purposes.
