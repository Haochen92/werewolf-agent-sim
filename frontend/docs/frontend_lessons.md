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

---

## Small things that cost an afternoon

- `pgrep -f pattern` matches the shell that is running the loop containing the pattern, so a
  "wait until it finishes" loop never ends. Use `grep -c '[p]attern'`.
- A percentage move (`y: '115%'`) is relative to the moving element; shrink the element and the
  move shrinks with it. Give moves in your own units.
- Safari's timeline: a blue Composite record means the layer tree was rebuilt (a keyed-whole
  remount); the orange band is memory, not CPU; its charts interpolate sparse samples.
- A dev server's numbers are not a production build's; compare production against production
  (the preview on 3118 is a production build of the working tree).
