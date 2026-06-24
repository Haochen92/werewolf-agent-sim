# Discussion-quality gate — concurrent vs sequential (study record)

> **The durable verdict** — *sequential clears the bar; Phase A #1 closes* — is carried destination-first
> in [`../report.md`](../report.md) §3–4. **This file is the full study record behind it:** the method, the
> deterministic metrics, the dimension-by-dimension read, and the honest caveats.

**Date:** 2026-06-05 · **Closes:** Phase A #1 (sequential day discussion)
**Method:** hand-judged A/B over transcripts, against [rubric.md](rubric.md). Deterministic
metrics from [scripts/metrics.py](scripts/metrics.py). No LLM judge.

## TL;DR — verdict

**Sequential clears the bar. Adopt it; Phase A #1 closes.** The core win is *structural*
and shows in every game: concurrent fan-out makes agents speak **blind to each other in the
same round**, producing redundant parallel monologues (worst at the day-1 opener and at any
shared accusation); the sequential scheduler conditions each turn on prior ones and **forces
the addressed agent to answer next**, yielding real back-and-forth. Concurrent is not
*broken* (it still converges and wins games when evidence is strong), but it reads as
parallel monologues where sequential reads as a conversation.

Confidence: **HIGH on the structural dimensions** (redundancy, responsiveness, dogpile shape)
— these are architectural and reproduced across all 8 games. **LOW on any quantitative delta**
— N=4/arm; numbers below are descriptive, not significant.

## What was compared (pinned except the design)

| | Sequential (this gate) | Concurrent (frozen, on disk) |
|---|---|---|
| Source | fresh runs, `data/gate_sequential.jsonl` | `werewolf_flashlite_3_v1*.jsonl` |
| Model | gemini-3.1-flash-lite | gemini-3.1-flash-lite (same family) |
| Memory | v4_deduped_v2; 2 off + 2 on | mem-off (v1) + mem-on (v1_deduped) |
| N | 2 mem-off + 2 mem-on | 4 mem-off + 4 mem-on |

Caveat (acceptable): concurrent's backend/temp/memory-store aren't recorded, so this is a
**structural/qualitative** comparison, not a pinned quantitative A/B. The parroting failure
mode is architectural and model-independent, so existing concurrent games are valid evidence
for it. (Pinned fresh concurrent runs were deemed unnecessary cost — the worktree exists at
tag `concurrent-baseline` if a quantitative pass is ever wanted.)

## Deterministic metrics (auditable; [scripts/metrics.py](scripts/metrics.py))

`echo_rate` = frac of a day's messages ≥0.60 lexically similar to an earlier message that day
(a **lower bound** on redundancy — misses paraphrase). `max_share` = top speaker's share of a
day; `max_consec` = longest same-speaker run.

| Condition | echo_rate | same-round echoes | max_share | max_consec | utt/day |
|---|---|---|---|---|---|
| **SEQ** mem-off | **0.00** | **0** | 0.25 | 2.00 | 17.0 |
| CONC mem-off | 0.06 | 8 | 0.22 | 2.08 | 13.0 |
| **SEQ** mem-on | **0.00** | **0** | 0.26 | 2.00 | 15.9 |
| CONC mem-on | 0.05 | 8 | 0.21 | 2.00 | 16.6 |

Read: sequential has **zero** lexical echo in both conditions; concurrent has consistent
same-round echo (16 instances over 8 games), concentrated on day 1. Turn-fairness and volume
are **comparable** — concurrent is *not* pathological on domination (its round-robin is in
fact marginally more even, by construction). The win is **robust to memory** (echo pattern
identical on/off).

## Dimension-by-dimension

### 1. Redundancy / parroting — **sequential better (HIGH confidence)**
Concurrent, mem-off game 3, **day 1, round 1** — 8 players, blind, near-identical openers:
> player_2: "…Does anyone have any initial thoughts on how we should handle the first vote?"
> player_5: "…Does anyone have any initial thoughts on who to look out for?"
> player_6: "…Does anyone have any initial leads or thoughts?"
> player_7: "…Does anyone have a theory on who we should look at first?"
> player_8: "…Does anyone have any initial thoughts on who to look out for…?"

Concurrent, day 3, round 2 — **four** blind near-identical accusations in one round:
> player_1/player_5/player_6/player_7 each: "Player 3, you're still avoiding/ignoring the
> question — why did you vote for a villager?" (×4, same round)

Sequential, mem-off game 1, **day 1** — conditioned, each turn references the last:
> s1 player_2 →player_5/agreement: "I agree with player_5. It is way too early…"
> s2 player_8 →player_5,player_2: "It's understandable to be cautious, **but** waiting too long…"
> s3 player_3 →player_8/agreement: "…**but player_8 makes a good point** about not staying silent."

Sequential echo_rate is 0.00; the lexical metric *undercounts* concurrent (the day-1 openers
are semantic dups it scores below 0.60). Structural and decisive.

### 2. Responsiveness — **sequential better (HIGH confidence)**
Sequential's reactive obligations force the addressed agent to answer **next**:
> s4 player_7 →player_2/accusation … → s5 player_2 **[reactive→owes player_7]** →player_7/defense
> s10 player_3 →player_2/accusation … → s11 player_2 **[reactive→owes player_3]** →player_3/defense

The player_5↔player_4 exchange (day 2, s14-s17) is genuine interleaved rebuttal. In concurrent,
the accused answers only **once per round-end**, after absorbing the whole round's hits
(player_3 responds at r2/r3/r4, each after 4 simultaneous accusations). Answers do eventually
come, but delayed and decoupled from individual accusers.

### 3. Dogpiling — **sequential better (MEDIUM-HIGH)**
Concurrent dogpile is **redundant by construction**: 4 agents hit the same target with the
same point in one blind round (day 3 above). Sequential pressure is **interleaved and bounded**
(per-pair K-cap): player_5 is pressed hard on day 2 (≈7 turns) but answers each accuser in
turn — reads as a defendant under fair questioning, not a redundant pile. *Caveat:* sequential
can still concentrate scrutiny on one player; it's bounded and responsive, not eliminated.

### 4. Turn-fairness — **no clear winner (MEDIUM)**
Comparable. Concurrent's round-robin is marginally more even (max_share 0.21-0.22 vs
0.25-0.26) but that evenness is *forced* — everyone must speak each round even with nothing to
add, which directly feeds the parroting. Sequential's distribution is need-based (max_consec 2,
max_share ≤0.35), healthy. No domination problem in either.

## Steelman / honest caveats
- **Concurrent is not broken.** With concrete evidence (a confirmed wolf) it converges and
  wins (day 3 example → correct lynch). The gate is "does sequential read *better*", and it
  clearly does — but this isn't "concurrent fails."
- **N is small.** All quantitative numbers are descriptive. The verdict rests on the
  *structural* dimensions, which don't need N.
- **Judge = the implementer.** Bias mitigated by (a) deterministic metrics, (b) verbatim
  excerpts above so any call is auditable, (c) explicit steelman. Excerpts are reproducible
  from the dumped transcripts.

## Decision
**Adopt sequential. Phase A #1 closes.** Unblocks Phase A #2 (roles), #3 (tracing), #4 (night
memory), #5 (v5 DB).

## Future work (post-MVP — none blocks shipping the sequential design)
Ordered roughly by value. All deferrable; the sequential design ships as-is.
1. **`current_round` → `seq` cleanup (v5).** The day path zeroes `current_round` (vestigial);
   `EvalCase.round`, `situation_summary` run-names, and `formatters` still reference `round`, so
   day-phase eval cases label as `round_0`. Replace with `seq`. (Already on the v5 backlog.)
2. **Eval-data schema shim.** `DayChannel.seq` is required, so old discussion-bearing eval cases
   won't deserialize. Add a `seq` default / migration validator — *only* needed if we replay
   pre-rebuild eval data; moot once v5 regenerates golds.
3. **Wolf-night discussion → sequential.** Night discussion still uses the old concurrent 2-round
   model. Applying the same reactive/proactive scheduler would bring the same coherence win and
   remove the last `round`-based code path.
4. **Novelty-gate hardening.** Judge strictness is currently lenient; consider a cheap
   embedding pre-filter before the LLM gate (cuts cost on echo-heavy days). See experiment_log
   "Tuning results".
5. **Scheduler tunable sweep.** `per_pair_reengagement_cap`, `proactive_budget`, `opener_floor`,
   `reengagement_cooldown_multiplier` were set by hand during tuning — a small grid sweep could
   confirm the defaults.
6. **Dialogue-style fine-tuning** (optional, Phase 4 of the FT plan) — fine-tune for natural
   turn-taking once the rest of the rebuild lands.
7. **Quantitative A/B (only if ever needed).** This gate is structural/qualitative. If a
   defensible *number* is ever required (e.g. for an external audience), run pinned fresh
   concurrent games from the `concurrent-baseline` tag worktree + a win-rate / judged A/B.

## Incidental fixes made during the gate (committed separately)
- `run_batch.py` now dumps `day_channel`/`day_summaries` (was dropping the transcript →
  records had no discussion to judge).
- `create_embeddings` wrapped with transient-error retry/backoff
  (`_RetryingGoogleGenerativeAIEmbeddings`) — the runtime retrieval-query embedding had no
  retry, so a single 429 aborted a mem-on game.
