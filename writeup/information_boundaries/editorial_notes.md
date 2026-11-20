# Information boundaries: editorial notes

## 2026-10-30: first draft of the Level 1 page

- **Explanatory path:** requirement (hidden information is part of the rules; the Healer reading the
  wolves' night chat) → the tiered classification (everyone, one faction, one seat, no prompt at all) →
  enforcement where the input is built (least privilege; the figure with the audit as a branch) →
  detection after the game, with the one real break told as detected and fixed → the deduction engine
  held to the same boundary (metamorphic tests) → what the checks inspect and recognise, and memory.
- **Moved out:** the flag arithmetic, the uncovered third field, the framework detail behind the code
  comment, the notebook-only period and the October checks fed no input → the Level 3, "Private fields
  in the wrong agent inputs" (link specification only; not drafted).
- **Claim changes from review:** recording scoped to player turns; the two unrecorded inputs named; the
  planted-leak consequence narrowed; the metamorphic claim scoped to the cases tested; the template
  search described as what it was; the formatter's behaviour corrected; the memory fix "proposed, not
  built". The figure's audit branch comes off the prompt variables (report §3), not the payload.
- **Owner rulings applied:** the intro example (a non-wolf with the wolves' chat); section 1 as the
  tiered classification; the nightly job for site games mentioned without its status.
- **Checked:** the editorial cold read and the claims review (both in `_authoring/`). "Editorially
  revised" is not "factually verified" beyond what the claims review covered.

## 2026-10-30: computed advice moved to chapter 3

The section on testing the deduction engine's output against hidden information (the metamorphic test,
with an Alice/Bob illustration) belongs to chapter 3, where the engine is discussed (owner). This page
keeps one sentence: the engine reads a view built from the seat's payload, and chapter 3 explains the
rest. The material is in `writeup/context_engineering/content_plan.md`, section 4.

## 2026-10-31: first draft of the Level 3 page "Private fields in the wrong agent inputs"

- **Explanatory path:** the finding in two sentences for direct arrival → what a flag is and what the
  109 counted (38 inputs × 2 lines + 33, all discussion turns; the Vigilante field outside the count,
  on the vote path too; the flag pair lifted from the pre-fix log) → where the shared bundle came from
  (the comment's "ignores extra keys"; the two ways of connecting steps, in plain words; the Vigilante
  field's separate origin that morning) → whether any model saw it (the template search, scoped to
  that day) → why nothing fired for three days, the fix and the clean post-fix block → the October
  instance (three checks fed nothing, with each inert window dated; the night-record gap 3–14
  October; the rewritten dead-player check; no re-audit of that window) → the record's three lessons
  read against the incident, and the limits.
- **Moved out or left off:** framework terms and the pinned versions, the full comment sentence, the
  commits and the fingerprint timing (source note); the "would have helped the village" aside; check
  and test counts; the reads check's later false alarms; the served-game capture work of the same
  session (chapter 7); the nightly job's status (owner ruling 2026-10-30).
- **Claim changes from the reviews:** the opening no longer says "every role's private fields"
  (three roles'); the shared bundle "by 6 June" carried three fields, since the Vigilante field was
  added that morning by a separate change; "the next game" became "a game played after the fix"
  (the post-fix fingerprint predates the fix commits); "with every check active" was dropped, because
  the June wiring already passed no eliminated-player list, so that check was inert from the first
  wiring; the October case is "found again", not "came back", with each check's inert window dated;
  the night-record change is dated 3 October without dating the move to ten seats; "verified in unit
  tests only" became "unit tests covering only part of" the builders; the three lessons are now
  quoted verbatim; the after-exhibit marks its omitted line; the search of the templates is written
  without "I". Added at the editorial reviewer's request: what is recorded (prompt variables made from
  the bundle, copied unchanged), the shared pattern of the two cases, and what the June lesson "does
  not reject" refers to.
- **Checked:** two editorial cold reads and two claims reviews (all four in `_authoring/`); the
  before/after lines against both smoke logs; the comment and the vote-step change against the fix
  commit's diff; the June wiring's call against its commit; the framework versions against
  `pyproject.toml`; the October fix against its commit. "Editorially revised" is not "factually
  verified" beyond what those reviews and checks covered; owner review pending. The Level 1's
  "Explore" line is plain text, so the editorial reviewer's parent excerpt came from a scratch copy of
  the chapter in which that line carries the link; the Level 1 was not edited.
- **Length:** about 1,260 words of page copy against the outline's 800–1,100 guide; the overage is
  the review-driven additions listed above, each named in the brief for the owner to keep or cut.

- **2026-10-31, later (owner):** the drafted Level 3 was replaced by the owner's short version, "Preventing
  private information leaks between agents" (`private_information_leaks.md`, about 330 words: problem, cause,
  fix, lessons). The long draft and its reviews stay in `_authoring/`. Facts in the short version checked
  against the record; one wording change: "a game played after the fix" (the record does not fix the order).
  The Level 1's Explore line now carries the live link.
