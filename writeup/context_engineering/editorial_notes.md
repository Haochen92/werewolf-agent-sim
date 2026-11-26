# Context engineering editorial notes

## 2026-10-31 — Assessment fields and answer order

- Revised section 3 from the owner's fuller argument, retaining the existing numbered answer layout. Distinguished skipped assessments, answer order, diagnostic value of written records, and coherence versus vote quality.
- Checked the 75% / 87.5% / 92.5% comparison against `evidence/memory_system/effectiveness/decision_replay/experiment_log.md` coherence study, and 40% / 26% against its reorder study (memory-off arms). This corrects the earlier unqualified statement that reordering alone changed nothing.
- Described observable written assessments rather than asserting access to internal reasoning. Kept the next-section bridge scoped to selected missed implications, not a promise of better decisions. Source-checked these comparisons; no whole-page review implied.

## 2026-10-31 — Establish why earlier information is transformed

- Expanded section 2's opening to distinguish private continuity, compact shared discussion, and structured claims for code checks before introducing transcription failures. Updated Page 2's question, central answer, parent context and opening/closing outline rows to follow the same order.
- Explicitly retained full transcripts as a possible player input and stated the absence of a better-play comparison. Avoided implying that compact daily records give the entire prompt a fixed size.
- Checked the summary and ledger rationale against `evidence/extraction/day_summary/report.md` §§1–4 and 8; private-note continuity is already established in the chapter introduction. This focused explanatory edit is not a new whole-page editorial or factual review.

## 2026-10-31 — Explicit facts and visit direction

- Applied the owner's approved opening revision and request to identify the watch behind the visit-direction example. Renamed the subsection to name reconstruction and ambiguity.
- Replaced the conflated private-night-record explanation with the Illusionist's statement and the Investigator/Sentinel responses to the Sentinel's watch. Kept the separate self-visitor-list case distinct.
- Checked the incident and replacement rule wording against `evidence/gameplay/discussion_evidence.md` §8.6 and the separate concession result against `evidence/gameplay/turn_prompt/report.md` decision 4. The private-result rewrite remains material for L2.
- This local revision is source-checked for those claims; it does not constitute factual verification or editorial review of the whole chapter.

## 2026-10-31 — Owner-approved section 3 opening

- Applied the owner’s supplied section verbatim: establish the need for explicit assessments and diagnostic records before explaining required fields and answer order. Removed the compare-candidates paragraph as requested. Retained the navigation link.

## 2026-10-31 — Approved deduction section

- Applied the owner's approved revision of section 4: mechanism, permitted-information and decision boundaries, certainty wording, then three replay screens with limits. Replaced the earlier enforced-mode silence result with the supplied live-mode results and updated the source mapping. Removed L1 authorship as approved.
- Page 4 outline reviewed separately for proposed changes; no outline rewrite applied in this pass.

## 2026-10-31 — Page 1, Making facts available and unambiguous (first draft and review)

- Drafted `facts/facts.md` from the approved outline (`_authoring/l2_outlines.md`, page 1) as six
  successive questions: what the player had to reconstruct (the two board lines), what never reached
  the prompt (the code review and the night record), what a present line could mean (the reworded
  result), which rules went unstated (the visit rule and the ranking line, with the Illusionist case as
  the limit), whether printing sufficed (the July bundle, with its limits beside it), what is not
  established. The opening keeps "absent" and "present but needing reconstruction" apart.
- Exhibit change against the outline: §1's before/after is lifted whole from the investigator's
  as-played prompt in game `832404e9` (the game master's announcement and the two board lines from the
  same prompt) instead of the golden fixture's test board, so that §3's result line comes from the same
  game. Not an illustration; the wording matches today's formatters.
- Moved out or kept to a clause: the four-variant table and how the invented check was found
  (Evaluation's factual-errors page, linked); the three labelled blocks and the vote-note fix (page 2);
  why the reads precede the action (page 3); T2/T3 token counts and the coverage monitor (sources
  comment); the Sentinel beyond one sentence (parent); model names (sources comment).
- Claims checked against `turn_prompt/report.md` (decisions 1–4, "The board facts", "What is not
  established"), `discussion_evidence.md` §6.2, §8.4–8.6, `factual_errors/experiment_log.md` §2, §8–9,
  the rule text in `Agents/prompts/game_rules.py` and the formatters. Numbers lifted as they stand. The
  Illusionist limit keeps the clause that a smaller model stayed at 10 of 10 throughout.
- Reviewers: editorial (cold read with the parent excerpt; run on a scratch copy of the chapter in
  which the Level 1's placeholder "Explore" line carries the link, since the Level 1 was not to be
  edited) and claims (against the sources). Resolutions are in `facts.brief.md`.
- Claim changes from the reviews: the §4 limit no longer says a stated rule "guards the origin" and
  "does not undo" a repeated false rule; it gives the carried-kill replay's figures (first speaker 1 of
  5 → 0 of 5, too few to measure; later speakers 10 → 7 → 4 of 10 on one model, 10 of 10 on a smaller
  one), notes that the visit replay's repeated misreading did fall (11 → 3 of 20), and calls the reach
  of a correct rule into an existing cascade open. "The one comparison planned before its data" became
  "the most firmly planned" (T1b and T2 were planned too). The board's first test is scoped to the one
  recurring case. The ~3% is scoped to deaths, roles and who was left, as a floor. The 97 → 82 replay
  names its arm (earlier days re-summarised) and its model judge. "I wrote the missing rules in" became
  "the missing rules went in" (drafting authorship not recorded).
- Page copy after review: about 2,500 words, including about 200 of verbatim exhibits; over the
  1,200–2,000 guide for the reasons recorded in the brief's trial record.
- "Editorially revised" is not "factually verified": the claims review checked consequential claims,
  not every figure; the owner's read is pending.

## 2026-10-31 — Page 2 drafted: Carrying earlier days forward: the day summary and the claim ledger

*Entry for `editorial_notes.md`; written to a separate file because four pages were drafted concurrently.*

- First draft of `previous_days/previous_days.md` under the write-portfolio-page skill, from the outline approved
  in conversation on 2026-10-31 (`_authoring/l2_outlines.md`, Page 2). Explanatory path: what a new call lacks →
  why earlier days are condensed into fields (size decides that; claims that span days and must be set against
  the record decide the form) → the two lists the summariser writes, with the speaker's own claim fields as the
  first source and the summary as fallback → the three-block "Previous days" section a player reads, lifted
  whole, with its three authors → two cascade cases and the guard each produced (narration → attribution; the
  misread "I was roleblocked" → the ledger's self-block rule, with the first broader rule that dropped a true
  Vigilante claim and was caught by the summary replay) → why judging left the model (the subjective verdicts;
  the record check judged wrong 27 of 27 across 66 summaries) → replay checks and the runtime → what is not
  established, with the never-run transcript comparison as the one caveat at the close.
- Moved out or kept to notes: the "5 of 5 → 0 of 5" later-speaker figure (kept apart from the e06 replay in which
  the invented claim did not recur); the full ledger check list and formatter names; the rescue path's detail;
  tracing; population-rate numbers; model family names (in the sources comment only).
- Claim changes after the two fresh-context reviews: the bench figure for the attributed summary (36% → 31%)
  came off the page, because the record shows it measured the whole 2026-10-03 pass with the attributed summary
  on top (the arm isolating the re-summarised days is 32% → 31%); "what the town acts on is mostly claims" became
  "the evidence the town can test is claims", since no measurement supports "mostly"; "each summary that went
  wrong was frozen" became "the summary failures found … were frozen"; the rescue model is now "where one is
  assigned" (the house default has none); the ledger's fallback is per kind of field; the summary is "written
  for each day of one game and never carried into another" (the ledger, not the summary, is rebuilt each prompt);
  the day-4 acceptance is told as the summary being the likely route; the stronger-model judge is named as the
  stronger model itself beside the 18 of 30.
- Structural change from the editorial review: the speaker's own claim fields, which the e06 case depends on,
  now appear in sections 2 and 3 instead of section 5, so the page agrees with the parent's "each speaker states
  its own claims in fields" from the start. Both reviewers were re-run after that change.
- Checked while drafting: the two lifted exhibits against `day_summary/report.md` §2–§3; the e06 lines, the vote,
  the fix and the Vigilante regression against report §7, `discussion_evidence.md` §8.4,
  `phase3_summary_replay/README.md` and `Agents/rules/claim_ledger.py`; the 27 of 27 and the 66 summaries against
  `deduction/experiment_log.md` §3; the plans sub-list against `Agents/schemas/output.py`; the role gloss against
  the role sheet. The editorial reviewer's parent excerpt was built by hand because the Level 1 page's "Explore"
  line is not a Markdown link (the parent needs a real link when its placeholders are wired; not edited here).
- "Editorially revised" is not "factually verified": the claims review checked the consequential claims it lists,
  not every number, and the owner has not yet read the page.

## 2026-10-31 — Page 3, "Making assessments explicit and testing how they shape decisions" (first draft)

*Entry written to `turn_request/_authoring/` because four pages were drafted concurrently; to be merged
into `editorial_notes.md`.*

- **Explanatory path.** Purpose first (tell a missed clue, a misapplied lesson and a decision against
  the written assessment apart), the design named once as an explicit, structured chain of thought
  written as fields, scoped to the written record and not the hidden reasoning tokens. Then: what the
  four fields let an investigator see, on the roleblocked healer's frozen turn; how the requested
  assessment was got into the answer (required verdict field, "no" as a value, fields only when they
  apply); where it sits relative to the action (the July reads, the October schema reorder), with order
  compliance kept apart from decision quality; the compare-candidates test as the main case; the
  night-1 lot and the example's named seat as a separate failure class; thinking effort as a separate
  lever; the untested combination at the close.
- **What moved out.** The reply brief's "As I said" result, the first vote-reason wording, the
  per-player vote layout, the 1–5 judge scores from May, all p-values, model names and versions, the
  tactical-advice audit's numbers (decision 7 kept to one sentence per the owner's ruling), the output-mode
  story (chapter 6), the uptake and silence results on the healer (page 4 and the Level 3), the layout's
  participation and cost figures (chapter 6). The outline's "other calls" pointer was cut to the dedup
  judge alone (cut list item 4).
- **Claim scope.** The page states that the action follows the written reasoning, not that reasoning
  improved. The §1 exhibit is labelled as one replay sample of the frozen turn on the unchanged prompt,
  not the game's own answer (the frozen case keeps the state before the turn, not the reads the game
  wrote). The thinking-study counts are the enforced-mode run's, with the live-mode re-run named in a
  clause (122 of 158 against 97 of 157). The suspicion-cue removal is "kept on principle", with its
  confound stated. The lot's rule is stated as the rule it set, not a law of models.
- **What was checked.** Every number lifted from the named sources and mapped in the page's sources
  comment: `turn_prompt/report.md` decisions 5–12 and 15, `turn_prompt/experiment_log.md` §3, §7, §11,
  `caching/experiment_log.md` §12, §16, `discussion_evidence.md` §6.7, §7.5, §8.6, §8.7, the
  decision-replay log, `deduction/report.md` §2 and §5, `deduction/experiment_log.md` §2, §4, §5, §9,
  and the deduction-injection case data.
- **Reviews.** Two editorial runs and one claims run in fresh contexts with the `claude` CLI (the
  second editorial run after §4 gained its cast and baseline and §5 took the suspicion-cue paragraph).
  Material changes from review: the cast, the eleven ballots and the minority-draw baseline before the
  compare-candidates result; "helped" moved from the 13 → 17 votes to the 11 vs 2 citations; the
  0.27 → 0.97 measure restated as the share of answers giving one verdict per item, credited to the
  instruction's move with the forced field already present; the verdict lists named as the exception to
  the all-required rule; the exhibit's night-record clause and mode stated; 267 as 89 cases × 3; the
  cite-exactly result scoped to its earlier model and setting; the dedup pointer corrected to input
  order. The editorial runs used a scratch copy of the chapter in which the Level 1's placeholder "Explore" line was
  given this page's link, since the real Level 1 (not edited) carries no link yet. Findings and actions
  are in the brief's Review resolution table. "Editorially revised" is not "factually verified".

## 2026-10-31 — Page 4 first draft: the deduction engine

*Entry for the chapter's `editorial_notes.md`; written beside the page because four pages were drafted
concurrently. To be merged.*

- Drafted `deduction_engine/deduction_engine.md` from the approved outline (`_authoring/l2_outlines.md`,
  page 4, revised twice on 2026-10-31). Explanatory path: the failure class and the cost rationale →
  the healer's turn followed through the engine (the seat's view, mechanics as role traits, the solver
  with one illustrative propagation table, the two printed lines) → the three grades, the contradiction
  case and why the grade is in the wording → the two boundaries (independence from hidden information,
  named a metamorphic test after the words, with the owner's Alice/Bob table labelled an illustration;
  consequences against advice, with one cover line beside one card sentence) → three replay screens in
  one table with comparison and limit, then the higher-thinking and larger-model results as the limit on
  where the engine adds value → scope, coverage, unmeasured effects and the one authorship sentence.
- Moved out: the four pre-engine attempts (notes), the acceptance-case seat block (notes), the eight
  levels (one sentence and a link), the enforced-mode uptake result, the carried-note 2×2, placement
  screens and the vote case (the planned Level 3, linked beneath §5), the rest of the test suite
  (Evaluation's code-checks page), the output-mode story (chapter 6), the bundled games' detail
  (chapter 1).
- Claim handling: the healer's 2 → 8 of 10 is stated as the engine against the game's original night
  record, not one line isolated; the enforced-mode "none spoke" appears once, with its date, mode and
  wording, and the speaking difference is attributed to neither the mode nor the extra lines; the Sentinel row keeps the downstream effect unresolved; the cover counts are
  exploratory (different judges per arm); the wolves' 3 of 8 is not attributed; "checked", never
  "proved"; no model family names; the rationale is cost, not necessity. The authorship sentence stays
  on this page per the outline, pending the owner's confirmation (brief, open question 1).
- Checked against `deduction/report.md` §1–§5 and its 2026-10-30 note, `experiment_log.md` §2, §4, §5,
  §8, §9, the catalogue §0 and AC1, `visit_wording_ab/README.md` arm C, `roles/report.md` decision 11
  and the paired games, and the live wolves' card. Numbers lifted as they stand.
- Reviews: editorial and claims (fresh contexts, `claude` CLI), two rounds each; resolutions in the
  brief's Review resolution table. Material changes from review: §5 now states what each arm received
  (only the healer row turns the engine off; the Sentinel and cover rows add a line to a running engine);
  §2 separates the direct rules from the solver and places the healer's lines in the first; §3 presents
  the grade as two dimensions; §1 dates the "cheaper route, not the only one" evidence as a later check
  on the same turn; the seat view lists wills, not votes; the counter-claimant line moved to notes
  because its record calls it a true fact dropped for not moving votes toward the truth. The Level 1's "Explore" line is not a markdown link, so the
  editorial reviewer's parent excerpt was supplied by a patched copy of the runner outside the repo
  that matches that line; the Level 1 page was not edited.
- "Editorially revised" is not "factually verified": the claims review checked consequential claims
  against the sources, not every number; owner review pending.
