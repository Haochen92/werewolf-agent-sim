# Explanation prototype: Making prompt caching work across providers

Page: `writeup/cost_and_latency/caching_across_providers.md` · Level 3 · Purpose: mechanism walkthrough
with one consequence told as an investigation (how four providers were made to reuse shared input, and
what the change made for the cache did to the game) · Date: 2026-10-31
Checkpoint: outline approved in conversation 2026-10-31 (cold-reviewed outline at
`caching_across_providers.outline.md`); drafting authorised without another stop.

Authoring material, not page copy. The cold reviewer does not see it. The outline holds the section
table, cut list, stays-off column, terms to gloss and handle-with-care list; this brief does not repeat
them.

## Reader and explanation

- **Reader outcome:** the reader can say why "turn caching on" was not a step: each provider stores a
  different thing and reads it under its own rule, so reuse had to be measured, the prompt laid out so
  every seat and call type shares the transcript, marks placed where a longer transcript can still find
  them, and the enforced output schema taken out of the cache key; and they can say what that last
  change did (Haiku reported reasoning tokens on every replayed sample and the replayed decisions
  improved, paid for in output) and what it does not show (whole games, other models).
- **Starting knowledge:** the Level 1 supplies what caching discounts (repeated input, never output),
  the layout with its boundary, that reuse must be verified in usage records (Gemini's automatic cache
  returned no reads), the paired-game result (28% on Luna, level on Haiku with more reasoning) and the
  participation effect. New here: prefix, cache write against read and the write premium, mark and
  breakpoint, content block, enforced schema against schema sent as text, legal targets, the admission
  check, reasoning tokens, the healer turn.
- **Concept order:** (1) a cache entry is something stored by one request and found by a later one, so
  what is stored and how it is found decide reuse, and a write costs more than plain input → (2) so
  measure before relying on it → (3) the layout decides what two requests share → (4) the mark decides
  whether a longer request can still find the entry → (5) an enforced schema is part of what the cache
  matches, so per-seat target lists split the cache; the text schema removes them from the key at the
  price of code validation and a retry → (6) the text schema also changed how much the model reasoned,
  which a replay pinned to the old mode exposed → (7) the paired games put the input saving and the
  extra reasoning in one bill.
- **Likely confusion:** reading §6 as "the output schema made Haiku smarter" in whole games, or
  "enforced = no reasoning". The page says: on one turn and 16 vote cases, one model, the replayed
  decisions improved; zero reported tokens do not show no reasoning happened. A second: reading the
  provider table as a league table; it describes tested integrations on a date.
- **Section order:** as the outline's §0–7. 0 Opening: why ten seats make this matter, the contract
  framing, the question. 1 What each provider stores: seat A then seat B, the four-row table, the write
  premium, one entry per model. 2 Measure first: the June probe in three sentences, the admission step
  with three real prompts. 3 The layout: where the old layout diverged, the new layout, the same three
  prompts before and after (table). 4 Marks on a growing transcript: Claude's walk-back with the two-turn
  diagram, OpenAI's breakpoints in two sentences. 5 The schema and the cache key: legal targets, why
  enforced splits the cache, the text alternative, the trial, the real-game failure rate and the enforced
  retry (table). 6 What it did to Haiku's reasoning: the replay pinned to the enforced mode, the
  three-row table, the vote cases, scope, the lesson about pinning the mode. 7 The paired games and what
  remains.

## Sample passage

The difficult relationship is §5: why an output schema, which is not prompt text, decides what two
votes can share, and why the alternative needs a retry. Drafted as page copy:

> A vote or night action does not return free text. Its reply is checked against a **schema**, a
> description of the fields the reply must contain, and the schema lists the **legal targets**: the
> players this seat may vote for or act on tonight. That list differs for every seat, because a seat
> cannot target itself, and it changes after every death. A rule of mine keeps those targets enforced
> by code through the schema, never written into the prompt as a list the model could misread.
>
> When the provider enforces the schema, the schema behaves like the start of the prompt: on Claude it
> is part of what the cache matches, and on OpenAI it is rendered before the messages. Two requests
> with identical text and different schemas therefore share nothing. With per-seat target lists, each
> seat's vote had its own cache, and votes, night actions and discussion turns could not read one
> another's copy of the transcript.
>
> The alternative keeps the rule and moves the schema out of the key: write the schema as text after
> the shared part, and validate the reply in code against the same per-seat schema, so an illegal
> target still fails. The question was whether replies written without enforcement would fail often
> enough to slow the live game with retries.

## Evidence and scope

- **Sources:** `evidence/caching/report.md` §2 (provider table, write premium, schema in the key),
  §3.2–3.5 (layout, Claude marks, OpenAI breakpoints, schema decision and retry), §4.1–4.4 (June probes,
  admission probe table, paired games, bench), §6 (open questions); `evidence/caching/experiment_log.md`
  §3 (June probe), §8 (admission caching step; the 800-token overlap, from working notes), §9 (Claude
  marks, 9,258 of 10,206), §12 (OpenAI's 4,582 reads; the unenforced trial), §13 (breakpoint probe,
  smoke check, bench, paired games), §16 (74 of 3,118; the enforced retry; frequency unmeasured);
  `evidence/gameplay/deduction/experiment_log.md` §8 (Result 1 table; "zero reasoning tokens do not
  show that no reasoning happened"; other low-cost models) and §9 (16 vote cases, 41% → 62% at low,
  61% → 77% at medium; 157/158 valid of 160); `Agents/llm_factory/catalog.py` `LIVE_EDITS_SINCE_MIGRATION`
  and the Luna/Haiku notes (switch dated 2026-10-14, "caching"), source note only.
- **Claim and limits:** mechanism (what each provider stores and reads; the walk-back; the schema in the
  key) from the report and the documentation it read on 2026-10-13; measured reuse from one probe
  sequence per row (three requests), not whole-game discounts; the schema decision's failure rates from
  a trial counting calls and twenty games counting seat decisions (different units, both named); the
  reasoning effect from one turn (10 samples a setting) and 16 vote cases (10 samples each), one model;
  the paired games two per arm, which show Luna's direction and cannot size Haiku's differences.
- **Elsewhere:** the node cache (chapter 1; no page exists yet, so no link); the field-order finding
  (chapter 3, `turn_request.md`); the engine's uptake measured in the enforced mode (chapter 3,
  `deduction_engine.md`); the admission check (Evaluation, `model_admission.md`); the extraction overrun
  and the participation story (Level 1 and the evidence report). Handle-with-care items applied: provider
  names unavoidable, model names as the Level 1 uses them (Haiku, Luna); no cross-backend score
  comparison; table dated; June figures scoped to the tested models and backend; two games per arm;
  "made for cost" as the recorded motive; "helped" = the replayed decisions; "reported no reasoning
  tokens"; retry frequency unmeasured; no claim the layout improved play; the 20-block, 80-breakpoint and
  four-written figures in the source note; no credits or plans named.
- **Open questions:**
  1. The outline's §3 says "two seats shared about 800 tokens". The log (§8) says this came from working
     notes with no data file kept. Used on the page as "about 800 tokens" with the source noted; the
     owner may prefer "only the opening rules".
  2. The outline's §7 lists "three seat models never measured under the layout". The report (§6) names
     DeepSeek, GLM and "the Gemini players" (more than one Gemini model). The page says "the seats on
     DeepSeek, GLM and Gemini" rather than counting three.
  3. The report's §4.4 bench (Luna, 18 discussion turns, no difference beyond noise) is used in the close
     as the one quality check that exists, with its power stated. If the owner wants the close shorter,
     it is the first cut.
  4. §6's table gives the enforced arm's reasoning tokens as "none reported in 4 of 10 samples; at most
     1,312" and the text arm's as "409–1,233, every sample". The log gives no per-sample list for the
     enforced arm beyond those two figures; the page states exactly that.
  5. (From the claims review.) The 16-vote re-run of 2026-10-30 (62% / 77%) and the enforced run of
     2026-10-16 (41% / 61%) rendered their prompts with the code of each day, and the deduction engine
     (first committed 2026-10-16, default mode "full") may be in the later prompts only. The page now says
     the two runs do not isolate the output mode. The owner may want to confirm from a rendered §9 prompt
     whether the engine block was present, or drop the vote re-run from this page.
  6. Length. The page copy is about 2,100 words of prose plus about 300 in four tables, against the
     outline's 1,000–1,300 guide. The approved outline carries eight sections, four tables and a diagram;
     the reviewers' blocking findings added orientation (model-to-provider mapping, the engine gloss, the
     retry history, the confound sentence, the unit labels, the scope reconciliation) rather than removing
     material. Candidates if the owner wants it shorter: the OpenAI paragraph of §4 to one sentence, §5's
     table to prose, §2 to two sentences, the vote re-run paragraph in §6 (also Open question 5).
  8. (From the third editorial read.) The admission probe's 29% different-seat share for Luna in the
     earlier layout is not explained by the page's account of OpenAI's boundary rule (the role card then
     sat in the system message). The report says the records do not identify which text was reused. The
     page states that; the owner may know the cause (the probe's prompt shape, or OpenAI matching below
     the message boundary) and may prefer a one-clause explanation.
  7. The Explore line on the Level 1 is plain text, so `parent_context.py` cannot find the link (and the
     parent file is named `cost_and_latency_codex.md`, which the script's convention does not find
     either). The editorial reviewer's excerpt was built by the script's own rule on a scratch copy of the
     chapter (parent renamed, link made real); nothing else in the Level 1 was changed.

## Review resolution

Reviews: editorial `caching_across_providers.review-editorial.claude.20261031T061851Z.tJ3R4j.md` (E1–E16),
claims `caching_across_providers.review-claims.claude.20261031T061926Z.EYh6Af.md` (C1–C8). Cosmetic items
omitted. A second editorial run followed the revision and a third followed the second round of fixes (files beside these).

| Finding | Action and reason | Whole-section recheck |
|---|---|---|
| E1 (blocking) §6 opens on an unexplained "disagreed with live play"; "engine", "engine on", "uptake" never explained | Fixed: §6 now opens by glossing the deduction engine in one sentence, naming the earlier replay (pinned to the enforced schema: the conclusion reached the notes, the decision barely moved) and the later replay that disagreed with it; the healer turn gets one plain sentence; "uptake" dropped | §6 reread as a whole |
| E2 (blocking) models never matched to providers; "four providers" but results by model; games mixing models assumed | Fixed: a paragraph under the provider table names Haiku (Claude) and Luna (OpenAI), states that a game's AI seats all run on one model chosen from the menu (confirmed in `server/schemas/requests.py` `NewSoloGame.model`) and names the June model as a Gemini model | §1 |
| E3 (high) "unmeasured" retry frequency contradicts the one-in-forty table figure | Fixed: the paragraph after the table says the twenty games used the plain text retry (six turns failed twice) and that the enforced retry came after them, so its frequency is unmeasured | §5 |
| E4 / C2 "four providers actually reuse it" overstated; Gemini seats get no reuse (cache objects serve extraction) | Fixed: opening reworded to "what each of four providers needed before it reused anything"; the Gemini row says the automatic cache returned no reads and the cache object serves post-game extraction, not turns, so Gemini seats get no reuse (report §1 per the claims reviewer, §3.1) | §0, §1, §7 |
| E5 Luna's probe rows change two things; paired-game arms undefined | Fixed: the caption says Luna's rows change the layout and the mechanism at once; §7 defines the arms (earlier layout + enforced schema against current layout + text schema) and no longer credits "the layout" alone | §3, §7 |
| E6 / C5 9,258 of 10,206 (91%) reads as current-layout evidence against the table's 77% | Fixed by removal: the 91% figure (an earlier-layout check, log §9) is dropped from the copy; the "any seat" claim now cites the table's 71%. Luna's 2,561 of 2,678 is labelled a probe seat | §4 |
| E7 schema defined for votes only while discussion turns are affected | Fixed: §5 opens with "every call returns structured output checked against a schema … the schema differs by call type", and legal targets as the vote/night addition | §5 |
| E8 / C4 "let the game's model reason more" states a mechanism for all models | Fixed: opening now "made Haiku report more reasoning tokens, and a replay found its decisions better for it"; the caveat stays beside the result in §6 | §0, §6 |
| E9 "long gap" reads as time | Fixed: "counted in blocks rather than time: if many lines arrive between two calls" (the 20-block figure stays in the source note per the outline) | §4 |
| E10 "held-back lines", "memory lookups", "brief" undefined | Fixed: glossed in one clause each; the diagram's "brief" became "instructions" | §3, §4 |
| E11 why Haiku read 0% and Luna 29% of a neighbour in the old layout | Fixed for Haiku (its marks ended a system message containing the role card, report §3.2 + §3.3); Luna stated only as "could reuse whatever opening two prompts shared", since no source explains the 29% | §3 |
| E12 how Luna read only the system message | Fixed: OpenAI stores an entry at the end of the system message and of the latest user message (log §12: "the end of the opening developer block"); the table row says the same | §1, §4 |
| E13 "Spoke" column unused | Fixed by removal: the column is dropped (figures kept in the source note); tying it to the parent's participation finding would claim a link the replay did not test | §6 |
| E14 reasoning tokens defined after the table; live setting = low unstated; "actual threat" undefined | Fixed: defined before the table; "(low)" stated; "a vote landed on an evil player" (the log's definition of right) | §6 |
| E16 "ten points" | Fixed: "about ten percentage points more replies marked wrong" | §7 |
| E15 (taste) "one entry per model" unused | Removed from the copy (kept in the source note) | §1 |
| C1 41% → 62% vote comparison is two runs two weeks apart; the engine shipped in between and the bench re-renders prompts with the code of the day | Fixed and flagged: the vote re-run is now "a later re-run … points the same way", with the sentence that the two runs were not side by side and rendered prompts with the code of each day, so they do not isolate the output mode; "helped the replayed decision" limited to the healer turn. Confirmed the cases hold game state (not rendered prompts) and that `DEFAULT_DEDUCTION_MODE = "full"`; whether the engine block was in the §9 prompts is Open question 5 for the owner | §6 |
| C3 "disagreed with live play" conflicts with the source (two replays disagreed) | Fixed: "replaying the same turn in the live output mode disagreed with that earlier replay" | §6 |
| C6 "the provider guarantees the shape" implies zero failures | Fixed: "enforces the shape; a content check still failed 3 of 170 Luna trial replies" | §5 |
| C7 one-in-forty read as both models | Fixed: "twenty Haiku games" | §5 |
| **Second editorial run** (`caching_across_providers.review-editorial.claude.20261031T062442Z.LXUIP0.md`, R1–R9) | | |
| R1 (blocking) §6 opens on an engine question but the table varies only the output mode | Fixed: §6 now opens on the replay and the output mode ("one recorded turn had been replayed with the schema enforced … replaying the same turn with the schema sent as text gave a different answer"), names the engine as the turn's origin and states that the engine is on in every row, so the table compares only the output mode; the engine-off rows (deduction log §8 Result 2) stay on chapter 3's page | §6 |
| R2 quality claims carry three scopes; "the only quality check" contradicts the replays | Fixed: opening bounded to "a replay of one Haiku turn found its decision better"; the close says "the only check of the layout on message quality" and ends by reconciling with the parent's "not established" | §0, §7 |
| R3 §4's "or a vote" relies on the schema change not yet introduced; the 71%'s schema mode unstated; why call types diverged | Fixed: the vote clause now carries a forward reference ("once its schema is out of the cache key, next section"); the probe caption states the schema was enforced in every row and the different seat's prompt is a discussion turn with the same schema (report §4.2); §3 says the other call types were built as prompts of their own | §3, §4 |
| R4 three units in one cell; trial-to-game gap unexplained; "content check" undefined; the open question never answered | Fixed: the table keeps trial units only (replies / calls); the games figure (74 of 3,118 seat decisions, one in forty) moved to the paragraph with its unit; "content check (an empty list of reads)"; "The trial said retries would be rare, and … switched" answers the question before the games showed more failures. The gap's cause is not in the sources and is not explained | §5 |
| R5 OpenAI figures lack layout and prompt; 96% against the table's 75%; why per-line breakpoints | Fixed: 4,582 dated to "the earlier layout's games"; the 2,561 of 2,678 probe figure removed (its prompt was a short synthetic transcript, not the admission prompt); "OpenAI does not walk back, so a breakpoint goes on every transcript line" (report §3.4) | §4 |
| R6 pricing paragraph separated from the table; GLM unplaced; write premium claimed for all four | Fixed: pricing paragraph moved directly under the table; the opening says "two of them charge more to write"; GLM dropped from the models paragraph and named only in the close as another listed model | §0, §1 |
| R7 "factual-error bench" and the sensitivity statement | Fixed: "replayed 18 recorded Luna discussion turns and had a judge mark replies that misstate the game … could only have detected a change of about ten percentage points in the share marked wrong" | §7 |
| R8 (taste) other-models clause | Shortened ("had also reported none under enforced output, but none was compared against the schema sent as text"); kept because the outline asks for it and it bounds the claim | §6 |
| R9 (taste) participation not mentioned beside the paired games | Fixed: one sentence points to the chapter page's finding and says this page counts cost per call | §7 |
| **Third editorial run** (`caching_across_providers.review-editorial.claude.20261031T062820Z.nfkclU.md`, T1–T10) | | |
| T1 (blocking) Luna's 29% different-seat reuse in the earlier layout contradicts OpenAI's boundary rule as the page states it | Fixed by scoping: the sources do not explain the 29% (report §4.2: the records do not identify which text was reused), so the copy explains Haiku's 0% and says Luna's 29% is not broken down; the inferred "whatever opening two prompts shared" clause removed. Open question 8 for the owner | §3 |
| T2 (blocking) the text schema seems to put the legal-target list in the prompt, against the stated rule | Fixed: the rule restated as code enforcement ("a reply naming a player outside the list is rejected, and the list is never left to a sentence in the prompt"); the alternative says "the same per-seat schema, targets included, as text … validated in code against it" (log §12, report §3.5) | §5 |
| T3 the latency question asked and not closed | Fixed: "The trial said retries would be rare" closes it for the trial; the enforced retry "adds one call's wait to the turn … so the cost in waiting is still open" | §5 |
| T4 unlike units across the table's failure cells | Fixed: both cells count trial replies (0 of 170 Haiku, 3 of 170 Luna; 1 of about 400 on each); the games figure stays in the paragraph with its own unit | §5 |
| T5 §6 opens on undefined terms and never says why decision quality is on a cost page | Fixed: §6 opens with the cost link (reasoning tokens are billed; 1.5× and several times in the paired games), then the replay, then the healer turn and engine, then the table | §6 |
| T6 "more reasoning tokens" rests on four zero samples while the enforced maximum is higher | Fixed: the paired-game 1.5× / several-times figures now carry "more"; the table's per-sample ranges stand as given in the log (no medians recorded there) | §0, §6 |
| T7 GLM unplaced; "never measured" against the admission check | Fixed: "passed the admission probe in the earlier layout and run the current one, but … never measured under it"; GLM named as served through OpenRouter | §7 |
| T8 (taste) the models paragraph did three jobs after the pricing paragraph | Fixed: the scope sentence moved into the opening, the June model into §2, the paragraph removed | §0, §1, §2 |
| T9 (taste) the vote re-run's four percentages add no reliable evidence | Compressed to one sentence with two figures (62% against 41% at low) and the confound. Kept rather than removed because the owner's 2026-10-31 ruling placed the vote re-run on this page; the owner may cut it (Open question 5) | §6 |
| T10 (taste) "nothing is stored on the application's side" | Removed | §4 |
| No fourth editorial run: the third round's fixes are local except the §6 paragraph order, which follows T5's proposed order; the Luna and legal-target repairs were checked against log §12 and report §3.5, §4.2 | | |
| C8 "the same direction" for other low-cost models overstated | Fixed: "had reported none under structured output or a forced tool call, but none was compared against the schema sent as text" | §6 |

Check technical repairs against sources. A misunderstanding can identify a problem even when the
reviewer's proposed solution is wrong. Record material findings, not cosmetic bookkeeping.

## Trial record

Draft snapshots: `caching_across_providers.first-draft.md` (before reviewer edits);
`caching_across_providers.reviewed-draft.md` (after).
Model and owner interventions: drafting agent on the default model; outline approved by the owner
2026-10-31 after a cold review (checkpoint satisfied before this run); both reviewers run with the
`claude` CLI per the skill, the editorial one on a scratch copy of the chapter so the parent excerpt
could be found (Open question 7).

| Owner change | Kind | Explanation redesigned or local edit? |
|---|---|---|
| | concept selection / order / missing connection / example or representation / prose / claim support | |

Fill after feedback; do not invent an owner usability score. Word count is a guide, not a quality measure.
