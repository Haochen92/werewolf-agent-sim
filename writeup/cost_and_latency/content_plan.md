# Cost and latency: portfolio content plan

Status: candidate plan, 2026-10-29, from a subagent pass checked against the record. The owner chose to keep the default recommendations for now and review all plans later; nothing here is approved. The open questions at the end stay listed; the defaults taken are below.

## Defaults taken (owner 2026-10-29: keep the recommendations for now)

- Pending owner review (an evidence edit): a short dated entry in `evidence/caching/experiment_log.md` recording the re-derived Haiku figures ($0.2146 over 197 calls, $0.2550 over 228), so the page's first number has a source.
- Four Level 2 pages: stage fit merged into model choice. Chapter 6 becomes stage fit's main home; Evaluation's admission page keeps the speed criterion and links here (in Evaluation's reconcile pass).
- Revised 2026-10-30 after an outside review (owner approved): the frame is managing the bill and the wait, with every saving checked in real runs; the memory-off 16 games lead, labelled model-call cost; visible waiting is explained before the percentage ("roughly 3–5%", two backlog assumptions); the caching section is about total cost, with Haiku's higher per-game cost on Level 1; offline work is a scheduling decision and "halves the price" is dropped; forced transitions removed; one tag, LLM inference optimisation.
- Section headings: "What does a game cost?", "When does the player have to wait?", "When does prompt caching save money?", "What work can run offline?"
- The Opus 5.5 estimate moves to Level 2, pending the owner: its rates need a cited source ($4 / $20 / $0.20 / $5 per million tokens; not in `pricing.py`), and it reprices memory-on games, so it no longer matches the memory-off lead. It may return to Level 1 as a reference point once both are fixed.
- The lead figure is memory off, $0.08–0.26 (16 games, 2026-10-18; voices on in 8, off in 8), labelled model-call cost. The memory-on game ($0.215) is a labelled supporting example for the cost drivers.
- AI-only games are enough; no served game with a human seat is priced.
- Votes at medium thinking stay an open decision and are stated as open; the cost shown is at today's setting.
- Haiku's change in participation: one sentence on Level 1 (its games cost more per game), the full story a subsection of the prompt-cache page.
- Section 1's supporting example: the output share of the bill, labelled memory on.
- Dropped: the "cheapest per token isn't cheapest per game" hook. Flash-Lite is not cheaper per token than Haiku or Luna (`pricing.py`); the map's note is corrected.
- Luna's $0.17 (2026-10-10) predates the 2026-10-13 fix that priced OpenAI cache writes; recheck or leave it off.

---

Candidate outline, 2026-10-29. Not page copy. Starting arrangement: `writeup/structure_proposal.md`
ch. 6 (five Level 2 pages). Built from the sources read in full or by section (listed under
"Disposition"). Three figures were re-derived today from the traces (marked **[re-derived]**); they are
not yet written in any evidence record (open question 1).

---

## 1. Frame

*Revised 2026-10-30 after an outside review, approved by the owner. The first cut promised a cleaner
optimisation story than its evidence supports: it led with two memory-on games while memory is off by
default, set that cost beside a wait measured on other games, read 2.7–5.1% as a range over games (its
endpoints are two assumptions about the stage's backlog), said batching "halves the price", and chained
the sections with transitions the evidence does not support ("the wait fixes the seat model"; "caching
pays most where nobody waits", when caching savings depend on reuse, not on who waits).*

**Reader's question.** An AI game with ten players makes hundreds of model calls, and a person at the
table waits on the AI turns. What does it cost, how long does the person wait, and what keeps both down?

**Central answer.** Serving an agent game means managing both the bill and the time people spend
waiting. Model choice, prompt caching and offline batching address different parts of that problem, and
each one's benefit had to be checked in actual runs. The checks found the useful results: caching can
cut input cost without cutting the total bill; a batch discount does not remove the cost of retries and
cache misses; and a model call's latency does not turn directly into visible waiting.

**The Level 1 shape.** Four question headings, each the next question a newcomer asks, each answered in
its first line. No forced transitions between them: the four questions are the progression.
- **Altitude.** Name prompt caching and a batch API, each explained in one clause. Provider-specific
  cache rules, price multipliers, the warming call, schema modes and the catalogue stay on Level 2.
- **Every number labelled** with what it covers: model-call cost only (hosting and infrastructure are not
  counted), the configuration, and the sample.

**Figures (two, small).** Section 1: one game's bill by call type, captioned with its configuration
(memory on). Section 3: a shared-start / private-tail diagram (the rules and public transcript every
seat shares, then each seat's private material).

**Tag.** Public: LLM inference optimisation. Supporting terms where demonstrated: prompt caching, batch
inference, model selection, token accounting, latency measurement. Experimental design is not a tag
here.

**Intro (~150–200 words): what it must convey, in this order**
1. Name the thing: serving a game means paying for every model call and making a person wait for the AI
   turns.
2. Why an agent game is heavy: each of ten seats reads the rules and the growing transcript on every
   turn; a measured game made about 200 calls; discussion runs one speaker at a time; reasoning is billed
   as output.
3. The central answer above: three levers for different parts of the problem, each checked in real
   runs.
4. No exhibit and no caveat bundle in the intro.

---

## 2. Sections in order

### Section 1. What does a game cost?

- **First line:** in 16 measured ten-seat AI-only games on Claude Haiku 5.5 with memory off, model calls
  cost $0.08–0.26 per game. Game length varied, so there is no single fixed price.
  - Configuration: memory off (the default player's setting), low thinking, 2026-10-18; voices on in 8
    of the 16 and off in 8. Source: `evidence/gameplay/data/persona_voice_games/README.md` ($2.48 in
    total). Label it *model-call cost*, not the cost of serving a game.
- **Main point: the cost drivers.** Every call's tokens are recorded and priced, so the bill can be
  broken down. Most of it is output, not input: the model's price and how much it writes, reasoning
  included, decide most of the cost. Game length is the other driver.
- **Supporting example, clearly labelled (memory on):** in one measured game with memory on, about half
  the input was read from cache, yet output was still about 54% of the $0.215 bill **[re-derived]**
  (870,186 of 1,754,420 input tokens from cache; output ≈ $0.116). Source:
  `batch_results/cache_ab_2026_10_13/haiku_after.jsonl`, read with
  `evaluation/experiments/game_cache_share.py`.
- **Exhibit:** that game's bill by call type (discussion $0.110; memory lookups $0.034; night actions
  $0.028; votes $0.025; day summary $0.011; gate and filter $0.004), captioned "one game, memory on".
- **Moved to Level 2:** the Opus 5.5 repricing ($8–10, estimate). Pending the owner (open question 4):
  the rates need a cited source, and the estimate reprices the two memory-on games, so it no longer
  matches a memory-off lead. It may come back to Level 1 as a reference point once both are fixed (the
  owner's 2026-10-25 worked hook wanted one).
- **Links to:** L2-1, *What a game costs, and how it is counted.*

### Section 2. When does the player have to wait?

- **First line / main point:** a model call can take several seconds without making the stage pause,
  because the server works out the next action while the browser is still showing earlier events. The
  stage waits only when the next event is not ready by the time it is needed.
- **Then the measurement:** on Haiku, the stage would have waited roughly 3–5% of its playing time,
  estimated from the traces of seven hosted games, all played by the owner while building. Level 2
  explains the reconstruction and why the range comes from two assumptions about the stage's backlog
  (`frontend/docs/stage_fit/README.md`, "What it found"; the bounds are its "restart" and "continuous"
  readings).
- **Where it waits (one or two sentences):** mostly in runs of passes: a pass is shown for 4 seconds
  while the next seat's call takes a median 5.4 seconds. Holding a pass longer would hide the pause but
  make the game longer: a pacing trade-off, not a latency fix, and not decided.
- **Model choice:** each job's model is chosen against its task quality, its cost and, for a live seat,
  visible waiting, not latency alone. Never "best". Whether a candidate can serve at all is
  Evaluation's model-admission page (one link).
- **Links to:** L2-4, *Choosing a model for each job, and keeping the stage ahead* (its question: how do
  we choose models that meet each job's requirements? Stage fit is its live-seat example), plus the
  inline link to Evaluation's model-admission page.

### Section 3. When does prompt caching save money?

- **First line / main point:** sharing the start of every prompt reduces repeated input charges; whether
  that lowers the bill also depends on how much the model generates and how many turns the game
  contains. Every call opens with what all players share, the rules and then the public transcript, and
  each seat's private material comes after it (the diagram).
- **Why the layout matters (the idea, no multipliers):** writing a cache costs more than plain input, so
  a prompt start that is written and never read again costs more than not caching. The layout lets later
  calls read what earlier ones wrote. One sentence separates this from chapter 1's node cache (it stores
  a finished AI turn; the provider's prompt cache stores processed input, never an answer).
- **Lead example: paired games, same deals.** The layout cut GPT-6 Luna's cost per call by 28%. On Haiku,
  the site's model, the cost per call did not change, because it reasoned more and used up the input
  saving. And Haiku's games under the new layout cost more per game: its players stopped passing nearly
  every turn, so a game held more discussion (65 → 87 discussion turns a game). The owner keeps the extra
  participation; whether it plays better was not measured. Source: `evidence/caching/report.md` §4.3,
  §4.5.
- **Moved to Level 2:** provider-specific cache rules (marks, breakpoints, automatic caching) and price
  multipliers.
- **Links to:** L2-2, *Sharing the transcript: the prompt-cache layout*. Inline: chapter 1's page on
  adding a human (checkpoint, node cache and prompt cache told apart).

### Section 4. What work can run offline?

- **First line / main point:** lesson extraction does not need to finish while someone plays, so
  selected games are processed later through a discounted batch API. It is a scheduling decision first:
  the work leaves every player's wait, and becomes eligible for batch pricing.
- **Second point, from the lead example: batch pricing still has to account for cache writes, misses and
  retries.** A 21-game extraction run on Claude Sonnet 5.5 cost $19.99 against about $9.50 estimated,
  mostly because of cache writes: replies that failed validation were retried in a way that wrote new
  caches, and some batched requests wrote the cache instead of reading it. Retries now keep the shared
  layout; the saving has not been measured in a comparable run. Source: `evidence/caching/report.md`
  §4.6; `evidence/extraction/post_game/report.md` "Cost".
- **Wording rule:** never "halves the price" unqualified. The batch API discounts eligible requests; the
  final job cost depends on the execution path.
- **Moved to Level 2:** the warming call, the enforced-schema retry mechanism, the dollar breakdown.
- **Links to:** L2-3, *Moving work out of the game: offline batch extraction*. Inline: chapter 4 for
  what extraction produces.
- **End of the chapter page.** No closing summary; each section carries its own limit.

---

## 3. Narrative check (main points, in order, as one paragraph)

A ten-seat game's model calls cost $0.08–0.26 on the site's default model, depending mostly on how long
the game runs and how much the model writes, since output is most of the bill. The person at the table
waits less than the model's latency suggests, because the server prepares the next action while the
stage is still showing earlier ones; the stage would have waited roughly 3–5% of the time, mostly on runs
of passes, and models are chosen against quality, cost and that visible wait. Sharing the start of every
prompt makes repeated input cheap, but on the default model the saving went into more reasoning and more
discussion, so the bill per game did not fall. Work that nobody waits for, the post-game extraction, runs
later as a discounted batch, and one run costing twice its estimate showed that retries and cache misses
have to be priced too.

Four questions, each answered on its own terms; the common thread is that every saving was checked
against the bill or the stage, not assumed.

---

## 4. Level 2 pages

| # | Level 2 page | Starting pages merged | Why it deserves a page | Featured story | Exhibits |
|---|---|---|---|---|---|
| L2-1 | **What a game costs, and how it is counted** | "What a game costs", plus cost accounting from `caching/report.md` §5 | A cost claim is only as good as its counting. The page has distinct decisions: record tokens, not dollars, priced at read time from dated rows; price writes at their premium; split by call type; estimate an unplayed model by repricing tokens, and say what that cannot tell. It also explains why costs from different runs do not compare | The 2026-10-12 read that made memory lookups look like 40% of a Haiku game: two holes found and fixed (`caching/experiment_log.md` §10). In the two later games lookups were 16% and 21% **[re-derived]**; that fall mixes the tracing correction with a real saving, and the page says so | One game's bill by call type; a per-model table whose columns are the configuration (model, seats, memory, date, measured or estimated); the Opus estimate with its caveats |
| L2-2 | **Sharing the transcript: the prompt-cache layout** | "The prompt-cache layout" (as proposed) | A per-provider contract (table). The layout resolves a tension: what every seat shares against a seat's own next turn (77% against 90% read). An enforced output schema is part of the cache key (cost side only; validation is chapter 1, page 4). It was verified by provider probes, paired games and a factual-error bench, and it had a side effect on behaviour | Paired games: Luna −28% per call; Haiku unchanged; Haiku's participation (openings 7–8% → 23–26%; free turns 20–35% → 53–54%) and the owner's ruling to keep it | Provider table; the prompt rendered before and after with the cache boundary marked (old render from tag `prompt-layout-baseline`); the paired-games table |
| L2-3 | **Moving work out of the game: offline batch extraction** | "Batch and offline work" | A design decision with two motives: latency (never in a player's wait) and cost (discounted batch pricing on eligible requests). Then a diagnosis of where batch and cache interact: the schema as cache key, the warming call, retry writes, the 15% miss rate. Also: why a Vertex batch was not built (its batch and cache discounts do not stack), and the synthesis saving, to order of magnitude only | The run that cost twice its estimate, in two stages: the $2.69 check, then the $19.99 run | The three-row cost breakdown; optional figure of one shared prefix with about 30 short tails (block 74) |
| L2-4 | **Choosing a model for each job, and keeping the stage ahead** | "Model choice by job" + "Stage fit" | Each part alone is thin. Model choice is one design block (map 96; the triage ruling allows at most one), and stage fit, standing alone, would duplicate Evaluation's admission subsection. Together they answer "why these models": the per-job constraint is the design, and stage fit is the measurement behind the seat's constraint. Also covered: thinking level as a per-job setting (seats low; summary medium with a 90 s budget; votes at medium still undecided); public benchmarks used to shortlist, never to select; the vendor in each slot follows the budget | Where Haiku makes the stage wait (passes, the morning after a night chain), and the stage-side alternative not yet chosen | The job / binding constraint / today's model / evidence table; the waits-by-beat table |

**Merged:** "Model choice by job" and "Stage fit" become L2-4. Five starting pages become four.

**If the owner prefers five pages:** stage fit becomes its own page, *Keeping the stage ahead of the
model* (see open question 2). L1 section 2 would then link to both pages, which breaks the
one-section-one-page pattern of the references.

### Level 3 candidates

- **Possible: *Placing cache marks on a growing transcript*** (under L2-2).
  - A mechanism walkthrough: one content block per transcript line, because Claude's lookup can stop
    only at a block boundary and looks back at most 20 blocks; OpenAI's latest-80 and latest-4
    breakpoint rule.
  - Checks: 9,258 of 10,206 tokens read on a seat's next turn; 2,561 of 2,678 and 2,648 of 2,674 on
    Luna.
  - Source: `caching/report.md` §3.3–3.4.
  - It passes the "adds a mechanism" test and would interrupt L2-2.
- **Possible: *Measuring the stage's waits from traces*** (under L2-4).
  - Rebuilds the stage's beats with the stage's own code, matches events to trace spans, leaves out the
    human's time, and bounds the backlog with two readings (restart, continuous).
  - Source: `frontend/docs/stage_fit/README.md` "How it was measured".
  - Only if L2-4 runs long.
- **Possible, home undecided: *Why Haiku stopped staying silent*.**
  - The role card's cautions moved from the system message to after the transcript. The words were
    identical, and participation rose to about Luna's level.
  - The mechanism is inferred, not isolated; two to six games per arm; play quality not measured.
  - Recommended as a subsection of L2-2. It could instead serve chapter 3 (where an instruction is
    placed) or chapter 1's conversation page (sources of silence). See open question 8.
- **Kept on Level 2:** the run that cost twice its estimate (L2-3 featured story); the Opus estimate
  (L2-1).
- **Not selected:**
  - the tell detector's cache-repeatability tests (chapter 4 and Evaluation);
  - the June Gemini probes (a verification paragraph on L2-2).

---

## 5. Disposition of every source

| Source | Where it goes |
|---|---|
| `evidence/caching/report.md` | §1–2 → L2-2 (where caching fits; provider table); §3.1, §3.6 → L2-3; §3.2–3.4 → L2-2 (+ L3 candidate); §3.5 → L2-2, cost side only (chapter 1 page 4 owns validation and the enforced retry); §4.1 → L2-3 and the L2-1 principle ($8.97 of $10.33 output); §4.2 → L2-2 verification (one paragraph; Evaluation owns admission probes); §4.3–4.5 → L2-2 featured; §4.6 → L2-3 featured; §4.7 (tell detector) → one line on L2-3 at most (caching adopted only after a quality check), home chapter 4; §5 → L2-1; §6 → L2-2 gaps |
| `evidence/caching/experiment_log.md` | §1 (June: about $0.30–0.40 a game, a large comparison planned) → L2-1 opening context; §9 (offline jobs, synthesis $4.02 → $1.51) → L2-3; §10 → L2-1 featured; §11 (write-pricing gap) → L2-1, caught and fixed; §13–15 → L2-2; §16 → gaps |
| `evidence/caching/scripts/` | Evidence link from L2-2 (historical Gemini probes) |
| `batch_results/cache_ab_2026_10_13/` | L1 §1 headline and exhibit, L2-1 (per-game cost, call-type split, Opus repricing), L2-2 (paired games). Read with `game_cache_share.py` |
| `batch_results/extraction_runs/` | Evidence link from L2-3 |
| `evidence/memory_system/v8/decisions.md` §10 (3.8 Flash $0.34 a game; Vertex batch not built), §11 (the offline ruling), §16 (hand-run batch; memory off by default) | L2-3; the ruling's rationale is chapter 6's, and what extraction writes is chapter 4's |
| `evidence/memory_system/v8/experiment_log.md` (2026-10-12 gate cost; the final summary $0.55 / $0.95) | L2-1 featured story; L2-3 cost line |
| `evidence/extraction/post_game/report.md` §3 (one call per role and phase, sharing a prefix), §4 (seat-ID count), "Cost" | §3 → L2-3 mechanism; §4 → L2-4, one line on why extraction gets the stronger model (home chapter 4); "Cost" → L2-3 |
| `evidence/extraction/tell_extraction/` | Chapter 4 / Evaluation. At most one line on L2-4 (a task reshaped so a cheaper model can do it) |
| `evidence/evaluation/model_admission/model_selection.md` (July) | L2-4: only the method rule (public benchmarks shortlist, never select) and the per-job slot idea. The July rankings, nine-seat costs and DeepSeek "strongest table" reads stay off (superseded, unblinded, one or two games, a different prompt version) |
| `evidence/evaluation/model_admission/report.md` §3 | Price rule → L2-1; stage-fit table → L2-4 (main home; see open question 2); speed exclusions (MiniMax, Qwen) stay Evaluation's; 2026-10-10 per-game costs → L2-1 table, labelled; §4 (stalls, rescue, backup key) → chapter 7; "Earlier and lighter choices" (summary Haiku vs Sonnet tie; memory-job models) → L2-4, one line each |
| `writeup/evaluation/model_admission/model_admission.md` | Not duplicated. L1 §2 and L2-4 link to it for "can this candidate serve?" |
| `frontend/docs/stage_fit/README.md`, `results.json` | L1 §2 lead; L2-4 featured story; possible L3 |
| `frontend/docs/live_timing_sheet.md` | Off the page (its per-call latencies are superseded by stage fit; its lag figures are a single flash-lite game) |
| `evidence/gameplay/data/persona_voice_games/README.md` ($2.48 for 16 Haiku games, $0.08–0.26 each, memory off) | L2-1 table row (see open question 5) |
| `evidence/gameplay/data/phase3_luna_games/`, `phase3_flash_games/` (2026-10-10 costs) | L2-1 table, labelled not comparable (see the care list) |
| `evidence/gameplay/deduction/experiment_log.md` §2; `gameplay/turn_prompt/report.md` decision 15 (thinking level) | L2-4 (a per-job setting, with its cost and time); correctness home is chapter 3 |
| `evidence/gameplay/discussion_evidence.md` (the summariser is cheap to upgrade: about 4 calls a game against about 150) | L2-4, possible example of "spend where one error reaches every seat", paired with the Haiku/Sonnet summary tie |
| `Agents/llm_factory/accessors.py`, `catalog.py`, `pricing.py` | L2-4 table (today's slots); L2-1 price rows; code links |
| `evidence/tracing/report.md` (usage ledger, block 159) | Chapter 7 home. L2-1 uses the pricing-at-read rule in one sentence and links |
| `docs/agentic_ai_encountered_issues.md`, `frontend/docs/server_design_notes.md` §13 (stalls) | Chapter 7. L2-4 gives one row ("stalled turn: time counted as failure") and links |
| Map blocks 6–12, 74, 96, 100, 149, 159; 19 (dedup cascade); fine-tuning (reranker cross-encoder) | 6–11 → L2-1 to L2-3 as above; 12 → L2-2 gaps; 74 → L2-3; 96 → L2-4; 100 → Evaluation; 149 → chapter 3 + L2-4; 159 → chapter 7; 19 (built, switched off) and the untrained-into-production reranker → chapter 4 only |

---

## 6. Bridges

| Chapter | What crosses | Direction |
|---|---|---|
| 1 Game design | The node cache vs the prompt cache. Chapter 1, page 5 holds the three-row table (checkpoint, node cache, prompt cache) and the Level 3 page "The cache key that crossed games". Chapter 6 states the difference in one sentence on L1 §3 and one paragraph on L2-2, and links back; it does not retell the bug. Also chapter 1, page 4: the schema written as text and checked in code (validation side) | Ch 6 → Ch 1 |
| 3 Context engineering | The shared-prefix layout (structure proposal: "cost case lives in chapter 6"); thinking effort (correctness in chapter 3, cost and time in chapter 6); possibly the Haiku participation effect | Each to the other |
| 4 Memory | Extraction runs offline in batch. Chapter 4 owns what it writes and its quality (halo, seat-ID count). Chapter 6 owns why it runs offline, how batch and cache combine, and its cost. The memory L1 already says "an offline model reviews…"; `extraction_synthesis.md` moved the cache warm-up and cost material out to this chapter. Memory lookups' share of a game's cost (L2-1) | Ch 4 → Ch 6 for cost; Ch 6 → Ch 4 for content |
| 5 Evaluation | Model admission (can a candidate serve: probes, replays, real games, speed as a criterion) vs model choice by job (which job gets which model, and why). Stage fit: main home here (L2-4); Evaluation keeps it as an admission criterion (open question 2). Fair-comparison rules: costs from different runs and backends are not compared | Each to the other |
| 7 Production | The usage ledger's storage and collection limits; the 30 s request budget and the rescue model (time counted as failure); the traces that every cost and stage-fit figure is read from; the runtime fingerprint that labels configurations | Ch 6 → Ch 7 |
| 8 Frontend | The stage's beats and holds. A product fix for the waits (a longer pass hold, a visible decision beat) would be chapter 8's | Ch 6 → Ch 8, one line |

---

## 7. Claims to handle with care

**Headline cost and the estimate**
- **$0.21–0.26 a game, Haiku 5.5 (measured).**
  - Two ten-seat AI-only games, 2026-10-13. Current layout, unenforced schema, memory on (strategy
    points), seats at low thinking.
  - **[re-derived]** $0.2146 (197 calls) and $0.2550 (228 calls). Game 2 also made one $0.0045 call on
    Gemini 3.1 Flash-Lite, the then rescue model, so "every call on the seat model" (map) is off by one
    call.
  - Written only in `writeup/map.md`; no evidence report states it (open question 1).
  - Memory is **off** by default for players (`v8/decisions.md` §16), so this is not the default
    player's configuration (open question 5).
- **$0.08–0.26 a game, Haiku (measured).** 16 AI-only games, 2026-10-18, memory off, low thinking,
  voices on in 8 and off in 8; $2.48 in total (`persona_voice_games/README.md`). The map's hook table
  states it without "memory off". Game length varies about twofold.
- **Opus 5.5, $8–10 (estimate)** **[re-derived; matches the map]**.
  - $8.41 and $9.99; $7.09 and $7.92 without memory lookups.
  - Rates $4 input, $20 output, $0.20 cache read, $5 cache write per million tokens. These are not in
    `pricing.py`; cite the source (open question 4).
  - Output is about 52–55% of the estimate and would differ on Opus: thinking cannot be turned off, and
    the default effort is medium, where these seats ran Haiku at low.
  - The tokenizers differ.
  - It says nothing about play quality, and no Opus or Sonnet game has been played in the seats.
  - On a card or link preview, use a statement headline that carries "estimated".

**Other cost figures**
- **Sonnet seats, "about $2.30 a game against $0.12"** (`deduction/experiment_log.md` §2): an
  **estimate**; Sonnet never played seats. Keep off Level 1.
- **Haiku votes at medium thinking, "about $0.23 instead of $0.12"**: an **estimate** from about 2.7
  times the output on votes. The $0.12 base differs from the measured $0.21–0.26 (a different
  configuration). The decision is still pending. Keep off Level 1.
- **Luna $0.17, Flash-Lite $0.72, Gemini 3.5 Flash $2.72 (measured, 2026-10-10).**
  - Configuration: ten-seat AI-only, memory off, one model in every seat and as summariser, earlier
    layout. Flash-Lite's figure is from a different batch ("batch 4").
  - Flash's price came from an unchecked third-party listing.
  - These predate the write-pricing fix (`968bdad6`, 2026-10-13). The traces had priced OpenAI cache
    writes at zero (about 12% on one Luna game, `caching/experiment_log.md` §11), so Luna's figure may
    be understated.
  - Not comparable with the Haiku figures. Do not put them in one ranked list.
- **The Flash-Lite hook ("cheapest per token isn't cheapest per game"): drop it.** The price table
  refutes its premise. Per million tokens, Gemini 3.5 Flash-Lite is $0.30 input and $2.50 output;
  Haiku 5.5 and GPT-6 Luna are both $0.10 and $0.50 (`Agents/llm_factory/pricing.py`). Flash-Lite is not
  the cheapest per token, and the per-game figures come from different runs.

**Caching and extraction**
- **Luna −28% per call (measured).** Paired games, two per arm, same seeds and lineups, memory on,
  2026-10-13, cost per 1,000 calls ($0.89 → $0.64).
  - Haiku: $1.10 → $1.10 (unenforced) / $1.07 (enforced).
  - Two games per arm show Luna's direction clearly and cannot size Haiku's small differences.
- **Factual-error check.** 18 discussion turns, Luna only, judged by Haiku: no difference beyond noise.
  Only a regression of about ten points could have shown; there are no vote or night cases.
- **Haiku's participation.**
  - Openings 7–8% → 23–26%; free turns 20–35% → 53–54% (6 games against 4).
  - The position effect is inferred, not isolated. Play quality was not measured.
  - Haiku games got about 20–25% costlier per game because they contained more discussion.
- **Vertex caching figures.** 0 automatic reads; 15,001 of 15,005 tokens read from an explicit cache;
  extraction 5,520 of 5,648. These describe the tested models on Vertex only. Never compare quality
  across backends.
- **Prices.** Write premium 1.25 times input (Claude; OpenAI GPT-6), 2 times for Claude's one-hour
  cache; reads about a tenth; batch at half price (provider list prices).
- **Extraction runs.**
  - Gemini 3.8 Flash, online and cached: 19 games, 570 calls, $10.33 ($0.93 uncached input, $0.43
    cached, $8.97 output). These are components of one bill, not a cached-against-uncached comparison.
    About $0.55 a game with de-halo.
  - Sonnet 5.5, batched: 21 games, 630 calls, $19.99 against about $9.50 (about $0.95 a game). Output
    $7.39, retry writes $7.02, batch writes $3.01; about 91 replies failed validation; about 15% of
    batch requests wrote instead of reading.
  - The reason the initial replies failed is unknown; their errors are logged now.
  - The revised retry path has not been measured in a comparable run.
  - The earlier two-game check: estimated under $0.50, cost $2.69. A later two-game estimate: about
    $0.45 a game with the cache working.
  - Synthesis $4.02 direct → $1.51 batched: the prompts differed, so this shows the order of the saving
    only.

**Latency**
- **Stage fit (measured).**
  - Haiku 2.7–5.1% (252–471 s of 9,260 s), seven served ten-seat games with a human seat, since
    2026-10-11, all played by the owner while building.
  - The two ends of the range are two readings of the stage's backlog. Limits are provisional.
  - Per call: median 5.4 s, slowest 5% 10.8 s.
  - DeepSeek V4.1 Flash 0.1–0.3% (3 games). One Luna game was excluded (its trace could not be read).
- **Thinking-level time.** Two different measurements; never mix them in one sentence:
  - frozen-case replay, discussion turns: 6.7 s at low against 11.2 s at medium
    (`deduction/experiment_log.md` §2);
  - admission replay: 9.5 s against 13.7 s.

**Model choice**
- Budget-driven: "chosen within a fixed budget; checked to be good enough and affordable". Never "best
  model" or "optimal".
- Never name credits, plans or credit amounts ("the Gemini credits ran out", "the owner's Anthropic
  credits" stay off). Say the vendor in each slot follows the budget.
- Today's slots, confirmed in code 2026-10-29:
  - seats: Haiku 5.5 at low thinking, schema written in the prompt, no rescue on the catalogue row;
  - day summary: the seat model at medium thinking, 90 s budget;
  - extraction: Sonnet 5.5, batched;
  - dedup and bulk: Haiku.
- Seat-ID count: Haiku 74 of 146 (51%), Sonnet 18 of 1,405 (1.3%), 3.8 Flash 1 of 872. The rejected
  models ran on 2 games each.

**Model names and bookkeeping**
- Model names: keep Haiku (the site's model), Opus (the reference point) and Luna (where the layout
  result differs). Avoid a catalogue of names in explanatory prose.
- Bookkeeping that stays off:
  - the catalogue seed versus live-table mismatch;
  - gitignored raw traces and stage-fit caches;
  - the usage ledger's 37 of 68 rows with counts;
  - the cost summary that undercounted one-hour writes. This one may be told as caught and fixed, on
    L2-1 only.
  - Served-game extraction is not deployed and memory is off in served games: say "extraction runs
    offline on chosen games", nothing about deployment state.

---

## 8. Open questions for the owner

1. **Record the headline's numbers in evidence.** $0.215 and $0.255, the call-type split, the output
   share, the 16–21% lookup share and the Opus repricing are written today only in `writeup/map.md` or
   were re-derived here. Should a short dated entry go in `evidence/caching/experiment_log.md` (or a
   cost note) so the page's first number has an evidence source?
2. **Stage fit's home.** Evaluation's admission page already carries the full stage-fit table and the
   explanation of the waits on passes. Recommended: chapter 6 (L2-4) becomes the main home, and
   Evaluation trims to the criterion (5.5 s median, 11 s slowest 5%) plus a link. Or keep both. And
   should stage fit merge into model choice (four pages, recommended) or stand alone (five)?
3. **Settled 2026-10-30:** "When does the player have to wait?" *Was:* **Section 2 heading:** "Does a player wait for the AI?" (the hook; recommended) or "Why does each job
   use a different model?"
4. **Opus rates (now also: whether the estimate returns to Level 1, repriced on a matching basis).** The source and date of $4 / $20 / $0.20 / $5 per million tokens (not in
   `pricing.py`).
5. **Settled 2026-10-30: memory off leads.** *Was:* **Which Haiku figure leads.** Memory-on $0.21–0.26 (2 games; the map's worked hook), or memory-off
   $0.08–0.26 (16 games), which is the default player's configuration? Or both in one line, each
   labelled?
6. **A served game with a human seat.** No per-game cost has been computed for one. Is AI-only enough
   for the page, or should one served game be priced from its usage counts?
7. **Votes at medium thinking.** Still undecided. If adopted, the headline cost changes (estimated about
   $0.23 against $0.12 on the base used there). Decide before publishing, or state it as an open choice
   on L2-4?
8. **Where Haiku's participation effect lives.** An L2-2 subsection (recommended), a Level 3 page, or
   chapter 3 / chapter 1's conversation page?
9. **L1 §1 lead example.** The output share (recommended, simplest), or the lookup-share correction (a
   stronger caught-and-fixed story, but it needs memory lookups explained on Level 1)?
