# Frontend performance and ownership audit — 2026-10-11

The existing stack is viable. Keep Next/React and the shared renderer; improve resource
selection, presentation lifetime and computation before considering a renderer replacement.
The user confirmed that earlier Safari crashes were resolved. This review concerns additional
headroom and maintainability, not a claim that the current app still crashes.

The best immediately actionable improvement is the landing preview’s backdrop selection.
The strongest animation candidates are ID-independent lighting computation and removing
repeated filter work with visually equivalent assets. A framework rewrite would not directly
remove the cost of the current oversized images, lighting blends or SVG animation updates.

## Scope and evidence

- Snapshot of the working frontend at HEAD `dda7cdcf45893c490109b05b925d2e47bc3c8571`, including
  existing uncommitted workbench changes, copied to `/tmp/werewolf-audit-20261011-oi45v7af/frontend`.
  Secrets, build outputs and scratch directories were excluded; installed dependencies were shared.
- Built and served that snapshot on port 3137. Existing dev servers and application files were
  left unchanged. The new artifacts are this report, the owner guide and a diagnostic script.
- Reviewed live ingestion, replay/preview controllers, scene lifetimes, painting, animation,
  assets, CSS filters, documentation, unit tests and browser tests.
- Chromium and Linux WebKit exercised the mocked landing/replay and explicit nine-seat workbench.
  Landing viewport: 390×844, DPR 3. Theatre viewport: 844×390, DPR 3; workbench uses its iPhone frame.
- **No physical iPhone run or current Safari memory trace was available.** Chromium uses
  SwiftShader software graphics. Headless layer reports were stale, and some WebKit rAF samples
  were absent. Those layer counts and timings are unsuitable for drawing FPS/GPU conclusions.
  Image dimensions, DOM observations and code-path findings remain useful. This is not a 60-FPS certification.
- Raw browser JSON, build/test logs, asset census and the temporary microbenchmark are in the
  snapshot’s parent directory. The checked-in [census script](../scripts/profile-theatre.mjs)
  reproduces the scenarios; it subsequently gained guards against reporting unsampled layer peaks.
- A durable [evidence summary](frontend-audit-2026-10-11-evidence.json) records both browser
  versions, dimensions, DOM observations, Chromium heap samples and the computation timings.
  Both browser walks reached the replay curtain twice without page errors. WebKit did not
  reliably deliver the offscreen/pause observation in this headless run; do not treat that
  single sample as a diagnosed Safari visibility bug.

### Checks completed

| Check | Result |
| --- | --- |
| Production build, including lint/type validation | Passed; Next 15.5.23 |
| `npm run lint` | Passed, with `next lint` deprecation notice |
| Unit suite in isolated snapshot | 58 files passed, one failed; 1,413 tests passed, three failed |
| Selected existing Chromium live/replay tests | Four passed: first live deal, queued live beats, replay speed, keyboard transport |

The three unit failures are in `src/stage/scenes/night-lobby.test.ts`. They use an implicit
workbench default while expecting nine-seat roles/counts; the snapshot’s default is now the
ten-seat Phase 3 fixture. Pin the legacy fixture in those tests and test the ten-seat default
separately. Do not blindly accept new goldens. Existing work was not rewritten by this audit.

The build reports first-load JS of **376 kB for `/`, 346 kB for a replay, 378 kB for a live
game, and 527 kB for the workbench**. These are Next’s build-reported sizes, not measured heap
or the complete page’s transfer size. Workbench includes fixtures and tools absent from normal routes.

## What is already improved

The October 2 audit is a historical baseline, not a list of current defects:

- `CarScene` now retains the shared dining-car set across scene bodies; `Stage` owns the backdrop.
- Vote and pack no longer rebuild the entire scene on every ordinary beat.
- Night choice lighting uses a zero-duration cut on small stages.
- `Bounded` and the lift’s `box` constrain several moving wrappers.
- Smaller sprite variants and bounded next-speaker decode-ahead exist.
- `useCountdown` only requests a theatre rerender at expiration. The 250 ms visible countdown
  updates live in a smaller consumer; the earlier whole-stage ticking complaint is obsolete.
- The phone-rule test now samples active animations during its window, not only at the end.

Keep these fixes. Also recognize existing visual/motion compromises: small stages use camera
cuts, backdrop cuts, 24-step motion, no grain, no puppet contact filter and simplified ending
arrivals. Further removal of effects or lower motion cadence would conflict with the requested
quality-preserving direction. Some effects could eventually be restored after equivalent,
cheaper rendering has been proven on the phone.

## Prioritized improvements

### 1. Select artwork by displayed physical pixels, not DPR alone — high confidence

[`Backdrop.tsx:42`](../src/stage/instruments/Backdrop.tsx#L42) chooses 1×, 1.5× or 2× from
`devicePixelRatio` and a small-stage cap. It does not include the actual stage scale. That
treats a tiny preview and a landscape theatre similarly despite different pixel needs.

Both engines loaded a **3300×1350** backdrop on the portrait landing, displayed at
**456.5×186.75 CSS pixels**, including its bleed. At DPR 3, its approximate display demand is
**1370×560 physical pixels**. The existing **2200×900** image already exceeds that demand.

| Representation | RGBA8 pixel-buffer estimate |
| --- | ---: |
| Current 3300×1350 | 16.99 MiB |
| Existing 2200×900 candidate | 7.55 MiB |
| Difference per decoded buffer | 9.44 MiB, about 56% |

This arithmetic estimates one uncompressed RGBA buffer, not total memory saved: browser
decodes, GPU copies, tiles and compressed cache entries have their own lifetimes. The source
file can be a few hundred kilobytes while its decoded surface is much larger.

For comparison, the landscape workbench backdrop displays at approximately 953×390 CSS
pixels: at DPR 3 it needs about 2860×1170, so its 3300×1350 asset is reasonable. **Do not apply
a global 1× cap to all phones.**

Expose measured stage scale separately from `useSmall`. Select the smallest asset meeting
`stageScale × DPR × supported camera magnification`, with resize hysteresis so adjacent widths
do not repeatedly replace the image. Keep geometry/layout mode separate from asset density
and motion policy. Small width is not a reliable device capability classification.

Chromium requested both 1× and 1.5× backdrops during initial landing load. Responsive
`srcset`/`sizes`, or a correctly initialized density decision, can avoid that upgrade request.
Verify selection at portrait, landscape, desktop, camera zoom and the full-size card views.

`ChipSprite` always uses the 384×384 head; landing heads sampled here displayed around
31–32 CSS pixels, or 93–97 physical pixels at DPR 3. Introduce size-appropriate head variants
or responsive sources, while preserving larger night-photo/card uses. Static imports in a
manifest do **not** mean every image binary is downloaded: distinguish imported metadata
from requested/decoded assets before splitting all manifests for performance.

### 2. Give the landing preview a resource lifecycle — high confidence

[`FeaturedReplay`](../src/app/(site)/_components/landing/FeaturedReplay.tsx) statically imports
`ReplayTheatre`, fetches the replay immediately and mounts it when data arrives. Intersection
visibility controls autoplay only. In Chromium the preview was below the viewport at y≈996,
already held the large backdrop, and remained mounted after scrolling away; playback did pause.

The preview computes public beats to choose its window, then `ReplayTheatre` computes public
and X-ray cuts again and eagerly folds the entire game into `ahead`, even before a viewer opens
Reveal. This is smaller CPU work than lighting in the measured fixture, but avoidable at landing load.

Recommended sequence:

1. Preserve the carriage dimensions and show a faithful poster of its first frame initially.
2. Conditionally import and mount the existing interactive theatre slightly before it enters
   the viewport. Load the replay at the same boundary, and show it only after required assets
   are ready. Dynamic import alone does not defer mounting/data work if immediately rendered.
3. Pause using both intersection and document visibility. A full replay’s timer currently has
   no page-visibility guard either. On return, preserve replay position; for live sessions,
   maintain server deadline and catch-up semantics while suspending decorative work.
4. After a grace period far offscreen, optionally dispose the preview renderer while retaining
   its cursor, filters and user-paused state outside it. Repeated scrolling must not create
   a mount/decode storm. Pause is cheap to add; disposal should be measured separately.
5. Derive the X-ray cut/full future view on demand if the UI actually needs it. Never trim a
   replay to its visible event window without a checkpoint: earlier events establish game state.

This preserves the interactive experience once visible. A prerendered video would alter the
current controls, seeking and Reveal behavior, so it is an optional product choice, not an
equivalent implementation. [Next lazy loading](https://nextjs.org/docs/app/guides/lazy-loading),
[page visibility](https://developer.mozilla.org/en-US/docs/Web/API/Page_Visibility_API).

### 3. Cache lighting geometry independently of React/SVG IDs — high confidence

[`Stage.tsx:300`](../src/stage/Stage.tsx#L300) has a bounded cache, but its key is
`id + '\0' + JSON.stringify(opts)`. The ID comes from `useId`. A retained Paint instance can
reuse old options, but a newly mounted instance with the same geometry gets a different key.
The comments claiming reuse across instances overstate what it provides.

Separate expensive geometry from final ID-bearing markup. Cache numeric profiles/paths by
semantic options, then bind fresh gradient IDs cheaply per instance. Keep it bounded, ideally
by estimated bytes as well as entry count. This preserves the SVG drawing exactly and avoids
sharing conflicting gradient IDs between a preview, theatre and workbench.

A local Node microbenchmark, 3 warmups and 15 samples on the 407-event fixture, found:

| Operation | Median | Largest sample |
| --- | ---: | ---: |
| Generate a day house-light drawing | 17.37 ms | 26.20 ms |
| Fold complete event log | 0.76 ms | 1.20 ms |
| Generate X-ray beats | 0.98 ms | 2.79 ms |
| Ingest events one by one into the store | 14.63 ms | 17.72 ms |
| Hydrate the same log in one batch | 0.58 ms | 1.11 ms |

These are host computation measurements, not browser frame times or an iPhone speedup claim.
They support prioritizing geometry over a worker rewrite of ordinary small-game event folding.
Precompute truly fixed geometries during the asset build; consider a worker only for dynamic
heavy cases, accounting for serialization, stale responses and scene transition timing.

### 4. Preserve filters’ appearance while reducing their runtime cost — device profiling needed

The full-stage masks have already been replaced. Remaining examples include grayscale heads
in `Wing.module.css`, desktop puppet drop shadows, screened lamp glows in `paint/light.ts`,
and the grade above moving figures.

- Bake equivalent grayscale portrait variants and contact shadows into the asset pipeline,
  where they depend only on the image. Preserve alpha, color-space behavior, shadow padding
  and each lighting variant; compare pixels in both browsers. Load variants only as needed.
- Keep screen-blended glows tightly bounded. A static overlay can still participate in repaint
  or compositing when content below it moves. Retaining its DOM is helpful but not sufficient.
- Do not bake a light overlay into the **background** if it is supposed to darken foreground
  puppets as well: that would change the art. Partition only effects whose layering semantics
  remain identical, or render the relevant group together.
- Prototype one vote-chip/puppet animation with a tight wrapper and browser-driven `transform`.
  Check layer bounds, repaint rectangles and peak memory throughout the transition. Do not add
  `will-change` broadly: overlapping blended layers can make the total cost larger.

`Tween` writes SVG transform attributes from a MotionValue callback. `useSteps` supplies a
JavaScript easing function. Those paths are not proof of compositor-only animation, and 24
distinct positions per second are not guaranteed evenly presented frames. Preserve authored
timing/curves while testing a native keyframe implementation, rather than lowering cadence again.
[Motion performance](https://motion.dev/docs/performance) distinguishes rendering cost from
hardware acceleration; [WebKit’s Layers inspector](https://webkit.org/web-inspector/layers-tab/)
exposes layer memory and paint information needed to assess the tradeoff.

### 5. Optimize live ingestion without breaking reveal/catch-up — medium priority

[`store.ts:99`](../src/game/store.ts#L99) scans for duplicates, copies the event list, builds
a Map and sorts on every accepted event, even an ordinary increasing-sequence append.
`LiveTheatre` then regenerates beats and recreates its fold cache when `events` changes.

Use an increasing-sequence fast path and keep the out-of-order insertion path for withheld
events revealed after game over. Batch catch-up notifications or merge a catch-up block once,
while preserving the history/live boundary and making human input requests prompt. A persistent
fold cache needs explicit invalidation from the earliest inserted sequence; caching merely by
array length would be incorrect. Do not debounce deadlines along with decorative updates.

The 25× difference between isolated store batching and per-event ingestion above is **not**
a promised end-to-end speedup: it excludes React, network delivery and rendering. It identifies
unnecessary work that becomes more relevant on reconnects and larger logs.

### 6. Put bounds around growing history and retained state — lower priority until measured

- `fold-cache.ts` retains every requested endpoint for the controller’s lifetime. Views share
  structure, so this is not automatically quadratic duplication of all event objects, but
  historical arrays and snapshots still consume memory. Consider checkpoints plus a bounded
  nearby-view cache for long games.
- The transcript renders all filtered rows and performs scroll geometry reads in a layout
  effect. Profile long logs with the drawer open before adding virtualization. If needed,
  virtualize by chapter/row with stable keys, measured heights, overscan, and explicit handling
  for follow-to-current, keyboard focus, selection and find-in-page.
- The global session store has `reset`, but normal route cleanup does not call it. One previous
  live log can remain held after leaving. Query caches can simultaneously hold several replay
  responses. This is retention, not proof of a leak. Define ownership/eviction at route or
  session boundaries; avoid erasing an active session during a transient Strict Mode cleanup.
- `staleTime: Infinity` does not itself mean permanent retention. TanStack distinguishes
  freshness from inactive-query garbage collection; use per-query policies for large replay
  responses. [TanStack defaults](https://tanstack.com/query/latest/docs/framework/react/guides/important-defaults).

Two rapid complete public replay walks in Chromium reached the curtain without page errors.
After explicit GC, heap at the curtain was about **9.38 MiB then 9.98 MiB**, DOM elements
489 then 497. That short warmup/growth observation establishes neither a leak nor a plateau.
It does not include decoded image/GPU memory or minutes of thermal load. A longer same-state
soak is still needed.

## Stack and graphics-format decisions

| Option | Recommendation |
| --- | --- |
| Next/React + current DOM/SVG stage | Keep. Fix the measured costs first; React handles app UI and state adequately here. |
| Vite or another React framework | Could simplify a pure SPA deployment, but will not intrinsically change Safari’s painting/compositing of this stage. No migration justified by this audit. |
| PixiJS/WebGL for the scene, DOM for controls/text | A useful bounded experiment if richer smooth phone animation remains a requirement after the above fixes. Port one representative vote scene; compare fidelity, p95 frame time, peak memory, cold load and recovery from lost graphics context. Keep reducers/beats and accessible DOM UI. |
| Canvas 2D | Can consolidate DOM objects, but may require redrawing most of the canvas each frame. Not automatically faster, and interactive text/accessibility needs a DOM layer. |
| SVG for small vectors; WebP for textured rasters | Appropriate already. Separate geometry generation cost from SVG rendering cost. Rasterizing every vector could increase decoded memory. |
| AVIF instead of WebP | Benchmark transfer bytes, decode latency and visual quality on the actual phone. A smaller encoded file of the same dimensions does not inherently shrink its decoded RGBA footprint. No mass conversion justified. |
| Atlases / GPU-compressed textures | Scene-scoped atlases can help a GPU renderer; a giant atlas can keep unused textures resident. GPU compression belongs to that renderer’s resource pipeline, not a drop-in `<img>` source change. |

For a Pixi experiment, use bounded filter areas, deliberate texture ownership/unloading and
preparation before first use; its renderer does not eliminate memory management. These are
also concerns in [Pixi’s performance guide](https://pixijs.com/8.x/guides/concepts/performance-tips).
The [image-format guide](https://developer.mozilla.org/en-US/docs/Web/Media/Guides/Formats/Image_types)
is useful for encoding choices; it does not establish which format decodes fastest on this phone.

## Tests to add, in order

| Test | What it should protect |
| --- | --- |
| Explicit fixture identity | Every beat-index/golden scenario pins its game. Add separate ten-seat and necromancer scenarios. |
| WebKit behavioral project | Run key live/replay, selecting targets, keyboard/touch, portrait/landscape and drawer cases in WebKit with separate visual baselines. Existing config is Chromium-only. |
| Visibility lifecycle | Initial offscreen preview avoids loading renderer/assets; visible starts once; far-offscreen and hidden document pause; returning preserves position and intentional pause; portrait guard does not conceal ongoing expensive playback. |
| Asset density | At representative CSS sizes/DPRs, chosen dimensions meet actual display demand without excessive oversampling; no redundant large initial request. Include full-size cards and camera zoom. |
| Paint cache correctness | Identical semantic geometry across new instances computes once; SVG IDs remain distinct; changing options invalidates; cache stays bounded. |
| Live burst/reconnect | Ordered append, duplicates, out-of-order revealed backlog and catch-up batches produce the same view and beat semantics as the trusted fold; deadlines remain responsive. |
| Scene lifetime | Backdrop/light/wing identities survive appropriate transitions; seek/backward navigation resets only required transient state. |
| Transient effects | Observe entire animation lifetimes including removed exit nodes, rapid target changes, open/close panels, simultaneous winners and card/target selection—not just beat arrivals. |
| Physical-device soak | Production build, cold start, normal/fast replay, long drawer, Reveal, ten-seat night rooms, repeated route changes and background/resume for at least 15–30 minutes. Compare the same settled scene after warmup. |

The current phone-rule gate is useful but still infers rendering cost from DOM geometry and
style writes. It samples at 150 ms, requires multiple sightings, and skips disconnected nodes
at the final check: short or removed exit animations can escape it. Its painted-bounds walk
also adds layout/inspection work, so do not use that run’s timing as a baseline benchmark.
Its prohibition on `will-change` is a conservative policy, not a universal rendering law.

For physical Safari, record renderer/OS/device, viewport, low-power state, temperature/run
order, exact fixture and scene. Use Web Inspector’s Frames/CPU, Layers and Memory timelines;
check paint rectangles and **peak** allocation during transitions. Report median/p95 frame
duration and missed frame deadlines relative to the device refresh rate, not only average FPS.
Use warm and cold runs; thermal degradation is different from a JavaScript leak.
[WebKit memory tools](https://webkit.org/blog/6425/memory-debugging-with-web-inspector/).

Use behavior and visual equivalence as hard CI gates. Establish repeatable device baselines
before inventing fixed memory/FPS thresholds. Linux Playwright WebKit is valuable compatibility
coverage, but not the iOS process or its memory limits. [Playwright browsers](https://playwright.dev/docs/browsers).

## Code ownership and organization

**The top-level separation is good; the frontend is not yet easy enough to own without a map.**
Pure folds, beat generation, reducers, route-local components and shared rendering are useful
boundaries. TypeScript strict mode and substantial behavioral tests are strengths. Avoid a
wholesale folder reshuffle: it creates review churn without fixing responsibility boundaries.

The biggest review obstacles are specific:

| Current file/group | Ownership issue | Suggested split |
| --- | --- | --- |
| `film/Film.tsx` — 1,541 lines; CSS — 1,434 | Chooser, record/docket, notes, reads, precedents and findings in one review surface | `Film.tsx` composition; `FileChooser`, `SeatFile`, `Docket`, individual sections; section-owned CSS |
| `instruments/Wing.tsx` — 797; CSS — 1,073 | Seat rail, tile, role guessing and notebook editing mixed | `wing/Wing`, `WingTile`, `GuessSelect`, `NoteEditor`; keep tile data contracts together |
| `containers/LiveTheatre.tsx` — 696 | Platform lifecycle, live controller, submitting/drafting and scene assembly | Extract cohesive `usePlatformTransition` and `useTurnActions`; keep the live reducer as authority |
| `instruments/` | Motion primitives, HUD, scene props and editing controls coexist | Gradually group `motion/`, `hud/`, `props/` as those components are changed |
| `assets/manifest.ts` — 962 | Large manual import surface | Group by asset family or generate typed handles from asset metadata; retain a stable public facade |
| `docs/` | Current contracts interleaved with historical observations and design bundles | Short current architecture/ownership guide; chronological decisions/evidence under history/ADRs |

Line count is a review signal, not a mandatory component-size limit. Keep tiny implementation
helpers local. Split when responsibility, state lifetime, CSS ownership or testing boundary
differs. `Film`’s pure models are already separate; build on that rather than moving UI logic
into an undifferentiated `utils` directory.

A gradual target, preserving familiar names:

```text
src/
  app/                       # routing and route-local page composition
  game/                      # event model, fold, session store
  hooks/                     # application/query/stream lifecycle
  lib/                       # API, keys, configuration, persistence
  components/site/           # shared website UI
  stage/
    Stage.tsx, units.ts, set.ts
    beats/                   # event -> presentation sequence
    containers/              # live/replay controllers and pure reducers
    scenes/                  # picture composition and set lifetime
    paint/, cast/            # geometry and character drawing
    instruments/
      motion/, hud/, props/  # group by responsibility as touched
    film/sections/, drawer/
    workbench/
  assets/                    # sources + generated variants/typed handles
  types/contracts/           # generated server boundary
```

Enforce dependency direction in ESLint: `game` must not import stage/routes; pure beat/model
modules must not depend on UI; scene rendering should not introduce HTTP calls or store
writes; workbench fixtures must not enter production route graphs. Keep exceptions deliberate
and small. A renderer experiment is much cheaper when those boundaries are real.

### Documentation quality, not comment quantity

There are already many docstrings. The issue is historical narrative and claims stronger than
the code proves. For example: `Paint` says cross-instance caching; `CarScene`/`set.ts` imply
remount always means redecode; `Bounded` says browsers always repaint the entire box; phone
motion comments imply guaranteed steady 24 FPS. These should describe observed conditions
and intended policy, with a link to dated evidence, not promise browser internals.

Keep a module header to purpose, inputs/outputs, state lifetime and one or two critical
invariants. Put JSDoc on public props, coordinate spaces, units, privacy/entitlement contracts
and surprising cache/cleanup rules. Explain **why** near an unusual key, portal or effect.
Move historical explanations into dated decisions. For example, the cache contract should
explicitly say whether an ID affects reuse, what invalidates it and how its memory is bounded.

`docs/stage_architecture.md` alone is about 1,000 lines and `build_log.md` about 1,300. They are
valuable references, but not a first reading assignment. The new [owner guide](../README.md)
provides a shorter route through the code and names the invariants to protect. Scratch files
under `src/__tmp` and the accidental `undefined/` output should eventually move outside source
and test discovery after their owner’s ongoing work is finished.

## Recommended implementation order

1. Pin fixture assumptions and establish WebKit/device baselines; retain current artwork.
2. Correct preview asset density and defer preview resources until near visibility.
3. Separate lighting geometry caching from SVG IDs, with fidelity and lifecycle tests.
4. Bake equivalent filtered variants, then profile one bounded native animation on the phone.
5. Add the live append/batch fast path and bounded history policies where larger logs justify it.
6. Refactor Film/Wing/live-controller responsibilities in separate reviewable changes.
7. Only then compare a single Pixi-rendered scene against the optimized DOM scene if the
   desired phone motion still cannot meet the measured frame/memory budget.

Each change should include before/after measurements at the same fixture and transition,
visual comparison, and an explicit preservation of seek, input, Reveal and catch-up semantics.
