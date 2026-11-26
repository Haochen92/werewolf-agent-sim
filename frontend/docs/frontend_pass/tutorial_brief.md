# Brief: the learning tutorials (step 4 of the frontend pass)

Written 2026-10-26, after the owner accepted both pilots. One agent per topic. This brief is shared;
each agent's prompt adds its topic.

## Who reads it

The owner: an engineer re-owning a React and Next.js app that AI agents built to the owner's specs.
The owner wrote the event schema and co-wrote the beat sheet; the rest of the frontend, tests included,
was AI-built. They will read each tutorial to understand the concepts well enough to explain any case
in an interview, and then trace the code themselves. Plain words; every term defined where it is
first used; no assumed folklore.

## Where it goes

- `frontend/docs/learning/<topic>/<topic>.md`, with its figures in `frontend/docs/learning/<topic>/figures/`.
- Links: a sibling tutorial is `../<other>/<other>.md`; a document in `frontend/docs/` is
  `../../<doc>.md`. Code is cited in backticks as `path::symbol`, paths relative to `frontend/`, never
  line numbers.
- The form's exemplar is the accepted pilot `frontend/docs/learning/react_identity.md` (being moved to
  `learning/react_identity/react_identity.md` in parallel; link it by the new path). Read it whole
  before writing.

## The form (proposal §3.1, owner ruling 2026-10-26)

1. **What this teaches, and what you need first.** One short section; name the prerequisite
   tutorials by link.
2. **One section per concept.** The mechanism first, in plain words, with a tiny generic example
   where it helps. Then "In this project": the cases as worked examples, each with its lesson number,
   the code symbol, and any number with its N, date and conditions. Then "See it yourself": a step the
   owner can do with the committed code, the workbench, DevTools or the browser profiler; if the
   script that produced a number is not committed, say so. Then "The rule", one sentence.
3. **Case index** at the end: every lesson number (and S-number, phone lesson) placed to this topic,
   mapped to its section. Every row the placement table gives this topic must appear.
4. **If you are asked about it:** the one-minute answer in the owner's first person, honest about who
   built what.
5. **Reading:** principles.md's lists for this topic plus primary sources only (official docs pages
   by name, at most one book).

Two rules. **The cases set the syllabus:** teach only the concepts the cases need, to the depth at
which each case becomes obvious; a concept with no case here goes to Reading. **Prerequisites are
explicit:** react_identity and rendering_pipeline are the foundations; memory_and_pictures,
loading_and_deploy and stage_motion build on rendering; performance_method builds on all of those;
realtime_and_sync stands alone; testing comes last; css_layout stands alone.

## Figures (owner, 2026-10-26: the code was not theirs, so the concepts need pictures)

- 3 to 7 per tutorial, one wherever a mechanism has a shape: a before and after, a timeline, a layer
  stack, a pipeline, a race. Not decoration: each must make one concept easier than the prose alone.
  Prefer a worked example with real names and numbers from this project over an abstract diagram.
- Exemplars of the look and the density: `frontend/docs/client_design/figures/*.svg`, and how they
  sit in `frontend/docs/client_design/client_design.md` (each inserted right after the paragraph it
  illustrates, as `![Figure N: one-sentence alt text](figures/NN-short-name.svg)`).
- Draw with the kit: write your generator at
  `/tmp/claude-1001/-home-ubuntu-projects-werewolf-agent-sim/0f7e942f-0b66-40d7-bf2f-55014dfa11bc/scratchpad/figkit/gen_<topic>.py`,
  `sys.path.insert(0, ".../scratchpad/figkit")`, `from figkit import Fig` (palette and API in its
  docstring), run it with `poetry run python`. Hand-written SVG is fine too; keep the palette.
- Render and **look at every figure** before inserting it:
  `bash .../scratchpad/figkit/render.sh .../scratchpad/figkit/png_<topic> <svg files>`, then Read each
  PNG. The usual fault is text running past its box (about 7.5 px per character at 14 px sans,
  7.7 px at 12.5 px mono): fix, re-render, look again. White background, width about 960 to 1000.
- Every name and number in a figure is checked against the code or its source document, like the
  prose.

## Style

- The plain-presentation habits (`evidence/experiment_report_style_guide.md`, "Plain presentation"):
  the question plainly and the answer first; context before numbers; counts a reader can picture.
- No em-dashes, no icons, no filler sentences.
- State observed conditions as observed and policies as policies. The 2026-10-11 audit named four
  over-claims that recur in the lessons; never repeat them as guarantees: a cache that reuses across
  instances (lessons 12 and 36, told as one), a remount meaning a re-decode (lesson 13, build_log
  §8.8), the box alone being repainted (lesson 8), a steady 24 frames a second (lesson 14).
- The lessons' "we" is the builder. In the tutorial, say what the code does and what was found, dated;
  where it matters, the agents built and the owner tested on the device.

## Facts that hold today (check before contradicting a source)

No CI exists: a gate or test runs only when someone runs it. The general jump (timing sheet ruling 3)
is not built; only the seat's own-turn jump (`TURN_JUMP_MS`, 30 s). The stall watchdog is not built.
Persona voices are on in hosted games since 2026-10-19, off in batch. Music deployed 2026-10-15. The
site's default model is Claude Haiku 5.5 since 2026-10-15. "The X-ray" is the code's and older docs'
name for what the site calls the reveal.

## Rules

- Write only inside your own folder (and the scratchpad). Edit no other file. No git commands that
  change anything. Do not run servers, builds or tests; `render.sh` is allowed.
- Verify every claim about the code by reading it. Where a source document and the code disagree,
  follow the code and say so in your final report.
- Length: 2,500 to 4,500 words for a full topic; 1,500 to 2,500 for stage_motion and css_layout.
- Write the document once, whole, when you have read everything.
- End with a short report: the files written, the word count, each figure and what it shows, any
  claim you could not verify, and any contradiction between sources.
