# Discussion-quality gate — concurrent vs sequential (study record)

> **The durable verdict** — *sequential clears the bar; Phase A #1 closes* — is carried destination-first
> in [`../report.md`](../report.md) §3–4. **This file is the full study record behind it:** the method, the
> deterministic metrics, the dimension-by-dimension read, and the honest caveats.

**Date:** 2026-06-05 · **Closes:** Phase A #1 (sequential day discussion)
**Method:** hand-judged A/B over transcripts, against [rubric.md](rubric.md) — a **human**
scoring guide, not an LLM-judge prompt (see its header). Deterministic metrics from
[scripts/metrics.py](scripts/metrics.py). **Nothing LLM grades this gate.** (Distinct from the
scheduler *under test*, which uses a runtime LLM novelty gate — that's part of the design being
evaluated, not the evaluation of it.)

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

| Condition | echo_rate | max_share | max_consec | utt/day |
|---|---|---|---|---|
| **SEQ** mem-off | **0.00** | 0.25 | 2.00 | 17.0 |
| CONC mem-off | 0.06 | 0.22 | 2.08 | 13.0 |
| **SEQ** mem-on | **0.00** | 0.26 | 2.00 | 15.9 |
| CONC mem-on | 0.05 | 0.21 | 2.00 | 16.6 |

*The fairness columns count **turns, not airtime or influence** — they detect concentration/domination,
not fairness in a richer sense; distinct-speaker coverage is computed but not tabled, so the rubric's "no
silent survivors" axis is a **judged** call here, not a measured one.*

Read: sequential has **zero** lexical echo in both conditions; concurrent shows a consistent low
rate (0.05–0.06). The cross-arm echo comparison is **`echo_rate`** above.

> **`same_round_echoes` is a concurrent-only diagnostic, not a cross-arm metric.** It counts echoes that
> fall in the *same blind round*: **16 over the 8 concurrent games, day-1-concentrated**, localizing
> concurrent's pathology to the blind parallel fan-out. Sequential has no rounds, so it doesn't apply —
> the figure characterizes *where* concurrent's echo lives, not a delta between the arms. The cross-arm
> echo metric is `echo_rate`.

Turn-fairness and volume are **comparable** — concurrent is *not* pathological on domination (its
round-robin is in fact marginally more even, by construction). The win is **robust to memory** (echo
pattern identical on/off).

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
max_share ≤0.35 on any single day, aggregate mean 0.25–0.26), healthy. No domination problem in either.

## Steelman / honest caveats
- **Concurrent is not broken.** With concrete evidence (a confirmed wolf) it converges and
  wins (day 3 example → correct lynch). The gate is "does sequential read *better*", and it
  clearly does — but this isn't "concurrent fails."
- **N is small.** All quantitative numbers are descriptive. The verdict rests on the
  *structural* dimensions, which don't need N.
- **Judge = the implementer** (who has a stake in sequential winning). Three checks on that bias:
  (a) the scored claims are deterministic metrics, not a subjective rating; (b) every *qualitative*
  call is backed by a verbatim excerpt, reproducible from the dumped transcripts, so a reader can
  re-check and overrule it; (c) the strongest case *for the loser* is argued on the record — the
  "Concurrent is not broken" caveat above is the implementer making concurrent's best argument.
- **What version this gated.** The sequential arm was generated *after* the first-live-run fixes
  (the external novelty judge, `mention`-discharge, `opener_floor`=3 — all landed earlier the same
  day) — so this ratifies the **final** architecture, not a pre-novelty one. It predates the
  `reengagement_cooldown_multiplier 3→1.0` fix (2026-06-24): the knob sat at the detuned `3`, which
  *over*-suppressed re-engagement (exhausted pairs stayed shut), so sequential read marginally
  *calmer* here than the shipped config would — a benign direction, and the consecutive K=2 cap
  bounds re-engagement under `1.0` regardless. The structural verdict is unaffected; the exact
  current config was not re-gated.
- **What the echo number does — and doesn't — show.** `echo_rate=0.00` is **lexical** (difflib), so
  it certifies the *structural* win: blind-round redundancy is gone because agents read before
  speaking, by construction. It does **not** measure the *semantic* proactive echo the novelty judge
  exists to tame (the agreement-pile "reworded same point"), and the gate has no novelty-on/off arm,
  so the judge's specific contribution is **un-ablated**. That semantic echo is tamed rests on the
  hand-judged Dimension-1 read, not the metric — reduced **by design, not quantitatively verified**.

## Decision
**Adopt sequential. Phase A #1 closes.**

Weighed against the limitations: the evidence is deliberately thin on *numbers* — N=4/arm,
unpaired, concurrent's backend/temp unrecorded, judge=implementer. Adoption does **not** rest on
a quantitative delta (there isn't a significant one, and the doc doesn't claim one). It rests on
the **structural** finding — concurrent's blind-round redundancy and sequential's forced
responsiveness are *architectural* properties that reproduce in **all 8 games**, hold on memory
on *and* off, and don't need N. The decision leans only where the evidence is strong and
explicitly disclaims the weak part.

The commitment is also **reversible**: the concurrent design is frozen at tag
`concurrent-baseline`, so if a defensible *number* is ever required (e.g. an external audience),
the pinned quantitative A/B (future work #6) runs against it with nothing re-derived. A decisive
structural win + a reversible commitment + a preserved fallback is enough to adopt now despite
small N.

## Future work
Workstream-level future work — wolf-night migration, the scheduler tunable sweep, novelty-gate hardening,
the residual `current_round`, human integration — is tracked in the parent journey log
[`../experiment_log.md`](../experiment_log.md) §11. The one item specific to *this gate*: a pinned
**quantitative A/B** against the `concurrent-baseline` tag worktree (a win-rate / judged comparison), if a
defensible *number* is ever required for an external audience — this gate is structural/qualitative by
design (see the "What version this gated" caveat above).
