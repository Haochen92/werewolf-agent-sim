---
name: write-portfolio-page
description: Write or substantially revise a portfolio write-up page in writeup/ (Level 1 chapter, Level 2 subject or Level 3 depth). Frames the argument and outlines it before drafting, then gets a cold editorial read and a claims check from fresh-context reviewers. Use for new pages, page rewrites and section rewrites; small wording or scope fixes skip the workflow.
---

# Write a portfolio page

The page is public copy for a hiring reader assessing an **entry-to-mid-level AI engineer**. Show
practical judgement: appropriate methods, implementation choices, useful checks, diagnosed failures
and understood limits. Research-level experimental completeness is not the default standard; claims
must still fit their evidence. The owner must be able to read, own and defend every sentence.

The writing rules already exist; this skill does not repeat them. It adds a **process** that makes
the writer show it has understood the argument before it writes polished prose, and that gets the
draft read by someone who does not already know what it meant to say.

The **approach is constant** and the **structure adapts to the subject**. An architecture page may
follow execution order; an investigation follows successive questions. There is no fixed
"problem → solution → results" template.

## 0. Size the job

| Job | What to run |
|---|---|
| Small fix: a word, a claim's scope, a number, a link | Edit directly under the guides. If a claim changed, add one line to the chapter's `editorial_notes.md`. No brief, no reviewers. |
| One section rewritten | Steps 1–3 for that section only (short), draft, then the **editorial** review of the whole page (a section changes the page's flow). Claims review only if claims changed. |
| New page, or a rewrite of most of one | The full workflow below. |

## 1. Read the inputs

Read these yourself; do not summarise them from memory.

- **Rules, every level:** `writeup/portfolio-writing-prompt.md` (the copyable block is the rule set)
  and this skill's [`references/voice.md`](references/voice.md) (the owner's voice).
- **Rules for the level:** Level 2 → `writeup/portfolio-level-2-writing-prompt.md`; Level 3 →
  `writeup/portfolio-level-3-writing-rubric.md` (it also says when a Level 3 page is justified).
- **Worked examples:** use [`references/examples.md`](references/examples.md) to select the example
  closest to this page's explanatory need. Read its page copy before outlining; use another only
  when it resolves a structural choice. Examples teach selection and reasoning, not fixed headings.
- **This page:** the chapter's `content_plan.md`; the brief at the top of the page file, if any; the
  chapter's `editorial_notes.md`; the chapter's outline in `writeup/map.md`, including its "Handle with
  care" list where one exists (it names what stays off the page); the existing draft.
- **What the reader has just read:** the parent page's introduction and the parent section that links
  here (Level 2 → the chapter page's summary of this subject; Level 3 → the Level 2 subsection).
  `python3 scripts/parent_context.py <page.md>` prints exactly that excerpt; the cold reviewer gets
  the same text.
- **Sources:** the evidence reports and records the brief cites. Lift numbers as they stand; never
  re-derive or invent one.

## 2. Frame the page

Choose a primary explanatory purpose and reader-dependent opening using [page types](references/page_types.md). Page level is
reading depth, not report type: an investigation can be L2, and L3 can explain a mechanism. Hybrid
pages may borrow another mode for a section; do not force every section through one template.


Create `<page dir>/_authoring/<page stem>.brief.md` from
[`references/brief_template.md`](references/brief_template.md) and fill in **Frame** and **Evidence
selection**. Keep both short enough to expose uncertainty rather than hide it.

- **Frame:** the reader's question and central answer; what the parent establishes and what this
  page must still define; the opening needed before the first decision; and the claim being made
  (mechanism, diagnosed failure, practical choice or measured improvement). Scope evidence to that
  claim rather than demanding a general performance study for a targeted fix.
- **Core argument:** write the essential concepts and their connections before listing experiments
  or numbers. These are what must survive a length cut.
- **Evidence selection:** choose examples to support those concepts. Relevant does not mean essential:
  use the smallest set that makes the argument understandable and assessable, while retaining enough
  explanation for each. An additional example should establish a different point or materially
  change the interpretation. Record alternatives omitted and their destinations.
- **Depth:** L2 keeps the complete central explanation and material caveats. An L3 proposal must
  name a focused follow-up question and how it answers it; full logs and reproduction stay in
  evidence. Do not create L3 merely to store overflow.

## 3. Outline the argument

Fill in **Argument outline** in the brief. For each section: the question it answers, its main point,
the selected example or finding (if needed), material omitted or linked, and why the next section
follows from it. Name the structure you chose and why it fits *this* subject (see the examples).

Check the outline before drafting: read only the main points in order. Do they answer the frame's
question? Does any section need a term or result that a later section introduces?

**Checkpoint (default on).** Stop and show the owner the Frame and the Argument outline. Draft only
after they reply, unless the conversation already contains their approval of the proposed frame
and outline. Record existing approval and proceed without asking again. The owner may also waive
this checkpoint for a task ("no checkpoint"); record that in the brief. Routine wording changes do
not require renewed approval; seek clarification only for a material change outside agreed scope.

## 4. Draft from the outline

- Write the page copy under the guides. Keep the page file's existing layout: title, the italic
  header line, any historical brief, `## Page copy (draft)`, then the sources comment.
- Build on the parent without repeating its introduction at length. A concise definition or
  orientation may still be needed to make this subject understandable independently. Explain an
  approach's purpose and selection criteria before asking readers to assess its results; other
  subjects need different openings (see page types). Do not open with conclusions that require
  concepts introduced later.
- Keep source mappings in the HTML sources comment at the end, as the existing pages do. Moved-out
  detail goes into supporting notes in a comment; never delete it, and never let it rescue misleading
  page copy.
- Questions you could not settle from the sources go in the brief's **Open questions**, not into
  smooth prose.
- If drafting shows the outline was wrong, fix the outline first, then the draft.

If the draft is long, remove secondary branches before compressing the core explanation. Preserve
context, transitions, comparisons and material limitations; do not retain every experiment as a
dense sentence of numbers. Read the resulting prose for gaps after removing material.

Before review, read only the headings, opening sentences and exhibit captions. Can a reader follow
the argument from those alone?

## 5. Review in fresh contexts

Two reviewers, run in parallel, each in a fresh context so they cannot see what the writer meant.
They return findings; they do not edit the page.

```bash
.agents/skills/write-portfolio-page/scripts/review.sh editorial <page.md> [claude|codex]
.agents/skills/write-portfolio-page/scripts/review.sh claims    <page.md> [claude|codex]
```

- **editorial**: a cold read of the supplied page copy (no brief or source documents supplied), given
  the parent excerpt as context; it flags lengthy reintroduction while allowing concise useful
  definitions. It checks selection as well as missing explanation. It first
  states the argument it understood, then marks where comprehension breaks. If it needs the brief to
  follow the page, the page is missing something.
- **claims**: reads the page, the brief and the sources, and checks the consequential claims:
  mechanisms, comparisons, scope, built/run/deployed status, first-person ownership and the
  Handle-with-care list. It checks a number only where a claim depends on what it counts. It is not a
  number-by-number audit.

Use your own CLI by default (Claude Code → `claude`, Codex → `codex`); the owner may ask for the other
one as a cross-check. Run both in the background where your harness allows it (a review takes a few
minutes). Each run saves a uniquely named `<stem>.review-<kind>.<cli>.<run-id>.md` beside the brief,
so earlier findings remain available. Set `DRY_RUN=1` to print
the prompt without calling a model. The reviewer instructions are in [`reviewers/`](reviewers/).

The editorial review is text-only: it receives the title, subtitle, page prose, captions and
inline diagram source, but does not inspect linked image pixels. Record visual understanding as
unchecked when it depends on those images. Claude runs with tools disabled; Codex runs read-only in
an empty directory with instructions not to use tools. The latter is procedural isolation, not a
filesystem access boundary. Do not describe it as a technically enforced no-tools review.

## 6. Resolve and revise

Fill in **Review resolution** in the brief: one row per material finding, with the action taken
(fixed / declined, with the reason / flagged for the owner). The writer keeps one voice: apply
findings yourself rather than pasting reviewer wording.

- Fix reasoning and selection before wording. For each request for more context, choose **explain,
  relocate or remove**; adding prose is not the default. Check whether a supporting example has
  displaced the page's main question. Do not remove a material caveat while retaining its claim.
- If a correction changes a claim, recheck the passages around it, not just the sentence.
- When a finding says a term or some context is missing, first ask whether the passage that needs it
  belongs on this page (topic selection over compression, `voice.md`). Add the explanation only if it
  does; otherwise move the passage to a deeper page or a supporting note.
- After resolving, report the page-copy word count against the level's guide. Growth past the guide
  needs a reason for each addition; without one, trim.
- Re-run a reviewer only when the structure or a central claim changed. Do not loop on taste.

## 7. Finish

**Done** means: no unresolved misleading claim; no missing explanation the argument needs; open
factual questions listed in the brief, and the affected claims qualified or flagged rather than
smoothed over. Style preferences alone never block completion.

Then:

- Add a dated entry to the chapter's `editorial_notes.md` in its existing style: the explanatory path,
  what moved out, claim changes, what was checked, and that "editorially revised" is not "factually
  verified".
- Update the page's italic header line (status and date). Keep a parent subsection in sync when a
  Level 3 page is added, renamed or dropped.
- Report to the owner: the brief's path, the outline in one line per section, the unresolved findings
  and open questions. Do not mark anything approved or published.

## Maintaining and testing the workflow

After changing the runner, run `bash -n scripts/review.sh` and `python3 scripts/test_review.py`
from this skill directory. These check extraction, unique review outputs, CLI fallback and failure
handling with simulated responses, not writing quality. Use `DRY_RUN=1` on a real page to inspect
what each reviewer receives. A text-only review cannot validate a diagram's rendering.

For a quality pilot, use an untouched topic with the same source packet and writer model for two
runs: existing guides alone, and guides plus this workflow. Save the first draft and the reviewed
revision separately in an isolated output directory. For an unattended comparison, obtain an
explicit checkpoint waiver; otherwise use the normal owner checkpoint and record any owner guidance
as an intervention. Compare anonymized drafts for understandable argument, section connections,
evidence scope and amount of owner revision needed. Include a clear passage and deliberately flawed
variants when testing reviewers, so both missed defects and unnecessary criticism are visible.
Try different primary page types before claiming that the workflow transfers reliably. Model admission
is a useful next pilot: can readers explain which question each test answers, why the checks are
combined, and what remains unchecked? Evaluate the first draft separately from review revisions and
record owner interventions. Script checks do not establish writing quality.
