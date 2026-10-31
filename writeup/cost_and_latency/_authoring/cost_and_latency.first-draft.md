# Cost and latency chapter (sample draft)

*Level 1 page, sample draft of 2026-10-30, written as a self-sufficient chapter page with no Level 2
pages, to judge whether its sections fit one page. Not reviewed; nothing approved. The chapter's plan is
[`content_plan.md`](content_plan.md); the authoring brief is
[`_authoring/cost_and_latency.brief.md`](_authoring/cost_and_latency.brief.md). Lines marked **Exhibit**,
**Link** and **Depth** are specs for the page, not page copy.*

---

## Page copy (draft)

### Cost and latency: serving a game within a budget and a wait

Every turn of this game is a model call. A ten-player game has ten seats, and each time a seat speaks,
votes or acts at night it is sent the rules, its role, the day's transcript so far and a summary of the
earlier days: about 10,000 input tokens a turn. A game runs four to six days, and the sixteen games I
priced most recently made between about 100 and 250 calls each. The model's reasoning is billed as
output, at five times the input rate. And because the discussion runs one speaker at a time, a person
at the table waits on every AI turn before their own.

Serving a game therefore means managing two things: what the calls cost, and how long a person waits
for them. My bar for cost is my own, not a market figure: a ten-player game should cost under $0.30 in
model calls. It falls as people fill seats, since a human's turn is a call not made. The bar for waiting
is set by reading speed: a call is fast enough when it finishes before the person has read what came
before it.

This page gives the measured cost, then the measured wait, then the levers I used on each and what
every lever gave up. Each saving was checked in real games, and several came out smaller than the
input-token arithmetic promised.

#### What a game costs

Sixteen AI-only games on Claude Haiku 5.5, the site's default seat model, with memory off (also the
default) cost $2.48 in model calls: $0.08 to $0.26 a game, $0.16 on average. The spread is game length.
A four-day game made about 105 calls; a six-day game made up to 254. These are model-call costs only;
hosting is not counted.

Where the money goes is the useful part, because every call's tokens are recorded and priced from a
dated price table. In those games about half of all input tokens were read from the provider's cache,
at a tenth of the input price, so input was already cheap. Output was about half the bill, and about
half of the output tokens were reasoning. The model's price and how much it writes decide most of the
cost; the length of the game decides the rest.

With memory on, each seat also looks up lessons from earlier games before it decides. In one measured
memory-on game ($0.215, 197 calls) the bill split by call type as discussion $0.110, memory lookups
$0.034, night actions $0.028, votes $0.025, the day summary $0.011 and the two short filter calls $0.004.

**Exhibit.** That split as one horizontal bar, captioned "one game, memory on, Haiku 5.5, 2026-10-13".

**What the same game would cost on other models.** I have only played seats on the smallest model
class. To see what the budget rules out, I repriced the recorded tokens of two games at other models'
list rates, as if each model had written exactly what Haiku wrote.

| Model | Memory off (average of the 16 games) | Memory on (the game above) |
|---|---:|---:|
| Claude Haiku 5.5 (measured) | $0.16 | $0.21 |
| GPT-6 Luna | $0.16 | $0.21 |
| DeepSeek V4.1 Flash | $0.20 | $0.27 |
| Gemini 3.5 Flash-Lite | $0.63 | $0.87 |
| Gemini 3.6 Flash | $2.33 | $3.20 |
| Claude Sonnet 5.5 | $3.03 | $4.18 |
| Claude Opus 5.5 | $6.05 | $8.35 |

The estimate is rough in one direction: a stronger model would not write the same tokens. Opus cannot
turn its reasoning off, where these seats ran at low thinking, and each model tokenises differently. It
says nothing about play quality; no Sonnet or Opus game has been played in the seats. What it does show
is that the budget sets the model class. Everything above the smallest class costs ten to thirty times
my bar before any of it is tested for play. The choice within the class is then made on quality and on
waiting.

#### How long a person waits

A model call that takes six seconds does not make a person wait six seconds. The browser plays the game
as a stage: each spoken line is shown at reading pace, five to fifteen seconds, a pass for four seconds,
a verdict for six. The server does not wait for the stage. It works out the next action while the stage
is still showing the last one, so the person waits only when the next event has not arrived by the time
the stage reaches it.

I measured that from the traces of seven games I played on the site while building, replaying each
game's events through the stage's own timing code against the moment each event left the server. On
Haiku the stage would have stood waiting for the model for roughly 3 to 5% of its playing time. The two
ends of that range are two assumptions about what the stage's backlog does across a page reload, not
two groups of games.

Where it waits is specific. A pass is shown for four seconds, but the next seat's call takes 5.4
seconds at the median whether it speaks or passes, so a run of passes is a run of short waits. The
morning after a night waits on the wolves, whose chat lines, kill and skills run one after another for
about 24 seconds on the first night, longer than the night display. A spoken line, shown for five to
fifteen seconds, covers most turns. DeepSeek V4.1 Flash, about twice as fast, kept ahead almost always
(three games, under 0.3% waiting).

Two trade-offs sit here. Holding a pass longer would hide the pause but make every game longer; that is
a pacing choice I have not made. And whether a stronger model class is slower is untested here; the
latency I have measured varies with the thinking level, below.

#### The levers, and what each gave up

**One model per job.** Rather than one model for everything, each job gets the model its own
constraint allows. A seat's turn is bound by the wait and the per-game cost, so it runs on the smallest
class at low thinking. The day summary, one call a day, is what every seat reads about the past, so one
error there reaches all ten; it runs at medium thinking with a 90-second budget, about four calls a
game against about 150 seat calls. Post-game extraction, which writes the lessons memory keeps, is
bound by quality: on Haiku 51% of its observations named a seat by its id, which no later game can
match, against 1.3% on Sonnet, so extraction runs on Sonnet and recovers the cost offline. Bulk jobs,
such as duplicate checks, run on cost. Public benchmarks shortlist a candidate; they never pick one.
Whether a candidate can serve at all, its output format, its caching and its speed, is an admission
run.

**Link:** How a model is admitted to the menu → Evaluation, model admission.

**Thinking level.** More reasoning is more output tokens and more time, so it has to pay for itself per
job. On sixteen frozen vote situations replayed ten times each, Haiku at medium thinking chose a vote
that fitted the evidence in 61% of samples against 41% at low, and was better in twelve situations of
the sixteen. On twenty-three frozen discussion turns it made no difference, and a turn took 11.2
seconds instead of 6.7. The votes wrote about 2.7 times the output. Seats run at low today; moving
votes alone to medium is an open decision, and it would raise the per-game cost by roughly the vote
share of the bill.

**Prompt caching.** A provider's prompt cache charges a tenth of the input rate for a prompt start it
has already processed, so I laid every call out as the part all seats share first, the rules and then
the public transcript, with each seat's own material after it. Later calls read what earlier calls
wrote, including votes and night actions, which had never read the cache before. Whether that lowers
the bill depends on the model. In paired games with the same deals, the layout cut GPT-6 Luna's cost per
call by 28%. On Haiku the cost per call did not move, because Haiku reasoned more under the new layout
and spent the saving; and its games cost 20 to 25% more, because its players stopped passing nearly
every turn (65 to 87 discussion turns a game). I kept the extra participation. Whether it plays better
is not measured; a factual-error check on eighteen turns showed no change beyond noise.

Caching is also a per-provider contract, not a flag. It is a marked boundary on Claude, breakpoints on
OpenAI and automatic on DeepSeek. On Vertex the implicit cache returned no hits in two probes four
months apart, and the explicit cache has a 4,096-token minimum, which is one reason a Flash-Lite game
cost $0.72 under the earlier layout. A cache write also costs 1.25 times plain input, so a prompt start
that is written once and never read costs more than not caching at all.

**Exhibit.** A shared-start / private-tail diagram: the rules and the public transcript every seat
shares, then one seat's role, notes and instructions.

**Depth:** The prompt layout for each provider's cache → Level 3. Why Haiku stopped staying silent →
Level 3.

**Live or offline.** Nobody waits for extraction, so it never runs during a game. Finished games are
collected and sent as one batch, which the provider prices at half rate. The discount is on eligible
requests, not on the job. A 21-game run on Sonnet cost $19.99 against about $9.50 estimated: replies
that failed validation were retried in a way that wrote new caches ($7.02), and 15% of the batched
requests wrote the shared start instead of reading it ($3.01). Retries now keep the shared layout; the
saving is not yet measured in a comparable run.

**Depth:** The extraction run that cost twice its estimate → Level 3.

**Bounding the context.** Without a bound, each day's input grows with every line said. Two mechanisms
hold it. The day summary replaces the earlier days' transcripts with one structured account, so a seat
on day four reads one summary per past day, not three days of lines. It exists for fidelity and for
code to read as much as for cost, and it is itself one medium-thinking call a day, about 5% of the
memory-on game's bill. And a player may pass: a seat with nothing new says so at no cost, and a gate
holds a line that repeats one already said. The trade-off is a quiet table. Under the earlier prompt
layout Haiku passed almost every opening and most free turns, and one game's second day had no
discussion at all. Where repetition is sorted, by the player's own pass or by the gate, was settled in a
one-day calibration study.

**Link:** The day's design, passes and the gate → chapter 1. The day summary and the claim ledger →
chapter 3.

**Replacing a call with a local model.** The cheapest call is none. I trained small local models for
two memory jobs the API handles. A 4-billion-parameter classifier for the keep-or-discard duplicate
decision reached 65 to 69% on 65 labelled cases against 83 to 85% for the API models, and was closed. A
22-million-parameter cross-encoder for reranking retrieved lessons matched the API reranker on
seventeen turns (NDCG@5 0.882 against 0.871) at 16.6 milliseconds a pair on one CPU core. It is trained
and benchmarked, not wired in; none of these runs in production.

**Link:** What memory stores and how it is kept clean → chapter 4.

<!--
Sources (page copy → record). Re-derived figures are marked [re-derived]; see the brief.

Intro
- 10,000 input tokens a turn: Agents/llm_factory/pricing.py (comment on the Haiku row).
- 100–250 calls, 4–6 days: the 16 persona_voice_games manifests (104–254 calls, days 4–6) [re-derived].
- output at five times the input rate: pricing.py Haiku row ($0.10 / $0.50).
- $0.30 bar: the owner, 2026-10-30; own bar, not market-derived.

What a game costs
- $2.48, $0.08–0.26, memory off, low thinking, voices on in 8 / off in 8, 2026-10-18:
  evidence/gameplay/data/persona_voice_games/README.md. Mean $0.16, 53% of input cached, output ≈ half
  the bill, reasoning ≈ half of output: the manifests' usage buckets [re-derived].
- Memory-on game $0.215, 197 calls, call-type split: content_plan.md §2 (game_cache_share.py on
  batch_results/cache_ab_2026_10_13/haiku_after.jsonl) [re-derived in the plan].
- Repricing table: pricing.py list rates; Opus 5.5 at $4 / $20 / $0.20 per million, NOT in the
  catalogue, source needed before publishing. Method and caveats: content_plan.md §7 "Opus 5.5".
- "no Sonnet or Opus game in the seats": content_plan.md §7.

How long a person waits
- Stage holds, server runs ahead, 2.7–5.1%, two readings (restart / continuous), 5.4 s median,
  passes 270 s over 21 waits, morning shutter 24 s night 1, DeepSeek 0.1–0.3% on 3 games, pacing
  alternative not chosen: frontend/docs/stage_fit/README.md.
- "stronger class slower: untested": no record compares classes; thinking-level times are the
  deduction log §2.

Levers
- One model per job: writeup/_planning/map.md block 96; Agents/llm_factory/accessors.py (seat Haiku low
  via catalogue row; summary medium; extraction Sonnet; dedup Haiku); summary ≈ 4 calls vs ≈ 150:
  evidence/gameplay/discussion_evidence.md; 90 s budget: content_plan.md §7; seat-id count 74/146 vs
  18/1,405: evidence/extraction/post_game/report.md §4; "benchmarks shortlist, never select":
  evidence/evaluation/model_admission/model_selection.md.
- Thinking level: evidence/gameplay/deduction/experiment_log.md §2 (65/160 vs 98/160; 12 of 16;
  49/115 vs 47/115; 11.2 s vs 6.7 s; output tokens per vote 852 vs 2,317; decision pending). The
  2026-10-30 note's live-mode rerun (62% / 77%) is not on the page; see the brief's open question 4.
- Prompt caching: evidence/caching/report.md §3.2 (layout), §4.3 (Luna $0.89 → $0.64 per 1,000 calls;
  Haiku $1.10 → $1.10; 65 → 87 turns), §4.4 (18 turns, no change beyond noise), §4.5 (participation;
  owner keeps it; "20–25% costlier": content_plan.md §7), §2 (per-provider mechanisms), §4.1 (Vertex: no
  automatic hits June and October; 4,096 minimum), §5 (write premium 1.25×). Flash-Lite $0.72:
  evidence/gameplay/data/phase3_luna_games/README.md (batch 4, 2026-10-10, earlier layout).
- Live or offline: evidence/memory_system/v8/decisions.md §11, §16; pricing.py BATCH_FACTOR;
  evidence/caching/report.md §4.6 ($19.99 vs ≈ $9.50; $7.02; $3.01; 15%; retry fix unmeasured).
- Bounding the context: evidence/extraction/day_summary/report.md §8 (kept for bounded prompts and
  code-read fields); $0.011 of $0.215 ≈ 5%: the call-type split above; pass "costs nothing" and the echo
  gate: evidence/gameplay/data/silence_calibration/README.md (terms; the one-day study); Haiku's silence
  under the earlier layout: evidence/caching/report.md §4.5.
- Local models: evidence/fine_tuning/report.md (classifier 65–69% vs 83–85%, closed; reranker NDCG@5
  0.882 vs 0.871 on 17 turns / 319 pairs, trained, benchmarked, not wired; ONNX 16.6 ms per pair, one
  thread).

Kept off the page (content_plan.md §7): credits or plans; "best model"; costs from different runs in
one ranked list; the Flash-Lite per-token hook; Sonnet "$2.30 vs $0.12"; the undercounted one-hour
writes; the served-game extraction's deployment state.
-->
