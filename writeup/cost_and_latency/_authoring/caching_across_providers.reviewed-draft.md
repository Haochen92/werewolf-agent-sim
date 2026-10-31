# Making prompt caching work across providers

*Level 3 · [Cost and latency](cost_and_latency_codex.md) · first draft 2026-10-31, revised the same day after an editorial and a claims review; for the owner's review.*

## Page copy (draft)

Ten seats read the same rules and the same day's transcript on every discussion turn, vote and night action, so most of a game's input is repeated. The chapter page shows the layout that puts that shared part first so the provider can charge less for it. This page is about what each of four providers needed before it reused anything, how the reuse was measured and laid out, and what one change made for the cache did to the game. Most of the measurements are on the two seat models the layout was built for, Haiku on Claude and Luna on OpenAI; a game's AI seats all run on one model, chosen from the menu.

Caching turned out to be a contract with each provider, not a flag. Each stores something different, reads an entry only when a later request can find it, and two of them charge more to write an entry than to send the same input plainly. Getting reuse meant measuring before relying on it, laying the prompt out so every seat and every kind of call shares the transcript, placing marks a growing transcript can still find, and taking the enforced output schema out of the cache key. That last change, made for cost, also made Haiku report more reasoning tokens, and a replay of one Haiku turn found its decision better for it.

### What each provider stores, and what it costs to write

Seat A sends its turn; a minute later seat B sends a prompt with the same opening. Whether the provider reuses its work for A depends on what it stored from A's request and whether B's request can find it. What it stores is always a **prefix**, the beginning of a prompt, which is why shared content comes first; what counts as a storable prefix differs.

| Provider | What it stores | What the application has to do |
|---|---|---|
| DeepSeek | Each request's prompt, and any prefix two requests have shared | Order prompts so calls share as long a start as possible |
| OpenAI (GPT-5.6 and later) | Only prompts that end at a boundary: the end of the system message or of the latest user message, or a **breakpoint** the request places | Place breakpoints where the shared part ends; switch off the automatic write so changing content is not stored |
| Claude | Only prefixes that end at a **mark** the request places | Place marks where the shared part ends; budget for writes as well as reads |
| Gemini on Vertex | Only a named cache object the application creates; its automatic cache never fired in the tests | Create the object from the shared input, reference it from later calls, delete it afterwards. The game does this for post-game extraction, not for turns, so Gemini seats get no reuse |

*The integrations tested and the provider documentation read on 2026-10-13, not a catalogue of provider features.*

Writing is not free. Claude and OpenAI charge 1.25 times the input price for each token written to the cache and about a tenth of it for each token read back, so a prefix written and never read costs more than no cache at all. A cache pays only when the same prefix is read again, and the rest of the page is about making that happen.

### Measure before relying on it

The first design, in June, assumed the then game model's automatic cache (a Gemini model on Vertex) would reuse a repeated prompt. An identical 15,000-token prompt sent four times read zero cached tokens on every call, and only 2 of 600 recent production calls had recorded any hit; a cache object created explicitly from the same input read 15,001 of its 15,005 tokens. Those figures describe the tested models and backend; the rule they taught was general: a repeated prompt alone is not evidence of a saving. A model's **admission check** (the tests it passes before it can play) now measures caching on three real prompts: a seat's turn, that seat's next turn after another message, and a different seat's turn.

### Lay the prompt out so everyone shares the transcript

In the earlier layout each seat's role card sat in the system message, after the rules and before the transcript, so two seats' prompts diverged there, sharing about 800 tokens, and votes, night actions and memory lookups (the calls that search for lessons from earlier games) were each built as a prompt of their own, opening differently from a discussion turn.

The current layout opens every call with the rules, then the transcript, and puts everything that differs by seat or call type below the boundary. Two details decide what can share. The roster of the dead sits below the boundary because it changes at the day's vote, so night calls can still read the day's transcript. And a seat used to see its own held-back lines (lines the game withheld as repeats) marked as unpublished; now every seat sees the published lines only, so every copy of the transcript is identical.

The same three prompts, before and after, on the two models the layout was measured on:

| Share of the prompt read from cache | Same seat, next turn | Different seat |
|---|---:|---:|
| Haiku, earlier layout | 90% | 0% |
| Haiku, current layout | 77% | 71% |
| Luna, earlier layout | 57% | 29% |
| Luna, current layout | 75% | 69% |

*One probe sequence per row; the different seat's prompt is a discussion turn with the same schema, enforced in every row. Haiku's rows use cache marks; Luna's earlier row is its automatic cache and its current row explicit breakpoints (next section), so Luna's rows change two things at once.*

In the earlier layout Haiku's marks sat at the end of a system message that contained the role card, so a different seat matched nothing; the probe records count cached tokens without identifying which text was reused, so Luna's 29% is not broken down. Now a different seat reads most of the prompt. A seat's own next turn reads a little less on Haiku, because its role card now follows the transcript and is sent again every turn. These are cached-token shares on three requests, not a whole-game discount.

### Marks a growing transcript can still find

Claude stores a prefix only where the request places a mark. For each mark, Claude looks for an entry ending exactly there; if none exists, it walks back a limited number of **content blocks**, the pieces a message is sent in, for an entry ending at an earlier block boundary. So the transcript is sent one block per line, with a mark on the last line and another on the system message. As one block, a longer transcript would hold no boundary where the earlier entry ended.

```text
Turn 1:  [system ✓] [line 1] [line 2] [line 3 ✓] [role card, instructions …]
         no entry yet → store "system … line 3"            (written at 1.25× input)

Turn 2:  [system ✓] [line 1] [line 2] [line 3] [line 4] [line 5 ✓] [role card, instructions …]
         no entry at line 5; walk back: line 4 no, line 3 yes
         → read "system … line 3" (about 0.1× input), process lines 4–5,
           store "system … line 5"                         (only lines 4–5 written)
```

Because the system message now holds only the rules, turn 2 can be any seat's turn and still read the entry; that is the 71% in the table above. A vote can read it too once its schema is out of the cache key (next section). The limit is the walk-back's reach, counted in blocks rather than time: if many lines arrive between two calls, the old boundary can be too far back to find, and how often that happens in games is unmeasured.

OpenAI stores an entry at the end of the system message and at the end of the latest user message unless the request places breakpoints. Each turn's message ends with its changing instructions, so in the earlier layout's games Luna had reused only the system message: exactly 4,582 cached tokens on each of seven discussion calls while the transcript grew, with most of its input written and never read. OpenAI does not walk back, so a breakpoint now goes on the system message and on every transcript line, and a later call finds an earlier call's last line among its own; a three-call probe confirmed both reuse paths, with the private part never written.

### Taking the schema out of the cache key

Every call returns structured output checked against a **schema**, a description of the fields the reply must contain, and the schema differs by call type. For a vote or night action it also lists the **legal targets**: the players this seat may vote for or act on tonight. That list differs for every seat, since a seat cannot target itself, and changes after every death. A rule of mine keeps the targets enforced by code: whatever the prompt says, a reply naming a player outside the list is rejected, and the list is never left to a sentence in the prompt.

When the provider enforces the schema, the schema behaves like the start of the prompt: on Claude it is part of what the cache matches, on OpenAI it is rendered before the messages. Two requests with identical text and different schemas share nothing, so each seat's vote had its own cache, and votes, night actions and discussion turns could not read one another's copy of the transcript.

The alternative keeps the rule and moves the schema out of the key: write the same per-seat schema, targets included, as text after the shared part, and validate the reply in code against it, so an illegal target still fails. The question was whether unenforced replies would fail often enough for retries to slow the live game.

| | Schema enforced by the provider | Schema sent as text, checked in code |
|---|---|---|
| What shares a cache | Only calls with an identical schema: each seat's vote is its own cache | Every call at the same moment, whatever its type |
| Trial replies that failed validation | 0 of 170 on Haiku; 3 of 170 on Luna, each an empty list of reads | 1 of about 400 on each of Luna and Haiku |

The trial said retries would be rare, and Luna and Haiku switched to the text schema in mid-October, for caching. Real games then broke the schema more often than the trial had suggested: 74 of 3,118 seat decisions in twenty Haiku games, about one in forty. In those games a failed reply was simply asked again as text, and six turns failed twice. Since then a reply that breaks the schema is asked again once with the schema enforced, on the same model; that one call reads no cache and adds one call's wait to the turn, and how often it fires in games has not been measured, so the cost in waiting is still open.

### What it did to Haiku's reported reasoning

The text schema also changed how much Haiku thinks before it answers, and that is billed: **reasoning tokens** are output the model spends thinking before its reply. In the paired games below, Haiku's reasoning rose about 1.5 times on discussion turns and several times on votes. What the extra reasoning bought showed up in a replay. One recorded turn had been replayed with the schema enforced, and Haiku had taken in a conclusion without acting on it; two weeks later, the same turn replayed with the schema sent as text gave a different answer.

The turn is the **healer turn**, one recorded turn replayed many times: the healer had been blocked overnight, one player had admitted visiting it, and only the Chanteuse role blocks, so a good turn names that player as the Chanteuse in its **read**, the one-line assessment of another player each turn asks for. The turn came from testing the **deduction engine** (chapter 3), which works out selected conclusions from a seat's own facts and writes them into its prompt; the engine is on in every row below, so the table compares only the output mode. Haiku at its live thinking setting (low), 10 samples per row:

| Output mode | Read named the Chanteuse | Reasoning tokens |
|---|---:|---|
| Schema enforced (the retired mode) | 2 of 10 | None reported in 4 of 10 samples; at most 1,312 |
| Schema sent as text (the live mode) | 8 of 10 | 409–1,233, every sample |
| Schema as text, high thinking | 10 of 10 | 2,933–5,042 |

A later re-run of 16 recorded vote cases in the live mode pointed the same way (62% of votes on an evil player at the low setting, against 41% in the enforced run), but it came two weeks after that run and rendered its prompts with the code of its day, so unlike the healer replay it does not isolate the output mode. On the healer turn, the change made for cost helped the replayed decision, and the extra reasoning is paid for in output.

This is one model's evidence, on one turn and a vote re-run. Zero reported reasoning tokens do not show that no reasoning happened; other low-cost models had also reported none under enforced output, but none was compared against the schema sent as text. The practical lesson is that a replay must pin the output mode the game runs: the engine's results on chapter 3's [deduction engine page](../context_engineering/deduction_engine/deduction_engine.md) had been measured in the retired mode.

### What the paired games showed, and what remains

Two games per arm on the same two deals, memory on, compared the earlier layout with the enforced schema against the current layout with the text schema, putting the input saving and the extra reasoning in one bill. On Luna the cost per call fell 28%, from $0.89 to $0.64 per thousand calls, as votes and night actions went from reading no cache to reading about 60% of their input. On Haiku the cost per call stayed at $1.10: with the text schema it reasoned about 1.5 times as much on discussion turns and several times as much on votes, which used up the input saving. Two games per arm show Luna's direction clearly and cannot size Haiku's small differences. Haiku's higher whole-game cost, from more participation, is the chapter page's finding; this page counts cost per call.

Still open: the other listed models (DeepSeek, Gemini, and GLM served through OpenRouter) passed the admission probe in the earlier layout and run the current one, but their reuse and play were never measured under it, and the long-gap miss on Claude and the enforced retry's frequency are unmeasured. The only check of the layout on message quality replayed 18 recorded Luna discussion turns and had a judge mark replies that misstate the game; it found no difference beyond noise, and could only have detected a change of about ten percentage points in the share marked wrong. Whether the layout changed play beyond factual errors is not known, which is why the chapter page calls an improvement in play not established.

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
- Revision 2026-10-31 after the reviews: the 9,258 of 10,206 check (log §9, 2026-10-12) ran under the
  earlier layout and is kept here, not in the copy; the healer table's "spoke" column (5/10, 7/10, 8/10)
  moved here; "one entry per model" (report §2) moved here. The vote re-run (§9) and the enforced run
  (§2, 2026-10-16) rendered prompts from stored game state with the code of each day
  (`vote_cases.jsonl` holds `state`, not a rendered prompt; `Agents/config/run.py`
  DEFAULT_DEDUCTION_MODE = "full"; the engine's first commit 9c7f37b6 is dated 2026-10-16), so the copy
  says the two runs do not isolate the output mode. "A game's AI seats all run on one model chosen from
  the menu": `server/schemas/requests.py` NewSoloGame.model ("from the model menu only"). Gemini seats
  get no reuse: report §1 and §3.1 (cache objects serve extraction). OpenAI's system-message boundary:
  log §12 cause 1 ("the end of the opening developer block"). Haiku's 0% for a different seat in the
  earlier layout: the system message then held the role card (report §3.2) and carried a mark (§3.3).
- Third editorial round: Luna's 29% different-seat share in the earlier layout is not explained by the
  sources (report §4.2: the records "do not identify exactly which text was reused"), so the copy says
  so rather than deriving a cause. The rule on legal targets: log §12 ("Legal targets stay limited by
  code, in the schema, and never move into the prompt as text") and report §3.5; in the text mode the
  same per-seat schema, targets included, is appended after the cache boundary and the reply is
  validated against it. Trial units: enforced 170/170 Haiku, 167/170 Luna (empty reads lists);
  unenforced 1 in 412 Haiku, 1 in 388 Luna (log §12). The vote re-run's medium figures (77% against
  61%) and "valid samples" (157 and 158 of 160) stay here. GLM via OpenRouter: report §4.2.
- Kept off the page per the outline and the chapter's handle-with-care list: the extraction overrun and
  the batch figures; the node cache (chapter 1; no page exists yet); credits, plans and who pays; the
  catalogue seed; the larger June model's 4,000-token blocks; the tell detector.
-->
