# Authoring brief: Information boundaries: what each agent may know

Page: `writeup/information_boundaries/information_boundaries.md` · Level 1 · started 2026-10-30 · checkpoint: approved in conversation (owner reviewed the content plan 2026-10-30)

Authoring material, not page copy. The cold editorial reviewer never sees this file.

## Frame

- **Primary page type and level:** architecture or mechanism explanation, at Level 1. The chapter has no
  Level 2 pages, so the overview pattern would only produce one-line summaries.
- **Secondary mode, if needed:** a short incident account inside section 3 (detected, cause, fix), kept to
  the finding; the investigation is the Level 3.
- **Existing outline approval:** the content plan, revised after the outside review and reviewed by the
  owner 2026-10-30, with two owner changes: the intro example is a non-wolf receiving the wolves' chat;
  section 1 is the tiered information classification.
- **Reader's question:** chapter 1 said each agent's input is built from what its seat may know. Where is
  that boundary enforced, and how is it checked?
- **Central answer:** information is classified by who may receive it; the permitted fields are selected
  when each seat's input is built, and nothing later is trusted to discard the rest; a post-game audit of
  the recorded inputs detects violations but does not prevent them; a helper that computes advice is held
  to the same boundary; the audit's scope and blind spots are stated.
- **Reader starting point:** chapter 1's "Keeping each player's information separate" (context isolation,
  input built per turn, a model cannot unsee its input, inputs checked after test games, the
  `context_isolation.svg` figure). This page must still define: the classification, the steps the input
  passes through, the audit, the metamorphic test.
- **Opening choice:** the requirement first, with a concrete consequence (the Healer reading the wolves'
  night chat), then the three things the page keeps apart.
- **Claim level:** mechanism, plus one diagnosed failure told as detected and fixed.
- **Distinctions the reader needs:** the boundary (who may know what) vs the enforcing code (selection at
  construction) vs the detecting checks (after the game); a check's coverage (what it inspects) vs its
  recognition (what it can match); independence of hidden information vs correctness of a deduction.
- **What the evidence establishes:** the classification and its enforcement points (report §1–2); the
  checks run after every batch-runner game and fail the batch (§3); unit tests plant leaks
  (deterministic_audits report row 2); the 109-flag incident, none rendered, fixed, next run clean (§4,
  experiment_log §2); the deduction engine reads only a view from the seat's payload, with metamorphic
  tests (deduction report §3–4; tests).
- **What stays uncertain:** whether a reworded secret has ever leaked (the checks cannot tell); memory
  isolation is by construction only; two call sites unrecorded; rendered prompts not checked per game.
- **Stays off the page:** whether the nightly job for site games is installed or has run (owner
  2026-10-30: mention the job without its status; wording "is built to run"); test authorship and counts;
  missing CI; the notebook-only period of the checks (Level 3 may tell it as the cause of the delay); dates
  inside the explanation.

## Evidence selection

**Core argument, before examples or numbers:** hidden information is part of the rules → classify it by
audience → enforce the classification where the input is built, because every later step forwards or
filters by accident → detect violations by checking what was sent, after the game → apply the same rule to
any helper that writes into the prompt, and test it by varying what the seat cannot see → say what the
checks inspect and recognise.

| Essential concept | Selected evidence (source), if needed | Why this example earns space | Alternatives omitted / destination |
|---|---|---|---|
| Why the boundary matters | The Healer given the wolves' night chat (hypothetical; `check_wolf_channel_isolation`, report §3) | Owner's choice: explicit about what the leak gives (who the wolves are, whom they will kill) | The healer-receives-the-roster flag line → Level 3 |
| Tiered classification | A wolf's reads name its packmate, so reads never enter shared state (experiment_log §4) | Shows classification shaping storage, before any filtering | Full private-field table (report §1) → evidence |
| Enforce at construction | The three steps and how each treats extra fields (report §2) | The reason the rule sits at the first step | Framework internals (`Send`, state types) → Level 3 |
| Detect after the game | The rewrite that sent every speaker the full payload (report §4, experiment_log §2) | The one real break on record; shows detection, not prevention | Flag arithmetic, the uncovered third field, the notebook-only period, the October checks fed no input → Level 3 |
| Same rule for computed advice | Swap two roles the Investigator cannot see, require identical lines (deduction report §4; `test_candidates.py`) | Defines the metamorphic test by a concrete case | Correctness tests → Evaluation's code-checks page |
| Coverage | Report §5 | Limits that change how to read "checked" | Resumed site games partly captured → dropped (site audit status stays off) |

Level 3: "Private fields in the wrong agent inputs". After this page, the interested reader may ask how a
documented design decision put private fields into every input, why no model saw them, and why it went
unnoticed until the checks were wired in; the Level 3 answers with the cause (a framework behaviour true
on one path and false on this one), the flag analysis, the template search and the recurrence. Not yet
drafted; the page carries a link specification.

## Argument outline

Structure: mechanism, in the order the information travels (classification → construction → detection →
a second consumer → coverage). Each section answers what the previous one leaves open.

| # | Section | Reader understands afterwards | Selected example, if needed | Omitted / linked | Why the next follows |
|---|---|---|---|---|---|
| 0 | Intro | Hidden information is part of the rules; the three things kept apart | Healer reads the wolves' chat | Ch1's human-table contrast (not repeated) | "Who may know what" must be defined first |
| 1 | Classifying information by who may receive it | Four tiers, from everyone to no prompt at all | A wolf's reads name its packmate | Private-field table | Knowing the tier does not say where it is enforced |
| 2 | Building the boundary into the input | Why enforcement sits where the input is built | The figure (audit as a branch) | Framework detail | A mistake there raises no error, so what was sent must be checked |
| 3 | Checking what was actually sent | The audit detects after the game; the incident, detected and fixed | The full-payload rewrite | Level 3 link | Field checks cannot read new text, and the deduction engine writes new text |
| 4 | Holding computed advice to the same boundary | The engine's view and the metamorphic test, and what it does not show | Swap two hidden roles | Correctness → Evaluation | With all checks named, what remains outside them |
| 5 | What the checks cover | What the audit inspects; what it can recognise; memory explained | — | — | Closing line to chapter 8 |

## Open questions

- The figure's audit branch: the review placed it on the payload; the record says the audit reads the
  recorded prompt variables (report §3, "Audit the data layer"), which carry exactly what the payload
  carried. Drawn from the prompt variables. Owner to confirm.
- The Level 3 is not drafted; the link is a specification only.
- Chapter 1's "Explore: Agent information boundaries" link should be repointed to this page (chapter 1
  edit, not done here).

## Review resolution

| Reviewer | Finding (passage) | Action | Recheck needed? |
|---|---|---|---|
| Editorial #1 (blocking), claims #1 | "Every model call's prompt variables are recorded" contradicts the unrecorded inputs | Corrected: "every player turn's"; figure label matched; the two unrecorded inputs named (memory-lookup query, a human player's board) | No |
| Editorial #2 | Page opened directly never says what a seat is or what the named roles do | Explained: one sentence defining a seat; the Healer and the Investigator glossed where used. Full game intro declined: chapter 1 carries it | No |
| Editorial #3 | Why a held-back line is secret | Explained in one clause (never said, so no player may see it) | No |
| Editorial #4 | "Is built to run" ambiguous about the nightly job's status | Declined: owner ruling 2026-10-30, mention the job without its status | Owner aware |
| Editorial #5, claims #4 | One swap test presented as general independence | Corrected: the test family's range stated; "on the cases tested"; the general guarantee attributed to the construction | No |
| Editorial #6 | Why the three things must stay distinct | Explained: mixing them is how a boundary fails quietly; sections take them in order | No |
| Editorial #7 | "Framework drops fields a step does not declare" uses new vocabulary | Explained: LangGraph named, "for this kind of step it does not" | No |
| Editorial #8 | "Helper" ambiguous | Corrected: "component" | No |
| Editorial #9, claims #3 | "Memory sits outside both"; the retrieval rule unstated; reassurance the record does not make | Explained: rule stated; "outside the audit altogether"; kept the past-games reasoning (owner agreed it in the plan review), framed as reasoning; "silently" kept from the report | Owner may confirm |
| Claims #2 | Planted leaks do not show the runner feeds the checks | Corrected: "so each check is shown to fire on a known violation" | No |
| Claims #5 | "Searched by hand" was a template grep | Corrected: the templates were searched for the leaked fields | No |
| Claims #6 | The formatter emits a fixed variable set, not every field | Corrected: fills the same full set for every role, never narrowing | No |
| Claims #7 | "Designed, not built" | Corrected: "proposed, not built" | No |

Word count after resolution: 929 (guide 750–900). The additions over the guide each answer a finding: the
seat definition and role glosses, why the three things stay distinct, the metamorphic test's range, and
the named unrecorded inputs. If trimming is wanted, the metamorphic paragraph is the first candidate.
