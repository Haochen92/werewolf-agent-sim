# The playbook: table of contents (draft 2026-10-26)

For `frontend/docs/playbook.md`, about two to three pages. Methods for directing AI builders, drawn
from area D's scan with the exemplars area A, B and C found, and the owner's recorded working rules
(`playbook_working_rules.md`) placed under the method each belongs to. Each section in the written
playbook will give: when to use it, the steps, the exemplar sections, the one rule it taught.

**Preface, two lines.** The owner ruled and AI agents built, to specs the owner wrote or co-wrote;
the design benches and generated masters live in `frontend/claude_artifacts/`, outside git, so every
exemplar is a document in the repo. Delegation rule (owner 2026-07-14 and 2026-10-10): self-contained,
well-specified work goes to Opus agents; rulings, design mapping and claim wording stay in the main
session.

1. **Mock to spec to code to golden.** Benches per scene, a handoff that separates what was decided
   from how, the codebase's own "how" document that wins over the handoff and lists departures, a
   beat table mirrored by one function and pinned by goldens on a real game, the work ordered with a
   "who" per step, the old version tagged before deletion. Exemplars: `HANDOFF.md` §1, §4, §9, §11;
   `stage_architecture.md` §1, §2, §9, §11; `beat_sheet.md` head and §0. Rule: change the table, change
   the code, regenerate the golden, in that order. Folds in *the handoff between sessions* (settle the
   decisions that are expensive to retrofit before assembly; give the next session one link it can keep
   editing). Gap to fix while writing: `stage_architecture.md` §9's departure list stopped early.

2. **The asset brief, for image and audio generation.** Rulings first; the house style read off the
   approved pieces (for audio, measured key, tempo, loudness); what the asset must never carry, with
   the reason (the costume rule: a puppet is every viewer's face for a seat, so a role prop would leak
   hidden information); shared blocks, a lineup sheet first, then one item per call with the previous
   approval attached; a spec that aims past the goal because the model under-delivers; negatives moved
   from the prompt to the gate because a named object gets summoned; a measured gate; batch the call,
   keep the single prompt for reruns; record the first generation's habits and forbid them; the shipping
   checklist. Exemplars: `cast_expansion_brief.md` (the template), `role_cards_brief.md` §0, §1, §5, §6,
   `night_rooms_brief.md` §3 to §5, `music_brief.md`. Working rules placed here: the costume rule
   (2026-09-28); a picture swap runs only the specs that show the picture (2026-10-18). Rule: each step
   attaches the last approved picture, never the original anchor.

3. **Mock-against-repo review.** Read-only; every field a mock reads or sends classed as ours,
   derivable or missing; conflicts with the rulings and the code, each with evidence; the brief item by
   item; a build order with size and who; the questions only the owner can answer; the rulings recorded
   with dated amendments in place. Exemplar: `design_2026-09-26/pages_review.md` §A to §F. Rule: check
   every claim a mock makes against the code before building it.

4. **Measured performance work: audit, census, one batch, a gate.** Audit on a frozen snapshot stating
   what the host cannot show; state the rule; probes that remove one kind of work each; census every
   instance; fix the whole list in one batch; make the rule a test; measure before and after the same
   way, one script, one build, one sitting; list the knobs not yet turned. Exemplars:
   `rendering-audit-2026-10-02.md` "Scope"; `stage_architecture.md` §6; `build_log.md` §8.7, §8.9;
   `frontend-audit-2026-10-11.md` follow-up; `e2e/phone-rule.spec.ts`. Working rule placed here: sweep,
   not whack-a-mole (owner 2026-10-15). Sibling step from the server: measure before pinning a number
   (`seat_continuity.md` §4, the 30 s grace measured through the real proxy chain). Rule: when the fourth
   fix of one rule follows the fourth crash, the rule becomes a test.

5. **Decision by a mock with a switch per change.** List the candidate changes; one mock with a toggle
   per change; the owner rules switch by switch; write the rule as a test a builder can apply; record
   what was retired and why; build steps with their done date. Exemplars: `typography.md`; the logo in
   `pages_review.md` F2; the benches' control strips. Rule: give the builder a test, not a list ("would
   this sentence make sense if the train were real?").

6. **The rulings convention.** "Rulings (owner, date)" first, numbered; proposals below, marked;
   amendments in place, dated, with what they replaced; the old value kept beside the new; "Open for the
   owner" at the foot, closed in place; the owner adjusts against the running app, not the mock; **the
   status line is updated in the commit that ships** (three briefs rotted: role cards and night rooms
   say DRAFT after shipping, typography says not deployed). Exemplars: `role_cards_brief.md` §0, §7;
   `pages_review.md` §F; `stage_architecture.md` §1, §12; `beat_sheet.md` §0's dated holds;
   `build_plan.md` §1; `ten_seat_pass.md` §1. Rule: a superseded value stays on the page beside its
   replacement, with both dates.

7. **Give the builder eyes: the workbench.** One route mounts the real components on a fixture game;
   the URL holds the whole state; captions and the beat stepper come from the same table as the player;
   phone frames on a desktop; Playwright takes a screenshot per named URL; acceptance written as
   workbench views plus a named test. Exemplars: `stage_architecture.md` §1 ruling 1, §7, §12;
   `BUNDLE_README.md`; `opening_round_brief.md` "Acceptance". Working rules placed here: every visual
   change comes with a before-and-after picture, cropped to the change (2026-10-18); lean briefs for
   visual tasks: affected specs while adjusting, one full run at the end, one sheet per changed state,
   name the sections to read (2026-09-28). Rule: if a view cannot be named in a URL, an agent cannot
   check it.

8. **The read-only audit on a frozen snapshot, and how to read one.** Copy the tree, build it on its
   own port, change nothing; scope the threat in one sentence; every main claim checked in the code;
   each fix as found, why it was like that, the fix, how it is now, with commit and test; an "accepted
   or left" table carrying the owner's decision; say what was not run. Then, as the receiver: read the
   audit as a list of claims to measure, not a to-do list; survey it against the code days later.
   Exemplars: `multiplayer-audit-2026-10-15.md`; both frontend audits' "Scope" sections and the
   2026-10-15 follow-up; `build_log.md` §8.9 "a second pass from the readings"; lesson 19. Rule: say what
   was not run.

9. **Coupling alarms when the engine changes.** Name each copied fact; give it one place and an alarm
   (an exhaustiveness test or a runtime error on the first undeclared field); keep a table of change,
   update, caught by; regenerate a golden only for a deliberate wire change and review its diff.
   Exemplars: `server/README.md` "When the engine changes"; `server_client_transport.md` §8, §10;
   `tests/server/test_engine_sync.py`, `test_openapi_snapshot.py`. Rule: cross-boundary couplings are
   allowed; silent ones are not.

10. **Re-owning code you did not write: the code walk and the challenge record.** Read one module a day
    after it is written; ask which module owns a lifecycle, or what a table's invariant is; record the
    answer as a dated ruling with rejected alternatives; delete the backstop that would hide a broken
    invariant. When something breaks, write it to be read cold: the story with the wrong first diagnosis
    kept, the decisive evidence, the fix with its pinning test, "what to know". And record the general
    lesson the day it is learned, in the lesson log, in one shape. Exemplars: `server_design_notes.md`
    §4, §10 to §12; `server_encountered_challenges.md` §2; `frontend_lessons.md` head. Working rule
    placed here: general lessons are recorded as they happen (2026-10-02). Rule: naming a layer does not
    make anyone ask what it guarantees.

11. **Build, test and deploy in a tree other sessions share.** Test one change from a scratch copy of
    HEAD plus your hunks, on the reserved port, after confirming whose server answers; regenerate every
    golden and keep only the explained ones; stop the server when the batch lands. Deploy from a clean
    detached worktree, migration first from inside the new image, pre-flight, no rooms or games running,
    swap with the old images kept as `:prev`, run the smoke list, record what was not run. Exemplars:
    `testing.md` "How a run is done here"; `build_plan.md` deploy entries `a651988` and `344b9e58` (to
    become `deploy_log.md`). Working rules placed here: known ports only, start the Playwright server per
    batch and kill it by pid, no production build while other sessions are busy, never kill another
    session's process without the owner (2026-09-27 to 2026-10-15). Rule: a build is of a commit, never
    of the working tree; a run against someone else's build proves nothing.

12. **An independent cross-layer review before calling a build done.** Hand the finished build to a
    reviewer that did not write it; ask for defects that cross layers (server ordering against client
    dedupe, fold against render, what the server delivers against what the UI shows); write an
    exact-order regression for each. Exemplar: `build_log.md` §3.8 to §3.12 and §6's last row. Rule:
    event identity and event recency are different facts, and only a reader of both sides found that.

13. **Public copy that must stay true.** Each claim names the code it rests on; an exhibit is captured
    from a real run through the function the server calls; the wording is chosen to survive a change
    already expected; a benefit claim matches the research verdict; where site numbers restate eval
    numbers, a parity test ties them. Exemplars: `pages_review.md` B12, B14, F9; `landing_features.md`
    "Why this wording", "The drafted line is real"; `scorecards_plan.md` "One ruler" (planned). Rule:
    copy describes the mechanism, never a benefit the evidence does not show.

**Placed in the preface, not a section:** the delegation rule; library overrides go through the
library's own API (owner 2026-10-01), which is a code rule rather than a method and belongs in
`frontend/README.md`'s conventions if it is not there already.

**Considered and not added:** the feature-plan form (`scorecards_plan.md`, appears once, unbuilt); the
"who" column as a method of its own (it is a step inside 1 and 3).
