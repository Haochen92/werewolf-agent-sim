# Authoring brief: Designing and validating LLM judges

Page: `writeup/evaluation/llm_judges/llm_judges.skill.md` · Level 2 · started 2026-10-28 · checkpoint: approved in conversation; defaults accepted for all open questions

Authoring material, not page copy. The cold editorial reviewer never sees this file.

Trial run of the `write-portfolio-page` skill (full rewrite). This run covers steps 1–3 only; the
baseline page `llm_judges.md` was not read, only its brief and sources comment.

## Frame

- **Primary page type and level:** design decision with its evidence (page_types: "Design decision or
  trade-off"), Level 2. How to build a judge whose verdict can be acted on, and how to check it.
- **Secondary mode, if needed:** the featured section (the 1–5 quality rubrics) uses diagnostic mode:
  symptom (high scores that do not move) → what the scores were actually measuring → what decided the
  design calls instead. The live-game section borrows a little from reliability: what a wrong verdict
  costs, and how failing open limits it.
- **Existing outline approval:** approved by the owner in conversation, 2026-10-28, with the stated
  default for every open question.
- **Reader's question:** When one model grades another model's output, how do you make its verdict
  reliable enough to act on?
- **Central answer:** The judges that held up asked a narrow question about meaning, were handed the
  facts they needed, and were checked against something outside themselves. The broad 1–5 quality
  rubrics caught gross faults but could not rank versions, so those design calls went to other
  measures. The judges and live classifiers used today have been checked only by other models; the
  check against a person is prepared but not yet done.
- **Distinctions the reader needs:**
  1. **Catching a gross fault vs ranking close versions.** A judge can do the first without the second
     (the smoke-alarm point). A score that never moves is measuring what the format forces, not quality.
  2. **What the judge is given to decide with vs what it is checked against afterwards.** Facts or
     per-case criteria handed to the judge (its reference) are not a check of the judge; a person's
     labels, an outcome or a computation that the judge never sees are. Agreement with blind model
     readers is a weaker check than a person's: it cannot catch a bias both share.
  3. **A judge that measures vs a classifier whose verdict acts in the product.** The echo gate's
     verdict decides what the table hears, so it also has to be cheap, run on every turn and fail safe.
     Failing open limits a failed call; it does not prevent a wrong but valid verdict.
- **What the evidence establishes:**
  - The day-summary judge's presence-type dimensions sat at or near the maximum on every run, model and
    prompt version, while the content dimensions caught real failures (dropped accusers, an invented
    game-master announcement, claims written as fact). Version differences were smaller than the swing
    between identical runs; the decisions were made on architecture, latency and reading summaries.
  - The extraction judge's original dimensions clustered at 4.00 over 48 games; reading its scores found
    two bugs in the judge's own prompt.
  - The factual-error judges (yes/no against a fact sheet built by code; per-case written expectations)
    are the best-checked judges: a 23-case labelled set chose the reader; flagged public messages and
    samples of flagged notes and rejections were read by a person; re-judging the same outputs moved
    totals by one or two of 267.
  - Reading verdicts found faults in judges themselves (two prompt bugs, a wrong expectation, a judge
    that trusted text the summariser never sees).
  - The echo gate, against four blind model readers on 65 lines, held 10 of 29 restatements and none of
    36 worthwhile lines. The opening filter, before a fix, held 6 lines of 7 that the readers judged
    worth hearing.
- **What stays uncertain:** (scope beside each claim, not a closing disclaimer)
  - Every person's check is from the original nine-player game and was made with earlier judge models;
    none has been repeated on the current game or the current judge model.
  - The live classifiers rest on model readers only; the opening filter has not been re-measured since
    its fix.
  - Judges, in-game gates and players now default to the same model, so self-preference is possible
    wherever a run keeps the default.
  - The flat-score mechanism (the generator's prompt forced the section to exist) is the record's
    explanation; it was not tested by an intervention. The ±1 swing mixes generation and judging,
    because the harness regenerated summaries each run.
  - The calibration step and its pass bar are built but have not been run on real labels.
- **Stays off the page:** (from map.md "Handle with care", and the general list)
  - Never say or imply the current judges are calibrated: the labelling packets *enable* the human
    check; the gap closes only when the labels are done and acted on.
  - Human review of specific replay verdicts is not calibration of the judges used elsewhere.
  - Bookkeeping: a runner named in a record but missing from the repo (the parallel-round filter
    check); blank "check:" lines in unused review sheets; "no record found" of a re-run; which tests
    are AI-written. State the limitation in plain terms instead ("the checks predate the current
    judge model").
  - Model and vendor names in explanatory prose (owner voice); "a stronger model", "the players' own
    model", "one of the two models compared" carry the meaning. Code and folder names.
  - The retired discussion tagger (owner ruling 2026-10-22).

## Evidence selection

| Material (source) | Role | What it helps the reader understand or assess |
|---|---|---|
| Three conditions for using a model; code first (`llm_judge/report.md` workflow §1; census screens by code; today's summaries checked by code, `day_summary.md` status note) | essential | Why a judge exists at all, and that the third condition (its answers can be checked) is the one the featured judges lacked |
| Day-summary judge: only window onto a past day; five 1–5 dimensions; 18 pairs; transcript shown (`extraction/day_summary/experiment_log.md` ①②; `day_summary.md` L1) | essential | The setup of the featured story, in game terms a cold reader can follow |
| Rubric text for "village dynamics" (and "evidence type") (`evaluation/src/judges/prompts/day_summary.py`, `DAY_SUMMARY_RUBRIC` dims 3–4), beside 5.00 / 4.89–5.00 and the prompt that forced the section (`day_summary.md` L2 point 2) | essential (exhibit 1) | That the rubric's words asked for quality but the score behaved like a presence check |
| Content dimensions caught dropped accusers (5 of 18 pairs), an invented game-master announcement, confirmed-vs-claimed errors (`day_summary.md` L2 point 2; design log ②) | essential | That the judge was useful as a fault detector: the page must not read as "the judge was useless" |
| Version table: word limit 4.44→4.39 (reverted; model wrote 130–230 words anyway); structured output 4.44→4.50, kept for architecture; model choice decided by hand reading and latency; ±1 swing on one pair between identical runs; −0.11/−0.22 chased (design log ②; `day_summary.md` L2 point 3) | essential (exhibit 2) | Why a high, flat score could not answer the design question, and what answered it instead |
| Extraction judge: clustered at 4.00 over 48 games; two bugs in the judge's prompt found by reading scores (−1.19, +0.69); fixed extractions, only the judge prompt changed (`extraction.md` L2) | supporting | Same symptom on a second judge; and reading scores as a way to debug a judge |
| Census reader (yes/no against a code-built fact sheet, naming the wrong fact; cheap model over-flags, stronger re-reads) and expectation judge with the sentinel example (`report.md` case 1, workflow §2) | essential | The contrast: what a narrow, fact-backed judge looks like |
| Why no single reference answer (`report.md` workflow §2) | supporting | One design choice inside the contrast: a model answer marks down correct replies worded differently |
| Rubric design rules: requirements from the generator's own spec (shared standards text); one written rule per criterion; verdict with its evidence; rubric kept in step (day-summary copy outlived its format) (`report.md` workflow §3) | essential | The transferable design practice; ties the failure to a fix |
| Pairwise judge: order alternated; drove no design call; a human-labelled retrieval set did; generated and judged in one pass (`report.md` case 6; `scoring/report.md` Layer 1) | supporting | A narrower format still needs an anchor; also the generate-and-judge confound |
| Reference vs anchor; three anchors (person, stronger model, outcome) (`report.md` workflow §4) | essential | Distinction 2 |
| Check procedure: stratified by verdict, blind, controls, noise floor (1–2 of 267), read verdicts, recheck on model/rubric change (`report.md` §4) | essential | What validating a judge consists of |
| Census reader's person check: 23-case set chose it; I read 90 flagged public messages; precision about 0.8 on 25 flagged notes; 2–3 missed in 15 rejections (`llm_judge/experiment_log.md` §7; `report.md` full record) | essential | The one worked example of a judge checked against a person, with its scope (earlier game, earlier models) |
| Faults found by reading verdicts: wrong expectation ("never claimed any role"); summariser judge trusted the moderator's closing line, rerun without it (`report.md` key learnings; case 7; `labeling/report.md` case 4) | supporting | That a reference-based judge is only as good as its reference, and that reading is part of validation |
| Summariser comparison: the judge was one of the two models compared; decision held because the bias favoured the model that lost (`report.md` case 7) | supporting | Self-preference made concrete; leads to the same-model limit |
| Echo gate and opening filter: what each decides; cheap call at low thinking; fail open; human seats and replies to a named player never gated; own-role claims always kept; judges kind not truth (`Agents/turn/echo_gate.py`, `round_filter.py` docstrings; `report.md` case 2) | essential | Distinction 3 and the live-product constraints |
| Echo gate prompt versions on 146 lines (29% → 18% held; reading the holds found lines that credit a speaker then add were held) and the shipped bar vs four blind model readers (10 of 29, 0 of 36) (`llm_judge/experiment_log.md` §9) | essential | Reading verdicts shaping a live classifier; its current check and that check's limit |
| Opening filter: 6 of 7 held lines judged worth hearing before a fix; not re-measured since (`report.md` case 2, full record) | supporting | Why failing safe matters; an honest open item |
| Calibration step: pass bar 80% / lower bound 75% / no significant lean; built, not run on real labels; packets for accusation tags, echo gate, factual-error judge (`labeling/report.md` §5 and "Golden sets against what is deployed today"; `evaluation/src/labeling/config.py`) | supporting (link) | The next step; the full explanation lives on the reference-labels page |
| Same default model for judges, gates and players (`llm_judge/experiment_log.md` §2 correction; `report.md` "What is missing" row 7) | essential (limit) | A limitation that changes how to read any current judge number |

Left out, and where it lives instead:
- Discussion-evidence judge and its rubric split (74% → 63%): the fair-comparisons page uses it.
- Accusation tags (79% against an unchecked judge) and the human-seat addressing classifier: one more
  live classifier adds no new decision; the labelling page names the accusation-tag packet.
- Decision tagger, de-halo pass, point-dedup, dedup decision: memory chapter and reference-labels page.
- Tell detector, same-tell, memory-adherence, coherence judges, application and retrieval judges: memory
  research records; no current result rests on them.
- Agreement scores (kappa, per-label precision/recall, McNemar), sample sizing, packet design: the
  reference-labels page.
- Judge configuration (structured output, retry once, settings recorded per run): one clause at most;
  the fair-comparisons page owns recorded settings.
- Coverage of reference points (the planned golden-set method for summary judges): planned, not built;
  supporting note only.
- Per-judge model names, dates, top-up list: sources comment.

## Argument outline

Structure: **successive questions**, like the evidence-design example. Each section is the reason for
the next: when is a model the right tool → what goes wrong when its answers cannot be checked (the
featured story) → what the judges that held up did differently → how a judge is checked → what changes
when the verdict acts in the live game → what is established today. Execution order does not fit: a
judge has no pipeline order the reader needs; the argument is a chain of design lessons, and the
featured failure is what motivates the narrow design and the validation that follow.

| # | Section (working heading) | Question it answers | Main point | Carried by (example / finding) | Why the next section follows |
|---|---|---|---|---|---|
| 0 | Opening (no heading) | What is an LLM judge here, and what makes one usable? | A judge is a model grading another model's output against a rubric; in this project some measure, and some sit in the live game and act. The usable ones asked a narrow question with the facts handed over and were checked against something outside them; broad 1–5 rubrics caught gross faults but could not rank versions; today's checks are by other models, a person's check is prepared | Two concrete uses named in one sentence each: grading a day summary; deciding whether a line is heard | States the three conditions it then unpacks, starting with whether a model should judge at all |
| 1 | When a model should judge | When is a model the right tool rather than code or a person? | Use a model only for questions of meaning, over more items than a person can read, where its answers can be checked; if code can compute the answer, use code | The factual-error census screens by code first; today's day summaries are checked by code against the claim record | The third condition is the one the featured judges lacked; the story shows what that costs |
| 2 | Featured: the quality scores that could not rank versions | Why did a judge that gave sensible high scores not help choose between versions? | The rubric's words asked for quality, but where the generator's prompt forced a section to exist the score only confirmed it existed (5.00 every run). Content dimensions moved and caught real faults, so it worked as a fault detector. Version differences were smaller than the swing between identical runs; the calls went to architecture, latency and reading summaries | Exhibit 1: the "village dynamics" rubric text beside its 5.00 and the forcing instruction. Exhibit 2: three changes tested, the score before/after, and what decided each. The extraction judge's 4.00 clustering and the two prompt bugs found by reading its scores, briefly | The judges that did hold up were designed differently; the contrast shows how |
| 3 | Narrow questions, with the facts handed over | What did the judges that held up do differently? | Ask a yes/no or fixed-class question; hand over the facts (a fact sheet built by code) or a per-case expectation; require the evidence with the verdict; write a rule for each criterion; take the requirements from the generator's own spec and keep the rubric in step with it. A narrower format (pairwise) still needs an anchor: a human-labelled set, not the pairwise judge, settled that design | Census reader (verdict names the wrong fact; cheap model over-flags, stronger re-reads); the sentinel expectation example; why no single model answer; the day-summary rubric's copy outliving its format (one sentence); the pairwise judge (short paragraph) | A narrow, well-fed judge can still be wrong, and the expectation it is given can be wrong; it has to be checked |
| 4 | Checking a judge against something it never sees | How do you know a judge is right, and what does each kind of check miss? | Draw the reference/anchor distinction. A person's labels on a stratified blind sample are the standard; a stronger model reader scales but shares biases; an outcome checks only in aggregate. Measure the noise floor, include controls, read verdicts and their reasons, recheck when the model or rubric changes. A judge from one of the compared models is a bias to account for | The census reader's person check (23-case set; I read 90 flagged public messages; ~0.8 precision on flagged notes; 2–3 misses in 15 rejections), with its scope; noise floor 1–2 of 267; faults found by reading (wrong expectation; judge trusting the moderator's line); the summariser comparison's self-preference and why its decision held. Link to the reference-labels page for the scores, pass bar and packets | Some model verdicts do more than measure: inside the live game they decide what players hear, which adds constraints |
| 5 | When the verdict acts: classifiers in the live game | What changes when a model's label changes the game rather than measuring it? | It must be cheap enough for every turn and fail safe: an error keeps the line, a human seat and a reply owed to a named player are never judged, a claim about one's own role is always kept, and it judges the kind of statement, never its truth. Failing open limits failed calls, not wrong verdicts, so the gate's errors still need measuring | Echo gate: three prompt versions on the same 146 lines, reading the holds, the widened bar, 10 of 29 / 0 of 36 against four blind model readers. Opening filter: 6 of 7 held lines were worth hearing before a fix; not re-measured since | Brings the reader to what is and is not established today |
| 6 | What is established, and the next check | Which judges can be trusted today, and what would change that? | Narrow, fact-backed judges are the ones that held up, and the factual-error judges have a person's check, from the earlier game and earlier judge models. The live classifiers rest on model readers. Judges, gates and players now share a default model. Packets for a person's check of the factual-error judge, the echo gate and the speakers' accusation tags are ready; until they are labelled and acted on, current judge numbers are provisional | Status in plain words; no new numbers | — |

**Outline check (main points read in order).** Use a model only where its answers can be checked → a
judge that could not be checked gave high, flat scores and decided nothing → narrow, fact-backed judges
held up → even those must be checked against something outside them, and each check has a blind spot →
a judge inside the live game must also fail safe, and its check is still model-only → so today: the
design is sound where narrow, a person's check is the missing step. This answers the reader's question.
Term order: "rubric" and "judge" defined in the opening; "reference" first used in §3 (as facts handed
over) and contrasted with "anchor/check" in §4; "noise floor" defined in §2 by what was repeated (the
identical runs) and reused in §4; "fail open" defined in §5. No section relies on a later one.

**Drafting changes (step 4, 2026-10-28).** Section order, questions and main points unchanged. Small
changes: §4 carries the three kinds of check as a short table (the outline had them as prose); exhibit 2
has three rows, leaving out the "list every accuser" step (a mixed result whose numbers are within the
swing); the pairwise judge sits at the end of §3 as planned. Length came out at about 2,400 words of page
copy including tables and captions, above the 1,800–2,000 plan; no cut made before review (the guide
cuts repetition first, and the reviewers should see the full argument).

**Skim (headings, opening sentences, captions).** The argument is followable from the skim. Fixed: §1's
first sentence promised "three things" without naming them; it now states them. Left: §2 opens with
game context rather than its point (the heading carries the point, and the context is what a cold reader
needs first); §4's "That comparison also carried a bias" leans on the paragraph before it. Also fixed
while skimming: §5 said human lines "never reach the model", which is true of the gate but not the
opening filter (it undoes a verdict against a human line); now "a human player's line is never held".

**Level 3:** none. The rubric story stays on this page (content plan: reassess once page 4 is drafted).

**Length plan:** about 1,800–2,000 words with two exhibits; §2 is the longest (about 450 words), §1 and
§6 the shortest.

## Open questions

1. **Same default model for judges, gates and players.** Stated as a current limit in §4/§6 (affects:
   every current judge number). If the default is changed before publication, the sentence changes.
2. **Boundary with the reference-labels page.** That page already explains the calibration step's scores,
   its 80% / 75% / no-lean bar and the three packets. Default: this page says what a check must contain
   and its status in one or two sentences and links there; it does not repeat the scores or the bar.
3. **Echo-gate numbers.** The hardening plan calibrates the gate's readers "if the write-up keeps the
   numbers". Default: keep 10 of 29 / 0 of 36 with "against blind model readers" beside it.
4. **First person for the census check.** Records say "the owner read" the 90 flagged public messages;
   page 1 already says "I checked the flagged public messages". Default: first person, matching page 1.
   The bench's "10 of 12 hand-checked" names no reader: kept as "by hand" if used.
5. **Day-summary rubric outliving its format.** Default: one sentence in §3 as the reason to share the
   rubric text with what it grades, saying no current result uses that judge; not called "retired"
   (the retirement note is not written).
6. **Flat-score mechanism.** The record's explanation (the generator's prompt forced the section, so the
   judge confirmed presence) is not tested by intervention. Default: say the prompt required the section
   and the score never moved, and call presence-checking the likely reading, not a demonstrated cause.

Defaults 1–6 above were accepted by the owner (2026-10-28). Raised by the review, for the owner:

7. **Are the two early 1–5-judge decisions still in effect?** (the extraction model chosen on 5–10 games;
   application prompt v2). The record says v7 carried the extraction choice forward; the ten-player memory
   may use another extractor. Page wording claims neither "superseded" nor "current": "two early decisions
   did rest on them, both on few games … none of the project's current results rests on them".
   *Round 2 (2026-10-29):* the editorial reviewer read "none of the current results" as possibly
   contradicted if the memory-note model still stands. Both sentences moved to the supporting notes, so the
   page now makes no claim either way. If you rule the choices superseded (or still current), the passage
   can come back with that status stated.
8. **Is the opening filter's declared-field override deployed?** `round_filter.py` in the working tree lets
   the speaker's own fields settle a claim's kind (the judge had labelled such lines "other"); the file
   has uncommitted changes. The page says nothing about it. If deployed, §5 could say code now keeps
   declared claims in the opening round.
9. **Noise-floor denominator.** Summary reports say re-judging moved totals by "1 to 2 of 267"; the run
   record gives bad notes 65 against 67 of 151. Page: "moved the count of bad samples by only one or two",
   true under either reading. Confirm which total, then add the denominator.
   *Round 2:* the claims reviewer pointed out that "samples" itself takes a side (notes vs samples). Now
   "moved the count judged faulty by only one or two", moved out of the procedure paragraph into the
   results paragraph. The editorial reviewer asked for the set size and unit; they wait on this answer.
11. **Does the ten-player blind hand count count as a person's check?** (round 2, claims finding 2) The
    factual-error log (§6) records that on the ten-player Haiku visit set every sample was read by hand
    before the verdicts came back: about 19 bad before and 6 after by hand, 16 and 5 by the judge. That is
    a blind comparison of totals, not items. The labelling report classifies no ten-player set as having
    a person's check, so the records disagree; the reader is not named. Page wording, true either way:
    "no judge has been scored item by item against a person's labels" and "the expectation judge's
    verdicts have been read but not scored against a person's labels". If you count it, the opening and
    §4 can add the totals with "a blind hand count on one test set".
12. **Evidence-type scores before structured output.** The caption says evidence type scored 4.89–5.00
    and the text attributes that to a later version requiring an evidence label on each accusation. Only
    the three final-prompt score files survive (all structured-output runs); whether the free-text runs
    also scored that high is unchecked. The text already calls presence-checking "the likely reading";
    if the free-text runs were also near 5, the second half of that sentence needs narrowing to the
    structured runs.
10. **Settled by the owner's ruling, 2026-10-29: the setting paragraph is removed (a Level 2 page
    continues from the chapter excerpt).** Original question kept below for the record.
    **Game setting paragraph.** Added because the cold reader could not follow the examples. Check that
    the description (agents plus people on the website; town and evil sides; the game master run by code)
    matches how the chapter page or site introduces the game, or replace it with a link if the site
    supplies that context above every Level 2 page.

## Revision pass 2026-10-29

Owner ruling: a Level 2 page does not re-introduce the game or the project; it continues from the chapter
excerpt (`scripts/parent_context.py`: the chapter introduction and its "Designing and validating LLM
judges" section). Taken as known from the excerpt: what a judge and a rubric are; that narrow judges with
facts were useful; that 1–5 rubrics clustered and could not distinguish versions; that code checks were
used where the record gives an answer; that review packets are ready and assessments provisional. Not in
the excerpt, so still explained on the page: the nine- and ten-player versions, memory notes, the census
reader, the expectation, the echo gate and opening filter.

**Page-copy word count:** 2,940 → 2,163 (same method both times: everything from the page-copy heading to
the evidence list, tables, captions and table pipes included; the prose alone is a little under 2,100).

Removed or moved (all moved passages are kept verbatim in the sources comment, "SUPPORTING NOTES"):
- **Opening:** the game-setting paragraph and the restated definition and summary removed (repeat the
  excerpt). The new opening starts from the chapter's summary and names the three distinctions the
  sections take in turn, then the nine/ten-player split and the status claim (scope unchanged).
- **"When a model should judge"** (section removed): its code-first point repeats the excerpt; its third
  condition became the two-sentence bridge at the start of the featured story. Moved to notes.
- **Featured story:** "game master" no longer named (not in the excerpt): "a code-written record of
  votes and deaths", "an announcement the game never made". The extraction-judge paragraph moved to
  notes (a second instance of a finding the excerpt already states); its scope point, that two early
  decisions rested on such judges, stays in the closing paragraph (open question 7 untouched).
- **Narrow questions:** the sentinel example moved to notes (it needs three roles and the visit
  mechanics explained); the expectation is now described by what it holds, with the investigation
  example from the factual-errors page. The pairwise-judge paragraph moved to notes (it answers whether a
  pairwise format fixes bunching, a different question, and needs memory search explained first).
- **Checking:** the summariser comparison (the line read out before the vote; the self-preference case)
  moved to notes; the self-preference reason now sits in one clause beside the same-model limit in the
  closing. Noise-floor wording unchanged (open question 9).
- **Live game:** the echo gate's prompt history moved to notes (how the prompt was shaped, not how far
  the shipped gate can be trusted); the shipped gate's check stays. "Night action" glossed as "what its
  own role did or learned overnight". The accusation-tags paragraph folded into the closing sentence on
  the packets.
- **Closing:** the last sentence no longer repeats the excerpt's "provisional"; it says the gap closes
  only when the labels are done and acted on (handle-with-care wording).

Scope kept as qualified: the status claim (earlier version only; current version not checked against a
person's labels; live classifiers at most against model readers); "held up" defined; the procedure
written as "should"; the census read not blind and not repeated; test-case reading not an agreement rate;
code protections apart from prompt rules; the same-model limit. Open questions 1–10 unchanged; none
settled by rewording.

**Over the guide (about 2,100 words of prose against roughly 2,000), reasons by section:**
- *Quality scores that could not rank versions* (about 720 words with two exhibits): the featured story;
  the rubric excerpt and the table carry the page's first distinction, and the unit sentence on the swing
  answers a claims finding.
- *Checking a judge* (about 480 words): the only person's check in the project, with the scope that §6's
  "held up" and the opening's status claim depend on (not blind, not repeated, test-case reading is not an
  agreement rate).
- Opening, *Narrow questions*, *Live game* and *Established* are each within a normal share of the guide.

Structure change: five sections instead of six (the first folded into the featured story's bridge). Order
of the remaining sections, their questions and main points unchanged. A second review is not required
for structure; the claims-review recommendation from 2026-10-28 stands (the setting paragraph it would
have checked is now gone).

## Review resolution (round 2)

Reviews: `llm_judges.skill.review-editorial.claude.20261029T015526Z.k6nAsh.md` (cold read, given the
chapter excerpt) and `llm_judges.skill.review-claims.claude.20261029T015814Z.PjS7Uf.md`. Resolved
2026-10-29.

| Reviewer | Finding (passage) | Action: fixed / declined (why) / flagged | Recheck needed? |
|---|---|---|---|
| Editorial 1 (blocking) | Current-game hand reading seems to contradict the opening and closing | Fixed: one wording in all three places ("scored item by item against a person's labels"); the reading is now named (the expectation judge), its finding given (the wrong expectation), and why it is weaker stated. Whether a blind hand count also counts: flagged (Q11) | Opening, §4, §6 re-read together |
| Editorial 2 | "Test-case verdicts" not tied to a judge | Fixed, and a mislabel corrected: the 10 of 12 belong to the census reader on the earlier test set, not the expectation judge; now its own paragraph naming each judge | Sources note corrected |
| Editorial 3 | The opening's three distinctions don't state why narrow judges worked | Fixed: the opening now states what the narrow judges shared (an answerable question given the facts; verdicts that stood when a person read them), then the two further points | No |
| Editorial 4 | "A reply owed to a player who named the speaker" and accusation labels arrive unexplained | Fixed: "a line answering a player who named the speaker" (no obligation needed); the accusation marks explained in the closing clause, with why they need an outside check. A §5 paragraph declined: it would grow the page for a label the section does not use | No |
| Editorial 5 | "A check the player never made" collides with "check" meaning validation | Fixed: "an investigation the player never made" | No |
| Editorial 6 | Noise floor: no set size or unit; result inside the procedure paragraph | Partly fixed: the definition stays in the procedure, the result moved to the results paragraph with a neutral unit ("the count judged faulty"). Set size waits on Q9 | Owner |
| Editorial 7 | Census check could read as covering misses; 23-case set result; "two or three" | Fixed: statements that never reached the stronger stage were not sampled, so counts are floors; "about two or three" is the record's own wording, kept with "about". The 23-case set's result declined (it chose between reader set-ups, a different question; "was used to choose" says what it did) | No |
| Editorial 8 | Unit change to "games"; are the early decisions still in effect; memory notes undefined | Fixed by moving the passage to notes (Q7 stays open); "memory notes" no longer appears on the page | No |
| Editorial 9 (taste) | "Its later structured output" unclear | Fixed (agreed): "a later version, which wrote one entry per accusation" | No |
| Editorial 10 (taste) | "Highest overall" undefined, no number | Fixed (with claims 1): completeness 4.83 against 4.44 | No |
| Editorial 11 (taste) | How four readers' labels were combined | Fixed (with claims 6): one reader per line | No |
| Editorial 12 (taste) | "Situation and certainty rules" opaque | Fixed by removal (claims 4): the rule is stated generically | No |
| Claims 1 | "No version could be told apart" contradicted by the model row | Fixed: scoped to prompt versions; the judge did separate the models (4.83 vs 4.44) and the choice went against its ranking, on speed and hand reading. Checked in the three score files | Smoke-alarm sentence now says "could not reliably measure" |
| Claims 2 | Ten-player blind hand count vs "no judge checked by a person" | Flagged (Q11); worded true either way | Owner |
| Claims 3 | "Shown to no one" wrong: website observers see held lines | Fixed: "shown to no player" | No |
| Claims 4 | Shared-text example is a judge that did not hold up | Fixed: paragraph reframed as the workflow's rules for a checkable verdict; the memory-notes example moved to notes. A drift-not-bunching sentence was added, then also moved to notes (the reframing covers it) | No |
| Claims 5 | "Fullest check in the project" ignores the dedup classifier | Fixed: "fullest check of any judge" | No |
| Claims 6 | Four readers could read as four labels per line | Fixed: "four model readers, one per line" | No |
| Claims 7 | "Bad samples" takes a side on Q9 | Fixed: "the count judged faulty"; Q9 still open | Owner |

**Length after round 2:** page copy about 2,220 words (tables and captions included; about 2,150 of
prose), up from 2,163. Additions, each answering a finding: the opening's statement of what narrow judges
shared (editorial 3); the census floor sentence (editorial 7); the separate paragraph naming which judge
each hand reading covers, with its finding (editorial 1–2, and a mislabel); the model row's scores and the
scoped ranking sentence (claims 1); the accusation-marks clause (editorial 4). Offsets: the early-decisions
passage and the memory-notes example moved to notes; the drift-not-bunching sentence moved to notes.
Section reasons for running long are unchanged from the revision pass (§2 the featured story with two
exhibits; §4 the only person's check and the scope the status claims rest on).

**Another review:** structure unchanged (same five sections and order). The opening's central statement
was rewritten (editorial 3) and the status claim reworded in three places (editorial 1 / claims 2), so a
short claims re-check of the opening, §4's two results paragraphs and §6 is worth one run; the editorial
reviewer need not run again.

## Step 7 (not reached in this run): edits that would follow elsewhere

Listed instead of made, per the trial's file limits:
- The evaluation chapter has no `editorial_notes.md`; the dated entry would go into a new one (or the
  chapter's existing convention, to confirm with the owner).
- `writeup/evaluation/exhibits/source_map.md`: LJ-rubric and LJ-flat-scores from "planned" to "drafted";
  the menu entry 5 ("Checking the judge against a human read") mapped to §4.
- `writeup/evaluation/content_plan.md`: page 4 row unchanged; the "Kept on Level 2" row for the rubric
  story re-assessed (stays on Level 2).
- `writeup/evaluation/evaluation.md`: the Level 1 summary is consistent with this frame; no change
  expected unless the same-model limit is added there.
- After review (2026-10-28): the editorial-notes entry would record the added game-setting paragraph,
  the narrowed status claim in the opening ("a person's measure of accuracy exists only for the earlier
  game"), the scoped "held up", and open questions 7–10; and that "editorially revised" is not
  "factually verified".
- `writeup/evaluation/reference_labels/reference_labels.md`: none needed; this page still links there for
  the scores, pass bar and packets.

## Review resolution

Reviews: `llm_judges.skill.review-editorial.claude.20261028T145757Z.2HbusZ.md` and
`llm_judges.skill.review-claims.claude.20261028T150010Z.lOMlQr.md`. Resolved 2026-10-28.

| Reviewer | Finding (passage) | Action: fixed / declined (why) / flagged | Recheck needed? |
|---|---|---|---|
| Editorial 1 (blocking) | The game is never introduced; roles, game master, floor, rounds arrive unexplained | Fixed: a new first paragraph says what the game is (agents and people, secret roles, town and evil sides, night actions, day discussion and vote, game master run by code) | No; setting only |
| Editorial 2 (blocking) | Earlier vs current game never introduced; the opening's caveat seems to contradict the census check | Fixed: the opening names the nine- and ten-player versions; the caveat now says a person's measure of accuracy exists only for the earlier game (with claims 1) | Rechecked §4 and §6 for consistency |
| Editorial 3 | "Held up" undefined; one judge stands in for a rule | Fixed: §6 defines it (most verdicts stood when a person read them) and names the factual-error judges; §4 now gives the test-case reading (10 of 12; every current-game verdict read) and says it is not an agreement rate | §6 re-read |
| Editorial 4 | The bridge "met the first two conditions but not the third" does not name the failure | Fixed: the bridge says they were given the source to judge by, but no person's labels said whether their scores were right | No |
| Editorial 5 | Noise on one pair vs table differences in 18-pair means | Fixed (with claims 8): says one pair's swing moves the 18-pair average by about as much as the version differences, and that no version could be told apart | No |
| Editorial 6 | Two summariser-model comparisons look like one; "flawed" undefined; time in a score column | Fixed: §4 names the later comparison as on the current game and replacing the current cheaper writer; "flawed" defined; table column renamed "What the judge's scores showed", and the chosen model stated | No |
| Editorial 7 | Sentinel example needs the visit logic and the rival claim | Fixed: two players claimed investigator; several roles visit, so a visit shows only that the player acted | No |
| Editorial 8 | Pairwise: reason after the decision; memory search unexplained | Fixed: one clause on the situation description as the search query; the one-pass confound now follows "settled nothing" (stated as a limit, not as the cause) | No |
| Editorial 9 | Census check changes units; private notes undefined; which stage rejected; precisions in different forms | Fixed: statements defined as public messages or private notes; rejections are the stronger stage's; both results now in counts or "four in five" | No |
| Editorial 10 | Human players first appear late | Fixed by the new setting paragraph | No |
| Editorial 11 | Accusation tags first appear in the closing | Fixed: one paragraph at the end of §5 introduces them as the player's own label, with no person's check | No |
| Editorial 12 | Memory-note bug details undefined | Fixed: kept the point and the 4.00 clustering; the two bugs now "each moved a score by more than half a point"; memory notes defined once | No |
| Editorial 13 | Naming: factual-error judge(s), game master vs moderator, memory-notes vs extraction judge | Fixed: "factual-error judges" defined as the two; "moderator" replaced by "a line read out before the vote"; the memory-notes judge named as the extraction judge in text and evidence list | No |
| Editorial 14 (taste) | "model answer" reads as an LLM's answer | Fixed (agreed): "reference answer, a single correct reply" | No |
| Claims 1 | Opening says today's judges were checked only against models; contradicts §4/§6; addressing classifier unchecked | Fixed: rewritten as "a person's measure of accuracy exists only for the earlier game; on the current game no judge has been checked against a person's labels; live classifiers at most against other models" ("at most" covers the unchecked classifier without naming it) | Rechecked §6 |
| Claims 2 | Check procedure in present tense reads as practice; census read not blind, not repeated after model change | Fixed: procedure in "should"; §4 says the census reading started from verdicts (not blind) and was not repeated after the move to a new model | No |
| Claims 3 | "Design decisions made by other means" overstated: two early calls rested on 1–5 judges | Fixed: the opening scopes to the summary's design; §2 adds the two early decisions on few games. Not called "superseded": flagged (open question 7) | No |
| Claims 4 | Day-summary setup in present tense, wrong for today; game master record separate | Fixed: "In May, in the nine-player game … apart from the game master's record of votes and deaths" | No |
| Claims 5 | "Today's summaries are checked by code" overstated | Fixed: fixed fields checked by code patterns in a replay of past failure days | No |
| Claims 6 | Own-role rule is a prompt instruction, not code | Fixed: code protections and prompt rules separated; "the gate is told always to keep…". The working-tree filter change that trusts declared fields is left off: flagged (open question 8) | No |
| Claims 7 | Thinking level and call frequency wrong for the filter | Fixed: "with little thinking: the gate once per line, the filter once per opening round" | No |
| Claims 8 | Unit mismatch in the noise comparison | Fixed with editorial 5 | No |
| Claims 9 | "1–2 of 267" not traceable to the run record (65/151 vs 67/151) | Flagged (open question 9); worded without a denominator so it is right either way | Owner |

**Second review:** editorial, not needed (section order and questions unchanged). Claims, recommended
once: the central status claim in the opening and §6's "held up" were rewritten, and the new setting
paragraph and the §4 additions (test-case reading, the later comparison's framing) are facts no reviewer
has checked.

**Length after revision:** about 2,940 words of page copy (was about 2,420). The additions answer
blocking or worth-fixing findings. Candidates if the owner wants it shorter, without losing a claim's
scope: the test-case reading sentence in §4 (keep only "case-by-case reading is not an agreement rate"),
the pairwise paragraph's mechanics, and the third row of exhibit 2.
