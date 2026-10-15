# Principles to carry to the next project

Written for the owner. The general rules this project taught, grouped by topic. For each:
the principle in a line or two, where it was learned here (lesson numbers are
`frontend_lessons.md`; the phone's are `phone_lessons.md`; the audits are dated docs), and what
to read for the topic in general. The lessons tell the stories; this is the index to
generalise from.

---

## 1. React: identity, rendering and where state lives

- **A component re-renders when its parent does, unless something stops it.** Memo stops it
  only when every prop is the same object as last time. So stable identities come first
  (`useMemo`, `useCallback`, data that is not rebuilt), and `memo` second. *Lessons 5, 6, 33.*
- **State lives in the lowest component that needs it.** Typing into a box at the top of the
  tree redraws the tree on every letter. The parent takes the value when it is used (on submit)
  and pushes values in with a version counter. *Lesson 34.*
- **A `key` is an identity.** Changing it throws away the subtree and builds it again. Key the
  smallest thing that must restart. *Lesson 1; phone §5.*
- **Effects are for syncing with something outside React**, not for deriving data. An effect
  without dependencies runs after every render; one that sets state on every render doubles
  every render. *Lessons 4, 7, 33.*
- **Never mix state from two moments in one render.** When a child describes something to a
  parent, the description and the props it was made with travel together. *Lesson 3.*
- **A server component cannot call a client hook.** Shared components marked `'use client'`
  mark the line. *Small things.*

**Read:**
- react.dev:
  - "Preserving and Resetting State"
  - "Choosing the State Structure"
  - "You Might Not Need an Effect"
  - "Adjusting some state when a prop changes"
  - the reference pages for `memo`, `useMemo` and `useSyncExternalStore`
- The React Compiler, which automates much of the memoising by hand (not used here).
- Next.js: "Server and Client Components".

## 2. Caching, memoising and identity

- **A cache key must contain exactly what the result depends on.** If the key has too much in
  it (an instance id), the cache misses; if it has too little, it serves stale results. The
  paint cache was keyed on `useId` and missed on every remount. *Lessons 12, 36.*
- **A cache over a growing log grows with it.** Extend it on an append, rebuild it on an
  insertion. An append can be told from an insertion exactly when the log is sorted by a
  unique key. *Lesson 35.*
- **Keep the identity of what did not change**, so everything downstream can skip work (structural
  sharing, `keepSame`). *Lesson 35.*
- **Bound every cache**, by count or bytes. "Kept forever" is a memory leak with a delay. *Lessons
  35, 37; the October audit §6.*
- **A cached answer is a snapshot of an earlier moment.** Anything that means "now" (where
  history ends, the server's clock) must come from a fresh read. *Multiplayer audit, finding 9.*

**Read:**
- TanStack Query, "Important Defaults": `staleTime` against `gcTime`.
- Immutable data and structural sharing.
- Memoisation, cache invalidation and LRU eviction.

## 3. The browser's rendering pipeline

- **Know the pipeline: script, style, layout, paint, composite.** A change costs from the
  first stage it touches onward. `transform` and `opacity` can skip to compositing; layout
  properties and SVG attributes cannot. *Lessons 8, 9; phone §6.*
- **The browser repaints the box that changed, not the thing in it.** Keep moving things in
  tight boxes. *Lesson 8.*
- **Every animated property makes a layer, and a layer is a bitmap in memory.** Filters and
  blend modes are paid over their whole area, every time that area is drawn again. *Lessons
  10, 11, 26; phone §1–2.*
- **Even, low frame rates read better than uneven high ones.** *Lesson 14.*
- **Two things with the same z-index are ordered by where they sit in the page**, which can
  depend on timing. Give whatever must be on top a higher number. *Small things.*

**Read:**
- web.dev: "Rendering performance", and "Stick to compositor-only properties and manage layer
  count".
- Chrome DevTools: the Performance panel (Rendering, Layers).
- Safari Web Inspector: the Timelines and Layers tabs.

## 4. Memory

- **Count decoded bytes, not file bytes.**
  - An image takes width × height × 4.
  - A sound takes seconds × sample rate × channels × 4.
  - A 30 KB head became 0.56 MB; a 2 MB track became 33 MB.

  *Lesson 37; phone §3.*
- **Choose a picture's size from the pixels it is drawn at**, measured before the first fetch,
  not guessed from the device. *Lessons 22, 30.*
- **A phone kills a tab at a fixed line, while a desktop only slows down.** Test memory on the
  device. *Phone §4.*
- **Free what a page decoded when the viewer leaves it.** *Lesson 37.*

**Read:**
- MDN: "Responsive images", and the Web Audio API's `AudioBuffer`.
- WebKit's blog posts on memory debugging with Web Inspector.

## 5. Loading

- **A request that starts only when another finishes is waiting on it.** Find the waterfall
  and start things side by side; a dynamic import starts at its first render. *Lesson 29.*
- **Defer a mount only into a box that already has its final size.** *Lesson 27.*
- **Compress JSON, but not a stream.** A header set for a whole route block travels with every
  response in it. *Lesson 31.*
- **Preloading is a promise to need a file early.** A font preloaded on a page that does not show it
  competes with the first paint. Fonts not preloaded flash in late. *October audit
  follow-up.*

**Read:**
- web.dev's "Learn Performance" course: the critical rendering path, resource hints,
  `next/font`, lazy loading.
- *High Performance Browser Networking* (Ilya Grigorik, free online).

## 6. Real-time data: streams, catch-up and liveness

- **A backlog delivered down a live socket arrives one message at a time**, and each message
  can be a render. Batch the backlog before it reaches the store. *Lesson 32.*
- **Tell history from news by a line drawn when you connect**, and land history still. Draw
  the line from a fresh read. *`useGameStream`; multiplayer finding 9.*
- **A connection can be dead and still look open.** Liveness needs a heartbeat the client can
  hear and a watchdog that acts on silence. The browser's own retry covers only some failures.
  *Multiplayer finding 7.*
- **Order by sequence numbers, never by arrival.** Make appends cheap and insertions correct,
  and de-duplicate by membership. *`store.ts`; lesson 35.*
- **Of two answers to the same question, the older one must lose.** Compare the version each
  was taken at before applying it. *Multiplayer finding 8.*
- **The server's clock is the authority.** A client shows it; it never runs its own.
  *`live_timing_sheet.md` ruling 4.*

**Read:**
- MDN: "Using server-sent events" (the `id:`/`Last-Event-ID` resume, named events) and the Page
  Visibility API.
- Martin Kleppmann, *Designing Data-Intensive Applications*: logs, ordering and replication.

## 7. Multiplayer: authority, privacy and races

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

## 8. Method

- **Measure before you fix, and the same way after.** Use one script, one build and one
  sitting, with nothing animating. *Lessons 17, 25, 28.*
- **Take a census of the whole class of problem, fix it in one batch, then add a gate** so it
  stays fixed. *Lesson 16; phone fixes.*
- **A rule written down is kept only by a measurement.** A render census found two lessons
  broken. *Lesson 33.*
- **Read an audit as a list of claims to check, not a to-do list.** The survey's "phone
  copies of the lobby pictures", measured, came to files only about a tenth too big for a
  phone. *Lesson 19.*
- **Subtract before you add:** remove the thing to learn what it costs. *Lesson 15.*
- **Know whose server answered before trusting a test.** And when HEAD moves during a run,
  compare against the commit that was built. *`testing.md`.*

**Read:**
- web.dev on Core Web Vitals and field data against lab data.
- Brendan Gregg's "USE method" (utilisation, saturation, errors), a general way to look at a
  slow system before guessing.
