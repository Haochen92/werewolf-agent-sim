# Information boundaries: portfolio content plan

Status: candidate plan, 2026-10-29, from a subagent pass checked against the record. The owner chose to keep the default recommendations for now and review all plans later; nothing here is approved. The open questions at the end stay listed; the defaults taken are below.

## Defaults taken (owner 2026-10-29: keep the recommendations for now)

- Revised 2026-10-30 after an outside review (owner approved): boundary, enforcement and detection kept apart; the audit is detection after the game, never prevention; "select authorised fields when building the input" replaces "one place removes information"; the figure relabelled with the audit as a branch; the intro states the requirement without "voids the game"; memory explained as a retrieval-policy violation, not a leak; coverage split into what the audit inspects and what its checks recognise.
- The nightly job for games played on the site is mentioned, without its status (owner 2026-10-30); wording in the care list.
- A Level 3 page may hang directly off this Level 1 page (no Level 2 pages; no empty levels).
- The 109-flag story is told in full on this chapter's Level 3; Evaluation's code-checks page keeps its short version and links here.
- Section 1 is prose with one example, not a table of every private item.
- The October recurrence (checks that received no input) goes on the Level 3 page only.
- A new four-step figure, not an extension of chapter 1's `context_isolation.svg`.
- Closing line: what each viewer's screen is sent is decided separately on the server (chapter 8).
- Done: `skills_inventory.md` moves secrets handling to chapter 7.
- Chapter card: Context isolation as the one public tag; invariant checks, metamorphic testing and least-privilege input construction as supporting terms.
- Level 3 title: "Private fields in the wrong agent inputs". *2026-10-31: the owner replaced the drafted page with a
  short version titled "Preventing private information leaks between agents" (`private_information_leaks.md`); the
  long draft stays in `_authoring/wrong_agent_inputs.reviewed-draft.md`.*

---

Candidate outline, 2026-10-29. Not page copy. Paths are relative to the repo root; `evidence/` paths
as written.

---

## Frame

*Revised 2026-10-30 after an outside review, approved by the owner. The page now keeps three things
unmistakably apart: the intended boundary, the code that enforces it, and the checks that can detect a
violation. The first cut credited the audit with prevention ("caught it before any private field
reached a prompt's text"; "warn one step before exposure"). The audit runs after each batch game; in the
incident, the private fields stayed out of the prompts because the templates did not name them
(`agent_boundaries/report.md` §2: an "incidental" filter), and the audit found them afterwards. Also
corrected: "a leak voids the game" (overstated), "one place removes information" (several builders
enforce one rule, and the template step filters by accident), the figure's labels (the filter sat on
the wrong arrow), and the memory gap (another role's lessons are not a current secret).*

**The reader's question.** Chapter 1 said each agent's input is built from what its seat may know.
Where is that boundary enforced, and how is it checked?

**The central answer.** The engine knows every player's role, but each agent should receive only what
is available to its seat. The boundary is built into the input: permitted fields are selected when each
seat's input is constructed, and nothing downstream is relied on to discard the rest. A post-game audit
of the recorded inputs detects mistakes; it does not prevent them. The one time a change broke the
rule, the audit found private fields in inputs where they did not belong; the templates happened to omit
them, and the fix moved the protection back to where the input is built. A helper that computes advice
for a seat is held to the same boundary. What the audit inspects and what its checks can recognise are
stated plainly.

**Page type: a Level 1 page that reads as a mechanism explanation.** The chapter has no Level 2 pages,
so the overview pattern would only produce one-line summaries. Progression: requirement → what each
agent may know → the boundary built into the input → the check that detects violations → the same rule
for computed advice → what the checks cover. Level 1 altitude and lengths: intro 150–200 words, five
sections of about 90–130, one example per section at most, no framework identifiers in the copy. About
750–900 words plus the figure. One Level 3 link, under the checks section.

**What chapter 1 already established (do not repeat at length).** From "Keeping each player's
information separate": players hold different information; one program holds everything, and an agent
knows only its call's input; a model cannot unsee its input; the term context isolation; the figure
`context_isolation.svg`. The intro recaps it in one sentence. Ch1's "Explore: Agent information
boundaries" link should point to this page.

**Scope line.** Chapter 3 covers what an agent can *use*; this page covers what it may not *see*.
Secrets and prompt injection are chapter 7's; what each viewer's screen is sent is chapter 8's.

**Tag.** Public: Context isolation. Supporting terms: invariant checks, metamorphic testing,
least-privilege input construction.

---

## Sections in order

### Introduction (no heading; about 150–200 words)

- **Main point: the requirement, without overstating the consequence.** Hidden information is part of
  the game's rules. The engine knows every role, but each agent should receive only what its seat
  could know. If a healer receives the wolves' identities, its decisions no longer test play under the
  intended rules, and anything measured on that game describes a different game. So the boundary belongs
  in the code that constructs each agent's input.
- One sentence picks up ch1. Then the page's question: where is that boundary enforced, and how is it
  checked?
- One sentence sets the ch3 line: this page is what an agent may not see; chapter 3 is how what it may
  see is presented.
- **No caveat bundle; no example beyond the healer sentence.**

### 1. What each agent is allowed to know (about 100–120 words)

- **Main point:** information has different audiences. Public information goes to every seat (the dead
  and their revealed roles, how many of each role are in play; made public on purpose, chapter 3 says
  why). Faction-shared information goes to that faction only (the wolves' list of each other and their
  night chat). Seat-private information goes to one seat (what it did at night and learned, its
  remaining uses of an ability, and what the agent itself produces: its honest suspicions of the others,
  its *reads*, and lines the game held back). A dead player receives nothing further.
- **Example:** a wolf's reads name its packmate, so reads are kept off the game's shared state
  entirely. Source: `evidence/agent_boundaries/experiment_log.md` §4 ("Reads"); `report.md` §1.
- Prose, not a table.

### 2. Building the boundary into the input (about 110–130 words, plus the figure)

- **Principle: select authorised information when constructing the seat's input; do not rely on
  downstream components to discard it.** Not "one place removes information": several builders (day
  and night) apply one rule, and a later step does filter, by accident.
- **Why:** the later steps do not protect. The formatter passes every field it is given through to the
  prompt variables. The template uses only the variables it names and silently ignores the rest, so it
  filters, but only as a side effect of how each prompt is written, and that changes with every prompt
  edit. The framework's declared state types document what a role should see but are not enforced for
  this kind of step (one clause at most; framework detail is the Level 3's).
- **Figure (new; the review's layout):**

  ```text
  Full game state
        ↓  Select fields permitted for this seat      ← the enforcement boundary
  Seat-specific payload ──→ recorded ──→ post-game audit (detects; off the path to the model)
        ↓  Format the supplied fields
  Prompt variables
        ↓  Render the variables named in the template  ← filters only by accident
  Model prompt
  ```

  The audit branches from the recorded payload, not from the path to the model, so the figure shows
  what prevents exposure and what detects mistakes. Source: `agent_boundaries/report.md` §2; code
  `Agents/nodes/day/flow.py::_private_fields`, `Agents/nodes/night/solo.py`, `pack.py`.

### 3. Checking that the boundary is respected (about 120–130 words, plus the Level 3 link)

- **Main point: detection, after the game.** Every model call's input is recorded. After each game the
  batch runner plays, code checks the recorded inputs against who may receive each item (wolf names only
  to wolves, a night result only to the seat that acted, a held-back line to nobody, nothing to a dead
  player), and one violation fails the batch. Unit tests build inputs with the real builders and plant a
  violation to show the check catches it. Games played on the site save the same inputs, and a nightly
  job is built to apply the same checks to them (owner 2026-10-30: mention the job, without its status;
  see the care list for the exact wording).
- **Supporting incident, told as detection, not prevention:** a rewrite of the discussion gave every
  speaker the same full input. The audit found private fields in inputs where they did not belong. In
  this incident the templates omitted those fields, so the models did not receive them. The fix removed
  them when building each seat's input, rather than relying on which variables a template happened to
  use; the next run flagged none.
- **Moved to the Level 3:** the raw log lines, the 109-flag arithmetic, the framework behaviour behind
  the code comment, and the later checks found receiving no input.
- **Level 3 link:** "Private fields in the wrong agent inputs →".

### 4. Applying the same rule to computed advice (about 100–120 words)

- **Main point:** a helper that computes advice must respect the same boundary as the agent. The
  deduction engine (chapter 3) writes conclusions into a seat's prompt, and the program running it holds
  the true roles; it reads only a view built from that seat's own input, so it sits inside the existing
  boundary with no second place to enforce it.
- **The test, in plain words first:** if hidden roles change while the player's visible information
  stays the same, the generated deductions should stay the same. Then name it: a **metamorphic test**.
- **What it shows and does not:** it checks that the output does not depend on hidden information; it
  does not by itself show that every deduction is correct. Correctness is Evaluation's code-checks page
  (one link).
- **Example:** a test swaps two hidden roles the Investigator cannot see and requires identical lines.
  Source: `tests/engine/deduction/test_candidates.py::test_hidden_roles_the_seat_cannot_see_do_not_change_its_items`;
  the same pattern in `test_evil_seat.py`, `test_covers.py`; `evidence/gameplay/deduction/report.md`
  §3–§4; `Agents/deduction/seat_view.py`.
- **Authorship:** the engine is AI-written; phrase as a design statement. No test authorship.

### 5. What the checks cover (about 90–120 words)

Two questions, kept apart:
- **What does the audit inspect?** Recorded inputs from batch runs (state the scope plainly), not every
  call path and not every final rendered prompt. Two calls are built from the same filtered input but
  not recorded (the memory lookup's query and a human player's seat); the rendered prompt text was
  checked by hand at the time of the incident, not every game.
- **What can its checks recognise?** Known fields and some exact text, not every possible disclosure: a
  secret restated in other words would pass.
- **Memory, explained before it is named.** Each role's lessons from earlier games (chapter 4) are
  stored under that role, and a seat can query only its own role's store, by construction; nothing
  asserts it. Serving another role's lessons would not reveal a current opponent's secret role (lessons
  come from past games); it would break the retrieval rule and give the seat guidance meant for a
  different role. Call it a policy violation, not a leak. The assertion that would check it is designed,
  not built.
- Source: `agent_boundaries/report.md` §5; `evidence/evaluation/deterministic_audits/report.md` case 1;
  `Agents/memory/retrieval/accessors.py`.

### Closing line (one sentence)

What each viewer's screen is sent (a player, a spectator, a replay) is decided separately in the
server, from public information only; chapter 8 covers it.

---

## Narrative check

> Hidden information is part of the game's rules, so each agent should receive only what its seat could
> know, and the boundary belongs where its input is built. Information has three audiences: everyone,
> one faction, or one seat, including what an agent produces itself. The permitted fields are selected
> when each seat's input is constructed; later steps pass things on or filter only by accident, so
> nothing downstream is trusted to discard what slipped through. After each batch game an audit checks
> the recorded inputs against those audiences; it detects mistakes rather than preventing them, and the
> one time a rewrite broke the rule, it found the private fields, which the templates happened to omit,
> and the fix moved the protection back to the builders. A helper that computes advice is held to the
> same rule, tested by changing what the seat cannot see and requiring the same output. And the page
> says what the audit inspects and what its checks can recognise.

**Does it hold?** Yes: intended boundary → enforcing code → detecting checks → the same rule applied to
a new component → coverage. The three-way distinction (boundary, enforcement, detection) is visible in
the headings and in the figure.

---

## Level 3 recommendation: yes

**Page:** "Private fields in the wrong agent inputs" (owner 2026-10-30; replaces "The superset payload:
109 flags, none rendered").

**Reader question:** a change put private data into every role's input. How did it get past every
step, why did no model see it, and why did it go unnoticed until the checks were wired in?

**Why it earns a page (what it adds that section 3 cannot hold):**
- **The cause, which is the interview-worthy part:** a code comment justified one universal bundle with
  "the framework ignores extra keys". That is true where a compiled subgraph filters its input to its
  declared schema, and false for the dispatch these steps use, which delivers the bundle verbatim. The
  documented justification was the bug. State the framework versions in the source note.
- **The analysis:** what the 109 are (flag events, not distinct inputs: 76 wolf-identity flags = 38
  inputs × 2 lines, plus 33 investigator-result flags); a third field (the vigilante's shot feedback)
  leaking with no check covering it, found by inspection, on the vote path as well as discussion.
- **The severity reasoning:** an exhaustive search of the templates showed the private placeholders
  exist only in each role's own template, so nothing rendered and no game result was affected.
- **The verification lesson:** the checks were correct but ran only by hand, so nothing fired between
  the rewrite and the day they were wired into the batch runner. The same failure shape recurred later,
  when three checks were found to be receiving no input from the runner and were fixed the same day:
  a check outside the execution path verifies nothing.
- **Before/after exhibit**, as in section 3, with the fix stated (bundle built by role; the comment
  rewritten to state the rule and why a shared bundle is unsafe).

**Passes the Level 3 tests:** one focused follow-up question; the parent keeps the finding and its
essential caveat (caught, none rendered, fixed); the L3 adds the cause, the arithmetic and the
severity method, which would bury section 3. About 800–1,100 words.

**Sources:** `evidence/agent_boundaries/experiment_log.md` §2 (the whole story) and §6 (the October
recurrence); `report.md` §4; the two colocated logs; fix commit `ef43342`, check added `8008623`,
wiring `e9d30ba` (source note only).

**Overlap to settle:** Evaluation's code-checks page (`writeup/evaluation/code_checks/code_checks.md`)
already tells the 109 briefly and the October recurrence in a paragraph. The L3 should be the one full
home; code-checks keeps its short version and links here.

---

## Disposition of the blocks

| Block | Segment | Lands in | Notes |
|---|---|---|---|
| 1 | Problem: hidden information is part of the rules | Intro | The healer-who-knows-the-wolves framing; the "correctness, not play" placement |
| 2 | Design: four layers, one enforcer | Section 2, with the new four-arrow figure | No layer identifiers in copy; framework behaviour stated plainly; version in the source note |
| 3 | Verification: capture, checks, unit tests | Section 3. Blind spots → section 5 | "Eleven checks, nine live" stays off; the checks are described by what they check. Served-game audit: held (open question 1) |
| 4 | Case study: 109 flags → 0 | Section 3 lead example (short) + Level 3 (full) | Before/after exhibit |
| 5 | Gaps | Section 5 | Memory isolation by construction is the lead; unlogged call sites in one sentence. "Resumed served game only partly captured" applies only if served audits are mentioned; otherwise drop it |
| 47 | Design: the deduction engine reads one view built from the seat's bundle; metamorphic test | Section 4 | The engine is AI-written; it is a design statement, not an authorship claim |
| (49, parked) | Public-by-design fields | Section 1, one clause → chapter 3 | Its real reason (fewer errors) is ch3's |
| (98, 99) | Prompt injection; secrets | Not here → chapter 7 | Settled scope |
| (158) | Served-game capture and nightly audit | Chapter 7 ("Seeing what happened"); here only per open question 1 | Not installed per the record |
| Report §1 private table, reads, held lines | (inside blocks 1 and 3) | Section 1 | Not separate blocks; the reads are section 1's lead example |
| Spectator wire | — | Closing line → chapter 8 | |

---

## Claims to handle with care

- **The served-game leak audit is not running, per the record.** It is built and tested, and the
  capture table is migrated. But the nightly job was found not installed on 2026-10-23 (no crontab
  entry, no log; `writeup/_planning/map.md` "Eval hardening" item 3; `evidence/evaluation/experiment_log.md`
  line ~324). On 2026-10-26, 11 of 68 served games had a capture and none had been audited (map block
  158). My read-only check today (2026-10-29): the `ubuntu` user's crontab has no leak entry and
  `/home/ubuntu/leak_audit.log` does not exist. A root crontab or a systemd timer was not checked. So:
  **no sentence may say or imply that games on the site are checked.**
  *Updated 2026-10-30 (owner): the nightly job may be mentioned, without saying whether it is turned
  on.* So describe what exists, never what it has done: "games played on the site save the same inputs,
  and a nightly job is built to apply the same checks to them". Never "are checked each night", "a
  nightly audit runs" or any result from it. Interview risk: a reader may ask what it has found;
  installing it and running it over the existing captures would make a stronger sentence true.
- **Scope of the live checks:** "after every game the batch runner plays" (the batch runner and the
  capture scripts), never "every game".
- **"Zero since the fix":** the record supports "the post-fix run flagged none" and no real leak since.
  It also shows false alarms (the reads check was narrowed three times, and the pack's chat was once
  flagged in a packmate's prompt). Prefer "the next run flagged none" on L1; the L3 may mention the
  narrowing.
- **"None rendered"** rests on one exhaustive template search at the time of the incident, not a
  standing check of rendered prompts. Keep it scoped to that incident.
- **Framework behaviour** (the bundle is delivered verbatim; a compiled subgraph filters; templates
  ignore extra variables) holds for the pinned versions (`langgraph 1.1.10`, `langchain-core 1.3.3`).
  Version goes in the source note.
- **Enforcement is code that selects, not a guarantee against everything.** Don't write "impossible
  to leak". A model can still claim knowledge it doesn't have (ch1 already says this).
- **Memory isolation:** "holds by construction, not asserted". The fix is designed, not built. Never
  "memory is isolated and verified".
- **Authorship:** the deduction engine is AI-written. No test authorship or counts (no "372 tests",
  no "1,064 pass"). "Unaudited AI-written tests" and missing CI stay off.
- **Dates:** none inside the explanation (no "June 6", no "three days" on L1; the L3 may use the
  timeline because it is causal there).
- **Wording:** "flags", not "leaks", for the 109 (they are flag events, and none reached a model);
  "the first run with the checks in the batch", not "the first run of the checks".
- **No folder or code names in headings;** none in body copy except in source notes.

---

## Open questions for the owner

1. **Settled 2026-10-30: mention the nightly job, without its status** (wording in the care list). *Was:* **Served-game audit.** Install the cron and run it over the existing captures before publishing, so
   one sentence ("games played on the site are checked the same way each night") becomes true? Or
   leave served games off this page, as Evaluation's code-checks page does? I recommend leaving them
   off until it has run, and changing the structure proposal's chapter 2 line to match.
2. **Level 3 directly under Level 1.** Chapter 2 has no Level 2. Is a Level 3 hanging off an L1
   section acceptable here? (Evaluation's rule anchors every L3 in an L2 subsection.)
3. **Home of the 109 story.** Should this chapter's L3 be the single full account, with Evaluation's
   code-checks page keeping its short version and linking here? Both pages currently show the same
   flag lines; this page would show the before/after pair instead.
4. **Section 1: table or prose?** A five-row "item → who receives it" table is the one comparison a
   reader might scan. Is it worth its space at L1, or should section 1 stay prose with the reads
   example?
5. **The October "three checks fed nothing" recurrence.** Put it only in the L3 epilogue (my
   recommendation; code-checks already tells it), or add one clause to section 3?
6. **Figure.** A new four-arrow figure for section 2, or extend ch1's `context_isolation.svg`? I
   recommend a new one: ch1's figure shows *what* each player receives, not *where* the filter sits.
7. **Closing line.** "Decided separately in the server" rather than "the same rule carries through to
   the screen"? (See the closing-line note.)
8. **Stale cross-reference.** `writeup/_planning/skills_inventory.md` "Chapter assignments" still gives chapter
   2 "secrets handling" (and line 51 the security row). It should move to chapter 7 per the 2026-10-29
   ruling. Not edited here.
9. **Chapter card tags.** Proposed: context isolation (public tag); invariant checks and metamorphic
   testing as supporting terms on the page. Confirm.
