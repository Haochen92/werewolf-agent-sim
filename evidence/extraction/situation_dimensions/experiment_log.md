# Situation dimensions: journey log (May to October 2026)

> **What this is.** The dated path from one shared paragraph describing "the situation" to separate
> fields on every lesson and every memory query, and what each test of those fields showed. Later
> entries supersede earlier ones. Where a design was falsified, it is shown in its place.
>
> **Companion docs.** The current design: [`report.md`](report.md), which also defines the
> terms used here (lesson, observation, cell, stakes numbers). This log condenses the folder's
> earlier `experiment_log.md` (in git history at `2382b34c`), [`dimension_schema_build_spec.md`](dimension_schema_build_spec.md),
> [`v6_full_store.md`](v6_full_store.md), [`criticality_screen/experiment_log.md`](criticality_screen/experiment_log.md)
> and [`dimension_accuracy_audit/experiment_log.md`](dimension_accuracy_audit/experiment_log.md), which
> stay in the folder, plus the entries on these fields in
> [`../../memory_system/v8/experiment_log.md`](../../memory_system/v8/experiment_log.md). Everything
> before October ran on the nine-seat game.

---

## ① Motivation: one paragraph doing two jobs

**Before late May 2026 · the shared paragraph.** Extraction, the duplicate check and the memory query
all included one block of prose that named four things to describe: the information landscape (what
is known, claimed and unknown), the consensus texture (how the room is aligned), the agent's exposure
(how visible or at risk it is) and the game phase (early, middle or late). It was a sound first
design. The earliest extraction prompt had produced situations like "after a mislynch", which matched
every mislynch ever stored, and naming the conditions that make one board differ from another fixed
that. The same paragraph also told the query what to write, so both ends of the store used one
vocabulary.

**2026-05-27 · prose drops fields and embeds worse.** During the study that built a human-labelled
retrieval test (`../situation_summary/`), one healer case was queried two ways: with a label in front
of each part ("Information landscape: …"), and as the same text with the labels removed. The labelled
query scored a
higher cosine similarity against every one of the stored items known to be right for that case, by
0.008 to 0.046. A paragraph also let the model blur or leave out a part it had been asked to cover.
The root cause: the two ends of the store matched only as long as two prompts kept following one
style, and nothing enforced it.

## ② First design: the four parts become fields

**Late May 2026 · fields, joined back into a labelled string.** The four parts became output fields.
The code joins them into one labelled string, which is what gets embedded. A field cannot be silently
dropped, and the labels are added by code, not by the model's memory of a house style.

**2026-05-27 · a fifth field, falsified.** The human-labelled test had 20 cases and 340 relevance
grades (0, 1 or 2 per returned item). It scores a ranking with NDCG, a measure that rewards putting
the most relevant items first, from 0 to 1. The first queries scored about 0.83. A fifth field, *core
dilemma* (the agent's specific tradeoff, such as "should I reveal my role to avoid elimination?"),
seemed to capture what the four parts missed. On the 6 cases clean enough to score it fairly, it
lowered NDCG@5 by 0.084. The model wrote abstract tradeoffs instead of the concrete board, and
abstract text sits further from concrete stored lessons. The field was removed.

**Late May 2026 · the shipped version.** The query that shipped (structured fields, no core dilemma,
the investigator's private findings described first) scored +0.061 NDCG over the first queries. The
first comparison had shown +0.112, but 108 retrieved items had never been graded and counted as zero;
grading them by machine settled the gain at +0.061. Those 108 grades were never checked by a person.

## ③ Implement → verify → decide

**2026-06-13 · the phase label is too coarse.** *Catches:* can an agent tell that a lesson does not
fit its board, and on what? A replay planted one endgame lesson ("final three against the serial
killer") into 20 mid-game town votes and asked the model to rule on each lesson. It rejected the plant
13 of 20 times, on the numbers: "we are still at 5 players, not final-three." *Decision:* the agent
reasons on the exact player count, but the only field carrying it was the three-way phase label. A
lesson's situation needed exact numbers.

### The per-cell design (2026-06-15)

**② The design.** A walkthrough of every role and phase rebuilt the fields from two rules. First, a
field's form follows what an embedding can carry: free text is embedded, while numbers, yes/no flags
and opposites ("agrees with my read" against "opposes it") are stored as separate fields, because an
embedding blurs them. Second, a field states the board, never advice; the advice is the lesson's
payload. One set of fields per role and per day or night (a *cell*) serves the stored lesson and the
query alike. Day discussion and vote share a cell.

The dispositions:
- the phase label became the stakes numbers (players alive, distance to the nearest evil win, swing)
  plus a stakes sentence written from them;
- consensus split into the room's alignment, the seat's position and a direction label;
- exposure split into heat now and the cost of a visible move;
- the target candidates and the private-against-public gap became fields of their own;
- the vigilante's bullets and the wolf's partner status were added as counters.

**Two reversals in the same walkthrough.**
- *Numbers fully out of the embedding* became *numbers out, their meaning in*. A lesson from the wrong
  stage is often the opposite lesson, and the similarity search is the one stage that cannot read a
  separate number. So the stakes sentence says "one death from a wolf win, every vote decisive", not
  "endgame".
- *Compute the numbers from game state* became *the extraction model writes them, then the sentence
  from them*. A lesson drawn from a whole game has no single board to compute from. The query side
  does have one, which mattered later (2026-07-02).

**Build order.** One cell first (villager day), then a screen, and the rest only if the screen showed
a lever.

**2026-06-15 · stakes-adjusted ranking: a win, then a leak, then noise.** 119 villager-day
observations were re-extracted from 20 games. *Catches:* does ranking lessons partly by how close their
stakes numbers are to the seat's improve town votes, mostly in the endgame? Each frozen vote was
replayed with no memory, with similarity ranking, and with the adjusted ranking, and scored +1 for
voting a wolf or killer, −1 for a town player, 0 for an abstain.
- First run: +0.25 over similarity alone in the endgame (16 votes), near zero in mid-game, 4 votes
  flipped toward a threat and none away. *Decision:* go.
- *Catches:* the pool was not held out. 20 of the 30 test games were the games the lessons came from,
  so a seat could be shown a lesson that knew its own game's outcome. With those excluded, the endgame
  gain fell to +0.087 (23 votes). *Decision:* hold.
- After the other roles' cells were built: on held-out games for three town roles (125 votes), the
  adjusted ranking scored 0.032 below similarity alone. The villager subset, run twice on the same
  inputs, gave +0.061 and then −0.037. *Decision:* any effect is below the replay's run-to-run noise;
  do not wire the adjusted ranking into play.
- The owner adopted the new fields anyway, on the quality of the extracted lessons, and kept the
  numbers in the store.

**2026-06-15 · the full store and a hindsight leak.** All six roles were re-extracted (993
observations, 17 role and phase groups). *Catches:* is the direction label set from what the seat
believed at the time? In 12.9% of records it disagreed with the record's own prose, set from the
outcome rather than the seat's read. The field descriptions were changed to say "the read you
expressed then" (7.1%), and a check at store-write time now resets a direction that contradicts prose
saying the room had no consensus (0% detectable). A rebuilt store had 919 observations.

**2026-06-15 · the query written in the same fields.** The live query was rewired to write the seat's
cell. *Catches:* does a query in the store's own fields find better lessons than the old prose query?
With the old query, lessons beat no memory by +0.088 on the 125 replayed votes; with the new one, by
+0.120. The record read this as the rewrite improving retrieval. The two numbers come from separate
runs, and the same day's identical reruns had swung by 0.1, so the gain is not separable from noise.

**2026-06-16 · the fields decide duplicates.** The owner judged that a model asked whether two
many-field entries are the same lesson would not answer reliably. So the duplicate check now groups entries by swing, alive bucket and
room direction before any model looks, and never merges entries that differ in verdict, information
class or exposure class (the two class labels were added for this, 2026-06-16). The principle: a hard
rule where a mistake is irreversible (a merge destroys a lesson), a soft one where it only costs
ranking.

**2026-06-18 · gating by the fields: flat.** An earlier replay over 7,534 shown lessons had found 58%
judged not relevant, with similarity scores no different for relevant and not-relevant ones (0.828
against 0.827). Matching on the alive bucket or swing cut the not-relevant share by 5 and 6 points.
So a soft re-ranking was built: each lesson's score is scaled between 0.7 and 1.3 by how many of four
fields agree with the query (alive bucket, swing, information class, exposure class). *Catches:* do
lessons re-ranked this way apply more often? On 24 held-out town votes, judged per lesson by a model:
the top five changed in 23 cases; "does not apply" went from 38% to 36%; the vote hit a threat a third
of the time either way. *Decision:* the setting stays off.

**2026-07-02 · the filled values had never been checked.** A review of the evaluation tools noticed
that every field was written by a model and none had ever been compared with the true value, even
where the board gives it for free. If the values were wrong, the gating and stakes tests had measured
noise. *Catches:* are the query's filled values correct? A free audit scored 20,284 query situations
from 6,275 decisions in three runs against each decision's own board, with a rule written beforehand:
treat the gating verdict as unproven if any field it uses scores under 80%.
- Players alive: 97% exact (99% in the right bucket). Wolf partner revealed: 97.5%.
- Vigilante bullets left: 16.4%, and 0% on day 2, where every vigilante with 2 bullets wrote 1.
- Swing, as written by wolves: 60.6%, against 82.7% for always answering "no".
- Distance to parity: 5–9% exact.
- A catch made before scoring: 176 wolf night decisions had no roster saved, so their truth read as 0
  players and dragged wolf players-alive to 71%. Those cases are now skipped; the corrected figure is
  97%.

The rule fired. *Decision:* the fields a seat can know (players alive, bullets, partner status) are
now computed from the game state at query time and written over the model's values. A re-run of the
gating test with computed values (about $10–15) was authorized and held for spending approval.

**2026-07-04 · the prose still lagged the numbers.** Overwriting a number after the fact left the
model's stakes sentence, already embedded, written from its own wrong number, so a corrected bullet
count could disagree with the sentence the search used. *Fix:* the
computed numbers are now given to the model as known board facts before it writes, from the same
function as the overwrite, so the sentence is written from the true numbers.

**2026-07-11 · the truth was narrower than the instruction, and the numbers were public.** *Catches:*
does the audit's truth match what the prompt teaches? The field descriptions said "the leading evil
faction" and "which faction is winning", but the truth counted only the wolves. A seat that correctly
called a serial-killer endgame a swing was graded wrong. The truth now uses all three sides'
countdowns. The same day the owner noticed that distance to parity and swing were never hidden: the
cast is fixed and every death reveals the dead player's role, so the counts of the living are public.
*Decision:* both are now computed at query time from that public census. The audit's earlier numbers
were graded against the wolf-only truth.

**2026-07-21 · memory research closed.** After the town-only memory run leaned negative, the owner
closed the memory research; no memory version was promoted, and the live game runs with memory off
(`../../memory_system/v7/execution_plan/`). The
gating re-run authorized on 2026-07-02 was never run.

### The ten-seat game (October 2026)

**2026-10-11 to 12 · cells for twelve roles, and a reviewed query.** The ten-seat roles got cells from
one table that names each role's field groups; the same table generates the observation, lesson and
query form of each cell. A uses-left counter was added for the limited-ability roles. An outside
review of the query led to these changes: the query now states the rules, the public dead and the
seat's own exact state; after a concealed death, its stakes count is stated as the worst case for the
town; and the four category labels that only the gating used are no longer asked for.

**2026-10-12 · do the lessons shown fit?** *Catches:* in real ten-seat games, do the lessons a seat is
shown fit its decision? Seven memory-on games on a 12-game store; four Claude Sonnet readers judged 96
lookups against the true roles. 15% of 268 shown lessons fitted, and 36 of 96 lookups had at least one.
The readers all named the same pattern: retrieval matched the role but not the stage, and the score
did not track fit (in one healer lookup the worst lesson scored 0.887 and the best 0.829). Eight of the
96 query situations had the query's own wrong swing line, whose wording was fixed.

**2026-10-12 · a stage filter.** Every lesson already stored the board it was learned on. *Catches,
first:* are the stored counts right? Of 196 observations carrying uses left, 165 were exact, 29 gave
the count after the night's action, and 2 were impossible; 7 were wrong on "some left or none".
*Fix:* uses left is defined as the count before acting. *Catches, second:* does dropping lessons from
another stage (alive bucket, partner lost, uses left) improve fit? In an offline replay of the 96
lookups, fit rose from 15% to 25%, with 25 lookups left empty. *Decision:* the filter is built into
retrieval, off by default.

**2026-10-13 · a larger store.** On a 40-game store, refilling the filtered lookups from same-stage
lessons gave 52 of 96 lookups a fitting lesson, against 41 without the filter (different readers from
the first read). The readers named the remaining misfit: lessons keyed to an event the seat has not
seen, which no stage field records. Lesson synthesis now groups lessons by partner lost and uses left
as well, so a lesson's stage label holds for all its sources.

**2026-10-14 · the filter in play, unmeasured.** The 20 memory-on games of the credit demonstration ran
with the stage filter on. They measured the credit pass, not fit or play
(`../../memory_system/v8/experiment_log.md`).

## ④ Remaining questions

- Whether gating helps once its keys are exact. The re-run was never done, and the query no longer
  writes the two class labels.
- Whether the two class labels are right. A sampler to pick cases for a human check was built; the
  labelling was not done.
- Whether the stage filter changes play. No game has measured it.
- Whether any stored field other than uses left matches the record.

---

**Sources.** `../situation_summary/experiment_log.md` (2026-05-27 entries) ·
`../../memory_system/effectiveness/decision_replay/experiment_log.md` (2026-06-13 capability probe;
2026-06-15 design entries) · `dimension_schema_build_spec.md` · `criticality_screen/experiment_log.md`
and its JSON outputs · `v6_full_store.md` · `../../memory_system/v7/plan.md` (G3c, gating efficacy, the gating
screen) · `../../evaluation/hardening_pass/experiment_log.md` §2.1 ·
`dimension_accuracy_audit/experiment_log.md` and `data/dimension_audit_20260702_105203.json` ·
`experiment_log.md` §9 (2026-07-11) · `../../memory_system/v7/execution_plan/report.md` §5 ·
`../../memory_system/v8/decisions.md` §10–11 · `../../memory_system/v8/experiment_log.md`
(2026-10-12 gate parts one and two; 2026-10-13 fit read and synthesis split; 2026-10-14 demo run).
