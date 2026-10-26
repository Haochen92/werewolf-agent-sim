# Learning: the frontend, taught from this project's cases

Status (2026-10-26): the index of the learning track. It was `principles.md` (written 2026-10-15,
eight topics, 30 of the lessons) and became this index on 2026-10-26: one section per tutorial, every
principle line kept, the lessons it had not reached (2, 13, 18, 20, 21, 23, 24, 29a and 38 to 49)
added, and the "Read" lists kept with each topic.

Written for the owner. The frontend was built by AI agents to the owner's specs and rulings (the owner
wrote the event schema and co-wrote the beat sheet). These documents teach the general frontend
knowledge behind what was built and what went wrong, so that each case can be explained, and carried
to the next project.

Three kinds of document, each with one job:

- **The tutorials** below teach one topic each: the concepts first, then this project's cases as
  worked examples, a step to see it yourself, the rule, and a one-minute answer.
- **[`frontend_lessons.md`](../frontend_lessons.md)** is the log: every lesson as it was learned,
  numbered, with its date and story. Each tutorial ends with an index from lesson numbers to its
  sections.
- **[`phone_lessons.md`](../phone_lessons.md)** is the dated case study of making the stage survive a
  phone (2026-10-01 to 10-02), told as one story; it links the tutorials for the concepts.

**Reading order.** The two foundations first: react_identity and rendering_pipeline. Then
memory_and_pictures, loading_and_deploy and stage_motion, which build on rendering. Then
performance_method, which uses all of them. realtime_and_sync and css_layout stand alone. testing
comes last. The design record of the page's data flow is
[`client_design.md`](../client_design/client_design.md); realtime_and_sync teaches its concepts.

| Tutorial | What it answers | Builds on |
|---|---|---|
| [React identity](react_identity/react_identity.md) | Why does a component redraw, remount or keep its state? | none |
| [The rendering pipeline](rendering_pipeline/rendering_pipeline.md) | What does the browser do to draw a frame, and what does each property cost? | none |
| [Pictures, sound and memory](memory_and_pictures/memory_and_pictures.md) | Why did a phone kill the tab, and how is a picture's size chosen? | rendering |
| [Loading, hydration and deploys](loading_and_deploy/loading_and_deploy.md) | What loads when, and why was the first visit slow? | identity, rendering |
| [Stage motion](stage_motion/stage_motion.md) | What moves on the stage, how often, and what carries over between beats? | rendering |
| [Performance method](performance_method/performance_method.md) | How do you find and fix what is slow without guessing? | all of the above |
| [Real time and sync](realtime_and_sync/realtime_and_sync.md) | How does a page follow a growing log over a connection that drops? | none |
| [CSS layout facts](css_layout/css_layout.md) | Which layout behaviours cost an afternoon here, and why? | none |
| [Testing a real-time UI](testing/testing.md) | What does each kind of test pin, and what does none of them cover? | all |

---

## React identity: keys, renders, memo, effects and where state lives

[Tutorial](react_identity/react_identity.md).

- **A component re-renders when its parent does, unless something stops it.** Memo stops it
  only when every prop is the same object as last time. So stable identities come first
  (`useMemo`, `useCallback`, data that is not rebuilt), and `memo` second. *Lessons 5, 6, 33.*
- **State lives in the lowest component that needs it.** Typing into a box at the top of the
  tree redraws the tree on every letter. The parent takes the value when it is used (on submit)
  and pushes values in with a version counter. *Lesson 34.*
- **A `key` is an identity.** Changing it throws away the subtree and builds it again. Key the
  smallest thing that must restart. *Lesson 1; phone §5.*
- **Separate what persists from what changes, and put the persistent part in one place** that
  outlives the parts that come and go. *Lesson 2.*
- **Effects are for syncing with something outside React**, not for deriving data. An effect
  without dependencies runs after every render; one that sets state on every render doubles
  every render. *Lessons 4, 7, 33.*
- **Never mix state from two moments in one render.** When a child describes something to a
  parent, the description and the props it was made with travel together. *Lesson 3.*
- **A cache key must contain exactly what the result depends on.** If the key has too much in
  it (an instance id), the cache misses; if it has too little, it serves stale results. The
  paint cache was keyed on `useId` and missed on every remount. *Lessons 12, 36.*
- **Keep the identity of what did not change**, so everything downstream can skip work (structural
  sharing, `keepSame`). *Lesson 35.*
- **A server component cannot call a client hook.** Shared components marked `'use client'`
  mark the line. *S19.*

**Read:**
- react.dev:
  - "Preserving and Resetting State"
  - "Choosing the State Structure"
  - "You Might Not Need an Effect"
  - "Adjusting some state when a prop changes"
  - the reference pages for `memo`, `useMemo` and `useSyncExternalStore`
- The React Compiler, which automates much of the memoising by hand (not used here).
- Next.js: "Server and Client Components".
- Immutable data and structural sharing.

## The rendering pipeline: frames, layers, paint and what each property costs

[Tutorial](rendering_pipeline/rendering_pipeline.md).

- **Know the pipeline: script, style, layout, paint, composite.** A change costs from the
  first stage it touches onward. `transform` and `opacity` can skip to compositing; layout
  properties and SVG attributes cannot. *Lessons 8, 9; phone §6.*
- **The browser repaints the box that changed, not the thing in it.** Keep moving things in
  tight boxes. *Lesson 8.* [2026-10-26: an observed condition, not a guarantee: build_log §8.10
  measured where it held; the tutorial gives the limit.]
- **Every animated property makes a layer, and a layer is a bitmap in memory.** Filters and
  blend modes are paid over their whole area, every time that area is drawn again. *Lessons
  10, 11, 26; phone §1–2.*
- **A transform set from script moves a picture only if it has a layer of its own;** otherwise
  every frame repaints it. *Lesson 40.*
- **An instant swap is not an animation:** switch it with `visibility`, not an opacity fade, which
  is still a layer. *Lesson 47.*
- **Don't start the first move under a fading cover:** a fade over the whole stage lifts the page
  onto many layers at once. *Lesson 48.*
- **Two things with the same z-index are ordered by where they sit in the page**, which can
  depend on timing. Give whatever must be on top a higher number. *S20; also S13, S15.*

**Read:**
- web.dev: "Rendering performance", and "Stick to compositor-only properties and manage layer
  count".
- Chrome DevTools: the Performance panel (Rendering, Layers).
- Safari Web Inspector: the Timelines and Layers tabs.

## Pictures, sound and memory

[Tutorial](memory_and_pictures/memory_and_pictures.md).

- **Count decoded bytes, not file bytes.**
  - An image takes width × height × 4.
  - A sound takes seconds × sample rate × channels × 4.
  - A 30 KB head became 0.56 MB; a 2 MB track became 33 MB.

  *Lessons 13, 37; phone §3.*
- **Choose a picture's size from the pixels it is drawn at**, measured before the first fetch,
  not guessed from the device. *Lessons 22, 30.*
- **Decode ahead every picture the next beat will show**, including the one it changes into
  halfway; a fresh picture shown before it is decoded draws late or blank. *Lessons 13, 43.*
- **A baked copy of something computed must cover everything the computation reads**, and a
  layout that only moves a baked picture is that picture moved, not a second bake. *Lessons 29a, 44.*
- **A phone kills a tab at a fixed line, while a desktop only slows down.** Test memory on the
  device. *Phone §4.*
- **Free what a page decoded when the viewer leaves it.** *Lesson 37.*
- **Bound every cache**, by count or bytes. "Kept forever" is a memory leak with a delay. *Lessons
  35, 37; the 2026-10-11 audit §6.*
- **Sound starts only after the viewer has pressed something**, and iPhone Safari has its own
  `interrupted` state for an audio context. *S3, S4.*

**Read:**
- MDN: "Responsive images", and the Web Audio API's `AudioBuffer`.
- WebKit's blog posts on memory debugging with Web Inspector.
- Memoisation, cache invalidation and LRU eviction.

## Loading, hydration and deploys

[Tutorial](loading_and_deploy/loading_and_deploy.md).

- **A request that starts only when another finishes is waiting on it.** Find the waterfall
  and start things side by side; a dynamic import starts at its first render. *Lesson 29b.*
- **A deferred component is deferred only if its mount, its data and its pictures all wait.**
  *Lesson 23.*
- **Defer a mount only into a box that already has its final size.** *Lesson 27.*
- **A size measured after mount is a guess on the first render, and the guess fetches.** *Lesson 30.*
- **Compress JSON, but not a stream.** A header set for a whole route block travels with every
  response in it. *Lesson 31.*
- **A loading boundary splits hydration in two,** and a request the outer part starts can answer
  before the inner part hydrates. *Lesson 42.*
- **A page drawn on pictures shows its words before its pictures:** hold it whole, and run the
  hold before React. *Lesson 45.*
- **A wait the viewer can see must say it is waiting,** until the thing is drawn, not until its
  data come. *Lesson 39.*
- **A deploy empties the CDN of every file it renamed,** and the first visitor at each of its
  locations pays for all of them (the probable cause; not proven). *Lesson 38.*
- **Preloading is a promise to need a file early.** A font preloaded on a page that does not show it
  competes with the first paint. Fonts not preloaded flash in late. *The 2026-10-11 audit's
  follow-up.*
- **Module state is not shared just because two files import the same module.** *S1; also S18.*

**Read:**
- web.dev's "Learn Performance" course: the critical rendering path, resource hints,
  `next/font`, lazy loading.
- *High Performance Browser Networking* (Ilya Grigorik, free online).

## Stage motion: what moves, how often, and what it carries over

[Tutorial](stage_motion/stage_motion.md). The rules themselves are in
[`stage_architecture.md`](../stage_architecture.md) §6.

- **Even, low frame rates read better than uneven high ones.** *Lesson 14.* [2026-10-26: the
  phone's 24 steps a second is what the stepped motion aims at, not a measured steady rate.]
- **Whatever a scene says was on the stage must come from what the stage showed,** not from the
  log. *Lesson 41.*
- **A percentage move is relative to the moving element;** shrink the element and the move
  shrinks with it. *S10.*

## Performance method: how to find and fix what is slow

[Tutorial](performance_method/performance_method.md).

- **Measure before you fix, and the same way after.** Use one script, one build and one
  sitting, with nothing animating. *Lessons 17, 25, 28.*
- **Take a census of the whole class of problem, fix it in one batch, then add a gate** so it
  stays fixed. *Lesson 16; phone fixes.*
- **A rule written down is kept only by a measurement.** A render census found two lessons
  broken. *Lesson 33.*
- **Read an audit as a list of claims to check, not a to-do list.** *Lesson 19.*
  [2026-10-26: an example citing "the survey's phone copies of the lobby pictures", "about a
  tenth too big", was removed here; no source for the figure was found.]
- **Subtract before you add:** remove the thing to learn what it costs. *Lesson 15.*
- **Before fixing a stall, find where its time goes:** decoding, or each frame's work. *Lesson 46.*
- **When one page lags and another with the same scene doesn't, diff the pages,** in the viewer's
  own engine. *Lesson 49.*
- **Know the instrument:** dev numbers are not production numbers; read layer memory on the
  device. *S11, S12, S16.*

**Read:**
- web.dev on Core Web Vitals and field data against lab data.
- Brendan Gregg's "USE method" (utilisation, saturation, errors), a general way to look at a
  slow system before guessing.

## Real time and sync: a page that follows a growing log

[Tutorial](realtime_and_sync/realtime_and_sync.md). The design record:
[`client_design.md`](../client_design/client_design.md).

- **A backlog delivered down a live socket arrives one message at a time**, and each message
  can be a render. Batch the backlog before it reaches the store. *Lesson 32.*
- **Tell history from news by a line drawn when you connect**, and land history still. Draw
  the line from a fresh read. *`useGameStream`; multiplayer finding 9.*
- **A connection can be dead and still look open.** Liveness needs a heartbeat the client can
  hear and a watchdog that acts on silence. The browser's own retry covers only some failures.
  *Multiplayer finding 7.* [2026-10-26: built: `catch-up-boundary.ts::streamStalled` reopens a
  stream silent past 40 s.]
- **Order by sequence numbers, never by arrival.** Make appends cheap and insertions correct,
  and de-duplicate by membership. *`store.ts`; lesson 35.*
- **A cache over a growing log grows with it.** Extend it on an append, rebuild it on an
  insertion. An append can be told from an insertion exactly when the log is sorted by a
  unique key. *Lesson 35.*
- **Whatever holds a place in a derived list needs a rule for when the list changes under it,**
  and a viewer's override lapses when the moment it was made in has passed. *Lessons 21, 24.*
- **Of two answers to the same question, the older one must lose.** Compare the version each
  was taken at before applying it. *Multiplayer finding 8.*
- **A cached answer is a snapshot of an earlier moment.** Anything that means "now" (where
  history ends, the server's clock) must come from a fresh read. *Multiplayer finding 9.*
- **The server's clock is the authority.** A client shows it; it never runs its own.
  *`live_timing_sheet.md` ruling 4.*

**Read:**
- MDN: "Using server-sent events" (the `id:`/`Last-Event-ID` resume, named events) and the Page
  Visibility API.
- TanStack Query, "Important Defaults": `staleTime` against `gcTime`.
- Martin Kleppmann, *Designing Data-Intensive Applications*: logs, ordering and replication.

## CSS layout facts

[Tutorial](css_layout/css_layout.md).

- **Two rules for one class name in a CSS module are one class.** *S2.*
- **What is absolutely placed can lengthen the page;** clip it, and know that `overflow: clip` and
  `scrollWidth` disagree. *S7, S8, S14.*
- **A grid row can keep a height from before its content measured itself.** *S17.*
- **Don't make a `<button>` the box whose layout matters;** test a variant page on the device.
  *S23.*

## Testing a real-time UI

[Tutorial](testing/testing.md). The suite itself: [`testing.md`](../testing.md).

- **Tests that pass alone and fail in parallel are waiting on time, not on state.** Wait on the
  state. *Lesson 20; S21.*
- **A gate that reads state at the end of a window misses what happened inside it.** *Lesson 18.*
- **Know whose server answered before trusting a test.** And when HEAD moves during a run,
  compare against the commit that was built. *`testing.md`; S22.*
- **A check runs only when someone runs it.** This project has no CI.

## The server's half: authority, privacy and races

No tutorial: these are the server's rulings, told in [`seat_continuity.md`](../seat_continuity.md),
[`server_client_transport.md`](../server_client_transport.md) and the
[multiplayer audit](../multiplayer-audit-2026-10-15.md). Kept here because they were learned with
the client.

- **The server decides what each player may see, per event, when it sends it.** A client that
  only hides data has already leaked it. *Multiplayer audit, "What is solid".*
- **Side channels leak as surely as data does.** Counts, ids, timings, the length of a phase,
  and the wording of an error can all say what a payload hides. Check every number and message a
  viewer receives. *Multiplayer findings 1–3.*
- **Check-then-act across an `await` is a race.** Reserve first, give back on failure, and
  allow one at a time where it matters. *Multiplayer finding 4.*
- **Tell "rejected" from "failed".** Destroy credentials only on a definite refusal (403, 404,
  410), never on a network error. *Multiplayer finding 11.*
- **Design for the player who leaves.** A grace period for a dropped connection is not a policy
  for someone who has gone. *Multiplayer finding 5.*

**Read:**
- Gabriel Gambetta, "Fast-Paced Multiplayer" (client-server game architecture, an
  authoritative server).
- OWASP on information exposure through error messages, and side-channel leaks.
- Race conditions and TOCTOU (time-of-check to time-of-use), and idempotency keys.
