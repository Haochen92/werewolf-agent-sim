# Making prompt caching work across providers

*Level 3 · [Cost and latency](cost_and_latency_codex.md) · first draft 2026-10-31*

## Page copy (draft)

Ten seats read the same rules and the same day's transcript on every discussion turn, vote and night action, so most of a game's input is repeated. Prompt caching charges less for input the provider has already processed, and the chapter page shows the layout that puts the shared part first. This page is about what it took to make four providers actually reuse it, and what one change made for the cache did to the game.

Caching turned out to be a contract with each provider, not a flag. Each one stores something different, charges more to write a cache entry than to send the same input plainly, and reads an entry only when a later request can find it. Getting reuse meant measuring before relying on it, laying the prompt out so every seat and every kind of call shares the transcript, placing marks a growing transcript can still find, and taking the enforced output schema out of the cache key. That last change, made for cost, also let the game's model reason more.

### What each provider stores, and what it costs to write

Seat A sends its turn. A minute later seat B sends a prompt with the same opening: the rules and the transcript so far. Whether the provider reuses the work it did for A depends on two things: what it stored from A's request, and whether B's request can find it. The stored thing is always a **prefix**, the beginning of a prompt, which is why shared content has to come first. What counts as a storable prefix differs.

| Provider | What it stores | What the application has to do |
|---|---|---|
| DeepSeek | Each request's prompt, and any prefix two requests have shared | Order prompts so calls share as long a start as possible |
| OpenAI (GPT-5.6 and later) | Only prompts that end at a boundary: the end of the latest user message, or a **breakpoint** the request places | Place breakpoints where the shared part ends; switch off the automatic write so changing content is not stored |
| Claude | Only prefixes that end at a **mark** the request places | Place marks where the shared part ends; budget for writes as well as reads |
| Gemini on Vertex | Only a named cache object the application creates | Create the object from the shared input, reference it from later calls, delete it afterwards |

*The integrations tested and the provider documentation read on 2026-10-13, not a catalogue of provider features.*

Writing is not free. Claude and OpenAI charge 1.25 times the input price for each token written to the cache and about a tenth of it for each token read back, so a prefix that is written and never read costs more than no cache at all. An entry also belongs to one model: the same prompt on two models is two caches. A cache pays only when the same prefix is read again, which is the question the rest of the page answers.

### Measure before relying on it

The first design, in June, assumed the then game model's automatic cache would reuse a repeated prompt. A probe sent an identical 15,000-token prompt four times; every call read zero cached tokens, and only 2 of 600 recent production calls had recorded any hit. A cache object created explicitly from the same input did work: one request read 15,001 of its 15,005 tokens from it. Those figures describe the tested models and backend, but the rule they taught was general: a repeated prompt alone was not evidence of a saving.

So before a model joins the game, its **admission check** (the tests a model passes before it can play) now measures caching on three real prompts: a seat's turn, that seat's next turn after another message, and a different seat's turn. The next section uses those three prompts to show what the layout changed.

### Lay the prompt out so everyone shares the transcript

In the earlier layout each seat's role card followed the rules, before the transcript. Two seats' prompts diverged there, sharing about 800 tokens, and votes, night actions and memory lookups each started from a prompt of their own. Only a seat's own next turn could reuse much, and only on providers whose cache could find it. On the three admission prompts, the providers with an automatic cache reused a seat's next turn far more than a neighbour's, 57–79% against 29–36% on the two that reused most; three reused little of either, and the Gemini model nothing.

The current layout opens every call with what all seats share: the rules alone in the system message, then earlier days' summaries and today's transcript, ending on a separator line. Below that boundary come the roster of the dead and the roles remaining, the role card, the call's instructions, private results, the turn's brief and any retrieved lessons. The dead list sits below the boundary because it changes at the day's vote, which lets night calls still read the day's transcript. One more change made every seat's copy of the transcript identical: a seat used to see its own held-back lines marked as unpublished, and now sees the published lines only.

The same three prompts, measured before and after on the two models that had the most to gain:

| Share of the prompt read from cache | Same seat, next turn | Different seat |
|---|---:|---:|
| Haiku, earlier layout | 90% | 0% |
| Haiku, current layout | 77% | 71% |
| Luna, earlier layout | 57% | 29% |
| Luna, current layout | 75% | 69% |

*One probe sequence per row. Haiku's rows use cache marks; Luna's earlier row is its automatic cache and its current row uses explicit breakpoints (next section).*

A different seat now reads most of the prompt. A seat's own next turn reads a little less on Haiku than before, because its role card now follows the transcript and is sent again every turn. These shares count cached tokens on three requests; they do not by themselves give a whole-game discount.

### Marks a growing transcript can still find

Claude stores a prefix only where the request places a mark, and the mark is not stored anywhere by the application: the code that builds each request places it again. For each mark, Claude looks for an entry that ends exactly there; if none exists, it walks back a limited distance, one **content block** at a time, for an entry ending at an earlier block boundary. The transcript is therefore sent one block per line, with a mark on the last line and another on the system message. As one block, a longer transcript would contain no boundary where the earlier entry ended.

```text
Turn 1:  [system ✓] [line 1] [line 2] [line 3 ✓] [role, brief …]
         no entry yet → store "system … line 3"            (written at 1.25× input)

Turn 2:  [system ✓] [line 1] [line 2] [line 3] [line 4] [line 5 ✓] [role, brief …]
         no entry at line 5; walk back: line 4 no, line 3 yes
         → read "system … line 3" (about 0.1× input), process lines 4–5,
           store "system … line 5"                         (only lines 4–5 written)
```

Because the system message holds only the rules, turn 2 can be any seat's turn, or a vote, and still read the entry. In one check a seat's next turn read 9,258 of 10,206 input tokens from cache. The limit is the walk-back's reach: a long gap between two calls can leave the old boundary too far back to find, and how often that happens in games has not been measured.

OpenAI stores an entry only at the end of the latest user message unless the request places breakpoints, and each turn's message ends with the changing brief, so before this change Luna reused a flat amount per call: seven discussion calls under one system message each read exactly 4,582 cached tokens while the transcript grew, and most of Luna's input was written and never read. With a breakpoint on the system message and on each transcript line, a seat's next turn read 2,561 of 2,678 tokens, and the private part was never written.

### Taking the schema out of the cache key

A vote or night action does not return free text. Its reply is checked against a **schema**, a description of the fields the reply must contain, and the schema lists the **legal targets**: the players this seat may vote for or act on tonight. That list differs for every seat, because a seat cannot target itself, and it changes after every death. A rule of mine keeps those targets enforced by code through the schema, never written into the prompt as a list the model could misread.

When the provider enforces the schema, the schema behaves like the start of the prompt: on Claude it is part of what the cache matches, and on OpenAI it is rendered before the messages. Two requests with identical text and different schemas therefore share nothing. With per-seat target lists, each seat's vote had its own cache, and votes, night actions and discussion turns could not read one another's copy of the transcript.

The alternative keeps the rule and moves the schema out of the key: write the schema as text after the shared part, and validate the reply in code against the same per-seat schema, so an illegal target still fails. The question was whether replies written without enforcement would fail often enough to slow the live game with retries.

| | Schema enforced by the provider | Schema sent as text, checked in code |
|---|---|---|
| What shares a cache | Only calls with an identical schema: each seat's vote is its own cache | Every call at the same moment, whatever its type |
| Replies that failed | The provider guarantees the shape | 1 in about 400 trial calls on each of Luna and Haiku; about one seat decision in forty in twenty real games |

The trial replayed 17 schemas and 24 real turns per model. Real games broke the schema more often: 74 of 3,118 seat decisions in twenty Haiku games, with a read keyed by a player's name, a verdict word outside the allowed set, or cut-off JSON. So a reply that breaks the schema is now asked again once with the schema enforced, on the same model; that one call reads no cache. How often the retry fires has not been measured. Luna and Haiku switched to the text schema in mid-October, for caching.

### What it did to Haiku's reasoning

Two weeks later a replay disagreed with live play. The **healer turn** is one recorded turn replayed many times, chapter 3's example for the deduction engine: the healer had been blocked overnight, one player had admitted visiting it, and only the Chanteuse role blocks, so a good turn names that player as the Chanteuse in its **read**, the one-line assessment of another player each turn asks for. The engine's effect on that turn had been measured in a replay pinned to the enforced schema. Replaying it in both modes, with the engine on and Haiku at its live thinking setting:

| Haiku, engine on, 10 samples each | Read named the Chanteuse | Spoke | Reasoning tokens |
|---|---:|---:|---|
| Schema enforced (the retired mode) | 2 of 10 | 5 of 10 | None reported in 4 of 10 samples; at most 1,312 |
| Schema sent as text (the live mode) | 8 of 10 | 7 of 10 | 409–1,233, every sample |
| Schema as text, high thinking | 10 of 10 | 8 of 10 | 2,933–5,042 |

**Reasoning tokens** are the billed output a model spends thinking before its reply. With the schema enforced, Haiku reported none in 4 of 10 samples; sent as text, every sample used them, and the read went from 2 to 8 of 10. The same held for votes: 16 recorded vote cases from two games, replayed 10 times each in the live mode, named the actual threat in 62% of valid samples at the low thinking setting against 41% under the enforced schema, and rose at the medium setting too. The change made for cost helped the replayed decisions, and the extra reasoning is paid for in output.

What this shows is bounded. It is one model's evidence, on one turn and 16 cases; zero reported reasoning tokens do not show that no reasoning happened; and other low-cost models had shown the same direction in earlier checks (no reasoning tokens reported with structured output, or thinking switched off by a forced tool call), none of them a like-for-like comparison. The practical lesson is that a replay must pin the output mode the game runs: the engine's uptake results on chapter 3's [deduction engine page](../context_engineering/deduction_engine/deduction_engine.md) had been measured in the retired mode.

### What the paired games showed, and what remains

Two games per arm on the same two deals, memory on, put the input saving and the extra reasoning in one bill. On Luna the layout with the text schema cut the cost per call by 28%, from $0.89 to $0.64 per thousand calls, as votes and night actions went from reading no cache to reading about 60% of their input. On Haiku the cost per call stayed at $1.10: with the text schema it reasoned about 1.5 times as much on discussion turns and several times as much on votes, which used up the input saving. Two games per arm show Luna's direction clearly and cannot size Haiku's small differences.

What remains open: the seats on DeepSeek, GLM and Gemini run the layout but were never measured under it; the long-gap miss on Claude and the enforced retry's frequency are unmeasured; and the only quality check, 18 Luna discussion turns on a factual-error bench, found no difference beyond noise where only a regression of about ten points would have shown. Whether the layout changed play beyond factual errors was not measured.

<!--
Sources and supporting notes, 2026-10-31 (first draft):
- Opening and §1: evidence/caching/report.md §2 (prefix; the four-row table; "tested integrations and
  the provider documentation read on 2026-10-13"; write at 1.25× input and reads about a tenth on
  Claude and OpenAI; Gemini bills a cache object's input once at full price, omitted from the page;
  entries belong to one model).
- §2: caching/experiment_log.md §3 (gemini-3.1-flash-lite on Vertex, 15k-token prompt four times, 0
  cached tokens; 2 of 600 production calls, 0.4% of input tokens; a 20-second-wait attempt also 0);
  report §4.1 (explicit cache 15,001 of 15,005; the 4,096-token explicit-cache minimum; extraction
  5,520 of 5,648; the October probe on gemini-3.5-flash-lite also 0 up to about 8,192 tokens; "the
  tested models and backend, not every Gemini model"). Admission caching step: log §8 (commit
  a061474b), report §4.2. Evaluation's page: writeup/evaluation/model_admission/model_admission.md.
- §3: report §3.2 (earlier layout: rules then role card in the system message; the current layout; the
  dead list below the boundary; held-back drafts no longer shown; the seat's own next turn reuses a
  little less; tag prompt-layout-baseline). "About 800 tokens" and "about 84%" between one seat's
  turns: log §8, from working notes, no data file kept. Probe table: report §4.2 (Claude 90/0 on
  2026-10-11 with marks, uncommitted path per log §8; Qwen 79/36; Luna 57/29; GLM 10/13; DeepSeek 8/11;
  MiniMax 3/3; Gemini 3.5 Flash-Lite 0/0; current layout Haiku 77/71 and Luna 75/69, enforced schema,
  2026-10-13; "one probe sequence per row"; "count cached tokens; do not identify which text").
  Smoke check 53–71% across variants: log §13. The DeepSeek caveat (short probe ≠ whole-game discount):
  report §4.2.
- §4: report §3.3 and log §9 (marks on the system message and the transcript's last line; one block per
  line; the walk-back is at most 20 content blocks; Claude allows four marks, two used; 9,258 of
  10,206; the long-gap miss unmeasured). The diagram is the report's §3.3 block, copied. OpenAI: log
  §12 (4,582 cached tokens on seven discussion calls; three quarters of Luna's input written and never
  read, report §3.4) and log §13 / report §3.4 (explicit-only mode, prompt_cache_breakpoint on text
  parts; OpenAI matches the latest 80 breakpoints and writes the latest four; probe: 2,561 of 2,678 on
  the seat's next turn, 2,648 of 2,674 for seat B, private part never written; the first call reported
  0 written, unexplained).
- §5: report §2 ("an enforced output schema behaves like the start of the prompt"), §3.5 and log §12
  (owner's rule on legal targets; output_schema_with_legal_targets; trial 17 schemas × 10 samples per
  mode plus 8 real turns × 3 variants per model; 1 in 388 Luna calls, 1 in 412 Haiku calls; Luna's
  three enforced misses were empty reads lists, a content check; the enforced schema added about 540
  hidden input tokens and 0.8 s on Haiku, omitted). Field order (15/24 → 24/24 after reads-first): log
  §12, told on writeup/context_engineering/structured_assessments/turn_request.md, off this page. Real games:
  log §16 and report §3.5 (74 of 3,118 seat decisions, memory demo run 2026-10-14; six turns to the
  rescue model; the lookup's situation call five times; 426 copied verdicts, fixed the same day; the
  enforced retry 7f508c4d / 68cef8b0, "not cached, its schema is in the key"; frequency not measured).
  "Mid-October, for caching": catalog.py LIVE_EDITS_SINCE_MIGRATION (json_mode for Luna and Haiku,
  "2026-10-14, caching") and the two models' notes; report §3.5 "owner's decision". The seed/live-table
  mismatch (report §3.5 "Where the mode is set") stays off per the chapter's list.
- §6: gameplay/deduction/experiment_log.md §8 Result 1 (case 9b3219e5dc1eb831, R1's turn after
  player_7's admission, memory off, 10 samples per arm, game path, Haiku at low; json_schema 2/10 read,
  5/10 spoke, 1/10 tied the block, reasoning 0 in 4 samples and at most 1,312; json_mode 8/10, 7/10,
  about 5/10, 409–1,233 every sample; json_mode high 10/10, 8/10, 3–5/10, 2,933–5,042; "zero reasoning
  tokens do not show that no reasoning happened"; 0 of 20 fact-check violations in live-mode samples).
  Other low-cost models: §8 "What it shows" (Gemini 3.5 Flash-Lite 0 reasoning tokens with structured
  output at minimal and low; a forced tool call turned thinking off for DeepSeek V4 Pro and Haiku; none
  a like-for-like text-format comparison). Votes: §9 (16 cases as played, 10 samples each; json_schema
  65/160 = 41% low, 98/160 = 61% medium; json_mode 97/157 = 62% low, 122/158 = 77% medium; 203 and 208
  valid of 210; output about 1,440 tokens a vote at low and 2,120 at medium). "Two weeks later":
  switch 2026-10-14, replays 2026-10-30. The engine measured in the enforced mode: deduction log §4
  and §8 Setup; writeup/context_engineering/deduction_engine/deduction_engine.md. "Chapter 3" = the
  context-engineering chapter. Subagent harness rows (§8 Result 3) off the page.
- §7: report §4.3 and log §13 (two games per arm, same two seeds and line-ups, memory on; Luna $0.89 →
  $0.64 per 1,000 calls, −28%, input per call −36%, output −10%; votes 0% → 64% read, night 0% → 60%;
  Haiku $1.10 → $1.10 unenforced, $1.07 enforced; reasoning about 1.5× on discussion and 3–5× on votes;
  "cannot size Haiku's small differences"; Haiku's games about 88 discussion turns against 65 — the
  participation story stays on the Level 1). Bench: report §4.4 (Luna, 18 turns × 5 samples, judged by
  Haiku; 11/90, 13/90, 10/90; "no configuration differed beyond noise"; only about ten points would have
  shown; discussion turns only). Open items: report §6 (DeepSeek, GLM and the Gemini players use the
  layout, "on cost they can only gain or stay level", play not tested; play quality beyond factual
  errors; the bench's missing vote and night cases).
- Kept off the page per the outline and the chapter's handle-with-care list: the extraction overrun and
  the batch figures; the node cache (chapter 1; no page exists yet); credits, plans and who pays; the
  catalogue seed; the larger June model's 4,000-token blocks; the tell detector.
-->
