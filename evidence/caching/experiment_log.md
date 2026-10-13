# Prompt caching — investigation log

> **What this is.** How the project's use of prompt caching developed, from June to October 2026: what
> we hoped to cache, what the measurements said, and how each finding changed the next step. Sections are
> in time order. A design that was later disproved is shown as it was proposed, with its disproof after it.
>
> **Companion.** How caching works today, with the full evidence and open limitations, is
> [report.md](report.md). The report also explains the project's vocabulary (seat, turn, brief, memory
> lookup, extraction cell); this log reintroduces a term only where it first matters.

---

## 1. Motivation (June 2026): cost was building up

In June every seat ran on Gemini (`gemini-3.1-flash-lite` on Google's Vertex AI), and a game cost about
$0.30–0.40. A large win-rate comparison was planned, many games long, so the per-game bill mattered.

Two places sent a large prompt start again and again, which is what a prompt cache rewards:

1. **Seat turns, especially day discussion.** The public transcript only grows. On every turn everything
   before the newest message is fixed, which is the textbook shape for a cached prefix.
2. **Post-game extraction.** After a game, an LLM reads the transcript and writes lessons for the memory
   store. We wanted one call per role instead of one combined call, to get lessons written from each
   role's perspective. The worry was cost: per-role extraction meant six calls on the expensive
   `gemini-2.5-pro` model, each carrying the whole transcript.

One idea covered both. Gemini documents **implicit caching**: the provider reuses a recently seen prompt
start automatically, with no work in the harness. If each prompt kept its changing content at the end,
the fixed start would be reused for free. That matched the documentation and the shape of our prompts,
so it was a reasonable bet.

---

## 2. Two hypotheses

**Hypothesis A — seat turns get cheaper through implicit caching and a reordered prompt.** Reorder every
turn's prompt so the content shared by all seats comes first and each seat's own content comes last:
*preamble → rules → earlier days' transcript → today's transcript*, then *role card → private
information → memory → brief → task*. The first part is the same for every seat and grows only at its
end during a day, so implicit caching would reuse it from turn to turn. We called this order **layout (c)**.

Two alternatives were weighed and rejected:
- *Move the role card to the end of the system message* (layout (b)). This caps the shared start at the
  ~1.2k-token system message, which precedes the transcript, so the transcript is never shared. If
  seat caching was going to happen, it had to be (c).
- *Explicitly cache each exact transcript state.* In turn-by-turn discussion each state is read by
  exactly one next speaker, so each cache would be used once (§4 shows why that loses money).

**Hypothesis B — per-role extraction stays affordable through a cached transcript.** Split extraction
into one call per role, and cache the shared transcript so each extra role pays only for its own short
instructions. If that held, richer extraction would no longer cost six times as much input.

---

## 3. The load-bearing assumption first: does implicit caching fire?

Hypothesis A rested entirely on implicit caching working on our model, so that was tested before
building anything.

**Probe on the game model** ([`probe_implicit_cache.py`](scripts/probe_implicit_cache.py)). *Tests:*
whether implicit caching fires at all on `gemini-3.1-flash-lite` on Vertex. A 15k-token identical prompt
was sent four times in a row, then again after a 20-second wait. **Every call read 0 cached tokens.** The
usage field was present and wired correctly; it simply read zero. Production data agreed: 2 of 600 recent
calls had any cache hit, 0.4% of input tokens.

**Hypothesis A was disproved on this model and backend.** Layout (c) would cache nothing if implicit
caching never fires. This was the central bet, and it failed at the first measurement.

**Probe on 2.5-flash** ([`probe_implicit_25flash.py`](scripts/probe_implicit_25flash.py)). *Tests:*
whether the failure was specific to flash-lite, so that a friendlier model would rescue the design.
An ~8.7k-token prefix read 4,085 cached tokens on about 2 of 11 calls and nothing on the rest; prompts of
1.7k, 2.7k and 5k tokens read nothing. The documented 2,048-token minimum was necessary but not
sufficient, and caching seemed to happen in blocks of about 4k tokens. Real discussion prompts were
4.2–5.3k tokens in total, so they would rarely qualify before late in a day. Switching the game model
for caching was also unattractive: 2.5-flash cost more per token (especially output, which caching does
not discount) and would change game outputs. Not a lever.

---

## 4. Pivot: can an explicit cache rescue either target?

Gemini also offers an **explicit cache object**: the harness creates a named cache from some text, and
later requests reference it. Two probes:

- **Does it work?** ([`probe_explicit_cache.py`](scripts/probe_explicit_cache.py)) Yes. A 15,001-token
  cache object served 15,001 of a 15,005-token prompt.
- **What is the minimum?** ([`probe_explicit_min.py`](scripts/probe_explicit_min.py)) 4,096 tokens,
  enforced by the API: *"The minimum token count to start caching is 4096."*

A cache object is not free. Creating it costs the full input price and each read about a tenth, so it
pays only if read at least twice: for a block of size `B` read `N` times, `B + 0.1·N·B < N·B` from
`N = 2`. That test decided both targets.

**Seat turns: deferred.** Caching each exact transcript state means one read per cache: 100% to create
plus 10% to read is 110%, worse than not caching. The real obstacle is the reuse count, not the fact
that the transcript changes. A checkpoint scheme would pass the test: cache the transcript once it
crosses 4,096 tokens and let every later turn that day read it. But it needs a per-day cache lifecycle
in the harness and pays nothing on the short early-day prompts. It was worth building only if the
planned comparison ran very many games, so it was deferred.

**Extraction: shipped.** The transcript is over 10k tokens, the same for every role, and read by every
role's call on an expensive model. One cache per game, created at full price, then read at a tenth by
each role: each extra role costs only its short instructions plus its output. This reversed Hypothesis
B's cost problem.

*Problem → fix.* The extraction prompt opened with *"You are a {role} analyst…"* and placed the
transcript below, so no two roles' prompts shared a start. The fix put the transcript first and the role
last, so the cached block is the same for every role; the cache is created once per game and deleted
after the calls.

*Caveat carried forward.* Putting the transcript first is a prompt change that can affect output. It
shipped because caching required it, not because its effect on quality was shown to be neutral. At the
time, extraction prompts were frozen to protect hand labels that depended on them, so the A/B was
deferred; it has never been run.

*An idea it opened.* Once a transcript is cached, sending the full transcript costs about the same as
sending a summary, so the cost reason for daily summaries disappears. An A/B of full transcript against
summaries was noted but not run: the summaries also feed a judge signal and extraction, which would have
to change with them.

---

## 5. The build (2026-06-10): concurrency, region and cost

Building per-role extraction with a cache object surfaced four facts the probes had not.

- **An explicit cache suits a fan-out better than an implicit one.** The six role calls run at the
  same time. Under implicit caching all six would be in flight before any had stored the prefix, so all
  six would pay full price. Creating the cache first, then sending the calls, guarantees every call reads it.
- **No region lock was needed.** The first build assumed caching was unsupported on Vertex's `global`
  location and pinned the cached model to `us-central1`. A live check found caching worked on both
  (about 97% of input read from cache either way), so the cache now uses the game's own location.
- **Structured output and the cache work together.** The LangChain Gemini client sends the output schema
  as generation configuration, not as a tool, so it does not conflict with a cache that holds plain text.
- **Caching removed the input penalty, not the output cost.** A probe on a ~6k-token prefix read 5,520 of
  5,648 input tokens from cache in each role call. Six role calls still produce six outputs, and output was
  the main cost on the Pro model. So per-role extraction remained more expensive than one combined call;
  caching only stopped the input from multiplying by six (about 72% less input).

Extraction later moved from one call per role to one call per (role, game phase) pair, a **cell**. The
cached prefix is identical across cells, so nothing in the economics changed.

*Provenance:* commits `a15689c` (prompt split), `03a196b` (fan-out), `9d65336` (cache), `571907d`
(region).

---

## 6. 2026-07-13 — A second consumer: the tell detector

**Motivation.** A new evaluation tool, the **tell detector**, reads a game transcript and tags each
player's tell-tale behaviour, one call per (game, player, channel), at temperature 0. The nine calls for
one (game, channel) share a 5.5–8k-token prefix (rules, transcript and checklist): above the 4,096
minimum and read nine times. Its first 60-game run billed **$13 against an estimate of $1.50–2.50**, so the
prefix became worth caching. The tool reused the extraction design: create a cache object, run the calls
against it, delete it.

**The mechanism transferred.** On a real game prefix, 5,374 of 5,716 input tokens were read from cache
(94%). The same usage data explained the estimate miss: each call spent **1,051 reasoning tokens**,
because the model's 1,024-token thinking budget was used in full every time. Reasoning bills at the
output rate and does not appear in an estimate built from input tokens.

**But caching cost reproducibility.** The day before, the uncached detector had produced identical
output on two separate runs (all 179 rows matched), and it was recorded as deterministic at temperature
0. Under caching that broke. Cached and uncached runs on the same game agreed on 0.82 of rows, and two
identical cached runs agreed with each other on only 0.56 (vote channel) and 0.77 (discussion). Caching
shipped as **opt-in, default off**, so measurement runs would stay reproducible.

**The same day: the determinism claim was itself wrong.** The obvious follow-up asked whether caching
plus minimal thinking (a 128-token budget) would restore stability. Two identical runs per configuration
on one game:

| | uncached | cached |
|---|---|---|
| **thinking = low** | 0.90–1.00 | 0.56–0.77 |
| **thinking = minimal** | 0.67 | 0.83 |

Two corrections followed:
1. **No configuration is exactly reproducible, including the uncached baseline.** The uncached run
   agreed with itself on 0.90 this time, while one of its runs also matched the previous day's output
   exactly. The 179-row match had been one lucky pair. The endpoint flips occasional rows in every
   configuration; caching makes it worse, but it is not the only cause.
2. **Minimal thinking breaks detection.** On the six hand-labelled cells of that game, the minimal-thinking
   runs correctly found 0 of the labelled days against 2 for low thinking, in every run, and wrote about
   30% fewer rows. Six cells is too few to size the loss, but 0 in every run is not borderline. The full thinking
   budget was doing the detection.

So the detector stayed uncached with low thinking, and reproducibility moved from the model to the
stored outputs: hand labels certify a stored run, and a rerun is a new sample.

**The same day again: accuracy decided it.** Exact reruns had never mattered to the detector's users,
which aggregate its output, and extraction had already accepted the same trade when it adopted caching.
One test remained: does the cached configuration score as well? The rule was stated before running:
within a few points of uncached, cached becomes the default. Cached, over 5 games and 40 labelled cells:
vote precision 0.83 against 0.77, recall 77% for both; discussion 0.93 / 87% for both. **The detector
now runs cached by default**, at about $0.12–0.14 a game instead of $0.22 (caching discounts input; the
reasoning tokens remain).

Two distinctions from this episode stand. "The cache works" and "the cache leaves output unchanged" are
different claims: the second can fail through the prompt reorder caching requires (§4) and, separately,
through the provider serving cached requests differently (this section). And an estimate built from input
tokens misses a thinking budget that is used in full.

---

## 7. 2026-07-26 — DeepSeek seats: an automatic cache that fires

**Motivation.** Everything above was measured on Gemini. In July the game gained DeepSeek seats
(`deepseek-v4-pro`, chosen on cost and dialogue quality; see
[`../model_selection/`](../model_selection/report.md)). DeepSeek caches prompt starts automatically, and on
this workload it fired: the first measured game read about 31% of its input from cache (450k of 1.50M
tokens). Hypothesis A had been disproved on Gemini, not in general. On a provider whose automatic cache
works, prompt order is a lever again.

**Problem → fix.** The day-discussion prompt opened its message with the **brief** (the line telling the
seat why it speaks now, such as "you were asked a question by X"). The brief changes every turn and sat
above the transcript, so it cut the shared start short. The brief moved below the transcript. Everything
above the transcript is now stable for the day, so a seat's turn begins with its previous turn's prompt
up to the end of the old transcript.

The same pass found one breaker in the memory lookup's prompts: a `Round:` header, left over from an
earlier design in which a day ran in rounds. Removing it from all eight lookup templates let them share
their start across a day.

**Rejected:**
- *The rest of layout (c)*: moving the role card and private information after the transcript so that
  different seats share it. Rejected on an expectation of worse play, because a seat would learn who it
  is only after reading the whole transcript. No test was run.
- *Sharing a start between the lookup call and the turn call.* The two prompts differ from the first token,
  and sharing would mean pasting the discussion instructions into a call that must not follow them, for a
  reuse of two.

**Result.** Two v4-pro games, before and after: **31% → 40.5%** of input read from cache, effective input
price $0.292 → $0.260 per million tokens. One game per side; the same release also capped message length
at about 120 words, and the second game was about half as long. So this shows the direction, not the size
of the reorder's effect. Shipped with the rest of that release's prompt changes.

*Provenance:* commit `47d9a719`; game costs in `../model_selection/report.md`.

---

## 8. 2026-10-04 — Many providers: measure each one before it plays

**Motivation.** By October the candidate seat models spanned OpenAI, DeepSeek and several models served
through OpenRouter (GLM, Qwen, MiniMax). Each caches differently, and a model's cost per game depends on
how much of a real turn it reads from cache. That had to be measured per model.

**Build.** The model-admission check (the tests a model passes before it can play) gained a caching
step: the provider's minimum cacheable prompt, and the cached share of three real prompts (a seat's turn,
the same seat's next turn, another seat's turn). The hallucination bench, which compares models on the same
turns, began recording cached tokens so each model's cost includes its discount.

**Result** (one probe per model; the table is in the report, §4.2):
- Claude, Qwen and OpenAI read much more of a seat's own next turn (57–90%) than of a neighbour's (0–36%).
- GLM, DeepSeek and MiniMax read little of either (3–13%), DeepSeek despite reading 31–41% of a live game
  (§7). The probe sends only three requests.
- Gemini 3.5 Flash-Lite cached nothing up to 8,192 tokens, repeating the June finding on a newer model.

**A re-check of the rendered prompts.** Rendering real prompts showed where the shared start ends. One
seat's successive turns share about 84% of their prompt. Two different seats share about 800 tokens,
because each seat's role card comes right after the preamble. The June plan's other moves (role card to
the end of the system message, the closing rules into it) had never been made. Two options were drafted:
- **A:** the role card last in the system message, with the fixed closing rules moved into it;
- **B:** a fully fixed system message, then the public board and transcript, then everything private to
  the seat, then the brief, so different seats share the transcript.

Neither was adopted. Each changes every seat's prompt at once, needs the owner's decision, and saves
nothing on Gemini. (These figures come from working notes; no data file was kept.)

*Provenance:* commits `a061474b` (admission caching step), `ae858f6a` (bench cached tokens); results in
`evaluation/eval_results/model_admission/`.

---

## 9. 2026-10-12 — Claude: a cache the request must mark

**Motivation.** Claude Haiku 5.5 passed admission as a seat model. The same week the Gemini budget ran
low ($24.90 left), and offline jobs (synthesis, re-extraction, judging) moved to Claude Message Batches,
Anthropic's half-price asynchronous API. Claude has no implicit cache. It stores a prefix only where the
request places a cache mark, and a later request reads it only if one of its own marks can find it,
looking back at most 20 content blocks.

**Seats.** *The simple option fails.* Claude's automatic mode places one mark at the end of the prompt.
Our prompts end with the brief, which changes every turn, so every call would pay 1.25× to store a prefix
that no later call reads. *Chosen design:* mark the system message, and send the turn's message one line
per content block with a mark on the transcript's last line. The seat's next turn has a transcript a few
lines longer, and its own mark finds the previous one. A seat's next turn read **9,258 of 10,206** input
tokens from cache. *Accepted limit:* if more than about 20 lines arrive between two turns of one seat, the
lookback can miss; this has not been measured.

**Offline jobs.** The direct and batched Claude calls gained a marked prefix: each request can carry its
own (one per game), kept for an hour so a batch waiting in a queue still finds it. Synthesis was the first
user. 112 calls on Sonnet 5.5 cost $4.02 as direct calls. A rerun with a revised prompt, as one batch with
the rules block cached, cost **$1.51** (350k uncached input, 583k cached reads, 199k cache writes, 170k
output). The prompts differed, so this shows the order of the saving, not a matched comparison.

**Extraction: the estimate that missed.** Extraction had just become an offline job over games saved at
their end. Its Claude check was estimated at under $0.50 for two games and cost $2.69, because no call read
the cache: Claude counts the enforced output schema as part of the cache key, and every cell has its own
schema. The fix wrote the schema as text after the cached prefix. The first full run (21 games) then cost
$19.99 against about $9.50: retries of replies that failed validation each stored their own copy of the
prefix, and about 15% of batch requests stored the prefix instead of reading it. Retries now go through a
second batch. The full account, with the usage records, is the case study in the report (§4.5).

**The Gemini path of the same job** runs as ordinary online calls on a cache object per game. Gemini's
cache holds prompt text only, so cells with different schemas share it. A Vertex batch was considered the
day before and set aside: on Vertex the cache and batch discounts do not stack, and extraction input was
already mostly cached.

*Provenance:* commits `5685bf29` (seat marks), `c5a6ba0c` and `4a8a5e82` (cached prefixes, batches,
1-hour cache), `8c961496` (schema after the prefix), `c3815883` (second-batch retries), `cf63039f` (the
Gemini path); runs in `batch_results/extraction_runs/*_2026-10-12/` and `../memory_system/v8/experiment_log.md`.

---

## 10. 2026-10-12 — A cost read that exposed two holes

**Motivation.** Seven test games with memory on (four on Claude Haiku 5.5, three on GPT-6 Luna) were
costed from the traces. Memory lookups came to about 40% of a Haiku game, against 20–28% of a Luna game.
Two causes were found behind the Haiku figure, and a third problem surfaced in the extraction check.

**Problem → fix 1: Claude's cache tokens never reached the traces** *(as believed then; §11 found they
were recorded under other names).* The tracing tool (Langfuse) read
Anthropic's raw usage block, whose input count excludes cache reads and writes. A cached turn was
therefore traced as about 1,000 input tokens out of about 10,000. The fix makes the tracer read the full
usage, with reads and writes as their own token types. The direct and batched Claude calls bypassed the
tracer entirely; each is now recorded with its tokens and cost.

**Problem → fix 2: the lookup prompt gave Claude nothing to mark.** It was a single user message with no
system message and no line to place a mark on, so every lookup was sent uncached. The rules became the
system message, identical for every lookup in a game; the instructions come next and end on a markable
line; the changing game state comes last. By design about 20k of the prompt's 26k characters are now a
stable prefix. No game has measured it yet.

**Problem → fix 3: cache writes were priced as plain input.** The extraction check (§9) showed its cost
summary pricing 1-hour cache writes at the input rate. Writes now cost 1.25× input for the 5-minute cache
and 2× for the 1-hour cache, both in the project's cost code and in the trace pricing. The trace pricing
also covers every name a provider's client uses for cached tokens, because a token type without a price
counts as free. *(§11 found two places this fix did not reach.)*

**Standing rule (owner, 2026-10-12).** Lay out every prompt so as much input as possible is cached:
stable text first and identical across calls, the changing part last, the stable prefix marked on Claude.
When measuring cost, read cache reads and writes from the traces, never input tokens alone.

*Provenance:* commits `d9e346fd` (traces), `1ad07a81` (lookup layout), `c0b77492` (write pricing).

---

## 11. 2026-10-13 — The first whole-game cached shares: Luna and Haiku

**Motivation.** A proposal to let different seats share the transcript (move the role card and every
seat-private part after it) needed a baseline: how much of a real game's input is read from cache today?
The admission probe (§8) measured three prompts, not a game. The seven memory-on test games of §10 were
already traced, so their cached share could be read out without new paid calls.

**Method.** A read-only script summed every generation's token counts per Langfuse session. All seven
games ran on the same code, before the memory-lookup layout fix of §10. Two limits: the Haiku runs
shared one session per two games, so their rows are pairs; and turn calls and lookup calls carry the same
trace name, so their shares cannot be separated.

**GPT-6 Luna, three games:**

| Game | Calls | Input tokens | Read from cache | Written to cache | Neither |
|---|---|---|---|---|---|
| 0 | 227 | 1,348,544 | 22.3% | 77.0% | 0.7% |
| 1 | 199 | 1,173,690 | 22.1% | 77.2% | 0.8% |
| 2 | 168 | 999,105 | 29.0% | 70.3% | 0.7% |
| all | 594 | 3,521,339 | **24.1%** | **75.1%** | 0.7% |

**Claude Haiku 5.5, four games in two sessions:**

| Session | Calls | Input tokens | Read from cache | Written to cache | Not cached |
|---|---|---|---|---|---|
| haiku_0 (2 games) | 390 | 3,662,485 | 25.4% | 39.8% | 34.8% |
| haiku_2 (2 games) | 498 | 4,743,755 | 28.2% | 36.5% | 35.3% |
| all | 888 | 8,406,240 | **27.0%** | **38.0%** | 35.1% |

**What the numbers show.** Both models read about a quarter of their input from cache, which is the
reuse between one seat's successive turns. They differ in what happens to the rest:

- **OpenAI writes almost every prompt start.** Its automatic cache stores what it sees, so on Luna nearly
  all unread input was written. OpenAI's documentation (read 2026-10-13) says that from GPT-5.6 on a write
  costs 1.25× normal input; assuming GPT-6 Luna falls under that rule, Luna's input cost about **97%** of
  what it would with no caching (0.1 × read + 1.25 × written + 1.0 × neither).
- **Claude writes only up to a mark.** What follows the marks is sent uncached at the normal price: the
  brief, the memory block, the closing rules, and every memory lookup, which had no marks in these games.
  Haiku's input cost about **85%** of uncached. Most of its 35% uncached share is expected to be the
  lookups; the layout fix should lower it, but no Haiku game has run since.
- **The admission probe overstated a game's reuse.** It measured 57% for a Luna seat's next turn; the
  games read 24%. One plausible reading: most calls are not a seat's next discussion turn (votes, night
  actions and lookups use other templates).

So on both models about three quarters of input is either written and never read, or not cached at all.
That is the room a cross-seat layout would work in: each token moved to a read saves about 1.15× its input
price where it was written, and 0.9× where it was not cached.

**Two corrections to §10.**
1. **Claude's cache counts did reach the traces before the fix.** The pre-fix Haiku generations carry them
   under Anthropic's raw names (`cache_read_input_tokens`, `cache_creation_input_tokens`). Langfuse neither
   labelled nor priced those names, so the reads and writes counted as free and the input field showed only
   the uncached part. The fix's effect was to label and price them, not to recover missing data.
2. **The cache-write pricing did not reach two places.**
   - Langfuse's price definitions price a write (`input_cache_creation`) only for Claude models. Luna's
     writes, 2.6M tokens across the three games, are priced at zero there, so Langfuse shows each Luna game
     at roughly half its cost.
   - The server's usage meter counts total input and cache reads only, so every write is priced at the
     normal input rate rather than 1.25×. On Luna game 0 that understates the cost by about 12%; Claude
     seats are affected the same way. The premium is priced correctly only for the direct offline Claude
     calls.

   The §10 cost figures for these games ($0.155, $0.188, $0.217 for Luna) agree within about 5% with a
   recomputation that prices writes at 1.25× for games 0 and 1, so they were probably priced with writes
   included; how they were computed is not recorded.

*Provenance:* sessions `v8_luna_mem2_{0,1,2}_all_enabled` and `v8_gate_haiku_{0,2}_all_enabled`
(`batch_results/v8_luna_memory/run2/`, `batch_results/v8_gate_haiku/`); prices from the model catalogue
($0.10 / $0.01 / $0.50 per million for Luna). Read with `evaluation/experiments/game_cache_share.py`
(read-only; rerun it on any later game's batch results to compare).

---

## 12. 2026-10-13 — Why OpenAI reused so little, and what an enforced schema costs

**Motivation.** §11 read Luna's 24% as reuse between one seat's successive turns. A separate read of the
Luna prompts, call type by call type, did not support that, and it changed what to build next.

**What the per-call read found** (a one-off read of the traced prompts; no script kept):
- Discussion turns read about 58% of their input from cache, but seven discussion calls under one system
  message each read exactly **4,582** cached tokens while the transcript grew. The reads were the fixed
  system message, not the growing transcript.
- Memory lookups, votes and night actions read nothing. Discussion is about 40% of a game's input, so
  40% × 58% ≈ 23% of the whole game, which is the 24% of §11.

**Three causes, each checked against the code and OpenAI's documentation (read 2026-10-13):**
1. **OpenAI stores an entry only at a boundary.** From GPT-5.6 on, an entry is written at the end of the
   latest eligible message (a user message, the end of the opening developer block) or at an explicit
   breakpoint. Lookups check only boundaries. A turn's user message ends with the brief, which changes
   every turn, so the end of the transcript is never a boundary, and only the system message is reused.
   This corrects §11: reuse of the old transcript between a seat's turns happens on Claude, where the
   harness marks the transcript's last line (§9), and not on OpenAI. OpenAI also offers explicit
   breakpoints (`prompt_cache_breakpoint`, with `prompt_cache_options.mode = "explicit"`); whether our
   Chat Completions client can send them is not yet checked.
2. **The night system message changes every call.** It ends with the retrieved memories and the seat's
   strategy note.
3. **Vote and night schemas carry each seat's legal targets.** `output_schema_with_legal_targets`
   rebuilds the schema with the living players minus the seat itself, so it differs between seats and at
   every death. An enforced schema acts as the very start of the prompt on both providers: OpenAI renders
   schemas before the messages, and Claude counts the schema in its cache key (§9). So votes and night
   actions cannot share across seats, and different call types (discussion, vote, night, lookup) can never
   share with each other, because their schemas differ by nature.

**A constraint from the owner.** Legal targets stay limited by code, in the schema, and never move into
the prompt as text. Dropping the target list from the schema was therefore ruled out. That left two
levers: cache boundaries in the right place (Claude marks, OpenAI explicit breakpoints, the stable part
first), and an **unenforced** schema: the schema written as text after the cached part, the reply
validated in code against the same per-seat schema, so an illegal target still fails. The open question
was whether unenforced replies fail often enough that retries would slow the live game.

**Trial: unenforced against enforced.** Built first: an unenforced path for Claude (`json_mode`, the
schema appended to the last user message after the cache marks), a reply parser that reads only a
thinking model's text and tolerates a sentence around the JSON, and a field-order check in the admission
probe. Both models at their game thinking levels; 17 ten-seat schemas × 10 samples per mode, plus 8 real
ten-seat discussion turns × 3 variants in the unenforced mode.

| | Enforced probes | Unenforced probes | Unenforced real turns | Call time, unenforced vs enforced |
|---|---|---|---|---|
| GPT-6 Luna | 167/170 | 169–170/170 over two runs | 48/48 | +0.5 s |
| Claude Haiku 5.5 | 170/170 | 170/170 | 47/48 | −0.8 s, ~540 fewer input tokens |

- **Unenforced replies almost never failed:** 1 in 388 Luna calls (a role outside the list in a read) and
  1 in 412 Haiku calls (a malformed read entry), each caught by validation and worth one retry. Luna's three
  enforced misses were empty `reads` lists, a content check, not a parse failure.
- **On Haiku the enforced schema costs tokens and time.** It added about 540 hidden input tokens per call,
  consistent with the 3.6k the extraction schemas added (§9), and enforced calls ran 0.8 s slower, which
  fits the schema compilation Anthropic documents for a new schema.

**The field-order problem.** A reordered reply still validates, so the pass counts could not show it. The
schemas order their fields so a seat commits before it speaks. Checked on the real turns:
- Luna: 24/24 in schema order. Haiku enforced: 24/24, which confirms the decoder fixes the order on Claude.
- **Haiku unenforced: 15/24.** Every mismatch put `reads` first; in 2 cases the two memory-verdict fields
  went after the message. `reads` and the strategy note always stayed before the message, and with memory
  off the moved verdict lists were empty.
- One plausible cause: the user message opens with "*Before your decision, record your current read…*",
  while the schema put the memory verdicts first. Haiku followed the prompt over the schema.
- **Asking in words did not fix it.** Adding "write its fields in exactly the order the schema lists them"
  to the unenforced instruction gave 13/23 in order. The instruction at the end lost to the prompt's
  opening line, and it was reverted.

**Decision (owner): reads first in every seat schema.** The shared base of all 16 seat schemas now orders
reads → strategy verdicts → memory verdicts → strategy note → decision, and the discussion prompt's
examples follow. The July reads work (T1c, `../generation_prompt/validation_plan.md`) tested reads
*before the strategy note and the action*; that order is kept, and the position of the memory verdicts
relative to reads was not what it tested. **Result: Haiku unenforced, the same 24 real turns, 24/24 in
schema order and no failures.** This changes every seat's prompt in both modes, so it is a new prompt
epoch.

**Still unmeasured:** whether unenforced replies or the new order change message quality (the
hallucination bench), and Luna's field order under the new schema.

*Provenance:* configs `evaluation/config/model_admission/unenforced_schema_trial_2026_10_13.json`,
`unenforced_field_order_2026_10_13.json`, `haiku_field_order_{json_mode,json_schema,instructed,reads_first}_2026_10_13.json`;
records under `evaluation/eval_results/model_admission/` with the same labels.

---

## 13. 2026-10-13 — The shared-prefix layout: built, checked, measured

**Can OpenAI take explicit breakpoints through our client?** *Tests:* whether §12's missing piece exists
for the Chat Completions API we use. The installed SDK has it: a request-level
`prompt_cache_options: {"mode": "explicit"}` and a `prompt_cache_breakpoint` on text content parts; OpenAI
matches against the latest 80 breakpoints of a request and writes the latest four. A three-call probe on
GPT-6 Luna (rules in the system message, 40 transcript lines each marked, a private part unmarked):

| Call | Read from cache | Written |
|---|---|---|
| Seat A | 0 of 2,590 | 0 reported |
| Seat A's next turn, 3 lines longer | **2,561 of 2,678** | 87 (the 3 new lines) |
| Seat B, same transcript | **2,648 of 2,674** | 0 |

Both reuse paths that never worked on Luna (the growing transcript, and another seat) worked, and the
changing private part was never written. The first call reported 0 written although the second read what
it stored; that was not explained. LangChain passes both fields through unchanged.

**The build** (behind `WW_PROMPT_LAYOUT=shared_prefix`, today's layout untouched without it). Every seat
turn and memory lookup now opens with what all seats and call types share: a system message of the rules
alone, then the public record (earlier days, today's transcript) ending on the user message's only
transcript rule. The board, the role card, the call's instructions, private results, brief and memory come
after it; night prompts move their memories and strategy note out of the system message. The transcript is
published lines only, so a held-back turn's note is dropped (round turns keep theirs on the candidate until
the round's filter has decided). Claude keeps its two marks; OpenAI gpt-6 models get explicit-only caching
with breakpoints on the system message and the record's lines. A test renders every living seat's
discussion, vote, night, pack and lookup prompt in one game and finds one identical prefix.

**Smoke check: do both APIs accept it?** *Tests:* refused requests or broken output under the new layout.
The 8 real ten-seat turns × 3 variants of §12, both models, both schema modes: 0 failures in 96 real turns,
field order kept in all, and the share another seat read from cache rose from 0% (Haiku) and 29% (Luna)
to 53–71%. A seat's own next turn fell on Haiku from 90% to 77% (enforced), as expected: its role card now
sits after the transcript and is sent again each turn.

**Bench: does the layout, or an unenforced schema on top of it, change message quality?** *Tests:* more
factual errors. GPT-6 Luna, all 18 ten-seat discussion turns × 5 samples, judged by Claude Haiku 5.5
against each case's golden:

| Arm | Bad samples | Against today, per case (better / worse) |
|---|---|---|
| Today's layout, enforced | 11/90 (12%) | — |
| Shared prefix, enforced | 13/90 (14%) | 4 / 5, p = 1.0 |
| Shared prefix, unenforced | 10/90 (11%) | 4 / 2, p = 0.69 |

No detected change at this power: 18 cases would show only a large regression (about ten points). It
covers discussion turns only; the ten-seat frozen set has no votes or night turns.

**Games: what does it save?** Two games per arm on the same two seeds and lineups, memory on (strategy
points from `ten_seat_v2`), every call on the seat model. "After" means the new layout with the unenforced
schema; for Haiku a third arm kept the schema enforced. Per call, because game length differed:

| | Cost per 1,000 calls | Read / written: vote | Read / written: night | Discussion turns per game |
|---|---|---|---|---|
| Luna, today's layout | $0.89 | 0r / 100w | 0r / 100w | 70 |
| **Luna, new layout** | **$0.64 (−28%)** | 64r / 0w | 60r / 0w | 72 |
| Haiku, today's layout | $1.10 | 0r / 87w | 0r / 99w | 65 |
| Haiku, new layout, unenforced | $1.10 | 63r / 1w | 56r / 0w | 87 |
| Haiku, new layout, enforced | $1.07 | 0r / 78w | ~18r / 55w | 89 |

- **On Luna the change pays:** input cost per call fell 36%, output 10%, and votes and night actions went
  from never reading the cache to reading about 60% of their input.
- **On Haiku the input saving was spent elsewhere.** Unenforced, Haiku reasoned more on seat turns (about
  1.5× on discussion, 3–5× on votes, against both enforced arms). Enforced, its reasoning stayed near
  today's, but the per-seat target lists kept votes and night from sharing the cache. A day-summary rise
  first read as a schema effect appeared in the enforced games too; it was game-to-game variation.
- **Haiku's games got longer under the new layout, in both schema modes:** about 88 discussion turns per
  game against 65, so a Haiku game cost about 20–25% more. §14 explains why.

*Provenance:* `evaluation/config/model_admission/smoke_shared_prefix_*_2026_10_13.json`,
`evaluation/config/hallucination_bench_shared_prefix_luna.json`, `batch_results/cache_ab_2026_10_13/`
(games), read with `evaluation/experiments/game_cache_share.py`; commits `0d936b08` (layout), `5e3c5f30`.

---

## 14. 2026-10-13 — An unexpected benefit: Haiku stops staying silent

**The question.** Haiku's longer games could have been waste: wordier messages, or the same point made
again. Reading the games turn by turn said otherwise.

**What changed is how often a seat volunteers, not how much it says.** Messages ran 40–50 words in every
arm. On turns where a seat may pass, Haiku in today's layout almost always did, consistently across six
games (four gate games of 2026-10-12 and the two baseline games):

| Spoke rather than passed, day 2 on | Openings | Proactive turns |
|---|---|---|
| Haiku, today's layout (6 games) | 7–8% | 20–35% |
| Haiku, new layout (4 games, both schema modes) | 23–26% | 53–54% |
| Luna, today's layout (5 games) | 28–43% | 58–72% |

Each volunteered line invites answers, so reactive turns followed (13 before, 45–56 after). The new layout
brings Haiku to about Luna's level of participation.

**One seat can set a day.** Day 2 of game 1, same seed, same night: the Sentinel had watched player_8 and
seen player_2 visit. In today's layout it passed its opening, noting "*Do not claim early*", every seat
passed, and the day had 3 lines. In the new layout it opened with "*I'm the Sentinel. On night 1 I watched
player_8, and player_2 came to them that night. Player_2, what were you doing at player_8's house?*",
noting "*Share results early when they help town*"; the Chanteuse answered and the day ran to 11 lines.
In game 2 of today's layout, day 2 had no lines at all.

**One plausible reading.** The role cards tell information roles to be careful: the Sentinel's says
"*revealing your role could mark you as a night target*", the Healer's "*don't draw fatal attention*". Today
those lines sit in the system message; in the new layout they sit in the user message after the transcript,
next to the opening rules ("*share new information from the night*"), the seat's own night results and the
brief. The words are identical, only their position moved. Haiku seems to weigh the system message's
caution heavily and hold back; Luna does not. The position effect is inferred, not isolated.

**Decision (owner).** Today's Haiku is too quiet; the extra participation is kept as a benefit of the
layout, not counted against it. The Phase 3 hand reads (batch 4, 2026-10-10) had already named
"*information roles withholding results*" and "*thin, repetitive days*" as problems. Haiku's cost per game
rises because its games now contain more discussion; its cost per call is unchanged.

**Not measured:** whether Haiku plays better under the new layout (town win rate, bad claims). Two games
per arm cannot say.

---

## 15. Where it stands

Caching is a property of each provider: automatic on DeepSeek, boundary-based on OpenAI (implicit at the
last eligible message, or explicit breakpoints), marked on Claude, a cache object on Gemini. The
shared-prefix layout (§13) makes votes, night actions and lookups share the day's transcript across seats
on both Luna and Haiku. On Luna it cuts the cost per call by about 28% with no detected change in message
quality; on Haiku it saves nothing per call but ends its habit of passing almost every free turn (§14).
The layout is still a process-wide flag; choosing it per model means moving it into the model catalogue.
Open: game quality under the new layout beyond factual errors, the bench's missing vote and night cases,
the lookup layout's effect, and the June extraction reorder, ranked in the report.
