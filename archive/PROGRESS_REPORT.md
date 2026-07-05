# Progress Report: Memory System Integrity in Agentic Werewolf Simulation

## Project Context

This project implements a multi-agent Werewolf game simulation where LLM-powered agents develop strategic memory through repeated gameplay. The system uses a **retrieval-augmented generation (RAG) pipeline** for agent memory: post-game extraction captures strategic observations and tactical principles, which are stored in a vector-indexed memory store and retrieved via semantic search during future games to inform agent decision-making.

The memory pipeline consists of three stages:
1. **Extraction** -- An LLM analyzes the full game transcript post-game and produces structured observations (episodic memory) and strategy points (tactical principles), each tagged with a role perspective and game phase.
2. **Deduplication** -- Each new extraction is compared against the most similar existing entries via embedding similarity search. An LLM judge decides whether to DISCARD (duplicate), REPLACE (improved version), DIFFERENTIATE (same situation, different action), or KEEP (novel entry).
3. **Retrieval** -- During gameplay, agents generate situation summaries of their current game state. These summaries are used as semantic search queries to retrieve the most relevant stored observations and strategy points.

---

## Problem: Hallucination and Semantic Drift in the Memory Pipeline

During evaluation of memory quality after multiple game cycles, we identified systematic integrity failures at two points in the pipeline:

### 1. Hallucination During Deduplication Rewrites

The dedup stage allowed the LLM judge to rewrite entries during KEEP decisions (supposedly "minor wording improvements"). In practice, the model fabricated dimensional context that was not present in the source extraction:

**Original extraction:**
> Situation: "When you have been saved by the healer, granting you high social trust without revealing your specific role."

**After KEEP rewrite:**
> Situation: "In the mid-game, you are a player who has been saved by the healer, establishing you as a confirmed non-wolf to the village without revealing your specific role. This creates a high-trust information landscape where your voice carries significant weight, but you remain a target for wolves who want to eliminate confirmed villagers."

The rewrite invented "mid-game," "high-trust information landscape," and "target for wolves" -- none of which were grounded in the source game data. This is a form of **confabulation** where the model generates plausible-sounding but ungrounded context to match a quality template.

This is particularly damaging because the fabricated details persist in the memory store and influence future retrieval. A hallucinated "mid-game" label causes the entry to be retrieved for mid-game situations and missed for early/endgame situations where it might equally apply.

### 2. Situation-Action Boundary Violation in Extraction

The extraction model frequently embedded strategic recommendations inside the `situation` field, which is designed to describe observable game state for semantic search matching:

> Situation: "You have obtained crucial investigation results but must remain hidden to avoid becoming an immediate target for the wolves. The optimal strategy depends on the nature of your findings: if you have a guilty read, you must guide the discussion using publicly available information..."

The bolded portion is action content that belongs in the `action` field. When strategy leaks into the situation field, it degrades retrieval precision -- the entry matches on strategic keywords rather than game-state dynamics.

### 3. Epistemic Status Violations

The extraction model frequently described game situations using omniscient ground truth rather than the information actually available to the assigned role:

> "A wolf was being targeted by the Investigator" (strategy point for wolf perspective)

In a live game, the wolf doesn't know their accuser is the Investigator. This phrasing would never match a real game-state query where the wolf describes their situation as "a player is aggressively accusing me." The epistemic mismatch between stored entries and runtime queries degrades retrieval recall.

---

## Solution: Structured Dimensional Enforcement and Pipeline Hardening

### 1. Schema-Level Dimensional Fields (Structured Output Enforcement)

Rather than relying on the LLM to naturally embed dimensional context in free-text situation descriptions, we introduced **dedicated schema fields** on the Pydantic extraction models:

```python
class StrategyPoint(BaseModel):
    situation: str          # Core game dynamic only
    information_landscape: str   # Required -- evidence type and richness
    game_phase: str              # Required -- early/mid/endgame
    consensus_texture: str | None  # Optional
    social_pressure: str | None    # Optional
    action: str
```

A `composed_situation` property concatenates these fields into the final stored string. This enforces two properties:
- **Completeness** -- The model must explicitly populate `information_landscape` and `game_phase` for every entry, eliminating the inconsistency where observations had dimensional context but strategy points did not.
- **Grounding** -- The dimensional fields are populated at extraction time when the model has full game context, rather than at dedup time when the model is working from truncated text fragments.

This approach leverages **structured output** (constrained decoding against a JSON schema) to enforce data quality at the schema boundary rather than relying on prompt instructions alone.

### 2. Elimination of KEEP Rewrites (Immutable Extraction Outputs)

We removed the rewrite capability from KEEP decisions entirely:
- Removed `new_rewritten_situation` and `new_rewritten_action` fields from the `Keep` and `ObservationKeep` Pydantic schemas
- Updated the storage handler to pass the original extraction through without modification
- Updated the prompt to state: "The new entry is stored exactly as extracted with no rewrites"

This makes KEEP a **pure classification decision** with no generative component, eliminating the hallucination surface.

### 3. Input-Bounded Rewrites for REPLACE and DIFFERENTIATE

For dedup decisions that require rewriting (REPLACE merges two entries; DIFFERENTIATE rewrites both situations to make a distinguishing variable explicit), we added an explicit constraint:

> "Rewrites must only use details present in the entries being compared. Do not infer or invent game phase, information landscape, consensus texture, social pressure, or any other context not explicitly stated in the input entries."

Since the extraction stage now embeds dimensional context via structured fields, the dedup model has sufficient material to work with for DIFFERENTIATE rewrites without needing to fabricate additional context.

### 4. Separated Epistemic Status Rule with Graded Certainty Spectrum

We extracted the epistemic status rule from `SITUATION_STANDARDS` into a standalone `EPISTEMIC_STATUS_RULE` that can be selectively injected:
- **Injected for**: strategy point extraction, strategy point dedup, batch strategy dedup
- **Not injected for**: observation extraction (god's perspective is valid), observation dedup, situation summaries (agent naturally doesn't know hidden roles)

The rule was rewritten to define a **five-tier certainty spectrum** rather than a binary known/unknown distinction:

1. **Own role and private findings** -- the agent's direct knowledge (e.g., investigator knows their findings)
2. **System-confirmed** -- role revealed by game mechanics (elimination, healer save)
3. **Claimed with strong evidence** -- public claim backed by corroborating events
4. **Claimed with no evidence** -- unvalidated role claim
5. **Unknown** -- behavioral descriptors only

This spectrum prevents over-correction (e.g., blocking an investigator from referencing their own findings) while still catching omniscient narration.

### 5. Prompt Centralization and Dead Code Removal

During the refactor, we discovered duplicated prompt definitions -- `PER_EXTRACTION_DEDUP_PROMPT` existed both in `prompts/dedup.py` and inline in `memory_deduplication.py`, with the inline copy being the one actually used. We:
- Moved `OBSERVATION_DEDUP_PROMPT` to `prompts/dedup.py` (previously only existed inline)
- Deleted all inline prompt copies from `memory_deduplication.py`
- Removed the unused `BATCH_DEDUP_PROMPT` (superseded by cluster-based variants)
- Updated imports to use the canonical prompt location

---

## Results After 3 Games

### Dimensional Field Compliance
- `information_landscape` and `game_phase` populated on every extraction
- `consensus_texture` and `social_pressure` correctly omitted when not relevant
- No fabricated dimensional context in stored entries

### Epistemic Rule Compliance
- Strategy points correctly use the assigned role's perspective
- Investigator entries reference own findings directly ("If you have successfully identified a wolf")
- No omniscient narration in strategy points (e.g., no "the Investigator was arguing with a wolf" from villager perspective)

### Dedup Quality
- KEEP decisions store originals without modification
- DIFFERENTIATE decisions produce clean rewrites grounded in input entries (e.g., splitting investigator strategy into "covert guidance when safe" vs. "overt reveal when under threat")
- REPLACE decisions merge without adding hallucinated context

### Memory Store Health
- 8 observations and 8 strategy points per game extracted across 4 roles
- Natural dedup reducing redundancy (e.g., 2 "Night 1 target selection" observations merged into 1 with observation_count=2)
- Strategy point namespaces showing healthy differentiation (wolf/day_discussion has 5 entries covering distinct tactical scenarios)

---

## Technical Patterns and Takeaways

### Schema Boundaries as Quality Gates
The most effective intervention was moving quality enforcement from prompt instructions to schema constraints. Free-text prompts asking the model to "use the dimensional framework" produced inconsistent compliance. Dedicated Pydantic fields with `Field(description=...)` produced near-perfect compliance because structured output decoding constrains the generation at the token level.

**Design principle**: When a data quality property must hold reliably, encode it as a schema constraint rather than a prompt instruction. Prompts are suggestions; schemas are contracts.

### Minimizing the Generative Surface of Classification Pipelines
The dedup pipeline is fundamentally a **classification task** (DISCARD/REPLACE/DIFFERENTIATE/KEEP) with an optional generative component (rewriting entries). The hallucination occurred exclusively in the generative component. By removing generation from the KEEP path and constraining generation in the REPLACE/DIFFERENTIATE paths to input-bounded rewrites, we preserved classification accuracy while eliminating confabulation.

**Design principle**: In multi-stage agentic pipelines, audit each stage for unnecessary generative surface. If a stage's primary function is classification or routing, minimize or eliminate any generative side-effects.

### Epistemic Alignment Between Storage and Retrieval
The epistemic status violations created a **query-document mismatch** -- entries were stored using omniscient language but queried using the agent's limited in-game perspective. This is analogous to the **indexing-query distribution gap** in traditional information retrieval. The fix was ensuring both sides of the semantic search use the same epistemic frame.

**Design principle**: In RAG systems, the stored documents and the runtime queries must share the same "voice" and information assumptions. A mismatch in perspective, terminology, or abstraction level degrades retrieval even when the underlying semantics are similar.

### Composition Over Prompt Repetition
Rather than asking both the extraction model and the dedup model to independently produce situation-standards-compliant text (with the dedup model having less context and therefore hallucinating), we structured the pipeline so that dimensional composition happens exactly once at the extraction boundary, where the model has full game context. Downstream stages consume the composed output.

**Design principle**: In multi-agent pipelines, assign generative responsibilities to the stage with the richest context. Downstream stages should transform, classify, or route -- not regenerate.
