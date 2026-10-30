You are checking the claims on one page of an engineering portfolio against its sources. You work
read-only in the project repository. Do not edit any file.

WHAT TO READ
- The page file named below: its page copy (the `## Page copy` section) and its sources comment at
  the end, which maps claims to evidence.
- The authoring brief named below, if it exists: its Frame, Evidence selection and Open questions.
- The evidence the sources comment and the brief cite. Follow links into `evidence/` as needed.
- The evidence rules in `writeup/portfolio-writing-prompt.md` (sections EVIDENCE DISCIPLINE and WHAT
  STAYS OFF THE PAGE) and, for a Level 2 or 3 page, the section CAUSAL AND EVIDENTIAL PRECISION in
  `writeup/portfolio-level-2-writing-prompt.md`.
- The chapter's outline in `writeup/map.md`, including its "Handle with care" list where one exists.

WHAT TO CHECK
Consequential claims, the ones whose failure would mislead a reader about how the system works or
what an experiment showed:
- **Mechanisms:** does the page describe how something works the way the records describe it? When
  the page describes current behaviour, check the code named in the sources; when it describes a
  historical experiment, check the records of that time, not today's code alone.
- **Comparisons:** are separate experiments kept apart? Is a bundled change presented as isolating
  one factor? Is a replay presented as a frequency estimate?
- **Inference:** does the conclusion follow from the evidence, even if the source repeats the same
  wording? Single-item variability does not estimate uncertainty in an aggregate; a few repeated
  scores do not establish a universal noise cutoff; sharing requirements does not guarantee aligned
  interpretation. These are examples, not a mandatory statistical audit.
- **Proportionality:** assess the actual claim (mechanism, diagnosed failure, practical choice or
  general improvement). Narrow an unsupported claim rather than demand new research to defend an
  unnecessary stronger one. Keep material limitations; do not impose research-level completeness
  on a bounded engineering decision.
- **Validation:** calibration vs held-out evaluation; correctness vs consistency; reviewed cases vs
  representative coverage; intended checks vs checks actually completed.
- **Scope:** does the wording ("every", "only", "never", "proves", "establishes") match what was
  tested? Is the sample unit right (turns vs games vs judgements; repeated samples vs independent
  situations)?
- **Status:** built vs run vs deployed vs validated.
- **Ownership:** first-person claims the records support; nothing AI-written presented as hand-written.
- **Off-page items:** anything from the Handle-with-care list, or repository bookkeeping that reflects
  poorly, that has reached the page copy.
- **Numbers:** check a number only where a claim depends on what it counts (its denominator, unit or
  comparison). The owner has ruled out a number-by-number audit; numbers are lifted from the reports
  as they stand. Do flag a number that conflicts with its cited source.

Do not judge style or structure; a separate reviewer does that.

OUTPUT
Return exactly these sections:

## 1. Findings
One entry per claim with a problem, most consequential first:
- **Claim:** short exact quote from the page copy, with its heading.
- **Source checked:** file and section (or code path).
- **Verdict:** overstated · unsupported inference · unsupported · conflicts with source · wrong mechanism · wrong status ·
  ownership · off-page item · unclear (needs the owner).
- **Why:** one or two sentences.
- **Suggested scope:** what the claim can say instead, in one sentence, or "remove".

## 2. Checked and supported
A bulleted list of the consequential claims you checked that hold, one line each with the source.
This shows what was covered.

## 3. Not checked
Claims you could not check and why (source missing, historical configuration not recorded, etc.).
