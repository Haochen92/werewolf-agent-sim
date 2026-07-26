# Case Study: Outcome Halo in Observation Extraction — a Ground-Truth Specimen

**Scope:** two observations extracted from a single human-seat game (2026-07-26) whose `net_verdict`
gradings can be checked against the player's own attested intent — the only case in this archive
where the graded player can personally vouch for what the action was trying to do.
**Date:** 2026-07-26 · **Branch:** `feature-dimension-schema` (working tree ahead of `7b891fe`,
HITL driver uncommitted at time of writing).
**Run:** game `447cbe95-9173-4a1e-a76b-9a3e9201141a` — seats on `gemini-3.1-flash-lite`, extraction
on `gemini-2.5-pro` (per-cell v6 dimension schema), memory retrieval OFF, human seat =
serial_killer, played by the project owner.
**Artifact:** `observation_extraction_human_game.json` (FROZEN RECORD) — all 12 extracted
observations, deleted from `memory_stores/v6_1` the same day under the poisoning rule (human games
are never mined); this copy exists only as evidence.

## Verdict

The extraction judge's `net_verdict` graded the serial killer's strongest move of the game — killing
a wolf — as "negative," reaching that verdict by inventing a speculative counterfactual, and graded a
night-one kill "negative" by charging another faction's simultaneous kill to this player's ledger.
Both failures fit the previously established pattern that `net_verdict` tracks outcome rather than
decision quality (the selection-halo finding: verdicts calibrate to whether the faction won, not to
pivotalness). What this case adds is ground truth: the graded player is the project owner's own
seat, so intent is attested rather than inferred. The result does not reopen the closed v7
compounding campaign — verdicts never fed game credit — but it localizes the defect to the two places
verdicts DID flow: dedup partitioning and strategy-point synthesis weighting. Forensics below;
skip by subhead.

## What `net_verdict` is, and where it flows

Every extracted observation carries a judge-assigned `net_verdict` (positive / negative / mixed) plus
an `impact_on_final_game_outcome` rationale, emitted by the extraction model itself as part of the v6
dimension schema. Three consumers matter, and their exposure differs:

- **Game credit: not a consumer.** The loop's credit machinery (`conversion_credit`) is
  vote-endpoint-based and never reads the verdict — so verdict errors could not move the v7
  endpoint measurement.
- **Dedup partitioning: consumer.** The dedup gate treats differing `net_verdict` as a hard
  never-duplicate rule (`Agents/memory/dedup_gate.py` — "the positive/negative contrast IS the
  lesson"). A wrong verdict therefore changes which observations survive as distinct store entries.
- **Strategy-point synthesis: consumer.** Cluster synthesis weights by outcome spread
  (`Agents/memory/strategy_synthesis.py`), so a systematic verdict bias tilts the direction of
  synthesized lessons.

## The specimen

Both entries below are lifted verbatim from the artifact (serial_killer / night_action cells).

**Entry 1 — attribution leakage.** Night 1, 9 alive, zero information; the kill happened to hit the
Vigilante:

> **approach:** "Made a speculative, information-less kill on the first night, which happened to
> eliminate the Vigilante."
> **impact_on_final_game_outcome:** "Negative. By removing the Vigilante, you eliminated a chaotic
> village-sided role that could have caused mis-lynches, **benefiting your solo win condition**.
> Simultaneously, **the wolves killed the Investigator**, meaning the two strongest village power
> roles were removed at once, accelerating the wolves' path to parity…" (emphasis added)

The rationale's first clause assesses the action as beneficial; the "negative" verdict is then
reached by folding in the wolves' independent night kill — an event the serial killer neither caused
nor could observe. The judge graded the joint night outcome, not the decision.

**Entry 2 — outcome back-propagation.** Night 2, 7 alive, the player publicly "on watch"; the kill
correctly removed a wolf identified from behavioral tells:

> **approach:** "Targeted and killed a player **correctly identified as a wolf** based on their
> aggressive, information-forcing behavior during the day's discussion."
> **impact_on_final_game_outcome:** "Negative. Although eliminating a rival wolf is beneficial in a
> vacuum, doing so while you were the primary lynch suspect was a fatal error. This action **removed
> a viable alternative target** for the village, allowing them to consolidate votes on you the next
> day…" (emphasis added)

Killing wolves is the serial killer's win condition, and the entry concedes the read was correct.
The "fatal error" framing rests on a counterfactual — that the village would have lynched the wolf
instead — which the day record does not support: the information identifying that player as a wolf
only became public through the death reveal, and the lynch pressure on the human seat was already
built from the previous day's discussion. The player was lynched, the player lost, and the verdict
works backward from that loss. Ground truth from the seat: the kill was a deliberate, correct
priority call, not a blunder.

**Distribution context** (context, not an independent result): all 12 observations from this game —
11 negative, 1 mixed, across serial_killer and vigilante cells, N = 1 game. Both graded roles died;
`source_game_winner` was recorded as `None` in the fold for this run, so the faction-won correlation
cannot be checked from this artifact alone — the calibration claim rests on the original selection-
halo analysis, not on this case.

## Scope and what this does not show

- N = 1 game, 2 analyzed entries; this is a mechanistic exhibit, not a rate estimate.
- Human play is out-of-distribution for the extraction prompt (which assumes an LLM's turn
  transcript); a judge error on a human game does not measure the error rate on agent games — though
  the two failure mechanisms (cross-faction attribution, outcome back-propagation) are
  transcript-agnostic.
- The v7 endpoint result is untouched: verdicts never entered credit, and the compounding campaign's
  closure stands on its own instrumentation.

## The call, and what would change it

No pipeline change now — memory research is closed and live ships memory-off. The case is recorded
as the sharpest available illustration of why the credit redesign moved all valence to deterministic
anchors (vote-endpoint day credit, accuracy-credited reads) and demoted model judgment to
diagnostics.

If store-building ever reopens (post-MVP), the direction this case argues for: replace the judge's
`net_verdict` at extraction time with the same deterministic anchors the credit system already
trusts — grade a night kill by its mechanical consequence chain (target's true faction, subsequent
vote endpoints), not by a model's post-hoc causal story. What would weaken this case: a golden-set
audit showing judge verdicts agreeing with deterministic anchors at high rate on agent-only games —
the disagreement rate has not been measured (2026-07-26).
