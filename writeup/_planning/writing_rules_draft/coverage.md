# Coverage of the existing writing rules (draft, 2026-11-17)

> **Snapshot, not maintained (2026-11-17).** This is an inventory of the rules in the old guides, made the
> morning the short guides were drafted. No writer or agent needs to read it. Its statuses refer to the
> first draft of `core_rules.md`, which has changed since. The rulings on the ten contradictions listed
> below are now written in `core_rules.md` and `voice.plain.md`. Its remaining use: if the long guides are
> ever deleted, check the "reference only" rows first.


This table lists each distinct rule or requirement in the existing writing guidance and says where it
would sit if `core_rules.md` were adopted. It is a proposal; the owner decides. No existing file was
changed.

**Files covered, with the row prefix used for each:**

| Prefix | File |
|---|---|
| SG | `evidence/experiment_report_style_guide.md` |
| WR | `.claude/skills/write-report/SKILL.md` |
| PS | `.agents/skills/write-portfolio-page/SKILL.md` |
| V | `.agents/skills/write-portfolio-page/references/voice.md` |
| PW | `.agents/skills/write-portfolio-page/references/portfolio-writing-prompt.md` |
| L2 | `.agents/skills/write-portfolio-page/references/portfolio-level-2-writing-prompt.md` |
| L3 | `.agents/skills/write-portfolio-page/references/portfolio-level-3-writing-rubric.md` |
| PT | `.agents/skills/write-portfolio-page/references/page_types.md` |
| EX | `.agents/skills/write-portfolio-page/references/examples.md` |
| BT | `.agents/skills/write-portfolio-page/references/brief_template.md` |
| ED | `.agents/skills/write-portfolio-page/reviewers/editorial.md` |
| CL | `.agents/skills/write-portfolio-page/reviewers/claims.md` |

"CR n" means rule n of `core_rules.md`.

**How I merged rows.** Two rules share a row only when they say the same thing in substance. When a
later file restates an earlier rule, the restatement gets its own row with the status `duplicate of`,
so the owner can see every place a rule lives. The style guide's 31-item checklist restates rules
from its body; I gave a row only to the two checklist items that add something new (SG-97, SG-98),
and the other 29 are counted under the body rows they repeat.

## Count summary

| Status | Rows |
|---|---|
| in core_rules | 35 |
| reference only | 229 |
| duplicate of another row | 117 |
| conflicts with another row | 14 (ten conflicts, K1–K10; most have a row on each side) |
| proposed for removal | 3 |
| **Total** | **398** |

By file: SG 98 rows, WR 39, PS 34, V 22, PW 59, L2 57, L3 33, PT 13, EX 15, BT 4, ED 11, CL 13.

## Conflicts (these need a ruling)

| # | Rows | What conflicts |
|---|---|---|
| K1 | SG-14 vs WR-06 | The style guide ranks the goals as: a persuasive account of the contribution, then first-read clarity, then relevance and proportion, then length, with accuracy as a constraint on all four. The write-report skill says it is applying "its goal ranking" but gives a different list: accuracy, first-read clarity, no repetition, length. |
| K2 | SG-62 vs SG-17, SG-55 | "Reflect, don't narrate" asks for one sentence on what each major finding means after every major finding. The Core Principle says not to "append a generic lesson when the judgment is already clear", and the Lessons section says to include lessons only when they add insight. |
| K3 | SG-84 vs V-09, WR-19 | The anti-pattern "fait accompli" says "Show the path" for reports in general. Voice rule 9 says to explain the finding and not retell the investigation, and write-report says a report body must never read chronologically. They probably mean different document types (journey log versus report or page), but SG-84 does not say so. |
| K4 | V-05 vs SG-45, SG-54, SG-63 | Voice rule 5 says always "I", never "we". The style guide's templates and examples use "we" ("we had X, but not Y", "We chose v2 …", "We initially assumed …"). It is not stated whether evidence reports may use "we". |
| K5 | WR-30 vs V-17 | Write-report asks the writer to answer the reader's objection inline, with headings such as "Why a tiered score, and not a flat blend or a plain decision tree". Voice lists "defensive negations" and "rhetorical question-and-answer" as habits to remove. The boundary between answering a real objection and a defensive negation is not drawn. |
| K6 | SG-55 vs L2-09 | The style guide asks for lessons "stated as a transferable principle, not a project-specific observation", and its second good example is itself a compressed maxim ("fields generated before the action become prospective commitments, fields after become retrospective rationalizations"). The Level 2 prompt says to avoid universal rules drawn from a few cases and to say what to inspect next instead. |
| K7 | WR-34 vs SG-20 | Write-report says reading contracts and remarks about the document are residue and must be replaced by a short orientation block. The style guide requires a journey log's header to state "the rule that later entries supersede earlier ones", which is a reading contract. |
| K8 | PW-58 vs EX-01, L2-01 | The general portfolio prompt says to use the Level 2 and Level 3 reference pages as examples only after the owner approves them. `examples.md` tells the writer to read examples A and B, which are drafts the owner preferred but did not approve, and C, which it says is not verified. The Level 2 prompt is itself built on an unapproved draft. |
| K9 | SG-12 vs SG-06 | "The Reader" says the reader knows the technique and the report should "explain *our* system, not the field". "Read this first" says to explain the standard technical term in plain words the first time it appears. A ruling is needed on whether a report defines standard terms that its reader is assumed to know. |
| K10 | WR-14 vs V-14 | Both say a mechanism that no test isolated is a hypothesis. Write-report asks for the label "one plausible reading:", and voice asks for the word "suspected". One label should be chosen. |

Outside the files in scope: SG-60 says to move artefacts generated elsewhere (for example in
`eval_results/`) into the evidence folder and clean up the originals. `CLAUDE.md` describes
`evaluation/eval_results/` as part of the live data plane. These may conflict; I marked SG-60
`reference only` because the other rule is outside these files.

## Proposed for removal

| Row | Rule | Reason |
|---|---|---|
| SG-76 | "Prefer a plain sentence to an aphorism": second clause, "then crystallize it only once it is already clear" | Superseded by "Read this first" rule 5 (2026-11-17) in the same file, which keeps a short sentence only if its meaning is already literal, and which says it wins any conflict. |
| SG-95 | Anti-pattern "Aphorism density": "One or two land … crystallize only what earns it" | Same reason as SG-76; its first half is a duplicate of SG-04. |
| L2-53 | The second block "Three interpretation checks, applied sentence by sentence" | It repeats the three checks given a few lines earlier in the same prompt (universal wording, competing explanations, caveat reversal) almost word for word. |

## Full table

| Row | Where | Rule, in one plain sentence | Origin stated | Status |
|---|---|---|---|---|
| SG-01 | SG, Read this first, "The rule" | The goal is the least effort for the reader per idea, not the fewest words. | owner ruling 2026-11-17 | in core_rules (opening) |
| SG-02 | SG, Read this first | When clear and short conflict, choose clear; the rules on cutting filler never justify packing more into the remaining sentences. | owner ruling 2026-11-17 | in core_rules (tie-break) |
| SG-03 | SG, Read this first, item 1 | Say who or what does the action, what it acts on and what happens. | owner ruling 2026-11-17 | in core_rules (CR 1) |
| SG-04 | SG, Read this first, item 2 | Use words in their literal meaning; no figure of speech or phrase invented for the document. | owner ruling 2026-11-17 | in core_rules (CR 2) |
| SG-05 | SG, Read this first, item 3 | State the cause and the consequence; leave no step for the reader to work out. | owner ruling 2026-11-17 | in core_rules (CR 1) |
| SG-06 | SG, Read this first, item 4 | Use the standard technical term and explain it in plain words the first time. | owner ruling 2026-11-17 | in core_rules (CR 5) |
| SG-07 | SG, Read this first, item 5 | Keep a short memorable sentence only if its meaning is already literal. | owner ruling 2026-11-17 | in core_rules (CR 2) |
| SG-08 | SG, Read this first, "The check" | Give the finished text alone to a fresh reader, collect sentences read twice and non-literal words, and reword each one. | owner ruling 2026-11-17 | in core_rules (CR 13) |
| SG-09 | SG, Read this first, layout | In a table comparing two or three things, put the things in rows and their properties in columns. | owner ruling 2026-11-17 | reference only |
| SG-10 | SG, Read this first, layout | Group a long list under two or three named goals or decisions. | owner ruling 2026-11-17 | reference only |
| SG-11 | SG, Purpose | A report covers one experiment or segment and makes an evidence-backed case; select the strongest material rather than catalogue everything. | — | reference only |
| SG-12 | SG, The Reader | Write for an engineer who knows the technique but not the project; explain our system, not the field. | — | conflicts with SG-06 (K9) |
| SG-13 | SG, The Reader | Keep claims supported, and distinguish measured results from expected benefits. | — | in core_rules (CR 4) |
| SG-14 | SG, The Reader | Rank goals: persuasive account, first-read clarity, relevance and proportion, then length. | — | conflicts with WR-06 (K1) |
| SG-15 | SG, The Reader | Accuracy does not need every abandoned idea, but keeps any qualification whose removal would change the reader's conclusion. | — | in core_rules (CR 7) |
| SG-16 | SG, The Reader | Revising a document is a structural edit: rewrite paragraphs whole, move sections, delete repeats, give unequal space to unequal weight. | — | reference only |
| SG-17 | SG, Core Principle | Make the engineering judgement visible, using the shape that fits (experiment, architecture, debugging); do not force a failure story or append a generic lesson. | — | reference only |
| SG-18 | SG, Document Types | Pick one of five document types and use its skeleton. | — | reference only |
| SG-19 | SG, Document Types | Experiment report skeleton: Motivation → Design → Iterations → Setup → Results → Decision → Lessons → Next → Artefacts. | — | reference only |
| SG-20 | SG, Document Types, journey log | A journey log opens with an orientation header (what it is, later entries supersede earlier ones, companion docs), closes with a sources footer, and runs the loop ①–④ between them. | — | conflicts with WR-34 (K7) |
| SG-21 | SG, Document Types, journey log | The loop is a menu, not a mandate; a short log may use only some sections. | — | reference only |
| SG-22 | SG, Document Types | Decision record skeleton: tension → principle → rejected alternatives with reasons → decision and named trade-off → lessons. | — | reference only |
| SG-23 | SG, Document Types | A negative finding is first-class; its skeleton ends by stating what would change the verdict. | — | reference only |
| SG-24 | SG, Document Types | Reference doc skeleton: orientation line → guarantee → mechanism → verification → evidence (verdict first) → limits only where needed. | — | reference only |
| SG-25 | SG, Discipline for reference docs | A claim about how a framework behaves carries a version pin, and a test where the document depends on it. | — | reference only |
| SG-26 | SG, Discipline for reference docs | Include only current, consequential limitations, checked to still exist; severity labels belong in a risk register. | — | reference only |
| SG-27 | SG, Discipline for reference docs | In a case study, give the verdict first and the forensic detail after. | — | reference only |
| SG-28 | SG, Discipline for reference docs | Pitch at the busy reader's level; when two statements conflict over an unimportant mechanism detail, delete the over-specific one instead of reconciling it. | — | reference only |
| SG-29 | SG, Discipline for journey logs | An earlier section must not know a later result; show a falsified design in place. | — | reference only |
| SG-30 | SG, Discipline for journey logs | Argue each point once; later sections point back to it. | — | reference only |
| SG-31 | SG, Discipline for journey logs, ① | Be charitable to the design being replaced, and end the motivation on the root cause. | — | reference only |
| SG-32 | SG, Discipline for journey logs, ② | State the design's mechanics before its benefits, show rejected alternatives, state benefits as expected rather than validated, and map a replaced design's weaknesses one to one. | — | reference only |
| SG-33 | SG, Discipline for journey logs, ③ | Present each refinement problem first, then the fix, and close with a short provenance line. | — | reference only |
| SG-34 | SG, Discipline for journey logs, ③ | Every probe names the one risk it isolates. | — | reference only |
| SG-35 | SG, Discipline for journey logs, ③ | A killed approach is shown, diagnosed and traced, never deleted. | — | reference only |
| SG-36 | SG, Discipline for journey logs, ④ | Keep historical uncertainties with the decision they affected; do not copy them all into a present-day limitations list. | — | reference only |
| SG-37 | SG, Limitations and scope | Lead with the supported contribution, then qualify its reach. | — | reference only |
| SG-38 | SG, Limitations and scope | Include a limitation only if you can name the claim it qualifies and how the reader would misread it without it; no required number of limitations. | — | reference only |
| SG-39 | SG, Limitations and scope, table | Treat each kind of limitation as the table says (evidence limit, current defect, accepted trade-off, optional optimisation, resolved incident). | — | reference only |
| SG-40 | SG, Limitations and scope | Name the exact missing evidence instead of calling a system "untested". | — | in core_rules (CR 4) |
| SG-41 | SG, Limitations and scope | Keep process claims as specific as the evidence; one evaluated change is not "every change is tested". | — | in core_rules (CR 4) |
| SG-42 | SG, Limitations and scope, Avoid/Prefer table | Use direct, proportionate wording for missing evidence. | — | duplicate of SG-40 |
| SG-43 | SG, Limitations and scope | Do not repeat a caveat across sections; keep a serious one visible wherever a headline alone would mislead. | — | in core_rules (CR 7) |
| SG-44 | SG, Limitations and scope | Do not turn accepted uncertainty into a promised task; say "planned" only when it is. | — | reference only |
| SG-45 | SG, Structure §1 Motivation | Frame the motivation as a gap ("we had X, but not Y …") in one paragraph, and say what each component does before naming it. | — | reference only |
| SG-46 | SG, Structure §2 | State the approach, briefly the rejected alternatives, and the hypothesis of the first version. | — | reference only |
| SG-47 | SG, Structure §3 Iterations | For each iteration give what changed, why, and what happened; each version follows from the previous one's findings, not a flat list. | — | reference only |
| SG-48 | SG, Structure §3 | A one-shot structural redesign is reported as one decision and its A/B, not a forced v1→v2→v3 chain. | — | reference only |
| SG-49 | SG, Structure §4 | Keep the evaluation setup factual and short; explain any metric added partway. | — | reference only |
| SG-50 | SG, Structure §5 | State the headline before a table, address surprises after it, and show results both ways when an outlier or confound mattered. | — | reference only |
| SG-51 | SG, Structure §5 | State N with the result and separate direction from magnitude; write the limitation, not a shorthand grade. | — | in core_rules (CR 4) |
| SG-52 | SG, Structure §5 | Distinguish measurements, estimates and implementation status. | — | in core_rules (CR 11) |
| SG-53 | SG, Structure §5 | Never let a table speak for itself. | — | reference only |
| SG-54 | SG, Structure §6 | State the choice and why; explain material trade-offs; do not manufacture a drawback. | — | reference only |
| SG-55 | SG, Structure §7 Lessons | Include a lesson only when it adds insight, stated as a transferable principle grounded in evidence. | — | conflicts with L2-09 (K6) |
| SG-56 | SG, Structure §8 | "What's next" is optional; separate commitments from ideas and state conditions. | — | reference only |
| SG-57 | SG, Structure §9 | Give a factual table of artefacts. | — | reference only |
| SG-58 | SG, Structure §9 | Stamp provenance: git SHA or runtime fingerprint, config, input datasets. | — | reference only |
| SG-59 | SG, Structure §9 Placement | Keep in the prose the numbers needed to assess a claim; move configs, raw records and commit identifiers out of the sentence. | — | reference only |
| SG-60 | SG, Structure §9 | Co-locate supporting artefacts in the evidence folder; move ones generated elsewhere and clean up originals. | — | reference only (possible conflict with `CLAUDE.md`, see note above) |
| SG-61 | SG, Structure §9 Pointer discipline | Cite code by console-entry names or package paths; deep `file:line` anchors only where the line is the point; frozen scripts carry a FROZEN RECORD header. | — | reference only |
| SG-62 | SG, Tone and Style | After each major finding, add one sentence on what it means or what you would do differently. | — | conflicts with SG-17, SG-55 (K2) |
| SG-63 | SG, Tone and Style | Present a corrected assumption as a finding. | — | reference only |
| SG-64 | SG, Tone and Style | Without downstream metrics, describe what became observable instead of claiming impact. | — | reference only |
| SG-65 | SG, Tone and Style | Explain material trade-offs in context; do not invent a sacrifice. | — | duplicate of SG-54 |
| SG-66 | SG, Tone and Style | Keep tables interpreted: takeaway before, surprises after. | — | duplicate of SG-50 |
| SG-67 | SG, Tone and Style | Avoid pure fact lists; say what each challenge taught. | — | reference only |
| SG-68 | SG, Prose legibility (intro) | Concision means cutting filler, not compressing what remains. | — | in core_rules (tie-break) |
| SG-69 | SG, Prose legibility | One main idea per sentence, one reasoning step per paragraph, subject and verb close together. | — | in core_rules (CR 3) |
| SG-70 | SG, Prose legibility | Say what a component does before using its name. | — | in core_rules (CR 5) |
| SG-71 | SG, Prose legibility | Replace vague evaluations with the observation or the limitation. | — | in core_rules (CR 9) |
| SG-72 | SG, Prose legibility | Unpack stacked hyphenated modifiers into clauses. | — | in core_rules (CR 3) |
| SG-73 | SG, Prose legibility | Use about one em-dash per paragraph at most. | — | reference only |
| SG-74 | SG, Prose legibility | Introduce shorthand before relying on it. | — | duplicate of SG-70 |
| SG-75 | SG, Prose legibility | Prefer a plain sentence to an aphorism. | — | duplicate of SG-04 |
| SG-76 | SG, Prose legibility | Crystallise a point into a short sentence once it is already clear. | — | proposed for removal |
| SG-77 | SG, Prose legibility, Exemplar | Writers imitate the prose they see, so the guide should be written in the voice it asks for. | — | reference only |
| SG-78 | SG, Plain presentation 1 | Ask each part's question in plain words and answer it first, in a bold line. | 2026-10-22 | in core_rules (CR 8) |
| SG-79 | SG, Plain presentation 2 | Give context (what, against what, how) before the number. | 2026-10-22 | in core_rules (CR 6) |
| SG-80 | SG, Plain presentation 3 | Prefer counts a reader can picture to fitted coefficients; put a fit in a box after the counts. | 2026-10-22 | in core_rules (CR 6) |
| SG-81 | SG, Plain presentation 4 | One comparison per table. | 2026-10-22 | reference only |
| SG-82 | SG, Plain presentation 5 | State findings apart from a short "how sure we are" list. | 2026-10-22 | reference only |
| SG-83 | SG, Plain presentation 6 | Inside a kept finding nothing is lost: check every number, N and caveat item by item; keep a finding only if key to today's design or a unique skill. | 2026-10-22 | reference only |
| SG-84 | SG, Anti-patterns | Do not present the final design as obvious from the start; show the path. | — | conflicts with V-09, WR-19 (K3) |
| SG-85 | SG, Anti-patterns | No orphaned tables. | — | duplicate of SG-53 |
| SG-86 | SG, Anti-patterns | Do not bury corrections. | — | duplicate of SG-63 |
| SG-87 | SG, Anti-patterns | No claimed impact without evidence. | — | duplicate of SG-64 |
| SG-88 | SG, Anti-patterns | No limitations inventory. | — | duplicate of SG-38 |
| SG-89 | SG, Anti-patterns | Do not overstate a gap. | — | duplicate of SG-40 |
| SG-90 | SG, Anti-patterns | No universal process claims. | — | duplicate of SG-41 |
| SG-91 | SG, Anti-patterns | Do not bury the achievement under caveats. | — | duplicate of SG-37 |
| SG-92 | SG, Anti-patterns | No flat iteration lists. | — | duplicate of SG-47 |
| SG-93 | SG, Anti-patterns | Lessons must generalise. | — | duplicate of SG-55 |
| SG-94 | SG, Anti-patterns | Density is not concision; this is the most common failure in practice. | — | duplicate of SG-69 |
| SG-95 | SG, Anti-patterns | A page of maxims exhausts the reader; crystallise only what earns it. | — | proposed for removal |
| SG-96 | SG, Checklist (29 items) | The remaining checklist items restate body rules. | — | duplicate of the body rows they restate |
| SG-97 | SG, Checklist | A reader who skips the tables should still follow the narrative from the prose. | — | reference only |
| SG-98 | SG, Checklist | Check that no historical finding has drifted into a current or universal claim; date, scope or cut it. | — | reference only |
| WR-01 | WR, Step 0 | Pick the document type first. | — | duplicate of SG-18 |
| WR-02 | WR, Step 1 | Read the whole guide, then the discipline block for the type. | — | reference only |
| WR-03 | WR, Step 2 | Read the matching exemplar in full (list given). | — | reference only |
| WR-04 | WR, Step 3 | Write an argument brief before drafting and get it confirmed if none was supplied. | — | reference only |
| WR-05 | WR, Step 3 | The brief records which evidence carries each claim and what is excluded and why. | — | reference only |
| WR-06 | WR, Step 3 | Apply the goal ranking accuracy → first-read clarity → no repetition → length. | — | conflicts with SG-14 (K1) |
| WR-07 | WR, Step 3 | A revision is a structural edit, with a plan for what moves, merges and is cut. | — | duplicate of SG-16 |
| WR-08 | WR, Step 4 | Lift verdicts, statuses and numbers from the cited evidence; never re-derive them. | — | in core_rules (CR 11) |
| WR-09 | WR, Step 4 | State N; separate direction from magnitude at small N. | — | duplicate of SG-51 |
| WR-10 | WR, Step 4 | Stamp provenance. | — | duplicate of SG-58 |
| WR-11 | WR, Step 4 | Cite code by stable handles. | — | duplicate of SG-61 |
| WR-12 | WR, Step 4 | For a retracted claim, cite the correction, never the original headline. | — | reference only |
| WR-13 | WR, Claim-calibration | Scope each verdict to what was tested (store version, epoch, faction, N, instrument); a null reads "no detected effect at this power". | owner's markup 2026-07-06 | reference only |
| WR-14 | WR, Claim-calibration | Label a mechanistic explanation "one plausible reading:" and acknowledge contrary evidence in the verdict sentence. | owner's markup 2026-07-06 | conflicts with V-14 (K10) |
| WR-15 | WR, Claim-calibration | State what a design controls and what it leaves uncontrolled; no triumphal labels such as "confound-killer". | owner's markup 2026-07-06 | reference only |
| WR-16 | WR, Claim-calibration | Explain any measure a table relies on (what, why chosen, how validated) before first use. | 2026-07-06/07 | reference only |
| WR-17 | WR, Claim-calibration | A coined term must not promise a mechanism the code does not implement; define it by its mechanism and what it does not do. | 2026-07-06/07 | reference only |
| WR-18 | WR, Claim-calibration | The report body includes only mistakes that changed the method or set a standing rule; clerical slips stay in the log. | 2026-07-07 | reference only |
| WR-19 | WR, Claim-calibration | Put forensic narrative in one bounded section or the log; the report body never reads chronologically. | 2026-07-07 | reference only |
| WR-20 | WR, Self-containment | Assume the reader never clicks a link; links are receipts, not the explanation. | owner's markup 2026-07-06 | reference only |
| WR-21 | WR, Self-containment | Show the fix on the same concrete example as the problem (before → after). | 2026-07-06 | reference only |
| WR-22 | WR, Self-containment | Show each artefact the document reasons about inline once, lifted from the real record; mark an invented example as illustrative. | 2026-07-06 | in core_rules (CR 11) |
| WR-23 | WR, Self-containment | A reader-facing doc is self-contained at one example per claim. | 2026-07-06 | reference only |
| WR-24 | WR, Self-containment | No conversation residue: no "the user", no house rules cited by bare name. | 2026-07-06 | reference only |
| WR-25 | WR, Self-containment | A journey log keeps decisions and reversals; the steady-state design lives in the report. | 2026-07-06 | reference only |
| WR-26 | WR, Self-containment | Acid test: a reader without repo access can explain what the system does, what the core artefact looks like, and which results are trusted. | 2026-07-06 | reference only |
| WR-27 | WR, Explanation-completeness | Place the component in the pipeline first: who writes it, who reads it, when, and its central design problem. | 2026-07-06 | reference only |
| WR-28 | WR, Explanation-completeness | For each decision: problem → obvious fix → why it fails → chosen fix → accepted trade-off. | 2026-07-06 | reference only |
| WR-29 | WR, Explanation-completeness | Give every mechanism its job and what happens without it, where it is used. | 2026-07-06 | reference only |
| WR-30 | WR, Explanation-completeness | Anticipate the reader's objection and answer it inline, for example in a heading "Why X, and not Y". | 2026-07-06 | conflicts with V-17 (K5) |
| WR-31 | WR, Explanation-completeness | Define a category by what membership lets the reader do. | 2026-07-07 | reference only |
| WR-32 | WR, Explanation-completeness | Explain a study from another workstream in one or two sentences before using it, or cut the reference. | 2026-07-06 | reference only |
| WR-33 | WR, Explanation-completeness | Under-explanation, not length, is the enemy; compress by deleting redundancy, never reasoning. | 2026-07-06 | duplicate of SG-68 |
| WR-34 | WR, Explanation-completeness | No meta-commentary about the document; replace reading contracts with a compact orientation block. | 2026-07-06 | conflicts with SG-20 (K7) |
| WR-35 | WR, Step 5.1 | Argument pass: full checklist, fact-dump check, drift from the brief, verdict scope. | — | reference only |
| WR-36 | WR, Step 5.2 | Prose-legibility pass, including a grep for internal names to check each is introduced. | — | reference only |
| WR-37 | WR, Step 5.3 | Outsider-and-history pass. | — | duplicate of SG-98 |
| WR-38 | WR, Step 5.4 | Fresh-reader pass by a subagent with no context; reword every listed sentence. | 2026-11-17 | duplicate of SG-08 |
| WR-39 | WR, Step 6 | Deliver with a review note, and flag factual ambiguities rather than smoothing them. | — | reference only |
| PS-01 | PS, opening | The reader is a hiring reader for an entry-to-mid-level AI engineer; show practical judgement, not research completeness; the owner must be able to defend every sentence. | — | reference only |
| PS-02 | PS, opening | The approach is constant; the structure adapts to the subject; no fixed template. | — | reference only |
| PS-03 | PS, §0 | Size the job: small fix, one section, or full workflow. | — | reference only |
| PS-04 | PS, §1 | Read the inputs yourself; do not summarise them from memory. | — | reference only |
| PS-05 | PS, §1 | Inputs include the content plan, brief, editorial notes, map with its Handle-with-care list, and the parent excerpt. | — | reference only |
| PS-06 | PS, §1 | Lift numbers as they stand; never re-derive or invent. | — | duplicate of WR-08 |
| PS-07 | PS, §2 | Choose the page's purpose and depth from page types; one writer owns the explanation. | — | reference only |
| PS-08 | PS, §2 | Write a short brief: reader outcome, concept order, likely confusion, evidence. | — | reference only |
| PS-09 | PS, §2 | Write one difficult passage as real page copy before drafting. | — | reference only |
| PS-10 | PS, §2 | Distinguish an illustration from evidence; label invented or simplified examples. | — | duplicate of WR-22 |
| PS-11 | PS, §2 | Choose the representation by what the reader must understand; use a diagram only when it is clearer. | — | reference only |
| PS-12 | PS, §3 | Give each section one line (what the reader learns, how); do not force a causal link between independent parts. | — | reference only |
| PS-13 | PS, §3 | Show the owner the central point, section order and sample passage before expanding, unless waived. | — | reference only |
| PS-14 | PS, §4 | Keep the page file's existing layout. | — | reference only |
| PS-15 | PS, §4 | Build on the parent page without repeating its introduction at length. | — | reference only |
| PS-16 | PS, §4 | Explain an approach's purpose and criteria before its results; do not open with conclusions that need later concepts. | — | reference only |
| PS-17 | PS, §4 | Keep source mappings in the closing HTML comment; moved-out detail goes to notes and never rescues misleading copy. | — | reference only |
| PS-18 | PS, §4 | Put unsettled questions in the brief's Open questions, not in smooth prose. | — | reference only |
| PS-19 | PS, §4 | If drafting shows the outline was wrong, fix the outline first. | — | reference only |
| PS-20 | PS, §4 | If the draft is long, remove secondary branches before compressing the core. | — | in core_rules (CR 10) |
| PS-21 | PS, §4 | Read as a newcomer before review; save a first-draft snapshot. | — | reference only |
| PS-22 | PS, §5 | Run two fresh-context reviewers, editorial and claims, who report findings and do not edit. | — | reference only |
| PS-23 | PS, §5 | The editorial review is text-only; record visual understanding as unchecked; do not call the isolation technically enforced. | — | reference only |
| PS-24 | PS, §6 | Record each material finding and its action; the writer applies fixes in one voice. | — | reference only |
| PS-25 | PS, §6 | A reviewer's misunderstanding shows a presentation problem, not that its repair is correct; check repairs against sources. | — | reference only |
| PS-26 | PS, §6 | Fix reasoning and selection before wording; for a context request choose explain, relocate or remove. | — | reference only |
| PS-27 | PS, §6 | If a correction changes a claim, recheck the passages around it. | — | reference only |
| PS-28 | PS, §6 | Before adding a missing term, ask whether the passage belongs on this page. | — | duplicate of V-10 |
| PS-29 | PS, §6 | Report the word count against the level's guide; growth needs a reason for each addition. | — | reference only |
| PS-30 | PS, §6 | Reread each revised section whole and remove explanations that local fixes piled up. | — | reference only |
| PS-31 | PS, §6 | Re-run a reviewer when structure changed; do not loop on taste. | — | reference only |
| PS-32 | PS, §7 | Define "ready for owner review"; completed steps or reviewer approval do not establish it. | — | reference only |
| PS-33 | PS, §7 | Finish: dated editorial-notes entry, header line, reviewed snapshot; never mark approved. | — | reference only |
| PS-34 | PS, Maintaining | Test the runner; run quality pilots; classify owner changes; change a decision step rather than append a universal rule. | — | reference only |
| V-00 | V, header | The three portfolio guides win if they disagree with voice.md. | review rounds 2026-10-13 to 10-28 | reference only |
| V-01 | V, Voice 1 | Name the thing first. | owner, same rounds | reference only |
| V-02 | V, Voice 2 | Go from familiar to specific one layer at a time; the game's need comes before the framework term. | owner | reference only |
| V-03 | V, Voice 3 | Define by what each party knows and wants; explain a design by the tension it resolves. | owner | reference only |
| V-04 | V, Voice 4 | Give the frame, then the parts. | owner | reference only |
| V-05 | V, Voice 5 | Plain and conversational; always "I", never "we"; never claim AI-written code as hand-written; counts a reader can picture. | owner | conflicts with SG-45, SG-54, SG-63 (K4) |
| V-06 | V, Voice 6 | Put material scope beside the claim; dates in source notes; no repeated generic disclaimers. | owner | duplicate of SG-43 |
| V-07 | V, page 7 | Select evidence by its purpose; full run histories belong in evidence. | owner | reference only |
| V-08 | V, page 8 | Each passage has one main job; keep conditions, denominators and limitations on the page. | owner | reference only |
| V-09 | V, page 9 | Explain the finding, not the investigation; organise by the finding. | owner 2026-10-28 | in core_rules (CR 8) |
| V-10 | V, page 10 | Select topics instead of compressing; move a detail that answers a different question. | owner | in core_rules (CR 10) |
| V-11 | V, page 11 | One term one meaning, one unit and question per paragraph, one job per sentence with the point first. | owner | in core_rules (CR 3) |
| V-12 | V, page 12 | Diagrams show what, prose explains why; a link follows a stated problem. | owner | reference only |
| V-13 | V, page 13 | Every sentence advances understanding; keep connecting explanation; remove empty repetition. | owner | reference only |
| V-14 | V, page 14 | Observation is not cause; call a mechanism "suspected" unless isolated; rule tests do not show usefulness. | owner | conflicts with WR-14 (K10) |
| V-15 | V, Words to avoid | Keep established technical terms and explain them; do not erase statistical distinctions. | owner | duplicate of SG-06 |
| V-16 | V, Words to avoid | Avoid catalogues of model names; do not substitute "stronger" or "cheaper" without evidence. | owner | reference only |
| V-17 | V, Words to avoid | Avoid nominalisations, defensive negations, trade-off jargon, promotional adjectives, rhetorical Q&A, repeated labels. | owner | reference only |
| V-18 | V, Care | Keep repository bookkeeping that reflects poorly off the public page; follow Handle with care. | owner | in core_rules (CR 12) |
| V-19 | V, Care | Tell a caught fault as caught, with what changed and its scope. | owner | reference only |
| V-20 | V, Care | A limitation that changes how to read a result always stays. | owner | in core_rules (CR 12) |
| V-21 | V, Care | Spend checking effort on the reasoning, not re-auditing figures; never invent or silently change a number. | owner | reference only |
| PW-01 | PW, How to use it | For editorial passes the writer owns wording and a separate model verifies facts; flag rather than audit. | — | duplicate of L3-01 |
| PW-02 | PW, How to use it | An inaccessible path is not source material; supply the contents. | — | reference only |
| PW-03 | PW, How to use it | After approval, record the prompt and exemplar revision; do not silently change the reference. | — | reference only |
| PW-04 | PW, prompt opening | Interest comes from the problem, choice, finding and consequence, not promotion or suspense. | — | reference only |
| PW-05 | PW, Audience and evidence | Match evidence to the type of claim (mechanism, fix, design, general improvement). | — | reference only |
| PW-06 | PW, Audience and evidence | Keep limitations that change interpretation without defending an unclaimed broader benefit. | — | duplicate of V-20 |
| PW-07 | PW, Reading structure | Level 1, 2 and 3 responsibilities and the Level 3 layout. | — | reference only |
| PW-08 | PW, Reading structure | Navigation links are site features, not page copy. | — | reference only |
| PW-09 | PW, Reading structure | Readers must not need repository links to understand a claim or its limitation. | — | duplicate of WR-20 |
| PW-10 | PW, Reading structure | Preserve the supplied structure; do not add page levels. | — | reference only |
| PW-11 | PW, Portfolio vs record | Complete logs stay in evidence; pages explain questions, findings and decisions. | owner 2026-10-28 | reference only |
| PW-12 | PW, Portfolio vs record | Keep essential methods, conditions, units, results and limits beside claims; never move adverse findings out to shorten. | owner 2026-10-28 | duplicate of V-08 |
| PW-13 | PW, Portfolio vs record | Two checks: can the reader assess the decision without the evidence; does each detail change understanding. | owner 2026-10-28 | reference only |
| PW-14 | PW, Portfolio vs record | Organise around the reader's reasoning and say why one finding motivates the next. | owner 2026-10-28 | duplicate of L3-06 |
| PW-15 | PW, Opening and selection | Choose the opening from what the reader needs before the first decision. | — | duplicate of PT-06 |
| PW-16 | PW, Opening and selection | Parent context does not forbid a concise definition. | — | duplicate of PT-07 |
| PW-17 | PW, Opening and selection | Write the argument as concepts first; select examples with distinct jobs. | — | reference only |
| PW-18 | PW, Opening and selection | Remove secondary branches before compressing. | — | duplicate of PS-20 |
| PW-19 | PW, Opening and selection | Level 3 answers a focused follow-up; classify by responsibility, not length. | — | duplicate of PT-01 |
| PW-20 | PW, Work before writing 1 | Identify each subject's question, decision, example, result, scope and implication. | — | reference only |
| PW-21 | PW, Work before writing 2 | Check quotes and numbers; track denominator, unit, version, independence; do not settle a source conflict by picking the more impressive result. | — | reference only |
| PW-22 | PW, Work before writing 3 | Separate demonstrated, proposed, built-but-unused and current practice; check who did the work before writing "I". | — | in core_rules (CR 11) |
| PW-23 | PW, Work before writing 4 | Select material; do not inventory the sources. | — | duplicate of V-07 |
| PW-24 | PW, Writing style | Plain, precise, connected paragraphs; avoid long chains of method, numbers and caveats. | — | duplicate of SG-69 |
| PW-25 | PW, Writing style | Question before procedure, comparison before numbers; end with the next question. | — | duplicate of L3-08 |
| PW-26 | PW, Writing style | Define a measure by what it does and does not establish; name the counting unit; explain unit changes. | — | in core_rules (CR 6) |
| PW-27 | PW, Writing style | Examples reduce workload; paraphrase faithfully; never present a paraphrase as a quote. | — | duplicate of L3-13 |
| PW-28 | PW, Writing style | Cohesion check: why does each paragraph follow the previous one. | — | duplicate of L3-18 |
| PW-29 | PW, Writing style | A Level 1 summary is usually two short paragraphs; vary sentence patterns. | — | reference only |
| PW-30 | PW, Writing style | Length guides per level; never cut an explanation to hit a count. | — | reference only |
| PW-31 | PW, Writing style | Explain why a result mattered; replace "direction only" with what the sample supports. | — | duplicate of SG-71 |
| PW-32 | PW, Writing style | One lead example per Level 1 summary. | — | reference only |
| PW-33 | PW, Writing style | First person only for supported contributions. | — | duplicate of PW-22 |
| PW-34 | PW, Writing style | Use established terms and explain each on first use; no keyword lists. | — | duplicate of SG-06 |
| PW-35 | PW, Writing style | Do not treat component checks as end-to-end; keep test scope, scoring, validation and controls separate. | — | reference only |
| PW-36 | PW, Writing style | Internal folder names and identifiers do not substitute for explanation. | — | duplicate of SG-70 |
| PW-37 | PW, Writing style | Keep the conclusion and its material limitation together, not a closing disclaimer. | — | duplicate of SG-43 |
| PW-38 | PW, Writing style | Use specific link text; leave an editorial spec for unbuilt pages; no dead links. | — | reference only |
| PW-39 | PW, Writing style | Integrate exhibits: what to notice, the evidence, its consequence. | — | reference only |
| PW-40 | PW, Writing style | Use a small labelled flow diagram for handoffs; label current, historical or proposed; never draw an unbuilt safeguard. | — | reference only |
| PW-41 | PW, Writing style | Avoid repeated labels, rhetorical Q&A, promotional adjectives, invented compound labels, contrasts made to impress. | — | duplicate of V-17 |
| PW-42 | PW, What stays off | Bookkeeping that reflects poorly stays off; follow Handle with care. | — | duplicate of V-18 |
| PW-43 | PW, What stays off | Do not present every caught fault as a deep flaw. | — | duplicate of V-19 |
| PW-44 | PW, What stays off | Leaving bookkeeping off is never a reason to drop a caveat. | — | duplicate of V-20 |
| PW-45 | PW, Evidence discipline | Do not invent results, causes, contributions or status. | — | in core_rules (CR 11) |
| PW-46 | PW, Evidence discipline | A deterministic check is repeatable, not automatically correct; "no model-call cost" is not "free". | — | reference only |
| PW-47 | PW, Evidence discipline | A replay of one situation is not a frequency estimate; twenty samples of one case are not twenty situations. | — | reference only |
| PW-48 | PW, Evidence discipline | Correlation with an outcome is not causation. | — | reference only |
| PW-49 | PW, Evidence discipline | Model agreement is not human validation; blinding does not make labels correct. | — | reference only |
| PW-50 | PW, Evidence discipline | A requested setting is not proof of behaviour; a shifted baseline is not proof of drift. | — | reference only |
| PW-51 | PW, Evidence discipline | A fail-open response does not prevent a wrong but valid classification. | — | reference only |
| PW-52 | PW, Evidence discipline | Measuring a quality deficit is different from a policy excluding the model. | — | reference only |
| PW-53 | PW, Evidence discipline | A regression case detects recurrence but does not guarantee a fix. | — | reference only |
| PW-54 | PW, Evidence discipline | Keep sample context near a number; a source note cannot rescue misleading copy. | — | duplicate of PS-17 |
| PW-55 | PW, Worked example | The worked example shows method through a task, numbers with sample and baseline, the changed conclusion, and scoped limits. | — | reference only |
| PW-56 | PW, Final editing pass | Seven final checks before returning a draft. | — | reference only |
| PW-57 | PW, Output | Keep notes separate from prose; flag missing evidence; do not mark approved. | — | reference only |
| PW-58 | PW, Using the reference pages | Use only the Page copy section as an example, and use the Level 2 and 3 references only after the owner approves them. | — | conflicts with EX-01, L2-01 (K8) |
| PW-59 | PW, Using the reference pages | Compare a new chapter on clarity and progression, not on matching counts of paragraphs or terms. | — | reference only |
| L2-01 | L2, Status | The Level 2 prompt is provisional and based on an unapproved draft. | 2026-10-25 | reference only |
| L2-02 | L2, table | State the decision or distinction before the process. | — | duplicate of PS-16 |
| L2-03 | L2, table | The lead story must not imply its cause explains every failure. | — | reference only |
| L2-04 | L2, table | One explanatory job per paragraph; select numbers by what they establish. | — | duplicate of V-08 |
| L2-05 | L2, table | Give each explanation one home and cross-reference it. | — | duplicate of SG-30 |
| L2-06 | L2, table | Preserve distinctions the intervention depends on (present, correct, clear). | — | reference only |
| L2-07 | L2, table | A working intervention does not identify the internal mechanism. | — | duplicate of V-14 |
| L2-08 | L2, table | Connect studies through the question; do not pool separate experiments. | — | reference only |
| L2-09 | L2, table and Causal precision | Replace slogans and universal lessons with what to inspect or test next. | — | conflicts with SG-55 (K6) |
| L2-10 | L2, table | Keep the actual sampling unit and denominator ("three of four observed errors"). | — | in core_rules (CR 4) |
| L2-11 | L2, table | Organise by the finding, not the order of the work. | owner 2026-10-28 | duplicate of V-09 |
| L2-12 | L2, table | Split a term with two meanings before using it. | — | duplicate of V-11 |
| L2-13 | L2, table | One denominator per paragraph. | — | duplicate of V-11 |
| L2-14 | L2, table | One question per paragraph. | — | duplicate of V-11 |
| L2-15 | L2, table | One job per sentence; lead with the point; provenance in notes. | — | duplicate of V-11 |
| L2-16 | L2, table | Level 2 gives the decision and strongest evidence; Level 3 the detailed comparisons. | owner 2026-10-28 | duplicate of V-08 |
| L2-17 | L2, table | List the separate questions a passage answers before writing; the reader knows what changed before any number. | — | reference only |
| L2-18 | L2, table | Keep what happened apart from the suspected explanation. | — | duplicate of V-14 |
| L2-19 | L2, table | Say what each kind of test establishes. | — | duplicate of V-14 |
| L2-20 | L2, table | Group limits by purpose; a known mismatch is a fix to make. | — | reference only |
| L2-21 | L2, Before drafting | Keep the subject's other mechanisms distinguishable from the featured story's. | — | duplicate of L2-03 |
| L2-22 | L2, Page design | Open with the problem and central question; no full project introduction. | — | duplicate of PS-16 |
| L2-23 | L2, Page design | Order subsections as the reader needs them; report structural changes. | — | reference only |
| L2-24 | L2, Page design | One purpose per subsection; fullest explanation in one place. | — | duplicate of SG-30 |
| L2-25 | L2, Page design | Logs stay in evidence; keep enough method and limits to assess claims; never move an adverse finding out. | — | duplicate of PW-12 |
| L2-26 | L2, Page design | Develop the featured story with context; each exhibit has a distinct purpose. | — | reference only |
| L2-27 | L2, Page design | Consider a labelled diagram for workflows; mark historical, current and proposed. | — | duplicate of PW-40 |
| L2-28 | L2, Page design | A Level 3 link sits beneath the subsection it deepens. | — | duplicate of L3-20 |
| L2-29 | L2, Page design | Keep result, implication and scope together; end with remaining limits, not a summary. | — | reference only |
| L2-30 | L2, Page design | Evidence links establish provenance only. | — | duplicate of WR-20 |
| L2-31 | L2, Selection check | Show practical judgement at the supported strength. | — | duplicate of PS-01 |
| L2-32 | L2, Selection check | Can the core argument be stated without listing experiments. | — | reference only |
| L2-33 | L2, Selection check | For context requests: explain, relocate or remove. | — | duplicate of PS-26 |
| L2-34 | L2, Depth without density | About 1,200–2,000 words, a guide not a limit. | — | duplicate of PW-30 |
| L2-35 | L2, Depth without density | Each paragraph one idea; vary paragraph length. | — | duplicate of SG-69 |
| L2-36 | L2, Depth without density | Intermediate counts and version history need a reason to appear. | — | reference only |
| L2-37 | L2, Depth without density | Follow a number with its meaning for the decision. | — | reference only |
| L2-38 | L2, Depth without density | State the practical limit instead of "directional", "robust", "proven". | — | duplicate of SG-71 |
| L2-39 | L2, Depth without density | First person only for supported contributions. | — | duplicate of PW-22 |
| L2-40 | L2, Depth without density | No repeated labels; headings say what the subsection explains. | — | reference only |
| L2-41 | L2, Causal precision | Separate observation, interpretation and intervention evidence. | — | reference only |
| L2-42 | L2, Causal precision | Correct information present is not proof it was clear or used. | — | reference only |
| L2-43 | L2, Causal precision | An intervention that changes two details isolates neither. | — | reference only |
| L2-44 | L2, Causal precision | No general rate from selected failures. | — | duplicate of PW-47 |
| L2-45 | L2, Causal precision | Distinguish more reasoning from a different model, replays from games, judge from generation variation. | — | reference only |
| L2-46 | L2, Causal precision | Model labels, deterministic code and regression tests have the limits stated in PW-46, PW-49, PW-53. | — | duplicate of PW-49 |
| L2-47 | L2, Causal precision | Built, run, deployed and validated are separate states. | — | duplicate of PW-22 |
| L2-48 | L2, Causal precision | Avoid universal lessons such as "instructions do not work". | — | duplicate of L2-09 |
| L2-49 | L2, Review before returning | Fix distinctions and claims before polishing; skim headings and first sentences. | — | reference only |
| L2-50 | L2, Review before returning | Check universal wording ("every", "only", "proves") against its scope. | — | reference only |
| L2-51 | L2, Review before returning | Check whether two offered explanations could both be true. | — | reference only |
| L2-52 | L2, Review before returning | If a later caveat undoes an earlier sentence, rewrite the earlier sentence. | — | reference only |
| L2-53 | L2, Review before returning | Second copy of the three checks above. | — | proposed for removal |
| L2-54 | L2, Output | Separate notes from prose; completion note; no self-scores. | — | duplicate of PW-57 |
| L2-55 | L2, Review rubric | Score 0/1/2 per criterion; do not average; three criteria must score 2. | — | reference only |
| L2-56 | L2, Testing transfer | Test the prompt on another subject before changing it. | — | reference only |
| L2-57 | L2, Handoff | Drafter checks facts, editorial reviewer checks reading; preserve legitimate voice differences. | — | duplicate of L3-01 |
| L3-01 | L3, Editorial responsibility | The writing pass owns wording; a separate verifier owns facts; flag questions rather than infer. | — | reference only |
| L3-02 | L3, Editorial responsibility | "Editorially revised" is not "factually verified"; flag scope changes. | — | reference only |
| L3-03 | L3, What changes | Level 3 depth comes from explaining details, not denser sentences. | — | reference only |
| L3-04 | L3, What changes, table | Level 2 expectations adapted for Level 3. | — | reference only |
| L3-05 | L3, Write-up vs log | Logs stay in evidence; Level 3 explains one investigation. | owner 2026-10-28 | duplicate of PW-11 |
| L3-06 | L3, Write-up vs log | Progression: question → mechanism → investigation → finding → limits; central findings get more room. | owner 2026-10-28 | reference only |
| L3-07 | L3, Write-up vs log | Remain assessable without links; do not hide uncertainty behind links. | owner 2026-10-28 | duplicate of PW-12 |
| L3-08 | L3, Connected investigation 1 | Question before procedure. | owner 2026-10-28 | reference only |
| L3-09 | L3, Connected investigation 2 | Comparison before shorthand. | owner 2026-10-28 | duplicate of SG-70 |
| L3-10 | L3, Connected investigation 3 | One explanatory job per paragraph. | owner 2026-10-28 | duplicate of V-08 |
| L3-11 | L3, Connected investigation 4 | Define what a measure establishes. | owner 2026-10-28 | duplicate of PW-26 |
| L3-12 | L3, Connected investigation 5 | Numbers after orientation. | owner 2026-10-28 | duplicate of SG-79 |
| L3-13 | L3, Connected investigation 6 | Examples should reduce effort; paraphrase unless exact wording is the evidence. | owner 2026-10-28 | reference only |
| L3-14 | L3, Connected investigation 7 | Finding and scope together; do not postpone a material caveat. | owner 2026-10-28 | duplicate of SG-43 |
| L3-15 | L3, Connected investigation 8 | End with the question or decision the finding motivates. | owner 2026-10-28 | reference only |
| L3-16 | L3, Connected investigation 9 | Retain useful technical language and define it. | owner 2026-10-28 | duplicate of SG-06 |
| L3-17 | L3, Connected investigation 10 | Select evidence, preserve the record. | owner 2026-10-28 | duplicate of PW-11 |
| L3-18 | L3, Cohesion check | The reader can say why each paragraph follows; transition words cannot repair a missing link. | — | reference only |
| L3-19 | L3, Selecting a Level 3 page | All six criteria must hold. | — | reference only |
| L3-20 | L3, Anchored in the parent | Every Level 3 page belongs to a parent subsection; update the parent with it. | 2026-10-30 | reference only |
| L3-21 | L3, Selecting | Two tests: remove the link; complete "Readers will learn how…". | — | reference only |
| L3-22 | L3, Selecting | Record each candidate in five fields; verify historical claims against records of that time. | — | reference only |
| L3-23 | L3, Supplement | Open with the question, why it mattered and the main conclusion; no suspense. | — | reference only |
| L3-24 | L3, Supplement | Define an unfamiliar mechanism before its performance, and use the same precise term throughout. | — | duplicate of V-11 |
| L3-25 | L3, Supplement | Make counting units explicit; ask the verifier when their relationship is missing. | — | duplicate of PW-26 |
| L3-26 | L3, Supplement | Separate confirmation, rejection and unresolved outcomes; a rule's historical name is not proof. | — | reference only |
| L3-27 | L3, Supplement | Explain the pattern of results; accuracy may hide error types. | — | reference only |
| L3-28 | L3, Supplement | Label estimates and assumptions; a formula earns space only if explained. | — | reference only |
| L3-29 | L3, Supplement | Keep population and scope mismatches beside the conclusion; a reason to reopen is not proof of error. | — | reference only |
| L3-30 | L3, Supplement | Give the main investigation priority; dates only where they explain. | — | reference only |
| L3-31 | L3, Supplement | The parent keeps the main finding and caveats. | — | duplicate of PT-03 |
| L3-32 | L3, Additional criteria | Level 3 rubric criteria. | — | reference only |
| L3-33 | L3, Additional criteria | Turn an unclear assumption into a verification question, not smoother prose. | — | duplicate of PS-18 |
| PT-01 | PT, opening | Choose the level by explanatory responsibility, not length or format. | — | reference only |
| PT-02 | PT, L1 → L3 | A direct Level 1 to Level 3 link is valid; do not manufacture a Level 2. | — | reference only |
| PT-03 | PT, L1 → L3 | Without the link, the parent still explains its decision and limitations. | — | reference only |
| PT-04 | PT, purpose | Choose the primary purpose from the reader's question; a hybrid keeps one central question. | — | reference only |
| PT-05 | PT, purpose table | Six page purposes with their progression, evidence and main failure. | — | reference only |
| PT-06 | PT, opening table | Choose the opening from what the reader is missing. | — | reference only |
| PT-07 | PT, opening | Parent context does not prohibit a concise definition. | — | reference only |
| PT-08 | PT, opening | Use the chapter plan as a routing aid. | — | reference only |
| PT-09 | PT, Adapt | Worked adaptations (day_and_night, evidence_design, human_in_the_loop, silence policy). | — | reference only |
| PT-10 | PT, Adapt | For a hybrid, record the main purpose in the brief; no section per mode. | — | reference only |
| PT-11 | PT, Same principles | Distinguish observation, interpretation, intent, implementation and validated behaviour. | — | duplicate of L2-41 |
| PT-12 | PT, Same principles | Logs and reproduction instructions are separate deliverables; do not force them through the workflow. | — | reference only |
| PT-13 | PT, Same principles | Review by purpose; depth is the explanation the claim needs. | — | reference only |
| EX-01 | EX, opening | Read the closest example's page copy; examples are not templates. | — | reference only (see K8 under PW-58) |
| EX-02 | EX, Why structures differ | Structure comes from the subject: execution order or successive questions. | — | reference only |
| EX-03 | EX, What both share 3 | Terms arrive when a need calls for them. | — | duplicate of V-02 |
| EX-04 | EX, A and B notes | Each section opens by answering what the previous one left open. | — | duplicate of L3-15 |
| EX-05 | EX, A notes | Place the featured failure inside the concept it teaches. | — | reference only |
| EX-06 | EX, B notes | Draw a distinction that changes the reading before the table. | — | duplicate of L2-06 |
| EX-07 | EX, B notes | Tell a later correction as what the better check found. | — | duplicate of V-19 |
| EX-08 | EX, Apply critically | Keep model names only where they change interpretation. | — | duplicate of V-16 |
| EX-09 | EX, What both share | The six shared transferable points. | — | reference only |
| EX-10 | EX, C | Define an approach before evaluating it; note C's scope gaps. | — | reference only |
| EX-11 | EX, C | Do not create an exemplar merely to fill a category. | — | reference only |
| EX-12 | EX, Choosing how to explain | For a transformation, show the intermediate states. | — | reference only |
| EX-13 | EX, Choosing how to explain | For a selection decision, organise by the questions each check answers. | — | reference only |
| EX-14 | EX, Choosing how to explain | For a quantitative finding, define the comparison and consequence first. | — | reference only |
| EX-15 | EX, closing | Clarity comes from making the relationship explicit, not from shorter sentences. | — | duplicate of SG-01 |
| BT-01 | BT, header | The brief is short authoring material; link inventories rather than copy them. | — | duplicate of PS-08 |
| BT-02 | BT, Sample passage | Label illustrative examples. | — | duplicate of PS-10 |
| BT-03 | BT, Review resolution | Check technical repairs against sources. | — | duplicate of PS-25 |
| BT-04 | BT, Trial record | Classify owner changes; no invented usability score; word count is not quality. | — | duplicate of PS-34 |
| ED-01 | ED, Reader | Stand in for a hiring reader who will not open links. | — | reference only |
| ED-02 | ED, What you have | No brief or sources; do not open files or guess intent. | — | reference only |
| ED-03 | ED, Parent excerpt | Do not ask for another introduction; flag long re-explanation and unexplained terms. | — | reference only |
| ED-04 | ED, Parent excerpt | Check the opening supplies the foundation for the first decision. | — | duplicate of PT-06 |
| ED-05 | ED, Visual scope | Do not claim to have reviewed images. | — | duplicate of PS-23 |
| ED-06 | ED, Your job | Report where understanding breaks; your own inference is not evidence the page explained it. | — | reference only |
| ED-07 | ED, Sections 1–4 | State the argument first, run an application probe, list findings by kind, give up to three improvements. | — | reference only |
| ED-08 | ED, Findings, Repair | Choose explain, relocate or remove; do not write replacement prose longer than a sentence. | — | reference only |
| ED-09 | ED, Look in particular for | Quote every sentence read twice; its usual causes; repair with a plain statement even if longer. | 2026-11-17 (uncommitted change) | duplicate of SG-08 |
| ED-10 | ED, Look in particular for | The other things to look for (unfollowed sections, early terms, mixed paragraphs, unoriented numbers, caveat reversals, causes from observations, repeated examples, method detail, empty repetition). | — | reference only |
| ED-11 | ED, closing | Do not praise or score; report effort, not only failures; recommend a visual only for a named relationship. | — | reference only |
| CL-01 | CL, What to read | Read-only; read page, brief, cited evidence, evidence rules and the map. | — | reference only |
| CL-02 | CL, Mechanisms | Check current behaviour against code, historical behaviour against records of that time. | — | reference only |
| CL-03 | CL, Comparisons | Keep separate experiments apart; a replay is not a frequency estimate. | — | duplicate of L2-08 |
| CL-04 | CL, Inference | The conclusion must follow from the evidence even if the source uses the same words. | — | reference only |
| CL-05 | CL, Proportionality | Narrow an unsupported claim instead of demanding new research. | — | reference only |
| CL-06 | CL, Validation | Calibration vs held-out evaluation; correctness vs consistency; reviewed vs representative; intended vs completed. | — | reference only |
| CL-07 | CL, Scope | Check universal words and the sample unit. | — | duplicate of L2-50 |
| CL-08 | CL, Status | Built vs run vs deployed vs validated. | — | duplicate of PW-22 |
| CL-09 | CL, Ownership | First-person claims must be supported; nothing AI-written as hand-written. | — | duplicate of PW-22 |
| CL-10 | CL, Off-page items | Flag Handle-with-care items on the page. | — | duplicate of V-18 |
| CL-11 | CL, Numbers | Check a number only where a claim depends on it; flag conflicts with its source. | owner ruling (no date) | duplicate of V-21 |
| CL-12 | CL, closing | Do not judge style. | — | reference only |
| CL-13 | CL, Output | Return findings, checked-and-supported, not-checked. | — | reference only |
