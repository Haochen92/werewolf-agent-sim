# Assessment: area C, lessons, audits and timing

Scanned 2026-10-26, read-only. Documents: `frontend_lessons.md` (whole), `phone_lessons.md`,
`principles.md`, `build_log.md` §8, `live_timing_sheet.md`, `stage_fit/README.md`,
`frontend-audit-2026-10-11.md`, `rendering-audit-2026-10-02.md`. Stories 7 (latency as tempo) and
10 (the live view had to survive a phone). Code checks were made by reading only.

## Summary table

| Document | Kind and status | Main issue | Feeds | Proposed action |
|---|---|---|---|---|
| `frontend_lessons.md` | Lesson doc, the log; living (last change 2026-10-22) | 50 numbered entries (29 is used twice) and 23 unnumbered "small things". Lesson 12 describes a cache key the code did not have until lesson 36 fixed it. Lesson 39 still says "Not deployed yet" | Learning track (all topics); story 10 | Keep as the log. Label the two 29s as 29a and 29b in place. Dated notes on 12 and 39. Place every entry (table in §6 below) |
| `phone_lessons.md` | Lesson doc, the first walk; dated record (2026-10-01 to 10-02, one 10-11 update) | Leaves out the real first crash (five full-stage SVG masks, build_log §8.1) and calls the layer cascade "the whole first crash". Lesson 5 says scenes are "still keyed whole", which §8.9 fixed the same day. Says "Eleven lessons" and has twelve | Story 10; rendering_pipeline, memory_and_pictures, performance_method | Light edit (passages named below). It becomes the template for the topic docs |
| `principles.md` | Lesson doc, to become the index; dated 2026-10-15 | Cites 30 lesson numbers, not the brief's 21. It stops at lesson 37 because lessons 38 to 49 came after it. "The October audit" and "the survey" are ambiguous | Learning track (the index); realtime_and_sync (§6, §7) | Rewrite as the index of `learning/`: one section per topic doc, keeping its principle lines and "Read" lists |
| `build_log.md` §8 | Journey log; dated record (2026-10-01 to 10-02) | Four claims were later overturned and carry no dated note (§8.2, §8.6, §8.8, §8.10 "Next"). §8.3 still has a "[pending the owner's reading]" placeholder | Story 10 (its primary source); five learning topics | Keep whole. Add a section index (below) and four dated notes |
| `live_timing_sheet.md` | Design record (the owner's rulings, 2026-10-01) with one game's measurements; living rulings | The head note says stage_fit "measured the lag again". stage_fit measured the opposite gap: the stage waiting for the model. Extraction at game over has been offline since 2026-10-12 | Story 7 (spine); story 4 (ruling 6); realtime_and_sync (ruling 4) | Light edit: reword the head note; dated notes on extraction and on the §4 solo row |
| `stage_fit/README.md` | Dated measurement record (2026-10-24); rerunnable | Close to the report standard. "Replaces the one earlier measurement" overstates in the same way as the timing sheet. The text gives "today's 5.5 s median" where its own table says 5.4 s | Story 7 (the measured figures) | Light edit: two sentences. Optional: report the lag (how far the stage runs behind) from the same simulation |
| `frontend-audit-2026-10-11.md` | Dated audit plus a follow-up of 2026-10-15; dated record | The follow-up lists the half-open stream as "Open", but it was fixed the same day (multiplayer finding 7). Its "Documentation quality" paragraph names four over-claims, and three recur in the lesson docs | Story 10; stories 1 and 4 from the client side (§5); six learning topics | Status line, with one dated note on the dead-stream item |
| `rendering-audit-2026-10-02.md` | Dated audit; superseded (taken into build_log §8.9 and §8.10 on 2026-10-02; called "a historical baseline" by the 10-11 audit) | None as a record. Its scope section is the clearest statement of measurement limits in the folder | Story 10 (lesson 19's audit read as claims); performance_method | Four-line card (below) and a status line |

## Per document

### frontend_lessons.md

- **Kind and status.** The lesson log, about 8,600 words. Living: lessons 46 to 49 were added
  2026-10-22. Entries 1 to 20 were written on 2026-10-02 out of build_log §8 (§8.10 calls the file
  "twenty entries"). Lesson 21 was added 2026-10-04 and 22 to 49 from 2026-10-11 to 2026-10-22. So
  the brief's "lessons from 32 on are dated October" should read: every lesson is from October;
  1 to 20 are the §8 batch, and 21 on are later.
- **Shape.** 50 numbered entries: 1 to 49, with 29 used twice. 29a is "a baked copy ... must cover
  everything the computation reads" and 29b is "a dynamic component's code starts loading at its
  first render". Two short opening mechanisms, "re-render and remount" and "a frame is drawn in
  three steps". One worked case box, "The carriage case, 2026-10-15" (29b to 31). Then a closing
  list, "Small things that cost an afternoon", of 23 unnumbered items that the brief's §6 does not
  place.
- **Reader question.** What general frontend rule did each mistake here teach, and where in the
  code can I see it?
- **Currency.** This is not a design record, so its mechanism claims are not graded. The code
  anchors a topic doc would reuse were checked for existence:
  - Present: `frontend/src/hooks/catch-up-boundary.ts::catchUpBatch`,
    `frontend/src/stage/containers/fold-cache.ts::grow`,
    `frontend/src/stage/containers/live-state.ts::keepSame`, `::runOf`,
    `frontend/src/stage/Stage.tsx` (`measured`, `drawn`),
    `frontend/src/stage/instruments/Backdrop.tsx::pickScale`, `::sheetFor`,
    `frontend/src/app/(site)/_components/landing/FeaturedReplay.tsx` (`theatreCode`, `painted`,
    `lifted`, `covered`), `frontend/src/stage/film/record-model.ts::shownMorning`,
    `frontend/src/stage/film/case-file.ts::shownSeat`,
    `frontend/src/stage/beats/beatsFor.ts::atStand`, `frontend/src/stage/cast/Puppet.tsx`
    (`rising`), `frontend/src/stage/instruments/TurnDock.tsx::useTyped`,
    `frontend/src/music/player.ts` (the `interrupted` rebuild), and the instruments `Bounded`,
    `CountText`, `Flip`, `useHydrated`, `PageGate`, `DecodeAhead`, `ahead`.
  - Paths given short in the text: `motion.tsx` is `frontend/src/stage/motion.tsx` (`stepped`,
    `PHONE_FPS = 24`). `guide/useNear.ts` is under `frontend/src/app/(site)/_components/guide/`.
    `DockInput` is a type in `frontend/src/stage/scenes/types`.
  - Not in the repo: lesson 33's render-census hook (a stand-in `__REACT_DEVTOOLS_GLOBAL_HOOK__`).
    The `day-drift.mjs` and `mem-walk.mjs` walks behind lesson 19 are also absent. A topic doc's
    "see it yourself" step has no script to point at for these.
- **Faults.**
  - **Lesson 12 against lesson 36.** Lesson 12 (2026-10-02) says "a bounded FIFO keyed by the
    generator's inputs makes a repeat free" and that keying by an instance id "would" miss. The
    code keyed on `useId` plus the options until `f30d4496` (2026-10-15). The 10-11 audit §3 says
    "the comments claiming reuse across instances overstate what it provides", and lesson 36
    records the fix. Lesson 12 therefore described the intended key, not the built one. Add a
    dated note to 12 pointing at 36, and make them one lesson in the topic doc.
  - **Lesson 39** ends "Not deployed yet." The mechanism is in the code (`FeaturedReplay.tsx`:
    `painted`, `PAINT_CAP_MS = 8000`, `TrainLoader`). Replace the line with the deploy state and its
    date. The owner confirms the commit; the scan cannot.
  - **Lesson 23** says "the chunk only since 2026-10-15, see 29", which is ambiguous. It means 29b.
  - **Lesson 31's second half** ("Why compression and streams are kept apart") says the exact
    mechanism behind Cloudflare's hold "is a guess". build_log §1.4 (2026-08-21) states it as fact
    ("transforming is what its buffering hangs off") and settles the header on "the `/api` block".
    Since 2026-10-15 the header sits on the stream's route only. See the overlaps below.
  - **Lesson 14** says stepping "gives each frame 42 ms and a steady beat". The 10-11 audit §4:
    "24 distinct positions per second are not guaranteed evenly presented frames." The lesson
    already calls it a presentation choice. Change "gives" to "aims at".
  - **Lesson 8** ("the browser repaints the moving box") rests on build_log §8.10. There, on
    Chromium, the fix cut paint records (the table's sink from 88 to 22) but barely moved raster
    (the vote over 15 steps, 10,489 to 10,341 ms), and "the phone's reading is the owner's" was
    never recorded. Keep the rule, and state what was measured.
  - **The head** says "The dated numbers are in `build_log.md` §8". That is true for 1 to 20 only.
    The numbers for 32 to 37 are in the 10-11 audit's follow-up, and later lessons carry their own.
  - **The voice.** The lessons say "we" ("We keyed each scene on its beat"), and one small thing
    is in an agent's first person ("mine failed to start"). That suits the owner's notes. Any
    chapter C sentence drawn from them must follow the constraint: agents built the code to the
    owner's specs.
- **One-home conflicts.** Listed in the area-level overlaps (lighting cache, catch-up batching,
  typing redraw, the backdrop pick, the Cloudflare header).
- **Feeds.** Every learning topic. Story 10 (lessons 1, 2, 8 to 11, 13 to 17, 19). Story 1 from the
  client side (31's stream half, 32). Story 4 from the client side (21, 24, 32, 35).
- **Proposed action.** Keep it as the log. Label 29a and 29b in place; do not renumber, because
  principles, phone_lessons and the 10-11 audit cite the numbers. Add dated notes to 12, 14 and 39.
  Fix the head pointer and lesson 23's reference. Number the small things S1 to S23 so the
  placement table can cite them.
- **Terms used before definition.** beat (lesson 1), the set, the wing, the host (2), the stand
  and the plate (7), the composer (5), the workbench and the `gpu=` switches (15), the Record and
  the seat chooser (21), passes and a run of passes (24), the carriage (23, 29b), the dock and the
  side slot (33, 34), the folds (35, defined in passing), observer-tier (41), Reveal (43), the deal
  and the reel (46, 48), the slates (26), golden (42, small things).

### phone_lessons.md

- **Kind and status.** Lesson doc, about 2,800 words: the first walk, and the form the brief adopts
  for every topic doc. It is a dated record of 2026-10-01 to 10-02, with one 2026-10-11 update in
  lesson 3. It has twelve lessons and an "If you are asked about it" paragraph.
- **Reader question.** Why did the stage die and stutter on an iPhone, what was the browser doing,
  and how do I see it myself?
- **Currency.** Not a design record. Story 10's load-bearing mechanisms were checked by reading:
  - The set and beat split, one host for the car: `frontend/src/stage/scenes/CarScene.tsx`.
  - Moves stepped at 24 a second on a phone: `frontend/src/stage/motion.tsx::stepped`,
    `::useSteps`, `PHONE_FPS = 24`.
  - Bounded movers: `frontend/src/stage/instruments/Bounded.tsx`.
  - The gate: `frontend/e2e/phone-rule.spec.ts`. It samples `document.getAnimations()` every
    150 ms and fails a large element seen animating in two samples.
  - The probe: `frontend/src/styles/gpu-probe.css`.
  - The guard against `<mask`: `paint.test.ts` and `atmosphere.test.ts`.

  All of these are present and match the text.
- **Faults.**
  - **The first crash is told wrong.** build_log §8.1 records two separate crashes. The first, from
    the redesign's deploy on 2026-09-28, killed every stage page at once: five full-stage SVG
    `<mask>` elements, found with the `nomask`/`nosvg` probe words and fixed with evenodd vector
    sheets. The second (§8.3) was rate-dependent: the scene rebuilt each beat, and the layer
    cascade at rest (17 layers, 534 MB). Lesson 1 cites §8.1 for the symptom and §8.3 for the
    numbers. Lesson 2 calls the felt country "the whole first crash". The closing paragraph says
    "the first crash was one small animation that cost 300 MB through the layer cascade". The mask
    crash, a platform limit on one technique, has no lesson at all. Add it as a lesson (or as
    lesson 1's first half), and correct lesson 2 and the closing paragraph.
  - **The head says "Eleven lessons"**; there are twelve.
  - **Lesson 5's fix line** says "the vote, lynch, night, deal, game over and replay night are still
    keyed whole and are the next thing to split (§8.3, §8.8)". §8.9 split them the same day under
    `CarScene`, and lesson 11 of this same file records it. Only the deal's and the ending's figures
    are still keyed per beat (§8.10).
  - **Lesson 10's gate** ends "so the class stays closed without anyone remembering the rule".
    There is no CI. The gate keeps the class closed only when someone runs it (lesson 10's own
    "see it yourself" step, with the dev server up). Say so.
  - **Lesson 11** says the phone "repaints on a steady beat with 42 ms for each frame". That is the
    intended policy, not a guarantee (10-11 audit §4 and its documentation-quality paragraph).
  - **Lesson 12** says the repaint "is the figure's column, not the stage". The same limit applies
    as for lesson 8 above.
  - **Lesson 8** says "the 18 MB sheet is decoded again each beat" only through build_log §8.8.
    The rendering audit (2026-10-02, "What these results deprioritize") observed that "a remount
    does not prove that an image was decoded again". Its warm pack traces recorded no
    `Decode Image` work. The black frame itself is the device's observation and stands.
- **Against the topic-doc form (brief §6).** Each lesson has "what you saw", "what was happening",
  "what fixed it" and "see it yourself". It lacks the rule line and the reading. `principles.md`
  holds both, by topic. It also cites build_log sections instead of the lesson number and the code
  symbol. Topic docs built on this form should add those three parts.
- **One-home conflicts.** Lessons 1, 2, 5, 6, 8 to 12 retell frontend_lessons 1, 8 to 11, 13 to 16
  and build_log §8.3 to §8.10. This is intended: phone_lessons is the walk, build_log the numbers,
  frontend_lessons the general rule. When the topic docs exist, each phone lesson moves into its
  topic, and this file can stay as the dated phone case study that links to them. Owner's choice.
- **Feeds.** Story 10 (the whole file; the closing paragraph is the interview answer). Learning
  topics: rendering_pipeline (1, 2, 6, 7, 9, 12), memory_and_pictures (3, 4, 8), react_identity
  (5), performance_method (10, 11), stage_motion (9, 11, 12).
- **Proposed action.** Light edit: the mask crash, lesson 2, the closing paragraph, the lesson
  count, and the passages on lesson 5, 10, 11 and 12 named above. Then it is the first walk.
- **Terms used before definition.** the theatre, the stage, beat, the set, the wing, the HUD, the
  camera, the grade, the light, the workbench, the census probe, the X-ray (through Reveal),
  `data-small`.

### principles.md

- **Kind and status.** Lesson doc, about 1,500 words, written in one commit on 2026-10-15
  (`c8f07bc5`). It has eight topics, each with principle lines, the lessons they came from, and a
  "Read" list. It is to become the index.
- **Reader question.** What general rules did this project teach, by topic, and what should I
  read to learn each topic properly?
- **Lesson coverage (correcting the brief).** It cites 30 lesson numbers, not 21: 1, 3 to 12, 14
  to 17, 19, 22, 25 to 37. Its "29" (§5) is 29b by content. The 20 entries it does not cite are
  2, 13, 18, 20, 21, 23, 24, 29a and 38 to 49. Twelve of those 20 postdate the file. It also cites
  two small things (`'use client'` and the z-index tie), multiplayer findings 4, 5, 7, 8, 9, 11 and
  "What is solid", `useGameStream`, `store.ts`, `testing.md` and timing-sheet ruling 4.
- **Currency.** §6's "Liveness needs a heartbeat the client can hear and a watchdog that acts on
  silence" is built: `frontend/src/hooks/catch-up-boundary.ts::streamStalled` reopens a stream
  silent past `STREAM_SILENT_MS` (40 s) and retries a closed one after 10 s.
- **Faults.**
  - "The October audit" (§2, §5) is ambiguous: there are two, 2026-10-02 and 2026-10-11. It means
    the 10-11 audit (§6 bounded caches; the follow-up's font preload).
  - §8's "the survey's 'phone copies of the lobby pictures', measured, came to files only about a
    tenth too big" cites lesson 19. Lesson 19 says nothing about lobby pictures, and "the survey"
    is undefined (perhaps the 10-11 follow-up, which calls itself "a survey"). The source of the
    "a tenth" figure was not found in this area's documents. It needs a source or removal.
  - §7 (multiplayer authority, side channels, check-then-act, rejected against failed, the player
    who leaves) is server-side. It feeds stories 3, 8 and 9 (area A) more than any client topic.
    See "placement unclear".
- **One-home conflicts.** None of its own. It summarises and links, as an index should.
- **Feeds.** The learning track (the index for all topics); realtime_and_sync (§6, §7).
- **Proposed action.** Rewrite as the index of `frontend/docs/learning/`. Give one section per
  topic doc, keep each principle line and the "Read" list, link the topic doc instead of the
  lesson numbers, and add the principles for lessons 38 to 49 (most go to loading_and_deploy and
  performance_method). Resolve "the October audit" and "the survey".
- **Terms used before definition.** None of consequence: it is written for a reader who has read
  the lessons. The topic docs it will index must define the terms themselves.

### build_log.md §8 (lines "The stage on a phone", 2026-10-01 to 10-02)

- **Kind and status.** Journey log, about 5,800 words of the file's 14,700, in ten dated entries.
  Each keeps the build log's shape: seen, mechanism, cost, settled. Dated record. Severity marks
  (🔴) are in two headings; it is a log, so leave them.
- **Reader question.** What happened, in what order, with what numbers, when the Playhouse stage
  met an iPhone?
- **Currency.** This is a journey log, so it is not rewritten. Story 10 depends on it, and four of
  its claims were overturned later without a dated note:
  - **§8.2** says "motion runs on the compositor". §8.4 found the opposite two days later, after
    reading motion's source: motion writes `style.transform` from script, so no layer. Phone
    lesson 7 and lesson 40 agree with §8.4. Add a dated note in §8.2.
  - **§8.6** says "Chromium's layer tree is no longer readable over the protocol". The small
    things list (2026-10-22) corrects this: headless Chromium counts layers over CDP
    (`LayerTree.enable`). Add a dated note.
  - **§8.8** states that "the 18 MB sheet is decoded again each beat". It needs a note giving the
    rendering audit's observation (above, under phone lesson 8).
  - **§8.10 "Next, by the readings"** lists five items. Three were done later:
    - grouping the catch-up frames: lesson 32, `catchUpBatch`, 2026-10-15;
    - `turnInput` fresh each render: lesson 33;
    - the light's cache keyed by geometry: lesson 36, `f30d4496`.

    The deal's and the ending's per-beat figures are still open. Rows in view only is still
    unbuilt; the 10-11 audit §6 says profile it first. §8.10 also says frontend_lessons has
    "twenty entries", and it now has 49. One dated as-built line covers all of this.
  - **§8.3** keeps a placeholder, "After the split: _[pending the owner's reading]_". The next
    paragraph answers it ("The split did not move the floor"). Replace the placeholder with a
    pointer to that paragraph.
- **Numbers and their N, for the write-up.**
  - "Seventeen layers and 534 MB became one and 114 MB" is one reading on the owner's iPhone over
    Safari's Web Inspector, of one page state (the replay at "before day 1", at rest), on
    2026-10-02.
  - The GPU route's "about 670 MB, and the tab died" is one reading on the same phone.
  - The vote's raster, 67,480 to 23,064 ms over 41 steps, is Chromium in the phone frame with the
    CPU throttled four times, production `a3d6404` against `fbaef8c`. It is not a phone figure.
- **Proposed section index** (a header block for §8; "Feeds" uses the topic names of brief §6):

| Section | Content | Feeds |
|---|---|---|
| §8.1 | Every stage page killed: five full-stage SVG masks; the subtraction probe; who did what | Story 10; rendering_pipeline; performance_method; playbook (measured performance work) |
| §8.2 | Where the art pipeline stands against production practice (with the compositor claim to correct) | Story 10; memory_and_pictures |
| §8.3 | Fast beats killed the page: the scene keyed per beat; the set and beat split; the bake; the inspector's layer table (534 MB to 114) | Story 10 (its central numbers); react_identity; rendering_pipeline; memory_and_pictures |
| §8.4 | The jar and shutter: an SVG transform attribute against a CSS transform on an HTML box | rendering_pipeline |
| §8.5 | The camera's move repaints the world: cut on a phone; raster per transition | stage_motion; rendering_pipeline |
| §8.6 | Three things still animating at rest; the census instead of a layer readout | rendering_pipeline; performance_method |
| §8.7 | The rule becomes a gate (`e2e/phone-rule.spec.ts`); the sweep's whole list in one batch; one flag for "a phone" | Story 10 (the method); testing; performance_method |
| §8.8 | The black frame: the backdrop remounted; one backdrop owned by the Stage; `decoding="sync"` | react_identity; memory_and_pictures |
| §8.9 | The stutter left: one host for the car, 24 steps a second, the GPU route measured and refused, the picture census; the second pass from the rendering audit; before and after table | Story 10; react_identity; rendering_pipeline; memory_and_pictures; stage_motion; performance_method; testing ("Verified") |
| §8.10 | The box, not the figure: bounded movers; the day-4 walk (no per-beat growth); the countdown as a leaf; test waits sized to the stream | Story 10; rendering_pipeline; react_identity; testing; realtime_and_sync (catch-up cost) |

- **One-home conflicts.** It is the home of the numbers. phone_lessons and frontend_lessons
  summarise it and link to it, and the file says so. Keep it that way.
- **Feeds.** Story 10 (primary). Learning topics as in the index above.
- **Proposed action.** Keep whole. Add the section index and four dated notes (§8.2, §8.6, §8.8,
  §8.10), and replace the §8.3 placeholder.
- **Terms used before definition.** the X-ray and Reveal (§8.6), `data-small` (§8.5), the strip,
  the wing, the bleed, the drape, the valance, the pelmet, the lift, the shelf room, the pack, the
  workbench words.

### live_timing_sheet.md

- **Kind and status.** Design record, about 3,100 words: the owner's six rulings (2026-10-01),
  derived from one real game's timings. The rulings are living, and three carry dated build notes.
  The measurements belong to one game: `553a1875`, solo, the human a wolf at seat 1,
  `gemini-3.5-flash-lite`, memory on, 527 durable events.
- **Reader question.** When the server emits each event, what each viewer's stage does with it,
  and how far each stage runs behind; and which tempo rules follow.
- **Against the design-record standard (brief §4).** It states the tension (agents answer in
  about 6 s and are read in 12 to 15). It derives the mechanism with concrete rows. It rules, and
  it records the rejected alternatives in ruling 4 (a cursor acknowledgement and a pull model, set
  aside because the table would wait on its slowest reader). It also says what is held (ruling 5)
  and what is open (§6). It meets the standard. Its weaknesses are currency and one mis-stated
  pointer.
- **Currency, checked against the code** (story 7 depends on it):
  - Ruling 1, holds live in the browser: `frontend/src/stage/beats/beatsFor.ts`
    (`WORDS_PER_SECOND = 2.4`, `SPEECH_CAP_MS = 15000`). Matches.
  - Ruling 2, read, never hurry: `frontend/src/stage/containers/live-queue.ts::LiveStep`
    ("Always normal live"). Matches.
  - Ruling 3, the jump: `frontend/src/stage/containers/live-state.ts::TURN_JUMP_MS` is 30 s, for
    the seat's own turn only. No "Caught up to the table" notice exists anywhere in `frontend/src`.
    So the general jump is not built, matching the sheet and the constraint.
  - Ruling 4, the server clock: deadlines are held server-side by
    `server/game/seat_clocks.py::SeatClocks`. The browser applies a measured offset from the
    status (`frontend/src/hooks/useCountdown.ts::recordServerClock`). Matches.
  - §6 open item 4 ("stamp each event with the server's emit time; the log has none today") still
    holds: `server/schemas/events.py` carries no emit time. stage_fit works round it with the
    Langfuse traces.
- **Stale passages.**
  - **The head note (2026-10-24)** says "the lag was measured again, from traces, on 13 served
    games" by stage_fit. stage_fit measures the opposite gap: how often the stage stands waiting
    because the model's event has not arrived. The sheet's lag is how far the stage runs behind
    the server. `evaluation/experiments/stage_fit.py` simulates the stage's backlog (its
    "continuous" reading) but does not report it. Reword the note: the waits were measured on 13
    games; the lag figures below are still the one flash-lite game's.
  - **Extraction at game over** appears in §1 ("tens of seconds to minutes"), §2 "Game over"
    ("Extraction then runs (memory on)") and the last row of §4. Since the owner's ruling of
    2026-10-12, extraction never runs in a live game. `server/game/run_config.py::game_run_config`
    says an offline job extracts later, "never during the game". The "Winding the reels…" curtain
    still exists (`frontend/src/stage/scenes/GameOverScene.tsx`), but what it waits for has
    changed. This was not traced further. Add a dated note in each place.
  - **§4's "a stretch of agent day turns" row** says "in solo the human waits for their turn beat
    after the dock opened". Since 2026-10-12 a solo prompt waits for the stage (`live-queue.ts`
    header). §1 already flags Scenario A's dock rows as "the old rule"; this row needs the same.
- **One-home conflicts.**
  - The jump: home is ruling 3 here. Multiplayer finding 10 summarises it consistently and links
    back. beat_sheet §12 (area B or D) should link here rather than restate.
  - The AFK clocks: the head points at `server_design_notes.md` §7, which is area A's home.
    Nothing here conflicts.
  - The server clock: home is ruling 4; principles §6 links it.
- **Feeds.** Story 7 (spine: the ruling, the bounded lag, the rejected per-viewer tempo); story 4
  (ruling 6, a reconnect lands still); realtime_and_sync (ruling 4). Constraint for the write-up:
  "an agent speaks in ~6.4 s and is read in 12 to 15" is the flash-lite game's figure. Haiku 5.5's
  measured discussion turn is 5.4 s median, 10.8 s at the slowest 5% (stage_fit).
- **Proposed action.** Light edit: reword the head note; add dated notes on extraction (three
  places) and on the §4 solo row. Keep the scenario tables whole as the 2026-10-01 game's.
- **Terms used before definition.** the entitlement sheet (the head's name for
  `server_client_transport.md`), the dock, the bar ("Acted n of N"), the mark, the strip notice,
  the drawer, fold ("one fold", ruling 3), `historyLanding`, `seesXray`, `over.*`, the pacing
  tracker. The tier letters P, F, S and O are defined in §0.

### stage_fit/README.md

- **Kind and status.** A dated measurement record (2026-10-24) with a rerunnable runner,
  `evaluation/experiments/stage_fit.py`, and `results.json` beside it. Living, in that it can be
  rerun on any served game.
- **Reader question.** Does the model keep ahead of the stage, on the models players can choose,
  and where does the stage wait?
- **Against the report standard.** It opens with the question and a bold answer, gives the method
  in four steps, and bounds the result with two readings ("restart" and "continuous"). Findings
  are in tables with N, and the limits are stated: seven Haiku games, all played by the owner
  while building, on today's holds. It names the product choice it does not make. It meets the
  standard already.
- **Currency.** The holds it quotes match `beatsFor.ts` (see the timing sheet above). The runner
  and `frontend/scripts/beats-for-log.ts` exist. The 13 games are 7 Haiku, 3 DeepSeek, 2 GPT-6
  Luna and 1 Flash-Lite. `results.json` holds 14 games: the 14th is the AI-only game, which never
  waits.
- **Faults.**
  - "This replaces the one earlier measurement, by hand on a flash-lite game": the same
    over-statement as the timing sheet's head note. It replaces the per-call latencies; it does
    not replace the lag. One sentence fixes both.
  - The latency-limits table says "at or under today's 5.5 s median". The per-call table gives
    5.4 s.
  - An optional addition that would make story 7's "lag bounded by the stretch between human
    turns" a measured claim on 13 games: report from the continuous reading how far the simulated
    stage ran behind the server at each human prompt. The simulation already computes it.
- **One-home conflicts.** The Haiku per-call latencies are at home here. The timing sheet's
  flash-lite medians are the earlier game's and should be labelled as such, which its head note
  does.
- **Feeds.** Story 7 (the measured figures: 2.7 to 5.1% waiting on Haiku over 9,260 s of stage in
  seven games; most waits in runs of passes and at the morning after the pack's chain).
- **Proposed action.** Light edit: the "replaces" sentence and the 5.5 s figure. Placement is open
  (see below).
- **Terms used before definition.** the pack's chain and the carrier's kill (night roles, defined
  only by context), the morning shutter.

### frontend-audit-2026-10-11.md

- **Kind and status.** Dated audit, about 4,800 words, by another agent. It worked on a copied
  snapshot (`dda7cdcf`) built on its own port, with no device. A follow-up of 2026-10-15 surveys
  the audit against the code four days on: before and after table, item status, findings, and
  questions settled. Dated record. Its `frontend-audit-2026-10-11-evidence.json` sits beside it.
- **Reader question.** Is the stack viable and the frontend ownable, and what are the prioritised
  improvements with their evidence?
- **Currency.**
  - The follow-up's "A stream left half-open by a phone's sleep may never be noticed (suspected).
    Open." was fixed the same day. Multiplayer finding 7 records a named `ping` event on the
    server (`f44028d8`) and the page's `streamStalled` (`a0fa2e44`). The code has
    `frontend/src/hooks/catch-up-boundary.ts::streamStalled` and the reopen watch in
    `frontend/src/hooks/useGameStream.ts`. Add a dated note pointing at finding 7.
  - The follow-up's item 5 ("Done. The store takes catch-up as a block") matches
    `catchUpBatch` and `fold-cache.ts::grow`.
- **Faults.**
  - The body links code by line number (`Backdrop.tsx:42`, `Stage.tsx:300`, `store.ts:99`). For a
    dated audit that is acceptable. A topic doc that quotes it must use `path::symbol`.
  - "Use behavior and visual equivalence as hard CI gates" is a recommendation. There is no CI. A
    status line should say the gates run by hand.
- **Its most useful passage for this pass.** The "Documentation quality, not comment quantity"
  paragraph names four claims "stronger than the code proves":
  - `Paint` caches across instances;
  - a remount always means a re-decode;
  - `Bounded` means the browser always repaints only the box;
  - phone motion is a guaranteed steady 24 FPS.

  Three of the four recur in this area's lesson docs and were never qualified: lesson 12, build_log
  §8.8 with phone lesson 8, lessons 8 and 14 with phone lessons 11 and 12. The topic docs should
  state each as observed conditions and intended policy, as this paragraph asks. Its ownership
  section ("current contracts interleaved with historical observations"; "a short current
  architecture/ownership guide") is also the earliest statement of the problem this docs pass
  addresses, and it produced `frontend/README.md`, the owner's guide.
- **One-home conflicts.**
  - Typing redraw and catch-up batching: this follow-up is the measurement record (6.3 to 2.5 s,
    100 to 7 renders). Lessons 32 and 33 are the lessons, and build_log §8.10 "Next" is the
    earlier plan. See the overlaps below.
  - The backdrop pick: item 1 here, lesson 22, phone lesson 3. Consistent.
- **Feeds.** Story 10 ("What is already improved", the stack decision). Stories 1 and 4 from the
  client side (§5 live ingestion and the follow-up's "Questions settled": why the beats are recut
  from the whole log, why "in order" can be told exactly). Learning topics: memory_and_pictures
  (§1), loading_and_deploy (§2), react_identity (§3), rendering_pipeline (§4), realtime_and_sync
  (§5), performance_method and testing ("Scope and evidence", "Tests to add", the gate critique,
  the Safari recording protocol).
- **Proposed action.** Status line: "Dated audit 2026-10-11 with follow-up 2026-10-15; items 1, 3, 5
  done, 2, 4, 6 partly; the dead-stream item fixed 2026-10-15, multiplayer finding 7; there is no
  CI." Add the one dated note.
- **Terms used before definition.** Reveal, `ahead`, "the R7 backlog" (the observer events after
  game over), the platform, `CarScene`, `Paint`, the carriage (as "landing preview").

### rendering-audit-2026-10-02.md

- **Kind and status.** Dated audit, about 1,700 words, by another agent: a copied snapshot at
  `04005ca0`, headless Chromium with software graphics, 42 transition captures. Superseded.
- **Proposed card:**
  - *Question:* before any Safari diagnosis, what does the stage's rendering cost in a controlled
    browser?
  - *Test:* 2026-10-02, a read-only audit of a production snapshot, 42 transition captures and
    microbenchmarks, CPU throttled four times.
  - *Answer:*
    - the lighting geometry is generated in render (57.7 ms median for the day's light; 109 ms
      observed on a counted chip);
    - the scene keys replace almost every node (385 of 388 on a counted chip);
    - the light and the grade cost raster under movers;
    - movers ride full-stage wrappers;
    - a night selection peaks at 30 layers;
    - the phone gate misses short animations.
  - *What followed:* the same day, build_log §8.9's "second pass" took the grade, the night choice
    and the light's cache, and §8.10 took the bounded movers. The 2026-10-11 audit calls this one
    "a historical baseline, not a list of current defects".
- **Reader question.** As the card.
- **Currency.** Not checked: a superseded record.
- **One-home conflicts.** Its numbers are quoted in build_log §8.9 ("60–110 ms" for the light's
  holes) and lesson 12, consistently. Its §5 gate critique is the source of lesson 18. Home of the
  critique: here; lesson 18 is the lesson.
- **Feeds.** Story 10 (lesson 19: "the other agent's audit was right on substance ... its proposed
  order and its GPU hope were checked against our numbers first"). performance_method: its
  "Scope and reproducibility" section is the best statement in the folder of what a measurement
  does not show. It says not to add nested trace events, that rAF intervals are not frames, that
  the variant order was fixed, and that software graphics predict nothing about an iPhone.
  testing (§5).
- **Proposed action.** Card and status line only.
- **Terms used before definition.** `Paint`, the grade, the house light, the pack, the workbench and
  its `frame=iphone14`, `hud=replay`.

## Area-level

### Overlaps, with one home each

| Ruling or finding | Told in | Recommended home | The others |
|---|---|---|---|
| The phone story's numbers (534 MB to 114; 670 MB GPU route; raster tables) | build_log §8.3, §8.9; phone_lessons 1, 2, 11; frontend_lessons 10, 17 | build_log §8 (it already says it is) | Summarise with the number's N and link. Correct phone_lessons' "first crash" |
| The lighting cache key | lessons 12 and 36; rendering audit §1; 10-11 audit §3 and follow-up item 3; build_log §8.9, §8.10 "Not done" | lesson 36 (the fix, `f30d4496`); the topic doc tells 12 and 36 as one lesson | Lesson 12 gets a dated note. build_log §8.10 gets its as-built line |
| Catch-up batching | lesson 32; 10-11 follow-up item 5 and its measured table; build_log §8.10 "Found on the way" and "Next"; principles §6 | lesson 32 for the rule; the follow-up table for the measurement (dev build, one rejoin at seq 200) | build_log §8.10 gets an as-built line. Story 4's client side cites lesson 32 |
| Typing redraw and the leaf | lessons 5, 33, 34; follow-up "Found in the survey"; build_log §8.10 "Left as is: `turnInput`" | lesson 33 (the measurement), lesson 34 (the rule) | The follow-up keeps its row. build_log §8.10 gets an as-built line |
| The backdrop pick by drawn pixels | lesson 22; phone lesson 3 (updated 2026-10-11); 10-11 audit §1 and item 1 | lesson 22 | Consistent already |
| The Cloudflare header | build_log §1.4 (2026-08-21, the `/api` block, mechanism as fact); lesson 31 (2026-10-15, stream route only, mechanism a guess) | build_log §1.4 for the story (story 1, area B); lesson 31 for the header-scope lesson | build_log §1.4 needs a dated note: header moved to the stream's route on 2026-10-15; mechanism unproven (lesson 31) |
| The dead stream | 10-11 follow-up ("Open"); multiplayer finding 7 (fixed); principles §6 | multiplayer finding 7 (area A) | The follow-up gets a dated note |
| The jump | timing sheet ruling 3; multiplayer finding 10; `live-queue.ts` header | timing sheet ruling 3 | Consistent; beat_sheet §12 should link |
| Subtract, census, gate | lessons 15, 16; phone lesson 10; build_log §8.7; principles §8 | `learning/performance_method.md` once it exists; until then lesson 16 | phone lesson 10 keeps the story and links |
| The four over-claims (cache across instances, remount means re-decode, the box alone repainted, steady 24 FPS) | lesson 12, 8, 14; phone lessons 8, 11, 12; build_log §8.8; code comments | 10-11 audit, "Documentation quality" (the critique) | Each topic doc states the observed condition and the policy, and links the dated evidence |

### Placement unclear

- **The 23 small things.** The brief's §6 places none of them. Nine are CSS layout and stacking
  facts that fit no proposed topic:
  - S2: two rules for one class name in a CSS module are one class;
  - S7: a wall capped short of its box ends in an edge;
  - S8: an absolutely placed wall lengthens the page;
  - S13: a `z-index: -1` backdrop and `isolation`;
  - S14: `overflow-x: clip` on `html`;
  - S15: a rounded `overflow: hidden` costs a mask;
  - S17: a grid row keeps a stale height;
  - S20: a `z-index` tie is ordered by mount order;
  - S23: a `<button>` as the layout box on iPadOS.

  Proposal: S13, S15 and S20 (paint order and clips) go to `rendering_pipeline.md`. The other six
  go to a ninth topic doc, `css_layout.md`. The other fourteen are placed in the table below.
- **principles.md §7** (multiplayer authority, side channels, races, rejected against failed, the
  leaver) is server-side and feeds stories 3, 8 and 9. The brief puts it in `realtime_and_sync.md`.
  Either split that doc into "the client's stream" and "multiplayer authority", or make
  `multiplayer_authority.md` a tenth topic. Owner's call.
- **stage_fit/** has its runner in `evaluation/experiments/` and its output in `frontend/docs/`.
  The CLAUDE.md lifecycle sends an exploration's output to `evidence/<experiment>/`. It is chapter
  C's evidence, so keeping it in `frontend/docs/` with a pointer from the evaluation README is
  defensible. Moving it is the convention. Owner's call.
- **phone_lessons.md after the topic docs exist**: it could be dissolved into them, or kept as the
  dated case study that links to them. The second keeps the interview answer in one place.

### Constraint check (brief §8)

- **The general jump is not built**: the timing sheet, multiplayer finding 10 and the code
  (`TURN_JUMP_MS` only; no strip notice) agree.
- **The stall watchdog is not built**: none of this area's documents claims it. The timing sheet's
  stall row names only the request budget and rescue.
- **Served games carry no runtime fingerprint**: not touched. stage_fit reads Langfuse traces.
- **No CI**: no document here says CI runs a check. Two passages lean the wrong way. Phone lesson
  10 says the gate keeps the class closed "without anyone remembering the rule". The 10-11 audit
  recommends "hard CI gates", which is a proposal, not a fact. Both get a clause.
- **Persona voices.** The brief's constraint says voices are OFF. The code says otherwise:
  `server/game/run_config.py::game_run_config` passes `persona_voices=True`, and its docstring
  says "AI seats use their dealt puppet's speaking voice in served games". Commit `73aafcb9`
  (2026-10-26) also corrected the report-pass proposal to "voices as on in hosted games". No
  document in this area mentions voices. **The brief's constraint itself looks wrong and should
  be checked before other areas apply it.**
- **Music deployed 2026-10-15**: lesson 37 and the 10-11 follow-up item 6 agree.
- **The beat sheet and stage_architecture are the truth for the stage**: the holds quoted by the
  timing sheet and stage_fit match `beatsFor.ts`. Phone lessons point at stage_architecture §6
  for the rules, which hold "Nothing animates at rest inside the camera" and the gate.
- **Haiku 5.5 the default since 2026-10-15**: stage_fit says so. The timing sheet labels its game
  as flash-lite.
- **Memory off by default in served games**: the timing sheet's game had memory on, which is
  that game's setting. Its game-over extraction text is stale for a different reason
  (extraction is offline since 2026-10-12).
- **Who wrote what**: build_log §8.1's "Who did what" is consistent (agents built to briefs, the
  owner tested and read the device). The lessons' "we" must be translated for chapter C (see
  frontend_lessons, "The voice").
- **One game's numbers against the 13-game figures**: the timing sheet's head note labels its
  figures as the flash-lite game's, but mis-states what stage_fit replaced. Story 7 should take
  per-call latency and waiting from stage_fit and the lag rows from the one game, each labelled.

### §6 delivered: the lesson-by-lesson placement

The brief's table was confirmed except for six corrections, marked **moved**:

1. Lesson 18 was listed under both performance_method and testing; it gets one home, testing.
2. Lesson 39 is a loading wait, not stage motion.
3. Lesson 48 is the layer cascade.
4. Lesson 14 is the stage's motion policy.
5. The small things are placed.
6. Lessons 12 and 36 are told as one.

| Entry | Lesson (short) | Home | Note |
|---|---|---|---|
| Head A | Re-render and remount | react_identity | The doc's opening mechanism |
| Head B | A frame in three steps; what a layer is | rendering_pipeline | The doc's opening mechanism |
| 1 | A key is an identity | react_identity | |
| 2 | Put the persistent part in one place (the host) | react_identity | Links stage_architecture §6 |
| 3 | Render from the description's own props | react_identity | |
| 4 | Memoise what registers | react_identity | |
| 5 | Ticking state at the root | react_identity | |
| 6 | New objects defeat memo | react_identity | |
| 7 | Effects without dependencies | react_identity | |
| 8 | The browser repaints the moving box | rendering_pipeline | Add the §8.10 measured limit |
| 9 | Transforms and opacity, not SVG attributes | rendering_pipeline | |
| 10 | An animated property makes a layer | rendering_pipeline | memory_and_pictures links it |
| 11 | Blend modes and filters per repaint | rendering_pipeline | |
| 12 | Cache keyed by instance misses | react_identity | Told with 36 as one lesson; dated note |
| 13 | Pictures cost decoded pixels; fresh `<img>` black on iOS | memory_and_pictures | |
| 14 | A steady low frame rate | **moved** to stage_motion | The `stepped` policy; "aims at", not "gives" |
| 15 | Subtract before you add | performance_method | |
| 16 | Census, one batch, a gate | performance_method | The owner's rule, 2026-10-02 |
| 17 | Measure the attractive answer first | performance_method | |
| 18 | A gate reading the end of a window | **moved**: testing only | performance_method links it |
| 19 | Read an audit as claims to measure | performance_method | Also a playbook rule (area D) |
| 20 | Tests waiting on time, not state | testing | |
| 21 | A viewer's override lapses without an effect | realtime_and_sync | Confirmed: state that refers to a place in a growing log, with 24 |
| 22 | Choose a picture's size from drawn pixels | memory_and_pictures | |
| 23 | Deferred only if mount, data and pictures wait | loading_and_deploy | |
| 24 | A derived list that folds items needs a cursor rule | realtime_and_sync | Its test twin links testing |
| 25 | A census compares two builds in one sitting | performance_method | |
| 26 | A filter's cost is area × count × how often | rendering_pipeline | |
| 27 | Defer a mount only into a sized box | loading_and_deploy | |
| 28 | Find what the main thread does first | performance_method | |
| 29a | A baked copy must cover what the computation reads | memory_and_pictures | Paired with 44; its invariant test links testing |
| 29b | A dynamic component loads at first render | loading_and_deploy | |
| Case | The carriage case, 2026-10-15 | loading_and_deploy | The worked example for 29b to 31 |
| 30 | A size measured after mount fetches | loading_and_deploy | memory_and_pictures links it |
| 31 | A header travels with its block | loading_and_deploy | The stream half links realtime_and_sync and build_log §1.4 |
| 32 | A backlog down a live socket | realtime_and_sync | |
| 33 | A rule is kept only by a measurement (render census) | performance_method | The census hook is not committed |
| 34 | Typed state lives in the leaf | react_identity | |
| 35 | A cache over a growing log grows with it | realtime_and_sync | |
| 36 | A cache must not be keyed on the instance | react_identity | With 12 |
| 37 | Count decoded bytes (pictures and sound) | memory_and_pictures | |
| 38 | A deploy empties the CDN | loading_and_deploy | Probable cause, not proven, as the lesson says |
| 39 | A visible wait must say it is waiting | **moved** to loading_and_deploy | Dated note on "Not deployed yet" |
| 40 | A script transform needs its own layer | rendering_pipeline | |
| 41 | A scene's carry-over comes from what the stage showed | stage_motion | The beat cutter (`atStand`) |
| 42 | A loading boundary splits hydration | loading_and_deploy | |
| 43 | Decode ahead every picture the next beat shows | memory_and_pictures | |
| 44 | A layout that moves a baked picture is that picture moved | memory_and_pictures | |
| 45 | Hold a picture-drawn page whole, before React | loading_and_deploy | |
| 46 | Find where a stall's time goes | performance_method | |
| 47 | An instant swap: `visibility`, not opacity | rendering_pipeline | |
| 48 | No first move under a fading cover | **moved** to rendering_pipeline | The cascade (10) in a loading context; loading_and_deploy links it |
| 49 | Diff the slow page from the fast one, in the viewer's engine | performance_method | |
| S1 | Module state duplicated across two bundles | loading_and_deploy | |
| S2 | Two rules, one class name | css_layout (new) | |
| S3 | Sound starts only from a press | memory_and_pictures | If renamed "pictures, sound and memory" |
| S4 | iPhone's `interrupted` AudioContext | memory_and_pictures | As S3 |
| S5 | `--update-snapshots` rewrites only failures | testing | |
| S6 | Production prefetches every `<Link>` | testing | |
| S7 | A capped wall ends in an edge | css_layout | |
| S8 | An absolute wall lengthens the page; `overflow: clip` | css_layout | |
| S9 | `pgrep -f` matches its own loop | testing | |
| S10 | A percentage move shrinks with its element | stage_motion | |
| S11 | Reading Safari's timeline | performance_method | |
| S12 | Dev numbers are not production numbers | performance_method | |
| S13 | `z-index: -1` backdrop and `isolation` | rendering_pipeline | |
| S14 | `overflow-x: clip` on `html` | css_layout | |
| S15 | A rounded clip round a layer costs a mask | rendering_pipeline | |
| S16 | Read layer memory on a device; CDP counts layers | performance_method | |
| S17 | A grid row keeps a stale height | css_layout | |
| S18 | `next dev` drops a dynamic chunk's stylesheet | loading_and_deploy | |
| S19 | A server component's child calling a client hook | react_identity | Cited by principles §1 |
| S20 | A `z-index` tie is mount order | rendering_pipeline | Cited by principles §3 |
| S21 | A full-page shot before `useNear` mounts | testing | |
| S22 | Whose server answered on the port | testing | Cited by principles §8 |
| S23 | A `<button>` as the layout box (iPadOS 18) | css_layout | And a method note: a variant page on the device |

Counts by home (76 rows: 50 numbered lessons, the two head mechanisms, the carriage case and 23
small things): react_identity 12, rendering_pipeline 12, memory_and_pictures 8, loading_and_deploy
12, performance_method 12, realtime_and_sync 4, testing 7, stage_motion 3, css_layout 6.
realtime_and_sync's weight comes from outside the log (below), and stage_motion's from
stage_architecture §6. If the owner wants fewer topics, stage_motion folds into rendering_pipeline
without strain.

### §6 delivered: source passages per topic doc

Each topic doc takes phone_lessons' form plus the three parts it lacks (the lesson number and code
symbol, the rule, the reading). For each, the passages it would draw on:

**`react_identity.md`**
- frontend_lessons: head A; lessons 1 to 7, 12 with 36, 34; S19.
- phone_lessons: 5 (keys and churn; the mark trick); 8 (the remount's black frame, linked from
  memory).
- principles: §1 whole; §2 first bullet (a cache key holds exactly what the result depends on).
- build_log §8: §8.3 (the set and beat split, the `.churn` probe table); §8.8 (one backdrop owned
  by the Stage, the registrar pattern); §8.9 (the `CarScene` host; "Found on the way", the notes
  editor closed by a transient, which is lesson 3); §8.10 (`useSeeded` in `ShelfRoomScene.tsx`;
  the countdown leaf, which is lesson 5).
- Audits: rendering audit §2 (the 385 of 388 nodes table); 10-11 audit §3 and the follow-up's
  "Found in the survey" (typing redraw, `CarSetSpec` rendering the host twice) and "Questions
  settled" (controlled input; can the dock lose its text).
- Code: `frontend/src/stage/scenes/CarScene.tsx`, `LynchScene.tsx`, `VoteScene.tsx`
  (`BallotLine`), `frontend/src/stage/Stage.tsx` (`drawn`),
  `frontend/src/stage/instruments/CountText.tsx`, `TurnDock.tsx::useTyped`.

**`rendering_pipeline.md`**
- frontend_lessons: head B; lessons 8 to 11, 26, 40, 47, 48; S13, S15, S20.
- phone_lessons: 1, 2, 6, 7, 9, 12 (after the light edits).
- principles: §3 whole.
- build_log §8: §8.1 (masks, a platform limit on one technique); §8.2 (with its compositor
  correction); §8.3 (the inspector's layer table); §8.4 (SVG attribute to HTML box); §8.5 (the
  camera move's raster table); §8.6 (three things at rest); §8.9 ("the paint under a mover", "the
  grade", "the GPU route, measured and refused"); §8.10 (bounded movers, and the tiles caveat
  under its table).
- Audits: rendering audit §3, §4, §5; 10-11 audit §4 and "Documentation quality".
- Code: `frontend/src/stage/instruments/Bounded.tsx`, `frontend/src/stage/cast/Puppet.tsx`
  (`rising`), `frontend/src/stage/instruments/Flip.tsx`, `frontend/src/styles/gpu-probe.css`,
  `FeaturedReplay.tsx` (`lifted && !covered`).

**`memory_and_pictures.md`** (consider "pictures, sound and memory")
- frontend_lessons: lessons 13, 22, 29a, 37, 43, 44; S3, S4.
- phone_lessons: 3, 4, 8.
- principles: §4 whole.
- build_log §8: §8.2 (sprite sizes against production practice); §8.3 (the bake and its 1×, 1.5×,
  2× sheet table; 48 sheets); §8.8 (`decoding="sync"`, with the rendering audit's re-decode
  caveat); §8.9 (the picture census: 197 MB touched, 70 MB never shown; `SPRITES.small`, 55 files).
- Audits: rendering audit, "What these results deprioritize" (remount is not re-decode; heads at
  23 CSS px); 10-11 audit §1 (the 16.99 against 7.55 MiB table), follow-up items 1 and 6, and the
  last settled question (music 115 to 175 MB decoded).
- Code: `frontend/src/stage/instruments/Backdrop.tsx::pickScale`, `::sheetFor`,
  `frontend/src/stage/cast/DecodeAhead.tsx`, `frontend/src/stage/cast/ahead.ts`,
  `frontend/src/music/player.ts`, `frontend/scripts/bake-sets.mjs`,
  `frontend/scripts/small-sprites.mjs`, `frontend/src/stage/instruments/backdrop.test.ts`.

**`loading_and_deploy.md`**
- frontend_lessons: lessons 23, 27, 29b, 30, 31 (header half), 38, 39, 42, 45; the carriage case;
  S1, S18.
- principles: §5 whole.
- build_log: §1.4 (Cloudflare buffering, area B's, linked with its dated note).
- Audits: 10-11 audit §2 (the landing preview's lifecycle) and the follow-up's item 2 and its
  "Found in the survey" bullets (six preloaded fonts, the Mantine stylesheet, the blur
  placeholders).
- Code: `frontend/src/app/(site)/_components/landing/FeaturedReplay.tsx` (`theatreCode`,
  `painted`, `PAINT_CAP_MS`), `frontend/src/app/(site)/_components/guide/useNear.ts`,
  `frontend/src/stage/Stage.tsx` (`measured`), `frontend/src/hooks/useHydrated.ts`,
  `frontend/src/components/site/PageGate.tsx`, `frontend/src/stage/pictures-of.ts`,
  `frontend/e2e/site.spec.ts`.

**`performance_method.md`**
- frontend_lessons: lessons 15, 16, 17, 19, 25, 28, 33, 46, 49; S11, S12, S16.
- phone_lessons: 4 ("testing on the device ... as the measurement of record"), 10, 11 ("what we
  measured before choosing").
- principles: §8 whole.
- build_log §8: §8.1 "Who did what" (where the subtraction method came from); §8.3 "The probe"
  (`?auto=`, and the history-API detail); §8.7 (the gate and the sweep's list); §8.9 (the
  subtraction readings and the before and after table); §8.10 (the day-4 walk that answered "day 4
  feels heavier"; its scripts are not committed).
- Audits: rendering audit "Scope and reproducibility" (the model statement of measurement
  limits); 10-11 audit "Scope and evidence", the physical-Safari recording paragraph and the
  "Physical-device soak" row.
- Code: `frontend/src/styles/gpu-probe.css`, `frontend/scripts/profile-theatre.mjs`. Lesson 33's
  census hook would need committing to be shown.

**`realtime_and_sync.md`**
- frontend_lessons: lessons 21, 24, 32, 35; lesson 31's stream half.
- principles: §6 whole; §7 if the owner keeps it here (see placement).
- Multiplayer audit (area A's document): the client halves of findings 7 (dead stream), 8 (an
  older status loses), 9 (a cached status is an earlier moment), 10 (the turn jump) and 11
  (rejected against failed).
- build_log §8.10 "Found on the way" (85 ms a catch-up frame in dev; the cost that became lesson
  32).
- Audits: 10-11 audit §5 and the follow-up's item 5 table and "Questions settled" (why the beats
  are recut from the whole log; an append is told from an insertion exactly).
- Timing sheet: ruling 4 (the server clock), ruling 6 and the §4 reconnect row.
- Code: `frontend/src/hooks/catch-up-boundary.ts::catchUpBatch`, `::streamStalled`,
  `frontend/src/hooks/useGameStream.ts`, `frontend/src/game/store.ts::syncPending`,
  `frontend/src/stage/containers/fold-cache.ts::grow`,
  `frontend/src/stage/containers/live-state.ts::keepSame`, `::runOf`, `::TURN_JUMP_MS`,
  `frontend/src/stage/film/record-model.ts::shownMorning`,
  `frontend/src/stage/film/case-file.ts::shownSeat`,
  `frontend/src/hooks/useCountdown.ts::recordServerClock`.

**`testing.md`** (area B writes the testing walk; area C's passages)
- frontend_lessons: lessons 18, 20; lesson 24's test twin; lesson 29a's invariant test; S5, S6,
  S9, S21, S22.
- phone_lessons: 10 ("see it yourself": running the gate, and the clause on no CI).
- principles: §8 last bullet.
- build_log §8: §8.7 "How it measures" (the gate's mechanics); §8.8's flake note (the curtain
  goldens failing two runs in three); §8.9 and §8.10 "Verified" (what each batch was checked
  against); §8.10 "Found on the way" (waits sized to the stream, `landsOn`).
- Audits: rendering audit §5 (the gate blind to a short animation); 10-11 audit "Checks
  completed" (three unit failures from an implicit fixture), "Tests to add, in order", and the
  gate critique (it infers cost from DOM geometry, samples at 150 ms, skips removed nodes; its
  `will-change` ban is "a conservative policy, not a universal rendering law").

**`stage_motion.md`** (consider "stage beats and motion")
- frontend_lessons: lessons 14, 41; S10.
- phone_lessons: 9 (the camera cuts on a phone), 11 (24 steps a second), 12 (the winners simply
  there).
- build_log §8: §8.5 (camera cuts on `data-small`); §8.7 (one flag for what a phone is,
  `useSmall`); §8.9 (the list of movers stepped by `useSteps`); §8.10 (the ending held still).
- stage_architecture §6 (the rules: "Nothing animates at rest inside the camera", the gate, the
  set kept up); pointed at, not restated.
- Audits: rendering audit, "deprioritize" bullet on `PHONE_FPS = 24` (a trade-off, not a fix);
  10-11 audit, "What is already improved" (the small-stage compromises, and keeping quality as the
  direction).
- Code: `frontend/src/stage/motion.tsx::stepped`, `::useSteps`,
  `frontend/src/stage/beats/beatsFor.ts::atStand`, `frontend/src/stage/Stage.tsx` (`useSmall`).

**`css_layout.md`** (new, proposed)
- frontend_lessons: S2, S7, S8, S14, S17, S23; lesson 27's layout-shift half links here.
- Code: `StationWall.module.css`, `Rooms.module.css` (the capped walls), the site layout's
  `.station` (`overflow: clip`), `Wing.module.css` (`.tap`).

### For §7 (area D's playbook), noted in passing

Three workflow patterns appear in this area's documents. Area D may use them.

- **An audit on a frozen snapshot.** Both audits copied `frontend/` to a temporary directory,
  built it on a port of their own and changed nothing. The audit was then surveyed against the
  code days later (the 10-11 follow-up). Exemplars: the "Scope" sections of both audits and the
  10-11 follow-up.
- **Read an audit as a list of claims to measure** (lesson 19). Exemplar: build_log §8.9 "A second
  pass from the readings".
- **Census, one batch, a gate** (lesson 16, the owner's rule of 2026-10-02). Exemplar: build_log
  §8.7.
