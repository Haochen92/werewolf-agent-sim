# Model admission: choosing and switching models

This page covers how the project decides that an AI model may do one of its jobs (play a seat, vote, write
the day summary, extract memory, judge) and with which settings. In industry this is **model migration**:
moving a working system from one model to another without breaking it. Here, with the project still
experimental, it is mostly finding which candidates are usable at all, but the same five questions apply:

1. **Quality:** can the model do each task as well as the current one, or well enough?
2. **Integration:** can the code use it as it is, or does it need an adapter?
3. **Cost and speed:** can it run a live game at an affordable price and a playable pace?
4. **Reliability:** does it keep answering under load, and stay the same model over time?
5. **Rollout and records:** can it be switched in and out safely, and is each decision written down?

**What decides admission today.** While the project is experimental, a model is dropped only when it costs
too much, is too slow for live play, or is too hard to integrate. Quality is measured and recorded, but a
model that does worse stays on the menu: GLM-5.3 Flash (32% of replayed replies with a factual error,
against the default's 9%) and DeepSeek V4.1 Flash (43%) are both listed. MiniMax M3 and Qwen3.8 Flash were
not taken, for latency. Quality would become a reason to drop a model if the game were commercialised.

Each section gives what was done, what it found and how far it can be trusted. The full record of every
run, with error codes, cache floors and the check of the catalogue's notes against the records, is the
[experiment log](experiment_log.md); raw outputs are in [`data/`](data/README.md). The factual-error test set
used for quality is described in [factual_errors](../factual_errors/report.md); prompt layout and caching in
[the caching report](../../caching/report.md). How it all fits together is in [the hub](../report.md).

## In short

- **A candidate passes three checks in order**: short test prompts (integration, cost, speed), a replay of
  saved game turns against the current model (quality), then real games (quality, cost, failures only a
  game shows). Each catches what the one before cannot.
- **Quality is measured, and is not yet a reason to drop a model** (that is cost, latency and integration
  today). Even as a gate it could only reject a clearly worse model, not rank close ones: two runs of the
  same model on the same 70 turns differed by about 6 points. The
  thinking level was searched for votes and discussion turns; the summariser, extraction and the judges
  were checked only lightly, and no judge was recalibrated, because no labelled set exists for them.
- **Integration needed adapters.** A forced tool call silently turned thinking off; a model passed every
  test prompt and answered half its real turns in prose; another reordered its reply on real turns. Each
  calling mode, a retry with the schema enforced, and per-provider cache marks came from these findings.
- **Reliability was learned in live play.** A provider that held requests for minutes led to a 30-second
  request budget, a rescue model on every row and a backup key from a second company.
- **Since 2026-10-24 the checks run as one command per candidate** (§6), with pass criteria written into
  its config before the run and a verdict of admit, reject or incomplete. It has not yet been run on a
  candidate.
- **Not done, against common practice:** a shadow or canary rollout, and a check that a model will play a
  lying role. Pinning was done only where it was available: Claude model IDs are pinned snapshots by the
  provider; the Gemini flash-lite models and DeepSeek offered nothing to pin to, and Luna's page does not
  say.

## Quick view

| Question | What was done | Trust | Main limit |
|---|---|---|---|
| 1. Quality | Replays on the factual-error test set; vote replays scored by code; real games; thinking-level search | 🟡 | Recorded, not yet a reason to drop; rejects only a clearly worse model, cannot rank; Gemini judges; no vote or night turns in the replay; summariser, extraction and judges barely covered |
| 2. Integration | Test prompts per calling mode, on short prompts and real turns; adapters | 🟡 | 27–170 calls per mode; the live check saves no output |
| 3. Cost and speed | Prices with cache and batch rates; cache floors; cost per game; seconds per call; the stage's waits, from served games' traces | 🟡 | Stage fit from 13 served games, 7 on Haiku; limits provisional; cost as right as the price rows |
| 4. Reliability | Request budget, rescue model, backup key; fingerprint and drift guards | ✅ built and deployed | Learned from stalls in live play, not tested before a switch |
| 5. Rollout and records | The model catalogue as a switch; dated notes per row | 🟡 | Several rulings never written down |

✅ sound · 🟡 usable with caveats.

**Where a model lives.** The game's models are rows in a **model catalogue** (database tables `models` and
`model_prices`, seeded from `Agents/llm_factory/catalog.py`). Each row holds the model's thinking level, its
**calling mode** (how a request asks for a structured reply), its rescue model and a note. A running server
re-reads the catalogue every ten seconds.

---

## 1. Quality: can it do each task well enough?

**The question:** on the jobs the project gives a model, does a candidate do as well as the current one, and
at which thinking level is it cheapest while still good enough?

**Per task, what was checked:**

| Task | How it was checked | What it found | Coverage |
|---|---|---|---|
| **Playing a seat** (discussion turns) | Replay of saved turns against the current model, read by AI judges for factual errors | Found two cheap candidates clearly worse (both kept on the menu); Haiku and Luna clearly better than flash-lite at low | Good for factual errors on day turns |
| **Voting** | Replay of saved vote turns, scored by code against the true roles | Haiku at medium right on 61% of votes, at low 41% | 16 vote turns |
| **Whole games** | AI-only games, read against a rubric | A stronger model's replay gain barely showed in games | 4–6 games per model |
| **Day summary** | Haiku against Sonnet, read by one AI judge | A tie, 18 of 30 flawed each | Six days from two games |
| **Memory extraction** | One or two pilot games re-extracted per model | Cost well, quality by direction only | One reader |
| **Judging** | Not checked after a switch | — | No golden or silver set for the judges |

### Replays against the current model

The candidate and the current model each regenerate the same saved game turns several times, and the same AI
judges read every reply for statements that contradict the game's facts. A **bad sample** is a reply with at
least one. A per-turn sign test asks whether the candidate did better or worse on more turns than chance
would give. Two sets of turns were used: **the nine-seat test set** (2026-10-04; 89 of its cases, the random
slice left out, 2 samples each) and **the ten-seat test turns** (2026-10-10 to 10-12; fourteen frozen Phase 3
turns, 5 samples each, 70 per model, each checked against a hand-written expectation).

**Nine-seat.** Luna at medium was the only candidate no worse than the default; both cheap no-thinking
candidates were clearly worse.

| Model | Bad samples | Turns better / worse than default | Sign test p |
|---|---|---|---|
| Gemini 3.5 Flash-Lite, medium (default) | 16/178 (9%) | — | — |
| GPT-6 Luna, medium | 10/178 (6%) | 10 / 4 | 0.18 |
| GPT-6 Luna, high | 19/178 (11%) | 10 / 12 | 0.83 |
| GLM-5.3 Flash, no thinking | 57/177 (32%) | 3 / 33 | < 0.0001 |
| DeepSeek V4.1 Flash, no thinking | 77/178 (43%) | 1 / 48 | < 0.0001 |

**Ten-seat.** Every candidate beat flash-lite regenerated in the same run; two by enough to rule out chance.

| Run | Candidate | Bad samples | Flash-lite, same run | Better / worse | p |
|---|---|---|---|---|---|
| 10-10 | Luna, medium | 10/70 (14%) | 25/70 (36%) | 7 / 2 | 0.18 |
| 10-11 | Haiku, thinking off | 21/67 (31%) | 27/69 (39%) | 6 / 5 | 1.0 |
| 10-11 | Haiku, medium | 11/70 (16%) | 27/69 (39%) | 7 / 3 | 0.34 |
| 10-11 | Haiku, low | 7/70 (10%) | 26/70 (37%) | 8 / 0 | 0.008 |
| 10-11 | Luna, low | 5/70 (7%) | 24/70 (34%) | 8 / 1 | 0.039 |
| 10-11 | Luna, medium | 3/70 (4%) | 24/70 (34%) | 7 / 1 | 0.070 |
| 10-11 | Haiku, low (repeat) | 11/70 (16%) | 24/70 (34%) | 6 / 2 | 0.29 |

### The cheapest thinking level that is good enough

- **Discussion turns.** Haiku at low was as good as at medium on the replay (10–16% against 16% bad) at 9.5
  seconds a turn against 13.7; seats play at low. Luna at low and medium tied case by case (7% and 4%,
  3 turns better and 3 worse) at about 390 against 1,260 reasoning tokens and 8 against 16 seconds.
- **Votes.** On 16 saved vote turns, 10 samples each, scored by code:

  | | Low | Medium |
  |---|---|---|
  | Votes right | 65/160 (41%) | 98/160 (61%) |
  | Discussion samples flawed | 49/115 | 47/115 |
  | Output tokens a vote | 852 | 2,317 |

  Medium was better on 12 vote turns and worse on 1 (p 0.003); errors in the vote's notes did not differ
  (50% against 46%, p 0.21). A majority of three low-effort votes was right as often as one (39% against
  41%), because the same context produces the same wrong belief. Medium for votes was approved on condition
  that a prompt change was tried first; no vote-specific level exists in the code yet.
- **Day summary.** With Haiku's turns fixed at low, summaries the games were played with gave 9% bad turns;
  Haiku rewriting them at low gave 14%, at medium 10% (2 better / 5 worse, p 0.45; 4 / 4, p 1.0). The summary
  runs at medium.
- **Extraction and judges:** no level search.

### Real games

AI-only ten-seat games with one model in every seat and as the summariser, memory off (2026-10-10): six on
Gemini 3.5 Flash, four on GPT-6 Luna at medium, audited by readers who saw the true roles. Flash made about
one invalid deduction per 15 lines heard, flash-lite one per 12, although on the replay Flash had made 1
error in 50 samples against flash-lite's 11: **a replay measures the failures it was built from, and games
show the rest.** Luna made 14 invalid deductions in about 166 lines, 11 of them from reading the Sentinel's
card literally, which exposed a gap in the rules text the looser models never hit.

### Earlier and lighter choices

- **Day-summary model.** Haiku against Sonnet on six days from two games, five summaries each: 18 of 30
  flawed on each, and 3 of the 6 live ones. The first judging was invalid (the judge saw the moderator's
  closing line, which the summariser never sees) and was rerun; the judge was Sonnet, one of the two models.
- **Memory-job models** (October 2026). Gemini 3.8 Flash against 3.5 Flash-Lite on two pilot games, and a
  Claude extraction and a de-halo judge on one game each, counted by one reader. The choice was superseded
  on 2026-10-15, when the offline jobs moved to Claude; batch extraction now defaults to Sonnet 5.5.
- **The July 2026 seat-model choice** ([model_selection](model_selection.md), nine-seat) rested
  on the owner's unblinded reads of one or two games per model. Its method note stands: use public
  benchmarks to shortlist, and measure on the game.

### How far to trust the quality checks

- **Two runs of one model differ by about 6 points.** Haiku at low scored 10% and 16% on the same turns,
  judges and day; flash-lite ranged 34–39% over four runs.
- **The judges are Gemini, the same family as the default they compare against**, and bias was not
  measured. The census reader was hand-checked on 10 of 12 verdicts; the flash-lite golden judge was found
  unreliable; the ten-seat golden judge was never checked on these runs. The summary judge was one of the
  two models it compared.
- **The nine-seat curated cases were chosen from flash-lite's own errors**, which favours a candidate; the
  random slice, which the factual-errors report advises for comparing models, was left out.
- **No vote or night turns in the replay**, and nine-seat and ten-seat numbers do not compare.
- **A judge was never re-checked after its own model changed.** The judges have no labelled set to
  recalibrate against.

## 2. Integration: can the code use it?

**The question:** does every reply come back in a form the game can act on, and do the model's settings
actually take effect?

**What was done** (`eval-model-admission`, pennies per model; one record per model stamped with the git
commit and prompt hash). Every seat schema is asked for several times at temperature 1.0. A reply passes if
it parses, fills the field the game acts on, names a listed player or an allowed token such as "abstain",
and carries the player's reads. The run records reasoning tokens, tries each **calling mode**, and replays
a few real discussion turns through the production template:
- `native`: Gemini's own constrained output.
- `forced_tool`: the model must call a tool whose arguments are the schema.
- `json_schema`: the provider enforces the JSON schema on the reply.
- `auto_tool`: the tool is offered, but the model may answer in prose.
- `json_mode`: the schema is written as text after the prompt, and the reply is checked in code. This is
  the **unenforced** mode.

**What it found** (2026-10-04 nine-seat; 2026-10-11 and 10-13 ten-seat):

| Model | Mode chosen | Real turns failed | Outcome |
|---|---|---|---|
| Gemini 3.5 Flash-Lite | native | 0 of 6 | the default at the time |
| GPT-6 Luna | json_schema (both tool modes refused with reasoning on: HTTP 400) | 0 of 6 | admitted |
| Claude Haiku 5.5 | json_schema (51 of 51; a forced tool call passed 45 of 51 with 0 reasoning tokens) | 0 of 6 | admitted; now the default seat model |
| DeepSeek V4 Pro | auto_tool (forced tool passed 27 of 27 with 0 reasoning) | 3 of 6, in prose | recommendation not adopted; the row keeps the factory's forced tool call, no thinking |
| GLM-5.3 Flash | json_mode | 0 of 6 | admitted without thinking |
| MiniMax M3 | json_mode | 0 of 6 | not taken: too slow (§3) |
| Qwen3.8 Flash | none (no mode passed every call) | 6 of 6 (HTTP 400); 0 of 6 in a second, `json_schema`-only run | not taken: too slow (§3) |

**Four findings, and the adapter each led to:**
1. **A forced tool call turns thinking off without an error.** DeepSeek and Haiku passed under it with 0
   reasoning tokens. → The run counts reasoning tokens and prefers a mode that actually reasons; each
   catalogue row carries its own calling mode.
2. **Real turns fail where test prompts pass.** DeepSeek passed 27 of 27 test prompts and answered 3 of 6
   real turns in prose. → Real-turn failures now count against a mode (the code comment in `admit` cites
   the case).
3. **The unenforced mode is reliable enough, with a safety net.** On 2026-10-13 `json_mode` failed about
   once in 400 calls on Haiku and Luna (170 test calls per mode, twice, plus 24 real turns). → Production has
   used it for both since 2026-10-14, by the owner's decision, and a reply that breaks the schema is asked
   again with the schema enforced (`7f508c4d`). The offline jobs on Claude use it too, because an enforced
   schema is part of Claude's cache key and would stop calls sharing a cache (`d839e6f3`).
4. **Pass counts hid a reordering.** The schemas put the player's reads before the message on purpose, so
   the model commits to its reads before it speaks. Test prompts kept that order 17 of 17 times; Haiku's real
   turns in `json_mode` kept it 15 of 24, and 13 of 23 when told to. → The schemas list the reads first, and
   real turns then kept it 24 of 24.

Two smaller adapters: the factory places Claude's cache marks itself, and OpenRouter requests are pinned to
each maker's own servers.

**How far to trust it.** It shows a model can return replies the game can act on, at 27–170 calls per mode;
its one check of meaning is that a target is a real player. The offline logic is pinned by
`tests/evaluation/test_model_admission.py`, which, like most of `tests/`, is AI-written and unaudited. The
**live check of menu models** (`tests/live/test_model_structured_output.py`, skipped by default) asks every
menu row for every schema once; its only recorded run (2026-09-10) is in its docstring, with no output
saved, and its credential check has no branch for Claude models, so for Haiku it looks for a Google key.

## 3. Cost and speed: can it run a live game?

**The question:** at the game's pace and with real players waiting, what does a game cost, and is each turn
fast enough?

**Price.** Cost is computed from tokens by model and hour (`server/game/usage.py`) and dated price rows
(`Agents/llm_factory/pricing.py`), so fixing a price corrects every game it applied to. Cache reads are
discounted; cache writes cost a premium (1.25× input on Claude and GPT-6, 2× for Claude's one-hour cache);
batch calls, used by the offline jobs, bill at half rate.

**Where caching starts** (smallest tested prompt that read any cache): about 256 tokens for DeepSeek, Qwen and
GLM; partly from 256 and nearly fully from 1,024 for MiniMax; 512 for Haiku; 2,048 for Luna; none found for
Gemini 3.5 Flash-Lite on Vertex up to 3,636 tokens, nor on real turns of 4,155–5,258 tokens. These are
brackets between tested sizes. How the prompt is laid out so turns share a cached prefix is in the caching
report.

**Cost per game** (ten-seat, AI-only, 2026-10-10): Gemini 3.5 Flash $2.72, flash-lite $0.72, GPT-6 Luna
$0.17. Flash's price came from a third-party listing not checked against Google's page.

**Speed.** Seconds per real turn on the 2026-10-04 test prompts: flash-lite 4–8, Luna 6–16, GLM 12–15,
DeepSeek 19–92, MiniMax 23–64, Qwen 37–135. Latency decided three candidates: MiniMax and Qwen were not
taken, and GLM was taken without thinking. On the replay, Haiku at low took 9.5 s a turn and Luna at low 8.1.
The live game gives a request 30 seconds (§4); when that budget was set in September 2026, the slowest
honest turn took 11.

**What "fast enough" means is set by the display.** The server never waits for the stage: it runs ahead,
and the browser plays each beat at its full length, a speech line at 2.4 words a second for 5 to 15 seconds.
So a turn is fast enough when it is finished before the stage reaches it; if not, the stage shows the
speaker thinking and everyone waits. It is now measured from the traces of served games, by replaying each game's beats (cut by the
stage's own code) against the time each event left the server (`frontend/docs/stage_fit/`, 2026-10-24):

| Model | Games | A discussion turn: median, slowest 5% | Stage time spent waiting for the model |
|---|---|---|---|
| Claude Haiku 5.5 | 7 | 5.4 s, 10.8 s | 2.7–5.1% |
| DeepSeek V4.1 Flash | 3 | 3.5 s, 4.5 s | 0.1–0.3% |
| GPT-6 Luna | 2 | 6.4 s, 9.3 s | 2.1–5.3% |
| Gemini 3.5 Flash-Lite | 1 | 5.2 s, 8.0 s | 3.6–4.1% |

On Haiku most of the waiting comes in runs of passes (a pass shows for 4 s, while the next seat's call takes
5.4 s median even when it passes) and at the morning after the pack's night chain (its chat lines, kill and
skills run one after another, about 24 s on night 1). After a speech, which shows for 5–15 s, most turns
fit. Votes, written in parallel, rarely make the stage wait. Seven games is a small sample, all played by
the owner while building, so these limits are provisional.

**How far to trust it.** The arithmetic is exact but only as right as the price rows and the names usage is
recorded under, and both have been wrong: before the October fixes, traces counted OpenAI's cache writes as
free and Claude's cache reads and writes under unpriced names, so some earlier game costs were understated.
Speed was recorded as ranges over a few turns, not as the slowest 5% of calls, which is what keeps a live
player waiting.

## 4. Reliability: does it keep answering, and stay the same model?

**The question:** a model that is good, workable and cheap can still stall under load or change underneath.
What keeps a live game going?

**Learned from live play.** In September 2026 the served game ran on Vertex's shared pool, which held single
requests for 2–5 minutes and then bounced them (HTTP 429). The SDK and LangChain re-sent each bounce several
times, so nothing ever failed and the rescue model never fired; one turn's draft took 301 seconds. What was
built:
- **A request budget:** 30 seconds a request, two attempts, 90 for summaries (`c67d47cb`, 2026-09-30). A
  timeout, a 429 or a server error counts as a stall.
- **A rescue model on every row:** a stalled turn goes to the rescue at once, and after two stalls in a row
  the game's turns start on the rescue for five minutes before the primary is tried again (`c74284cb`).
- **The budget on every provider, and a rescue for the day summary** (`957d0b2e`, `cc4977ea`, 2026-10-21).
  Before, only Gemini had the budget: DeepSeek waited 600 seconds three times before the rescue was asked.
- **A backup key from a second company** (`9f350ea5`): a same-company rescue fails when its company does, so
  a player may give a second company's key, whose fixed backup model (Haiku, Luna, Gemini 3.6 Flash or
  DeepSeek V4 Flash) takes the rescue. The DeepSeek name is not fixed: DeepSeek routes `deepseek-v4-flash`
  to V4.1 Flash since 2026-09-10.

How often it matters: in one flash-lite game, 36 of 115 calls went to the rescue model. A preview model
(`gemini-3-flash-preview`) stalled for about 45 minutes in one replay and is no longer used for evaluation.

**Staying the same model.** A model service can change under an unchanged name: on 2026-06-11 ten games came
back with the villagers winning 10% against 67% in the original batch, with identical prompts and code. Two
backends for one model (Google AI and Vertex) score differently even at temperature 0. So every game record
carries a fingerprint of the model, backend, prompt and commit; comparisons run both sides in one time
window; and the embedding model behind memory search is checked at the start of each batch
([experimental controls](../experimental_controls/report.md)).

**How far to trust it.** The rescue path is deployed and has carried real games; it was built after stalls
in live play, not tested on a candidate before it was switched in.

## 5. Rollout and records: switching safely, and writing it down

**The question:** once a model passes, how is it switched in, how is it switched back, and does anyone know
why it was chosen?

- **The catalogue is the switch.** A row is added, changed or dropped in the database, and the server picks
  it up within ten seconds. Rolling back is editing the row. Every row has a rescue model.
- **Each row's note is the summary of its admission.** Checked against the records on 2026-10-23, seven of
  the ten notes hold, one cannot be re-checked (it rests on a docstring) and two have no record behind them
  (log §10).
- **Rulings not written down.** The latency rejections of MiniMax and Qwen have no written ruling, and the
  seed still lists `json_schema` for Luna and Haiku although production has used `json_mode` since
  2026-10-14. Models that did worse on the replay stay listed by policy (above), not by oversight.
- **The records were on one machine until 2026-10-23,** when the 20 admission records and the replay runs
  were moved into [`data/`](data/README.md), each with its config and where it came from.

## 6. One command per candidate (built 2026-10-24, not yet run on a candidate)

**The question:** until October each check was a separate tool with a hand-written config, read by eye. Can
the checks run as one pipeline with a verdict?

**What was built** (`poetry run python -m evaluation.src.cli_runner.admit --config <file>`). One config
names the candidate and the thinking levels to try, the current model, the case sets to replay and the pass
criteria. The command then:
1. runs the test prompts once per thinking level, through the existing admission runner;
2. replays each case set with the current model first and the candidate at each level, through the existing
   replay runner;
3. scores every vote by code against the game's true roles (the new canonical vote scorer);
4. applies the criteria and names the cheapest thinking level that passes (fewest output tokens per
   sample, reasoning included);
5. writes one report, sectioned by the five questions of this page, and a verdict: **admit**, **reject**,
   or **incomplete** when a criterion could not be measured.

`--plan` writes the configs and prints how many model calls each step will make, running nothing (the worked
example, GPT-6 Luna at low and medium against Haiku, is at most 2,730 calls). `--from-existing` re-gates
outputs already on disk at no cost. Real games stay a manual step after it.

**The criteria in the worked example** (`evaluation/config/template/admission_example.json`):

| Question | Criterion | Value | Where it comes from |
|---|---|---|---|
| Integration | The chosen mode passes every test call, fails no real turn, and reasons when thinking is asked for | — | DeepSeek's prose replies; the forced tool call that turned thinking off (§2) |
| Quality (advisory today) | Bad-sample rate no more than this many points above the current model's, and not significantly worse by the sign test (p 0.05) | 6 points | Two runs of Haiku at low scored 10% and 16% (§1) |
| Quality (advisory today) | Votes right no more than this many points below the current model's, and not significantly worse | 10 points (provisional) | Derived from sampling spread (about 4 points an arm at 160 votes); no vote rerun spread measured. **Owner's call** |
| Speed, discussion set | Median and slowest 5% seconds per sample | 5.5 s and 11 s (provisional) | No slower than Haiku, whose stage waits 2.7–5.1% of the time; a median at or under 4 s would keep up through passes (`frontend/docs/stage_fit/`) |
| Speed, vote set | Slowest 5% seconds per sample | 11 s (provisional) | Ballots are written in parallel and rarely make the stage wait; any other set keeps the 30 s request budget (§4) as its ceiling |

**Today's policy is in the command.** A config switch, `quality_rejects`, is off by default: the quality and vote rows are then marked advisory, reported beside the verdict but never a rejection, so only integration, speed and cost can reject. Turned on, for a commercial release, they reject too. The cheapest passing level is still chosen among the levels that failed no check, quality included.

**The vote scorer was checked against the earlier result.** On the saved thinking-level outputs it gives
medium 98 of 160 right exactly, and low 66 of 160 against the earlier 65. The one difference is a day-4 vote
on the Necromancer, who is evil and was alive: the earlier script counted only the Chanteuse as right that
day. A per-case override reproduces 65, and the example config uses the log's evidence-based answer for one
game day, so its reference numbers will differ from 65 of 160. The code is pinned by
`tests/evaluation/test_model_admission_pipeline.py` (8 tests, AI-written like the rest of `tests/`).

## What the checks taught

1. **Test on real turns, not only short prompts.** The prose replies and the reordered fields passed every
   short prompt and failed on real ones.
2. **Check that a setting took effect.** A forced tool call turned thinking off without an error; only the
   reasoning-token count showed it, as it showed that Gemini Flash-Lite's "minimal" level gave no reasoning.
3. **A gate, not a ranking.** With a 6-point rerun spread at 70 samples, a replay rejects a clearly worse
   model and cannot order close ones.
4. **A replay measures the failures it was built from; games show the rest.**
5. **Reliability is part of fitness.** A model can be good and cheap and still unusable when its provider
   holds requests for minutes; the rescue path is what made live games possible.

## Not done, against common practice

| Practice | Why it matters here | State |
|---|---|---|
| **Pass criteria fixed before a run** ("no more than N points worse than the current model") | Without them, a gate is judged after its result is known | Each past run was read afterwards; criteria now live in the admission config (§6), not yet used on a candidate |
| **Shadow or canary rollout:** the new model on a share of live games, watched before everyone gets it | Games show failures the replay cannot | Switches went straight to the catalogue |
| **A check that the model will play a lying role** | A wolf that refuses or softens a lie breaks the game | Not seen in the records |
| **Pinned model snapshots, deprecation dates, tokenizer and context changes** | A new tokenizer changes prompt length and cache floors; an alias can move | Pinned where the provider allows it (checked 2026-10-25): `claude-haiku-5-5` is a pinned snapshot, though Anthropic's serving infrastructure can still change; `gemini-3.1-flash-lite` and `gemini-3.5-flash-lite` have no numbered version; DeepSeek's names move (`deepseek-v4-flash` routes to V4.1 Flash since 2026-09-10); `gpt-6-luna` is its own default snapshot, with no dated version. What each pin covers is in [experimental controls](../experimental_controls/report.md), §1. Drift is guarded by the fingerprint after the fact |
| **Tail latency** (the slowest 5% of calls) | It is the wait a live player feels | Measured per graph node from served games' traces (§3); the §6 gate computes it per case set |
| **Recalibrating the judges after any model change** | A judge is a model too | No labelled set for the judges |

## What we would do differently next time

| Stage | Change | What was done | What it would buy |
|---|---|---|---|
| Quality | **1. Write each task's pass criteria before the run** | Results were read afterwards; built into the §6 command on 2026-10-24, after the runs on this page | A gate that can fail a candidate on its own terms |
| Quality | **2. Cover every task in the replay, with vote and night turns, and compare on the random slice** | Day discussion turns and 16 vote turns; summary and extraction on a few games | Each job's model checked on the decisions that matter |
| Quality | **3. Judge with a model from neither side, checked against an owner-labelled sample, and run each candidate twice** | Gemini judges for a Gemini default; one run per arm | A comparison no family preference can tilt, with its own spread |
| Integration | **4. Save every run's output, the live check's too, under the run's id** | Records sat on one machine until 2026-10-23; the live check saves nothing | Every catalogue note traceable to a record |
| Cost and speed | **5. Derive each phase's latency limit from its display time, and time one game per candidate against it** | Derived on 2026-10-24 from 13 served games' traces, after the models on this page were chosen | The live-play decision made on the wait players would feel |
| Reliability | **6. Put each candidate through a stall drill before it goes live** | The rescue path was built after live stalls | A provider's failure mode known before players meet it |
| Rollout | **7. Roll out to a share of games first, and write each ruling into the catalogue note with its record id** | Straight switches; several rulings unwritten | A switch that can be watched, and a menu that explains itself |

**Bottom line.** The project's admission covers the five questions of a model migration unevenly. Quality and
integration are checked before a model goes live, and caught failures a short check would have missed. Cost
and speed are measured and decided three candidates. Reliability was built after live play showed what a
stalling provider does, and it is now the strongest part. The weak points are the quality check's judges and
coverage, latency limits derived from seven games only, and the rollout's missing written rulings.

## Sources

| What | Code | Record |
|---|---|---|
| Test prompts (admission run) | `evaluation/src/cli_runner/model_admission.py` (`eval-model-admission`), `evaluation/src/model_admission/{probes,seat_schemas}.py` | [`data/`](data/README.md) (20 records, 2026-10-04/11/13); configs `evaluation/config/model_admission/*.json`; [log](experiment_log.md) §1 |
| Live check of menu models | `tests/live/test_model_structured_output.py` | docstring note of 2026-09-10; log §2 |
| Replays against the current model | `evaluation/src/cli_runner/regen_replay/both/hallucination_bench.py` (`eval-hallucination-bench`) | [`data/`](data/README.md) (`admission_bench_*`, `phase3_*`, `shared_prefix_luna_2026_10_13`); configs `evaluation/config/model_admission/bench_*.json`, `evaluation/config/hallucination_bench_phase3_*.json`; log §3 |
| Thinking level for votes | `evaluation/experiments/haiku_effort_{cases,score}.py` | `reasoning_failures/experiment_log.md` §2; `reasoning_failures/data/haiku_effort_replay/`; log §4 |
| Day-summary model | `evaluation/experiments/haiku_summary_compare.py` | `reasoning_failures/experiment_log.md` §3; `reasoning_failures/data/haiku_summary_compare/`; log §5 |
| Real games | `evaluation/experiments/phase3_capture.py` | `game_play_enhancement/data/phase3_{flash,luna}_games/README.md`; `discussion_evidence.md` §8.4; log §6 |
| Memory-job models | `evaluation/experiments/{claude_extraction_compare,dehalo_compare}.py` | `memory_system/v8/experiment_log.md` (2026-10-11); `memory_system/v8/data/{extraction_model_comparison,dehalo_compare}/`; log §7 |
| July choice | none | `model_selection/report.md`; log §8 |
| Cost, cache and batch pricing | `Agents/llm_factory/{pricing,catalog}.py`, `server/game/usage.py`, `evaluation/src/core/costs.py`, `evaluation/experiments/game_cache_share.py`, `scripts/model_catalog.py` | `caching/report.md` §4–5; `caching/experiment_log.md` §11; log §9 |
| Request budget, rescue, backup key | `Agents/llm_factory/health.py`, `Agents/turn/agent_player.py` (`_STALLED`), `server/game/model_catalog.py` (`BACKUP_MODELS`) | commits `c67d47cb`, `c74284cb` (2026-09-30), `957d0b2e`, `cc4977ea`, `9f350ea5` (2026-10-21); `frontend/docs/server_design_notes.md` ("Stalls") |
| Drift guards | `Agents/run_fingerprint.py`, `evaluation/src/audits/embedding_canary.py` | [experimental controls](../experimental_controls/report.md); `model_drift/drift_surfaces_and_guards.md` |
| Catalogue notes against the records | `Agents/llm_factory/catalog.py` (`SEED_MODELS`) | log §10 |
| Stage fit (does the model keep ahead of the stage) | `evaluation/experiments/stage_fit.py`; `frontend/scripts/beats-for-log.ts` | `frontend/docs/stage_fit/README.md`, `results.json` (2026-10-24) |
| One command per candidate | `evaluation/src/cli_runner/admit.py`; `evaluation/src/model_admission/{gate,vote_scoring,schemas}.py`; example `evaluation/config/template/admission_example.json`; tests `tests/evaluation/test_model_admission_pipeline.py` | §6 (built 2026-10-24) |

*Rewritten 2026-10-24 as a plain summary of the 2026-10-23 write-up, which is kept whole as the
[experiment log](experiment_log.md), and organised around the five questions of a model migration. The model
choices themselves belong to the design folders named in the log.*
