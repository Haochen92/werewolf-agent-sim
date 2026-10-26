# React identity: keys, renders, memo, effects and where state lives

## What this teaches, and what you need first

How React decides what to keep, what to rebuild and what to run again when something changes, with
the stage's own mistakes as the worked examples. This is a foundation topic: you need only
JavaScript and the idea that a component is a function that returns JSX. Its sibling foundation is
[`rendering_pipeline.md`](rendering_pipeline.md), which starts where this one stops: what the
browser does once React has changed the page.

Five words used throughout:

- **Component**: a function that takes inputs and returns a description of what to show.
- **Props**: the inputs a parent hands a component (`<Dock text="hi" />` passes `text`).
- **State**: a value a component keeps between calls (`useState`). Setting it asks React to call the
  component again.
- **Hook**: a function named `use...` (`useState`, `useMemo`, `useEffect`) that attaches something
  to the component it is called in.
- **Instance**: one placed copy of a component, with its own state. `<Dock />` written twice is two
  instances.

---

## 1. Identity is position plus key

React keeps a tree of instances. Each time a parent runs again, React lines up what it returned now
against last time and decides, child by child, whether it is the same instance. It is the same when
three things match: the **position** (the nth child of this parent), the **type** (the same
component function) and the **key**, if one is given. All three match: the instance is kept with its
state. Any one differs: the old instance is thrown away and a new one made.

```jsx
{editing ? <Field /> : <Field />}      // same position, same type: one instance, state kept
<Field key={user.id} />                // a new user.id: a new instance, state starts over
{wide ? <WideCar /> : <NarrowCar />}   // a change of type at one spot: a new instance
```

So a key is not a "refresh" signal; it is the instance's name, and a new name means a new instance
with everything under it. And a type is compared by reference: a component function created during
a render (including `memo(Thing)` called inside a render) is a new type each time, so its instance is
rebuilt on every render.

### In this project

**Lesson 1, the whole scene keyed per beat.** Every scene was `<XBeat key={beat.id:seq} />`, so that
a beat would "start fresh" (build_log §8.3, 2026-10-01). Each beat named a new instance, and React
built the whole scene again: the car's picture, the shutter, the light, the wing's nine heads, the
puppet. Now the smallest thing that must restart is keyed:

- `frontend/src/stage/scenes/VoteScene.tsx::VoteBody` keys `VoteBeat` on the viewer and their choice
  only, so the vote stays up from chip to chip; the newest ballot line is keyed on the count
  (`BallotLine key={counted}`), so only it arrives again.
- `frontend/src/stage/scenes/DayScene.tsx` keys the `TurnDock` on `beat.seq`: a new turn starts with
  an empty box.
- Where only a little state must restart, there is no key. `LynchScene.tsx` holds `told` with the
  beat it belongs to and resets it during render when `beat.seq` moves on (the pattern is in
  section 6).

**Lesson 2, eight scenes, eight types.** The deal, the day, the vote, the lynch, the night's lobby,
the morning, the game over and the replay's night all stand in the dining car, but each was its own
component, so a change of scene put a new type at the same spot and rebuilt the car (build_log
§8.9). Now `frontend/src/stage/scenes/CarScene.tsx::carScene` makes one host that stays at that spot.
Each scene is a *body* under it that describes its set with `CarSetSpec`; the host draws the set
(`CarSetSheet`) and keeps it. The `memoised` map in the same file wraps each body in `memo` once and
reuses the wrapper: calling `memo(body)` in the host's render would be the new-type trap above.

**The backdrop, one level up (build_log §8.8).** `frontend/src/stage/Stage.tsx::Stage` draws the one
`BackdropSheet` in its own paint layer; a scene's `instruments/Backdrop.tsx::Backdrop` only
*registers* a description through `BackdropContext`. The picture's position belongs to the Stage, so
no beat or scene change can move it.

**A remount on purpose.** The host renders `<Body key={epoch} />` and bumps `epoch` when the set
first comes up, so the body mounts again under the set in the same commit and its pieces land above
the set's. A key is the tool for "start this over"; the mistake is using it on more than must.

### See it yourself

- The mark trick (phone lesson 5): in the console on `/workbench/vote`,
  `const el = document.querySelector('[data-layer=paint] [data-room] img')`, step a beat, then
  `el.isConnected`. `true` means the element is the same one.
- The committed form of that trick is the phone gate, `frontend/e2e/phone-rule.spec.ts`: it holds
  the set's elements (`SET_MARKS`: the wing, the house light, the room's picture) before each step
  and fails a beat that disconnects them.

### The rule

Key the smallest thing that must restart, and put what must persist at a position nothing above it
changes.

---

## 2. Render versus commit

A **render** is React calling your component functions to work out what the page should be. It
produces a description; the screen does not change. The **commit** is React comparing that
description with the last one and applying the differences to the DOM (the browser's own page
elements). The browser then lays out and paints, which is rendering_pipeline's subject.

So a render can commit nothing; everything in the component function is paid on every render, which
is why it must be cheap and change nothing outside itself (React's word: *pure*); and one update can
take several renders before the browser paints (an effect that sets state, section 5), each pass
seeing only its own state.

### In this project

**Heavy work inside render (rendering audit §1, 2026-10-02).** `Stage.tsx::Paint` calls a paint
generator during render. For the house light that means tracing the light's holes
(`paint/holes.ts`): 109 ms observed on one counted-chip transition (instrumented production `Paint`,
headless Chromium, CPU throttled four times), and 60 to 110 ms as lessons 12 and 36 record it. Work
that size in a render is why the drawing is cached (section 4).

**Lesson 3, two moments in one pass.** With the car's set kept across scenes, the host renders with
the new beat's props *before* the body's new description arrives, since the body sends it from a
layout effect after the commit (build_log §8.9, "Found on the way"). For that one pass the set was
drawn from the morning's view under the night's description, whose wing holds no death back. The
wing took it as a seat that had just died and closed the live notes editor. The fix, in
`CarScene.tsx`: a description travels with the props it was made with
(`interface Described { spec; props }`), and `CarSetSheet` is drawn from `described.props`, never
the host's current props.

### See it yourself

React DevTools, Profiler tab: record while stepping a beat in the workbench. Each bar is one commit.
With "Record why each component rendered while profiling" on (the Profiler's settings), clicking a
component says whether it rendered in that commit and why. A component listed as rendered may still
have changed nothing in the DOM.

### The rule

Keep render cheap and pure, and never draw from state taken at two different moments.

---

## 3. Re-render versus remount

These are the two outcomes of section 1, and they cost very different amounts.

A **re-render** runs the same instance's function again. Its state and its DOM elements are kept,
and React changes only what differs: the same `<img>` stays, with a new `src` if that changed. The
cost is CPU time.

A **remount** throws the instance away and makes a new one: its effects are cleaned up, its elements
removed and new ones created, its state starts from the initial value, its effects run again, and
its pictures are new elements to load and decode. That costs memory as well as time, since every
element made and dropped is garbage to collect. This project calls the elements rebuilt per step
**churn**.

`memo` and `useMemo` (section 4) only skip re-renders. A memoised component inside a subtree whose
key changes is remounted all the same.

### In this project

**The churn table (build_log §8.3, 2026-10-01).** What one beat step rebuilt, Chromium, 30 steps at
330 ms, counted by a MutationObserver probe, before and after the set and beat split:

| per step | day before | day after | morning before | morning after |
|---|---:|---:|---:|---:|
| DOM nodes added | 343 | 194 | 321 | 234 |
| pictures | 15.1 | 6.0 | 15.1 | 6.6 |
| paint sheets regenerated | 2.0 | 0.0 | 2.1 | 0.1 |

The split (phone lesson 5) made each scene a stable set that updates in place (`DaySet`,
`MorningSet`) and a small keyed part that remounts so its arrival plays again (`DayTurn`,
`MorningBeat`). Chromium's live nodes showed the pressure: 1,088 at the start, 1,468 mid-run, 693
three seconds later, transient and not a leak. On the owner's iPhone the page died at two to three
beats a second before the split; a desktop's slack hides that pressure and a phone's memory cap does
not.

**385 of 388 (rendering audit §2, 2026-10-02).** On a production snapshot (`04005ca0`, headless
Chromium), the audit counted the elements under the stage's layers before a transition and which
were disconnected after it. A counted chip in the vote replaced 385 of 388; a packmate's line, 402
of 403. The already split day replaced 121 of 220, the turn it meant to replace.

**The black frame (build_log §8.8).** Observed on the owner's iPhone in Safari: a freshly mounted
`<img>` with `decoding="async"` (what `next/image` sets) painted nothing for a frame until its decode
landed, so each beat that remounted the backdrop flashed the dark behind it. Chromium kept the
decoded picture and showed no flash, so the screenshot tests never saw it. That is an observed
condition on one engine, not a law that every remount re-decodes. The fixes: the Stage-owned
backdrop (section 1), and `decoding="sync"` on the stage's pictures so that what still remounts
paints at once when its bytes are cached.

**The host, measured (build_log §8.9).** The vote's 41 steps fell from 67,480 to 23,064 ms of raster
(Chromium's phone frame, CPU throttled four times), but the host shipped in one batch with other
fixes, so that number is the batch's. The host's own evidence is a walk through thirteen changes of
scene in which the wing, the light, the shutter and the backdrop were kept every time.

### See it yourself

- `/workbench/day?auto=330` steps a beat every 330 ms; watch "DOM Nodes" in Chrome's Performance
  monitor rise and settle.
- The §8.3 `.churn` probe is not committed. A console stand-in:
  `let n = 0; new MutationObserver(m => m.forEach(r => n += r.addedNodes.length)).observe(document.body, { childList: true, subtree: true })`,
  step ten beats, read `n`.
- React DevTools' "Highlight updates when components render" flashes what rendered but does not tell
  a re-render from a remount; pair it with the mark trick.

### The rule

A re-render costs CPU; a remount costs CPU, memory and the instance's state, so make remounts rare
and deliberate.

---

## 4. Memo and referential equality

JavaScript compares objects by **reference**, whether two names point at the same object, not by
contents: `{ a: 1 } === { a: 1 }` is `false`.

By default a component re-renders whenever its parent does. `memo(Child)` skips that re-render if
every prop is the same as last time, by reference (`Object.is`). An object or function written
inline in the parent (`style={{...}}`, `onClick={() => ...}`) is new on every render, so the check
always fails. `useMemo(() => value, deps)` and `useCallback(fn, deps)` hand back the *same* object
until a dependency changes. They are the precondition for memo, not garnish.

A **cache** is the same idea outside React: keep a result under a key and hand it back when the key
repeats. The key must contain exactly what the result depends on. Too much in it and equal requests
miss; too little and different requests get a stale answer.

### In this project

**Lesson 4, memoise what registers.** `CarScene.tsx::CarSetSpec` sends its description to the host
from a layout effect with no dependency list, so after every render of the body. Each send is a new
object, so the host's state changes and the host renders again. If the body rendered again with it,
it would send again: a loop. It does not, because the host renders the body through its `memo`
wrapper with the same props, so the host's second render stops at the body.

**Lessons 6 and 33, fresh objects broke the memo.** Written down on 2026-10-02, still broken on the
live page on 2026-10-15. The 2026-10-11 audit's follow-up measured it (dev build, seat 7 rejoining,
41 letters typed into the composer, renders counted per component):

| 41 letters | before (`cab002e2`) | after (2026-10-15) |
|---|---|---|
| what rendered | the whole stage: the set and the side slot twice per letter, 738 seat tiles, 1,394 transcript rows | the dock and its composer, 41 times each |

Two causes. The live theatre built the props it handed the scene (`turnInput`, `onCard`) as new
objects each render, so no memo below could hold. And `CarSetSpec`'s registration after every render
rendered the host a second time: the "twice". The fixes, in
`frontend/src/stage/containers/LiveTheatre.tsx`: `turnInput`, `dock` and `wayOut` through `useMemo`,
`onCard` and `onNext` through `useCallback`; and `memo` on the host, the set and the side slot. The
typed text also moved into the dock (section 6).

Where a description is plain data the code compares by value instead: `Stage.tsx::Camera`,
`Backdrop.tsx::Backdrop` and `Stage.tsx::Paint` key on `JSON.stringify` of it, so "a new-but-equal
object changes nothing", in the code's words.

**Lessons 12 and 36, one case: the key held the instance.** `Paint`'s drawing depends on the
generator and its options. The instance's id (from `useId`, unique per instance so two stages on one
page never share an SVG gradient name) only *labels* it. Lesson 12 (2026-10-02) described the right
key, "keyed by the generator's inputs". The code then keyed on `id + '\0' + JSON.stringify(opts)`,
as the 2026-10-11 audit §3 read it, calling the comments' claim of reuse across instances an
overstatement. build_log §8.10 had judged the fix not worth a pass, since with the host the light is
one instance from the deal to the ending. A remount proved otherwise: the dining car mounts again
after a night with a new `useId`, missed, and traced the house light again, 60 to 110 ms on a phone,
on the morning's busiest beat. The key lesson 12 describes was built only on 2026-10-15
(`f30d4496`, lesson 36): `Stage.tsx::drawn` draws under a stand-in id (`ANY_ID`), keeps the drawing
by the options alone, per generator, and writes each instance's id in on the way out.

What it provides, as the code makes it: drawings kept in the page's memory, at most 48 per generator
(`KEEP`), least recently used dropped first. A repeat skips the tracing only while it is among those
48, within one page load; writing the id in and setting the markup are still paid.

### See it yourself

- React DevTools Profiler, "why each component rendered" on: type into the composer in a live game;
  each commit should list `TurnDock` and its composer only. Lesson 33's census hook (a stand-in
  `__REACT_DEVTOOLS_GLOBAL_HOOK__` counting renders per component) is not committed, so the Profiler
  is the route.
- The cache's contract is a test: `frontend/src/stage/paint/paint.test.ts`, "is the drawing under
  another id once the stand-in is renamed" (`npm test` in `frontend/`).

### The rule

Memo holds only when every prop keeps its identity, and a cache key holds exactly what the result
depends on, never the instance.

---

## 5. Effects and their dependencies

An **effect** is code React runs *after* a commit, to keep something outside React in step: an
observer, a timer, a subscription, a measurement of the DOM. `useEffect(fn, deps)` runs `fn` after
the browser has painted. A function returned from `fn` is the **cleanup**, run before the next run
and when the instance goes. The dependency list decides when it runs again:

```js
useEffect(fn)          // no list: after every commit of this instance
useEffect(fn, [])      // once, after the first commit
useEffect(fn, [a, b])  // again only when a or b is a different value (Object.is)
```

A **layout effect** (`useLayoutEffect`) differs in one way: it runs after React has changed the DOM
but *before* the browser paints. It is for measuring an element, or for a change that must land in
the same frame as the commit. If it sets state, React renders again before painting, so the screen
shows only the result.

Effects are not for deriving data from props or resetting state when a prop changes; both can be
done during render (section 6), and an effect costs an extra render.

### In this project

**Lesson 7, observers made on every render.** The stand's layout effect had no dependency list, so it
created two ResizeObservers and measured the plate on every render of every beat (build_log §8.10).
Now `frontend/src/stage/instruments/Stand.tsx::Stand` makes one ResizeObserver over the elements
whose size it depends on (the stand, the plate, the speech box) and runs again only when
`[speech, g.u, g.railY, plated]` change. The observer, not the render, calls the re-placement.

**No list, on purpose.** `CarSetSpec`'s sending effect has none, because the description must follow
every render of the body; that is safe only because of the memo in section 4. Its withdrawal is a
second layout effect on `[set]`, so it runs only when the body goes.

**A handoff in one frame (build_log §8.8).** `Backdrop.tsx::Backdrop` registers its description in a
layout effect keyed on its JSON and clears it in the cleanup. When a scene gives way, the old
description's clearing and the new one's arrival fall in one commit, before paint, so the Stage
never draws a frame without a backdrop. Observed on production: the backdrop's `<img>` kept its mark
across forty beats and six scene changes (phone lesson 8).

### See it yourself

- `npm run lint` runs `react-hooks/exhaustive-deps`, which flags a list missing something the effect
  reads. The camera effect in `Stage.tsx::Stage` turns it off on purpose, with the reason beside it.
- No committed script counts effect runs. Locally, add `console.count('stand')` inside the effect in
  `Stand.tsx`, step beats in `/workbench/day`, see it rise only when the stand or its words change,
  then remove it.

### The rule

Give every effect the dependencies it reads, and leave the list off only when the effect must follow
every render and something else stops the loop.

---

## 6. Where state lives

Setting state re-renders the component that owns it and, unless memo stops it, everything below. So
the owner of a piece of state decides how much of the tree pays for each change. The policy:
**state lives in the lowest component that needs it.** A parent that needs a value at one moment
reads it then, as the argument of a callback, instead of holding it.

Two patterns make that work:

- **Pushing a value into a child**: pass it as a prop with a version counter, and let the child take
  it when either changes, by "adjusting state when a prop changes", compared during render, not in
  an effect:

  ```js
  const [prev, setPrev] = useState(prop);
  if (prev !== prop) { setPrev(prop); setValue(prop); }   // React re-runs at once, before commit
  ```

- **Starting state over**: key the component on what it belongs to (section 1).

One boundary more. In Next.js a **server component** runs on the server and sends finished markup;
it has no state and cannot call hooks. A file starting `'use client'` holds **client components**,
which can. A component a server component renders that calls a hook must be a client component.

### In this project

**Lesson 5, a ticking state at the root.** A 250 ms countdown interval set state in the live
theatre, so the theatre and every scene body under it re-rendered four times a second during a live
turn, while figures were animating (build_log §8.10). The clock is now split by who needs what
(`frontend/src/hooks/useCountdown.ts`):

- `useCountdown`, in the theatre, checks every 250 ms but asks for a render only once the deadline
  has passed. The theatre hears one event, the expiry.
- `useTimeLeft` ticks every 250 ms, but only inside
  `frontend/src/stage/instruments/CountText.tsx::CountText`, the leaf that shows `1:14`, placed in
  the dock, the ballot and the pack's line.

**Lesson 34, typed state in the leaf.** The composer's text was the live theatre's state, so each
letter re-rendered the stage (the table in section 4). Now
`frontend/src/stage/instruments/TurnDock.tsx::useTyped` holds the line in the dock. The parent needs
it twice and holds it neither time: on Send it receives the line as the argument of `onSay`; to put
a draft in, it passes `text` with a counter, `DockInput.landed`, because two drafts can be the same
string. `useTyped` compares `text`, `notes` and `landed` with what it last took, during render, and
takes the new value. The dock is keyed on `beat.seq`, so the next turn starts empty.

**S19, a server component's child calling a client hook.** `frontend/src/stage/cast/ChipSprite.tsx`
began calling `useSmall()` (which reads the Stage's context) while the landing's server-rendered
cards imported it. Neither `tsc` nor lint noticed; `next build` failed at prerender: "Attempted to
call useSmall() from the server". The file now starts with `'use client'`.

### See it yourself

- React DevTools Profiler during a live turn with the clock running: the commits every 250 ms list
  `CountText` and nothing above it.
- Highlight updates on, type into the composer: only the dock flashes.
- For S19, `npm run build` in `frontend/` is the check that catches it; the dev server and `tsc` do
  not.

### The rule

Put state in the lowest component that needs it; a parent reads the value when it acts and pushes
one in with a counter.

---

## Case index

| Case | Short | Section |
|---|---|---|
| Head A | Re-render and remount | 3 |
| 1 | A key is an identity | 1 |
| 2 | One host holds what persists | 1 |
| 3 | Render from the description's own props | 2 |
| 4 | Memoise what registers | 4 (its effect: 5) |
| 5 | Ticking state at the root | 6 |
| 6 | New objects defeat memo | 4 |
| 7 | Effects without dependencies | 5 |
| 12 with 36 | A cache keyed on the instance misses | 4 |
| 34 | Typed state lives in the leaf | 6 |
| S19 | A server component's child calling a client hook | 6 |
| Phone 5 | Keys and churn; the mark trick | 1 and 3 |

---

## If you are asked about it

"React keeps a component's state as long as it stays at the same position, with the same type and
key. On the werewolf stage I own, every scene was keyed on the beat, so each beat threw away and
rebuilt the whole scene: one counted vote replaced 385 of 388 elements, and fast beats crashed the
page on an iPhone. I separated what persists from what changes: one host holds the dining car's set,
each scene only describes the set it wants, and only the part that has to replay is keyed. Then
re-renders: memo works only if every prop keeps its identity, and the live page handed down fresh
objects every render, so 41 typed letters redrew the whole stage. Memoising those props and moving
the typed text into the dock left 41 renders of the dock and nothing else. Caches follow the same
logic: our lighting cache had the instance id in its key, so a remount missed and re-traced 60 to
110 ms of geometry; now the key holds only the options the drawing depends on. And ticking or typed
state lives in the leaf that shows it, never at the root."

---

## Reading

From principles §1:

- react.dev:
  - "Preserving and Resetting State"
  - "Choosing the State Structure"
  - "You Might Not Need an Effect", with its section "Adjusting some state when a prop changes"
  - the reference pages for `memo`, `useMemo` and `useSyncExternalStore`
- The React Compiler, which automates much of the memoising by hand (not used here).
- Next.js: "Server and Client Components".

From principles §2:

- TanStack Query, "Important Defaults": `staleTime` against `gcTime`.
- Immutable data and structural sharing (a topic; its case, lesson 35, is in realtime_and_sync).
- Memoisation, cache invalidation and LRU eviction (a topic).

Added, react.dev only:

- "Render and Commit" and "Keeping Components Pure" (section 2).
- "Synchronizing with Effects" and the reference page for `useLayoutEffect` (section 5).
- The reference pages for `useCallback` and `useId` (section 4).

No case here, so reading only: transitions and Suspense (the `useTransition` and `<Suspense>`
reference pages) and Strict Mode's double run of effects in development (`<StrictMode>`).
