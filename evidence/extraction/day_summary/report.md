# Day Summary — how it works today

**Orientation.** At the end of each day's discussion, before the vote, one LLM call condenses that day's
public talk into a **structured summary**: accusations, role claims, alliances, and village dynamics.

It exists for two reasons. First, it **bounds the context**: without it, every later day would re-feed the
full raw transcript of every earlier day, so the prompt would swell as the game runs on. Summarizing caps
each past day at a fixed-size digest, and only the current day is ever shown raw. Second, it **turns dialogue
into signal**: a raw discussion is mostly repetition, hedging, and social texture, so a structured extract of
the load-bearing facts is cheaper and cleaner for a downstream model to read than the transcript.

That is why the summary is the *only* representation of a past day any agent ever sees again: raw transcripts
are never re-shown. So the component runs on a two-channel design, and that split is the thing to hold onto:

```
day discussion ─▶ LLM structured summary ──┐
                                            ├─▶ day_summaries ─▶ { agent prompts · situation-summary query · post-game extraction }
vote resolution ─▶ game-master vote result ┘   (the only record a later day gets)
```

- The **LLM summary** carries the *argumentative* content: who accused whom and why, who claimed what, how
  the village aligned.
- The **game-master vote-result message** carries the *hard facts*: the full vote tally (voter→votee), the
  elimination, and the death-revealed role. It is written deterministically at vote resolution, independent
  of the LLM.

Both are appended to `day_summaries`, so a later day reads both. This doc is the current truth of how that
runs; the path that got here is [experiment_log.md](experiment_log.md), and the measurement apparatus (the
quality judge) is written up in [../../evaluation/llm_judge/day_summary.md](../../evaluation/llm_judge/day_summary.md).

## What it captures (current schema)

The LLM emits `DaySummaryOutput` ([output.py:125-161](../../../Agents/schemas/output.py#L125-L161)) via
structured output, and a deterministic serializer flattens it back into the plain-text block agents read
([summary_agent.py](../../../Agents/nodes/day/summary_agent.py)):

- **`accusations`** — one entry per distinct accusation, each listing *all* accusers, the target, the
  reasoning, an `evidence_type` label, and any defense.
- **`role_claims`** — who claimed which role, with a certainty note (death-revealed = confirmed fact,
  publicly corroborated, or unverified).
- **`alliances`** — voting blocs and the basis they formed on.
- **`village_dynamics`** — three prose fields: `information_landscape`, `consensus`, `drivers`.

The structured record is persisted alongside the prose for the post-game tagger and credit logic; agents
themselves see only the serialized prose, so nothing about the structured fields changes gameplay.

## Guarantee / contract (present-tense)

- **Hard facts are backstopped, not entrusted to the LLM.** The vote tally, the elimination, and the
  death-revealed role reach later days through the game-master message, written both to `day_channel` and as
  its own `DaySummary` at vote resolution ([orchestrator.py:185-241](../../../Agents/nodes/orchestrator.py#L185-L241)).
  A summary miss cannot lose them.
- **Structured output forces enumeration.** Each accusation is a separate `Accusation` entry, so a pile-on's
  participants are far less likely to be silently merged away than in free text.
- **Serialization is deterministic.** `_serialize_day_summary` produces a fixed text shape, so every
  downstream consumer gets the same format regardless of which model wrote the summary.
- **It runs in both memory arms.** The summary is computed before any memory retrieval, so it is identical on
  the memory-on and memory-off arms, and it emits a judgeable `DaySummaryCase` for the quality judge.
- **What is NOT guaranteed.** Downstream *sufficiency* (the judge grades intrinsic quality, not whether an
  omission changes a decision); v6-dimensional *currency* (the component still runs on the v5 situation
  framework); judge *calibration* (no human answer key sits behind the scores). See the gaps table.

## The mechanism / model

- **Node.** `summarize_day_discussion` ([flow.py:203-276](../../../Agents/nodes/day/flow.py#L203-L276)) reads the
  day's non-game-master messages (no-op if none), wraps the call in a `DaySummaryCase` eval span, and writes
  the result into `day_summaries`.
- **Agent.** `run_day_summary_agent` ([summary_agent.py](../../../Agents/nodes/day/summary_agent.py)) calls the
  model with structured output, retries once, and falls back to the raw formatted channel on repeated failure.
- **Model.** flash-lite with **medium thinking** (`get_llm_summary`,
  [accessors.py:64](../../../Agents/llm_factory/accessors.py#L64); `DEFAULT_SUMMARY_THINKING_LEVEL="medium"`,
  [accessors.py:19](../../../Agents/llm_factory/accessors.py#L19)). The thinking budget, not a larger model, is
  what removed the two worst failure modes (see Verification).
- **Prompt.** `DAY_SUMMARY_PROMPT` ([extraction/day_summary.py](../../../Agents/prompts/extraction/day_summary.py))
  composes the v5 `SITUATION_STANDARDS` and the game rules. It tells the model to exclude the formal tally
  (recorded separately), to keep in-discussion vote references and declarations, and to grade role-claim
  certainty by tier.

## Config / defaults

| Setting | Value | Where |
|---|---|---|
| generation model | flash-lite | `get_llm_summary` (accessors.py:64) |
| thinking budget | medium | `DEFAULT_SUMMARY_THINKING_LEVEL` (accessors.py:19) |
| output | structured `DaySummaryOutput` → deterministic serialize | summary_agent.py |
| situation framework | v5 `SITUATION_STANDARDS` | extraction/day_summary.py |
| retries | 1, then raw-channel fallback | summary_agent.py |

The old 400-word limit is effectively moot: the model writes ~130-230 words regardless (experiment_log §3).

## Verification

**Verdict.** The quality judge is a **smoke test, not a metric**. It reliably catches gross failures but
cannot rank near-equal prompts, and neither design decision that shipped was made on its scores.

The judge (gemini-2.5-pro, reference-based: it sees the transcript *and* the summary) scores five 1-5
dimensions, and they split by whether the judge can check them against the transcript.

- **Grounded trio: `completeness`, `accuracy`, `epistemic_correctness`.** These move, and they caught the
  real failures. A fabricated game-master announcement, dropped accusers, and confirmed-vs-claimed role errors
  all surfaced as 1-3 scores. Useful as a floor alarm.
- **Presence-check pair: `village_dynamics` (5.00 in every run) and `evidence_type_clarity` (4.89-5.00).**
  The prompt *forces* these sections to exist, so the judge almost always sees them and scores near the
  maximum. A gauge that never moves carries no information.

At n=18 with a single run per pair, per-pair scores swing ±1 and no prompt version is statistically
distinguishable. So the two shipped decisions rest on other grounds:

- **Format (structured over free-text)** was an architectural call: deterministic serialization, forced
  enumeration, and fields that later code can parse.
- **Model (flash-lite + medium thinking)** was a latency-and-inspection call. 2.5-pro scored highest but took
  ~120 min for 18 pairs, while medium thinking matched it on the dimensions that matter at flash-lite latency
  and removed the hallucination and dropped-accuser failure modes.

**What is measured, and what is deliberately not.** The judge grades *intrinsic fidelity* — whether the
summary accurately captures the day's critical information categories (accusations, role claims, vote
actions, dynamics). It does *not* measure downstream game outcome, and that is by design, not a shortfall:
tying summary quality to who won would make this a credit-assignment objective, which is the wrong question
for a summarizer and far less controllable than fidelity to the defined categories. The honest residual is
only that we don't test whether a *specific* omission changed a *specific* decision. The full apparatus
write-up, including the saturation mechanism and the calibration gap, is
[../../evaluation/llm_judge/day_summary.md](../../evaluation/llm_judge/day_summary.md).

**What it can't do.** The judge can flag a bad summary but cannot certify a good one as "good enough for
downstream," because it has no human anchor and never tests the downstream effect.

## Current-vs-documented gaps (freshness: 2026-07-01)

Ordered by how misleading each is to a reader. Severity weighs likelihood, impact, and detectability
together, not impact alone.

| # | Gap | State | Severity |
|---|---|---|---|
| 1 | **v6-dimensional currency** | The component still composes the v5 `SITUATION_STANDARDS`. Extraction and the situation-summary query moved to the v6 dimensional schema, and day-summary was left last-and-optional in the v6 migration. Whether a v5-framework summary supplies enough for the v6 consumers is unmeasured, but narrow: the per-agent and board dimensions are re-derived or computed deterministically, so they need not live in the summary. | Med |
| 2 | **Uncalibrated judge** | No human answer key sits behind the scores; the single judge is the sole authority. It is a *secondary* instrument, so calibration has stayed deprioritized. | Med |
| 3 | **Downstream impact not measured (by design)** | The judge grades intrinsic fidelity, not whether an omission changes a decision or query. This is intentional, not a shortfall: outcome-based measurement would be a credit-assignment objective, the wrong target for a summarizer. The bounded residual — a *specific* omission's effect on a *specific* decision — is further backstopped by the game-master channel, and day-summary is **not a measured bottleneck** (the binding limits are content quality and investigator transmission, the v6 A/B). | Low |
| 4 | **Structured record now persisted** | The full structured output is persisted alongside the prose for the post-game tagger and credit (a 2026-06-20 live-path change); agents still read only the prose. | Low |

**Open work.** The one credible upgrade is to calibrate the grounded trio against a small human golden set on
a few hard pairs, and to decouple regeneration from judging so judge-noise can be sized apart from
generation-noise. Neither is a priority while day-summary is not the binding constraint.
