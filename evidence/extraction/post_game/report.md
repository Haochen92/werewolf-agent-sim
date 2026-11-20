# Post-game extraction: turning a finished game into stored observations

**Scope:** how a finished ten-seat game becomes *observations*, the raw material of the agents'
memory: what an observation looks like, how the offline job writes them, how their quality is
checked, and the May 2026 study that set the job's shape (one model call per role, not one for the
whole game).
**Revised against the code:** 2026-10-22 at `c0732f88` (the extraction package, the post-game node
and the batch script have no uncommitted edits). On 2026-10-26 the halo, Claude batching and cost
passages were cut to summaries of their home reports, and the Gemini cost reconciled with caching.
**Companion docs:** [`experiment_log.md`](experiment_log.md) (the same work in date
order) · [the v8 record](../../memory_system/v8/experiment_log.md) (the ten-seat extraction runs,
2026-10-11 to 10-13) · [observation quality](../observation_quality/report.md) (the verdict halo, in full) ·
[the judge write-up](../../evaluation/llm_judge/extraction.md) · [credit](../../credit/report.md) (what
happens to the lessons made from observations) · [caching](../../caching/report.md) §3.1, §3.6 and
§4.6 (the shared prefix, batching, and the Sonnet run's cache writes in full).

> **Orientation: where extraction sits.**
>
> **a game ends and saves its record → (later, offline) one model call per dealt role and phase
> reads the whole game → observations → checked for duplicates and written to a store → synthesis
> turns clusters of observations into lessons → a seat in a later game is shown a few lessons**
>
> Extraction is the write side of memory. Nothing downstream can add what it never wrote down.

---

## 1. What extraction does

The agents keep a memory of past games. It holds two kinds of record:

- An **observation** is a short factual account of one move in one past game, seen from the role
  that made it: the board at that moment, what the role did, and what came of it. A model writes
  observations after the game, knowing every hidden role.
- A **lesson** (stored as a *strategy point*) is a piece of advice for one role in one kind of
  situation. A separate step, *synthesis*, writes lessons from clusters of similar observations
  across many games. The [credit report](../../credit/report.md) covers how lessons are scored.

Extraction writes observations. Its reader is the store, not a player: dedup compares each new
observation with what the store holds, and synthesis reads them in clusters. In served games a seat
is shown lessons only, never raw observations.

**Who writes it.** An offline job run by hand (`scripts/extract_batch.py`). It reads the extraction
input that every game saves when it ends: the roles, the day discussion, the wolves' night chat, the
exact night actions, each seat's last strategy note and the outcome.

**One observation, as stored.** This one comes from a ten-seat pilot game of October 2026, extracted
by Gemini 3.8 Flash for the Trailseer's night (the Trailseer follows one player each night and learns
where they went). Field names are the schema's own:

> **situation:** Entering the first night with no voting record or role reveals from day one,
> requiring a blind tracking choice across the village to catch night movement.
> **information_landscape:** Information-starved regime with zero deaths, zero revealed roles, and no
> public investigative claims yet established.
> **players_alive:** 10 · **distance_to_parity:** 4 · **is_swing:** false
> **criticality_stakes:** Ten players alive with maximum buffer before evil parity, allowing low-risk
> baseline information gathering.
> **target_landscape:** Nine other living players with zero public claims or revealed roles,
> requiring an unguided choice among unknown village members to establish early movement baselines.
> **approach:** Followed an unvetted village player into the night to observe their movement without
> any prior public role information.
> **immediate_response:** Observed the target visiting the player who was killed that same night and
> revealed as the vigilante.
> **impact_on_final_game_outcome:** Catching the player at the murder scene forced that player into an
> unsustainable counter-claim against the real investigator, creating the contradiction that led to
> their demise and secured town momentum toward eventual victory.
> **net_verdict:** positive

The first half describes the *situation*: what was true on the board, phrased so that a later search
from a similar moment finds it. A later seat's situation is matched against these fields, so they
must say what made the moment distinctive, not just "night 1". The second half is the move and its
effect. The one-word `net_verdict` is the model's judgement of whether the move helped its side.
§4 shows why that word is the least reliable part of the record.

Source: `evidence/memory_system/v8/data/extraction_model_comparison/gemini-3.8-flash_cc80ecdf.json`.
Observations written since 2026-10-13 also name the decision they describe (`decision_day`), and the
limited-use roles record how many uses they had left.

## 2. What runs today

| Part | Status |
|---|---|
| A finished game saves its extraction input, with no model call | Live in the game graph (the post-game node), for batch games and served games |
| The offline extraction job (`scripts/extract_batch.py`) | Built; run by hand, no schedule |
| The de-halo pass (a second model that rewrites unsupported verdicts) | On by default inside the job, on Claude Haiku 5.5 |
| Writing extracted observations into a store | Built (`tick learn --extracted`, and the store builder used for the ten-seat store) |
| Showing a served memory-on game's lessons in its replay once extracted | Not built. The database column for it exists, and nothing writes it |
| Memory in served games | A per-game choice that starts off; the production deployment allows it (`WW_MEMORY_ENABLED`) |
| Extraction inside a live game | Removed on 2026-10-12 by the owner's ruling |
| One call for the whole game, or one per role for the nine-seat game | Still in the package; used only by old store builders and experiments |
| Strategy points written per game | Off; lessons come only from synthesis across games |

The current ten-seat lesson store, `ten_seat_v2`, was built from 40 games extracted by this job:
19 on Gemini 3.8 Flash and 21 on Claude Sonnet 5.5.

## 3. How the job works

**One call per role per phase.** For each game, the job makes one model call for each role that was
dealt and each phase that role acts in: the day discussion, the day vote, and the night. A villager
has no night action, so it gets two calls. A ten-seat game comes to about 30 calls. Each call is told
which role and phase it covers and writes only that role's observations for that phase.

A single call for the whole game was the first design. It wrote most about the roles that dominate
the transcript and little about the rest, and a dedicated call fixed that (§5). The day was split
into discussion and vote for the same reason: one day call filed nearly every observation under the
vote, leaving the discussion empty.

**The shared prefix.** All of a game's calls begin with the same long text: the game's rules, the
extraction rules, and the whole game record. Only a short tail differs, naming the role and phase
and listing the fields to fill. The model provider caches that shared beginning, so it is paid for
in full once per game and read cheaply by the other calls.

**The rules every call follows** (in `Agents/prompts/extraction/cell.py`):

- **Naming:** never a seat id such as `player_2`, which means nothing in another game. Players are
  named by role or by behaviour ("the quiet player you watched").
- **Perspective:** the move described is always the assigned role's own, never what the other side
  did.
- **Evidence:** keep only lessons the record supports. A move followed by an event is not proof that
  the move caused it.
- **Outcome is not credit:** a side's win does not make each of its members' moves good. A move the
  record does not tie to a result is "unclear".
- **Situation fields describe the board, never advice.** How to act is the lesson's job, not the
  observation's.

**How the job runs on Claude.** The project's extraction model is Claude Sonnet 5.5, the code default
since 2026-10-15, when the Gemini credits ran out. It was chosen on cost, on how often a model leaked
seat ids, and on a side-by-side read of the same games (§4). The batch script defaults to it too
(until 2026-10-22 it defaulted to Claude Haiku 5.5, which §4 rules out). The job sends the calls as a
Message Batch, Anthropic's half-price offline queue. Each game's first call goes direct and writes
the shared prefix to a one-hour cache before the rest go in the batch, and each call's output schema
goes in as text after the prefix and is checked in code, because on Claude an enforced schema is part
of the cached beginning and every role and phase has its own; why, and what it cost, is in
[caching](../../caching/report.md) §3.6 and §4.6.

A reply that fails validation goes into a second batch the same way. Only what fails again is sent
direct with the schema enforced and no cache marker. A call that still fails is recorded as missing,
and the rest of the game's observations are kept.

**The same job on Gemini.** Naming a `gemini-*` model runs the older online path: the same calls,
with an explicit context cache built once per game. The 19 Gemini games of `ten_seat_v2` went this
way.

**After extraction.** The job runs the de-halo pass as a second batch (§4). Writing to a store is a
separate step: each game's observations are checked against the store for duplicates as they go in.
A game with a human seat is never written to a store.

## 4. How the output is checked

None of these checks is a benchmark. They are counts that a script can make, and reads by one
reader of a few games.

### Seat ids in the text

A script counts observations that contain a seat id. It needs no judge, and it decided the model
choice twice.

| Model | Games | Observations with a seat id |
|---|---|---|
| Gemini 3.8 Flash | 19 | 1 of 872 |
| Claude Sonnet 5.5 | 21 | 18 of 1,405 (1.3%) |
| Claude Haiku 5.5 | 2 | 74 of 146 (51%) |
| Gemini 3.5 Flash Lite | 2 | 5 of 45 and 18 of 43 |

Haiku and Flash Lite were cheaper and were ruled out for this. The naming rule itself was added in
May 2026, after the same count found seat ids in 306 of 363 observations (84.3%) of the earlier
nine-seat extractions.

### Are the facts right?

Claude read one smoke game's 43 observations against the engine's records: 42 were factually
correct, and one invented a detail. An earlier read of the 66 observations Gemini 3.8 Flash wrote
for two pilot games found one factual error. Its cause was in the input, not the model: the game
state dropped the night record of a player who died that night, so the extractor guessed that
player's last move. The saved input now
carries every night's full record, with a mark where the player was never told the result. These are
single reads by one reader.

### The verdict follows who won (the halo)

The one-word verdict is the least reliable field: with every hidden role known, the extractor tends
to call a winner's moves good and a loser's moves bad, which the project calls the *halo*. On 1,472
observations from the 40 ten-seat games, a move that the fixed rule table credit uses grades as good
was called positive 83% of the time on the winning side and 23% on the losing side; the **de-halo
pass** (a second model, Claude Haiku 5.5, that rereads each observation against the record and
rewrites a verdict the record does not support, usually to "unclear") halved the praise for winners'
bad moves (18% to 9%) but left that gap at 75% against 21%. The measurement and its limits are in
[observation quality](../observation_quality/report.md) §4, "How strong the halo is, and what de-halo
does".

What follows from this:

- The verdict never reaches a seat or credit. Synthesis, dedup and the replay see it.
- Each observation also carries the rule-based grade of its decision. Synthesis can be set to read
  the grade instead of the verdict (`synth_outcome`). Which gives better lessons has not been
  compared.

Record: [v8 decisions](../../memory_system/v8/decisions.md) §13; the earlier nine-seat finding is in
[observation quality](../observation_quality/report.md).

### The automated judge, and why it is only a floor alarm

In May 2026, before the ten-seat game, an AI judge scored nine-seat extractions from 1 to 5 on
several qualities. Its first run on 48 games found two problems, both in the judge itself:

- It scored *epistemic compliance* (not claiming knowledge the role could not have) on observations.
  Observations are written after the game with every role known, so this rule applies only to advice.
  Scoping it to advice moved the average from 2.81 to 4.00.
- It scored *specificity* on the one-line situation alone. The search actually matches the situation
  together with its descriptive fields. Showing the judge those fields moved the average from 3.19
  to 3.88.

Once fixed, the original qualities sat at the same high score on almost every game (for example,
grounding scored 4 out of 5 on all 48). Scores that uniform cannot rank one extraction above
another. The judge can flag a broken extraction; it cannot certify a good one. It has no human-labelled answer key
behind it, and no run on ten-seat extractions is recorded.

### Cost

| Model, as run | Games | Cost | Per game |
|---|---|---|---|
| Gemini 3.8 Flash, online with its cache | 19 | $10.42: $10.33 extraction, $0.09 de-halo | about $0.55 (71% of it the model's thinking) |
| Claude Sonnet 5.5, batched | 21 | $19.99 | about $0.95 |

The Sonnet run cost about twice its estimate of about $9.50, mostly in cache writes from retried
replies and from batched requests that missed the cache; the breakdown, and the retry path added
afterwards (§3, with no run recorded), are in [caching](../../caching/report.md) §4.6. A two-game
check estimated Sonnet at about $0.45 a game with the cache working.

## 5. Case study: one call for every role starved the rarer roles

**Verdict.** In May 2026 the extractor was one model call per nine-seat game, covering every role.
It wrote little about the healer and the investigator, the roles with the least airtime. Giving each
role its own call fixed this. The automated judge first marked the fix down; the decision was made on
a manual read. The same failure later reappeared inside the ten-seat day call.

**What happened.** One call was asked for four to eight items per role. It spent its budget on the
roles that fill the transcript, the wolves and the villagers. With Gemini 2.5 Pro, the strongest model
then used, the judge scored healer coverage at 1.20 and investigator coverage at 1.40 out of 5, on 5
games. A manual read showed what that meant. Five of the eight healer observations across those five
games were versions of one moment: night one, no information, choose whom to protect.

**The fix.** One call per role, all reading the same game, their outputs merged. On the same 5 games:

- healer coverage rose to 3.40 and investigator coverage to 3.80;
- per-role healer observations covered the whole arc of the role (first-night choices, what followed
  a save, the wolves' retaliation, the healer under suspicion), 19 to 21 of them across the 5 games;
- asked to pick the better output for each game and role, the judge chose the per-role output in 16
  of 20 pairings, including 5 of 5 for the wolf and 5 of 5 for the investigator. The single call won
  only the villager, 3 of 5, the role it already favoured.

**Why the judge first marked it down.** On the cheaper Gemini Flash models, the first per-role runs
scored lower on *diversity*. The judge saw the same event described from four roles' points of view
and read it as repetition. For a memory searched by role, a wolf's account of a vote and a healer's
account of the same vote are different records. The judge looked at the surface of one output, so it
could not see the information the other design lacked. A manual read of the investigator's
observations showed the gain: with the cheapest model, the single call wrote one investigator
observation per game, and the per-role call wrote three or four, covering choices the single call
never mentioned (whom to check, and what to do when every check comes back innocent).

**What it shows.** A model asked to cover several things in one answer gives most of the answer to
whatever dominates its input. The ten-seat pilot of October 2026 showed the same thing one level
down: a single day call per role filed nearly every observation under the vote, because a day's
talk ends in a vote. Split into separate discussion and vote calls, one re-extracted game went from 0
discussion observations to 16.

**Limits.** Five games of the older nine-seat game, scored by an uncalibrated judge, on models and an
output format that are no longer used. The size of the gain is not established. Its direction
held: with each of the four models tried, the per-role output covered the investigator more fully.
The ten-seat split was checked on one game.

## 6. What is not established

- **That extraction helps play.** No measurement links observation quality to how memory-on agents
  play. On the nine-seat game, the June static-memory A/B reported improvements on selected town
  decision measures, and the pre-registered July test of the learning loop detected no compounding
  benefit ([the memory hub](../../memory_system/report.md)); the ten-seat memory has not been tested
  at scale.
- **Recall.** Nothing measures how many of a game's important moments the job captures. The one
  attempt, on three nine-seat games in June 2026, used a metric that rewarded wordy observations and
  was overturned by a manual read.
- **Whether de-halo verdicts or rule-based grades give synthesis better input.** Both are stored;
  the comparison has not been run.
- **Judge calibration.** The automated judge was corrected against its own design intent, never
  against human labels, and has not been run on ten-seat output.
- **The batch job's current retry path at scale.** It was added after the 21-game Sonnet run, and
  no run with it is recorded.

## Sources and implementation

| What | Where |
|---|---|
| Saving the extraction input at game end | `Agents/nodes/orchestrator.py` (`post_game_analysis`) |
| The offline job: calls, batching, cache warm-up, retries, de-halo, store write | `Agents/memory/extraction/offline.py`; entry `scripts/extract_batch.py` |
| One call per role and phase | `Agents/memory/extraction/cell_units.py` |
| The Gemini online path and the older single-call and per-role extractors | `Agents/memory/extraction/extraction_agent.py` |
| Extraction prompt and its rules | `Agents/prompts/extraction/cell.py`; prefix builder in `Agents/memory/extraction/inputs.py` |
| Observation fields | `Agents/schemas/memory.py` (the cell observation classes) |
| De-halo pass and its settings | `Agents/memory/extraction/dehalo.py`; `DehaloConfig` in `Agents/memory/persistence/config.py` |
| Default extraction model | `Agents/llm_factory/accessors.py` (`DEFAULT_PRO_MODEL`) |
| Claude batching and the schema-as-text mode | `Agents/llm_factory/providers/anthropic.py` (`batch_parse`, `parse_with_claude`) |
| Folding extracted games into a store | `tick learn --extracted` in `Agents/memory/consolidation/tick.py` |
| Served retrieval shows lessons only | `server/game/run_config.py` (`retrieval_types_config`) |
| Tests (19 cases, passing at `c0732f88`) | `tests/memory/test_offline_extraction_job.py`, `test_postgame_per_cell.py`, `test_extraction_fanout.py` |
| Ten-seat extraction runs, costs and seat-id counts | [v8 log](../../memory_system/v8/experiment_log.md), 2026-10-11 to 10-13; run outputs in `batch_results/extraction_runs/` (not in git) |
| The verdict halo | [v8 decisions](../../memory_system/v8/decisions.md) §13; `evaluation/experiments/v8_verdict_halo.py` |
| The May 2026 judge runs (48 games) | `eval_sets/extraction_v1.jsonl`, `eval_configs/`, `eval_results/extraction_eval_20260524_*.jsonl` |
| The May 2026 per-role study | `model_comparison/` (Phase 6 files: `gemini-2.5-pro_5games*`, `per_role_judge_*_1219*`, `comparison_*_121952`) |
| The judge | `eval-extraction` (`evaluation/src/cli_runner/regen_replay/judge/extraction_judge.py`) |
