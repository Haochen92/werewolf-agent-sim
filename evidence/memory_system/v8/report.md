# Memory v8: the memory system of the ten-seat game

v8 separates learning from play: games read an existing store, while offline jobs extract observations, write lessons and update credit. The rebuild adapted v7 to new roles, moved extraction out of gameplay and addressed problems in lesson relevance, rule accuracy and outcome-based judgement. These are the reasons for the architecture below; whether it improves ten-seat play remains untested.

**Version.** This report describes the code at the `feature-frontend-v1` branch head on 2026-10-26
(`abfdf984`), checked against the code named in each statement. Every measured result belongs to the
store, prompts and models it ran on, named beside it; none was re-run on today's code. Deployment
statements are dated separately in "What is deployed, and since when".

## System and evidence at a glance

- **What it is.** The AI players can be given short lessons written from past games. After a game, a
  model writes accounts of the moves that mattered; another model condenses them into advice per role
  and kind of decision; during a later game, a seat looks up the advice that matches its situation
  and says, for each lesson shown, whether it followed it. A rule-based pass then scores each followed
  lesson by the decisions associated with following it and removes the ones that do worse than play without memory.
- **What has been checked.** Each stage on its own: how many of the lessons shown fit the decision
  (15% → 24–27% after a larger store and a filter by game stage, 96 lookups), how many lessons state a
  rule the game does not have (11% → 6.1%), how far the written verdicts follow the result instead of
  the move, whether each observation can be matched to its decision (98 of 102), and one run of the
  scoring pass over 20 games.
- **What is not known.** Whether memory makes the ten-seat players play better. No game set has
  compared memory on with memory off; the planning estimate is about 35–60 games per arm, extrapolated from nine-seat data and not yet checked for ten seats. v8 has not been
  tested at scale, which is not the same as having tested negative.
- **In the served configuration described here,** memory is the player's switch and starts off. Deployment dates are recorded separately below.

> **The data flow (manually operated, not an automatic loop).** A game ends and saves what it can teach → an offline job writes
> **observations** from it → a second model re-reads each observation's verdict → the observations are
> folded into the store and condensed into **lessons** → later games look lessons up and give a
> **verdict** on each → the **credit pass** scores followed lessons and prunes → the store is
> **published** to the database the server reads.

Read §1 for the architecture, §2 for the choices behind it, and §3 for the checks. §4 separates missing outcome evidence from remaining component questions. The [memory hub](../report.md) owns the version history; this report owns the ten-seat implementation.

**Terms used below.**

- An **observation** is a short account of one move and its effect, written by a model from a finished
  game ("On night 2 I blocked the player who had claimed Investigator; the check never came").
- A **lesson**, stored as a **strategy point**, is advice for one role at one kind of decision, written
  by a model from a group of observations ("Illusionist, night: spend a conceal only on an unclaimed
  victim").
- A **cell** is one role's shelf for one kind of decision: day discussion, day vote, or night action.
  The twelve roles give 36 cells.
- A **store** is a named set of observations and lessons. `ten_seat_v2` is the store published today.
- The **halo** is the tendency of a written verdict to praise the winning side's moves and blame the
  losing side's, whatever the move was worth.

## 1. What runs today

### 1.1 In a game: looking lessons up

**When a seat looks up.** With memory on, a seat looks up lessons before a decision, with three
exceptions (`Agents/memory/retrieval/plan_gating.py::retrieval_plan`):

- nothing on day 1 or the night after it, since nothing has happened that a lesson could match (the
  night shares day 1's number);
- no town seat on a day turn: town day lessons are written for the owner to review and never served;
- no human seat, which decides without the agent pipeline.

**How a lookup works.** A short call to the seat's own game model describes its situation in one or
two parts, using the same labelled fields the stored lessons were written in. The code computes the
facts a seat can know exactly (players alive, uses of an ability left, whether a wolf partner is
revealed) and writes them over the model's version. Each situation is searched against the seat's own
cell by embedding similarity: five lessons are fetched and the best three kept, so a seat sees up to
six (`Agents/memory/retrieval/pipeline.py::enrich_payload_with_memory`). Served games retrieve
strategy points only, never observations (`server/game/run_config.py::game_run_config`). How the
query is built and checked is told in full in the [situation query report](../../extraction/situation_summary/report.md).

**What is reused.** A lookup is the situation call plus the search. A seat makes one lookup for its
day's discussion at its first turn and reuses it, until someone makes a new role claim that day. Every
vote looks up afresh. A seat makes one lookup a night; a wolf makes two, one for the pack's chat and
one for its kill and ability. Only the lessons selected and the lookup's record are kept, never a
verdict; the cache lives in the server process, so a restart means a fresh lookup
(`Agents/memory/retrieval/lookup_cache.py`).

**Ordering by track record.** Two steps after the search use the counts the credit pass writes onto
each lesson. Lessons followed at least five times with more good grades than bad are placed first,
and when every kept lesson is such a lesson, one slot goes to the best untried one
(`Agents/memory/retrieval/filters.py::_sp_is_proven`). Both are on by default and do nothing on a
store without counts. If the published store carries the counts of the October demonstration's credit
pass, as the publishing code path suggests (the database was not checked), they apply in served
memory-on games to the lessons that pass found followed often with mostly good grades.

**Built and off.** Four optional steps are switchable per game and off in served games: a filter that
drops near-repeats, a model reranker, a tilt by matching situation fields, and the **stage filter**,
which leaves out lessons learned at another stage of the game (players alive, partner lost, uses
left) and refills from same-stage lessons in the cell
(`Agents/config/run.py::DEFAULT_STAGE_FILTER`). The stage filter was on in the October demonstration
games.

**The seat's verdict.** For each lesson shown, the seat answers follow, override ("its situation
holds but I have a better move") or not relevant, with a one-line reason
(`Agents/schemas/output.py::StrategyVerdict`). A turn shown no lessons gets no verdict field. Each
decision's record keeps its verdicts, which is what the credit pass reads later. The verdicts also
add to counters on the lesson in the live store (shown, followed, overridden, not relevant;
`Agents/turn/adoption.py::process_strategy_adoption`); the next publish of the store replaces them
with the credit pass's counts.

### 1.2 After a game: from a game record to observations

**The game saves its input; nothing is extracted during play.** When a game ends it saves what
extraction needs (roles, lineup, day discussion, wolf chat, each night's full record, each seat's
notes, the outcome) and calls no model (`Agents/nodes/orchestrator.py`; on the server, the
`extraction_input` column of the game's row). Extraction is an offline job run by hand over saved
inputs (`scripts/extract_batch.py`). Games that ended before inputs were saved are rebuilt from their
records (`scripts/backfill_extraction_inputs.py`; served games only when no seat was human).

**Extraction.** Each dealt role gets three calls, one each for its day discussion, its day vote and
its night, sharing one cached prefix (the rules, the record) per game. Each call returns the
observations for that cell: what the seat faced, what it did, the immediate effect, the end-of-game
effect, and a **verdict** on the move (positive, negative, mixed or unclear). The prompt asks for
takeaways the record supports, no fixed count, and the end-of-game effect only where something in
the game supports the link. The job's default model is Claude Sonnet 5.5 in Message Batches, with the
reply schema given as text after the cached prefix so every call can read the cache; a reply that
does not validate is asked again in a second batch, and only what fails twice goes direct with the
schema enforced (`Agents/llm_factory/providers/anthropic.py`, offline mode). Gemini 3.8 Flash, online
with its prefix cache, remains available by flag.

**De-halo.** A second model, Claude Haiku 5.5, re-reads each observation's verdict against the game
record and rewrites a verdict the record does not support, usually to "unclear"
(`Agents/memory/extraction/dehalo.py`; on by default, `DehaloConfig`). The original verdicts and the
judge's reasons are kept, so the pass can be re-judged or reverted. It changes the verdict word only,
not the end-of-game effect text.

**Decision tags and grades.** Each observation names the decision it describes: the day or night
number, and for a wolf's night whether it was the pack's chat, its kill or its skill
(`Agents/schemas/memory.py`, `decision_day`, `pack_turn`). With the decision named, code can grade
it from the game record by a fixed table of good, neutral and bad outcomes per role and action
(`Agents/memory/consolidation/grading.py`; the table is in the [credit report](../../credit/report.md),
"The ten-seat rule table"). Each observation then carries both outcome signals: the model's verdict
and the code's grade.

### 1.3 Into the store: from observations to lessons

**The fold.** New observations are added to the store and checked for duplicates against what is
already there: a near-duplicate is kept or discarded, and an old observation is never rewritten
(`Agents/memory/consolidation/obs_fold.py`). The dedup stack is told in the [dedup report](../../dedup/report.md).

**Synthesis.** Claude Sonnet 5.5 condenses each cell's groups of similar observations into lessons
(`Agents/memory/strategy_synthesis.py`; `TickConfig.model`). It is given the ten-seat rules, and its
prompt asks for one move per lesson in at most three sentences, mechanics only as the rules state
them, and advice for the cell's own phase only. It must not infer that the opposite of a failed move
is good, and it treats an "unclear" verdict as saying nothing about whether the move helped. A group
of observations is split by stage (players alive, pack partner lost, uses left) before synthesis, so
each lesson comes from one stage. Synthesis reads the
verdict by default; reading the grade instead is a setting (`TickConfig.synth_outcome`). Where a
lesson already has at least five scored follows, synthesis sees its score. Each lesson keeps the
observations it came from (`source_observations`), and each synthesis call's input and output is
logged, so a lesson can be traced to its sources.

**The rule screen is a review, not a stage.** The lessons of the published store were read by model
readers against the rules; the ones flagged as stating a wrong rule, and the duplicates the readers
found, were left out when `ten_seat_v2` was published (`scripts/publish_v8_store.py`). They stay in
the working store, marked. Nothing in the pipeline screens a lesson the learning tick writes later.

### 1.4 Keeping the store: two passes, both run by hand

Both passes live in `Agents/memory/consolidation/tick.py`; no schedule runs them.

- **The credit pass** (`tick credit`; no model call) re-scores every lesson from the memory-on games
  in its window. Each followed decision is graded by the table above and compared with memory-off
  decisions of the same kind, to reduce credit for decisions that already score well without memory. This comparison does not isolate the lesson's effect: situations, player choices and the baseline can still differ. It
  then prunes a lesson that scores below −0.15 after at least 8 follows, protects one that scores
  above 0 after at least 2, and evicts one shown at least 8 times, never followed, and overridden at
  least once and at least as often as marked not relevant. The thresholds are carried over from the nine-seat loop and
  are not validated for ten seats. It reads batch-run games from files and served games from the
  database; in a game with a human seat only the AI seats' decisions are graded (since 2026-10-26,
  [decisions](decisions.md) §15). Every change is recorded with its numbers. The
  scoring is told in full in the [credit report](../../credit/report.md).
- **The learning tick** (`tick learn`; paid) folds in new observations from the offline job, lets old
  ones age out (an observation not seen again for four ticks per time it has been seen is dropped),
  and synthesises on every second tick. The lesson dedup after synthesis is off by default since
  2026-10-26 (`TickConfig.sp_dedup`) until it is tuned. It never prunes or evicts lessons;
  that is the credit pass's.

**Publishing.** Both passes end by publishing: the store's records are mirrored into LangGraph's
Postgres store in the server's database, with their embeddings (Qwen3-Embedding-8B through
OpenRouter), re-embedding only what changed (`Agents/memory/persistence/postgres.py::publish`). The
server reads lessons from there. While nothing is published, or the index was embedded by another
model, a memory-on game is refused.

### 1.5 The store served today

`ten_seat_v2` was built on 2026-10-13 from 40 AI-only ten-seat games (12 seeding games, 4 pilot
games, 7 gate games, 1 smoke game and 16 games played through the server on 2026-10-10), extracted
offline: 2,277 observations, 2,008 kept after dedup, 605 lessons after synthesis and the lesson dedup,
and 498 after the review left out 37 flagged for a wrong rule and 78 duplicates. Every cell has
lessons (the smallest, the Speculator's night, 3). The credit pass of 2026-10-14 pruned 4 and evicted
4, leaving the 490 lessons published that day with the 2,008 observations. Served games read only
the lessons.

## 2. Why it is built this way

The choices below combine recorded owner rulings and implementation decisions; their sources are in the decision record
([decisions](decisions.md)) and the final plan ([plan](plan.md) §9). The working constraint for the
rebuild was **no extra judge, no new model calls and no new pipeline stage**; anything larger went to
limitations. The de-halo pass is the one approved exception.

| Choice | Why | Record |
|---|---|---|
| Town day lessons are written for the owner's review and never served | Advice the owner approves becomes fixed role-prompt text instead; keeping it out of play also closes the path by which v7's credit rewarded town withholding: town day advice is never followed, so it is never credited | decisions §5, §7; plan §9.1 |
| No forced disclosure for the town's information roles | In 28 saved ten-seat games they already reported the next day almost every time (Investigator after Suspicious 13 of 13, after Not suspicious 25 of 28; Sentinel 42 of 42; Trailseer 44 of 44, rough counts by claim field or text match) | decisions §5; plan §9.1 |
| New roles mapped onto existing cell shapes, plus one "uses left" field group | No per-role fields; old stores still load | decisions §5; plan §9.1 |
| Served games retrieve strategy points only | Set on 2026-09-25, when the store served was the nine-seat `demo_gen1`: it held observations only for the wolf and the serial killer, none for the town, so serving them would have given the sides different memory. The ten-seat store published since 2026-10-14 does hold town observations (1,133 of 2,008); the setting was carried over without a new ruling. The other reasons stand: since a ruling of 2026-07-15 observations are material for synthesis, not prompt content, and lessons are what the replay shows being weighed | `server/game/run_config.py::game_run_config` |
| Extraction offline, never during a game | It slowed and cost every game; the store needed more source games, cheaply; the saved input lets any game be extracted later | decisions §11 |
| The day extracted as two calls, discussion and vote | One day call filed nearly everything under the vote (one pilot game: 0 → 16 discussion observations, about $0.18 more a game) | decisions §6; plan §9.5 |
| A de-halo pass after extraction | The verdicts leaned toward the winning side; on the one game where a reader had marked them, Haiku 5.5 fixed the 4 halo verdicts and none of the 3 fair ones, at about $0.006 a game | log, 2026-10-11; plan §9.5 |
| Observations name their decision; both verdict and grade kept | The grade makes the halo measurable and gives credit a rule-based signal; which signal writes better lessons is not known, so synthesis reads either by setting | decisions §13 |
| Models chosen within the budget and credits at hand | Extraction moved from Gemini 2.5 Pro to 3.8 Flash for cost, then to Sonnet 5.5 when the Gemini credits ran out; synthesis on Sonnet 5.5 on Claude credits; the embedder moved to Qwen3-Embedding-8B, at $0.01 per million tokens the cheapest of those compared | log, 2026-10-11 and 2026-10-12; `Agents/llm_factory/accessors.py` |
| Lookups reused within a day's discussion and a night | About 60 lookups a game fell to about 38 on the owner's first ten-seat game; a new claim refreshes the day's lookup because it changes the situation | decisions §10 |
| The stage filter built and left off | It raised fit in replays; turning it on in served games is a separate ruling | decisions §11; log, 2026-10-13 |
| Credit as its own pass; prune and evict apply themselves | Without credit a harmful lesson is served every game and a good one is never promoted, a step back from v7; credit needs only the games, so it can run without additional model calls | decisions §12, §14 |
| v7's thresholds kept, labelled unvalidated | None of the nine-seat validations carry over to ten seats | decisions §12 |
| Lessons in the database the server reads | A file store re-seeded on every game broke served games on 2026-10-14 after the embedder change | `frontend/docs/deploy_log.md`, 2026-10-14 |

## 3. What has been checked

Each check below tests one stage. None compares play with memory and without it.

### 3.1 Do the lessons a seat is shown fit its decision?

**About a quarter do, after a larger store and the stage filter; about one in seven did before.**

*The test.* Seven AI-only memory-on games (four on Claude Haiku 5.5, three on GPT-6 Luna; 2026-10-12)
made 352 lookups. A sample of 96, spread across model, role and phase, was read by four Claude Sonnet
subagents against the rules and the games' true roles. Each lesson shown was judged to fit the
decision, fit partly, or not fit. The same 96 lookups were then searched again from the situations
the seats had written, which reproduced what the seats had been shown in 91 of 96.

*The result.* On the 12-game store `ten_seat_v1`, 39 of 268 lessons fit (15%), 79 partly (29%), 150
did not (56%); 36 of the 96 lookups had at least one fitting lesson. Day turns fit worst (discussion
7%, vote 13%, night 19%). The readers all reported the same pattern: the search matched the role, not
the stage of the game. Lessons about a dead partner, the last few players, night 1 or a pick already
made reached seats on day 2 or 3 with seven to nine alive, and the similarity score did not track fit
(one healer lookup: the worst-fitting lesson scored 0.887, the best 0.829). The seats mostly rejected
the misfits (their verdicts were sound in 65 lookups and mixed in 25, never plainly wrong), so the
cost was prompt room more than misplay.

The 40-game store and the stage filter were then replayed on the same 96 lookups, read by a second
set of four Sonnet subagents on the same rubric:

| Lessons shown | 12-game store | 40-game store |
|---|---|---|
| Top three, no filter | 15% fit; 36 lookups with a fit | 19%; 41 |
| Stage filter, gap left empty | 25%; 28 (25 lookups empty) | 27%; 33 (17 empty) |
| Stage filter, gap refilled from the cell | 22%; 30 (18 empty) | 24%; 52 (2 empty) |

Two comparisons sit in this table and answer different questions. **The filter with refill**, on the
40-game store and the same readers, moves the lookups with a fitting lesson from 41 to 52 and fit
from 19% to 24%. Without refill, fit reaches 27% but only 33 lookups contain a fitting lesson. Precision and coverage therefore need to be read together. **The whole change**, a store three to four times larger plus the filter, moves
them from 36 to 52 and fit from 15% to 24–27%, but across two sets of readers, so it is approximate.
With larger cells, refilling after the filter finds a same-stage lesson for most lookups; on the
12-game store refilling mostly added misfits (2 of the 28 promoted lessons fit). On the 12-game store
the filter dropped 101 of 146 misfits and 10 of 39 fitting lessons (all 10 on the players-alive
bucket).

*How sure we are.*

- **Readers:** model subagents, not people; the second read used different subagents.
- **What is left:** about three in four lessons shown still do not fully fit. The readers name the
  remaining misfit the same way: lessons keyed to an event the seat does not have (named at a victim's
  door, a rival claim, the room turning on the partner). The stage fields record counts, not events.
- **Not checked:** whether a lookup reused across a day's turns fits the later turns as well as a
  fresh one would.

### 3.2 Do lessons state the game's rules correctly?

**Model readers flagged 6.1% of the larger store for incorrect rules, compared with 10.8% of the smaller store.** Different stores and readers make this an approximate comparison, not an isolated effect of a fix.

*The test.* Model readers checked each lesson against the ten-seat rules text and flagged claims the
rules contradict, with a confidence.

*The result.* On the 176 lessons of the revised Sonnet synthesis (12 games, 2026-10-12), one Opus
subagent flagged 19 (10.8%: 7 high, 12 medium confidence); these 19 were left out of `ten_seat_v1`.
On the 605 lessons of the 40-game store, four Sonnet subagents flagged 37 (6.1%: 9 high, 28 medium).
The errors cluster in the same places each time: the Sigilist's "no effect" result read as protection
or as clearing the target, who an "immune" result can be, the pack choosing its carrier (it rotates by
seat), and votes on Day 1 (there is none). Traced to their sources, the errors are mostly synthesis
over-generalising from correct observations (two Healer saves of the same player read as permanent
protection), not extraction mistakes.

The synthesis prompt shaped this. On the 12 games, Gemini 3.1 Flash-Lite wrote 150 lessons with 9%
flagged; Sonnet 5.5, with three times longer lessons, 164 with 20% flagged; Sonnet with the revised
prompt (mechanics only as the rules state them, one move per lesson, the cell's own phase only), 176
with 11%, at about half the length (median 66 words) and with day advice in 1 of 32 town night lessons
instead of most of them.

*How sure we are.* Each figure is one read. The readers differ in strictness: on the 40-game store
one quarter's reader flagged 4 errors and another's 13. The 11% and the 6.1% come from different
readers and different stores, so the fall is approximate.

### 3.3 Does an observation's verdict judge the move or the result?

**The verdict is strongly associated with the winning side; de-halo reduces that association.** In the fitted models below, the win coefficient falls by about one third. This is not a count of bias errors removed. The detailed account is the
[observation quality report](../../extraction/observation_quality/report.md), "How strong the halo is,
and what de-halo does".

On 1,472 graded observations of all 40 games, the extractor called a good move positive 83% of the
time on the winning side and 23% on the losing side. After de-halo, 75% and 21%. On the 482 night and
vote observations of the 19 games first checked, de-halo turned the losing side's negative verdicts
from 53% to 27% (mostly to "unclear") and barely moved the winning side's positives (57% to 54%).

> **The same counts as a fit.** Each verdict (positive +1, negative −1, mixed or unclear 0) fitted
> against the code's grade of the decision and whether the side won. 19 games, 482 observations, the
> grade per role per game: weight on the side winning +0.74 against +0.33 on the grade; after de-halo
> +0.50 against +0.29. 40 games, 1,472 observations, each against its own decision's grade: +0.80
> against +0.40; after de-halo +0.53 against +0.36. Vote and discussion verdicts follow the result
> most (+0.84 each). Runner: `evaluation/experiments/v8_verdict_halo.py`; data `data/halo/`.

The verdict reaches synthesis (each observation is shown with it), the observation dedup (different
verdicts are never duplicates) and the replay's verdict stamp. It never reaches a seat or credit,
which uses the grade.

*How sure we are.* The grade is computed by code and never sees who won, so the comparison uses a repeatable scoring rule rather than another model's judgement. The rule is still a proxy for decision quality; outcome association alone does not prove that each verdict is biased. The de-halo pass revised 25–29% of verdicts across the three extraction runs, and a
read of one game's 19 revisions found most fair and a few over-corrected (a Fortune Teller's death
after declining the self-bet turned "unclear", although the self-bet gives immunity by rule). The
judge varies between runs. Which signal, verdict or grade, writes better lessons is not known.

### 3.4 Can each observation be matched to its decision?

**The tag and the model reader agreed in 98 of 102 cases.** The 2,277 observations of the 40 games were tagged with their
decision by Claude Haiku 5.5, one batched request per game ($0.08). A Sonnet reader per game named
each decision from the record without seeing the tag, on six games chosen at random, 17 observations
each: 98 of 102 agreed (96.1%; the record's ±3.8 points treat the 102 as independent, and taking the six games as the unit the 95% interval is about ±5 points, still above the 90% bar), and the day alone 101 of 102. This is agreement with a model reader, not a human-validated accuracy estimate. Three of the four misses were a
wolf's night tagged "several" where the reader chose the skill; one put a Healer's protection a night
early. The bar, set beforehand, was 90%. Of the 2,277 tagged observations, 1,711 could be graded by the
table; the rest describe decisions the table leaves unscored or the record cannot settle (a served
game does not record the night result of a player who died that night).

### 3.5 Does the credit pass run on ten-seat games?

**Once, as a demonstration.** On 2026-10-14, Claude Haiku 5.5 played 20 AI-only memory-on games
(the four lineups five times each, `ten_seat_v2`, stage filter on; about $0.23 a game). Every game
finished; no seat fell back to a random move. The credit pass compared them with the 12 memory-off
seeding games. Of 498 lessons, 148 were followed and scored (42 of them discussion lessons, graded on
the evil sides' rule that a day drawing twice one's share of accusations, or one's own elimination,
is bad); one bad grade was left out
as the seat's own wrong high-confidence read. It pruned 4, evicted 4 and protected 50, leaving 490.

| Removed | Lesson | Follows (good / bad) | Memory-off average | Score |
|---|---|---|---|---|
| Pruned | Illusionist, day discussion: one neutral question at most, or silence | 8 (2 / 6) | −0.07 | −0.27 |
| Pruned | Illusionist, night: spend a conceal only on an unclaimed victim | 24 (9 / 10) | +0.16 | −0.17 |
| Pruned | Necromancer, day vote: abstain with an abstaining room | 8 (0 / 0) | +0.83 | −0.51 |
| Pruned | Trailseer, night: follow a quiet unconfirmed player late | 14 (4 / 8) | −0.06 | −0.17 |
| Evicted | Fortune Teller day vote; two Necromancer nights; Speculator day vote | 0 follows in 8–11 showings, mostly overridden | n/a | n/a |

The Necromancer's vote lesson was pruned on neutral grades alone: an abstention grades neutral, and
memory-off Necromancers' named votes graded well (+0.83), so the lesson falls short of its baseline.
That is the table working as ruled, and the reason a score against the baseline decides, not a raw
rate. At the protected end were votes with the room, or abstentions, for the evil sides (the
Illusionist's day vote, 10 follows, all good, score +0.78; the Chanteuse's, 16 follows, +0.68).

*How sure we are.* Twenty games give at most a few dozen follows per lesson, so these show the pass
working, not which lessons are good. The baselines are the seeding games, read as if played with the
same prompts and model; they were not (owner: a demonstration, not a research result). The run also
found two faults, fixed in three commits deployed the same day: an unenforced reply schema broke 74
seat replies (each retried; six went to the rescue model), and Haiku copied the example's "follow"
onto 426 turns shown no lessons (credit ignored them, as they carried no lesson keys).

### 3.6 Smaller checks that set a choice

| Question | Result | N and caveat |
|---|---|---|
| Is a cheaper extraction model good enough? | 3.8 Flash about $0.34 a game against 2.5 Pro's $1.17, no player ids, read as well grounded; 3.5 Flash-Lite cheaper but wrote player ids into 18 of 43 observations in one game | 2 pilot games, one reading |
| Can Claude extract, batched? | Haiku wrote a player id into 74 of 146 observations, so it was ruled out; Sonnet into 9 of 136 | 2 games; the first run's cache never hit, fixed the same day |
| Are the stored "uses left" counts right? | After defining the count as before the decision: 471 of 527 exact on 3.8 Flash; some-vs-none wrong in 4.4% (Sonnet 5.8% on 191) | Mostly a last use written as 0, which would hide a "spend your last one" lesson; not fixed |
| Does the lesson dedup catch duplicates? | Against the readers' 65 groups, the Flash-Lite judge caught 9 (16 with a looser split); with the looser split, 25 of its 55 drops merged lessons of different stages | 605 lessons, dry run; the published store has the readers' groups applied |
| Does the embedder change hurt retrieval? | Qwen and Gemini shared 81% of the top five, the same first lesson 55%; of five disagreements read, each won 2, neither 1 | 236 stand-in queries; thresholds re-set on labelled dedup pairs |

## 4. What is not known

**Whether memory improves ten-seat play.** No game set compares memory on with memory off. Sized on
the nine-seat power table (a game-level spread of about 0.3), such a test needs about 35 games per arm
to detect a change of +0.20 on the July test's per-game score and about 60 for +0.15 (plan §9.6 item 9); the
table has not been re-run on ten-seat games. The earlier versions' results do not carry over: the
June static-memory A/B reported improvements on selected town decision measures; a later A/B on a
different store, run against a higher no-memory baseline, found no town effect and was not a
replication of the June test; separately, the pre-registered v7 endpoint detected no compounding
benefit. All three ran on nine-seat games at the minimal thinking setting, and
v8 changed much of the pipeline on their evidence. The [memory hub](../report.md) holds those
results; v8 has been tested by none of them.

Smaller unknowns, each tied to the claim it limits:

- **The prune and evict thresholds** are v7's, unvalidated for ten seats. The four prunes above rest
  on them.
- **Whether the credit pass has read a served game.** The record holds one credit pass, over the 20
  batch games. The code reads served games, grading only the AI seats' decisions in a game with a human seat (since 2026-10-26); no credit pass over served games is recorded.
- **The learning tick on ten seats.** `ten_seat_v2` was synthesised by a one-off build, not by the
  tick, and the demonstration stopped at credit. No ten-seat learning tick is recorded, and nothing
  screens the rules in what it would write.
- **Town day lessons reach no one.** They are checked only by the owner's reading, and never earn
  credit, since no seat follows them.
- **Which outcome signal writes better lessons.** A grade-reading store (`v8_grade_synth`, 568
  lessons) is built and unreviewed. A fair comparison needs the verdict variant rebuilt on the same
  code (about $5) and, by the record's estimate, about 1,000 follows per variant.
- **Selection.** Whether extraction picks the moves that mattered has not been measured on ten seats;
  the smoke game's read found it missing one lesson every model missed (the pack's attack on the
  immune Serial Killer told the wolves who the lone killer was).
- **Served memory-on games' lessons.** A served game saves its input, but no job yet extracts served
  games' inputs for their replays, and the replay shows no "lessons being written" notice.

## 5. What is deployed, and since when

From the deploy log (`frontend/docs/deploy_log.md`), separate from what the code at HEAD does:

- **2026-10-11:** the ten-seat game deployed with memory off and the ticket's switch disabled.
- **2026-10-14 (`d41b1c0c`):** the v8 pipeline code (credit, stage filter, synthesis), served games
  saving their extraction input (migration `0012`), and the Qwen embedder.
- **2026-10-14 (`344b9e58`):** lessons read from the Postgres store; the store published from the host
  (2,498 records, 490 strategy points); memory became available and one house-funded memory-on game
  was served. Fixes from the demonstration run (re-asking a broken reply with the schema enforced; no
  verdict field on a turn shown no lessons) were deployed the same day.
- **Live server since 2026-10-26 (`2ecec0cc`):** `dd985ebe` plus one fix. It does not include
  `5367f157` (2026-10-23), which made Sonnet the offline extraction job's default; the job runs from
  the repository, not the server.

What a player gets today: memory is a per-game switch that starts off
(`frontend/src/app/(site)/_components/ticket/TicketOffice.tsx`), available only where the deployment
turns it on (`WW_MEMORY_ENABLED`, `server/config.py`) and a store is published.

## Sources and implementation

| What | Where |
|---|---|
| When a turn looks up; the town day rule | `Agents/memory/retrieval/plan_gating.py::retrieval_plan` |
| The read path: search, caps, tiering, optional filters | `Agents/memory/retrieval/pipeline.py`, `accessors.py`, `filters.py`, `dimension_gating.py` |
| Lookup reuse | `Agents/memory/retrieval/lookup_cache.py` |
| The served configuration | `server/game/run_config.py::game_run_config`; `server/config.py`; `server/routes/_shared.py` |
| The seat's verdict and its counters | `Agents/schemas/output.py::StrategyVerdict`; `Agents/turn/adoption.py` |
| Saved input, offline extraction, de-halo | `Agents/nodes/orchestrator.py`; `Agents/memory/extraction/offline.py`, `dehalo.py`; `scripts/extract_batch.py`, `backfill_extraction_inputs.py` |
| Decision tags and grades | `Agents/memory/extraction/decision_tags.py`; `scripts/tag_observation_decisions.py`, `grade_observations.py`; `Agents/memory/consolidation/grading.py` |
| Fold, synthesis, credit, tick, publish | `Agents/memory/consolidation/` (`obs_fold.py`, `store_ops.py`, `credit.py`, `tick.py`, `config.py`, `publish.py`); `Agents/memory/strategy_synthesis.py`; `Agents/memory/persistence/postgres.py` |
| Building and publishing `ten_seat_v2` | `scripts/build_v8_store.py`, `scripts/publish_v8_store.py` |
| Runners for §3 | `evaluation/experiments/v8_gate_lookups.py`, `v8_stage_filter_replay.py`, `v8_reextract_reads.py`, `v8_verdict_halo.py`, `v8_decision_tag_check.py`, `v8_sp_dedup_dry_run.py` |
| Data for §3 | `data/gate/`, `data/reextract/`, `data/halo/`, `data/decision_tags/`, `data/seeding/`, `data/dehalo_compare/`, `data/extraction_model_comparison/`, `data/embedder_migration/` |
| How each result was reached, in order | [experiment log](experiment_log.md), 2026-10-11 to 2026-10-14 |
| Why each choice was made | [decisions](decisions.md); [plan](plan.md) §9 (§9.5 later rulings, §9.6 the credit port) |
| Run outputs and stores | `batch_results/`, `memory_stores/` (gitignored); each run's manifest carries its commit |

*Written 2026-10-26 from the v8 log, decision record and plan, with each statement about today's
code checked by reading it. No code, tests or experiments were run for this report.*
