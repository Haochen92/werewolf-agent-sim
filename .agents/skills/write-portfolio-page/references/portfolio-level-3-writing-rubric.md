# Level 3 writing guidance and review rubric

Status: provisional. Editorial reference:
[the field-audit draft](../../../../writeup/evaluation/code_checks/field_audit.md). This guidance has not yet been tested
on another investigation or approved as the final reference.

Use the general [portfolio prompt](portfolio-writing-prompt.md) and the clarity principles in the
[Level 2 rubric](portfolio-level-2-writing-prompt.md), with the adaptations below.

## Editorial responsibility

The writing pass owns phrasing, structure and readability. A separate verification pass owns checking
facts, statistics, code and records. Work from the supplied verified facts and corrections. When a
claim is unclear, contradictory or appears too strong, flag a specific question for the verifier rather
than silently inferring a replacement fact or starting an implementation audit.

Preserve this distinction in the completion note: “editorially revised” is not “factually verified”.
Changing a sentence's scope can change its claim; identify substantive changes for the verifier.

## What changes at Level 3

Level 2 explains a substantial subject through methods and examples. Level 3 develops one selected
investigation so that a reader can understand its setup, reasoning and interpretation. The language
should remain as clear as Level 2; the additional depth comes from explaining details that Level 2
summarises, not from denser sentences or more jargon.

Keep the Level 2 principles of reader orientation, paragraph clarity, narrative economy, technical
accessibility and integrated exhibits. Adapt the expectations as follows:

| Level 2 expectation | Level 3 adaptation |
|---|---|
| Explain the relevant approaches or causes across a subject | Explain the alternatives that matter to this particular investigation; no broad survey required |
| Use a featured story within several subsections | The whole page may be one investigation; no separate featured-story section required |
| Select the setup details needed to assess the main finding | Explain the units, reference values, exclusions and decision rules needed to follow the analysis |
| Summarise what the experiment established | Distinguish measured results, derived estimates, assumptions and unresolved interpretations |
| Add depth beyond the chapter summary | Add a specific explanation beyond the Level 2 parent, while retaining enough context for direct arrival |

## Investigation write-up versus experiment log

Owner rule, 2026-10-28: experiment logs generally belong in `evidence/`. A portfolio Level 3 explains
one mechanism or investigation through selected evidence; it is not the complete record of its runs.
Keep chronology, full variant tables, debugging attempts and reproduction details in the linked
evidence report unless they change how a reader assesses the finding.

A useful progression is question and stakes → relevant mechanism → investigation → finding and
decision → limits. Adapt it to the subject rather than repeating a method/results/caveats template
for every trial. Give central findings more attention than supporting checks, and explain what each
comparison resolves before introducing its numbers. An implementation-and-calibration page should
make the policy understandable before asking the reader to evaluate its calibration.

The page must remain assessable without opening its evidence links: retain essential methods,
sample units, comparisons, results and limitations, including adverse findings. Ask whether each
detail changes the interpretation. If it does not, keep it in evidence and preserve its source link.
Do not create another page level merely to hold overflow from an L3, or use optional links to hide
uncertainty. Depth is an explanation of how or why, not a count of experiments included.

## Writing a connected investigation

Owner guidance, 2026-10-28: organise around what the reader needs to understand, not the order in
which facts were collected. Apply these principles to investigation sections at any portfolio level.

1. **Question before procedure.** Establish what the experiment needs to answer before describing
   the replay, sampling or scoring. “Were agents passing when they had something useful to say?”
   gives the replay a purpose. Use a direct statement or question naturally, not a repeated formula.
2. **Comparison before shorthand.** Explain “responses generated from passed turns versus voluntarily
   posted messages” before abbreviating either group as “forced lines” or using internal labels.
3. **One explanatory job per paragraph.** Question and method → assessment criteria → result →
   interpretation and limits is a useful progression, not a mandatory set of headings. Avoid making
   every paragraph establish a mechanism, report numbers and qualify several different claims.
4. **Define what a measure establishes.** For example, “worthwhile” means adding a fact, interpretation
   or question, not necessarily being correct. Give that meaning before asking the reader to assess
   the result; a metric's name alone is insufficient.
5. **Numbers after orientation.** Name the comparison and counting unit first. Keep denominators
   understandable and explain switches between turns, messages, games and judgements. Preserve the
   distinctions needed to assess the evidence rather than compressing unlike units into one result.
6. **Examples should reduce effort.** Explain the relevant situation before showing the example.
   Prefer a faithful paraphrase when a quote requires learning several player IDs or game mechanics.
   Keep exact wording when it is the evidence being examined; never label a paraphrase as a quotation.
7. **Finding and scope together.** State what the result suggests, then explain the limitation that
   restricts that conclusion nearby. Avoid scattering generic disclaimers through every sentence,
   but do not postpone a material caveat until after the reader has formed a stronger interpretation.
8. **Connect the next step.** When the investigation continues, end with the question or decision
   motivated by the finding. “Could changing the instruction release more useful speech without
   increasing repetition?” explains why the next experiment is needed.
9. **Retain useful technical language.** Define terms such as blind judgement, calibration set or
   ablation where they identify the method precisely. Replace awkward shorthand, not technical
   substance. Clear language does not mean removing the terms an engineer needs to discuss the work.
10. **Select evidence, preserve the record.** Keep the method, findings and limitations needed to
    assess the argument. Link exhaustive variants and run histories in evidence, following the
    portfolio-versus-log rule above.

**Cohesion check:** after each paragraph, can the reader explain why the next follows? If not, supply
the missing reasoning, reorder the material or remove the detour. Transition words alone cannot
repair a missing connection.

## Selecting a Level 3 page

The question is whether the material deserves a separate reading experience or is simply a good
subsection. A vivid example does not earn a page, and neither does length, technical complexity or the
existence of a detailed source report.

Level 2 explains an engineering subject and the decisions within it. Level 3 examines one part of that
subject closely enough to understand how it works or how its conclusion was reached. That can be an
analysis, a mechanism, an implementation walkthrough or a debugging investigation. An unresolved cause
does not disqualify a page; a carefully bounded uncertainty is a defensible outcome.

All six must hold. If one fails, keep the material on Level 2, combine it with another investigation, or
leave it unpublished.

| Criterion | What must be true |
|---|---|
| Distinct reader question | The page answers a specific question beyond the Level 2 explanation |
| Substantial additional value | It adds a method, analysis, mechanism, implementation walkthrough or inspectable evidence, not more chronology |
| A reason to separate it | Explaining it properly would interrupt the parent's main argument or need a different depth of attention |
| Optional for the parent | Level 2 still explains its decision, finding and essential limitations; a reader can stop there without misunderstanding the work |
| A bounded scope | A clear beginning and end: what it examines, how, what it establishes and what remains unresolved |
| Defensible content | The author understands the work, the evidence supports the claims, and there is enough substance to justify a page |

**Anchored in the parent (owner 2026-10-25).** Every Level 3 page belongs to a Level 2 subsection that
covers the same finding, or a passage within one; its link sits there. The rule runs one way: a
subsection does not need a Level 3 page. When a Level 3 page is added, dropped or renamed, update the
parent subsection with it, so the two stay in sync.

Two tests make the criteria practical:
- **Remove the link.** Does the parent still make sense and represent the finding honestly?
- **One sentence.** Complete "Readers will learn how…". If the answer is only "see more details about the
  example", the proposal is not specific enough.

Record each candidate in five short fields: **reader question · added value · why separate · what stays on
Level 2 · verification needed**. "Verification needed" lists the consequential claims about how something
works or how an experiment was run (mechanism, configuration, version), to be checked against the
implementation and records of that time before publication. Reading today's code alone may not explain a
historical experiment. Exact figures are taken from the reports as they stand.

## Copyable instruction supplement

```text
This is a Level 3 editorial pass. Revise the supplied investigation for phrasing, structure and
readability, using the general portfolio writing rules. Do not independently verify source records,
code or statistics; a separate verifier handles those. Preserve supplied facts and identify any
substantive claim changes or unresolved factual questions in an authoring note.

Inputs:
- Existing draft and authorised destination: [INSERT]
- Parent Level 2 summary or brief: [ATTACH]
- Verified facts, corrections and scope limits: [ATTACH]
- Publication constraints: [ATTACH]

Open with the question the investigation addresses, why it mattered and its main conclusion. Then
explain the setup, method, results and consequence in the order a reader needs them. Do not withhold
the outcome for suspense or follow chronology when it obscures the reasoning.

Write a focused explanation, not an experiment log. Keep full run histories and variant tables in
linked evidence unless they are necessary to assess the result. Preserve essential methods, sample
units, adverse results and limitations on the page. Give each experiment a reason to appear and
connect its finding to the next question or decision; do not repeat a full report template per trial.

State the question before the procedure and the comparison before its numbers. Define what the
measure establishes before interpreting it. Give each paragraph one explanatory job; introduce
examples with enough context to reduce the reader's workload, using faithful paraphrase unless exact
wording matters. Keep useful technical terms and explain them. Put the finding and its material limit
together, then connect it to the next question or decision. Check that each paragraph follows from
the previous one through reasoning, not merely a transition word.

Define unfamiliar mechanisms before discussing their performance. If a feature called “gating” only
reorders results, explain that behaviour rather than relying on the label. Use the same precise term
throughout.

Make counting units explicit: a field comparison, response, decision and game are different units.
When several counts appear, explain their relationship from the supplied facts. If that relationship
is missing, ask the verifier; do not guess it or let a large number imply independence.

Separate confirmation, rejection/reopening and unresolved outcomes in a decision rule. A table can
help readers see different thresholds. Explain what passing the rule establishes and what it leaves
open. Do not convert the rule's historical name into a stronger claim of proof.

Present results with an explanation of their pattern. Accuracy alone may hide different errors;
include a confusion table or explanation when it changes the interpretation. A constant baseline
can contextualise a score without being a useful deployed solution.

Label estimates and assumptions explicitly. A formula earns space only when its assumptions and
meaning can be explained. If support is unclear, mark it for verification or propose omitting it;
do not make an illustrative calculation sound like an observed effect.

Keep population and scope mismatches beside the conclusion they qualify. Explain whether the audit
used the same roles, cases and game version as the experiment being reconsidered. Separate a reason
to reopen a result from direct evidence that the original result was wrong.

Give the main investigation priority. Implementation dates and later follow-ups belong only where
they explain the consequence or an unresolved boundary. Use connected prose around exhibits; avoid
turning the page into a log, inventory or gallery.

Retain the parent's main finding and essential caveats on the parent; this page supplies the deeper
explanation. A reader should not need repository links to understand either page.

Before returning the revision, apply the Level 3 rubric. Report editorial changes and questions for
the verifier separately. Do not claim factual validation or publication approval.
```

## Additional review criteria

Use the Level 2 rubric's 0/1/2 scale as an editing aid, not a validated quality score. These criteria
assess whether the explanation is clear; factual correctness remains the verifier's responsibility.

| Criterion | Clear presentation requires | Reason to revise or flag |
|---|---|---|
| Added depth | A named method, analysis or implication beyond the parent | The same finding repeated at greater length |
| Narrative cohesion | Questions precede methods, comparisons precede numbers, and findings motivate subsequent steps | A sequence of facts whose connections the reader must reconstruct |
| Method inspectability | The reader can identify inputs, reference values, comparisons and exclusions | “Every field was checked” when some need a different method |
| Counting units | Denominators and related counts are explained without suggesting false independence | Field comparisons described as separate situations |
| Decision-rule precision | Conditions and unresolved outcomes are distinguishable | Different confirmation and reopening thresholds collapsed into one bar |
| Analytical assumptions | Measured values, calculations and hypotheses are clearly separated | An attenuation estimate presented as lost benefit measured in the original experiment |
| Scope alignment | Differences between audit and original experiment are visible near interpretation | Wolf-side results used to quantify town-side errors without justification |
| Bounded consequence | The page states what changed and what still needs testing | Reopening an inconclusive result described as evidence the feature works |

An unclear assumption or unit should become a concrete verification question. Do not conceal the issue
with smoother prose. Once verified, incorporate the answer without importing unnecessary bookkeeping.
