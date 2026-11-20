# Explanation prototype: Private fields in the wrong agent inputs

Page: `writeup/information_boundaries/wrong_agent_inputs.md` (superseded 2026-10-31 by the owner's short version, `private_information_leaks.md`) · Level 3 · Purpose: diagnostic investigation
told as one connected story (closest example B, successive questions; the incident pattern from
`page_types.md`: impact → mechanism → containment → verification → remaining exposure) · Date: 2026-10-31
Checkpoint: outline approved in conversation 2026-10-31 (`wrong_agent_inputs.outline.md`, after a cold review).

Authoring material, not page copy. The cold reviewer does not see it. Topics and presentation:
`wrong_agent_inputs.outline.md` (seven sections, exhibits, "stays off" column, terms to gloss,
handle-with-care); chapter plan `../content_plan.md` ("Level 3 recommendation", "Claims to handle with
care"); `writeup/_planning/map.md` blocks 2–5 and the Handle-with-care list near line 266.

## Reader and explanation

- **Reader outcome:** the reader can say how a documented design decision put three roles' private
  fields into every speaker's input, why no model saw them (the templates named only their own
  placeholders), why nothing fired for three days (correct checks that nothing ran), and can recognise
  the same shape in the October case (checks that ran but were fed nothing).
- **Starting knowledge:** the parent gives the payload/variables/template stages, the healer example as
  a real failure, the refactor's wrong assumption about the framework, "the first batch run with the
  audit connected" finding wolf identities and Investigator results, the template review, the fix and
  the clean next run, and that the audit reads recorded inputs. This page adds the cause, what the 109
  counted, the severity method, the timeline and the recurrence. New terms glossed in a clause on first
  use: bundle of inputs (mapped to the parent's payload), flag, batch runner, placeholder, the Vigilante,
  withheld line.
- **Concept order:** (1) what a flag is: the checks read the recorded variables, which copy the bundle's
  values unchanged, so a flag says the boundary was crossed, not that a model saw it → (2) the 109 as
  flag lines (two per input for one check) and the third field no check covered → (3) the cause: a
  shared bundle justified by a framework behaviour that belongs to a different way of connecting steps;
  the Vigilante field's separate origin → (4) severity: the templates fill only their own placeholders,
  each private placeholder lives only in its role's templates, so nothing rendered; scoped to one search
  → (5) why three days: the checks ran only by hand; the fix → (6) the October instance, as the same
  pattern → (7) the lessons read against the incident, and the limits.
- **Likely confusion:** reading 109 as 109 leaks that reached models, or as 109 contaminated inputs;
  reading "none rendered" as a standing guarantee; reading "a boundary that does not reject" as a
  verdict on the detect-only audit. Each is met where it would arise.
- **Section order:**
  - §0 Opening: the finding in two sentences and what the page adds.
  - §1 What the checks found: what a flag is; the 109 as 38×2 + 33 in a table, all discussion turns; the
    Vigilante field outside the count, on the vote step too; the pre-fix flag pair inside its banners.
  - §2 Where the bundle came from: the discussion rewrite's shared bundle; the comment's "ignores extra
    keys"; the two ways of connecting steps, plainly; the Vigilante field added that morning into both
    builders' common part.
  - §3 Did any model see it?: the template question, the search, each placeholder only in its role's
    templates, nothing rendered on either path, no game result affected; scoped to one search.
  - §4 Why it went unnoticed, and the fix: four-line timeline; the fix in one paragraph; the clean
    post-fix block.
  - §5 The same shape, found in October: the shared pattern stated; three checks running but fed
    nothing, each window dated; the night-record gap 3–14 October; the fix and the rewritten dead-player
    check; no re-audit of those windows.
  - §6 What this establishes: the record's three lessons quoted, the first and third read against the
    incident; the limits; the site games' capture and nightly job as built.

## Sample passage

(§2, the difficult relationship: why "the framework ignores extra keys" was true and still wrong. As
drafted before review; the page's version leads with the contrast, per the first editorial read.)

The rewrite made the day's speakers take turns instead of speaking at once (chapter 1 covers that
change). The earlier design had built one bundle per role and handed each role its own. The rewrite
built one bundle with everything in it and handed it to every speaker, and the comment on that function
said the framework "ignores extra keys" on the message carrying the bundle, so each role's step would
read only what it needed.

That was true of a boundary the bundle never crossed. The framework has one way of connecting steps
that strips any field the receiving step did not declare, and another, the one this path used, that
hands the step whatever it was sent. The step's declared field list documents what the role should see
and enforces nothing when the game runs, and the code that turns the bundle into prompt variables reads
straight from what arrived. The private fields rode through every stage. The documented justification
was the bug.

## Evidence and scope

- **Sources:** `evidence/agent_boundaries/experiment_log.md` §1 (checks written 2026-05-09, notebook
  cell), §2 (the whole June story: verdict, cause, composition, third field, timeline, severity, fix,
  verification, lessons), §4 (the held-line check, 2026-07-02), §5 (night records replace the result
  fields 2026-10-03; the night-record check 2026-10-09; day builders pinned 2026-10-07), §6 (the October
  re-verification: three checks fed nothing, the fix, the rewritten dead-player check);
  `evidence/agent_boundaries/report.md` §2 (the layer model and the framework note with pinned
  versions), §3 (the checks read the prompt-input dict one layer upstream of rendering; a flag means the
  payload boundary was crossed; the nightly `leak-audit` as built), §4 (the case study), §5 (closed
  gaps); `leakwire_smoke.log` (109 `LEAK:` lines, 38 + 38 + 33; the lifted healer pair; `LEAK DETECTED
  ...: 109 leak(s)`; `WITH PRIVATE-INFO LEAKS`); `leakfix_smoke.log` (empty block between the banners,
  `Batch complete: 1 succeeded, 0 failed`, `EXIT: 0`); commits `291668f3` (2026-06-06 02:43 UTC, the
  Vigilante field added to both builders' base dict), `ef43342` (fix: role-gated speaker payload,
  `fan_out_day` base payload cleared of `vigilante_results`, docstring rewritten; its diff carries the
  old docstring sentence quoted on the page), `8008623` (the Vigilante check added), `e9d30ba` (checks
  wired into `run_batch`, called as `run_leak_tests(prompt_log, roles)` with no eliminated-player list;
  the call was unchanged until the October fix), all 2026-06-06; `c58e5c8d` (the post-fix run's
  fingerprint, 12:41 UTC, before the fix commits' 13:34 UTC timestamps); `94304a22` (2026-10-15, the
  `leak_inputs` fix and the rewritten dead-player check); `pyproject.toml` (`langgraph==1.1.10`,
  `langchain-core==1.3.3`).
- **Claim and limits:** a diagnosed mechanism (shared bundle + pass-through dispatch + a formatter that
  forwards everything) with its containment (templates named only their own placeholders) and its
  repair (selection by role, the vote step cleared, a new check, the checks wired into the runner);
  then a second instance of the verification gap, found rather than reborn. Limits kept beside the
  claims: a flag is not a leak to a model; "none rendered" rests on one search of the templates on the
  day, and the templates have since been rewritten; the audit reads recorded variables after the game;
  no re-audit of the October windows; the site games' job is built, status unstated.
- **Elsewhere:** the sequential-discussion rewrite itself → chapter 1; the served-game capture →
  chapter 7; Evaluation's code-checks page keeps its short version of the 109 (reconcile item: it should
  link here). Handle-with-care items applied: flags not leaks; "the first run with the checks in the
  batch"; "none rendered" scoped; framework terms and versions in the source note only; no "impossible
  to leak"; no test or check counts; no CI; no AI-written tests; the nightly job as built, never run;
  the deduction engine absent; no folder, file or function names in headings or body; the "would have
  helped the village" aside and the later false alarms left off (the plan allows one clause on the
  narrowing; declined for budget and because it answers a different question).
- **Open questions:**
  1. The comment is quoted as the fragment "ignores extra keys" rather than the full sentence, because
     the full sentence names the framework and its dispatch type, which the rules keep to the source
     note; the full sentence is in the source note. Confirm this satisfies "the comment quoted".
  2. First person: the page says "I put the selection back" for the June fix (orchestration code) and
     uses neutral voice for the template search and the October re-read and fix, since the record does
     not say who did them. Confirm or neutralise the one remaining "I".
  3. The October fix: the record (report §5, log §6) says found and closed 2026-10-14; the commit
     carrying it is dated 2026-10-15 08:30 UTC. The page gives the fix no day; the notes and source
     note record both dates.
  4. The page says the record holds no re-audit of the games played while the three checks were inert
     (6 June, 2 July and 3 October to 14 October respectively). If the owner has run or runs the fed
     checks over those batch records, one sentence with the outcome would close the October section the
     way the June section closes; the claims reviewer and the editorial reviewer both asked for it.
  5. "By 6 June carried three roles' private fields" and "hours, not days" rest on commit 291668f3's
     timestamp (02:43 UTC) against the fix commits (13:34 UTC). The experiment log does not date the
     Vigilante field's arrival; confirm the reading.
  6. The move to ten seats is dated only loosely ("as the game moved from nine seats to ten"); the
     claims reviewer notes the nine-seat deal was still dealt on 7 October. The night-record date
     (3 October) and the check (9 October) are the dated facts.
  7. The outline said "the next run flagged none"; the page says "a game played after the fix", because
     the post-fix fingerprint predates the fix commits and the game order is not recorded. The parent
     says "the next run"; align one way when the parent is next revised.
  8. Length: about 1,260 words of page copy against the 800–1,100 guide. The overage is the
     review-driven additions: what is recorded and why a flag implies the bundle (first editorial read),
     the Vigilante field's origin (both reads), the shared pattern and the dated inert windows (second
     read, blocking), the "does not reject" reading (second read), the harmless-until sentence (first
     read's probe). Each is a candidate to cut if the owner prefers the guide.

## Review resolution

| Finding | Action and reason | Whole-section recheck |
|---|---|---|
| E1: the vote-step leak's origin never stated | Fixed: commit 291668f3 added the Vigilante field to both builders' common part on the morning of 6 June; one sentence in §2, one clause in §1 | §1, §2, §4 reread; "three days" now applies to two fields and the page says the third was in place for hours |
| E2 / C4: "bundle" blurred the parent's payload and prompt variables; the record is the variables, not the bundle | Fixed: §1 maps the bundle to the payload once and says the checks read the recorded variables, which copy its values unchanged; "data layer" lesson in §6 reads "the variables one step before rendering" | §1, §6 |
| E3: `all_disabled` in the after-exhibit run name invites "the checks were off" | Fixed: the line is omitted and the omission marked, per C2's second-pass finding; the source note explains the run name | §4 |
| E4 / E9: October terms (the record, ten seats, game master, which three checks) | Fixed: the three checks named by purpose; "narrator" replaced by "the engine's transcript announcements"; "the project's record of this boundary"; ten seats tied to 3 October without dating the move | §5 |
| E5 / E2 (second read): "the same shape" never defined; October did not match June's "not on the path" | Fixed: §5 opens with the pattern covering both ("a check that nothing on the running path feeds with real data") and states how the two differ | §5, §6 |
| E6 / E1 (second read, blocking): October has no outcome; how long each check was inert | Fixed in part: each inert window dated from the commits; the unit-test verification stated; the page says the record holds no re-audit and why the builders are the reason to expect nothing crossed. Flagged: open question 4 | §5 |
| E7: "the checks were correct and present" overreaches given the uncovered field | Fixed: "the checks that existed" | §4 |
| E8: the after-exhibit arrived before the cause and the fix; roadmap order wrong | Fixed: the after block moved to §4; the before block now shows its banners so "the block between the two banners" has a referent (E10, second read); roadmap reordered | §1, §4 |
| E9 (first read): "true of a boundary the bundle never crossed" is a riddle | Fixed: §2 leads with the two ways of connecting steps, then "true of the first, this path used the second" | §2 |
| E10 (first read): the nightly-job sentence repeats the parent and leaves the October gap open for it | Fixed: one clause, "together with the game-state fields the October fix added" (report §3, log §6; confirmed by the claims reviewer against the capture code) | §6 |
| E11: the "one search" caveat repeated | Fixed: stated once in §3; §6 keeps one clause | §3, §6 |
| E12 / E6 (second read): the Vigilante undefined; "town" undefined | Fixed: glossed at first mention in the opening as "a villager-side role that may shoot at night and is told privately what its shot revealed" | opening, §1 |
| E4 (second read): "a boundary that does not reject" seems to indict the detect-only audit; the record unidentified | Fixed: §6 reads the first lesson against the layers the comment trusted and names selection at build time as the step that rejects, the checks as the detector; the record linked | §6 |
| E5 (second read): §1's first paragraph restated the parent | Fixed: cut to the new point (flag ≠ seen; the `LEAK:` label); the batch-runner gloss moved into the sentence that first needs it | §1 |
| E7 (second read): "batch run" vs "game"; which turns the 38 and 33 count | Fixed: "a batch of one game" became "ran its first game"; "all are discussion turns" added (log §2: the superset was the speaker builder; the vote fan-out was already role-gated for those fields) | §1 |
| E8 (second read): the lesson sentence repeated at the top and bottom of §4 | Fixed: the closing sentence removed; the pattern now opens §5 | §4 |
| C1: "every role's private fields" | Fixed: "three roles' private fields", named | opening |
| C2: "with every check active" overstates the June run; "by then" misdates the eliminated-player input | Fixed: the phrase dropped; §5 dates that check's inert window from the first wiring, confirmed against e9d30ba's call | §4, §5 |
| C3: first person for the template search | Fixed: the search is written without "I"; the June fix keeps "I" (open question 2) | §3 |
| C5: "rode through every stage" | Fixed: "up to the templates" | §2 |
| C6: a paraphrase presented as the record's words | Fixed: the three lessons quoted verbatim from the log's "Lessons" | §6 |
| C7: "verified in unit tests only" over the whole window | Fixed: "with unit tests covering only part of them" (day builders from 7 October, night builders only with the fix) | §5 |
| C1 (second pass): "grew to ten seats on 3 October" conflicts with the record | Fixed: 3 October dates the night-record change and 9 October the check; the move to ten seats is not dated | §5 |
| C2 (second pass): "came back" / "returned" overstates; one check was inert since June | Fixed: "found again"; heading "The same shape, found in October"; the windows dated | opening, §5 |
| C3 (second pass): the Vigilante field's date and route | Fixed: dated to early 6 June in §2; the opening says the bundle carried three fields "by 6 June" (open question 5) | opening, §2 |
| C4 (second pass): the omitted log line unmarked | Fixed: "[one line omitted]" marker; the before block's elision marked the same way | §1, §4 |
| Declined: the plan's optional clause on the reads check's later false alarms | Not added: answers a different question (what the checks have flagged since), and the page is over the guide | — |

## Trial record

Draft snapshots: `wrong_agent_inputs.first-draft.md` (before reviewer edits, 1,294 words of page
copy); `wrong_agent_inputs.reviewed-draft.md` (after, about 1,260 words). Reviews:
`wrong_agent_inputs.review-editorial.claude.20261031T061519Z.B2cz7R.md`,
`wrong_agent_inputs.review-claims.claude.20261031T061640Z.AJjqCR.md` (first pass);
`wrong_agent_inputs.review-editorial.claude.20261031T062046Z.s68NJy.md`,
`wrong_agent_inputs.review-claims.claude.20261031T062254Z.BTQD8P.md` (second pass, after the
structure changed: the after-exhibit moved, §5 rebuilt). The trims after the second pass were wording
only; no third review.
Model and owner interventions: drafting agent on the default model; outline approved in conversation
2026-10-31 (checkpoint satisfied before this run); reviewers on the `claude` CLI per the skill (opus).
Parent excerpt: the Level 1's "Explore" line is plain text, so `parent_context.py` finds no link; the
editorial reviews were run on a scratch copy of the chapter folder (outside the repo) in which that line
carries the link, so the reviewer received the excerpt the script's own rule produces (the parent's
introduction plus the "Tests and audits" subsection). The Level 1 page was not edited.

| Owner change | Kind | Explanation redesigned or local edit? |
|---|---|---|
| | concept selection / order / missing connection / example or representation / prose / claim support | |

Fill after feedback; do not invent an owner usability score. Word count is a guide, not a quality measure.
