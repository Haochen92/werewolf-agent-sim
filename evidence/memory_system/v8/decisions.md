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

## 10. How often a seat looks up its lessons (D4, 2026-10-12)

Counted on the owner's first ten-seat game (`403f4dbc`, Haiku 5.5): with memory on, about 60 lookups (a
situation call and a search each), 27 of them evil or neutral discussion turns, at 2 to 5 turns per seat
a day. The owner ruled:

- **Day discussion:** one lookup per seat per day, made at its first turn and reused for its later turns,
  made afresh once someone makes a new role claim that day (a new player and role pair; a claimant
  repeating its claim does not count, since one investigator claimed in four lines that game).
- **Votes:** a fresh lookup for every vote, the day's largest decision, made after the whole discussion.
- **Night:** one lookup per seat per night, shared by the pack's chat rounds, its kill and its ability.

On that game about 60 lookups become about 38, plus one per new claim. What is kept is the lessons
selected and the lookup's record, never the payload or a verdict: each decision records its own verdicts,
and a reused lookup's record says it was reused and on which round it was made. The cache lives in the
server process, so a restart only means a fresh lookup. Built in `Agents/memory/retrieval/lookup_cache.py`.
A human's claim carries no claim field yet, so it does not refresh a lookup.

**Amended the same day, after an outside review of the query.** A wolf's night is two lookups, one for
the pack's chat and one for its kill and ability: in a played game the talk moved from candidate
targets to a kill-and-block plan the first lookup could not anticipate (about six more lookups a game).
The review's other findings were fixed in the query prompt: it now states the rules, the public dead,
the seat's own exact state (a fortune teller's points, a speculator's pick, a necromancer's bodies and
conceals, the pack's carrier and target), and calls a parity count after a concealed death the worst
case for the town rather than exact; the four labels used only by the switched-off dimension gating
are no longer asked for. Not built, by the owner's choice: a whole-cell shortcut for cells of three or
fewer points (10 of the 24 cells retrieved in play), since more seeding will grow them; the offline
check of 12 to 20 frozen situations against a show-the-whole-cell baseline is deferred.

## 11. Extraction leaves the game: saved input, offline batch (owner, 2026-10-12)

The gate's relevance read and its stage-filter replay (`experiment_log.md`, the gate parts one and two)
showed the store needs more lessons per stage, so more source games, and that the lessons' `uses_left`
must mean the count *before* the decision. The owner's rulings:

- **Every game saves its extraction input when it ends** (roles, lineup, day discussion, wolf chat, the
  exact night actions, each seat's strategy notes, the outcome), whether or not anything is extracted.
  No model is called; the input is there for a later batch.
- **Post-game extraction never runs during a live game.** It is an offline job: it collects the games
  not yet extracted and submits them as one batch (a game's role calls together, sharing its cached
  prefix), the de-halo pass included. Served games are no exception: a memory-on game's replay shows
  its lessons once the job has extracted them, and until then says they are being written. Replays that
  already carry lessons keep them.
- **Batch route over online, for cost**; the model is decided by a two-game check of Claude Sonnet and
  Haiku (batched) against 3.8 Flash's saved outputs. The remaining Gemini credit (about $20) may be used.
- **Stage filter**: `uses_left` stays an exact count at extraction; retrieval compares some left (> 0)
  against none left. It is added to the cells that lack it (the Speculator, whose pick is its one use,
  and the limited-use roles' day cells) before re-extraction.

Past games without a saved input are rebuilt from their records: the game record (discussion, night
records, outcome) plus the decision cases (each seat's last note, the wolf chat in the wolf seats'
context). Checked on the 12 seeding games against the input live extraction used: identical except one
pack vote line on a game's last night, and 14 of 120 notes where the rebuild has the newer note of a
seat that died that night (live state drops it, so live extraction never saw it).

## 12. Credit comes to ten seats, and how a night is graded (owner, 2026-10-13)

The table itself is plan §9.6 item 10; this section keeps why.

**Why port now.** v8 closed with a reviewed static store, and that is a step back from v7: a lesson that
hurts play is retrieved again every game because nothing can prune it, and one that works is never
promoted. v7's credit was built to close exactly that gap, so a v8 story that stops at a static store
leaves the regression standing. The port is followed by a small demo run of memory-on games that shows
the loop on v8's own data: grading, credit, promotion into synthesis, prune and evict. It demonstrates
the mechanism; it measures no benefit (that needs ~35–60 games per arm, §9.6 item 9).

**How a turn is graded.** For each role's turn the owner asked three questions: what outcome is ideal,
what is neutral, and what is undesirable (a wasted turn, a limited use spent for nothing, a foreseeable
failure, exposing oneself). Four principles came out of applying it role by role:

- **Grade what the actor controls.** A sigil striking the pack's carrier is the Sigilist's choice, so it
  does not count against the kill. A Vigilante shot on an evil player is good even when the Healer saved
  the target or the target was immune: the choice was right, and the "immune" result outs the Serial
  Killer.
- **A predictable failure is the actor's.** A kill on a target the Healer saved is bad, not luck: the
  killers cannot decline to kill, so the skill at night is choosing the target, and attacking someone the
  Healer is likely to cover wastes the night. The same holds for an immune target.
- **Exposure is a cost.** A kill seen by a Sentinel at the victim's door or by a Trailseer following the
  killer is bad, for the Serial Killer and the pack's carrier alike; the pack can lower that risk with a
  conceal, the Serial Killer cannot.
- **A limited use spent for nothing is bad**: a watch that saw no one, a sigil on someone who did not
  attack, a self-bet on a quiet night, a conceal on a body with no record. An Investigator's check on the
  Serial Killer is bad as well: it spends a check and gives the town a false clear (10-11 had ruled only
  that it is not a find).

Harsh "bad" grades do not bias credit. A lesson is credited by lift: its followed outcomes against the
memory-off outcomes of the same turn kind (the 12 seeding games, graded by the same table). A role whose
turns are mostly "bad" simply has a low baseline.

**Left unscored.** The Necromancer: its borrowed actions interact in ways one grade cannot capture (a
borrowed block on the Vigilante, say, may be what kept it alive), and rewarding its kills alone would
push it to kill every night (10-11). The Illusionist is graded but marked hard to gauge: whether a
conceal mattered depends on what the victim's will would have said.

**Authority and thresholds.** None of the nine-seat validations carry over, so v7's thresholds (prune at
lift < −0.15 with ≥8 follows, protect with ≥2, evict at ≥8 retrievals) are kept and labelled unvalidated
for ten seats. Credit, prune and evict run on a copy; every change is listed with its numbers and reviewed
before a store is published.

**The database.** The tick's four tables (`memory_records`, `base_rates`, `obs_generations`, `tick_runs`)
share the server's `werewolf` database with the games and events, but nothing links to them and only the
tick reads them. A ten-seat tick on top of the nine-seat rows would fold the two stores together, so they
are dumped to a file (restorable with one `pg_restore`; the store is also on disk as
`memory_stores/demo_snapshots/demo_gen1`) and emptied before the first ten-seat tick.
