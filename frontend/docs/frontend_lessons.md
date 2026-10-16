# What the stage taught us about frontend work in general

Written for: the owner, to re-own and re-explain, and to carry to the next project. The phone
story is told in `phone_lessons.md` (what iOS Safari did and why); this is the part of it that
is not about phones at all: React, rendering, and how to work on a performance problem. Each
entry is the mistake we made or nearly made, the rule we keep now, and where to see it in this
repo. The dated numbers are in `build_log.md` §8.

The one sentence version: **the cost of a frontend is not the size of its JSX but what the
browser has to redo when something changes: which subtrees React rebuilds, which rectangles get
repainted, which layers get held, and how often any of it happens.**

## Two mechanisms the lessons lean on

**Re-render and remount are different things.** A *re-render* is React running a component
again and comparing what it returns with last time. It then changes the existing page elements
in place: the same `<img>` stays, with a new `src` if that changed. A *remount* throws the
element away and makes a new one. It happens when the element's `key` changes, or when its
place in the tree changes (a different parent, or a different component at that spot). On an
iPhone a brand-new `<img>` paints nothing until its picture is decoded, so a remount shows a
blank frame even for a picture already downloaded; a re-render does not. `memo` and `useMemo`
only skip re-renders, to save CPU: a memoised component inside a subtree whose key changes is
remounted all the same. So "the picture flashes" asks *what remounted it* (lessons 1, 2, 13),
and "the page is slow to respond" asks *what re-renders too often* (4 to 6).

**A frame is drawn in three steps, and only the last is cheap.** *Layout* works out where every
box goes. *Paint and raster* turn the boxes into bitmaps of pixels; for a large picture on a
phone's 3× screen that is a lot of pixels. *Composite* has the GPU stack those bitmaps on the
screen at their positions. A *layer* is one of those bitmaps. An element on a layer of its own
can be moved or faded by the compositor alone, every frame, without painting it again; an
element painted into a bigger layer has to be painted and rastered again whenever it moves. The
browser gives an element its own layer for a CSS or Web Animations animation of its transform
or opacity, and when told in advance (`will-change: transform`), but not for a style a script
writes each frame. The price of a layer is its bitmap, held in memory for as long as it lasts.
So a mover gets a layer while it moves and gives it up when it stops (lessons 8 to 10, 40).

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

**10. An animated property makes a compositor layer, and a layer is a bitmap.** Opacity too,
for a CSS or Web Animations animation; a style a script writes each frame gets no layer unless
it is asked for (`will-change`, lesson 40, found 2026-10-15).
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
`useNear`); the chunk only since 2026-10-15, see 29. Assert it the way it fails: count the requests before the scroll, not the DOM
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

**29. A baked copy of something computed must cover everything the computation reads, or be
tested against the live result.** The car's backdrop is baked (`scripts/bake-sets.mjs`) at two
layouts, while the shutter over its window is placed live from the layout's geometry. The
no-HUD layout got no sheets and reused the live HUD's, on a comment that the two were alike.
They had differed since the seat rail took 192 units (2026-09-29), so on the one screen that
used no HUD, the landing's carriage on an upright phone (from 2026-10-14), the shutter fell 96
units short of the window. One invariant now holds them: for every layout, the glass's centre
is the shutter's (`instruments/backdrop.test.ts`, `sheetFor`). When a shortcut maps one case
onto another, write the test that says they agree, not a comment.

**29. A dynamic component's code starts loading at its first render, not when you decide you
want it.** The carriage was meant to start its code, its replay and its pictures together
(23), but it rendered `ReplayTheatre` only once the replay had arrived, so the three ran one
after another. On a throttled phone (1.6 Mbps, 150 ms, 4× CPU, live site, 2026-10-15), after
the scroll: the replay JSON 0.1–1.3 s, the theatre's code 1.5–2.2 s, the stage's pictures
3.4–9.1 s, the stage painted at about 6 s. A desktop on a fast line ran the same chain in 2 s,
which is why nobody saw it. The fix is to call the same `import()` the `dynamic()` uses in the
effect that enables the query (`FeaturedReplay.tsx` `theatreCode`): the code request now
starts 7 ms after the replay's. To find this kind of chain, list each request's start time
after the trigger: a request that starts only when another one finishes is waiting on it.

**30. A size measured after mount is a guess on the first render, and the guess fetches.**
The stage learns it is phone-small (`SmallContext`) in a layout effect, and it started as
`false`. Its scenes rendered once as a desktop's before the re-render, and that was enough
for the puppet's `priority` image and `DecodeAhead`'s `new Image()` to ask for the full-size
poses. Every phone fetched both sizes: in the carriage's first window, the full
`talking.webp` and `thinking.webp` (235 KB) beside their `@small` copies. Lesson 22 had fixed
this for the backdrop alone. Now the Stage renders its scene only once it has measured itself
(`Stage.tsx` `measured`), still before the first paint, so every stage gets the fix: live,
replay, the guide's demos, the carriage, the workbench. The general rule: a value that picks
which file to fetch must be known before the first render that uses it, or that render
waits for it.

**31. A response header set for one route travels with every response in its block.**
`Cache-Control: no-transform` tells any middleman, Cloudflare here, to deliver a response
exactly as sent, and that includes not compressing it. It was added to wolf's `/api` to fix
the live game's event stream, which through Cloudflare was held so long that not even the
headers arrived within 25 s. Because it was set on the whole `/api` block in the Caddyfile,
every JSON response lost compression too: the replay went out at 142 KB where gzip makes
21 KB. Since 2026-10-15 the header is on the stream's route only
(`/api/games/{id}/events`), and the rest of `/api` is compressed.

*Why compression and streams are kept apart.* A compressor needs a run of text to work
well. A JSON body arrives whole, so it is compressed in one go. A stream arrives a few bytes
at a time, with gaps between, and a middleman that wants a bigger chunk to compress, or to
send, may hold the small pieces until more come. A held event is a frozen-looking stream.
Wolf's stream is the worst case for that: it sends nothing until the first game event, then
irregular gaps. Dota2pred's stream, behind the same Cloudflare without `no-transform`, sends
`: connected` at once and a heartbeat every 30 s of quiet, and it flows; Cloudflare did not
compress it at all (no `Content-Encoding`). So the exact mechanism behind wolf's old hold is
a guess. `no-transform` stays on the stream because its events are tiny, compressing them
would save almost nothing, and a stream that seems frozen is the failure already seen once.
To test whether it is still needed, send an opening comment and heartbeats, as dota does,
then try the stream without the header.

**The carriage case, 2026-10-15** (29–31): the cause was mostly not the size of the event
log. Of about 6 s to a painted stage on the throttled phone, the replay JSON was 1.2 s. The
rest was the chain (29), 1.2 MB of pictures, 235 KB of them fetched twice (30), and nothing
compressed (31). Steps:
- Commit `a4411355`: the code is requested beside the replay.
- Commit `fec8cf40`: the stage measures before it draws.
- Caddy, live 2026-10-15: the replay is 20.9 KB on the wire instead of 142 KB. The previous
  Caddyfile is kept beside it as `Caddyfile.bak.20261015-113614`.

Deployed 2026-10-15 at `323e853e`. The same throttled phone (iPhone 13 profile, cache off, the
carriage scrolled to after the landing has loaded), three runs: the replay is 20.9 KB and in by
1.0–1.1 s; the code starts beside it (the same millisecond) and is in by 1.7–3.4 s, when the first
beat is on the stage; no full-size `talking`/`thinking` is fetched. The first window's pictures,
ten files and about 850 KB, start with the stage and are in by 6.4–8.5 s. That is now the cost
that is left: 850 KB at 1.6 Mbps is over 4 s of transfer alone, and they cannot start before the
stage that names them has mounted.

**32. History replayed down a live socket arrives one message at a time, and each message is a
render.** The live stream sends the whole log before the news, one SSE message per event. Each
message is its own task, and a store read through `useSyncExternalStore` (zustand) renders at
the end of each, so the page rendered once per past event. Each render also re-sorted the log
and recut the beats over everything so far, so the work grew with the square of the game's
length. Now the frames that arrive together go to the store as one block
(`hooks/catch-up-boundary.ts` `catchUpBatch`), and news flushes the block first. On a 200-event
rejoin (dev build) the page rendered 7 times instead of 100, and landed in 2.5 s instead of
6.3 s. The general rule: when a stream carries a backlog, batch it before it reaches the store.

**33. A rule written down is kept only by a measurement.** Lessons 5 and 6 were already here, and
the live page still broke both. The composer's text lived in the live theatre's state, and the
props the theatre handed the scene were rebuilt on every render. So 41 typed letters drew the
dining car's set 82 times, 738 seat tiles and 1,394 transcript rows. The doubling came from
`CarSetSpec`, a child that re-registers its description after every render (lesson 4), which
renders the host a second time. The census that found this is a hook, not a profiler: a stand-in
`__REACT_DEVTOOLS_GLOBAL_HOOK__` installed before React loads (a page init script) counts the
fibers that did work in each commit, by component name. A fiber counts when it is not an object
seen in the previous commit and its `flags & 1` (PerformedWork) is set. It runs on a dev build,
where names survive. Fixes:
- The text moved into the dock (lesson 34).
- The props handed to the scene keep their identity (`useMemo`/`useCallback`: the dock, the turn,
  `onNext`, `wayOut`).
- The host, the set and the side slot are `memo`. The side slot is handed only the props it
  reads, not a spread.

After: the 41 letters render the dock and its composer, 41 times each, and nothing else.

**34. The state a hand types into lives in the leaf it is typed into.** The parent needs the line
twice, when it is sent and when a draft is put in. It reads the line as an argument of Send.
It puts a draft in as a prop, with a counter (`DockInput.landed`), because two drafts can be the
same string. The leaf takes the prop when it changes, by "adjusting state when a prop
changes", not by an effect. Key the leaf on the request (`key={beat.seq}`), so a new turn starts
empty. A controlled input is still right: an uncontrolled one would need the draft written
into the DOM by hand, and the word count, the preview and Send's state would stop updating.

**35. A cache derived from a growing log should grow with it, and what has not changed should
keep its identity.** The stage's folds (the game at each beat) were thrown away on every event
and rebuilt from the first event, so the view on the stage was a new object each time, and so
was every beat. Now:
- The cache takes the longer log when it only adds to the end (`fold-cache.ts` `grow`). The log
  is sorted and its event objects are never copied, so one comparison at the old end tells an
  append from an insertion.
- A recut keeps each beat that is equal to the old one at its place (`live-state.ts`
  `keepSame`).
- Both are bounded: 96 folds.

Downstream `memo` works only because of this.

**36. A cache meant to outlive an instance must not be keyed on the instance.** The paint cache
(`Stage.tsx` `drawn`) was keyed on `useId` plus the options. A part that mounted again got a new
id, missed the cache and traced the house light again, 60–110 ms on a phone, on the morning's
busiest beat. Now it draws under a stand-in id, keeps the drawing by the options alone, and
writes each instance's id in on the way out. A test checks that every generator's markup is the
same either way.

**37. Count decoded bytes, not file bytes.** A picture decodes to width × height × 4 bytes, a
sound to seconds × sample rate × channels × 4. The music's longest track is a 2 MB file and
about 33 MB decoded, and the player kept six such tracks for as long as the tab was open. Keep only
the few in play, and free decoded media when the last page that uses it is left
(`music/player.ts`). The same check sized the heads: a census of every head drawn found none
over about 234 physical px on a phone, so the phone's copy is 224 px (lesson 22).

**38. A deploy empties the CDN of every file it renamed, and the first visitor at each of its
locations pays for all of them.** Next names its code and pictures by their content
(`/_next/static/…/train@1x.b57accb5.webp`), so a build that changes a file gives it a new
name, and Cloudflare has never seen the new name. Cloudflare keeps a copy per location (a
`cf-ray` ending in `SIN` is Singapore), and only after someone there has asked for it once: the
first request is a `MISS` and goes all the way to the server; the ones after it are a `HIT`
from nearby, with an `age` header. Pages, `/api` and `/_next/image` are never kept at all
(`DYNAMIC`).

On 2026-10-15 the owner opened the site on a desktop for the first time after the 14:28
deploy. The landing's carriage stayed black for more than 10 s, and the guide took long. The
same pages on the phone a little later were quick. Measured from the server's own machine on a
throttled desktop (10 Mbps, 100 ms, 3× CPU, cache off): the landing's load event took 12.9 s
in the first run after the deploy, and 1.6–2.1 s in three runs later; `train@1x`, new that
day, was still a `MISS`. So the probable cause is a cold edge. It is not proven: nobody timed
the owner's own browser. To confirm it after the next deploy, open DevTools' Network tab on the
first visit and read the `cf-cache-status` of the slow requests.

What it shows: a CDN's value is not visible in a test from next to the server, where a `MISS`
costs a few milliseconds, but to a visitor far from it, where each `MISS` is a full round trip
to the server. Two things would soften it. First, fewer renamed files per deploy (content
hashing already keeps an unchanged picture's name; the code's chunks churn more). Second,
Cloudflare's Tiered Cache, which makes a location ask a bigger nearby one before the server.
Warming it from this machine would not help, because its requests go out through other
locations (`SIN`, `CDG` and `MXP` in three requests) than a visitor's.

**39. A wait the viewer can see must say it is waiting, until the thing is drawn, not until
its data come.** The carriage's window, while the replay loaded, held a single space: kept
blank on purpose so that nothing moved. Then, once the replay was in, the stage mounted and
painted its dark ground at once, and its pictures only as they came. On a cold edge (38) that
was more than 10 s of black glass, and the owner took it for a bug. A blank or dark box reads
as broken after a second or two, however correct the code behind it. The fix
(`FeaturedReplay.tsx` `painted`): a wait that is seen stays over
the stage (first the replay page's line, "Rewinding the reels…"; since 2026-10-16 the house's
loading picture, `TrainLoader`) until its pictures are decoded or 8 s have passed. The stage is laid out but
hidden under it, and the replay starts playing only then. The wait for the pictures
(`stage/pictures-of.ts`) is the one the replay page's curtain already used, now shared. The
general check: for every place the viewer waits, ask what they see at each step (nothing, a
dark ground, half the pictures), not only whether the data have arrived. Not deployed yet.

**40. A transform set from script moves a picture only if it has a layer of its own; otherwise
every frame repaints it.** The owner saw a speaker's puppet rise into the stand at a low frame
rate on a phone, while every other motion was smooth. Measured on the live replay (an emulated
phone at 3×, CPU 4× slower, 2026-10-15), the first 0.8 s of each speech ran at about 34 fps with
5–7 frames of 50–150 ms. The felt speech box was the obvious suspect, and taking its texture
off changed nothing. The trace showed where the work was: the raster threads were idle before
the speech, then busy flat out (about 200 ms of raster per 100 ms) for exactly the rise's
0.1–0.9 s. The rise is Motion setting `transform` from script each frame, and Chrome promotes
an element to its own layer for a CSS or Web Animations animation, not for a style written from
script. So the figure and its wall shadow, large pictures at the screen's density, were painted
and rastered again on every frame. With `will-change: transform` on both while they rise
(`Puppet.tsx` `rising`), raster per speech fell from about 1.5 s to 0.3 s and the long frames
from 4 to 1. Only while they rise: a layer is a bitmap held for as long as it lasts (10). Two
notes on method. Under Chrome's CPU throttling, the main thread's tasks are padded with idle
time, so their length says nothing about real work: read the raster threads and the paint
rectangles. And subtract one suspect at a time (15): the clip on the shadow, which looked
guilty (a 10,000-unit box), changed nothing either.

**41. Whatever a scene says was on the stage must come from what the stage showed, not from the
log.** As voting opens, the vote scene drops "the day's last speaker" behind the stand. It took
that seat from the folded log. Since 2026-10-12 a run of passes plays as one beat with the stand
empty, so a day ending in passes showed an empty stand, and then a puppet that had never been on
the stage flashed up for half a second as the table rose. Live it was worse: a seat never folds
the passes (they are observer-tier), so the log's last turn was a speaker from several turns
earlier. Only the beat cutter knows what each viewer was shown, so the cutter now stamps
`vote.opens` with the seat at the stand (`beatsFor.ts` `atStand`, nobody under a notice), and
the scene draws that. The rule for a transition that carries something over from the scene
before: hand it over from the previous beat, never rebuild it from the data.

**42. A loading boundary splits hydration in two, and a request the outer part starts can answer
before the inner part hydrates.** Adding the site's loader (`(site)/loading.tsx`, 2026-10-16)
put every site page inside a Suspense boundary. React hydrates the shell around a boundary first
and the page inside it a moment later. The nav, in the shell, asks for the rooms list to count
the tables boarding, and the departures board, inside the page, reads the same cached request.
With the answer quick (the tests' mocks), it arrived in between, so the board hydrated with
three rows where the server's HTML had the pending "·". React logged "Hydration failed" and drew
the board again. Nobody would see it on the page; the dev overlay's "1 Issue" badge showed up in
the rooms-390 golden. Before the boundary, the whole page hydrated in one pass, before any
answer could come, so the mismatch could not happen. The fix (`hooks/useHydrated.ts`):
`useSyncExternalStore` returns the server snapshot (false) during hydration and the client one
(true) after it, and the board and `useBoarding` treat the list as still pending until then. The
rule: a part that reads data the server did not have must draw what the server drew until it
has hydrated, and adding a Suspense or loading boundary is a moment to look for reads like it.

**43. Decode ahead every picture the next beat will show, including the one it changes into
halfway.** With Reveal on, a replay's passes popped in: the box, then its words, then the
puppet, late and differently for each seat. The decode-ahead (13) was already there, but it
held the next speaker's thinking and talking poses, and a pass rises thinking and then rests
(`base`) 0.6 s in. The rest pose was never fetched before that moment. Probed on production
(2026-10-16), each pass's rest pose was first requested 1.4 s into its beat, as the puppet
changed into it; with the pair chosen by the beat (`cast/ahead.ts`: thinking and base for a
pass, thinking and talking for a line), 4 to 6 s before, in the previous turn. The rule: list
what a beat shows from its first frame to its last, not what it opens with, and still hold only
that one beat's pictures (a pose decodes to about 4 MB, 37). The probe that settles it: record
each picture's first request against the time its beat began.

---

## Small things that cost an afternoon

- Two rules for one class name in a CSS module are one class: a `.head` for a page's header and a
  `.head` for a 2px playhead further down the same file merged, and the header became a 2px
  absolute strip. Name each part for what it is (`.playhead`).
- A browser starts sound only after the viewer has pressed something on the page; Safari only
  inside the press's own handler. Make or resume the `AudioContext` in a press listener, not in
  an effect that runs after it (`src/music/music.ts`). Fade with gain nodes: an iPhone ignores
  an audio element's `volume`.
- iPhone Safari gives an `AudioContext` a state the standard does not have: `interrupted`, when
  the viewer switches app or takes a call. A resume on returning to the page may be refused, and
  a check for `'suspended'` never matches it, so the music came back only when Safari got round
  to it. On a press, close an interrupted context and make a new one (`src/music/player.ts`).

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
- A component rendered by a server component that starts calling a client hook needs
  `'use client'`. Neither `tsc` nor lint notices; only `next build` fails, at prerender:
  "Attempted to call useSmall() from the server". `ChipSprite` was imported by the landing's
  server-rendered cards.
- Two things with the same `z-index` in one layer are ordered by where they sit in the page,
  and with portals that is the order they happened to be added in. The card's veil and the
  notes hint were both 5, and the veil covered the hint only because the hint mounted first.
  Making renders less frequent (lesson 33) changed the order, and the hint came out above the
  veil. Give anything that must cover something else a higher number; never rely on a tie.
- A full-page screenshot of a page whose sections mount as they come near (`useNear`) can be
  taken before they have mounted: the guide's golden came back with its demos blank. Scroll
  each one into view and wait for it before the whole-page shot.
- A Playwright run proves nothing until you know whose server answered on its port: another
  session's build held 3121 (2026-10-15), mine failed to start, and the suite ran against theirs.
  Check the port's process first (`ss -ltnp`, then `readlink /proc/<pid>/cwd`).
