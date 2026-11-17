# Portfolio voice guide

*In use from 2026-11-17. It replaces the earlier `voice.md`, which is in git history.*

This guide answers one question: what should a portfolio page written in my voice sound like, and
what should it emphasise? It applies to pages under `writeup/`. General writing quality (clear
sentences, order of explanation, terms, evidence, length) is covered by `docs/writing/core_rules.md`, which
is always read first.

**Which document wins when two disagree:** the core rules, then this guide, then approved example
pages. An example shows the intended result; it does not override a written rule.

Two terms: a Level 2 page covers one subject of a chapter in depth, and a Level 3 page goes
further into one part of that subject. The source notes are the comment at the end of each page
file that maps claims to evidence.

## A. Voice and explanation

**1. Open by establishing what the page is about and why it matters.** Give the reader enough
context to understand the first explanation. Define the subject directly when that is the clearest
opening, as in "The Ninth Express is a variant of the Mafia-style game played with AI agents."
Otherwise begin with the problem or requirement that motivates it.

**2. Introduce a technical term as the answer to a problem the reader already understands.**
Start from what the reader knows and add one new idea at a time. Describe what the game needs
before giving the framework's name for the technique that meets the need. Example: votes must be
collected independently, and the technique for that is called fan-out.

**3. Write in a natural, conversational technical voice.** Use "I" when describing decisions,
experiments or implementation work that I did. Never use "we": the project has one developer.
An explanation of a general mechanism usually needs no pronoun.

**4. Make only claims I can explain and defend.** Do not imply that code written by an AI was
written by hand.

**5. Avoid these habits, which I removed when rewriting earlier drafts:**

- A noun made from a verb standing in for whoever acts: "that distinction creates the central
  design problem".
- Denying something the reader had no reason to assume: "it was not a comparison of …".
- Describing a decision as an abstract exchange instead of saying what the code does: "taking
  responsibility for validation in exchange for …".
- Promotional adjectives.
- A question in the prose asked only so that the next sentence can answer it. A heading phrased
  as a real question is fine.
- The labels "Problem / Decision / Result" repeated in section after section.

## B. Telling the engineering story

**6. Explain a design decision through the requirements that conflicted.** Name the competing
requirements or constraints that made a decision necessary. Then explain how the chosen design
meets them and what limitation remains. Example: a waiting game must survive a server restart,
and a person's answer should be handled without a separate worker service. The design saves a
checkpoint and also keeps the waiting task in memory.

**7. Describe participants and components by what they have and do.** For a game participant:
what it knows, what it is trying to achieve, and what it can do. For a software component: what
it is responsible for, what information it receives, and what operations it performs.

**8. Introduce the overall structure before its parts, when that helps.** Say how many parts
there are and of what kind, then describe each. Example: the page says the game works "usually
through two basic mechanisms", then describes the day and the night. A short explanation does not
need an outline first.

**9. Organise the page around what was found.** State the finding, give the evidence that
supports it, and describe the decision or change that followed. Discuss another possible
explanation when it matters to the conclusion. The order in which the investigation happened
stays in the experiment log.

**10. Choose each piece of evidence for its purpose.** Keep a finding if it explains a decision,
supports the account of a mechanism, tests whether a result holds, or shows a limitation. The
full history of runs belongs in the evidence reports.

**11. Use a diagram for what the parts are and how they connect, and prose for why they are
arranged that way.** A figure can replace a passage only when it shows the same facts. A link to
a deeper page comes after a sentence that states the problem the deeper page addresses.

## C. Publication standards

**12. Put on the page what the reader needs to judge a claim without opening a link.** That is
the conditions of the comparison, what each count is out of, and the limitations. Full lists of
variants and the details needed to reproduce the work go to the evidence reports or to a Level 3
page. Dates, versions and the full configuration go in the source notes, unless one changes how a
claim should be read.

**13. Name a model only where the result depends on it.** In a passage that explains how
something works, do not list model names. Do not replace a name with "stronger" or "cheaper"
unless the evidence supports that description.

**14. Leave out internal housekeeping that does not affect a claim.** Each chapter has a "Handle
with care" list, and it is followed exactly. Examples of what stays off a public page: tests
written by an AI and not yet reviewed, the absence of automated testing on each change, scheduled
jobs that were never installed, records not under version control, runs made from uncommitted
code, paid runs that were planned and never run, and retracted numbers.

**15. Never leave out a limitation that changes whether a claim is accurate, or how much
confidence the reader should place in it.** Do not imply that a test, a monitoring process or an
operational safeguard exists when it has not been built. If the page says a behaviour is checked
automatically, that check must exist and run. Rule 15 takes precedence over rule 14.

**16. Tell a fault the project caught as caught.** Say that it was found, what changed, and which
results it affected. Do not hide it and do not make it sound dramatic.

**17. When checking a page, assume the reader will not open the evidence.** Spend the checking
time on whether the reasoning holds: separate experiments are kept apart, a cause is not
overstated, and each limitation sits next to its claim. Never invent a number, and never change
one without saying so.
