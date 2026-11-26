# Outline: Private fields in the wrong agent inputs (Level 3)

Page: `writeup/information_boundaries/wrong_agent_inputs.md` (superseded 2026-10-31 by the owner's short version, `private_information_leaks.md`) · Level 3, directly under the Level 1's
"Tests and audits: check that the rule holds" (the chapter has no Level 2; the link already sits there) ·
Proposed 2026-10-31; revised the same day after a cold review (the 109 explained where it first appears;
the framework contrast in plain words; the lesson stated at the end of the timeline so the October case
reads as its second instance; seven sections, not nine) · Length guide 800–1,100 words.

**Reader's question.** A change put private data into every role's input. How did it get past every
step, why did no model see it, and why did it go unnoticed until the checks were wired in?

**Central answer.** A refactor built one bundle of inputs for every speaker and justified it with a
comment that the framework would drop undeclared fields. The way of connecting steps that strips unknown
fields was not the way this path used, so the bundle arrived whole. The templates fill in only their own
placeholders, so nothing reached a model. The checks that would have caught it existed and were correct,
but ran only by hand, so three days passed before the first run with them wired in flagged 109
violations. Building the bundle by role fixed it; the next run flagged none. Four months later the same
gap returned in another form: three checks were running but receiving no input.

**What the parent already tells.** The healer example as a real failure; that a refactor gave every
speaker all roles' private fields on a wrong assumption about the framework; that the first batch run
with the audit found wolf identities and Investigator results in other inputs; that a template review
showed nothing rendered; the fix and the clean next run; that the audit reads recorded inputs, not
rendered prompts. This page adds the cause, what the 109 were, the severity method, the timeline and the
recurrence. It restates the finding in two sentences at the top for direct arrival and no more.

**Shape.** One investigation: what the checks found → where the bundle came from → did any model see it
→ why it went unnoticed, and the fix → the same shape later → what this establishes. Dates are allowed
on this page because the timeline is causal.

| § | Section (working heading) | What the reader learns, and how | Carried by | Stays off |
|---|---|---|---|---|
| 0 | Opening | The finding in two sentences and what this page adds | — | Check counts, test counts |
| 1 | What the checks found | The first batch game after the checks were wired into the runner reported 109 flags. Explain the number at once: flag events, not inputs; the wolf-identity check writes two lines per contaminated input (38 inputs × 2 = 76) and the investigator-result check one (33). What a flag means: the checks read the bundle of inputs recorded just before each model call, one layer before the prompt is rendered, so a flag says private data crossed the boundary where access is enforced, whether or not it would have been shown. Then one sentence of its own: a third field, the Vigilante's shot feedback, leaked with no check covering it, found by inspection, and through the vote step as well as discussion turns | **Exhibit:** the three-row arithmetic table, and a before/after pair lifted from the two smoke logs (a non-wolf's recorded input carrying the wolf roster; the same input after the fix). Lift real lines; if the logs hold only flag lines, show the flag line and the clean verdict and say so | "Leaks" for the 109: they are flags |
| 2 | Where the bundle came from | The discussion rewrite that made speakers take turns built one bundle and handed it to every speaker. Its comment said the framework ignores extra keys. The plain contrast: one way of connecting steps strips fields a step did not declare; the way used here passes everything through, and the builder that fills the prompt read straight from what arrived. "The documented justification was the bug" | Two short paragraphs; the comment quoted | Framework terms ("compiled subgraph", "node", "type annotation") and function names: source note, with the pinned versions |
| 3 | Did any model see it? | The severity method: an exhaustive search of every template showed each private placeholder exists only in its own role's template, so nothing rendered on either path; no recorded game result was affected. Scope: one search at the time of the incident, not a standing check of rendered prompts | One paragraph | "Impossible to leak"; the "would have helped the village" aside |
| 4 | Why it went unnoticed, and the fix | The checks were written in May against the earlier design and passed; they ran from a notebook cell. The rewrite landed on 3–4 June; the checks were wired into the batch runner on 6 June and the first game flagged. The fix in two sentences: the bundle built by role (wolves get the roster, the Investigator its results, the Vigilante its feedback, everyone else none), the vote step cleared of the Vigilante field, the comment rewritten to state the rule, a check added for the uncovered field; the next game flagged none with every check active. End with the lesson in one sentence: the checks existed but were not on the path that ran | A four-line timeline; one paragraph | Blame; test names and counts; later false alarms (one clause at most) |
| 5 | The same shape, four months later | Open as the second case of that lesson. An October re-read of the record against the code found three checks running but receiving no input from the runner (night records, held lines, eliminated players), so night-result isolation had had no live check since the ten-seat game began: guaranteed by the builders and unit tests only. Fixed the same day by lifting the inputs from the finished game's state; one check also rewritten because it read death days out of prose the new game no longer wrote | One paragraph | Function and file names |
| 6 | What this establishes | In the record's words: a boundary that does not reject is not a boundary; a check outside the execution path verifies nothing; audit the data layer, not the presentation layer, because that is what turned this into an early warning. Limits: the audit inspects recorded inputs, not rendered prompts; "none rendered" is scoped to that incident; games on the site save the same inputs and a nightly job is built to audit them (status unstated) | Three or four sentences | Any sentence saying served games are checked |

**Terms to gloss on first use.** "bundle of inputs" (the set of values built for one speaker's prompt;
never "payload" bare); "flag" (a check's report that private data crossed the boundary, not a leak
reaching a model); "rendered" (filled into the prompt text); "placeholder"; "batch runner" (the script
that plays games in bulk and runs the checks after each).

**Handle with care (from the chapter plan).** Flags, not leaks; "the first run with the checks in the
batch", never "the first run of the checks"; "none rendered" scoped to one search; framework behaviour
stated for the pinned versions, in the source note; no "impossible to leak"; no test counts, no CI, no
"AI-written tests"; the served-game audit described as built, never as run or as having found anything;
the deduction engine not mentioned; no folder or function names in headings or body.

**Verification needed before publication.** The before/after lines against `leakwire_smoke.log` and
`leakfix_smoke.log`; the vote-step statement against the fix commit; the framework claim against the
pinned versions named in the chapter plan; the October fix against its commit.

**Bridges.** Parent: the Level 1's "Tests and audits" subsection (the link exists). Evaluation's
code-checks page keeps its short version of the 109 and should link here (reconcile item). Chapter 7
for served-game capture. Chapter 1 for the sequential-discussion rewrite itself.

**Sources.** `evidence/agent_boundaries/experiment_log.md` §2 (the whole story), §6 (the October
recurrence); `evidence/agent_boundaries/report.md` §3–§4; the two smoke logs beside them; commits as
listed in the chapter plan's Level 3 section (source note only).
