# Portfolio authoring prompt and reference example

Status: provisional, 2026-10-25. The Evaluation Level 1 page is approved as the Level 1 reference; the
Level 2 and Level 3 references are drafted and waiting for the owner's review. A prompt supports
consistency; it does not guarantee identical prose or replace factual review.

This is an authoring prompt, not a Codex skill or a publication instruction. The workflow that applies
it to a whole page (frame, outline, draft, cold editorial read, claims check) is the
`write-portfolio-page` skill in [`.agents/skills/write-portfolio-page/`](../SKILL.md),
shared by Codex and Claude Code.

## How to use it

For Level 2 work, also use the [Level 2 prompt and review rubric](portfolio-level-2-writing-prompt.md).
It records the weaknesses found in the first factual-errors draft and the specific revisions that
improved it, with a focused worked example. It is provisional until tested on another subject.

For Level 3, use the [investigation writing guidance and rubric](portfolio-level-3-writing-rubric.md).
For editorial-only passes, the writer owns phrasing and structure; a separate model verifies facts.
Flag unresolved claims for that verifier instead of independently auditing the implementation.

Copy the prompt block below into the writing task. Replace the target-input placeholders. The worked
input/output example inside the block supplies one-shot guidance even when the writer cannot access
this repository. When files are available, also provide the content plan, relevant reports and any
correction notes. An inaccessible path is not source material: supply the file contents instead.

For this project's current task:

- Structure: the chapter's `content_plan.md` and the brief at the top of the target page's file
  (for Evaluation, `writeup/evaluation/`).
- Constraints and corrections: the chapter outline in `writeup/_planning/map.md`, including its "Handle with care"
  list, which is a required input: it names what stays off the page.
- Evidence: the method reports and the more specific records cited in the page brief.
- References: Level 1, `writeup/evaluation/evaluation.md`; Level 2,
  `writeup/evaluation/factual_errors/factual_errors.md`; Level 3,
  `writeup/evaluation/code_checks/field_audit.md` (each file's "Page copy" section).

After approval, record the revision of both the prompt and exemplar below. Keep the embedded example
aligned with the approved prose; do not silently change the reference when editing a later chapter.

- Level 1 reference: approved by the owner 2026-10-25 (`writeup/evaluation/evaluation.md`).
- Level 2 reference: drafted 2026-10-25, pending owner review (`factual_errors/factual_errors.md`).
- Level 3 reference: drafted 2026-10-25, pending owner review (`code_checks/field_audit.md`).
- Approved prompt revision: pending owner review.

## Copyable prompt

```text
You are writing a portfolio case study for a hiring reader assessing an entry-to-mid-level AI engineer.
The reader is technically curious but does not know this project. Write clear, engaging explanations of engineering decisions,
supported by the supplied evidence. The interest should come from the problem, the choice, the finding
and its consequence—not promotional language or suspense.

AUDIENCE AND EVIDENCE STANDARD
Demonstrate practical engineering judgement: selecting an appropriate approach, implementing it,
investigating failures, testing useful behaviour and understanding limits. Research-level experimental
completeness is not the default. Match evidence to the claim: explaining a mechanism, fixing a
reproduced failure, choosing a practical design and establishing a general improvement require
different support. Preserve limitations that change interpretation, without making every page defend
an unclaimed broader benefit. Keep technical terms that help assess the work.

TARGET INPUTS
Topic and page title: [INSERT]
Requested reading level and output file, if applicable: [INSERT]
Approved headings, ordering and link destinations: [INSERT]
Source reports or verified facts: [ATTACH OR INSERT]
Corrections, ownership limits and editorial constraints: [ATTACH OR INSERT]
What stays off the page (the chapter's "Handle with care" list): [ATTACH OR INSERT]
Existing draft, if revising: [ATTACH OR INSERT]

READING STRUCTURE
- Level 1 explains the chapter's overall problem, approach and major decisions. It can introduce
  substantial L2 subjects, or be self-contained with optional L3 deep dives linked directly from the
  relevant subsections. Do not create L2 pages merely to fill a hierarchy.
- Level 2 owns a substantial subject: its purpose, mechanisms, decisions and trade-offs. Use an
  opening, connected subsections and supporting examples as needed, with
  exhibits inside the explanation. Its layout, length and review rubric are in the Level 2 prompt
  (`.agents/skills/write-portfolio-page/references/portfolio-level-2-writing-prompt.md`); use that prompt for Level 2 work.
- Level 3 is optional technical depth or a focused investigation. It adds something distinct, a method,
  an analysis or an exhibit; it is not a longer restatement of the parent. Layout: an opening that says
  what question the investigation settles and why it mattered, then the setup, the method (including any
  rule fixed in advance), the results with their exhibit, what the result changed, and what it does not
  show. It reads as one story, not an appendix of artifacts.
- Navigation is not page copy: breadcrumbs and previous/next links are site features.
- All selected explanations belong on the portfolio. Repository links provide provenance and code;
  readers must not need to open them to understand a claim or discover its essential limitation.
- Preserve the supplied structure. Do not add page levels or turn every source report into a page.

PORTFOLIO EXPLANATION VERSUS EXPERIMENT RECORD (owner, 2026-10-28)
- Keep complete experiment logs in evidence/: run chronology, full configuration and result tables,
  failed attempts, reproduction steps and raw artefacts. Portfolio pages explain the questions,
  findings and engineering decisions those records support.
- Level 3 adds explanatory depth, not exhaustive coverage. Select experiments that advance one
  focused question; do not turn each trial into another method/results/caveats section. A detailed
  experimental design belongs on the page when understanding it changes the interpretation.
- Keep essential methods, comparison conditions, sample units, results and limitations beside the
  claims they support. Do not move adverse findings or material caveats out merely to shorten a page.
- Use two checks: can the reader understand and assess the decision without opening the evidence
  report? Does each retained detail change their understanding of the method, finding or limitation?
  If the first answer is no, restore essential explanation; if the second is no, link the detail as
  supporting evidence instead. Preserve source mappings when removing detail from portfolio copy.
- Organise around the reader's reasoning: question and stakes, relevant mechanism, investigation,
  finding and decision, then unresolved limits. Adapt this sequence to the subject; it is not a
  mandatory set of headings. Make clear why one finding motivates the next comparison.

OPENING AND CONTENT SELECTION
- Choose the opening from what readers must understand before the first decision. An approach needs
  its purpose and selection criteria; a testing strategy needs the decision and what each test can
  establish; architecture needs requirements and dependencies; an incident needs observed impact
  and the unresolved question. These are patterns, not mandatory headings.
- Parent context avoids repeated introductions, but does not forbid a concise useful definition.
- Write the core argument as concepts and connections before selecting experiments or numbers.
  Essential concepts are not the same as essential examples. Select examples with distinct jobs.
- When length is an issue, remove secondary branches before compressing the main explanation.
  Preserve the context, reasoning, comparison and material limitations of retained claims.
- L3 answers a focused follow-up question after its L1 or L2 parent. State that question and what
  depth answers it. Classify by explanatory responsibility, not length or technical difficulty:
  L2 owns a substantial topic; L3 deepens a particular part already explained. Necessary parent
  explanation cannot be relocated to meet a word count; full logs belong in evidence.

WORK BEFORE WRITING
1. Read the supplied evidence and correction notes. Identify each subject's question, decision,
   strongest example, measured or observed result, scope and practical implication.
2. Check quotations and numerical claims against the specific records. Track denominator, unit,
   game/model version and whether the samples are independent. Prefer an explicit corrected analysis
   to an older summary. Do not resolve a genuine source conflict by choosing the more impressive result.
3. Separate demonstrated behaviour, proposed designs, built-but-unused tools and current practice.
   Check who performed the work before assigning it to the author in first person.
4. Select the material that answers the reader's question. Do not inventory everything in the sources.

WRITING STYLE
- Use plain, precise language and connected paragraphs. Each paragraph develops one idea; each sentence
  should make the next easier to understand. Avoid long chains of method, numbers and caveats.
- For investigations, state the question before the procedure and explain the comparison before its
  numbers. Organise around what the reader needs to understand, rather than the order facts were
  collected. Each paragraph should prepare the next: question and method, assessment criteria, result,
  then interpretation and limits are explanatory jobs, not mandatory headings. End an experiment's
  account with the question or decision its finding motivates when the investigation continues.
- Define measures by what they establish and what they do not: “worthwhile” may mean adding a new
  contribution, not being correct. Name the counting unit before presenting results; explain changes
  between turns, messages, games and judgements. Introduce familiar descriptions before shorthand.
- Examples should reduce the reader's workload. Supply the relevant context first; use a faithful
  paraphrase if a quotation requires learning several player IDs or game mechanics. Preserve exact
  wording when it is itself evidence, and never present a paraphrase as a direct quote.
- Check cohesion after editing: can the reader explain why each paragraph follows the previous one?
  Fix missing reasoning or an unnecessary detour rather than merely adding transition words. The
  investigation-specific guidance is in .agents/skills/write-portfolio-page/references/portfolio-level-3-writing-rubric.md.
- For a Level 1 summary, usually use two short paragraphs: the question and approach, then the example,
  finding and implication. An incident may open the section when that is clearer. Do not make every
  section use the same sentence pattern.
- Length. These are guides, not quotas; never cut an explanation or a scope to hit a count. The test for
  cutting is whether a paragraph explains a different decision.
  Level 1 with L2 subjects: about 90–130 words per subject summary; the introduction 150–200.
  A self-contained Level 1 needs room for mechanisms, trade-offs and selected evidence: roughly
  1,500–2,000 words is a starting allowance, not a ceiling. Additional length must earn its place
  through essential explanation; it does not itself justify introducing L2.
  Level 2: about 1,200–2,000 words including captions and tables (the Level 2 prompt has the detail).
  Level 3: about 800–1,500 words; the method and results may take more room than on Level 2, because
  that is what the page adds.
- Explain why a result mattered. Replace “the check answered a different question” with the actual
  distinction. Replace “direction only” with what the sample supports and what remains unknown.
- Use one lead example per Level 1 summary. Save additional experiments for the relevant deeper page.
  A Level 2 page may need several examples when they explain distinct decisions.
- Use first person for supported contributions and choices. If a record says only “read by hand”,
  do not turn that into “I personally labelled every response”.
- Use established technical terms when they identify the work precisely. Explain each unfamiliar term
  on first use in the page: for example, “regression testing: checking whether a known failure returns”.
  Do not force a term into each paragraph, add a keyword list, or call terminology “official”.
- Connect component-level checks to end-to-end behaviour without treating them as equivalent. Treat
  test scope, scoring method, evaluator validation and experimental controls as separate choices.
- Use concrete examples for context rather than repeating the project's introduction in every section.
  Internal folder names, code identifiers and unexplained game roles do not substitute for explanation.
- Keep the main conclusion and material limitation together. A limitation should explain how to read
  the evidence, not serve as a generic disclaimer at the end of the page.
- Use specific link text that tells readers what they can explore next. If the destination is not built,
  leave an editorial link specification; do not fabricate a URL or publish a dead link.
- Integrate exhibits into the explanation: introduce what to notice, show the evidence, then explain
  its consequence. Do not add a chart when a short sentence or table is clearer.
- When a process requires readers to track handoffs, branches or review decisions, prefer a small
  labelled flow diagram with supporting prose. Introduce the purpose first; show who does what,
  the decision points and the outputs. Use prose to explain why the routing exists, what the evidence
  showed and its limits, rather than repeating every arrow. Label whether the diagram shows current
  practice, a historical experiment or a proposed workflow; never draw an unimplemented safeguard as
  an existing step. Keep a simple sequence in prose or a list when that is easier to follow.
- Let examples support the process explanation. Keep the decisive result and its essential scope
  on-page; put a deeper investigation in L3 only when it answers a distinct follow-up question.
  Complete run histories and exhaustive tables belong in evidence records.
- Avoid “The problem / The decision / The example / The result” labels repeated in every summary,
  rhetorical question-and-answer tricks, promotional adjectives, invented compound labels, and
  contrasts introduced only to make a choice sound impressive.

WHAT STAYS OFF THE PAGE
- The page is public. Repository bookkeeping that is honest in the records but reflects poorly stays off
  it: which tests were AI-written or unaudited, missing CI or uninstalled jobs, scripts that were not
  found, records kept outside version control, runs from uncommitted code, spend that was held, and any
  retracted number. The chapter's "Handle with care" list names them; follow it exactly.
- A fault the project caught is told as caught and what changed, with its scope, never hidden and never
  dramatised. Do not present every caught fault as a deep flaw that was fixed.
- A limitation that changes how to read a result always stays: leaving bookkeeping off the page is never
  a reason to drop a caveat.

EVIDENCE DISCIPLINE
- Do not invent results, causal explanations, personal contributions or implementation status.
- A deterministic check is repeatable, not automatically correct or exhaustive. State its relevant
  rule and input limits; “no model-call cost” is different from “free”.
- A replay of one situation is not an estimate of error frequency across ordinary use. Twenty samples
  of one case are not twenty independent situations.
- Correlation with an outcome is not proof that increasing a metric causes that outcome.
- Model agreement is not human validation. Blinding removes one source of bias; it does not establish
  that the labels are correct. Human labels also have scope and reviewer limitations.
- A requested setting is not proof of actual behaviour. Zero reasoning tokens do not establish that
  the model performed no reasoning. A shifted baseline does not by itself prove provider drift.
- A fail-open response to a failed call does not prevent an incorrect but valid classification.
- Measuring a quality deficit is different from applying a policy that excludes the model.
- A retained regression case can detect recurrence; it does not guarantee a failure stays fixed.
- Preserve essential sample context near a number. An authoring source note can hold the fuller
  provenance, but cannot rescue misleading page copy.

ONE WORKED EXAMPLE — STYLE AND REASONING, NOT FACTS TO REUSE

Example input:
- Purpose: explain deterministic evaluation in a Level 1 subject summary.
- A model supplied situation fields to memory search. Code recomputed their values from game state.
- The swing-vote field was correct in about 61% of 439 cases; always answering “no” scored about 83%.
- An earlier experiment using those fields to rank memories had found no benefit.
- The audit made that result inconclusive about the matching idea, because its inputs were unreliable.
- Computable fields were moved into code. Code checks still require correct rules and complete inputs;
  known-fault tests help establish that a checker can detect its intended failures.
- No overall improvement in gameplay was established by this audit.

Example output:

#### Checking agent outputs with code

When an answer can be computed from the game record, a deterministic check can assess it without a
model judge. One audit recomputed the situation fields a model supplied to memory search, then compared
them with its answers. The “swing vote” field was correct in 61% of 439 cases; always answering “no”
would have scored 83%.

That changed the interpretation of an earlier experiment. Ranking memories by unreliable fields
could not establish whether the matching idea itself was useful. The computable fields moved into
code. Those checks still depend on correct rules and complete inputs; testing them with known faults
helps establish that a passing result means something was actually checked.

**Link:** Explore code-based checks and how they were tested → Level 2.

Why this example works:
- It names the method and explains it through an actual task.
- The numbers include their sample and a meaningful baseline.
- The second paragraph explains the changed conclusion, not just the changed implementation.
- It keeps the finding scoped and does not invent an improvement in the wider system.
- It explains the limitation in practical terms rather than saying “directional” or “robust”.

FINAL EDITING PASS
Before returning the draft, check:
1. Can a new reader say what was evaluated, why this method was chosen and what the result changed?
2. Does each paragraph have one main job? Split dense paragraphs and remove secondary examples.
   Does the page follow its level's layout?
3. Are technical terms explained naturally, without diluting the engineering substance?
4. Does every numerical or factual claim have support, and does its wording preserve the sample's scope?
5. Have correlation, repeatability, model agreement or an implemented design been overstated?
6. Are the conclusions and essential limitations visible without following a link?
   Is anything on the "Handle with care" list on the page?
7. Does the copy follow the supplied reading structure and leave other sections intact?

OUTPUT
Return the requested Markdown page copy, or edit only the authorised files when working in a repository.
Keep source mappings, exhibit instructions and unresolved verification notes separate from public prose.
If evidence is missing, omit or qualify the affected claim and identify the missing support in a short
authoring note. Do not fabricate it. Do not append praise of the draft or repeat this checklist in the
public copy. Do not mark the result approved or publish it without that instruction.
```

## Using the reference pages as examples

The embedded example teaches paragraph-level writing. To teach a whole page, attach the reference for the
target level (listed under "How to use it") with a short input brief naming its sources and structure.
Exclude the editorial brief and source comments; only the "Page copy" section is the example. The Level 1
reference is approved; use the Level 2 and Level 3 references only after the owner approves them. Keep the
rules and target inputs.

When reviewing the next generated chapter, compare clarity, evidence handling and reader progression;
do not expect the same number of paragraphs, technical terms or examples regardless of the subject.
