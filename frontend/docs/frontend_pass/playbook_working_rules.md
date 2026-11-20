# Working rules recorded during the frontend build (for the playbook)

Drafted 2026-10-26 from the session memories, to be merged into `frontend/docs/playbook.md` once
area D's table of contents is in. Each rule is dated to the day the owner ruled it, carries its
reason, and names the document that shows it in use. The owner reads this once and strikes any rule
no longer held; a memory records one day's ruling, not a standing law.

## Briefing an agent for a visual task (owner, 2026-09-28)

**The rule.** Keep the task narrow. Run only the affected specs while adjusting and ONE full
end-to-end run at the end (two only before a deploy). One screenshot sheet per changed state, not
every role times every screen. Name the sections of a doc to read instead of "read fully".

**Why.** The owner iterates visually and waits on each pass. Measured on 2026-09-28: the build
compiles in about 10 s and a full Playwright run takes about 3 min, so an hour-long task was the
look-adjust loop (150 to 200 tool calls), a doubled end-to-end run, too many sheets, and agents
reading `stage_architecture.md` whole. A tightly scoped follow-up took 9 min and 18 calls.

**Seen in.** The briefs in `role_cards_brief.md` §6 and `night_rooms_brief.md` §5 ("shipping a
figure", "shipping a room"), which list the specs and sheets a change needs.

## Every visual change comes with a before-and-after picture (owner, 2026-10-18)

**The rule.** When a step changes what is on screen, the agent takes the screenshots, crops to what
changed, and shows the owner before asking to commit. A step with no visual change needs none.

**Why.** The owner judges looks from the pictures, not from a description or a passing test.

**Seen in.** The goldens: the golden from HEAD against the new shot is the before-and-after.

## A class of bug on a platform you cannot run: census, one batch, a gate (owner, 2026-10-15)

**The rule.** When one principle is violated in many places (nothing animates at rest inside the
stage; nothing full-stage repaints per frame), build the sweep first (a check over every scene and
beat in the phone frame for animations at rest, `will-change`, filters, masks, blends, large
movers during arrivals), fix the whole list in one batch, and keep the gate running with the
goldens. Never deploy a single-instance fix and ask the owner to retest.

**Why.** Four deploy rounds for iPhone crashes each fixed the one instance the latest crash exposed
("I feel like we are doing whack a mole right now"). The owner tests on a real phone by hand, so
each round cost a session.

**Seen in.** `build_log.md` §8.3 to §8.7, `frontend_lessons.md` lesson 16, `e2e/phone-rule.spec.ts`.

## A picture swap runs only the specs that show the picture (owner, 2026-10-18)

**The rule.** A new raster for an existing prop or set runs only the specs whose screenshots show
it: redraw those goldens, look at each by eye, build and deploy. The full end-to-end run (about
15 min) is for changes to code beyond the picture's own measured numbers. Re-measured CSS numbers
for the picture still count as a swap. Tall goldens may fall under the diff threshold and need
`--update-snapshots=all` forced for that test.

**Why.** The owner asked why a straightforward replacement needed the whole golden and test cycle;
the full suite mostly checks things a swap cannot touch.

**Seen in.** The landing carriage and the station train swaps (the specs are named in the memory
and in `site_architecture.md` "Tests").

## No costume may hint at a role (owner, 2026-09-28)

**The rule.** Characters are dealt to seats at random, independent of roles, so a doctor would read
as the healer and a detective as the investigator. Costumes come from 1920s train and travel life.
Also rejected: role-coded props (magnifying glass, medical items, weapons, badges, masks, pelts,
lanterns), numerals (they compete with seat numbers), dominant wolf red, killer violet or X-ray
cyan, uneven expressions (everyone equally guarded).

**Why.** The art must never leak or fake role information; players should read the talk, not the
costume.

**Seen in.** `cast_expansion_brief.md` (the template and the rounds), `role_cards_brief.md` §1.

## Library overrides go through the library's own API (owner, 2026-10-01)

**The rule.** Change a Mantine default through `styles`, `classNames`, `vars` or a theme override,
never by a higher-specificity selector in a CSS module. CSS-module rules are for the project's own
elements. Verify layout at the real container widths (the rail is 272 px; cards about 340 px at
two-up), not one desktop viewport.

**Why.** The owner claims frontend and library competence in applications, so agent-written
frontend code must read as if someone who knows the library wrote it. The first fix for a double
scrollbar was a specificity trick; the owner asked for the idiomatic version.

## General lessons are recorded as they happen (owner, 2026-10-02)

**The rule.** When a batch teaches something general (not stage- or iOS-specific), add a numbered
entry to `frontend_lessons.md` in the same shape: the mistake, the rule, where to see it. The dated
numbers stay in `build_log.md`; the phone-specific story stays in `phone_lessons.md`.

**Why.** The owner is re-owning agent-written code; general lessons are interview material and
carry to the next project, and the phone doc alone buries them.

## Servers and builds on a shared box (owner, 2026-09-27 and 2026-10-15)

**The rule.** No new localhost servers. Known ports only: the owner's dev server, one theatre
build, one site build, one Playwright server started per batch and killed by pid when the batch
lands (a second Playwright port is allowed only when the first is taken and memory allows). Before
a Playwright run, check which process owns the port and whose build it is; a suite that passes
against someone else's build proves nothing. No production build while other sessions are busy
without asking; check free memory first. Killing another session's process needs the owner's OK.

**Why.** Stray servers from A/B builds piled up; a dev server left running grew to several GB and
the kernel's OOM killer took out a probe; two back-to-back builds while other sessions ran suites
crashed the owner's server.

## Experiments on the cheap model, A/Bs with a cost quoted first (owner, standing)

Not a frontend rule, recorded here because frontend briefs sometimes propose model runs: paired
A/Bs run on the cheap Claude model, the cost is quoted before the run, and Sonnet is never a
player model.
