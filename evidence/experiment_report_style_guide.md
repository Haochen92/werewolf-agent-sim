# Experiment Report Style Guide

## Purpose

Each report covers one experiment or feature segment of the project. Multiple reports will later be synthesized into a cohesive portfolio writeup. Reports should be self-contained learning reflections — not experiment logs, not academic papers.

## Core Principle

**Show the reasoning journey, not just the destination.** The reader should understand what you expected, what you tried, what surprised you, and what you learned. A report that presents three prompt versions and picks the winner tells the reader *what*. A report that explains why each version existed, what hypothesis it tested, and what the results revealed about the underlying system tells the reader *how you think*.

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
    - *④ Limitations / future work* — ordered by criticality, dated for freshness.

  This is the journey genre's fullest form, the inverse of the reference doc, which distils the *same*
  workstream destination-first. **Menu, not mandate:** a short log might be just ①②④. Exemplar:
  `evidence/sequential_discussion/experiment_log.md` (its `report.md` is the paired reference doc).
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
- **Reference / how-it-works doc.** A reader needs to *use or audit* a finished mechanism, not learn
  how you got there. This is the one type that **inverts the Core Principle**: it leads with the
  synthesized destination and demotes the journey to an opt-in case study. Skeleton: *orientation line*
  (a one-line mental model — a pipeline or map — so every identifier introduced later has somewhere to
  hang) → *the guarantee / contract* (present-tense: what holds, where it's enforced, how it's
  verified — not a changelog) → *the model / mechanism* → *verification* → *evidence* (a case study,
  benchmark, or rationale, written **verdict-first then forensics**) → *known gaps* (criticality-ordered
  + freshness-dated). Use it when the artifact's value is the *current truth* of how something works,
  not the path to it; if the path *is* the point, use a journey type above. Exemplar:
  `evidence/agent_boundaries/report.md`.

### Discipline for reference docs (the part a fill-in template silently drops)

The shape is easy to copy; these habits are what made the exemplar trustworthy, and they erode first
under a fill-in-the-blanks template. They are *in addition to* the provenance-stamping and
direction-vs-magnitude rules below, which apply to every type.

- **Framework-behavior claims carry a version pin (+ a test where load-bearing).** "How LangGraph /
  LangChain / lib X behaves" is version-specific and the depth-reader's first thing to poke; assert it
  against the runtime fingerprint, and verify it empirically where the doc leans on it.
- **Gaps carry a freshness date AND an honestly-applied severity.** Severity = likelihood × impact ×
  detectability, *not* impact-if-violated alone (construction-enforced-but-unverified ≠ unenforced).
  Run a freshness pass against the repo before trusting any gap, and **mark minor gaps, don't delete
  them** — the list's value is the audit trail; criticality drives entry *length*, not inclusion.
- **Separate verdict from forensics.** Lead the case study with a 4-sentence outcome paragraph + a
  "skip by subhead" signpost, then the detail. One canonical doc — never fork a reader-friendly and a
  detailed version (they drift).
- **Pitch at the reader's altitude — drop nitty-gritty, don't reconcile it.** A reference doc serves a
  *busy auditor / interviewer*: current design + current gaps + future plan + the pivotal results that
  drove design shifts. It is **not** a forensic audit (commit-level provenance, which exact script ran,
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
  with provenance inline (SHA / config / file). *Verify:* every probe **names the one risk it isolates**
  ("*Catches:* …") → result → decision; a probe reported without the risk it tests is a fact-dump, and
  **falsification is first-class** — a killed approach is shown, diagnosed, and its recovery traced,
  never deleted. *Decide:* adopt / pivot / kill; a pivot re-enters ②.
- **④ Limitations — the reference doc's gap discipline, reused** (see *Discipline for reference docs*
  above for the full rule): criticality-ordered, freshness-dated, mark minor gaps rather than deleting
  them.

---

## Structure

### 1. Motivation (short)

What problem does this experiment address? Frame it as a gap: "we had X, but not Y, which meant we couldn't Z." No background tutorial — assume the reader understands the project. One paragraph.

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
  you are claiming. Mark confidence honestly (e.g. *high-direction / low-magnitude, N=4*) rather than
  implying a precision the sample can't support. Small-N over-claiming is this project's most likely
  failure mode; the headline metric stays the win rate, with proxies and N qualifying it.

Do not let tables speak for themselves. The reader should never have to infer what a table means.

### 6. Decision and Tradeoffs

State what you chose and why. Then explicitly address the strongest argument against your choice. Every decision has a tradeoff — name it and explain why it's acceptable.

Bad: "We chose v2 because it had the highest scores."
Good: "We chose v2 for its higher adoption accuracy and lower over-attribution rate. v2 does have the highest under-attribution (19%), which is the more dangerous failure mode since it makes useful strategies look unused. We accepted this because the schema reorder already substantially reduced both error types from v1, and 72% accuracy is sufficient for Phase 1's purpose of surfacing broad adoption patterns."

### 7. Lessons (the reflection)

What generalizable insights emerged? These are the most valuable part for the portfolio. Each lesson should be:

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

### 9. Artifacts

Table of files produced (eval sets, results, configs). Keep it factual.

**Stamp the provenance.** Record the lineage that produced the results — the git SHA /
`runtime_fingerprint`, the config, and the input datasets (by name, ideally by content hash). A
number a reader cannot trace back to the commit and config that made it is not reproducible, and the
report is where that pointer naturally lives. This is the same back-reference the eval-architecture
convention requires of every record — see `CLAUDE.md → Eval Architecture` and
`evidence/refactor/provenance_lineage_rationale.md`.

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

**Name tradeoffs, don't hide them.** Every design choice sacrifices something. Stating what you gave up and why it's acceptable is stronger than presenting the choice as obvious.

**Keep tables interpreted.** Never present a results table without stating the takeaway before it and addressing surprises after it.

**Avoid pure-fact dumps.** A "Challenges" section that lists five bullet points is an experiment log. A "Challenges" section that explains what each challenge taught you about the system is a reflection.

### Prose legibility (how a sentence reads)

Every rule above decides *what* to say and *in what order*. None of them decides how a sentence reads.
A report can pass all of them and still be hard work: ideas fused into one clause, hyphenated
modifiers stacked three deep, an em-dash breaking every line. Concision means cutting filler, not
compressing what remains — dense prose is a separate failure, and the checks above do not catch it.
The rules below are mechanical; apply them on a final read-through.

- **One main idea per sentence.** Keep the subject and verb close together. When a sentence welds three
  ideas into one clause, split it into three sentences.
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

---

## Anti-Patterns to Avoid

- **The fait accompli.** Presenting the final design as if it was obvious from the start. Show the path.
- **Orphaned tables.** Data without interpretation. Every table needs a "so what."
- **Buried corrections.** Hiding assumption changes in subsections. Pull them up as findings.
- **Impact theater.** Claiming vague impact without evidence. Either show numbers or honestly frame what was enabled.
- **Flat iteration lists.** "v1 did X. v2 did Y. v3 did Z." without causal links between them.
- **Lessons that don't generalize.** "We learned v2 is better" is not a lesson. "Schema field ordering affects reasoning direction in structured output" is.
- **Density mistaken for concision.** Fusing five ideas into one clause, stacking hyphenated modifiers, chaining em-dashes. The argument can be complete and the prose still unreadable — this is the failure the *Prose legibility* rules catch, and the one most common in practice. Cutting filler does not fix it.
- **Aphorism density.** Every sentence a crystallized maxim. One or two land; a page of them exhausts the reader. Say the thing plainly, then crystallize only what earns it.

---

## Checklist Before Finalizing

- [ ] Does every design decision name its tradeoff?
- [ ] Does every iteration link back to a specific finding from the prior version?
- [ ] Does every table have a stated takeaway?
- [ ] Are assumption corrections surfaced as findings, not buried?
- [ ] Are lessons stated as transferable principles with evidence?
- [ ] Is impact framed honestly (metrics if available, capability unlocked if not)?
- [ ] Would a reader who skips the tables still understand the narrative from the prose?
- [ ] Can an independent reader parse each *sentence* on the first pass — one main idea per sentence, roughly one em-dash per paragraph at most, internal shorthand defined before it's used? (This tests the sentences; the check above tests the argument — different failures.)
- [ ] Did you pick the right document type (experiment / build-journey log / decision record / negative finding / reference doc)?
- [ ] Is the provenance stamped (commit / fingerprint / config) so results are traceable?
- [ ] Are code pointers refactor-stable (console names / package paths), with deep anchors only where load-bearing?
- [ ] Is N stated, and direction separated from magnitude where the sample is small?
- [ ] *(Reference docs)* Does each framework-behavior claim carry a version pin (+ a test where load-bearing)?
- [ ] *(Reference docs)* Is each gap freshness-dated and severity-rated (likelihood × impact × detectability), with minor gaps marked, not deleted?
- [ ] *(Reference docs)* Is the verdict separated from the forensics (skim layer before depth layer)?
- [ ] *(Journey logs)* Does no earlier section depend on a later result — falsified designs shown in place, `(§N)` used as navigation only?
- [ ] *(Journey logs)* Does each refinement/fix lead with the problem, then the mechanism (not fix-first)?
- [ ] *(Journey logs)* Does each design state its mechanics before its benefits, and each experiment name the risk it isolates?
- [ ] *(Journey logs)* Is each argument made in one place and pointed back to elsewhere (no cross-section re-derivation)?
