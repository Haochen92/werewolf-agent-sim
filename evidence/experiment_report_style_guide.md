# Experiment Report Style Guide

## Purpose

Each report covers one experiment or feature segment of the project. Multiple reports will later be
synthesized into a cohesive portfolio writeup. Their purpose is to make a persuasive, evidence-backed
case for the author's engineering ability: what was built, which decisions mattered, and what the
results demonstrate. Select and explain the strongest material. A report need not catalogue everything
that happened or everything that could still be improved; the experiment log preserves that history.

## The Reader

Write for a software engineer who understands APIs, LLM prompts and the general technique at hand
(caching, retrieval, evaluation), but has **never seen this project**. They do not know our internal
names, pipeline stages, experiment labels or earlier decisions. Write for that reader, and do not turn
the doc into a beginner tutorial: explain *our* system, not the field.

Keep claims supported by the evidence, including the distinction between measured results and expected
benefits. Within that constraint, optimize for:

1. **A persuasive account of the contribution.** Lead with the achievement or decision the reader should
   remember, and select evidence that shows why it matters.
2. **Understandable on a first reading.**
3. **Relevance and proportion.** Give consequential decisions space; omit peripheral history and avoid
   repeating qualifications.
4. **Length**, optimized only once the first three hold.

Accuracy does not require exhaustive disclosure of every abandoned idea or missing experiment. It does
require keeping a qualification when removing it would materially change the reader's conclusion.

**Revising an existing doc is a structural edit, not a paraphrase.** Rewrite paragraphs whole, move
sections, delete repeated explanations, and give experiments unequal space when their weight is
unequal. Patching new sections into an old text leaves two voices and two vocabularies side by side,
which a reader cannot tell apart from two eras of truth.

---

## Core Principle

**Make the engineering judgment visible.** Explain why the design fits the problem and what supports
the decision. For an experiment, show the question, test, finding and resulting choice. For an
architectural decision, explain the requirements, alternatives and tradeoff. For a debugging case,
show the symptom, diagnosis, fix and verification. Do not force every topic into a failure-and-recovery
story or append a generic lesson when the judgment is already clear.

---

## Document Types

Not every report is a measured experiment. A few shapes recur — pick the one that fits and use its
skeleton. The Core Principle above and the Tone rules below apply to all of them.

- **Experiment report** (the default; full structure below). You ran variants and measured an
  outcome. Motivation → Design/Hypothesis → Iterations → Evaluation Setup → Results → Decision →
  Lessons → What's Next → Artifacts.
- **Build-journey log** (the chronological `experiment_log.md`) — the multi-phase superset of the
  experiment report. You ran a *sequence* of designs, experiments, and builds toward one shipped
  change, and the value is the **path**: what you tried, what got falsified, what you locked. The
  experiment report above is the single-experiment case; reach for this one when there are many beats
  over days or weeks.

  The log is a **loop of section-types**, each with its own treatment (see *Discipline for journey
  logs* below). It opens with an *orientation header* — what the document is, the rule that later
  entries supersede earlier ones, and pointers to companion docs — and closes with a *sources footer*.
  Between them the loop runs:
    - *① Motivation* — the gap, whether a problem in the current solution, an improvement, or
      something new. Stay charitable to the incumbent, and end on the root cause.
    - *② Design derivation* — the proposed design from first principles: mechanics first, alternatives
      rejected, virtues stated by construction.
    - *③ Implement → Verify → Decide* — the build-test-decide engine. It **repeats**: a pivot loops
      back to a fresh ②.
    - *④ Remaining questions / next steps, if needed* — distinguish unresolved evidence from work
      actually planned. Historical entries retain the uncertainty that shaped the decision at the time.

  This is the journey genre's fullest form, the inverse of the reference doc, which distils the *same*
  workstream destination-first. **Menu, not mandate:** a short log might be just ①②④. Exemplar:
  `evidence/gameplay/discussion/experiment_log.md` (its `report.md` is the paired reference doc).
- **Decision / design record.** You made an architectural or methodological choice, not a
  measurement — there is no dataset or results table, and forcing one is filler. Skeleton: *the
  tension* (the gap or conflict) → *the principle / design* → *alternatives considered and rejected,
  with reasons* → *the decision and its named tradeoff* → *Lessons*. The rejected alternatives are
  the most valuable part; they are where the judgment shows. (Examples: the structure audit, the
  provenance rationale, and the eval-architecture record, all in `evidence/refactor/`.)
- **Negative / non-feasibility finding.** You investigated and concluded *don't*, or *can't*. This is
  first-class, not a failed experiment — rejecting an approach with rigor is as portfolio-worthy as
  adopting one, and disproportionately convincing. Skeleton: *what you wanted to measure or build* →
  *why it looked feasible* → *what the investigation showed* → *the call (drop / defer / use a proxy)
  and why* → *Lessons*, stating what would change the verdict. (Example: concluding that deterministic
  decision-quality scoring isn't feasible, and substituting de-lucked outcome proxies.)
- **Reference / how-it-works doc.** A reader needs to understand or assess a finished mechanism. Lead
  with the current design and keep the journey in an optional case study. Skeleton: *orientation line*
  (a one-line mental model — a pipeline or map — so every identifier introduced later has somewhere to
  hang) → *the guarantee / contract* (present-tense: what holds, where it's enforced, how it's
  verified — not a changelog) → *the model / mechanism* → *verification* → *evidence* (a case study,
  benchmark, or rationale, written **verdict-first then forensics**) → *evidence limits or next steps,
  only where needed*. Apply the selection rules under *Limitations and scope* below. Use it when the
  artifact's value is the *current truth* of how something works,
  not the path to it; if the path *is* the point, use a journey type above. Exemplar:
  `evidence/agent_boundaries/report.md`.

### Discipline for reference docs (the part a fill-in template silently drops)

The shape is easy to copy; these habits are what made the exemplar trustworthy, and they erode first
under a fill-in-the-blanks template. They are *in addition to* the provenance-stamping and
direction-vs-magnitude rules below, which apply to every type.

- **Framework-behavior claims carry a version pin (+ a test where load-bearing).** "How LangGraph /
  LangChain / lib X behaves" is version-specific and the depth-reader's first thing to poke; assert it
  against the runtime fingerprint, and verify it empirically where the doc leans on it.
- **Select current, consequential limitations.** Check that a gap still exists before describing it
  as current. Include it where it changes the interpretation of a result, the suitability of the
  design, or the credibility of a claimed benefit. Keep dates when needed to distinguish versions.
  Severity labels belong in an operational risk register when one is needed; reader-facing reports
  should explain the actual consequence. Minor historical gaps can remain in the log.
- **Separate verdict from forensics.** Lead the case study with a short outcome paragraph and a
  "skip by subhead" signpost when useful, then the detail. Keep a canonical evidence source; a portfolio
  summary can link to it without repeating the full investigation.
- **Pitch at the reader's altitude — drop nitty-gritty, don't reconcile it.** A reference doc serves a
  *busy technical reader*: current design, reasons for the choices, pivotal results and relevant
  evidence boundaries. It is **not** a forensic audit (commit-level provenance, which exact script ran,
  edge-case thresholds belong in the source-map/ledger or nowhere). When two statements conflict over a
  *mechanism* detail that doesn't move the narrative, **delete the over-specific claim rather than
  reconciling it** — reconciliation adds the very noise the reader didn't want and re-introduces the
  detail you should be cutting. Keep the honest *highlight* (e.g. "the pieces had never run end-to-end")
  and drop the *plumbing* that proves it. (You may still dig forensically to learn *which* claim to cut —
  just don't put the dig in the doc.)

### Discipline for journey logs (the per-archetype treatment a flat template flattens)

A journey log is the loop above, but each archetype gets a *different* treatment — and those treatments,
not the section order, are what keep a long log honest and readable. They erode first under a
fill-in-the-blanks skeleton. (In addition to the provenance and direction-vs-magnitude rules below,
which apply to every type.)

- **Cross-cutting — chronological integrity, and one home per argument.** An earlier section must not
  know a later section's result: show a falsified or revised design **in place** rather than editing it
  away (the falsified beat is often the most instructive), and treat a `(§N)` forward-pointer as
  *navigation*, not laundering. And argue each point **once** — later sections point back (`argued at
  §6`) instead of re-deriving, the main source of bloat in a long log.
- **① Motivation — be charitable to the incumbent.** Explain why the thing you're replacing was a
  *defensible* choice before giving its failure mode and root cause; strawmanning the predecessor
  cheapens the log. End on the precise root cause — it is the target everything downstream aims at.
- **② Design — mechanics-first, and stated as a proposal.** Introduce what the design *is* (first
  principles + mechanics) before what it buys; show the alternatives weighed and **rejected** (the
  rejections are where judgment shows); state virtues **by construction, never as validated results** —
  validation is ③'s job, and importing it here is laundering. Replacing a prior design ⇒ map its
  weaknesses **1:1**.
- **③ Implement → Verify → Decide — name the risk, lead with the problem.** *Implement:* present each
  refinement **problem → fix** (the bold lead states what broke, then the mechanism — not the reverse),
  and close the section with a short provenance line (SHA / config / file) rather than threading
  identifiers through the prose (see *Placement* under Artifacts). *Verify:* every probe **names the one risk it isolates**
  ("*Catches:* …") → result → decision; a probe reported without the risk it tests is a fact-dump, and
  **falsification is first-class** — a killed approach is shown, diagnosed, and its recovery traced,
  never deleted. *Decide:* adopt / pivot / kill; a pivot re-enters ②.
- **④ Remaining questions — preserve the decision's context.** Keep historical uncertainties with
  the decision they affected and record later resolutions when they occur. Do not copy every old
  question into a present-day limitations list. Use *Limitations and scope* below to select what the
  companion report needs.

### Limitations and scope

**Lead with the supported contribution.** State what was achieved or learned, give the evidence, then
qualify its reach where necessary. A reader should understand the result before being asked to assess
its boundaries. Keep a material qualification adjacent to the claim, even in a short portfolio summary.

Before including a limitation, ask: **Which claim or design decision does this qualify, and how would
the reader misunderstand it without this information?** If neither answer is concrete, it probably
belongs elsewhere or can be omitted. There is no required number of limitations and no mandatory
standalone section.

| Kind of information | Treatment |
|---|---|
| Evidence limit: small sample, missing comparison, unresolved confound | Put the boundary beside the affected result. Use a short shared section only when several claims depend on it. |
| Current defect that materially affects the claimed behaviour | State its consequence and the actual mitigation or status. Do not rename it as a future opportunity. |
| Accepted tradeoff or known provider behaviour | Explain it with the design decision and why it was acceptable for this use case, where that reasoning is recorded. |
| Optional optimization or unsupported use case | Put it in scope, alternatives or future work if relevant. An unbuilt feature is not automatically a defect. |
| Resolved incident, obsolete measurement or maintenance reminder | Keep it in the log or implementation documentation unless it explains a consequential decision in the report. |

**Describe the exact missing evidence.** A tested system can lack a controlled comparison of one design
choice. A fix can pass local checks without having run at scale. Neither means the entire system is
"untested." State what was checked and what conclusion remains unsupported. Do not invent validation
or a rationale for skipping it; do not imply that historical tests validate today's exact version.

**Keep process claims as specific as the evidence.** Prefer "For the tell detector, cached and uncached
outputs were compared against labelled examples before caching became the default" to "Every caching
change is quality-tested before deployment." One evaluated change demonstrates a skill without claiming
an exceptionless process. A later improvement in practice can be described when its chronology is supported.

**Use direct, proportionate wording.** These are editing examples, not claims to copy into unrelated reports:

| Avoid | Prefer |
|---|---|
| "The extraction prompt was deployed untested." | "Extraction quality was evaluated separately; the effect of changing prompt order was not isolated in a controlled comparison." Use the first clause only if the relevant evaluation is documented. |
| "No whole-game cached share exists." | "The probe demonstrated reuse on selected requests; game-wide savings have not yet been established." |
| "Caching damages reproducibility." | "The detector's cached outputs varied more between runs, but precision and recall were comparable on five games and 40 labelled cases. Evaluations use stored outputs so the evaluated run remains inspectable." |
| "The optimization is incomplete: cross-player caching is unbuilt." | "The current layout supports reuse between a player's turns. Sharing more context across players is a further optimization." |

Do not repeat the same caveat in the overview, results, decision and closing list. Narrow the claim once
and keep the supporting detail in one place. A serious qualification must still be visible wherever a
standalone headline would otherwise mislead.

**Do not turn accepted uncertainty into a promised task.** Use "deferred" or "planned" only when that
is the actual status. If no comparison is planned, state the evidence boundary without creating a
backlog item. Do not infer a missed deadline, urgency or severity merely because a test is possible.

---

## Structure

### 1. Motivation (short)

What problem does this experiment address? Frame it as a gap: "we had X, but not Y, which meant we couldn't Z." No background tutorial on the field, but do not assume the reader knows the project (see *The Reader*): say what each component does before naming it. One paragraph.

### 2. Design and Hypothesis

What approach did you take and why? If there were alternatives you considered and rejected, say so briefly with the reasoning. If the design has multiple iterations (prompt versions, architecture changes), introduce the first version here with the hypothesis it tested. Subsequent versions go in the iterations section.

### 3. Iterations (if applicable)

For each iteration beyond the first:

- **What changed** — the concrete modification (prompt wording, schema order, architecture)
- **Why** — what hypothesis or problem motivated the change. Link it to a specific observation or failure from the prior version. "v1 showed X, so we hypothesized that changing Y would fix it."
- **What happened** — brief result, connected back to the hypothesis. Did it confirm or surprise you?

Do not present iterations as a flat list of "Version 1 / Version 2 / Version 3." Each version should flow from the previous one's findings.

This flow-from-the-previous rule fits **prompt or parameter tuning**, where the versions form a
chain. A **structural one-shot redesign** (a graph, schema, or pipeline rewrite judged by a single
post-hoc A/B per the variant-versioning policy in `CLAUDE.md`) is *not* a chain — report it as one
design decision and its A/B, not a forced v1→v2→v3 progression. Two shapes, both valid.

### 4. Evaluation Setup

How you measured. Keep this factual and concise — dataset size, judge model, metrics, any diagnostics added mid-experiment. If you added a metric partway through (e.g., attribution direction), explain what prompted the addition.

### 5. Results

Present data, then interpret it. For every table or comparison:

- State the headline finding in one sentence before the table
- After the table, address anything surprising or counterintuitive
- If an outlier or confound affected results, identify it and show results both ways
- State the sample size (N) with the result, and **separate direction from magnitude**. At small N,
  "memory-on won 4 of 4" is a *direction* you can believe and a *magnitude* you cannot — say which
  you are claiming. State the limitation itself ("4 of 4 games; too few to size the effect") rather
  than a shorthand grade like "direction-grade", and never imply a precision the sample can't support.
  Small-N over-claiming is this project's most likely failure mode; the headline metric stays the win
  rate, with proxies and N qualifying it.
- **Distinguish measurements, expectations and implementation status.** Report measured benefits with
  their scope. Label forecasts as estimates. For a shipped change, say what was verified and which
  benefit remains unmeasured; passing functional checks does not establish a cost or quality improvement,
  and lacking a benefit measurement does not mean no testing occurred.

Do not let tables speak for themselves. The reader should never have to infer what a table means.

### 6. Decision and Tradeoffs

State what you chose and why. Explain material tradeoffs or a credible alternative where they help the
reader assess the decision. Do not manufacture a drawback or an adversarial objection for every change.
If a cost reduction showed no quality loss on the evaluated sample, state that result with its scope.

Bad: "We chose v2 because it had the highest scores."
Good: "We chose v2 for its higher adoption accuracy and lower over-attribution rate. v2 does have the highest under-attribution (19%), which is the more dangerous failure mode since it makes useful strategies look unused. We accepted this because the schema reorder already substantially reduced both error types from v1, and 72% accuracy is sufficient for Phase 1's purpose of surfacing broad adoption patterns."

### 7. Lessons (the reflection)

Include lessons when they add insight beyond the decision already explained. A concrete diagnosis or
well-reasoned architectural choice can demonstrate ability without an extra "lesson learned" paragraph.
When a transferable lesson is useful, it should be:

- Stated as a transferable principle, not a project-specific observation
- Grounded in specific evidence from the experiment

Examples of good lessons:
- "For weak models, prompt consistency with the rest of the system matters more than prompt precision in isolation." (grounded in: DO/DON'T rules failed despite being more precise, because every other prompt used conversational style)
- "Structured output field ordering affects reasoning direction — fields generated before the action become prospective commitments, fields after become retrospective rationalizations." (grounded in: schema reorder was the single largest quality improvement)

Examples of bad lessons:
- "Prompt engineering is important" (too vague, no evidence link)
- "We learned that v2 is better than v3" (project-specific fact, not transferable)

### 8. What's Next

What does this experiment enable or block? If the next step depends on a condition (enough data, an ablation result), state the condition. If this experiment changed your plans for something downstream, say so.

This section is optional. Include intended work or a relevant condition for revisiting a decision, not
every possible experiment. Separate optional ideas from commitments.

### 9. Artifacts

Table of files produced (eval sets, results, configs). Keep it factual.

**Stamp the provenance.** Record the lineage that produced the results — the git SHA /
`runtime_fingerprint`, the config, and the input datasets (by name, ideally by content hash). A
number a reader cannot trace back to the commit and config that made it is not reproducible, and the
report is where that pointer naturally lives. This is the same back-reference the eval-architecture
convention requires of every record — see `CLAUDE.md → Eval Architecture` and
`evidence/tracing/fingerprinting/report.md`.

**Placement — what stays in the prose and what moves out.** Keep in the text every number a reader
needs to assess a claim (the N, the before and after, the cost against the estimate). Move detailed
configurations, raw usage records and commit identifiers to an evidence section, a case study's
forensics, a section-closing provenance line, or a linked file. Identifiers threaded mid-sentence make a
reader parse plumbing to reach the claim.

**Co-locate artifacts with the report.** All files that support the report — eval sets, eval results, eval configs — should live in the same `evidence/<experiment>/` folder alongside the report. This keeps the experiment self-contained and reviewable without hunting across directories. When artifacts are generated elsewhere (e.g., `eval_results/`), move them into the evidence folder and clean up the originals.

**Pointer discipline (how to cite code).** Cite code by handles that survive a refactor. Prefer a
console-entry name from `pyproject [project.scripts]`, or a package path whose README will still
orient a reader after a rename. Reserve deep `file:line` anchors for a claim that is load-bearing —
where the exact line *is* the point — and expect a reference doc to maintain those anchors as the
code moves. A record does not chase moving code: it freezes the pointer with a provenance stamp
(the SHA / `runtime_fingerprint` above) instead. Frozen evidence scripts carry a FROZEN RECORD
header — cite them as records of what ran, not as live code you are pointing a reader at. The reason
is empirical: the linkage audit found path-level pointers rot at every refactor while console-entry
names survive.

---

## Tone and Style

**Reflect, don't narrate.** After each major finding, add one sentence on what it means or what you'd do differently. Don't add filler — reflection is concise.

**Address assumption corrections explicitly.** If you started with assumption X and the data showed Y, that's a finding worth highlighting, not an embarrassment to bury. "We initially assumed over-attribution was the primary risk. At n=120, both directions appeared in roughly equal measure, which reframed our optimization target." The narrative of "assumed X, tested, found Y, adjusted" demonstrates learning.

**Frame impact as capability unlocked when no downstream metrics exist yet.** If you haven't measured end-to-end impact, don't fake it. Instead, describe what was unobservable before and is now observable. "Before this work, we had no way to distinguish strategies agents rely on from ones they ignore. This makes strategy quality measurable for the first time."

**Explain material tradeoffs in context.** State what was accepted and why it fit the requirements.
Avoid presenting every known constraint as an unresolved flaw, or inventing a sacrifice when the
evidence shows a useful improvement within the tested scope.

**Keep tables interpreted.** Never present a results table without stating the takeaway before it and addressing surprises after it.

**Avoid pure-fact dumps.** A "Challenges" section that lists five bullet points is an experiment log. A "Challenges" section that explains what each challenge taught you about the system is a reflection.

### Prose legibility (how a sentence reads)

Every rule above decides *what* to say and *in what order*. None of them decides how a sentence reads.
A report can pass all of them and still be hard work: ideas fused into one clause, hyphenated
modifiers stacked three deep, an em-dash breaking every line. Concision means cutting filler, not
compressing what remains — dense prose is a separate failure, and the checks above do not catch it.
The rules below are mechanical; apply them on a final read-through.

- **One main idea per sentence, one reasoning step per paragraph.** Keep the subject and verb close
  together. When a sentence welds three ideas into one clause, split it into three sentences; when a
  paragraph makes two inferential jumps, split it at the jump.
- **Say what a component does before using its name.** "The query writer (the call that turns the game
  state into a memory search)" before "the situation prompt". An internal name met cold is a lookup the
  reader cannot do.
- **Replace vague evaluations with the observation.** "Cleanly", "robust", "works well",
  "direction-grade" tell the reader you were satisfied, not what you saw. Write the observation ("15,001
  of 15,005 prompt tokens served from cache") or the limitation ("one game per side").
- **Unpack stacked modifiers.** A pile of hyphenated qualifiers ("criticality-ordered, freshness-dated,
  construction-enforced-but-unverified") buries the verb. Turn the modifiers back into clauses:
  "ordered by criticality, dated for freshness, and enforced by construction though not yet verified."
- **Cap em-dashes at about one per paragraph.** An em-dash suspends the sentence; several in a row
  fracture it. Keep the interruption that earns its place and convert the rest to periods, commas, or
  parentheses.
- **Introduce shorthand before you lean on it.** The portfolio is read by outsiders — interviewers
  included, as the reference-doc rules already assume. A term used before it is defined costs that
  reader a re-read. Define it once, in plain words, on first use.
- **Prefer a plain sentence to an aphorism.** A compressed maxim reads well the first time and obscures
  on the second. State the point directly, then crystallize it only once it is already clear.

**Exemplar — this guide, before and after.** An earlier draft described the journey-log loop in a
single breath:

> *Dense (avoid):* "It is a loop of section-types, each with its own treatment, bookended by an
> orientation header ('what this is' + the chronological-supersession contract + companion-doc
> pointers) and a sources footer: ① Motivation (the gap …) → ② Design derivation (…) → ③ Implement →
> Verify → Decide (…) → ④ Limitations (…)."

The current *Build-journey log* entry says the same thing across a short paragraph and a four-item
list. It is longer and easier to read: one idea per sentence, the shorthand ("orientation header,"
"sources footer") introduced in plain words, and its one em-dash pair spent where it clarifies. Writers
imitate the prose they see more reliably than the prose they are told to write, so the guide tries to
model the voice it asks for.

### Plain presentation (how a result reads to someone who must defend it)

The rules above make sentences readable. A section can still be hard to follow when it reports a
technical result: the owner, who must explain every claim in an interview, could not follow several
reports that passed every rule above. Six habits fixed them (2026-10-22). None of them drops a detail
of a finding that is kept; detail moves, it is not deleted.

1. **Ask the question in plain words, then answer it first.** Open each part with what it asks
   ("Are the values correct?") and a bold one-line answer, before any method.
2. **Context before numbers.** Say what was measured, against what, and how, then give the number.
   A percentage the reader cannot place is noise.
3. **Counts a reader can picture, not fitted coefficients.** Prefer "a loser's good move was called
   positive 23% of the time, a winner's 83%" to "+0.80 per unit of side won". If a fit summarises
   the counts, put it in a small box after them.
4. **One comparison per table.** Keep only the columns the point needs; mention the rest in the text.
5. **Findings apart from "how sure we are".** State what was found, then give a separate short list:
   what it rests on, what it holds across, what could still explain it, what was not checked.
6. **Inside a kept finding, nothing is lost.** Every number, N and caveat of a finding you keep
   appears in the new version or in the log. Check it item by item before replacing a section, and
   put back anything that is nowhere else. Which findings to keep is a separate choice: a finding
   stays if it played a key role in reaching today's design or shows a skill nothing else shows;
   redundant findings and dead ends that shaped nothing stay in git history.

**Exemplar.** `evidence/extraction/observation_quality/report.md` §4 before and after (the earlier version is
in git history at `2382b34c`). Before: a regression fit, two coefficients, and a paragraph on how to
read "per step of grade". After: three facts each observation carries, a 2×2 table of how often moves
were called positive, the halo stated in one line, a "how sure we are" list, and the fit in a box. The
owner could not explain the first and could explain the second.

---

## Anti-Patterns to Avoid

- **The fait accompli.** Presenting the final design as if it was obvious from the start. Show the path.
- **Orphaned tables.** Data without interpretation. Every table needs a "so what."
- **Buried corrections.** Hiding assumption changes in subsections. Pull them up as findings.
- **Impact theater.** Claiming vague impact without evidence. Either show numbers or honestly frame what was enabled.
- **The limitations inventory.** Copying every unrun test, optional optimization and provider caveat into
  one ranked list. Select the qualifications that affect the report's claims and place them in context.
- **Overstating a gap.** Calling a system "untested" because one comparison is missing, or describing an
  accepted tradeoff as a failure. Match the wording to the specific evidence that is absent.
- **Universal process claims.** Turning one successful quality check into "we always test before
  deploying." Demonstrate the practice through the actual case.
- **Achievement buried under caveats.** Opening with a list of what was not done before explaining what
  was accomplished. Lead with the supported result and retain the qualifications needed to assess it.
- **Flat iteration lists.** "v1 did X. v2 did Y. v3 did Z." without causal links between them.
- **Lessons that don't generalize.** "We learned v2 is better" is not a lesson. "Schema field ordering affects reasoning direction in structured output" is.
- **Density mistaken for concision.** Fusing five ideas into one clause, stacking hyphenated modifiers, chaining em-dashes. The argument can be complete and the prose still unreadable — this is the failure the *Prose legibility* rules catch, and the one most common in practice. Cutting filler does not fix it.
- **Aphorism density.** Every sentence a crystallized maxim. One or two land; a page of them exhausts the reader. Say the thing plainly, then crystallize only what earns it.

---

## Checklist Before Finalizing

- [ ] Does the opening make the contribution and its value clear?
- [ ] Are consequential choices explained, with material tradeoffs where relevant?
- [ ] Does every iteration link back to a specific finding from the prior version?
- [ ] Does every table have a stated takeaway?
- [ ] Are assumption corrections surfaced as findings, not buried?
- [ ] Do explicit lessons add insight, with evidence, rather than repeat the decision or state a generic maxim?
- [ ] Is impact framed honestly (metrics if available, capability unlocked if not)?
- [ ] Would a reader who skips the tables still understand the narrative from the prose?
- [ ] Can an independent reader parse each *sentence* on the first pass — one main idea per sentence, roughly one em-dash per paragraph at most, internal shorthand defined before it's used? (This tests the sentences; the check above tests the argument — different failures.)
- [ ] *(Plain presentation)* Does each part ask its question plainly and answer it first, give context before every number, use counts over coefficients, keep findings apart from "how sure we are", and keep every number, N and caveat of each finding it keeps?
- [ ] Read as the outside engineer of *The Reader*: does any passage need unstated context, use an unexplained internal term, or make more than one reasoning jump? Rewrite those passages.
- [ ] Are measured benefits, estimates and implemented changes distinguished, with the actual scope of verification?
- [ ] Does every included limitation qualify a specific claim or decision? Are optional ideas and historical loose ends kept out of the current limitations list?
- [ ] Does each qualification say plainly what remains unknown and why it matters, without implying a broader failure?
- [ ] Are material qualifications adjacent to the claims they affect, rather than buried in linked detail or repeated throughout?
- [ ] Are process claims supported at the stated scope, without turning one tested case into an "always" claim?
- [ ] Does future work reflect actual plans, rather than promises invented to resolve every unknown?
- [ ] Is every argument explained fully once, with later mentions pointing back (not re-argued in the intro, results, lessons and gaps)?
- [ ] Has any historical finding drifted into a universal or current claim? (Date it, scope it, or cut it.)
- [ ] Are vague evaluations ("cleanly", "robust", "direction-grade") replaced by the observation or the limitation?
- [ ] Did you pick the right document type (experiment / build-journey log / decision record / negative finding / reference doc)?
- [ ] Is the provenance stamped (commit / fingerprint / config) so results are traceable?
- [ ] Are code pointers refactor-stable (console names / package paths), with deep anchors only where load-bearing?
- [ ] Is N stated, and direction separated from magnitude where the sample is small?
- [ ] *(Reference docs)* Does each framework-behavior claim carry a version pin (+ a test where load-bearing)?
- [ ] *(Reference docs)* Are included limitations current, consequential and proportionate? Are historical measurements identified as historical?
- [ ] *(Reference docs)* Is the verdict separated from the forensics (skim layer before depth layer)?
- [ ] *(Journey logs)* Does no earlier section depend on a later result — falsified designs shown in place, `(§N)` used as navigation only?
- [ ] *(Journey logs)* Does each refinement/fix lead with the problem, then the mechanism (not fix-first)?
- [ ] *(Journey logs)* Does each design state its mechanics before its benefits, and each experiment name the risk it isolates?
- [ ] *(Journey logs)* Is each argument made in one place and pointed back to elsewhere (no cross-section re-derivation)?
