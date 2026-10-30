# Authoring brief: Designing and validating LLM judges

Page: `writeup/evaluation/llm_judges/llm_judges.skill_2.md` · Level 2 · started 2026-10-29 · checkpoint: approved in conversation 2026-10-29; owner defaults given

Authoring material, not page copy. The cold editorial reviewer never sees this file.

Trial run of the write-portfolio-page skill (second version, copy without example C), steps 1–3 only.
Inputs read: `writeup/portfolio-writing-prompt.md`, `writeup/portfolio-level-2-writing-prompt.md`, the
skill's `voice.md`, `examples.md`, `page_types.md`, both reviewer prompts; example B's page copy
(`evidence_design.md`, closest: an approach tested by evidence); the chapter page and the parent excerpt
(`parent_context.py`); `writeup/evaluation/content_plan.md`; `writeup/map.md` "Chapter outline:
Evaluation" with its Handle-with-care list; the exhibits source map; the original brief and sources comment
(packet). The chapter has no `editorial_notes.md`. Other versions of this page were not read.

## Frame

- **Primary page type and level:** approach or technique (when to use an LLM judge, how to design one, how
  to check it), at Level 2.
- **Secondary mode, if needed:** a diagnostic passage for the featured story (why the quality rubrics could
  not rank versions: symptom → what the rubric actually rewarded → why the differences were within noise →
  what decided instead). One section, not the page's structure.
- **Existing outline approval:** approved in conversation 2026-10-29 (Frame, Core argument and Argument
  outline as proposed). Owner answers, applied in the draft:
  - Judges defaulting to the players' own model: one sentence, as part of the next step, no model names.
  - Echo gate: about 200 words on the cost of a mistake and the safe-failure design; link the
    silence-calibration page for how its threshold was set.
  - A short table of which judges are checked by what (judge, what it decides, what checked it, which
    game), placed in §6.
  - First person for choices and uses ("I scored", "I widened the bar"), never "I wrote the judge".
  - Pairwise judging: one or two sentences at most.
  - Open questions 2–4 not answered by the owner: my stated defaults apply.
- **Reader's question:** when can a model's assessment of another model's output be trusted to guide a
  decision, and how do you design and check such a judge?
- **Central answer:** a judge earns trust when it answers a narrow question of meaning against facts it is
  handed, under a written rule, and when its verdicts are checked against something outside it; the
  project's broad 1–5 quality rubrics caught gross faults but mostly rewarded sections the generator was
  required to write, so their high, flat scores could not rank versions and those decisions went to other
  measures.
- **Reader starting point:** the parent defines an LLM judge and a rubric, says the useful judges were
  narrow and fact-fed, that the 1–5 rubrics clustered high and could not separate versions, and that the
  current game's judges await human validation with packets ready. This page must still define: the two
  uses (a judge that measures vs a classifier whose label changes the game), what "a reference" and "an
  anchor" are, the noise floor, blind model readers, and fail-open. It needs one sentence of game context per
  example (what a day summary is for; what an open-floor line is).
- **Opening choice:** an approach page opens with what the tool does, why it is needed and when to choose
  it. The parent already gives the definition, so the opening spends two short paragraphs on the need
  (questions of meaning, too many items to read) and the two uses, then states the central answer. The
  conditions for choosing a model follow as the first section, because the featured story is a case where
  the third condition (something outside the judge can check it) was missing.
- **Claim level:** practical choice plus a diagnosed failure. The evidence needed: the rubric-vs-score
  observation and the noise reading for the failure; the census check for the contrast; the calibration
  design described as built, not run. No general claim that narrow judges are better everywhere.
- **Distinctions the reader needs:**
  1. A judge that **measures** vs a **classifier in the product** whose label changes what players hear.
  2. A **reference** (given to the judge to decide with) vs an **anchor** (what its verdicts are checked
     against afterwards, never shown to it).
  3. A **person's check** vs **agreement with blind model readers** (cheap, but can share the judge's bias).
  4. **Built** (the calibration step, the owner packets) vs **run** (no label yet on the current game).
- **What the evidence establishes:** the day-summary and extraction rubric judges flagged gross faults but
  their presence-type dimensions sat at or near the maximum, and version differences were inside
  run-to-run variation, so design calls were made on other grounds; the census reader (yes/no against a fact
  sheet built by code) was checked by a person on the earlier nine-player game; the echo gate held 10 of 29
  restatements and 0 of 36 worthwhile lines against four blind model readers; the opening filter, before a
  fix, held lines readers judged worth hearing (6 of 7).
- **What stays uncertain:** why the presence-type scores stayed high is the records' explanation (the
  generator's prompt forced the section), not a tested cause; the 18 pairs were not stratified by
  difficulty, so easy days may also have lifted the scores; the version-to-version noise mixes generation
  and judging (the harness regenerated each time); no current-game judge or classifier has a person's
  check; the opening filter is unmeasured since its fix; judges and players now default to the same model.
- **Stays off the page:** from the Handle-with-care list: say the labelling packets *enable* the human check
  and the gap closes only when labels are done and acted on; "no person has checked the current game's
  judges yet" is the central open gap, explained here briefly; no AI-written-test, CI, missing-script or
  uncommitted-run bookkeeping; no "+17pp" or 0.14%. Memory *results* stay in the Memory chapter (this page
  uses the memory judges only as judges). From the records: the missing echo-gate runner script, the
  extraction prompt's eight-vs-five self-contradiction and the retrieval-judge fallback bug stay off.

## Evidence selection

**Core argument, before examples or numbers:**

1. Code first: a model is the right reader only when the question is about meaning, there are too many
   items to read, and its answers can be checked against something outside it. Without that check its
   number is a smoke alarm (it can flag a gross fault) but not a gauge (it cannot rank close versions).
2. Judges serve two uses with different stakes: measuring outputs offline, and classifying inside the live
   game, where the label changes what players hear.
3. A broad 1–5 rubric fails in a specific way: a dimension that checks whether something exists rewards
   whatever the generator was told to produce, so it sits at the top; the dimensions that compare content
   against the source do move, but only on gross faults; and differences between versions fall inside the
   run-to-run variation. So a high score cannot say which version is better.
4. A narrow judge works for the opposite reasons: one yes/no question, the facts handed over (built by code),
   a written rule for what counts, the evidence quoted with the verdict. The reference it decides with
   must itself be right.
5. A judge's number means something only once it is anchored: a person labels a blind, stratified sample;
   the judge is scored against it with a bar set beforehand; re-judging the same outputs measures the noise
   floor; controls catch over-flagging; and reading verdicts finds faults in the judge itself. Re-check
   when the judge's model or rubric changes. Blind model readers are a cheaper first check, not a substitute.
6. A classifier inside the game also has to make its mistakes cheap: fail open, never judge a human, and be
   measured for the mistakes it still makes (fail-open covers errors, not wrong but valid labels).
7. Current state: the best-checked judges were checked on the earlier game; today's judges and classifiers
   rest on model readers or nothing; the next step is the owner's labels through the built calibration step.

| Essential concept | Selected evidence (source), if needed | Why this example earns space | Alternatives omitted / destination |
|---|---|---|---|
| 1. When a model is the right reader | The three conditions; the census screening by code first (llm_judge/report.md workflow §1) | States the selection criteria the featured story violates; "smoke alarm" defined here | The five-row "anchoring situations" table (experiment_log §5): notes |
| 2. Two uses | The echo gate holds a line; a measuring judge only reports (report.md intro) | One sentence each; the live-classifier section depends on it | Dedup decision as a product classifier: memory chapter |
| 3. Featured: high, flat scores | **Exhibit LJ-rubric:** DAY_SUMMARY_RUBRIC dimension 4 (village dynamics), level 5 text, beside "5.00 on every pair, run, model and version" and the generator prompt that required the section (prompts/day_summary.py; day_summary.md L2 pt 2; day_summary/experiment_log ②). **Exhibit LJ-flat-scores:** a three-row table of what each May change did to completeness (word limit 4.44→4.39; structured output 4.44→4.50) and what decided instead (reverted on word counts 130–230; kept for architecture; model chosen by reading failures and latency, ~120 vs ~10 min). Noise: ±1 per pair between runs of the same prompt vs −0.11/−0.22 deltas (log ②; day_summary.md pt 3). Grounded dimensions caught dropped accusers, a fabricated game-master announcement, confirmed-vs-claimed errors as 1–3 scores. Extraction: original five dimensions clustered at 4.00 over 48 games, the two added ones did not (extraction.md (a)) | The parent's promised failure story; the exhibits show the mismatch between what was asked and what was rewarded; extraction in one sentence shows it was not one judge's quirk | Extraction's two prompt bugs (−1.19, +0.69): notes (a second "reading found it" example); evidence-type 4.89–5.00: one clause at most; unstratified-sample caveat stays on page |
| 3b. What decided instead; rubric drift | Architecture and latency for the summary; the summary was later rebuilt so code checks its claims; the judge's rubric still scores the dropped section, so no current result rests on it (report.md case 5; day_summary.md status) | Shows the practical consequence and leads to "version the rubric with what it grades" | The rebuilt summary's own story: chapter on day summaries / factual errors page |
| 4. Narrow judge contrast | Census reader: a fact sheet built by code; yes/no naming the wrong fact; a cheap model set to over-flag and a stronger one re-reading; I checked the 90 flagged public messages; precision about 0.8 on 25 flagged notes; 2–3 missed in 15 rejections (report.md case 1, full record; factual_errors.md) | The judge with a person's check; contrasts point by point with the rubric judges | The 23-case golden set that chose the reader (labeller unnamed): notes; the 10-of-12 test-set verdicts: notes |
| 4b. Reference forms | Reference answer rejected (penalises correct but differently worded replies); per-case expectations for frozen test cases, with the sentinel example in one sentence (report.md workflow §2, case 1) | Shows the design choice of *what to give the judge*, and sets up "the reference can be wrong" | Day-summary transcript as reference: implicit in featured story |
| 4c. Rubric rules | Shared requirements text with the generator; written rule per criterion; verdict with its evidence; rubric versioned with the component (report.md workflow §3) | Turns the two cases into transferable rules | Full workflow list: evidence report |
| 4d. Scale choice, pairwise | Pairwise compares two query versions without the bunching; here it generated and judged in one pass, and a human-labelled retrieval set made the call (report.md case 6; scoring Layer 1) | Answers "narrow labels or pairwise?" and gives the fixed-outputs rule | NDCG/scale table: scoring report; page 5 |
| 5. Anchoring a judge | Procedure (30–100 items, stratified by verdict, blind, bar fixed beforehand; calibration step built, not yet run on real labels); noise floor 1–2 of 267 on the nine-seat test set; controls; reading verdicts caught a wrong expectation ("never claimed any role" on a day the speaker had claimed investigator) (report.md workflow §4; factual_errors experiment_log; labeling/config.py) | Explains how labels validate a judge; the wrong expectation shows a reference-based judge inherits its reference's errors | Kappa, McNemar, sample sizing, packets' contents: link to page 5 (reference labels), which owns them |
| 5b. Blind model readers | Stronger model labels a sample without seeing the judge's answer; catches disagreement, not a shared bias (report.md workflow §4 table) | Most current classifiers rest on this; needed to read section 6's numbers | Model-panel failure (37%): page 5's featured story, link only |
| 6. Live classifiers | Echo gate: decides whether an open-floor line adds anything; fails open; human seats and replies to a named player never reach it; held 10 of 29 restatements and 0 of 36 worthwhile lines against four blind model readers on 65 lines. Opening filter: allow-list; before a fix, 6 of the 7 lines it held were judged worth hearing; not measured since (report.md case 2; echo_gate.py; round_filter.py; experiment_log §9) | The measure-vs-act distinction made concrete; fail-open vs wrong-but-valid | Gate prompt versions (29%→18%), calibration method: conversation page (chapter 1) link; accusation tags (79% vs an unchecked judge), addressing classifier: notes |
| 7. Current state | Factual-error judges person-checked on the earlier game; current judges and classifiers checked by model readers or not at all; judges default to the players' model; owner packets ready for accusation tags, echo gate, factual-error judge (report.md "What the tables show", "What is missing" 6–7; labeling/report.md "Golden sets against what is deployed today") | The central open gap, stated with its next step | The full trust table and top-up list: evidence report |

No Level 3 is proposed. The reserve ("why the quality rubric could not rank versions") stays on Level 2: the
featured section needs the same excerpt and scores, and reconstructing them is one section's work, not a
substantial separate analysis.

## Argument outline

Structure: an approach page that follows the **successive questions** a builder asks: is a model the right
reader → what goes wrong with a broad rubric → what a working judge looks like → how you know it works →
what changes when its label acts inside the game → where things stand. Each section's finding is the reason
for the next question, as in example B; the featured failure sits second because it motivates every design
rule after it.

| # | Section | Reader understands afterwards | Selected example, if needed | Omitted / linked | Why the next follows |
|---|---|---|---|---|---|
| 0 | Opening (no heading) | Judges answer questions of meaning at a volume no person reads; two uses, measuring and acting in the game; the central answer in two sentences | — | Re-definition of a judge (parent has it) | The first decision is whether a model should judge at all |
| 1 | When a model is the right reader | Three conditions; code first where the record computes the answer; an unchecked judge is a smoke alarm, not a gauge | The census: code screens statements, the model reads what is left | Anchoring-situations table | The project's first judges lacked the third condition; what did that look like? |
| 2 | High scores that could not rank versions (featured) | The day-summary rubric asked for quality but rewarded presence of a required section (5.00 always); content dimensions caught gross faults; version changes moved scores less than run-to-run variation; decisions went to architecture, latency and reading; the same clustering in extraction; the rubric later outlived the format, so nothing current rests on it | Exhibits LJ-rubric and LJ-flat-scores; one sentence on extraction (4.00) | Extraction prompt bugs; per-run tables; the summary's later redesign (linked) | If broad scores could not decide, what does a judge that can decide look like? |
| 3 | Narrow questions with the facts handed over | The census reader as the contrast: one yes/no question, a fact sheet from code, the wrong fact named, a cheap over-flagging read then a stronger re-read, checked by me; what to give a judge (facts, per-case expectations, not a model answer); the rubric rules (shared requirements, a written rule per criterion, evidence with the verdict, versioned with the component); a 1–5 scale last, pairwise for relative questions but only on fixed outputs | Census reader with its check; sentinel expectation in one sentence; the pairwise query judge in two | Scales and scores: page 5 and evidence | A well-designed judge still needs evidence that its verdicts are right |
| 4 | Checking a judge against a person | Reference vs anchor; the check (blind, stratified, bar fixed beforehand, built but not yet run on real labels); noise floor (1–2 of 267); controls; reading verdicts finds faults in the reference (the wrong expectation); re-check after a model or rubric change; blind model readers as a cheaper first check that can share a bias | Wrong expectation; noise floor | Kappa, McNemar, sample sizes, packet design: link to [Building reference labels](../reference_labels/reference_labels.md) | Most judges inside today's game rest on that cheaper check, and their mistakes reach players |
| 5 | When the judge's label changes the game | Echo gate and opening filter: what each decides; designed so a mistake keeps a line (fails open; humans and direct replies never judged); fail-open does not stop a wrong but valid hold, which is why each is measured: gate 10/29 and 0/36 against model readers, filter 6 of 7 wrongly held before a fix and unmeasured since | Both classifiers, numbers with their reader type | Gate calibration and prompt versions: link to the conversation page; accusation tags: notes | Puts the open gap in view: which judges have a person's check today? |
| 6 | What is established and what remains open | Factual-error judges have a person's check, on the earlier game; today's game's judges and classifiers have model readers or nothing; they now default to the players' own model, so a run should name a different judge model; packets ready, gap closes when labels are done and acted on | — | Full trust table and top-ups: evidence report | — |

Check of main points in order: need → criteria → failure without the third criterion → what a working judge
does → how it is checked → stricter needs when it acts → current state. This answers the frame's question.
Term order: "rubric" (parent), "smoke alarm" (§1, used in §2), "noise" (explained in §2 through ±1 per pair,
reused as "noise floor" in §4), "reference" (§3) before "anchor" (§4), "blind model readers" (§4) before the
gate's numbers (§5). No section needs a later term.

Target length: about 1,700–1,900 words including the two exhibits.

**Drafted 2026-10-29 (step 4).** Page copy about 2,130 words (counting tables and captions, not markdown
symbols), above the target and the Level 2 guide's 2,000. The growth has two owner-requested sources: the
status table in §6 (about 110 words) and the echo-gate passage at about 250 words. Changes from the outline:
the sentinel expectation is cut to one clause (the full case is in the sources comment); the "village
dynamics" rubric excerpt and the version table carry their point in italic captions; the pairwise remark is
one sentence at the end of §3; the rebuilt-summary paragraph is shortened to its consequence. Skim
(headings, opening sentences, captions): the argument can be followed; §2's opening sentence gives context
rather than the point, which the heading and the first caption carry.

## Open questions

1. **Same-model configuration on the public page.** Since 2026-10-12, judges and players default to the
   same model (report.md "What is missing" row 7). It changes how to read any current judge number (a
   model may favour its own output). Affects §6. Default: one sentence as current setting plus the remedy
   (name a different judge model per run); no dates.
2. **"I" for the census check.** factual_errors.md and report.md say the owner read the 90 flagged public
   messages; the 25 flagged notes and 15 rejections are listed in the same row. Default: "I checked the
   flagged messages and a sample of rejected statements", matching page 1. The wrong-expectation hand read
   names no reader: written without "I".
3. **Mechanism wording for the 5.00 scores.** The records explain them by the generator's prompt forcing
   the section; nothing tested that cause. Default: present it as the explanation the scores fit, with the
   unstratified 18-pair sample beside it.
4. **Day-summary judge status.** report.md says "retire" as a top-up, the note says "should not be re-run as
   it is". Default: "no current result rests on it; its rubric still describes the old format", not
   "retired".

Questions 1–4 are settled for the draft: 1 by the owner's answer, 2–4 by the defaults (4 now uses the
status note's own words, "should not be re-run as it is").

**Raised by the review (2026-10-29), for the owner:**

5. **Echo-gate packet drawn from the calibration lines** (claims finding 13). The claims reviewer reports
   that the owner packet labels 50 of the same 65 lines the gate's bar was set on. Passing would confirm the
   bar against a person on its tuning lines, not on new lines. Worded cautiously ("on the lines its bar was
   set on"); the owner decides whether that clause stays, or whether fresh lines should be drawn.
6. **"Not yet re-checked on the model they use today"** (§4, from claims finding 1). True per the records
   (report.md case 1; labeling report row 3). It is a limitation that changes how to read today's
   factual-error numbers, so I kept it, but it sits close to bookkeeping. Owner: keep, or fold into the
   next-step paragraph.
7. **"I scored 18 transcript–summary pairs"** (§2). The records do not name who ran the May judge. Kept
   under the owner's first-person rule for uses; owner to confirm it was their run.
8. **Rubric excerpt's date.** The quote is from today's `evaluation/src/judges/prompts/day_summary.py`; the
   claims reviewer could not confirm it matches the May 2026 text (git history not read). The page presents
   it as the rubric, not as a dated May quote. Owner or verifier: check the file's history at the May runs.
9. **Opening filter's fix.** The page describes it from the silence-calibration README (the 2026-10-18 fix
   keeps every kind of night result). `Agents/turn/round_filter.py` has uncommitted changes in the working
   tree; whether the live filter is exactly the fixed one is a deployment question for the owner.

## Step 7 (skipped in this trial): what I would have changed

- Chapter `editorial_notes.md`: none exists for Evaluation; would create one or add the entry where the
  owner keeps chapter notes.
- Page header line: status and date after drafting.
- Parent section (`evaluation.md`, "Designing and validating LLM judges"): no Level 3 added, so no sync
  needed; recheck its wording if §6's same-model sentence is kept.
- `exhibits/source_map.md`: LJ-rubric and LJ-flat-scores from planned to drafted, with their exact sources.
- Chapter `editorial_notes.md` entry should record the claim changes from the review: the central answer
  narrowed (bunching partly on presence-type dimensions; version differences never shown to exceed rerun
  variation), the noise floor restated as the judge's own variation, the re-check rule stated as intended
  practice, and "editorially revised" is not "factually verified".
- Parent section (`evaluation.md`): its "scores clustered near the top and could not distinguish versions"
  still matches; no change needed.

## Review resolution

Reviews: `llm_judges.skill_2.review-editorial.claude.20261029T030542Z.Jl6VL5.md` (E) and
`llm_judges.skill_2.review-claims.claude.20261029T030916Z.qELWcI.md` (C).

| Reviewer | Finding (passage) | Action: explained / relocated / removed / corrected / declined (why) / flagged | Recheck needed? |
|---|---|---|---|
| E1 (blocking) | Census check: public messages checked but only note figures given; "its" ambiguous; "2 or 3" | Explained: says the final output of the two-stage screen was checked; public 68 of 90 flags real, notes about four in five of 25, two or three real errors in 15 rejections ("so the counts are lower bounds"); the range is the record's own count | No |
| E2 | Rule "grade what the output was required to do" reads as recreating the failure; "fell short on definition" contradicts the shown diagnosis | Corrected: rules reworded and tied to their cases (ask for content checkable against the source, not presence; keep the rubric in step, the day-summary judge's own copy); the "definition" clause removed | No |
| E3 | "Only the factual-error judges" vs expectation-judge row; accusation tags first appear in the table | Corrected: opening sentence names both factual-error judges and scopes to "the judges on this page"; tags row removed and the tags explained in one clause in the next-step paragraph | No |
| E4 | Procedure in present tense, "never run" only at the end | Explained: the paragraph now opens with "the planned check ... built ... not yet run", then describes it | No |
| E5 | Nine- vs ten-player game never introduced | Explained: one sentence opening §2 (the game grew from nine to ten players; a check on one version does not carry over). Reason for the addition: the status table depends on it | No |
| E6 | Expectation judge appears unnamed; example needs game rules | Explained: named where it first appears, tied to frozen-turn replays (parent's term); example kept (it is the recorded case) with the mechanic in one clause | No |
| E7 | One pair's swing compared with version averages | Corrected (with C3): says each version ran once, so the variation of an average was never measured; the one-pair swing kept only as what was observed | No |
| E8 | Opening filter's fix unexplained | Explained in one clause: the fix made it keep every kind of night result; its error rate since is unmeasured | No |
| E9 | "Memory-quality judges described next" vs a day-summary judge | Corrected: "the quality judges for day summaries and memory notes" | No |
| E10 (taste) | Third table row mixes units, unexplained settings | Agreed in part: column renamed "What the scores showed"; "medium thinking" and "lowest setting" removed. Row kept: it is the one case where the highest-scoring option was not chosen | No |
| E11 | Noise floor unit unclear | Explained: "judging the same 267 replies a second time changed the count of failing replies by 1 or 2" | No |
| E12 (taste) | Unclear whether a pairwise judge was tried | Agreed: says it was used, on two versions of the memory search query; still one sentence (owner limit) | No |
| C1 | "All of these checks are repeated" stated as practice | Corrected: "should be repeated"; adds that the factual-error judges are not yet re-checked on today's model (flagged, question 6) | Owner |
| C2 | "A smaller difference means nothing" overreaches | Corrected: re-judging measures the judge's own variation; version comparisons regenerate replies and need a paired test, not just a larger gap | No |
| C3 | "Stayed within run-to-run variation" asserts an unmeasured quantity | Corrected in the paragraph and the caption ("never shown to exceed") | No |
| C4 | Opening "mostly rewarded sections ..." overstated; extraction cause unknown | Corrected: opening now says scores bunched near the top, partly on presence-type dimensions, and version differences were too small to separate from rerun variation; extraction "bunched in a similar way", no cause claimed | Central claim narrowed; see second-review note |
| C5 | "Only ... made on the earlier game" conflicts with the hand-read ten-seat expectation verdicts; expectations listed as an anchor; earlier judge models omitted | Corrected: expectation row "every verdict read by hand before use; no agreement rate", game "current ten-player test cases"; census row adds "with the judge models of that time"; closing line narrowed to the echo gate, opening filter and tags. The nine-seat finding that the expectation judge was unreliable on the cheaper model is left off: no page number rests on those runs (noted in sources) | No |
| C6 | Different judge model does not apply to live classifiers | Corrected: "Offline judges such as the factual-error judge should also run on a model different from the players'" (still one sentence, no model names) | No |
| C7 | Smoke-alarm sentence mixes correctness and repeatability | Corrected: names both gaps (no outside check; no repeated runs on fixed outputs); "had neither" | No |
| C8 | "Change the rubric ..." presented as a rule in use | Corrected: framed as "the rules I take" from the contrast; the last rule says the day-summary judge did not follow it | No |
| C9 | "Every later decision about a past day relied on it" overstated | Corrected: "what they knew of it [the discussion] came from the summary alone" | No |
| C10 | "Rare and bounded"; own-role rule is a prompt instruction | Corrected: "limits where that second mistake can happen"; code-enforced rules separated from the prompt's instruction | No |
| C11 (owner?) | "Four blind model readers" reads as four per line | Corrected myself (wording, not a ruling): "blind model readers, one per line"; table says "Blind model readers" | No |
| C12 | "I rejected a single model answer" unsupported ownership | Corrected: "The factual-error judges do not compare a reply with a single model answer, because ..." | No |
| C13 (owner) | Echo-gate packet uses the lines its bar was set on | Worded cautiously ("on the lines its bar was set on"); flagged, question 5 | Owner |
| C14 | Pairwise "avoids bunching" unobserved here | Corrected: "is meant to avoid" | No |
| C15 | "Most classifiers ... rest on this cheaper check" | Corrected: "The echo gate and the opening filter rest on this cheaper check" | No |
| C16 | Reversed causation for "no current result rests on" | Corrected: "No current result rests on this judge, and because its rubric still asks for that section, it should not be re-run as it is" | No |
| C not-checked | Rubric text vs May version; evidence-type label in free-text versions; "I scored"; filter fix identity | Evidence-type sentence narrowed to "the summary's structured format required that label"; the rest flagged, questions 7–9 | Owner |

**Length after resolution:** about 2,310 words of page copy (letters/digits tokens, tables and captions
included), up from about 2,130 at draft and above the Level 2 guide of 2,000. Reasons per addition, all
reviewer-required: the game-version sentence (E5, about 35 words); the census result per statement type
(E1, about 40); the noise reasoning and the paired-test caveat (E7, C2, C3, about 40); naming the
expectation judge and the frozen-turn replays (E6, about 25); the re-check status (C1, about 20); the
filter's fix (E8, about 20); the accusation tags explained inline (E3, about 25). Offsets: tags table row,
the "added dimensions" clause, the model row's settings, the rules list and several sentences tightened.
Remaining overage is from the owner-requested status table and echo-gate passage (recorded at step 4).
The next cut, if wanted, is the extraction sentence and the pairwise sentence (about 60 words).

**Second review:** structure unchanged. The central claim in the opening was narrowed (from "mostly
rewarded sections the generator was told to write" to "bunched near the top, partly on presence-type
dimensions; version differences too small to separate from rerun variation"), following the claims
reviewer's own suggested scope. No new claim was introduced, so a full second review is not needed; a
claims-only re-run on §2 and §6 would confirm the narrowed wording if the owner wants it.
