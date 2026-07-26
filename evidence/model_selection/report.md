# Seat-model selection — measured costs, quality reads, and external benchmark priors

> **What this is:** the selection record for the model that plays game seats (discussion, votes,
> night actions) — measured per-game costs from live HITL games, the owner's transcript-quality
> reads, and a mapping onto public benchmarks (eqbench.com) used as *priors*, never verdicts.
> Companion: `evidence/model_drift/drift_surfaces_and_guards.md` (why cross-run model comparisons
> need interleaving). Guiding principle: **measure on our game; use public benchmarks only to
> shortlist what to try next.**

## Current selection (2026-07-26)

| Slot | Model | Why |
|---|---|---|
| Production default (live seats) | `gemini-3.5-flash-lite` | 3–5s turns (latency is the UX constraint), single provider end-to-end, constrained structured output (zero schema-repair machinery needed), dialogue clearly above 3.1-flash-lite |
| Premium / spectator table | `deepseek/deepseek-v4-pro` | Best observed dialogue by a wide margin at ~$0.24–0.35/game post prompt-pass; 8–25s turns rule it out where a human waits on their own turn |
| Bulk / eval / batch | `gemini-3.1-flash-lite` | Cheapest, fastest, reasoning-free; the long-standing eval workhorse |
| Retired from consideration | `gemini-3.6-flash` | $1.02/game measured with quality below v4-pro — no remaining niche |

Scope of this verdict: quality claims are the owner's transcript reads over 1–2 full games per
model (not a blind eval); costs are single-game measurements with game length varying ±2×; all
post-prompt-pass numbers are on the 2026-07-26 prompt epoch (closed-world clause + ~120-word cap +
cache-ordered layout). A different epoch re-opens the comparison.

## Instruments (read before the tables)

- **Game cost** = Langfuse-recorded token usage × list prices (custom model/price entries,
  including cached-input and reasoning detail rates). It is a *bill*, not a normalized metric:
  game length (days survived, turns taken) varies ±2× between games and is not corrected for.
- **Dialogue quality** = the owner reading full transcripts while playing a seat. Consistent
  across games but low-N and unblinded; treat as strong directional signal, not measurement.
- **Latency** = wall-clock per structured turn as felt in live HITL play, not instrumented.

## Measured games (all 2026-07-26, 9-player cast, memory-off)

| Model | Input | Cached | Output | Cost | Notes |
|---|---|---|---|---|---|
| gemini-3.6-flash | 345k | 0 (0%) | 67.5k (45% reasoning) | **$1.02** | pre-prompt-pass epoch; Gemini implicit caching confirmed dead on this backend |
| deepseek-v4-pro | 1.50M | ~450k (31%) | 130k | **$0.55** | pre-prompt-pass epoch; turns averaged 142 words with 300-word tails |
| deepseek-v4-pro | 678k | 274k (40.5%) | ~76k | **$0.24** | post-prompt-pass epoch; turns averaged 92 words, cap held with no observed quality loss; roughly a half-length game — cap effect and game-length are inseparable at N=1 |
| gemini-3.1-flash-lite | — | — | — | ~$0.19 (est.) | estimate = the 3.6-flash token profile repriced; no dedicated measured game |
| gemini-3.5-flash-lite | — | — | — | ~$0.27 (est.) | same repricing; also emits reasoning tokens (probe: 73/74 output tokens on a trivial call) |

Cache economics (DeepSeek): cached input reads at $0.003625/M vs $0.435/M miss — cached tokens are
a rounding error on the bill. Whole-game cached share of 40–60% is the realistic ceiling
(first-turns each day, votes, and night calls are structurally cold); the cache-layout reorder
moved the effective input rate $0.292 → $0.260/M between the two v4-pro games.

Latency: v4-pro 8–25s per structured turn (49B active params, no thinking); flash-lite class 3–5s.
Latency compounds under the sequential day scheduler — per-turn waits sum, they don't parallelize.

## Quality reads (owner, low-N, unblinded)

- **v4-pro:** argument chains that build across turns (timing tells, EV arguments, correct use of
  our ruleset's SK night-immunity), coordinated multi-seat pressure, a mediator register. Clearly
  the strongest table. Verbosity was the cost — largely tamed by the 120-word cap (92-word average
  measured post-cap).
- **3.5-flash-lite:** noticeably better than 3.1-flash-lite (N=2 eyeball, partly confounded with
  the wolf-night redesign landing the same day).
- **3.6-flash:** not judged above 3.5-flash-lite by enough to justify ~4× its price; reasoning
  tokens (45% of output) buy latency, not visible table quality.
- Cross-model constant: "framed / roleblocked" genre-bleed appeared in every family until the
  closed-world rules clause (2026-07-26); post-clause, agents float impossible mechanics only as
  hypotheticals and self-correct.

## External benchmark priors — eqbench.com

Why this site: its benchmarks target exactly the properties a social-deduction seat needs, where
generic capability leaderboards (coding, math) do not. Mapping:

| eqbench.com benchmark | Measures | Maps to |
|---|---|---|
| EQ-Bench 4 | active social/emotional intelligence in multi-turn conversation | discussion persuasion, reading the table |
| Creative Writing v3 / Slop Score | prose quality / cliché density | dialogue naturalness (the "reads cryptic" complaint) |
| DiploBench | negotiation + strategic play in Diplomacy (as Austria vs LLM opponents) | closest analogue to werewolf play itself |
| Judgemark v4 | quality as an evaluation JUDGE | selecting judge models for our eval pipeline, not seats |

Caveats before citing any of these: DiploBench's own authors state it "is not a benchmark (yet)"
— single game runs with high variance between iterations. And none of these test structured-output
discipline, which is a real seat requirement here (DeepSeek's unconstrained tool-calling needed a
lenient-parse base + enum folds + a fallback model before it could hold a seat reliably).

**Scores: UNFILLED as of 2026-07-26.** The leaderboards are JS-rendered and not fetchable
programmatically at write time; transcribe from the browser when consulting. Candidates to record:
`deepseek-v4-pro`, `deepseek-v4-flash`, `gemini-3.5-flash-lite`, `gemini-3.1-flash-lite`,
`gemini-3.6-flash`, plus any shortlist candidate before spending a measured game on it.

| Model | EQ-Bench 4 | Creative Writing v3 | Slop | DiploBench | (date checked) |
|---|---|---|---|---|---|
| *(fill from eqbench.com)* | | | | | |

Intended use: a model that scores well here earns a **measured HITL game** (one cheap game ≈
$0.10–0.55); the game, not the benchmark, decides. Never select on benchmark rank alone — our
quality signal (owner reads) and our constraints (latency, structured output, provider ops) are
not what these benchmarks score.

## Known gaps (freshness-dated)

- **No blind quality eval** (2026-07-26, medium): all quality claims are unblinded owner reads.
  A cheap upgrade if selection ever gets contentious: same-day interleaved games per candidate,
  transcripts stripped of model identity, owner ranks them.
- **Flash-lite costs are estimates** (2026-07-26, low): repriced from another model's token
  profile; a real measured game would pin them (~$0.20 to find out).
- **Game-length confound on all per-game costs** (2026-07-26, low-as-labeled): ±2× spread; the
  tables label it rather than correct it. A per-turn or per-1k-transcript-token normalization
  would fix it if costs ever drive a close call.
- **Benchmark column unfilled** (2026-07-26, low): see above; JS-only leaderboards.
- **Win-rate/skill comparison across models: deliberately absent** (2026-07-26): per the drift
  doc, cross-model skill contrasts require interleaved same-window generation and enough games to
  beat seat-luck variance — a paid experiment nobody has commissioned. Dialogue quality and cost
  are the selection criteria today, not measured win rates.

Provenance: all measured games on `feature-dimension-schema` (series `82d548b..ad97c4a`,
2026-07-26), Vertex backend for Gemini models, official DeepSeek API (`deepseek/` factory prefix)
for v4-pro; prices as entered in the local Langfuse `models`/`prices` tables the same day.
