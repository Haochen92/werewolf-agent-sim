# Extraction selection — does the model pick pivotal turns, and should we steer it?

**Date:** 2026-06-17 · **Status:** diagnostic done (net_verdict calibration); steering recommendation
= anchor-injection, gated by the memory-pipeline prompt freeze.

## The question

A criticality screen / "mine the high-leverage turns" idea presumes extraction currently *infers
pivotalness*. Before building selection steering, resolve what extraction actually does — by reading
the prompt, not guessing.

## What extraction actually does (`Agents/prompts/extraction/postgame.py`)

NOT uniform-per-turn, NOT pure salience. It is a **whole-game, omniscient, outcome-conditioned pass
with a per-role quota**:
- one pass over the full transcript + all roles + `GAME OUTCOME`;
- instructed for pivotalness + causal chains ("patterns, mistakes, and **pivotal moments**", "look
  for multi-day patterns — causal chains and strategic sequences");
- outcome-aware (`impact_on_final_game_outcome` judged "from the END of the game", `net_verdict`);
- quota-bounded: "**4-8 observations** per role".

So the premise ("infers pivotal") is correct *by instruction*. The open questions become (a) how
reliable is the hindsight causal attribution, and (b) the quota is a fixed budget regardless of how
many pivotal moments a game actually had (pads low-event games, truncates rich ones).

## Diagnostic: is the hindsight `net_verdict` calibrated, or rationalized noise?

`netverdict_calibration.py` — `net_verdict` vs the deterministic `role_faction_won` (n=932, v6_1):

```
                   positive   negative   mixed   unclear   n
faction WON          64%        25%        8%      3%     432
faction LOST         21%        65%       11%      3%     500
pos−neg share:  WON +0.40   LOST −0.44   separation +0.84   (every role +0.66…+1.17)
```

**Outcome-conditioning is REAL, not noise.** The model faithfully uses the outcome it's handed —
strong, every-role separation. So "keep observations outcome-labeled" is trustworthy (pivotal
blunders survive as negatives).

**But the cleanness is an OUTCOME HALO, not per-action causal discrimination.** +0.84 separation,
~65% faction-concordance, and only 3% "unclear" + 11% "mixed" (87% confident-and-aligned) → the
judgment largely answers *"did your side win?"* and stamps it on every action, not *"did THIS move
matter?"* A won game still contains incidental moves (a lucky vote, idle chatter) that get a positive
glow; a lost game contains correct-but-unacted reads that get a negative one. Because observations are
not deterministically turn-anchored (the v6 criticality numbers on them are LLM-estimated, not
game-state-derived), this validates **labeling, not selection** — selection stays unvalidated. The
~22-25% within-faction minority is the only discrimination headroom and can't be confirmed as signal.

## What the two implications mean (the steering decision)

1. **Supports anchor-injection (feasibility).** `GAME OUTCOME` is an objective signal *injected into
   the prompt*, and the model demonstrably conditions on it. That's empirical evidence the
   feed-an-objective-signal → model-uses-it mechanism works here — so injecting a deterministic
   *leverage* signal is likely to land, not be ignored. (Suggestive, not proof: outcome is one plain
   scalar; per-turn anchors are richer and may be used less cleanly.)
2. **Motivates anchor-injection (necessity).** The halo is precisely the thing extraction can't do on
   its own: separate a pivotal winning move from one that merely rode the win. The deterministic
   pivotalness signal (de-luck proxy / `is_swing` / `decision_scoring`) is outcome-independent and
   *is* that discriminator. Injecting it is purely ADDITIVE — it supplies the missing signal while
   leaving the (trustworthy) labeling and the multi-day causal-chain pass intact. So we're not
   replacing a working selector; we're handing the halo the one input it's blind to.

Why it matters for the store: the halo currently lets incidental winning-side moves enter as
outcome-"validated" lessons and incidental losing-side moves as outcome-"validated" mistakes — both
non-pivotal. That pollutes the substrate that BOTH observations and (downstream) strategy_points build
on. Leverage-anchoring filters to the moves that actually moved the game.

## Recommendation

**Anchor the existing whole-game pass with deterministic leverage** (and swap the 4-8 quota for a
leverage-derived budget) — do NOT gut extraction into turn-scoped mode (that sacrifices the multi-day
causal-chain pass, whose labeling we just validated). Steer SELECTION by the objective measure; never
steer the CONTENT/lesson (the facts-vs-tactics line — same side as the registry threat-brief). Keep
selected turns outcome-labeled so pivotal blunders survive as negatives.

**Gate:** the extraction prompt is a memory-pipeline prompt that conditions Phase B gold labels, so
anchor-injection is a deliberate versioned experiment sequenced with the labeling plan — not a casual
tweak. This is one layer of the garbage-in fix; it stacks with the prompt-cap fix (investigator) and
the substrate, it is not the floor.

## Provenance

`netverdict_calibration.py` over `memory_stores/v6_1/observations.json`. Extraction prompt
`Agents/prompts/extraction/postgame.py`. Deterministic leverage signals
`evaluation/src/components/decision_scoring.py` + the de-luck proxy basket
(`evidence/metrics/proxy_win_monotonicity.md`). Related: `evidence/prompt_claims_audit/` (the
prompt-authored-bias layer upstream of this).
