# Experiment Report Style Guide

## Purpose

Each report covers one experiment or feature segment of the project. Multiple reports will later be synthesized into a cohesive portfolio writeup. Reports should be self-contained learning reflections — not experiment logs, not academic papers.

## Core Principle

**Show the reasoning journey, not just the destination.** The reader should understand what you expected, what you tried, what surprised you, and what you learned. A report that presents three prompt versions and picks the winner tells the reader *what*. A report that explains why each version existed, what hypothesis it tested, and what the results revealed about the underlying system tells the reader *how you think*.

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

### 4. Evaluation Setup

How you measured. Keep this factual and concise — dataset size, judge model, metrics, any diagnostics added mid-experiment. If you added a metric partway through (e.g., attribution direction), explain what prompted the addition.

### 5. Results

Present data, then interpret it. For every table or comparison:

- State the headline finding in one sentence before the table
- After the table, address anything surprising or counterintuitive
- If an outlier or confound affected results, identify it and show results both ways

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

**Co-locate artifacts with the report.** All files that support the report — eval sets, eval results, eval configs — should live in the same `evidence/<experiment>/` folder alongside the report. This keeps the experiment self-contained and reviewable without hunting across directories. When artifacts are generated elsewhere (e.g., `eval_results/`), move them into the evidence folder and clean up the originals.

---

## Tone and Style

**Reflect, don't narrate.** After each major finding, add one sentence on what it means or what you'd do differently. Don't add filler — reflection is concise.

**Address assumption corrections explicitly.** If you started with assumption X and the data showed Y, that's a finding worth highlighting, not an embarrassment to bury. "We initially assumed over-attribution was the primary risk. At n=120, both directions appeared in roughly equal measure, which reframed our optimization target." The narrative of "assumed X, tested, found Y, adjusted" demonstrates learning.

**Frame impact as capability unlocked when no downstream metrics exist yet.** If you haven't measured end-to-end impact, don't fake it. Instead, describe what was unobservable before and is now observable. "Before this work, we had no way to distinguish strategies agents rely on from ones they ignore. This makes strategy quality measurable for the first time."

**Name tradeoffs, don't hide them.** Every design choice sacrifices something. Stating what you gave up and why it's acceptable is stronger than presenting the choice as obvious.

**Keep tables interpreted.** Never present a results table without stating the takeaway before it and addressing surprises after it.

**Avoid pure-fact dumps.** A "Challenges" section that lists five bullet points is an experiment log. A "Challenges" section that explains what each challenge taught you about the system is a reflection.

---

## Anti-Patterns to Avoid

- **The fait accompli.** Presenting the final design as if it was obvious from the start. Show the path.
- **Orphaned tables.** Data without interpretation. Every table needs a "so what."
- **Buried corrections.** Hiding assumption changes in subsections. Pull them up as findings.
- **Impact theater.** Claiming vague impact without evidence. Either show numbers or honestly frame what was enabled.
- **Flat iteration lists.** "v1 did X. v2 did Y. v3 did Z." without causal links between them.
- **Lessons that don't generalize.** "We learned v2 is better" is not a lesson. "Schema field ordering affects reasoning direction in structured output" is.

---

## Checklist Before Finalizing

- [ ] Does every design decision name its tradeoff?
- [ ] Does every iteration link back to a specific finding from the prior version?
- [ ] Does every table have a stated takeaway?
- [ ] Are assumption corrections surfaced as findings, not buried?
- [ ] Are lessons stated as transferable principles with evidence?
- [ ] Is impact framed honestly (metrics if available, capability unlocked if not)?
- [ ] Would a reader who skips the tables still understand the narrative from the prose?
