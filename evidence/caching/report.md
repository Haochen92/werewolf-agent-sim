# Prompt caching — reducing repeated input costs

The Werewolf simulation sends the same game rules and discussion history to its agents many times.
Post-game analysis repeats another large input: the finished transcript, examined from several roles'
perspectives. This work made those repeated inputs cheaper through a prompt layout every call shares,
provider-specific cache handling, and accounting for cache reads, writes and retries.

The clearest results came from two places. In live games, a layout that opens every call with the same
rules and public transcript cut GPT-6 Luna's cost per call by 28% in paired games, with no detected change
in how often it misstated the game. In repeated analysis, a Gemini extraction check served 5,520 of 5,648
input tokens from cache, and the tell detector (an evaluation tool that identifies player behaviours in a
transcript) adopted caching after a five-game comparison found no loss in precision or recall. A Claude
investigation showed why every saving had to be verified from usage records: different output schemas and
retry paths turned expected cache reads into expensive writes.

This report explains the implementation reviewed on **2026-10-14** and the experiments supporting its
design. The [experiment log](experiment_log.md) preserves the full sequence of proposals, tests and
changes. Cache-read counts describe input reuse, not an equivalent percentage reduction in the total bill.

## 1. Where caching fits

Game turns need timely responses. An agent reads the rules, its role and private information, the
conversation so far, and instructions for its current action. If memory is enabled, a separate call
first turns the game state into a search query for relevant lessons.

Post-game extraction can wait. Since October 12, games save the inputs for that analysis and an offline
job processes them later. The job makes separate calls for each role and game phase; each of these
analysis units is called a **cell**. Those calls share most of their input even though they ask different
questions about the game.

Offline processing, batching and caching solve different problems. Moving work offline removes it from
the player's wait. Batching lets eligible jobs use asynchronous processing at a lower price. Caching
reduces the price of repeated input and can help both live and offline calls.

| Workload | Cache design in this project |
|---|---|
| **Agent turns and memory lookups** | Every call opens with the rules and the public transcript, the part all players and call types share; what differs comes after it (section 3.2). Claude requests mark the end of that shared part; OpenAI's GPT-6 models get explicit cache breakpoints there; DeepSeek reuses it automatically. Gemini gameplay gets no reuse: its automatic caching did not fire in the tested configurations, and the game creates no cache objects for turns. |
| **Post-game extraction** | Gemini uses one explicit cache per game, shared across its analysis calls. The Claude path writes a shared prefix before submitting the remaining calls as a batch. |
| **Other offline analysis** | Claude synthesis and judge calls mark their shared instructions and rules. The Gemini tell detector caches the transcript and checklist shared by calls about different players. |

The Gemini cache-creation helper falls back to sending the full prompt if creation fails. That keeps an
unavailable cache from preventing extraction. Successful API calls are only the first check: usage
records establish whether the provider actually reused the input.

## 2. How the providers cache

A **prefix** is the beginning of a prompt. Caching reuses a matching prefix, so shared content belongs
before content that changes between requests. Three details decide whether a matching prefix is actually
reused, and they differ by provider.

| Provider | What gets stored | What the application does |
|---|---|---|
| **DeepSeek** | Each request's prompt, plus any prefix that two requests have shared | Order prompts so calls share as long a start as possible. |
| **OpenAI** (GPT-5.6 and later) | Only prompts ending at a boundary: the end of the latest user message, or an explicit `prompt_cache_breakpoint` | Mark breakpoints where the shared part ends, and switch off the implicit write so changing content is not stored. |
| **Claude** | Only prefixes ending at a `cache_control` mark the request places | Mark where the shared part ends, and account for the cost of writing as well as reading. |
| **Gemini on Vertex** | Only a named cache object the application creates | Create the object from shared input, reference it from later calls, then delete it. |

These describe the tested integrations and the provider documentation read on 2026-10-13, not a permanent
catalogue of provider features. The dated measurements are in section 4.

**Writing a cache can cost more than sending the input.** Claude and OpenAI charge 1.25 times the input
price for each token written to the cache, and about a tenth for each token read back. A prefix that is
written and never read is therefore more expensive than no caching. Gemini bills a cache object's input
once at the full price. In every case, a cache pays only when the same prefix is read again.

**An enforced output schema behaves like the start of the prompt.** On Claude it is part of what the cache
matches; on OpenAI it is rendered before the messages. Two calls with identical text but different
enforced schemas share nothing. This matters for votes and night actions, whose schemas list each
player's legal targets (section 3.5).

**Concurrent requests need an existing cache to read.** A cache entry becomes readable only once a request
has written it. Gemini creates its cache object before the analysis calls start. The Claude extraction job
completes one direct call per game before submitting the batch, so the shared prefix has already been
written. This improves the opportunity for reuse; the batch measurements still include misses.

Cache entries belong to a particular model. Cross-model cost comparisons therefore use each model's
recorded reads, writes and outputs; equal prompt lengths do not imply equal cache discounts.

## 3. Design decisions

### 3.1 Cache the finished transcript across extraction calls

A finished game's transcript is large, fixed, and needed by every role-specific analysis call. That
made it a better initial target for explicit caching than live discussion, where the conversation
changes after each published message.

The extraction prompt places the transcript and shared instructions first, followed by the role and
phase to analyse. On Gemini, the job creates one cache from that shared beginning, runs the analysis
calls against it, and deletes it afterwards. If creation fails, the calls use the full prompt.

This removes much of the repeated input charge, while each call still pays for its own instructions
and generated output. The October extraction run in section 4.1 illustrates the distinction: output
accounted for most of its bill even with cached input.

The earlier prompt placed the role before the transcript. [Historical extraction-quality evaluations](../extraction/post_game/report.md)
examined the extractor separately, but did not isolate the effect of that reorder. The evidence here
establishes cache reuse, not that the two prompt orders produce equivalent quality. No retrospective
comparison of the two orders is currently planned.

### 3.2 Open every call with what all players share

The agents' prompts used to begin with the rules followed by each player's role card in the system
message, and some player-specific lines before the transcript. Two players' prompts therefore diverged
early, and only the opening rules could be shared. Votes, night actions and memory lookups each
started from their own prompt, so none of them reused the day's transcript.

Every agent turn and memory lookup now follows one layout:

```
system:  the rules, the same for every call of a game
user:    earlier days' summaries and today's transcript, ending on a separator line
         ── the cache boundary ──
         who is dead and which roles remain, the role card, the call's instructions,
         private results, the turn's brief, memory
```

Everything above the boundary is the same for every player and every kind of call at a given moment,
so a vote, a night action or another player's turn can read what an earlier call wrote. The list of the
dead sits below the boundary because it changes at the day's vote; night calls can still share the day's
transcript.

Two changes were needed for the transcript to be identical for everyone. A player used to see its own
**held-back drafts** (lines the game withheld as repeats) marked as unpublished; that private feedback made
each player's transcript different. Drafts are now kept only for the replay, and the strategy note written
with a withheld line is discarded, so the player does not later believe it said something nobody heard.

The cost is that a player's own next turn reuses a little less: its role card and instructions now sit
after the growing transcript and are sent again on every turn. The games in section 4.3 measure the net
effect. The earlier layout was compared once and retired; the git tag `prompt-layout-baseline` keeps it
runnable.

### 3.3 Give Claude a reusable boundary to mark

The Claude integration marks the end of the system message and the end of the transcript, before the
changing part. It splits the transcript into content blocks so a later, longer request can find a
previously cached boundary. In one implementation check, a player's next turn read **9,258 of 10,206
input tokens** from cache.

A mark is not stored anywhere by the application. It is a `cache_control` field on one content block of
one request, and the code that builds each request places it again. For an agent turn, that code marks
the end of the system message, then finds the separator line under the transcript, cuts the text above it
into one block per line, and marks the last of those blocks. Claude allows up to four marks per request;
this design uses two.

For each mark, Claude looks for a cache entry that ends exactly there. If none exists, it walks back
block by block, at most 20 blocks, for an entry that ends at an earlier block boundary. It reads what it
finds, processes the remaining blocks normally, and stores a new entry ending at the mark. Two turns:

```
Turn 1:  [system ✓] [line 1] [line 2] [line 3 ✓] [role, brief …]
         no entry yet → store "system … line 3"            (written at 1.25× input)

Turn 2:  [system ✓] [line 1] [line 2] [line 3] [line 4] [line 5 ✓] [role, brief …]
         no entry at line 5; walk back: line 4 no, line 3 yes
         → read "system … line 3" (about 0.1× input), process lines 4–5,
           store "system … line 5"                         (only lines 4–5 written)
```

The transcript is cut into one block per line because the walk-back can stop only at a block boundary.
As one block, a longer transcript would contain no boundary where the earlier entry ended. Since the
system message holds only the rules, turn 2 can be any player's turn, or a vote, and still read the entry.
A long gap between two calls can put the old boundary outside the 20-block window, so the design does not
guarantee a hit on every call.

### 3.4 Give OpenAI explicit breakpoints

OpenAI's GPT-6 Luna stores a cache entry only at the end of the latest user message, unless the request
places explicit breakpoints. Each turn's user message ends with its changing brief, so before this change
only the fixed instructions were ever reused: seven discussion calls under one system message each read
exactly 4,582 cached tokens while the transcript grew. Votes, night actions and lookups read nothing,
and three quarters of Luna's input was written to the cache at the 1.25 times rate without being read.

Luna's requests now use explicit-only caching, with a breakpoint on the system message and on each line
of the shared record. The installed SDK supports this on the Chat Completions API the project uses. OpenAI
considers up to the latest 80 breakpoints and writes the latest four, so a later call finds an earlier
call's last line among its own. A three-call probe confirmed the behaviour: a player's next turn read
2,561 of 2,678 tokens from cache, another player's turn 2,648 of 2,674, and the private part was never
written.

### 3.5 Keep legal targets in the schema, and decide whether to enforce it

A vote or night action's schema lists the players it may target, which differ for each player and after
every death. The targets are enforced by code through that schema, never written into the prompt as a list
(owner's rule). With the schema enforced by the provider, each player's vote has its own schema and so its
own cache (section 2): votes and night actions cannot share across players.

The alternative is to write the schema as text after the shared part and validate the reply in code
against the same per-player schema, so an illegal target still fails. In trials on 17 schemas and 24 real
game turns per model, these unenforced replies failed validation once in about 400 calls on each of Luna
and Haiku 5.5, and each failure costs one retry. Their fields came in a different order on Haiku until the
schemas were changed to put the player's reads first, matching the prompt's opening line; after that, all
24 real turns kept the schema's order.

Both modes remain available per model. In production, Luna and Haiku currently use the enforced schema,
which keeps the layout's sharing for discussion turns but not for votes and night actions. The paired
games in section 4.3 measured the unenforced mode, which is where Luna's saving came from.

### 3.6 Combine offline batching with shared input

The Claude extraction path uses Message Batches and a one-hour cache. One direct analysis call per game
writes the shared prefix, and its result is retained. The remaining calls are submitted as a batch.

Each analysis requires a different output structure, or **schema**. In the tested Claude path, enforcing
a different schema on every call prevented those calls from sharing a cache. The implementation instead
puts each schema into the prompt after the shared prefix and validates the returned JSON in code.

That choice makes retries part of the cost design. Failed replies go into a second batch using the same
layout. Only failures that remain are retried directly with the schema enforced and no cache mark.
Section 4.6 explains what the schema probe and larger run established, and the verification still
needed for the retry change.

The Gemini path processes the same saved inputs through individual API calls using an explicit cache.
It remains an offline job even though it does not use the provider's batch API.

## 4. Evidence

### 4.1 Gemini on Vertex: verify reuse before relying on it

The June probes redirected the work toward explicit extraction caches. On `gemini-3.1-flash-lite`,
automatic caching returned zero reads for repeated 15k-token prompts, including a warmed attempt with
a 20-second wait. Production records were consistent with it being an unreliable cost lever: only
2 of 600 recent calls recorded hits, covering 0.4% of input tokens.

| June 2026 probe | Observation |
|---|---|
| Automatic caching on `gemini-2.5-flash` | About 2 of 11 calls read roughly 4k tokens from an 8.7k-token repeated prompt. Smaller tested prompts produced no reads. |
| Explicit caching on the tested Vertex configuration | A request read 15,001 of its 15,005 input tokens from the cache object. |
| Explicit-cache minimum on that configuration | The API enforced a minimum of 4,096 tokens. |

The extraction implementation then read **5,520 of 5,648 input tokens** from cache in a June 10 check.
Reuse worked in both tested regions, `global` and `us-central1`. The October admission probe also found
no automatic cache reads on `gemini-3.5-flash-lite` for the tested sizes up to approximately 8,192 tokens.
These findings describe the tested models and backend, not every Gemini model.

A larger offline extraction run on October 12 processed **19 games in 570 calls** using
`gemini-3.8-flash`. Its recorded bill was **$10.33**: $0.93 for uncached input, $0.43 for cached input,
and $8.97 for output, mostly reasoning. Those are components of one run's bill, not a cached-versus-uncached
comparison. They show why a high input cache share does not imply an equally large reduction in total cost.

### 4.2 Test providers on actual game prompts

Before a model joins the game menu, the admission check tests its caching behaviour. It sends repeated
prompts at several sizes, then three prompts from one recorded discussion state: the first player's
turn, that player's next turn after another message, and a different player's turn.

The results below are the fraction of each request's input served from cache, from one probe sequence
per row. The first rows are the October admission probes in the earlier layout; the last two are the
same probe in the current layout, with the enforced schema.

| Model | Same player, next turn | Different player |
|---|---:|---:|
| Claude Haiku 5.5 | 90% | 0% |
| Qwen 3.8 Flash via OpenRouter | 79% | 36% |
| GPT-6 Luna via OpenAI | 57% | 29% |
| GLM 5.3 Flash via OpenRouter | 10% | 13% |
| DeepSeek v4-pro | 8% | 11% |
| MiniMax M3 via OpenRouter | 3% | 3% |
| Gemini 3.5 Flash-Lite | 0% | 0% |
| **Claude Haiku 5.5, current layout** | 77% | **71%** |
| **GPT-6 Luna, current layout** | 75% | **69%** |

The current layout lets a different player reuse most of the prompt. Haiku's own next turn reuses less
than before (77% against 90%), because its role card now follows the transcript (section 3.2). These
records count cached tokens; they do not identify exactly which text was reused.

A short probe establishes that reuse occurs; it does not establish a typical whole-game discount.
DeepSeek illustrates this: its two July games had much higher cached fractions than its three-request
probe. Different workload sizes and cache warmup may help explain the difference.

### 4.3 The layout in paired games

Two games per arm on the same two seeds and line-ups, memory on, every call on the player model. The
earlier layout used the enforced schema; the current layout was measured with the unenforced schema, and
for Haiku also with the enforced one. Costs are per call, because the games' lengths differed.

| | Cost per 1,000 calls | Votes: read / written | Night: read / written | Discussion turns per game |
|---|---:|---|---|---:|
| Luna, earlier layout | $0.89 | 0% / 100% | 0% / 100% | 70 |
| **Luna, current layout** | **$0.64** | 64% / 0% | 60% / 0% | 72 |
| Haiku, earlier layout | $1.10 | 0% / 87% | 0% / 99% | 65 |
| Haiku, current layout, unenforced | $1.10 | 63% / 1% | 56% / 0% | 87 |
| Haiku, current layout, enforced | $1.07 | 0% / 78% | about 18% / 55% | 89 |

On Luna the layout cut the cost per call by 28%: input cost per call fell by about a third, and votes and
night actions went from never reading the cache to reading about 60% of their input. On Haiku the cost per
call did not change. With the unenforced schema, Haiku reasoned more on its turns (about 1.5 times on
discussion and several times on votes), which used up the input saving; with the enforced schema, its
reasoning stayed near the earlier level but votes and night actions could not share the cache.

These are two games per arm. They show the direction clearly on Luna; they cannot size Haiku's small
differences.

### 4.4 Message quality under the current layout

The hallucination bench replays 18 recorded discussion turns, each with a written expectation of what a
correct reply must or must not say, and a judge marks replies that misstate the game. Luna, 5 samples per
turn, judged by Claude Haiku 5.5:

| Configuration | Replies marked bad | Per turn against the earlier layout (better / worse) |
|---|---:|---|
| Earlier layout, enforced schema | 11 of 90 (12%) | — |
| Current layout, enforced schema | 13 of 90 (14%) | 4 / 5 |
| Current layout, unenforced schema | 10 of 90 (11%) | 4 / 2 |

No configuration differed beyond noise. With 18 turns, only a large regression, about ten points, would
have shown. The bench covers discussion turns only; it has no vote or night cases for the ten-seat game.

### 4.5 An unexpected effect: Haiku stopped staying silent

Haiku's games under the current layout had about 35% more discussion. Its messages were no longer: the
difference was how often a player spoke on turns where it was allowed to pass.

| Spoke rather than passed, day 2 onwards | Opening statements | Free turns |
|---|---:|---:|
| Haiku, earlier layout (6 games) | 7–8% | 20–35% |
| Haiku, current layout (4 games) | 23–26% | 53–54% |
| Luna, earlier layout (5 games) | 28–43% | 58–72% |

In the earlier layout, Haiku passed almost every opening and most free turns; one game's second day had no
discussion at all. In the current layout it took part at roughly Luna's level. In one paired day, the
Sentinel passed its opening in the earlier layout, noting "Do not claim early", and every other player
passed too. In the current layout the same Sentinel opened with its night result and the day developed
from the questions that followed.

One plausible reading is the position of the role card's cautions, such as "revealing your role could mark
you as a night target". The earlier layout put them in the system message, which Haiku appears to weigh
heavily; the current layout puts them after the transcript, next to the opening rules and the player's own
night results. The wording is identical; only the position moved. The owner judged the earlier Haiku too
quiet and keeps the extra participation as a benefit. Its games cost more because they contain more
discussion; whether it plays better was not measured.

### 4.6 Claude extraction: make cache writes and retries visible

The Claude investigation changed both the request layout and the cost accounting. A small probe
confirmed that moving the schema after the shared text restored cache reuse. A larger run then exposed
expensive retries, leading to a revised retry path and validation-error logging.

**The symptom.** An initial two-game check, run on both Haiku 5.5 and Sonnet 5.5, was estimated at under
$0.50 and cost approximately **$2.69** combined. The Sonnet usage record showed zero cache reads and
nearly a million tokens written to caches. Its cost summary also undercounted the bill by pricing
one-hour cache writes as ordinary input; the accounting was corrected to include the write premium.

**The diagnosis and first fix.** Each game generated about 30 analysis calls with different output
schemas. A controlled probe found that the same prefix with another enforced schema created a new cache,
while the same schema allowed a read. Putting the schema into the prompt after the shared prefix removed
that source of mismatch. A three-call check on Haiku then wrote the 12.7k-token prefix once and read it
twice. All three replies passed application-side validation, for $0.006.

**The larger run.** A subsequent Sonnet run processed **21 games in 630 calls**, costing **$19.99** against
an estimate of about $9.50. The recorded breakdown explained the difference:

| Source | Recorded cost | What happened |
|---|---:|---|
| Output | $7.39 | Close to the expected output cost. |
| Cache writes on direct retries | $7.02 | About 91 replies failed validation. Retrying with each call's enforced schema wrote prefixes that other calls could not reuse. |
| Cache writes within the batch | $3.01 | About 92 requests wrote the prefix again instead of reading the warmed cache. |

The remaining cost was input and cache reads. The initial validation errors were not logged, so that
run does not establish why the replies failed. Errors are logged now. The new retry sequence in section
3.6 addresses the repeated writes, but its savings have not yet been measured in a comparable full run.

This is why cost checks include the retry path as well as the successful path. The 15% batch-write rate
also shows why estimates must allow for cache misses instead of assuming every warmed request gets the
discount.

### 4.7 Tell detection: choose the saving that preserves measured quality

The tell detector examines a transcript for a checklist of player behaviours. Calls about different
players share the same rules, transcript and checklist, so one cache can serve about nine calls per game
and channel. A real-game probe read **5,374 of 5,716 input tokens from cache (94%)**.

The adoption decision also checked detection quality. Repeated cached calls produced more variation in
the detected rows, even at temperature zero. Further tests showed that the uncached configuration could
vary too. Exact repetition was therefore a separate question from whether the detections were correct.

A comparison on **five games and 40 labelled cases**, using the detector's combined results from two
passes, found comparable quality:

| Metric | Uncached | Cached |
|---|---:|---:|
| Vote detection precision | 0.77 | 0.83 |
| Vote detection recall | 77% | 77% |
| Discussion detection precision | 0.93 | 0.93 |
| Discussion detection recall | 87% | 87% |

Caching became the default because it reduced input charges without a quality loss observed on that
sample. The slight precision increase is not evidence of a general accuracy improvement. Outputs are
stored so a scored run can be inspected exactly; rerunning the model produces another sample.

Reducing the reasoning budget was a different cost lever, with a different result. In a one-game probe
with six labelled cases, the minimal-thinking variants found zero correct labelled days versus two with
the low-thinking configuration. That small probe was enough to reject the change for adoption, though
not to estimate its general effect. The selected configuration kept low thinking and enabled caching.

The [investigation log](experiment_log.md#6-2026-07-13--a-second-consumer-the-tell-detector) records the
repeatability tests and the decisions as they changed. The [tell-detector report](../extraction/tell_extraction/report.md)
contains the broader evaluation context.

## 5. Cost accounting that supports the decisions

The implementation records cache reads and writes separately and prices each write at its premium:
1.25 times the input price on Claude and on OpenAI's GPT-6 models, twice for Claude's one-hour cache.
The game's own cost meter, the trace pricing and the bench's cost estimates all use the same rule. Before
this, the traces counted OpenAI's writes as free and recorded Claude's reads and writes under names that
were not priced, so some earlier game costs were understated; the experiment log records the corrections.
Direct and batch Claude calls are traced alongside the game calls, so offline work can be included when
assessing the pipeline's cost.

These changes make it possible to distinguish three expenses that an input-token estimate misses:
repeated cache creation, retries, and reasoning output. Each mattered in the recorded investigations.
Quality comparisons support the specific changes evaluated: the detector's adoption of caching and the
current prompt layout on Luna. The [experiment log](experiment_log.md) also records prompt reorders and
cache designs that were considered but not implemented.

## 6. Open questions

- **The schema mode in production.** Luna's 28% saving was measured with the unenforced schema, but
  production runs Luna enforced, so its votes and night actions do not yet share the cache.
- **Models never measured under the current layout.** DeepSeek, GLM and the Gemini players, including the
  site's default, use the layout too. On cost they can only gain or stay level; their play was not tested.
- **Play quality beyond factual errors.** The bench checks misstatements on discussion turns. Whether
  Haiku's extra participation, or the layout in general, changes how well players play was not measured.
- **The bench's missing cases.** It has no ten-seat vote or night turns.
- **The extraction reorder.** Whether putting the transcript before the role changed extraction quality
  was never tested (section 3.1).

## Evidence and implementation links

- **Gemini probes:** [`scripts/`](scripts/), frozen records of the June 6–8 investigation. Extraction
  reuse was checked June 10. These are historical probes, not current provider specifications.
- **Model admission and the current-layout probe:** [probe implementation](../../evaluation/src/model_admission/probes.py)
  and [recorded results](../../evaluation/eval_results/model_admission/), October 4, 11 and 13.
- **Paired games and their cache shares:** `batch_results/cache_ab_2026_10_13/`, read with
  [`game_cache_share.py`](../../evaluation/experiments/game_cache_share.py), which splits each game's reads,
  writes and cost by call type.
- **Bench run:** `evaluation/eval_results/hallucination_bench/shared_prefix_luna_2026_10_13/`.
- **Claude extraction:** October 12 runs under `batch_results/extraction_runs/`, including
  `check_sonnet_2026-10-12/summary.json`. The [log](experiment_log.md) connects the runs to the fixes.
- **DeepSeek games:** [model-selection report](../model_selection/report.md), July 26 comparison.
- **Quality investigations:** [tell-detector report](../extraction/tell_extraction/report.md) and
  [historical extraction report](../extraction/post_game/report.md). The extraction report describes
  an earlier pipeline version.
- **Implementation:** [prompt layout](../../Agents/prompts/layout.py),
  [Gemini cache helper](../../Agents/llm_factory/providers/google.py),
  [Claude provider integration](../../Agents/llm_factory/providers/anthropic.py),
  [OpenAI breakpoints](../../Agents/llm_factory/providers/openai_compat.py),
  [offline extraction](../../Agents/memory/extraction/offline.py),
  [transcript formatting](../../Agents/prompts/prompt_formatters.py),
  [pricing](../../Agents/llm_factory/pricing.py) and
  [trace pricing](../../Agents/observability/langfuse_prices.py).
- **Key revisions:** `9d65336` (Gemini extraction cache), `5685bf29` (Claude marks), `1ad07a81`
  (memory-lookup layout), `8c961496` (schema after shared prefix), `c3815883` (retry path), `968bdad6`
  (write pricing), `d80ee2d2` (reads-first schemas), `0d936b08` / `d41b1c0c` (current layout, the earlier
  one retired; tag `prompt-layout-baseline`).
