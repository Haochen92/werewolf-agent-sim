# What the phone taught us

Written for: the owner, to re-own and re-explain. Ten lessons from making the theatre survive
and feel right on an iPhone (2026-10-01 to 2026-10-02), each in plain words: what you saw on the
phone, what the browser was actually doing, what fixed it, and how to see it yourself. The
numbers and the dated detail live in `build_log.md` §8; each lesson points at its section. The
rules we keep are in `stage_architecture.md` §6, and the test that enforces them is
`e2e/phone-rule.spec.ts`.

The one sentence version: **a phone gives a page a fixed memory budget and kills it at the
line, and almost everything that spent that budget was something the browser did on our behalf
(a layer here, a decode there) rather than anything we drew too big.**

---

## 1. The browser turns the page into layers, and layers are what cost memory

**What you saw.** Every stage page died on the iPhone within a few beats, while the Mac was fine
(§8.1).

**What was happening.** A browser does not paint a page as one picture. It splits it into
layers: separate bitmaps the GPU stacks together, so that moving one does not mean repainting
the others. Each layer is a full-resolution bitmap of its area, held in GPU memory. A full-stage
layer on your phone is about 54 MB (the stage's pixels at the phone's resolution, times four
bytes each). Safari's Layers panel lists them; at rest the whole stage should be one.

**What fixed it.** Nothing directly; this is the frame for everything below. The first number
we read was 17 layers and 534 MB before a beat had played (§8.3).

**See it yourself.** Safari on the Mac → Develop → your iPhone → the page → the Layers tab.
The count and the total are the two numbers that matter.

## 2. One animating element promotes everything painted above it

**What you saw.** The felt country scrolling behind the car's window, a tiny thing, was the
whole first crash (§8.3).

**What was happening.** An element with a running animation gets its own layer, so the GPU can
move it without repainting. But the browser must keep paint order correct, so every element
painted *after* it that overlaps it must become a layer too, otherwise it would be drawn
underneath. One scrolling strip inside the camera therefore promoted the light, the grade, the
figures and the HUD: six full-stage layers. The felt country cost 54 MB six times over.

**What fixed it.** The rule **nothing animates at rest inside the stage**. The country was
baked into the backdrop picture; later the same rule caught the wing's breathing glows, the
night rooms' snow, the station's flakes and the lift's `will-change` (§8.6, §8.7).

**See it yourself.** Grep the stage's css for `animation:` and `will-change`. Anything that
matches and is on screen at rest on a phone is a layer, plus everything above it.

## 3. Memory is pixels, not file size

**What you saw.** The backdrop sheets are small WebP files, yet the page's memory was large.

**What was happening.** A picture on the wire is compressed; a picture on screen is not. To draw
it the browser decodes it into raw pixels, four bytes each, whatever the format. The 2200×900
unit sheet at 1.5× is 3300×1350 pixels: about 18 MB decoded from a 300 KB file. Nine 384 px
heads are about 0.6 MB each. This is also why `next/image` could not help here: its job is the
file on the wire, and the cost is the pixels after.

**What fixed it.** Picking the sheet by the screen: 1.5× on a phone, 2× on a desktop, never
more than the screen can show (§8.3). A 2× sheet on a 900 px wide stage would decode to 32 MB
for no visible gain.

**See it yourself.** Width × height × 4, for every picture on screen at once. The census probe
in §8.6 sums it for a page: 39 MB at the first beat, 22 MB in a night room.

## 4. A phone kills the tab at a line; a desktop just gets slower

**What you saw.** The same replay was smooth on the Mac and dead on the phone.

**What was happening.** iOS gives one tab a fixed budget for everything (page, pictures,
layers) and ends the tab when it crosses it, with no warning in the page. A desktop has swap
and gigabytes to spare; it degrades. So a design that is merely heavy on a desktop is fatal on a
phone, and the heaviness is invisible until you read the phone itself.

**What fixed it.** Testing on the device, with the inspector attached, as the measurement of
record; and the pace probe (`?auto=<ms>&loop=a-b` on the workbench) to find the floor before and
after each change rather than guessing (§8.3).

**See it yourself.** The Memory timeline in the inspector shows the page's side; the Layers
panel the GPU's side. The crash happens when their sum crosses roughly a gigabyte, and the
layers are the part that climbs fastest.

## 5. React keys decide what is rebuilt, and rebuilding is churn

**What you saw.** Beats faster than one a second killed the page even with no animation
running (§8.3).

**What was happening.** A React `key` tells React "this is a different thing": when it changes,
the old subtree is thrown away and a new one built. The scenes keyed their whole tree per beat,
so every beat rebuilt the car's paint, the haze, the light and the figures: thousands of DOM
nodes and several full-stage pictures, allocated and freed each time. The page's memory never
settled, and at speed the garbage outran the collector.

**What fixed it.** The set/beat split: a scene is a stable set (the paint, the shutter, the
light, the wing) that updates in place, and a small keyed part (the puppet, the box) that is
rebuilt per beat. Done for the day and the morning; the vote, lynch, night, deal, game over and
replay night are still keyed whole and are the next thing to split (§8.3, §8.8).

**See it yourself.** React DevTools' highlight-updates, or the probe trick from §8.8: mark a DOM
element with a property, step a beat, and see whether the mark survives.

## 6. The same move is cheap as a CSS transform and expensive as an SVG attribute

**What you saw.** The ballot jar's tip and the shutter's slide stuttered on the phone while the
puppets' rises did not (§8.4).

**What was happening.** The puppets move as HTML elements with a CSS `transform`: the browser
repaints one finished picture through a matrix. The jar and the shutter moved as groups inside
an SVG drawing with the `transform` *attribute* written every frame, and an SVG attribute change
is a layout change: the browser re-lays-out and repaints the drawing around it each frame, and
resamples the big picture on the CPU each time.

**What fixed it.** Each picture that moves now sits in an HTML box of its own with a small SVG
inside, and motion moves the box. Same geometry, same timings, a quarter of the work.

**See it yourself.** The Rendering Frames timeline: bars crossing the frame line during a move.
Compare the vote's count before and after `f33c89a`.

## 7. What motion does for you, and what it does not

**What you saw.** Moving the jar to motion did not make a GPU layer appear.

**What was happening.** Motion drives `x`, `y`, `rotate` and `scale` in JavaScript, writing the
element's `style.transform` each frame. It uses the Web Animations API only for `opacity`,
`filter`, `clipPath` and the `transform` string, and it does not add `will-change` unless asked
(we checked its source, §8.4). So motion moves are *software* moves: smooth enough for a picture
through a transform, no layer and no cascade. If a move needs the GPU, you say so yourself with
`will-change: transform` for the move's duration, and then lesson 2 applies for that second.

**What fixed it.** Knowing which it was. The `gpu=lift` workbench word puts `will-change` on
every moving box so the price can be read in the Layers panel before paying it in the build.

**See it yourself.** Open the vote's count in the workbench with and without `&gpu=lift`, Layers
panel open, and watch the count during the tip.

## 8. A fresh `<img>` is black for a frame on iOS

**What you saw.** The screen flashed dark between beats, and the wing flickered once per counted
chip, on the phone only (§8.8).

**What was happening.** `next/image` renders pictures with `decoding="async"`: the browser may
paint the page before the picture is decoded. On a desktop the decoded picture is still in a
cache, so a remounted image paints at once. iOS purges that cache, so a freshly mounted `<img>`
paints nothing until its decode lands, one frame of the page's dark behind it. Every scene keyed
whole remounted its backdrop and its wing per beat (lesson 5), so every beat showed the gap.

**What fixed it.** The backdrop now belongs to the Stage and is never remounted by a beat; and
every stage picture decodes synchronously, so what is still remounted paints at once.

**See it yourself.** The mark trick from lesson 5 on the backdrop's `<img>`: it should survive
forty beats and six scene changes (it does, on production).

## 9. A JavaScript-driven transform repaints everything inside it

**What you saw.** The count's push-in and the pull-backs were the laggiest moments and crashed
the most (§8.5).

**What was happening.** The camera is a `motion.div` round every stage layer. On a desktop it
keeps `will-change: transform`, so a zoom is a GPU matrix. On a phone we took that away (the
camera's layer forced the grade and the HUD onto layers, 212 MB at rest), so a zoom became a
JavaScript transform on a plain element: the whole world repainted every frame at the phone's
resolution, double-buffered, for a second. The trace put it first by a wide margin.

**What fixed it.** On a phone the camera cuts to its shot where the move would have started.
The move could come back as a GPU move once the budget is known (lesson 7), the camera being
what desktop viewers would miss most.

**See it yourself.** Chromium's trace in §8.5: raster time per transition beat, before and after.

## 10. The method: subtract, census, then a gate

**What you saw.** Four rounds of "you crash, I hunt, I fix the one I found". You called it
whack-a-mole, correctly (§8.7).

**What was happening.** One principle, violated in many places by code written before we knew
it, found one instance per crash because the only instrument was your phone.

**What fixed it.** Three tools in order. *Subtraction* (`?gpu=nolight`, `noimg`, …) to find
which part crashes a page when nothing else is known. A *census* (grep for the things that make
layers) to find every instance at once. Then a *gate*, `e2e/phone-rule.spec.ts`, that walks
every scene and beat in the phone frame and fails on any new instance, so the class stays
closed without anyone remembering the rule.

**See it yourself.** `npm run e2e -- e2e/phone-rule.spec.ts` with the dev server up. Its report
lists what still moves and how much of the stage it paints.

---

## If you are asked about it

The honest shape of the story: a stage built for a desktop, moved to a phone; the first crash
was one small animation that cost 300 MB through the layer cascade; the fix was to bake the
set, keep the set mounted, and let only the beat change; the remaining crashes were the same
rule in five more places, found by census and closed by a test. The thing we did not do, and
why: a canvas port would make every move a GPU matrix and the memory predictable, at the price
of rewriting the stage's drawing side; the DOM stage with these rules holds, so the port is the
known next step only if the stage has to be a showcase of motion on phones.
