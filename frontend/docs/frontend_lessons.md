# What the stage taught us about frontend work in general

Written for: the owner, to re-own and re-explain, and to carry to the next project. The phone
story is told in `phone_lessons.md` (what iOS Safari did and why); this is the part of it that
is not about phones at all: React, rendering, and how to work on a performance problem. Each
entry is the mistake we made or nearly made, the rule we keep now, and where to see it in this
repo. The dated numbers are in `build_log.md` §8.

The one sentence version: **the cost of a frontend is not the size of its JSX but what the
browser has to redo when something changes: which subtrees React rebuilds, which rectangles get
repainted, which layers get held, and how often any of it happens.**

---

## React: identity and re-rendering

**1. A key is an identity, not a reset button.** We keyed each scene on its beat so a new beat
would "start fresh", and so every beat threw away and rebuilt the whole scene: set, lights,
wing, figures (385 of 388 elements replaced for one more chip counted). The rule: key the
smallest thing that must restart, and reset the rest with state that follows a prop (`useState`
seeded from it, an effect on `beat.seq`). See `scenes/LynchScene.tsx` (`told` reset on the
beat), `scenes/VoteScene.tsx` (`BallotLine key={counted}`), and §8.3, §8.9.

**2. Separate what persists from what changes, then put the persistent part in one place.**
Eight scenes shared one set (the dining car) but each rendered its own copy, so a change of
scene was a change of everything. Now one host owns the set and each scene *describes* its set
to the host (`scenes/CarScene.tsx`: a body renders `<CarSetSpec …/>`, the host draws it). The
general shape: a stable parent, children that register a description, the parent rendering from
the description. See §8.9 and `stage_architecture.md` §6.

**3. When you render from a description, render from the description's own props.** The host
once drew the set from the *latest* props under the *previous* scene's description, for one
commit; that transient told the wing a seat had died and closed the live notes editor. A
description and the props it was made with travel together (`Described {spec, props}`). The
general rule: never mix state from two different moments in one render.

**4. Memoise what registers, or it loops.** A child that registers itself in a layout effect
re-registers on every render; if registering re-renders the parent, you have a loop. The bodies
are `memo`ised, and their registration runs only when its inputs change.

**5. A ticking state at the root re-renders the whole tree.** A 250 ms countdown interval set
state in the live theatre, so the theatre and every scene body under it re-rendered four times
a second during a live turn, while figures were animating. Ticking state belongs in the leaf
that shows it (`instruments/CountText.tsx`); the root hears only the one event it acts on
(expiry). The same goes for typed text: a composer's keystrokes must not reach the scenery.

**6. New objects every render defeat memo.** A `memo`ised child still re-renders if its parent
hands it a fresh object or callback each time (`turnInput`, `onCard`). `useMemo`/`useCallback`
are not optimisation garnish here; they are what makes the memo true.

**7. Effects without dependencies run every render.** The stand's `useLayoutEffect` recreated
two ResizeObservers and measured the plate on every render of every beat. Give effects their
dependencies, and observe the element whose size you actually depend on.

---

## Rendering: paint rectangles and layers

**8. The browser repaints the moving box, not the thing in it.** A figure is placed in stage
coordinates, so the easy wrapper to move it with was a full-stage `position: absolute; inset:
0` box; every frame of that move repainted 1600 × 900 and everything under it. A mover's box
must be its load's bounds (`instruments/Bounded.tsx`: bounds plus a pad, clipped, with the
coordinates put back inside). See §8.10.

**9. Animate transforms and opacity, never layout or SVG attributes.** The same slide was
smooth as a CSS `transform` on a box and a stutter as an SVG `transform` attribute on a group
inside a full-stage drawing (the drawing is re-laid-out every frame). See §8.4 and
`phone_lessons.md` lesson 6.

**10. Any animated property makes a compositor layer, and a layer is a bitmap.** Opacity too.
A layer costs its area × 4 bytes × device scale, for as long as the animation runs, and
everything painted *above* it in stacking order is lifted onto layers with it (the cascade).
A looping idle animation at rest holds that forever. Rules: nothing animates at rest; what
moves does so for a beat and stops; measure the Layers panel, not your intuition. See §8.1,
§8.6.

**11. Blend modes and filters are paid on every repaint of their rectangle.** Two
`mix-blend-mode: screen` sheets the size of the stage, a `grayscale` filter on each dead tile,
a sub-pixel grain tile over everything: each was a pass over the whole repaint rectangle under
any mover. Box them to what they affect, bake them where they do not change, and turn off what
the eye cannot see on a small screen. See §8.9.

**12. Generated markup from pure inputs is cacheable, and a cache keyed by instance misses.**
Tracing the light's holes cost 60–110 ms per distinct configuration; a bounded FIFO keyed by
the generator's inputs makes a repeat free. Keying it by a component instance id would make a
remount a miss for the same geometry.

**13. Pictures cost by decoded pixels, not file size, and the decode is on the main thread
at first paint.** Pick the asset by displayed size × device pixel ratio; keep separate copies
for the sizes you actually show; decode the next thing you will show a step ahead
(`cast/DecodeAhead.tsx`). A fresh `<img>` is black for a frame on iOS: reuse the element,
change its source. See §8.8, §8.9.

**14. A steady low frame rate reads better than an uneven high one.** When a frame's paint
does not fit 16 ms, the frames drop unevenly and that unevenness is the stutter. Sampling the
same easing at 24 steps a second (`motion.tsx` `stepped`) gives each frame 42 ms and a steady
beat. This is a presentation choice, not a fix for the paint cost, and it is honest to say so.

---

## Method: how to work on a performance problem

**15. Subtract before you add.** The fastest way to know what something costs is to remove
it and measure again: hide the light layer, hide the grade, hide the grain, each under the
same trace. The numbers decide the order of work (`gpu=` switches on the workbench, §8.9).

**16. Census, then one batch, then a gate.** For a bug class on a platform you cannot run,
enumerate every instance of the pattern first (every `inset: 0` mover, every animation at
rest, every oversized picture), fix the whole list in one pass, and write a test that fails
the class (`e2e/phone-rule.spec.ts`). One fix per crash report is whack-a-mole, and each
deploy costs the person testing on the device. (The owner's rule, 2026-10-02.)

**17. Measure the attractive answer before taking it.** "Put the movers on the GPU" was the
obvious route; measured on the phone it lifted every layer above each mover, 670 MB, and
killed the tab. The measurement took ten minutes; the rewrite it prevented would have taken a
day and shipped a crash.

**18. A gate that reads state at the end of a window misses what happened inside it.** The
first phone rule checked which animations were *still running* at the window's end and so
passed a 600 ms full-stage fade. Sample through the window. The same shape of mistake lives in
any test that asserts a final state and calls the path verified.

**19. Read someone else's audit as a list of claims to measure, not a to-do list.** The other
agent's audit was right on substance (rebuilt subtrees, full-stage movers, the ticking root)
and we took those; its proposed order and its GPU hope were checked against our numbers
first. Likewise an owner's report ("day 4 feels heavier") is a claim to measure: the walk
found no per-beat growth and no memory growth, which pointed at the phone, not the page.

**20. Tests that pass alone and fail in parallel are waiting on time, not on state.** Wait
for the attribute or element the next assertion needs; never for a duration. A settle helper
that waited on every lazy image hung once a drawer stayed mounted off-screen: wait only for
what is in the window.

**21. A viewer's override carries the moment it was made in, so it lapses without an effect.**
The Record opens on the latest morning, and the viewer may turn back a page; when a new
morning arrives (or the replay steps back past it) the pick should give way. Resetting it with an
effect on "a new morning" renders the stale page once and races the stage. Instead the pick is
stored as `{morning, latest}`: it holds only while `latest` is still the latest, and is computed
away otherwise (`film/record-model.ts` `shownMorning`; the seat chooser's `{seat, key}` in
`case-file.ts` `shownSeat` is the same shape). Derive "does the override still apply" in render;
never schedule its expiry.

**22. Choose a picture's size from the pixels it is drawn at, and choose it once.** The
backdrop's sheet was picked by the screen's density alone, so the landing's 334 px preview on
a phone took the same 3300 px sheet as a full theatre (17 MB decoded where 7.6 MB covered it),
and it was picked in an effect after a 1× default, so Chromium fetched both. Now the stage's
measured width × density × the camera's closest zoom picks the sheet, in render, and nothing
is drawn until the width is known; a resize trades down only past a margin. Layout ("is it
small?") and density are separate questions: a small stage on a dense screen still needs
pixels. See `instruments/Backdrop.tsx` `pickScale`, audit 2026-10-11 §1.

**23. A deferred component is deferred only if its mount, its data and its pictures all
wait.** `next/dynamic` moves the code out of the first load, but a dynamic component rendered
at once still loads at once, and a query enabled at once still fetches. The landing's preview
now holds its frame (and the marquee's and the controls' room, so nothing shifts) and starts
the chunk, the replay and the sheet together when the carriage is near (`FeaturedReplay.tsx`
`useNear`). Assert it the way it fails: count the requests before the scroll, not the DOM
after it (`e2e/site.spec.ts`, "loads when scrolled to").

**24. When a derived list folds items together, whatever holds a place in it needs a rule for
the item it holds being folded.** The beat list is cut afresh from the log on every event, and
since 2026-10-12 a run of passes is one beat: a pass on the stage can grow into a run, and a
turn on the stage can be swallowed by one. Carried across by "the same item, else the next one
at or after it", the stage would have skipped the run it was inside, or landed on it still and
moved on at once. The rule: decide, for each kind of merge, where the cursor goes and whether it plays
again (`live-state.ts` `runOf`), and test it with the list growing one event at a time. Its
twin in tests: anything that names an item by its index (a workbench `?beat=N`, a seek to beat
50) moves when the derivation changes; name it by what it is where the tool allows.

**25. A census compares two builds under one script, in one sitting, with nothing animating.**
The landing's rooms (2026-10-14) first measured "+100 ms on a phone, nothing on a desktop"; a
later script, scrolling the same rooms, found +440 / +1560 ms for the same commit. Neither
number means anything beside the other. Two things moved them: the scroll path, and the
latest games' loading shimmer (`background-position`, so a repaint every frame), which with
no API answering kept re-rastering the room's wall under it, about half the "cost" of the
wall. So: build the baseline (HEAD) and the change, run the same script against both, keep
animations still (`reducedMotion: 'reduce'`, or answer the data), and report the difference
of differences. And stop a painted wall where its light runs out: past the lamp's reach the
page's own ground is the same colour and costs nothing (`Rooms.module.css`, the capped walls).

**26. A filter is drawn on the CPU over its whole box, every time the box is drawn: its cost is
area × count × how often.** The guide's role cards carried ten `#inkwobble` filters each (noise
displacing the ink) and a `drop-shadow` on the figure. Harmless at 270 px wide; once the cards
grew to 417 px (2026-10-15) the carousel stuttered: 18 fps scrolling the rows and 12 fps turning
one, at 4× CPU throttle. Clean ink and a painted shadow (a radial gradient under the figure,
`RoleCard.module.css` `.portrait::before`) gave 42 and 48. Keep texture filters to a few small,
still things (the slates), and measure a filtered element again whenever it grows. Relates to 11.

**27. Deferring a mount is safe only where its box already has its final size.** The guide's
eleven demo stages were all built on load and kept a phone-speed CPU busy for about 9 s after
it, so whatever the reader scrolled to stuttered. Mounting them near the view
(`guide/useNear.ts`) was right for the day line, whose slot is a fixed height, and wrong for the
tools and the case file, which grew 50–430 px when their demos arrived: a section growing a
screen away is invisible while scrolling, but it moves an anchor jump's target in mid-flight.
The test that caught it measures a section, then clicks its tabs (`e2e/site.spec.ts`, "no tab set
moves the page"). Reserve the box, or mount at load. Relates to 23.

**28. Find out what the main thread is doing before blaming the paint.** The first throttled
run said the cards were slow with or without their filters. A trace showed size observers and
layout, not painting, and wrapping `ResizeObserver` to log its targets named the demo stages,
not the cards. Three checks: count the work with nothing moving, in 3 s windows until it reaches
zero (a page still settling, not a loop); measure the thing only once the page has settled; and
on a shared machine interleave old and new runs and take the median of three (single runs here
swung from 15 to 45 fps with the machine's load). Relates to 25.

---

## Small things that cost an afternoon

- Two rules for one class name in a CSS module are one class: a `.head` for a page's header and a
  `.head` for a 2px playhead further down the same file merged, and the header became a 2px
  absolute strip. Name each part for what it is (`.playhead`).
- A browser starts sound only after the viewer has pressed something on the page; Safari only
  inside the press's own handler. Make or resume the `AudioContext` in a press listener, not in
  an effect that runs after it (`src/music/music.ts`). Fade with gain nodes: an iPhone ignores
  an audio element's `volume`.

- `--update-snapshots` rewrites only the goldens that fail, and a golden fails only past its
  tolerance (`maxDiffPixelRatio` 0.005 here), so a deliberate change to a few lines of text (a
  colour, a size) passes against the old golden and is never written: the golden keeps the old
  look. After a deliberate change run `--update-snapshots=all` on the build that has it, then put
  back every golden whose pixels did not really move (a page you did not touch re-renders with
  sub-pixel noise), comparing each against HEAD.
- A production build prefetches every `<Link>` that scrolls into view (the dev server does not),
  as a `fetch` with an `rsc: 1` header to the page's own path. A test counting requests by path
  (`/replays/<id>`) counts the prefetch too and fails on production only; filter on the header.
  For a dynamic route with a `loading.tsx` the prefetch is only the page's shell, no data.
- A wall capped short of its box ends in an edge if any layer over it is darker than the page's
  ground (a black vignette is): the page's own colour below the cap shows lighter. Fade the foot
  to the ground as the topmost layer (`StationWall.module.css`, `Rooms.module.css`).
- An absolutely placed wall taller than a short page lengthens the page past its footer. Place it
  against a positioned wrapper with `overflow: clip` (the site layout's `.station`): clip cuts it
  at the page's foot and, unlike `hidden`, makes no scroll box, so sticky menus still stick.
- `pgrep -f pattern` matches the shell that is running the loop containing the pattern, so a
  "wait until it finishes" loop never ends. Use `grep -c '[p]attern'`.
- A percentage move (`y: '115%'`) is relative to the moving element; shrink the element and the
  move shrinks with it. Give moves in your own units.
- Safari's timeline: a blue Composite record means the layer tree was rebuilt (a keyed-whole
  remount); the orange band is memory, not CPU; its charts interpolate sparse samples.
- A dev server's numbers are not a production build's; compare production against production
  (the preview on 3118 is a production build of the working tree).
- A `z-index: -1` backdrop vanishes when both `html` and `body` set a background: `body` is an
  in-flow block, and its background paints over negative-z children of the root context. Make the
  backdrop's own section a stacking context (`isolation: isolate`) instead.
- `overflow-x: clip` on `html` keeps a desktop from scrolling sideways, but `scrollWidth` still
  counts the overflow and an iPad can still pan to it. Clip the wide element itself.
- A rounded `overflow: hidden` round an animating layer costs a mask the size of the clip. Clip
  moving content with a plain rectangle and draw the rounded corner on the frame around it.
- Headless Chromium here reports no `LayerTree` events, headed under Xvfb included. Read layer
  memory on a device (Safari's Layers tab); headless can still count paints and raster time
  from a trace (`browser.startTracing`), though `Paint` clip areas are layer-space and do not sum.
- `next dev` drops a `next/dynamic` chunk's stylesheet on a hot reload and never loads it back
  (2026-10: the landing's lazily loaded theatre lost its styles when a stage file was saved). The
  stage then draws unclipped at full size, with no HUD, which looks like a framing bug. A
  production build keeps every sheet. Hard-reload before you chase it.
- A Playwright run proves nothing until you know whose server answered on its port: another
  session's build held 3121 (2026-10-15), mine failed to start, and the suite ran against theirs.
  Check the port's process first (`ss -ltnp`, then `readlink /proc/<pid>/cwd`).
