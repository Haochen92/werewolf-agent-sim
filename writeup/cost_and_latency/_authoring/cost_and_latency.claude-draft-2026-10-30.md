# Cost and latency chapter (draft)

*Level 1 page, second draft of 2026-10-30, written as a self-sufficient chapter page with no Level 2
pages. Revised from the first draft on the owner's notes: concept first, the project's measurement as the
illustration; no stated budget figure; served-game costs lead. Not reviewed; nothing approved. The
chapter's plan is [`content_plan.md`](content_plan.md); the authoring brief is
[`_authoring/cost_and_latency.brief.md`](_authoring/cost_and_latency.brief.md). Lines marked **Exhibit**,
**Link** and **Depth** are specs for the page, not page copy.*

---

## Page copy (draft)

### Cost and latency: what a game of agents costs, and how long a person waits for it

In a game played by agents, every decision is a model call. Ten seats speak, vote and act at night
over four to six days, and each call carries the whole situation with it: the rules, the seat's role
and private knowledge, the day's transcript so far and an account of the earlier days. A game of this
kind therefore makes a few hundred calls, each with a long input, and its players reason before they
answer, which is billed as output. Two costs follow. The first is the bill. The second is time: when a
person sits at the table, the discussion runs one speaker at a time, and every AI turn before theirs
is something they wait for.

The aim on cost is the lowest bill at which the agents still play well, because the price of a game
is what decides whether it can be offered at all. The aim on time is a wait the person does not
notice. Both are worked on with the same set of levers: which model does which job, how much it
reasons, how prompts are laid out for the provider's cache, how much of the game's work is allowed to
exist, and what can be moved out of the live game altogether. Each lever has a price of its own, and
each saving below was checked in real games. Several came out smaller than the token arithmetic
promised.

#### Where the bill comes from

A call is billed in two parts. Input is what the model reads, priced in three bands: ordinary input,
input the provider has already processed and serves from its cache at about a tenth of the rate, and
input it writes to that cache, at a premium. Output is what the model writes, including its reasoning,
at several times the input rate: four to five times on the models used here. So a game's bill depends on how
many calls it makes, how much each one reads, how much of that reading repeats, and how much each one
writes.

The calls differ in all four. What each kind reads and produces:

| Call | Reads | Produces | In a game |
|---|---|---|---|
| Discussion turn | Rules, role, transcript, earlier days, the seat's notes | A spoken line, a private assessment of the others, updated notes | The most calls, and the most output |
| Vote | The same, after the whole discussion | A short decision after long reasoning | Ten a day, fewer as seats die |
| Night action | The same, plus the role's private results | One target | A few a night; the wolves also chat first |
| Day summary | A whole day's lines | Structured fields code reads back | One a day |
| Memory lookup (memory on) | The situation | A search query, then the lessons retrieved | One per seat per day, more for votes |
| Filters | One line against the day's lines | Hold or publish | One per open-floor line |

Two things follow from the table. Nine tokens in ten are input, because every call rereads the same
growing transcript; so the input looks like the cost. But the output is written at four to five times the
price and half of it is reasoning, so in money the two halves are close. In sixteen AI-only games on
Claude Haiku 5.5, about half of all input was read from cache and output was still about half of the
bill. The model's price and how much it writes decide most of the cost; the length of the game decides
the rest. One memory-on game ($0.215, 197 calls) shows the split by call type: discussion $0.110, memory
lookups $0.034, night actions $0.028, votes $0.025, the day summary $0.011, the filters $0.004.

**Exhibit.** That split as one horizontal bar, captioned "one game, memory on, Haiku 5.5, 2026-10-13".

#### What a game costs today

Finished games on the site, priced from their recorded tokens at each model's rates on the day, have
cost about $0.09 to $0.15 in model calls on the four models players can choose: GLM 5.3 Flash,
DeepSeek V4.1 Flash, GPT-6 Luna and Claude Haiku 5.5, Haiku at the top of that range. A human's seat
makes no calls, so a served game costs less than the same game played by ten agents: the sixteen
AI-only Haiku games with memory off cost $0.08 to $0.26 each, $0.16 on average, the spread being
length (about 105 calls in a four-day game, 254 in a six-day one). Hosting is not counted in any of
these figures.

Those are all models of the smallest class. To see what the next classes would cost, the recorded
tokens of two games were repriced at other models' list rates, as if each model had written exactly
what Haiku wrote:

| Model | Memory off (average of the 16 games) | Memory on (the game above) |
|---|---:|---:|
| Claude Haiku 5.5 (measured) | $0.16 | $0.21 |
| GPT-6 Luna | $0.16 | $0.21 |
| DeepSeek V4.1 Flash | $0.20 | $0.27 |
| Gemini 3.5 Flash-Lite | $0.63 | $0.87 |
| Gemini 3.6 Flash | $2.33 | $3.20 |
| Claude Sonnet 5.5 | $3.03 | $4.18 |
| Claude Opus 5.5 | $6.05 | $8.35 |

This is an illustration, not a measured game: a stronger model would not write the same tokens, Opus
cannot turn its reasoning off where these seats ran at low thinking, and each model tokenises
differently. No Sonnet or Opus game has been played in the seats, so it says nothing about how they
would play. What it shows is the size of the step. The next class up costs fifteen to forty times a
Haiku game before anyone has checked whether it plays better, so the smallest class is where the
choice is made, on quality and on waiting.

#### When a person waits

A call's latency and a person's wait are different quantities. The browser plays a game as a stage:
each spoken line is shown at reading pace, five to fifteen seconds, a pass for four seconds, a verdict
for six. The server never waits for the stage; it works out the next action while the stage is still
showing the last one. So the visible wait is the call's time minus whatever the stage still had to
show, and a six-second call behind a ten-second line costs the person nothing.

What the stage still has to show depends on the order of the work. Votes are written in parallel,
behind the vote's own beats, so they rarely wait. A discussion turn depends on the line before it, so
it is on the critical path; and a pass, shown for four seconds, gives the next call the least cover.
At night the wolves' chat, kill and skills run one after another, a chain that can outlast what the
stage shows at night.

Measured from the traces of seven games I played on the site while building, replaying each game's
events through the stage's own timing code, the stage on Haiku would have stood waiting for the model
for roughly 3 to 5% of its playing time. The ends of that range are two assumptions about the stage's
backlog across a page reload, not two groups of games. Most of the waiting came in runs of passes (a
pass shows for four seconds; the next seat's call takes 5.4 seconds at the median whether it speaks or
passes) and at the morning after a night (the wolves' chain took about 24 seconds on the first night).
DeepSeek V4.1 Flash, about twice as fast, kept ahead almost always (three games, under 0.3%).

Two trade-offs sit here. Holding a pass longer would hide the pause but make every game longer; that
pacing choice is not made. And whether a stronger model class is slower is untested here. The latency
that has been measured varies with how much the model reasons, which is the next lever.

#### The levers, and what each gave up

Six levers act on the bill and the wait. Four of them run both ways, and more of one thing is less of
another; two only help, and the question is where they stop.

| Lever | What more of it buys | What it costs, or where it stops | Setting here |
|---|---|---|---|
| Model tier | Better play, expected; not tested in the seats | Fifteen to forty times the bill per tier step; whether a bigger tier is slower is not measured here | Smallest tier in the seats; Sonnet for offline extraction |
| Thinking effort | Votes right 62% to 77% at medium | About 1.5 times the output a vote; a discussion turn 6.7 s to 11.2 s, with no gain on discussion | Low in the seats; medium for the day summary; medium for votes open |
| Prompt caching | Input at a tenth once reread; Luna 28% less a call | Input only: Haiku spent the saving on more output and more talk; needs the shared-start layout; works differently on each provider; a write never reread costs more than no cache | Shared-start layout on every provider |
| Bounding the work | Smaller prompts and fewer calls; the summary is about 5% of a bill | A quieter table; a summary can omit or distort; a cap can end a discussion early | Day summary, discussion cap, pass with a gate |
| Offline batching | Half rate, and out of the person's wait | Only work nobody waits for; retries and cache misses paid in full (one run $19.99 against $9.50) | Lesson extraction, run by hand |
| A local model | No API call; 16.6 ms a pair on one core | Only a narrow job, and it must match the API model: the duplicate classifier did not (65 to 69% against 83 to 85%) | None wired in |

**Model tier selection.** A game has several kinds of call, and each has its own binding constraint: a
live seat's turn is bound by the wait and the per-game cost; a call whose output every seat reads is
bound by the damage one error does; an offline job is bound by quality alone, because nobody waits
and the cost can be handled by scheduling. One tier for everything would be chosen on the tightest
constraint and overpay or underperform on the rest. Public benchmarks shortlist a candidate but do not
say whether it follows these rules, returns valid actions or answers in time; that is an admission
run on the game's own tasks. Here the seats run on the smallest class at low thinking. The day
summary, about four calls a game against about 150 seat calls, runs at medium thinking with a
90-second budget, because one error in it reaches all ten seats. Extraction, which writes the lessons
memory keeps, runs on Sonnet: on Haiku 51% of its observations named a seat by its id, which no later
game can match, against 1.3% on Sonnet, and the cost is recovered offline. Bulk jobs such as duplicate
checks run on cost.

**Link:** How a model is admitted to the menu → Evaluation, model admission.

**Thinking level.** Reasoning is billed as output and takes wall time before the first visible token,
so a higher level has to pay for itself on the job it is applied to, and the gain is not uniform
across jobs. On sixteen frozen vote situations replayed ten times each in the live output mode, Haiku
at medium thinking named the actual threat in 77% of samples against 62% at low, writing about 2,120
output tokens a vote against 1,440. On twenty-three frozen discussion turns, replayed earlier under
the enforced output mode, medium made no difference to the error rate and took nearly twice the time.
Medium for votes alone is an open decision, worth roughly the vote share of the bill.

**Prompt caching.** A provider's prompt cache charges about a tenth for a prompt start it has already
processed, and a premium of 1.25 times to write one. It pays when later calls reread what earlier
calls wrote, and it is defeated when the shared part diverges early, when a write is never read, or
when the model spends the saving elsewhere. In a game of seats the natural layout is the part all
seats share first, the rules and then the public transcript, with each seat's own material after it,
so that every seat's turn, vote and night action can read the transcript another seat's call wrote.
Whether that lowers the bill then depends on the model. In paired games with the same deals, the
layout cut GPT-6 Luna's cost per call by 28%. On Haiku the cost per call did not move, because Haiku
reasoned more under the new layout and spent the saving; and its games cost 20 to 25% more, because
its players stopped passing nearly every turn (65 to 87 discussion turns a game). I kept the extra
participation. Whether it plays better is not measured; a factual-error check on eighteen turns showed
no change beyond noise.

The cache is also a per-provider contract, not a flag: a marked boundary on Claude, breakpoints on
OpenAI, automatic on DeepSeek. On Vertex the implicit cache returned no hits in two probes four months
apart and the explicit cache has a 4,096-token minimum, which is one reason a Flash-Lite game cost
$0.72 under the earlier layout. A cache that is written and not reread costs more than no cache.

**Exhibit.** A shared-start / private-tail diagram: the rules and the public transcript every seat
shares, then one seat's role, notes and instructions.

**Depth:** The prompt layout for each provider's cache → Level 3. Why Haiku stopped staying silent →
Level 3.

**Bounding the work.** Model settings and caching change the price of the work; the game's design
decides how much work there is. Without a bound, each day's input grows with every line said, and the
whole of it is reread by every later call. Three mechanisms hold it, each with a cost of its own. The
day summary replaces the earlier days' lines with one structured account, so a seat on day four reads
one summary per past day rather than three days of transcript; it is itself one medium-thinking call
a day (about 5% of the memory-on game's bill), and it can omit or distort what it summarises, so it
exists for fidelity and for code to read as much as for cost. A cap ends the discussion, but lets
each player who is owed a reply take one last turn, so an accusation is not cut off unanswered. And a
player may pass, with a gate that holds a line repeating one already said; the gate runs after the line
is written, so its saving is in what later calls do not have to read, not in the call it checks. The
trade-off of all three is a quieter table: under the earlier prompt layout Haiku passed almost every
opening and most free turns, and one game's second day had no discussion at all.

**Link:** The day's design, the cap, passes and the gate → chapter 1. The day summary and the claim
ledger → chapter 3.

**Offline and batched.** Work nobody waits for should not run while anyone is waiting. Moving it out of
the live game removes it from the person's wait, and makes it eligible for the provider's batch
pricing, half rate for requests that can be answered later. The discount is on eligible requests, not
on the job: retries and cache misses inside the job are paid in full. Here, lesson extraction never
runs during a game; finished games are collected and sent as one batch. One 21-game run on Sonnet cost
$19.99 against about $9.50 estimated, because replies that failed validation were retried in a way
that wrote new caches ($7.02) and 15% of the batched requests wrote the shared start instead of
reading it ($3.01). Retries now keep the shared layout; the saving is not yet measured in a comparable
run.

**Depth:** The extraction run that cost twice its estimate → Level 3.

**A local model instead of a call.** The cheapest call is none. A small model trained for one narrow
job can run on the server for milliseconds, if it does the job as well as the API model it replaces,
which is the whole question. Two memory jobs were tried. A 4-billion-parameter classifier for the
keep-or-discard duplicate decision reached 65 to 69% on 65 labelled cases against 83 to 85% for the
API models, and was closed. A 22-million-parameter cross-encoder for reranking retrieved lessons
matched the API reranker on seventeen turns (NDCG@5 0.882 against 0.871); it is trained and
benchmarked, not wired in. Neither contributes to the costs above.

**Link:** What memory stores and how it is kept clean → chapter 4.

<!--
Sources (page copy → record).

Intro
- A few hundred calls, 4–6 days: evidence/caching/experiment_log.md §17 (104–254 calls, days 4–6). Reasoning billed as output; output at five times input: Agents/llm_factory/pricing.py
  (Haiku and Luna $0.10 / $0.50; DeepSeek $0.15 / $0.60).

Where the bill comes from
- Three input bands and the write premium: pricing.py (cost_usd, WRITE_FACTORS); caching/report.md §5.
- Call table: what each call reads and writes: evidence/caching/report.md §1; Agents/prompts/layout.py;
  lookups per seat per day / per vote: evidence/memory_system/v8/decisions.md §10; the filters:
  evidence/gameplay/data/silence_calibration/README.md (terms).
- "Nine tokens in ten are input", "about half of all input read from cache", "output about half the
  bill", "half of output reasoning": evidence/caching/experiment_log.md §17 (2026-10-30; the 16
  manifests added up by evaluation/experiments/game_cost_reprice.py: mean 1.44M input, 53% cached,
  160k output, 75k reasoning; ≈ $0.08 output of $0.16).
- Memory-on split: content_plan.md §2 (game_cache_share.py on
  batch_results/cache_ab_2026_10_13/haiku_after.jsonl) [re-derived in the plan].

What a game costs today
- Served games $0.09–0.15 (GLM 5.3 Flash $0.09, DeepSeek V4.1 Flash $0.10, GPT-6 Luna $0.11, Haiku 5.5
  $0.15): the owner's reading of the site's ticket office on 2026-10-30, which shows
  `avg_cost_usd` per model from `replays.average_costs()` (server/routes/system.py), priced by
  server/game/usage.py game_cost from stored counts at dated rates. Game counts per model
  (`priced_games`) NOT recorded here; see the brief. Memory-off averages.
- 16 AI-only games $2.48, $0.08–0.26, mean $0.16, 105–254 calls: persona_voice_games/README.md;
  evidence/caching/experiment_log.md §17.
- Repricing table: evidence/caching/experiment_log.md §17; rates in
  evaluation/config/reprice_rates_2026_10_30.json (the catalogue's, plus Opus 5.5 at $4 / $20 / $0.20 per
  million from Anthropic's first-party rates as the Claude API reference lists them, read 2026-10-30).
  "No Sonnet or Opus game in the seats": content_plan.md §7.

When a person waits
- Stage holds, server runs ahead, parallel votes, the pack's chain, 2.7–5.1%, two readings, 5.4 s
  median, passes, 24 s night 1, DeepSeek 0.1–0.3% (3 games), pacing alternative not chosen:
  frontend/docs/stage_fit/README.md. "Stronger class slower: untested": no record compares classes.

Levers
- One model per job: writeup/_planning/map.md block 96; accessors.py and the catalogue rows (seat
  Haiku low; summary medium; extraction Sonnet; dedup Haiku); summary ≈ 4 calls vs ≈ 150:
  evidence/gameplay/discussion_evidence.md; 90 s budget: content_plan.md §7; seat-id count 74/146 vs
  18/1,405: evidence/extraction/post_game/report.md §4; benchmarks shortlist, never select:
  evidence/evaluation/model_admission/model_selection.md.
- Thinking level: evidence/gameplay/deduction/experiment_log.md §9 (live mode: 97/157 = 62% vs
  122/158 = 77%; ≈ 1,440 vs 2,120 output tokens a vote; decision pending) and §2 (discussion: 49/115
  vs 47/115 bad, 11.2 s vs 6.7 s, enforced mode). The two modes are named on the page.
- Prompt caching: caching/report.md §3.2 (layout), §4.3 (Luna $0.89 → $0.64 per 1,000 calls; Haiku
  $1.10 → $1.10; 65 → 87 turns), §4.4 (18 turns), §4.5 (participation; owner keeps it; "20–25%
  costlier": content_plan.md §7), §2 (per-provider mechanisms), §4.1 (Vertex: no automatic hits in June
  and October; 4,096 minimum), §5 (1.25×). Flash-Lite $0.72: phase3_luna_games/README.md (batch 4,
  2026-10-10, earlier layout).
- Bounding the work: evidence/extraction/day_summary/report.md §8 (kept for bounded prompts and
  code-read fields; can omit or distort: §7 case); $0.011 of $0.215 ≈ 5%; the cap with last replies:
  writeup/game_design_orchestration/conversation/conversation.md; the gate after the line:
  silence_calibration/README.md; Haiku's silence: caching/report.md §4.5.
- Offline and batched: v8/decisions.md §11, §16; pricing.py BATCH_FACTOR; caching/report.md §4.6.
- Local model: evidence/fine_tuning/report.md (classifier 65–69% vs 83–85%, closed; reranker NDCG@5
  0.882 vs 0.871 on 17 turns / 319 pairs, not wired; ONNX 16.6 ms per pair, one thread).

Kept off the page (content_plan.md §7): a stated budget figure (owner 2026-10-30: arbitrary); credits
or plans; "best model"; costs from different runs in one ranked list (served games given as a range);
the Flash-Lite per-token hook; Sonnet "$2.30 vs $0.12"; the undercounted one-hour writes; the
served-game extraction's deployment state.
-->
