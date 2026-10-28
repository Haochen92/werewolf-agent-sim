# Extraction and the outcome halo: grading the move, not the result

**Scope:** what the post-game extraction model writes about each player's moves, the finding that its
verdict on a move mostly repeats whether that player's side won (the *outcome halo*), and what the
pipeline does about it today: a prompt rule, a second-model check of each verdict, and a rule-based
grade stored beside it. Also what is known about whether extraction picks the moves that mattered.
It describes the ten-seat code; the nine-seat measurements of June and July 2026 appear as history and
as the case study.
**Revised against the code:** 2026-10-22 at `c0732f88` (the extraction, de-halo and consolidation code
has no uncommitted edits).
**Corrected:** 2026-10-28, §4 (why the gap is an upper bound, which negatives de-halo removed, the
verdict list) with dated notes in place; the phase table in §4 added the same day.
**Companion docs:** [the journey log](experiment_log.md) (the same story in date order) ·
[the case study](outcome_halo_case_study.md) (two graded entries from the owner's own seat) ·
[the ten-seat decisions](../../memory_system/v8/decisions.md) §12–13 (the grading table, the
measurement and the rulings) · [the credit report](../../credit/report.md) (how the same grading
table scores lessons).

> **Orientation: where extraction sits.**
>
> **a game ends → its transcript, roles and outcome are saved → an offline batch job extracts
> observations, one call per role and phase → a second model checks each verdict (de-halo) → each
> observation is tagged with the decision it describes and given a rule-based grade → synthesis
> writes lessons from groups of similar observations → when memory is on, a seat is shown matching
> lessons at its decisions**
>
> An *observation* is a short, structured account of one player's move and what it led to, written
> after the game by a model that sees everything: every role, every private night action, and who won.
> Observations are never shown to a seat. They are raw material: *synthesis* (another model call)
> reads groups of them and writes the short pieces of advice, called *lessons*, that seats are shown.

---

## 1. What extraction writes

Extraction runs after a game ends, never during one. Each finished game saves its extraction input;
a batch job later makes one call per dealt role and per phase (day discussion, day vote, night
action). One role in one phase is called a *cell*. The prompt asks for the role's observations from
"the game's pivotal moments: usually a few, fewer or none when no decision of the role mattered", with
no fixed count.

Each observation has a description of the board at that moment, what the player did, what happened at
once, what it meant by the end of the game, and a one-word **verdict**: positive, negative, mixed or
unclear. Here is one, lifted from a ten-seat game the wolves won, for the Serial Killer's night action
(a lone killer who wins by being the last one standing):

> **situation:** "Day 4 ended in a 2-2 tie between the agent and an accuser, establishing clear voting
> blocs heading into the night with four players remaining."
> **approach:** "Stabbed the claimed vigilante instead of targeting either member of the two-player
> bloc that voted against the agent."
> **immediately:** "The claimed vigilante was eliminated overnight (also targeted by the wolves),
> shrinking the living roster to three players."
> **end of game:** "Directly caused the serial killer's defeat; killing the only non-wolf player who
> voted alongside the agent on Day 4 created a three-player Day 5 consisting of two wolves and the
> serial killer…"
> **verdict, as extracted:** negative

The verdict reaches three places: synthesis (each observation is shown to it tagged with its verdict,
and the prompt weights a group of observations by the spread of their verdicts), deduplication (two
observations with different verdicts are never merged), and the verdict stamp in a game's replay. It
never reaches a seat and never reaches credit, which scores lessons by a fixed rule table instead
([the credit report](../../credit/report.md)).

## 2. The finding: the verdict mostly says who won

A verdict is meant to grade the move. In practice it mostly grades the result. The extraction model
is handed the outcome and writes "from the end of the game", so a move by a losing player tends to be
called negative and a move by a winning player positive, whether or not the move itself was good.

The example above shows how. Its own "immediately" line says the wolves attacked the same player that
night, so the death was not the Serial Killer's doing alone. The end-of-game text still says the stab
"directly caused" the defeat. The rule-based grade described in §3 counts a Serial Killer's kill that
lands on a town player as a good night, and graded this one good.

The case study (§5) found two forms this takes:

- **Credit across sides.** Another side's move that same night is charged to this player, as in the
  example.
- **Working back from the loss.** The verdict starts from "this player lost" and builds a story in
  which a correct move becomes the mistake.

This matters because synthesis turns verdicts into advice. If losers' moves are all called negative,
synthesis learns "don't do what the losers did", including the moves that were right.

## 3. What runs today

The rule behind the design was set in June: an objective signal may steer which moves get attention
and may grade a move, but it never writes the lesson. Today's three parts follow it. The grade sits
beside the verdict, and the de-halo pass changes only the verdict word. Nothing rewrites what an
observation says the player did or saw.

**A prompt rule.** The extraction prompt states that "a side's win does not make each member's move
positive, and a side's loss does not make each move negative", and that a move which merely came
before a good or bad night is "unclear". It also asks for the link in the record that ties a move to
its effect. Live in the extraction prompt.

**A second-model check, called de-halo.** After extraction, Claude Haiku 5.5 reads the same game record
and every observation's verdict. Its only job is to catch a verdict the record does not connect to the
move. It keeps a verdict when something in the record links the move to its effect, changes it to
"unclear" when the outcome merely followed, and flips it only when the record shows the move worked
against the player's own side. It changes only the verdict word, not the end-of-game text. The original
verdict and the judge's reason are kept in a separate record, so the pass can be re-judged or undone.
On by default in the offline job, at about $0.006 a game. For the example above, it changed the
verdict to unclear:

> "The serial killer's kill of a town player is in its own interest, and the endgame and Day 5 outcome
> came from other players' votes the record does not tie to this kill."

**A rule-based grade beside the verdict.** Each observation names the one decision it describes (the
day or night number, and for a wolf's night which of the pack's turns). That lets the decision be
graded by the same fixed table credit uses, which asks what the move did for the player's own goal: a
vote for a wolf is good for a town player, a kill the healer saved is bad for the killer, a limited
ability spent on nothing is bad. Each observation then stores both the verdict and that grade. A
config setting chooses which one synthesis reads. In grade mode, synthesis sees "graded: positive" (or
"not graded") and does not see the extraction model's end-of-game text.

| Part | Status |
|---|---|
| Prompt rule against outcome credit | live in the extraction prompt |
| De-halo pass | on by default in the offline extraction job |
| Each observation names its decision | asked for by the extraction schema; the 40 games extracted before the field existed were tagged by a separate model pass |
| Rule-based grade stored beside the verdict | computed by a separate script after extraction; written onto the 40-game store |
| Synthesis reads the verdict or the grade | a config setting; the default and the published store use the verdict; a grade-variant store is built and not reviewed |
| Memory in the served game | a per-game choice that starts off; the production deployment allows it |

**Selection.** Whether extraction picks the moves that mattered was a separate question. The June
proposal was to hand the extraction model a list of the turns the game's own arithmetic marked as
decisive, as a suggestion. That was tested once and not adopted (§4). The prompt instead asks for the
pivotal moments with no fixed count.

## 4. How strong the halo is, and what de-halo does

### How we know the halo exists

For every observation we have three facts:

1. **The extractor's verdict:** positive, negative, mixed or unclear.
2. **A grade of the same move, computed by code** from the game record: good or bad. It judges the move's direct effect against the roles revealed after the game. A town vote for a wolf is good, a vote for a villager bad; a vigilante's shot on an evil player is good, on a villager bad. (The full rule table is in the [credit report](../../credit/report.md) §2.) The grade is only a stand-in for move quality, but it never sees who won the game.
3. **Whether the player's side won.**

If the verdict judged the move, two moves with the same grade would get similar verdicts whichever side won. They don't. Out of 1,472 observations from 40 games, this is how often the extractor called a move positive:

| | Bad move | Good move |
|---|---|---|
| **Losing side** | 0% | **23%** |
| **Winning side** | **18%** | 83% |

A good move on the losing side was called positive 23% of the time; the same kind of move on the winning side, 83%. A winner's *bad* move (18%) was praised almost as often as a loser's *good* one (23%). The verdict is mostly telling us who won.

### How sure we are

- **It is counting, not judging.** No model scored anything in this test. The numbers are counts over 1,472 observations, written by two different extraction models.
- **It holds in every slice.** The gap appears in discussion, votes and night actions (the phase table below, "By phase"), and for town and non-town roles alike. So it is not a side effect of winners and losers playing different roles or phases.
- **The gap is the most the halo could be, not the halo itself.** The grade is a stand-in for move quality and is sometimes wrong. Even if it is wrong at the same rate for both sides, it can open a gap with no halo at all: the winning side likely makes more truly good moves, so more of its rule-graded good moves really are good and fewer of its rule-graded bad moves really are bad, and a perfectly fair verdict would still praise the winners' graded moves more often. Real differences the grade cannot see (a winner's good vote that also swung the table) push the same way. So the gap is an upper bound on the halo: it is the halo plus whatever real difference in move quality the grade fails to separate. That second part would have to be very large to explain the whole gap. A fair verdict praises a truly good move equally often whichever side made it, so for it to give 83% against 23%, the losers' rule-graded good moves would have to be truly good at barely a quarter of the winners' rate (23 ÷ 83 = 28%). The case study in §5 shows the halo itself on a seat whose intent is known. (Corrected 2026-10-28: this point said a grade wrong in the same way for both sides "cannot create a gap". It can, through the different share of truly good moves on each side, as above.)
- **Not checked:** whether the stage of the game plays a part (losers' moves come earlier, where effects are harder to see).

### What de-halo does

**De-halo** is a second model (Claude Haiku 5.5) that rereads each observation against the game record and changes any verdict the record does not support, usually to "unclear". On the same observations, positive verdicts afterwards:

| | Bad move | Good move |
|---|---|---|
| **Losing side** | 0% | 21% |
| **Winning side** | 9% (was 18%) | 75% (was 83%) |

It halved the praise for winners' bad moves. On the losing side it moved many negatives to "unclear", and only some of them were unfair: a loser's good move called negative fell from 27% to 12%, which is the fix intended, but a loser's bad move called negative also fell, from 79% to 48%, and by the grade those negatives were right. (Corrected 2026-10-28: this sentence counted the 79% to 48% fall among "unfair negatives" removed; by the grade it turned correct verdicts into unclear ones.) And a loser's good move is still called positive only 21% of the time, against 75% for a winner's. **De-halo reduces the halo; it does not remove it.** That is why the verdict never decides a lesson's score: credit uses the code's grade, and the grade is stored beside the verdict.

A second review was chosen because it is narrow: it may keep a verdict, soften it to "unclear" or flip it (§3), and it changes nothing else in the observation, with the original verdict kept beside it so the pass can be undone. De-halo's model was picked on one test game, where a reader had marked which verdicts were halo and which were fair. Claude Haiku 5.5 fixed all four halo verdicts and none of the fair ones, for under a cent. One game picks a model; it does not measure its accuracy.

### By phase

The same observations split by phase. Each cell is the share before de-halo → after; "good" and "bad" are the rule-based grade's call, and the counts are observations (`evaluation/experiments/halo_phase_breakdown.py`).

| Phase | Side | Good moves (n) | called positive | called negative | Bad moves (n) | called positive | called negative |
|---|---|---|---|---|---|---|---|
| Discussion | losing | 97 | 26% → 16% | 21% → 11% | 137 | 0% → 0% | 87% → 59% |
| Discussion | winning | 217 | 81% → 64% | 1% → 0% | 52 | 40% → 17% | 25% → 19% |
| Vote | losing | 159 | 13% → 16% | 36% → 14% | 130 | 1% → 1% | 72% → 35% |
| Vote | winning | 204 | 85% → 83% | 1% → 0% | 112 | 8% → 1% | 29% → 31% |
| Night | losing | 90 | 37% → 34% | 19% → 8% | 93 | 0% → 0% | 75% → 51% |
| Night | winning | 105 | 84% → 83% | 4% → 2% | 76 | 16% → 14% | 20% → 8% |
| All phases | losing | 346 | 23% → 21% | 27% → 12% | 360 | 0% → 0% | 79% → 48% |
| All phases | winning | 526 | 83% → 75% | 2% → 1% | 240 | 18% → 9% | 25% → 21% |

The halving of winners' praise for bad moves came from discussion (40% to 17%) and votes (8% to 1%), while at night it barely moved (16% to 14%), and the gap in praise for good moves stayed wide in every phase after de-halo (votes 16% against 83%). De-halo cut the unfair negatives on losers' good moves in every phase, but in discussion it also cut the praise those moves fairly earned, from 26% to 16%.

### Two supporting checks

- **Can each observation be matched to its move?** Grading needs every observation to name the decision it describes. A reader that did not see these tags named each observation's decision from the game record, and agreed on 98 of 102, above a 90% bar set beforehand.
- **Does extraction miss the decisive turns?** In June, on three nine-seat games, a list of the game's decisive turns was given to a cheap extraction model to see whether it covered more of them. It made no difference, and on a hand read the cheap model covered the key turns about as well as the expensive one. The list was not adopted. Three games show the direction, not a rate.

## 5. Case study: two correct moves graded as mistakes

**In short.** In a game where the project owner played the Serial Killer, the extraction model called
the owner's best night a "fatal error" and charged the owner for the wolves' kill. It is the only
case in the record where the player's intent is known rather than inferred. Full text:
[`outcome_halo_case_study.md`](outcome_halo_case_study.md). (Nine-seat game, July 2026, Gemini 2.5 Pro
extraction.)

**What happened.** On night 1 the owner's kill happened to hit the Vigilante. The verdict's own text
said this helped the Serial Killer, then called it negative by adding in the wolves' kill of the
Investigator the same night, which the owner neither caused nor could see. On night 2 the owner,
publicly suspected, killed a player correctly read as a wolf, which is the Serial Killer's best
possible night. The verdict conceded the read was right, then called the kill a fatal error because it
"removed a viable alternative target" for the village. The day record does not support that: the
votes against the owner had formed the day before. The owner was voted out the next day and lost.

**Why.** Both verdicts were written from the end of the game, with the loss in hand. The first credits
across sides; the second works back from the loss.

**The fix.** The case named the test that would settle it: compare the model's verdicts with
rule-based grades on games played only by agents. That test is §4. The fixes are §3.

**What it shows.** The verdict can be wrong against known intent, not merely correlated with the
outcome.

**Limits.** One game, two entries; human play is not what the prompt was written for. It shows the
mechanism, not a rate. All 12 observations from the game carried a negative verdict except one mixed.

## 6. What is not established

- **Which outcome signal writes better lessons.** The grade variant of the store is built but not
  reviewed, and the two variants were never compared. The fair comparison randomizes per seat inside
  the same games and needs on the order of 1,000 followed lessons per variant.
- **De-halo leaves the end-of-game text.** It rewrites the verdict word only. In the default verdict
  mode, synthesis still reads the extraction model's end-of-game story, as in the §1 example.
- **The grade covers only what the rule table can grade.** 1,711 of 2,277 observations received one.
  An observation about a pattern over several decisions has none, the Necromancer is unscored, and a
  decision whose result was never made public (the player died that night) is left ungraded.
- **The grade is a rule set, not ground truth.** Its rows are pinned by unit tests and were set by the
  owner role by role. It measures what the rule says a move did for the player's goal, not every
  consequence.
- **Selection in the ten-seat game is unmeasured.** The June test was three nine-seat games. Whether
  today's extraction captures the ten-seat game's decisive moves has only been read, game by game.
- **Nothing here shows memory improves play.** The served game runs with memory off by default, and
  the ten-seat memory has not been tested at scale.

## Sources and implementation

| What | Where |
|---|---|
| The extraction prompt (per cell: the evidence rule, "outcome is not credit", pivotal moments, no count) | `Agents/prompts/extraction/cell.py` |
| The observation schema (fields, the verdict, the decision the observation names) | `Agents/schemas/memory.py` |
| The offline extraction job | `scripts/extract_batch.py`; `Agents/memory/extraction/offline.py` |
| The de-halo pass and its prompt; on/off, model, thinking level | `Agents/memory/extraction/dehalo.py`; `Agents/prompts/extraction/dehalo.py`; `DehaloConfig` in `Agents/memory/persistence/config.py` |
| Tagging old observations with their decision | `scripts/tag_observation_decisions.py`; `Agents/memory/extraction/decision_tags.py` |
| The rule-based grade (the table credit uses) | `Agents/memory/consolidation/grading.py`; applied by `scripts/grade_observations.py` |
| Writing tags and grades onto a store; building the grade variant | `scripts/build_v8_store.py` |
| Synthesis reading the verdict or the grade | `synth_outcome` in `Agents/memory/consolidation/config.py`; `_format_cluster` in `Agents/memory/strategy_synthesis.py` |
| Verdict never merged across in dedup | `Agents/memory/dedup_gate.py` |
| The halo fit (§4) | `evaluation/experiments/v8_verdict_halo.py` (`--grain observation` for the 1,472-observation fit); data in `evidence/memory_system/v8/data/halo/` |
| The phase table (§4) | `evaluation/experiments/halo_phase_breakdown.py`, over `evidence/memory_system/v8/data/halo/observation_rows.jsonl` |
| Test-game judge comparison, seeding revisions, tag check | [v8 log](../../memory_system/v8/experiment_log.md), 2026-10-11 and 2026-10-13 |
| The rulings | [v8 decisions](../../memory_system/v8/decisions.md) §13 |
| The §1 example | game `20497d9e`, observation 7 of `batch_results/extraction_runs/flash_seed_gate_2026-10-12/` (`extracted.jsonl`, `dehalo.jsonl`, `grades.jsonl`) |
| The June selection test | [`memory_system/v7/extraction_coverage_ab_spec.md`](../../memory_system/v7/extraction_coverage_ab_spec.md); anchor option `--anchors-from` in `evaluation/src/studies/reextract_cells.py` (research only) |
| The June first sign (932 observations) | [`netverdict_calibration.py`](netverdict_calibration.py) over `memory_stores/v6_1/observations.json` |
| The case study and its frozen observations | [`outcome_halo_case_study.md`](outcome_halo_case_study.md); `outcome_halo_human_game.json` |
