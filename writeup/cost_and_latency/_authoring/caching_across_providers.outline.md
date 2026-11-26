# Outline: Making prompt caching work across providers (Level 3)

Page: `writeup/cost_and_latency/caching_across_providers.md` · Level 3, directly under the Level 1's
"Reuse shared input without losing useful behaviour" (the chapter has no Level 2; the drafter adds the
Explore link at the end of that subsection) · Proposed 2026-10-31; revised the same day after a cold
review (the schema section split into the decision and its consequence; the October probes moved to the
layout section as its before/after; the model named; the reasoning effect stated as help on the replayed
cases at the price of the input saving; provider-manual detail cut) · Length guide 1,000–1,300 words.

**Reader's question.** The chapter page says shared input goes first and reuse is verified in usage
records. What did it take to get four providers to reuse it, and what did a change made for the cache do
to the game?

**Central answer.** Caching is a per-provider contract, not a flag. Each provider stores something
different, charges more to write an entry than to send the input, and reads only when a later request
can find the entry. Getting reuse meant measuring before relying on it, laying the prompt out so every
seat and every kind of call shares the day's transcript, placing marks a growing transcript can still
find, and taking the enforced output schema out of the cache key, since it made every vote its own cache.
That last change, made for cost, let Haiku reason more: a replay pinned to the old mode showed two weeks
later that the enforced schema had been suppressing its reasoning, and that the text schema improved the
replayed decisions. The same extra reasoning is why the layout cut Luna's cost per call by 28% and left
Haiku's level.

**What the parent already tells.** What caching discounts (repeated input, never output); the layout
with the boundary; that reuse must be verified in usage records and Gemini's automatic cache returned no
reads; the paired-game result (28% on Luna, level on Haiku with more reasoning); Haiku's participation
effect and the owner's ruling to keep it. This page adds the per-provider mechanics, the probes, the
boundary placement on a growing transcript, the schema decision and what it did to reasoning.

**Shape.** Mechanism first, then the decisions in the order they were forced, then the consequence, then
the close. Sections 5 and 6 are the page's featured decision and its consequence, where cost and
correctness met.

| § | Section (working heading) | What the reader learns, and how | Carried by | Stays off |
|---|---|---|---|---|
| 0 | Opening | Why it mattered (ten seats re-read the same rules and transcript many times a day); the contract framing in two sentences; the question | Two short paragraphs | Cost totals (Level 1) |
| 1 | What each provider stores, and what it costs to write | Open concretely: seat B sends the same opening as seat A a minute later; whether the provider reuses A's work depends on what it stored and whether B's request can find it. Then the four-row table in plain words; writes at 1.25 times the input price and reads at about a tenth, so a prefix written and never read costs more than no cache; a cache entry belongs to one model; dated to the integrations tested on 2026-10-13 | The provider table | Cross-provider ranking (behaviour, not a league table) |
| 2 | Measure before relying on it | The principle and the June result in two or three sentences: the automatic cache on the then game model read nothing from a 15,000-token prompt sent four times, and 2 of 600 production calls had any hit; an explicit cache object did read almost all of its input. "A repeated prompt alone was not evidence of a saving." The admission check gained a caching step with three real prompts (a seat's turn, its next turn, another seat's turn), which §3 uses | Two or three sentences | The larger model's 4,000-token blocks; the tell detector; the extraction cache object beyond one clause |
| 3 | Lay the prompt out so everyone shares the transcript | The earlier layout diverged at the role card, so two seats shared about 800 tokens; the new layout and what sits below the boundary and why (the dead list changes at the vote); one sentence that two changes made every seat's copy of the transcript identical (glossed in a clause, or left at that). Then the before/after measured by the same three prompts: in the earlier layout, automatic caches reused a seat's own next turn far more than a neighbour's (57–79% against 29–36% on the two best), several reused little, Gemini nothing; in the new layout a different seat reuses most of the prompt (0% → 71% on Claude, 29% → 69% on Luna) and a seat's own next turn a little less (90% → 77%) | A compressed before/after table: same seat / different seat, earlier layout / current layout, for Claude and Luna | Every model's row; what the layout did to what the player reads first (chapter 3, one clause and a link); the participation story (Level 1) |
| 4 | Marks a growing transcript can still find | Claude stores only at a mark the request places and looks back a limited distance for an earlier entry, so the transcript is sent one block per line with a mark on the last; the two-turn walk-back; 9,258 of 10,206 tokens read on a seat's next turn; a long gap between calls can put the old boundary out of reach, unmeasured. OpenAI in two sentences: it stores only at the end of the latest message unless breakpoints are placed, so a growing transcript reused a flat amount and most input was written and never read; with a breakpoint per line a seat's next turn read 2,561 of 2,678 | The two-turn block diagram from the report | The 20-block, 80-breakpoint and four-written figures; SDK and field names (source note) |
| 5 | Taking the schema out of the cache key | Legal targets live in the vote's schema, never in the prompt as a list (owner's rule), so with the schema enforced each seat's vote had its own cache and votes and night actions shared nothing. The alternative: the schema written as text after the shared part and the reply validated in code against the same per-seat schema. The trial: one validation failure in about 400 calls on each model. Real games broke the schema about one decision in forty, so a reply that breaks it is asked again with the schema enforced, and that one call reads no cache. Switched in mid-October for caching | One paragraph and one short table (enforced against text: what shares a cache, failure rate) | The extraction overrun; the field-order finding (chapter 3, page 3); the catalogue row; the retry's frequency (unmeasured, one clause) |
| 6 | What it did to Haiku's reasoning | Found two weeks later: a replay of the deduction engine's healer turn, pinned to the enforced schema, disagreed with live play. With the schema enforced Haiku reported no reasoning tokens in 4 of 10 samples; sent as text, every sample used them; on that turn its read went from 2 to 8 of 10 with the engine's lines, and 16 replayed vote cases rose at both thinking levels (41% → 62% right at the low setting). So the change made for cost helped the replayed decisions, and the extra reasoning is paid for in output. Scope: one model; one turn and 16 cases; zero reported tokens do not show no reasoning happened; other low-cost models showed the same direction without a like-for-like test. The lesson: a replay must pin the mode the game runs, since the engine's uptake results (chapter 3, page 4) had been measured in the retired mode | A three-row table: enforced / text / text at a high setting, with read, spoke and reasoning tokens | Chapter 3's account of the engine; the thinking-level study beyond the live-mode row |
| 7 | What the paired games showed, and what remains | Two games per arm: 28% less per call on Luna; level on Haiku, because its extra reasoning (§6) used up the input saving. Remaining: three seat models never measured under the layout; the long-gap miss on Claude; the enforced retry's frequency; whether the layout changed play beyond factual errors (one clause, if §4.4 of the report supports it; otherwise omit) | Three or four sentences | The bench, unless glossed; dollar figures per game (Level 1); the node cache (chapter 1's Level 3) |

**Cut list if long** (in order): §2 to two sentences; §4's OpenAI sentences to one; §5's table to prose;
§7's remaining-questions list to one sentence.

**Terms to gloss on first use.** "prefix"; "cache write" and "cache read"; "mark" and "breakpoint" (a
provider's name for where an entry may end); "content block"; "enforced schema" against "schema sent as
text"; "legal targets"; "admission check" (the tests a model passes before it can play); "reasoning
tokens"; "the healer turn" (one recorded turn replayed many times, chapter 3's example).

**Handle with care.** Provider names are unavoidable here and model names follow the Level 1's usage;
never compare scores across backends; the provider table describes tested integrations on a date, not a
catalogue; the June figures are the tested models and backend, not Gemini in general; the paired games
are two per arm; "a change made for cost" states the recorded motive (owner's decision, mid-October);
the reasoning effect is one model's evidence and "helped" means the replayed decisions, not whole games;
"reported no reasoning tokens", never "did no reasoning"; the enforced retry's frequency is unmeasured;
no claim that the layout improved play.

**Verification needed before publication.** The probe rows against the admission results folder; the
two-turn diagram against the Claude request builder; §4.4's bench result, if used; the catalogue switch
date; the live-mode vote figures in the deduction log §9; the provider rules against the documentation as
read on 2026-10-13 (dated in the source note).

**Bridges.** Parent: the Level 1's caching subsection (add the Explore link). Chapter 3 page 3 for the
field order and page 4 for the engine results measured in the old mode; chapter 1's Level 3 for the node
cache; Evaluation's model-admission page for the admission check; the evidence report for the batch
overrun.

**Sources.** `evidence/caching/report.md` §2, §3.2–3.5, §4.1–4.4, §6; `evidence/caching/experiment_log.md`
§3, §8, §9, §12, §13, §16; `evidence/gameplay/deduction/experiment_log.md` §8–9; `Agents/llm_factory/catalog.py`
notes (source note only).
