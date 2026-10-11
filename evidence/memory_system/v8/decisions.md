# v8 memory: the decision record of 2026-10-11

How the v8 plan was reached in one long owner–Claude discussion: each question, what was found in the
code or data, and what was ruled. The current plan is `plan.md` §9; what was run is
`experiment_log.md`. Commit hashes point at the change that carried each ruling out.

## 1. Where it started

`plan.md` (revised 2026-10-10/11) set the direction: town night-only memory, a fixed disclosure
policy, day and night memory for evil and neutral roles, with D1–D5 open. The owner asked what the
memory evaluation, the proxy metrics and the retrieval evaluation need for the new roles and
mechanics, and what goes in the demo versus the write-up.

Three read-only searches of the code found:

- **Scoring.** Credit, decision scoring, conversion and most of `compute_metrics` still encoded the
  nine-seat cast: threat set `{wolf, serial_killer}`, per-role night fields a ten-seat game never
  fills. Several silent mis-scores:
  - a Vigilante's shot on a wolf graded as friendly fire;
  - the pack's votes graded by the town rule;
  - the conversion channel inert.
- **Retrieval evaluation.** `eval-retrieval`, `eval-turn` and the replay exist. They have no ten-seat
  situations, old-role situation prompts in the replay, and no cache-aware checks.
- **Demo and write-up.** The memory switch was disabled in the UI, but the API still took memory on.
  Landing card 1 is hard-coded to a nine-seat game. The write-up is a skeleton, and two front doors
  carry stale claims.

## 2. Defects found and fixed

- **The replay dropped a player's later discussion turns.** `memory_consulted` and `player_reads`
  were sent once per (player, day, round 0, phase). Fixed in `0638ab4c`.
- **The server accepted memory on with the nine-seat store.** `WW_MEMORY_ENABLED` gates it, off by
  default. Fixed in `651b7960`.
- **21 metrics read 0 on every ten-seat game.** Set to None in `fa6ce77e`, then ported in
  `e5763cd1`.
- **The night record dropped what the rules decided.** It now keeps the outcome and every actor's
  record (`b3730102`). The eval case also says what a night turn decided (`38cd2a5e`).

## 3. Rulings of the second discussion (plan §8)

- **Before seeding:** record the night's outcome and the turn kind.
- **Threat sets by side.** The `wolf` role is retired; the pack is the Chanteuse and the Illusionist;
  the lone killer is the Serial Killer or the Necromancer. An Investigator's find is a delivered
  "Suspicious".
- **The new roles' grading** (plan §8.3):
  - the Chanteuse's tiered blocks;
  - the Illusionist without claim space (whether a later claim lands is day play, not attributable
    to the conceal);
  - the Necromancer by nights survived and win, with body-effect grading deferred;
  - the neutrals graded on their own objectives.
- **Night namespace:** one `night_action` per role; the pack's chat, kill and skill share it, and
  each pack role has its own cells.
- **Old research harness frozen** (`loop/`, studies, audits): production imports nothing from it.

## 4. Judgement in observations

The owner noted that observations were meant to be facts, while the horizon text and two fields
(`impact_on_final_game_outcome`, `net_verdict`) ask for judgement. Synthesis then weights by those
verdicts.

- **Who judges.** The owner: extraction sees the whole game, and synthesis sees only a cluster, so
  the judgement belongs at extraction.
- **An external review** (pasted by the owner) added the distinction that mattered: recorded fact,
  supported explanation, strategic conclusion. Only the first two belong in an observation.
- **External advice on counterfactual testing** (branching a saved game, matching similar games):
  noted as future work.
- **The owner's constraint:** no extra judge, no new model calls, no new pipeline stage. Anything
  larger goes to the report's limitations.
- **What was built (plan §9.2):**
  - the evidence rule in the extraction prompt;
  - evidence stated inside the existing end-of-game field;
  - "unclear" carries no direction in synthesis;
  - no automatic "opposite of a failure" in synthesis;
  - a zero floor on counts;
  - the immediate and end-of-game effects shown apart.
  - The "same-game observations are not independent" instruction was dropped: synthesis cannot see
    game ids.

## 5. Scope rulings (plan §9.1)

- **D1 revised.** Town day is extracted and synthesized for the owner's review, never retrieved in
  play (`f17b53e6`). Approved advice becomes fixed role-prompt text (option A). Code that picks
  advice by game state (option B) is future work.
- **D2: no forced disclosure.** In 28 saved ten-seat games the information roles already reported
  the next day almost every time; with town day memory out of play, the risk D2 guarded against is
  closed.
- **D3: map the new roles onto existing cell shapes,** with one new "uses left" field group
  (`890c5dec`).
- **The prompts:**
  - concealment and the will in the epistemic rule;
  - the synthesis rules block (the whole ten-seat pool);
  - the driver lines (`fba61f9d`);
  - concealment in the parity clocks (`d8cbca94`);
  - the seeding arm and lineup cycling (`d1d773bd`).

## 6. The pilot and what it changed (`experiment_log.md`)

Four games, one per lineup: 194 observations in all 36 cells, 51 strategy points after an offline
synthesis, about $2 a game.

- **Cost.** Langfuse put extraction at $1.00–1.19 a game on gemini-2.5-pro, mostly its thinking.
  - The newer Flash models are cheaper; gemini-3.8-flash exists and is on a promotion.
  - Re-extracting two games: 3.8 Flash about $0.34 a game, no player IDs, as well grounded.
    3.5-flash-lite was cheaper but leaked player IDs.
  - **Ruled: extraction on 3.8 Flash** (`04a24082`).
- **Batch extraction** (Vertex batch, 50% off) was considered and not built. On Vertex the cache
  discount and the batch discount do not stack, and extraction input is already mostly cached. It
  would save about $2–3 on the seeding for about 250–350 lines. Listed as future work.
- **Claude's read of all 66 observations** against the engine records:
  - 1 factual error in 66. Its cause: game state drops a dying actor's record, so the extractor
    guessed that role's last night. **Fixed** (`bbcba5cd`): the full record, marked "never told".
  - About 6 of 66 hold outcome-driven verdicts or hindsight.
- **The day call filed nearly everything under the vote.** The owner asked for a separate
  discussion extraction. **Ruled: two day calls** (`4948f914`); one game re-extracted gave 0 → 16
  discussion lessons.
- **Counterfactuals: option A** (ruled). Keep the wording; rely on the synthesis guard and the
  owner's review.

## 7. The demo and the portfolio

An external recommendation (pasted by the owner) proposed one worked example: source observations
(expandable, "N of M shown"), the synthesized strategy, and its later use. It goes on the portfolio
rather than the app's landing page, with a small teaser in the app. Credit-informed synthesis is an
optional second example, only where records trace the exact transformation.

- **Agreed.** The seeding should capture the example. Provenance was added (`ec5e1b7b`), and the
  tick's snapshot keeps the synthesis log (`4a32fdf0`). No migration is needed: memory records are
  stored as whole JSON.
- **Credit data.** Ten-seat credit needs memory-on games, with retrieval on and extraction off, plus
  the credit port. The v7 run (`evidence/v7_final/runs/v2_full/`) kept per-generation stores, the
  `distilled_from` lineage and prune events, so it likely holds a traceable credit example
  (nine-seat, no wills, zero reasoning). The trace is deferred (owner KIV).
- **The v7 blind spot.** Credit rewarded town concealment and abstain advice it could not see the
  cost of. The will offsets the in-game cost of withholding in part, but not the credit's
  blindness. Under the revised D1 the pathway is closed: town day advice is never followed, so it
  is never credited.

## 8. The metrics port and the credit system

- **Metrics.** The 21 metrics and the new-role proxies are computed from each night's full record
  (`e5763cd1`), checked by hand against one pilot game. The owner ruled the Chanteuse's fellow-wolves
  rule and the Sentinel, Trailseer and Sigilist proxies.
- **Credit.** It needs its own port, set out in plan §9.6: side-based decision grades, the pack's
  chat graded by that night's kill (ruled), no conversion channel, unscored missing baselines, its
  own database, memory-on data, and validated thresholds. It runs after launch, as a diagnostic.

## 9. v8

The owner named everything from this iteration on **v8**. The seeding plan, log and data moved into
`evidence/memory_system/v8/` with this record. The bulk seeding comes next (plan §9.5).
