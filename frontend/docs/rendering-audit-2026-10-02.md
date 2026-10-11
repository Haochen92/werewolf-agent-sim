# Rendering audit — 2026-10-02

The code and controlled browser measurements identify several rendering costs before any Safari-specific diagnosis is needed. They do not establish the cause of an iPhone process termination or a safe GPU memory budget.

## Scope and reproducibility

- Read-only investigation of application code. No application changes made by this audit.
- Copied `frontend/` into `/tmp/werewolf-render-audit-iCQcH8` at the start; built and served that isolated production snapshot on port 3129. The production build completed successfully.
- Repository HEAD was `04005ca09953939a4b81d8ad40ca547efed6d11e`. The snapshot also contained the in-progress light blend-box change and small image files, before the later scene-persistence, decode-ahead, and stepped-motion edits. Those files were not yet connected throughout the renderer.
- Headless Chromium, viewport 1200 × 850, device scale factor 3, workbench `frame=iphone14`, `hud=replay`, animation enabled. CPU throttled 4× for traces and browser generator measurements.
- The host's renderer is ANGLE/SwiftShader, **software graphics**. Results show costs and differences on this host, not predicted iPhone FPS or Safari GPU allocation.
- 42 transition captures: three repetitions of four lighting variants for day 0→1, vote 14→15, and pack 0→1; three repetitions of baseline and hidden light/grade for vote 5→6. The latter is the counted-chip transition. Vote 14→15 is table-down→next voting-open, not a counted chip.
- Scripts, source snapshot, build log, trace JSON and measurement JSON remain in the temporary directory. `trace-audit.cjs`, `diagnostic.cjs`, `browser-math.ts`, `results.json`, `chip-count/results.json`, and `diagnostic-results.json` contain the main evidence. `night-choice-layers.json` contains the successful night-selection observation. The later `choice-audit.cjs` interception did not establish a selective-animation ablation; do not use its results to attribute the layer increase to one effect.
- Timings are short samples, not a device certification. Variant order was fixed, so warm-cache/order effects remain possible. Raster durations below sum worker task durations and can overlap in wall time. Paint, layout, JavaScript and animation-event totals must not be added indiscriminately because trace events can nest. Recorded requestAnimationFrame intervals are not presented-frame measurements and are not reported as FPS.

## 1. Lighting geometry is generated synchronously in React render

`Stage.tsx`'s `Paint` calls the generator in a component-local `useMemo`. `paint/light.ts` invokes `lightHoles` and `softHoles`; `paint/holes.ts` numerically constructs blur profiles, overlap helpers, a grid partition and traced SVG paths. Remounting the component loses that memo.

Browser microbenchmarks, 4× CPU, 3 warmups and 15 samples per function:

| Operation | Median ms | Largest sample ms |
| --- | ---: | ---: |
| Day light holes/profiles | 5.1 | 7.7 |
| Day light overlap/path geometry (`softHoles`) | 52.3 | 79.6 |
| Complete day light markup | 57.7 | 65.5 |
| Wolf room light markup | 13.1 | 14.9 |
| Wolf target light markup | 7.0 | 9.0 |
| Fold the complete fixture event log | 1.2 | 2.2 |
| Generate the fixture's public replay beats | 1.5 | 2.5 |

Instrumenting the actual production `Paint` call, without changing its output, observed **109 ms** generating the house light on vote 5→6 (`vote.chip-counted`, third chip). A pack 0→1 transition spent **69.8 ms** generating its room light. These are individual transition observations, not medians; microbenchmark warmup and runtime conditions differ.

Day 0→1 invoked **no new Paint generators**, demonstrating that its persistent set already avoids this work. It can still be rasterized again during animation.

Action: preserve static Paint instances and cache/precompute geometry by semantic lighting inputs. Separate generated IDs from reusable geometry; blindly sharing complete SVG strings risks gradient ID collisions. Move genuinely static art preparation out of interaction-time rendering. A bitmap is one option, but cached vector paths can remove generation cost without an additional decoded full-stage image.

## 2. Scene keys replace most of the visual tree

Counted existing descendants under `[data-layer]` before a transition, then checked which exact nodes were disconnected afterward:

| Transition | Replaced / previous descendants |
| --- | ---: |
| Day 0→1 | 121 / 220 |
| Vote 14→15, next vote opens | 441 / 444 |
| Vote 5→6, next counted chip | 385 / 388 |
| Pack 0→1, packmate's line | 402 / 403 |

Day's changing turn is deliberately replaced while its lighting and backdrop survive. The baseline vote and pack replace almost everything: `VoteScene` keys `VoteBeat` by beat/ordinal, and `PackScene` keys the component containing `NightRoom` by beat and turn props.

Action: retain room, wing, lights and unchanged instruments; restart only the specific animation or interaction state that requires it. Preserve seek, backward navigation, selection reset and replay semantics when changing keys.

Concurrent workspace edits observed during the audit already remove the vote's beat/ordinal key and change several other scene lifetimes. The measurements above describe the saved baseline, **not a regression test of those new edits**. Pack's whole-room key was still present at the final source check.

## 3. Overlays increase raster work during movement

Median summed RasterTask time in the capture window, three runs per condition:

| Transition | Baseline ms | Hide light ms | Hide grade ms | Hide both ms |
| --- | ---: | ---: | ---: | ---: |
| Day 0→1 | 2005 | 1674 | 1725 | 1173 |
| Vote 14→15, next vote opens | 4126 | 3588 | 3985 | 2569 |
| Pack 0→1 | 195 | 180 | 118 | 114 |
| Vote 5→6, next counted chip | 617 | — | — | 201 |

These CSS subtraction experiments hide rendering but leave the React/generator path in place. They support a rendering cost from both the house light and the grade; removing the house light alone is not the complete treatment. The snapshot already contained the tighter glow bounds.

For the counted chip, median Layout time remained 161.5 ms baseline versus 188.6 ms with both overlays hidden; decoded-image work was essentially unchanged, 23.1 versus 23.2 ms. Therefore the overlay subtraction did not eliminate other work. Those small-sample differences are not evidence that removing lighting intrinsically worsens layout.

Action: reduce repeated redraw area and expensive foreground effects. Investigate a bounded independently animated chip/card surface, while maintaining correct occlusion. Measure both initial transition work and the remaining movement separately.

## 4. The animation paths are not uniformly compositor-driven

`Tween.tsx` animates a MotionValue, then writes an SVG `transform` attribute and opacity from JavaScript callbacks. `VoteTable.tsx` uses this for chip flight, face changes and other details. This is not a guarantee of an independent compositor animation. `Lift.tsx` moves a 1600 × 900 load wrapper regardless of the visible load's size, and the phone explicitly removes its `will-change` hint.

The architectural tradeoff is real: reducing promotion can reduce layer allocation while leaving more work during movement. A giant scaled world is not automatically wrong; the relevant questions are the browser's actual layer bounds, raster scale, invalidation and effect dependencies.

Action: prototype a tightly bounded HTML/sprite wrapper animated with a browser-driven transform. Confirm that motion avoids repeated layout/paint and that overlapping content does not create unacceptable backing surfaces. Moving an existing full-stage wrapper to a higher z-order does not make its bounds small.

## 5. Night selection still produces a substantial transient layer increase

On settled `/workbench/pack?beat=3&animate=1&frame=iphone14&hud=replay`, selecting Seat 4 produced:

- A running **600 ms opacity animation** on the `light` layer's 1600 × 900 element; displayed bounds were about 693 × 390 CSS pixels.
- Several simultaneous photo opacity animations.
- Layer-tree count **12 before → 30 at peak → 11 after** in the successful observation. The peak included multiple content layers around 2200 × 900 logical units.

This confirms a transient compositing cost, not Safari memory consumption or proof of a crash. The simultaneous photo animations mean the increase cannot be attributed solely to the light fade.

`NightRoom.tsx` uses a full-stage `motion.div` for `roomChoice`. The phone-rule test checks `document.getAnimations()` after its 3.2-second watch. Its mutation observer detects attribute writes, but a short WAAPI animation can complete without per-frame style writes and be absent when checked. A test can consequently miss this class of temporary layer increase. The concurrent remount-check addition does not by itself close that timing gap.

Action: monitor animations and layers during their lifetime, including user selections, rather than only after arrivals settle. Test a phone cut for the choice overlay or a smaller representation, then inspect visual quality and peak layers on iPhone.

## What these results deprioritize or leave open

- Event folding and beat generation are inexpensive for this fixture relative to lighting generation. Larger games or live event bursts are not ruled out. LiveTheatre also recreates its fold cache when the event array changes and rerenders for its 250 ms countdown: secondary candidates to profile if live remains worse than replay.
- A remount does **not** prove that an image was decoded again. Warm pack traces recorded zero `Decode Image` work while the transition still rebuilt the room. Decode-ahead cannot fix SVG geometry computation, layout, or repainting an already decoded image.
- Phone-sized images remain useful. The census found 384 × 384 heads displayed as small as approximately 23 × 23 CSS pixels at DPR 3. The 3300 × 1350 backdrop was displayed around 953 × 390 CSS pixels including bleed, so its oversampling here was much less severe than those tiny heads. No raster-resolution ablation was performed; relative impact is unproven.
- The new workspace `PHONE_FPS = 24`/stepped easing reduces distinct motion positions by design. It is a quality/performance tradeoff, not evidence that the renderer can now sustain 60 FPS. Quantizing values does not guarantee evenly presented frames or eliminate animation callbacks. Evaluate it separately from structural fixes.
- No iPhone crash logs, Safari trace, physical-device peak memory, long-running replay, or real live network/event session was available in this audit. Safari-specific bugs, resource ceilings and leaks remain unproven and cannot be eliminated here.

## Recommended architectural order

1. Finish retaining room/set components and remove repeated lighting geometry generation.
2. Address short full-stage fades and verify transient layer peaks, including target selection.
3. Prototype bounded compositor-driven chip/card motion while retaining required occlusion.
4. Optimize grade/lighting redraw and image resolution using measured device results.
5. Assess optional lower-motion quality separately. Consider a different scene renderer only after the bounded prototype establishes what the phone can do.

References: [WebKit layer tradeoffs and inspection](https://webkit.org/web-inspector/layers-tab/), [Motion rendering and animation execution](https://motion.dev/docs/performance), [Chrome profiling and CPU-throttling limitations](https://developer.chrome.com/docs/devtools/performance/reference).
