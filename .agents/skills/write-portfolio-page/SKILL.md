---
name: write-portfolio-page
description: Write or substantially revise a portfolio write-up page in writeup/ (Level 1 chapter, Level 2 subject or Level 3 depth). Prototypes the explanation before drafting, then checks reader comprehension and claims with fresh-context reviewers. Use for new pages, page rewrites and section rewrites; small wording or scope fixes skip the workflow.
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

- **Rules, every level:** [`references/portfolio-writing-prompt.md`](references/portfolio-writing-prompt.md) (the copyable block is the rule set)
  and this skill's [`references/voice.md`](references/voice.md) (the owner's voice).
- **Rules for the level:** Level 2 → [`references/portfolio-level-2-writing-prompt.md`](references/portfolio-level-2-writing-prompt.md); Level 3 →
  [`references/portfolio-level-3-writing-rubric.md`](references/portfolio-level-3-writing-rubric.md) (it also says when a Level 3 page is justified).
- **Worked examples:** use [`references/examples.md`](references/examples.md) to select the example
  closest to this page's explanatory need. Read its page copy before outlining; use another only
  when it resolves a structural choice. Examples teach selection and reasoning, not fixed headings.
- **This page:** the chapter's `content_plan.md`; the brief at the top of the page file, if any; the
  chapter's `editorial_notes.md`; the chapter's outline in `writeup/_planning/map.md`, including its "Handle with
  care" list where one exists (it names what stays off the page); the existing draft.
- **What the reader has just read:** the parent page's introduction and the parent section that links
  here (Level 2 → the chapter subsection; Level 3 → the relevant subsection of its L1 or L2 parent).
  `python3 scripts/parent_context.py <page.md>` prints exactly that excerpt; the cold reviewer gets
  the same text.
- **Sources:** the evidence reports and records the brief cites. Lift numbers as they stand; never
  re-derive or invent one.

## 2. Prototype the explanation

Choose the page's primary purpose and depth using [page types](references/page_types.md), including
whether L1 is self-contained or delegates substantial subjects to L2. Direct L1 → L3 links are valid. These
help select material; they do not dictate headings. Keep one writer responsible for the explanation.

Create `<page dir>/_authoring/<page stem>.brief.md` from
[the brief template](references/brief_template.md). Keep the planning portion short: normally one
screen plus the sample passage, not a second content plan. Link existing source inventories rather
than copying them. Record:

- **Reader outcome:** what the reader should understand or be able to decide afterwards, in one
  concrete sentence. State what the parent already supplies.
- **Concept dependency:** the few concepts needed to reach that outcome, in the order a newcomer
  needs them. Organise the explanation, not the source report's chronology or inventory.
- **Likely confusion:** the consequential mistaken interpretation, if any. Do not list hypothetical
  caveats or turn these planning distinctions into an abstract opening paragraph.
- **Evidence:** the minimum sources and examples that establish the retained claims; material scope
  and unresolved facts. Keep the engineering question bounded to an entry-to-mid-level role.

Then **write one difficult passage as actual page copy**, including its example or proposed visual
if useful. This is the explanation prototype, not a promise to explain later. Distinguish an
illustration that teaches a concept from empirical evidence that supports a claim; label invented
or simplified examples accordingly. See [examples](references/examples.md#choosing-how-to-explain-a-concept).

Choose a representation by what the reader must understand: input/output for a transformation;
criteria and alternatives for a choice; steps for a sequence; separate responsibilities for interacting
components; successive questions for an investigation; comparison before numbers for a finding.
These are options, not routing rules. Plain prose may suffice. Use a diagram when relationships,
branches or handoffs become clearer in it, not merely because the topic contains a workflow.

## 3. Agree the explanatory order

Give each proposed section one line: **what the reader learns, and how it is explained**. Include
only evidence that serves that point. Link secondary questions to depth; do not compress them into
qualifications. Do not force a causal transition between independent responsibilities.

Read the order and the prototype together. Does the sample make the difficult relationship concrete?
Does the reader need an explanation supplied only later? An approved topic list does not itself show
that its prose will work.

**Checkpoint (default on).** Show the owner the central point, the short section order and the sample
passage together, before expanding to the full page. This replaces a long outline approval packet.
If the conversation already approves an equivalent explanation or authorises drafting without another
stop, record that and proceed; do not request permission again. Otherwise, existing content-plan
approval supplies the agreed topics, while this checkpoint reviews their presentation. A waiver such
as "no checkpoint" applies to this checkpoint too. Small fixes need no prototype or approval.

## 4. Expand the explanation

- Expand the approved prototype into the page; preserve its clarity, not necessarily its exact wording.
  Write the page copy under the guides. Keep the page file's existing layout: title, the italic
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

Before review, read the page as a newcomer, including the difficult passage in context. Can the
reader explain what happens, why the choice follows, or what the comparison establishes without
supplying a missing connection? Headings alone and a correct summary are insufficient. Save the
first full draft as `_authoring/<stem>.first-draft.md` before reviewer edits; do not overwrite a
previous trial's snapshot (use a dated suffix).

## 5. Review in fresh contexts

Two reviewers, run in parallel, each in a fresh context so they cannot see what the writer meant.
They return findings; they do not edit the page.

```bash
.agents/skills/write-portfolio-page/scripts/review.sh editorial <page.md> [claude|codex]
.agents/skills/write-portfolio-page/scripts/review.sh claims    <page.md> [claude|codex]
```

- **editorial**: a cold read of the supplied page copy (no brief or source documents supplied), given
  the parent excerpt as context; it flags lengthy reintroduction while allowing concise useful
  definitions. It checks selection as well as missing explanation. It states the argument, attempts
  a concrete application question using only the page, then marks
  where understanding required inference or unnecessary rereading. If it needs the brief to
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

- Treat a reviewer's misunderstanding as evidence of a presentation problem, not proof that its
  proposed repair is technically correct. Check repairs against the sources. A request to clarify
  may need a concrete example or reorganisation rather than an additional sentence.
- Fix reasoning and selection before wording. For each request for more context, choose **explain,
  relocate or remove**; adding prose is not the default. Check whether a supporting example has
  displaced the page's main question. Do not remove a material caveat while retaining its claim.
- If a correction changes a claim, recheck the passages around it, not just the sentence.
- When a finding says a term or some context is missing, first ask whether the passage that needs it
  belongs on this page (topic selection over compression, `voice.md`). Add the explanation only if it
  does; otherwise move the passage to a deeper page or a supporting note.
- After resolving, report the page-copy word count against the level's guide. Growth past the guide
  needs a reason for each addition; without one, trim.
- Reread each revised section as a whole. Remove redundant explanations introduced by local fixes;
  check that definitions, qualifications and transitions have not accumulated around a buried point.
- Re-run a reviewer when the structure or a central explanation changed. Do not loop on taste.

## 7. Finish

**Ready for owner review** means: claims fit their evidence, the essential explanation is present,
and the reader can follow or apply it without reconstructing missing relationships. A reviewer
passing the page or the writer completing the steps does not establish this. Difficulty distinguishing
components, following a mechanism or interpreting a comparison is substantive, not cosmetic taste.
Record unresolved factual questions and qualify affected claims. Pure wording preferences need not
block delivery.

Then:

- Add a dated entry to the chapter's `editorial_notes.md` in its existing style: the explanatory path,
  what moved out, claim changes, what was checked, and that "editorially revised" is not "factually
  verified".
- Update the page's italic header line (status and date). Keep a parent subsection in sync when a
  Level 3 page is added, renamed or dropped.
- Save the reviewed page copy as `_authoring/<stem>.reviewed-draft.md` (dated suffix for a new trial).
- Report the change, unresolved issues and the brief's path concisely. Do not mark anything approved
  or published. After owner feedback, record which changes required conceptual reconstruction versus
  local edits; workflow completion is not evidence of writing quality.

## Maintaining and testing the workflow

After changing the runner, run `bash -n scripts/review.sh` and `python3 scripts/test_review.py`
from this skill directory. These check extraction, unique review outputs, CLI fallback and failure
handling with simulated responses, not writing quality. Use `DRY_RUN=1` on a real page to inspect
what each reviewer receives. A text-only review cannot validate a diagram's rendering.

For the next quality pilot, use three untouched topics with different explanatory needs. Keep the
source packet fixed for any paired comparison and record model, prototype approval or waiver, and
owner interventions. Preserve first and reviewed drafts separately; capture the owner-revised
version when available. Do not tune only against a page whose explanation the owner already repaired.

Classify required owner changes in the brief: concept selection, order, missing connection,
example/representation, prose, or claim support. Record whether the owner had to redesign the
explanation or mostly make local edits. A shorter page, more reviewer findings, completed steps or
reviewer approval is not a quality score. The target is less owner reconstruction while preserving
correctness and sufficient explanation; no numeric usability threshold is claimed without owner
assessment. If failures persist, change the relevant decision step instead of appending another
universal rule. Automated checks validate the runner, not writing quality.
