# Site architecture: the pages around the theatre

The app has two halves with two toolkits. The **site** is the pages you move between: `/`, `/play`,
`/rooms`, `/play/room` and `/replays`. It is built from Mantine components themed from the page
mockups (`claude_artifacts/design/pages/*.html`, with `landing.html` as the style source). The
**theatre** is the stage: `/games/[id]`, `/replays/[id]` and `/workbench`. It is CSS modules over
`stage/paint/materials.ts` and never imports Mantine (stage_architecture.md). Rulings: review
`design_2026-09-26/pages_review.md` §F (F2 name, F3 Mantine stays and Silkscreen goes).

## Routes

`src/app/(site)/` is a route group. The parentheses keep it out of the URL, so the pages keep their
paths. Its `layout.tsx` wraps every site page in the shell: `IconSprite`, `TopNav`, the page, and
`SiteFooter`, in the column, inside `.station`: the screen's width and the page's height,
positioned and `overflow: clip`, so a page's wall is placed against it from the very top and cut
off at the page's foot (a wall taller than a short page never lengthens it; sticky pieces still
stick, as clip makes no scroll box). The theatre's routes sit outside the group and get no nav. `/replays` (the archive,
inside the group) and `/replays/[id]` (the theatre, outside it) share a URL segment but not a layout,
which Next allows because the two resolve to different paths.

Titles: the root layout's `metadata.title.template` is `The Ninth Express · %s`, so a page sets only its
own part (`'Rooms'`). `/` gets the default, `The Ninth Express`.

## Tokens: one table, the theatre wins

- `src/theme/tokens.ts` is the table. `SITE_TOKENS` holds the site-only roles, with the landing's
  names and values (`--bg --panel --panel-2 --line --text --muted --paper-dk --ink2 --brass --red
  --amber-hi --r-s/m/l --shadow --site-max --gutter`), plus the signage's materials from the
  2026-10-14 redesign (`--brass-line --brass-hi --brass-lo --board-top/bot --plate-top/bot
  --plate-edge --plate-ink --sign-text --sign-muted --well-text`; new names beside the old, so
  `--brass` and the pages outside the redesign keep their look). `THEATRE_ALIASES` holds the names the site
  shares with the stage (`--ink --bone* --cloak1/2 --paper --amber --town --wolf --sk --*-ink --film
  --sure`), read from `vars()` in `materials.ts`. Where a mockup disagrees (`--bone2`, `--bone3`,
  `--killer`), the theatre's value is used.
- `src/styles/tokens.css` declares the same tokens as CSS custom properties for CSS modules. Its
  second block is the August palette (`--ink-900`, `--text-dim`, …). It stays only until the pages
  that still read it are rebuilt.
- `src/theme/tokens.test.ts` checks that every shared name carries the theatre's value, and that
  `tokens.css` matches the TS table one for one.
- The Mantine theme (`src/theme/`: colors, typography, layout, components) is built from the table.
  `primaryColor` is amber. `dark` is a warm scale from `--text` down to `--bg`. The radii are
  `xs` 8px, `sm`/`md`/`lg` = `--r-s`/`--r-m`/`--r-l`, and `xl` = the pill. The page is always dark
  (`forceColorScheme="dark"` plus `data-mantine-color-scheme="dark"` on `<html>`).
- Themed components (`theme/components/*.module.css`): Button, Anchor, Input/TextInput/Select,
  SegmentedControl, Chip, Switch, Modal, Notification, Table, Title and Alert. Anything else renders
  as stock Mantine over the warm scale.

## Fonts

Which face goes where (three voices, three props) is ruled in [typography.md](typography.md)
(2026-10-16); this section is how they load.

- `src/theme/fonts.ts` loads the mockups' faces through next/font: Outfit (300 to 800) as
  `--font-site-sans`, IM Fell English (roman and italic) as `--font-site-serif`, and EB Garamond
  (500, 600) as `--font-site-garamond`, for names on the signage (the wordmark, the model on the
  roof board, a seat's name in the transcript). They are set on `<html>` so that Mantine's portals
  get them too. `--font-sans`, `--font-serif` and `--font-garamond` are the stacks, each with a
  fallback. Serif for in-world labels and names, the sans for interface text.
- The theatre keeps its own instances in `src/stage/fonts.ts` (`--font-stage-*`), applied by the
  theatre layouts. The Silkscreen pixel face is gone.

## Components (`src/components/site/`)

| Component | What it is |
|---|---|
| `TopNav` | The station's signboard (redesign 2026-10-14 §1): the gold 9 badge (2026-10-18) and the name in EB Garamond, and Play · Rooms · Replays as recessed wells on a board hung from two brass rods; the current page is the cream plate (`aria-current`). Rooms carries a split-flap count of the tables boarding (`hooks/useBoarding`, the same query as the departures board). The guide is not a fourth door but an enamel sign (`SITE.guide`, owner 2026-10-14): after the doors and a brass line, an open book and "Guide"; the book alone under 1060px; on a phone the book at the end of the name's row (the board is a grid there, so the sign never falls onto a row of its own, and the name shrinks to leave it room). Once the board scrolls away a slim strip of it pins to the top (`inert` while hidden); its name drops cleanly when the doors need the room; on a phone the strip keeps the book at its right end (owner 2026-10-15). On a phone the doors share a second row. |
| `Board.module.css` | The signage's materials, composed by every board on the site: `board` (wood in a brass frame: what you operate), `rivets`, `well` (a recessed button; `aria-current`/`-pressed`/`-selected` make it the cream plate), `plate` (the primary action), `enamel` (a navy sign screwed to a board: somewhere to read, not a door) and `flap` (one split-flap tile). Paper carries what you read; brass is for lines and hardware, never a small flat fill. |
| `StationWall` | A page's wall: each a picture of its room's wall (owner 2026-10-18, below): `records` the archive, `granite` the ticket office, `cards` the guide; the landing and the departures hall have pictures of their own. Placed against `.station` from the page's top, under the page's own stacking context (`wallPage` on its `<main>`), its foot faded to the page's ground. Further down, each side of the guide's roles stands on a tile in its own colour (ochre, oxblood, aubergine, slate; `Guide.module.css` `.side::before`, owner 2026-10-15). |
| `SiteFooter` | The GitHub link with its icon, the other links, and the credit line, whose "N games archived" is live (`GamesArchived`, the archive's `X-Total-Count`). |
| `Button` | Mantine Button narrowed to the kit's three variants (below): `well` (the default), `plate` and `text`. Polymorphic. |
| `GuideSign` | The guide's one look wherever a page points at it: the navy enamel and the open book (`Book`, which the nav's sign draws too), a size up for a page: under the hero's tickets, under the roles. |
| `PlateTabs.module.css` | The site's plain tabs, composed by any tab set that is not itself a picture: dark tabs, the chosen one a brass plate; `small` inside a panel. |
| `Paper` | The paper surface for things inside the fiction. Polymorphic Box. |
| `Flapword` | Split-flap tiles for one word, with `tone` `hot` or `dim`. |
| `Icon` / `IconSprite` | One `<symbol>` sprite, rendered once by the site layout. It holds `i-*` (the mockups' icons plus `i-lock-open`, `i-ticket` and `i-github`) and `sg-*`, whose paths are the stage's `Sigil`. |

## The controls kit (owner 2026-10-15)

Every clickable thing on the site pages is one of three kinds (the census and sort are on the
bench https://claude.ai/artifact/XktnahYzDTKqxhG61TrqBe):

- **Station objects** carry a meaning, so they keep their own look and are one component each,
  used wherever that meaning appears: the paper tag (a way to play), the slate (a game), the
  enamel sign (the guide), the signboard's doors, the role card and sigil disc, the puppet head,
  the guide's railway stops and folder tabs, the features' brass plates, the carriage's player.
  They are built on Mantine's behaviour (UnstyledButton, Radio) where they need it.
- **Everyday controls** are Mantine components with our variants, and take their colours from
  the surface under them. `Button`: `plate` (the riveted cream plate, owner 2026-10-15) is the one main action of a view, `well` every other
  button (a way to another page included), `text` a word that acts. Links are Mantine's
  `Anchor`, always underlined. One switch, one select, one chip, one set of plain tabs
  (`PlateTabs`).
- **Surfaces** set `--ctl-*` (`styles/tokens.css`) and the controls read them: the dark is the
  default (amber text and links, the recessed well), and `data-surface="paper"` turns them to ink
  (`Paper` sets it; so does any paper card with a control on it). A control never picks its own
  colours, so a new background needs a surface block, not a new button.

A new one-off look for a job that already has one is the thing to avoid: reach for a variant, or
add one to the kit. The stage keeps its own controls (`ActPlate`, the placards) and never imports
these.

The facts the chrome shows (name, author, GitHub, nav, footer links, year, and the landing's featured
replay) live in `src/lib/site.ts`, with TODOs for the owner. Characters and chips come from `src/assets/manifest.ts`
and `ChipSprite`, never from the strips inlined in the mockups (review §B6).

## The landing's platform and carriage (redesign 2026-10-14 §2–4)

- The hero is a picture (owner, 2026-10-18): the night platform as a handmade set (felt cast, the
  wooden toy carriage), filling the first screen from the page's top, behind the nav's board, to the
  fold. Two files, `assets/site/hero-wide.webp` (1536×1024) and `hero-tall.webp` (1024×1536, a
  screen taller than wide), in one `<picture>`, so a screen fetches only its own; still, no filter;
  its foot fades to the ground; on a wide screen the carriage's section starts just under it, on a
  phone after a breath of dark, below the first screen (owner 2026-10-18). Masters in
  `claude_artifacts/design/rasters/wood/hero/`, fitted by `scripts/fit-hero.mjs`.
- The words stay words over its calm sky (Landing.module.css `.heroText`): the game's name, a gold
  rule with the brand's 9 (`HeroRule`, vector), the hook, the two tickets, the purse (HouseDoorNote,
  outlined to read over the picture) and the guide's sign. On a wide screen they sit centre-left,
  their middle at 31% of the screen (27% under 1366px, smaller again under 1100px) so the tickets
  clear the cat and the fox; on a phone centred, the name on two lines, the passengers under them, and the purse and the
  guide's sign at the screen's foot (`.heroFoot`, owner 2026-10-18). The foot keeps at least the
  passengers' height under the tickets, so a short phone runs the hero past the fold rather than
  lay the sign over them.
- The tickets (`HeroTicket`, the landing's, the departures hall's and the ticket office's, where
  `current` marks the page's own kind) are
  flat cream card on the scene: the shape (scalloped ends, a notch each side, a bite out of the top)
  is a mask, so it stays round at any size, and the fibre is one 512 px tile (`ticket-paper.webp`)
  under both. A wide screen shows the kicker, the line and a ruled foot ending in the arrow (the
  tables boarding are the nav's count alone); a
  phone, and a portrait tablet (860px and under, the site's phone layout), the title and the way
  in. A hover lifts the ticket and nudges its arrow.
- `.landing` sets `--lx`/`--rx`, where the platform's lamps hang, which the carriage's light
  reads. (`PlatformBackdrop`, the vector wall the landing and then the hall stood on, is in git
  history.)
- Behind the carriage, the night (owner, 2026-10-18: a gradient, not a second picture after the
  hero's): black for the top half, then a dark blue down to the wheels, with snow falling through
  the black and gone by two thirds of the way down (`.night`). The page's one idle motion outside the theatre, kept cheap: two sheets of flakes
  drawn once, each moved by a transform (two layers, behind the carriage, never over the game's
  window), started when the carriage comes near, still for reduced motion.
- `FeaturedReplay` is the replay theatre's mini mode in the big window of a carriage standing at the
  platform. Over 860px the whole carriage (end, door, window, door, end) with the replay's controls
  on the stage; at 860px and under, the window edge to edge and the controls on the platform beneath
  it (`CarriageUnder`: one playback board whose sleepers seek). The phone preview has no
  transcript or Reveal pane (owner, 2026-10-14: they did not fit beside the carriage, and the
  Reveal pane drew a second stage); the whole replay has both, and the gameplay guide explains
  them. A roof board names the game (its ID as split-flap tiles, read once as
  `role="img"`) and its model; under the platform, the details and "Watch the whole game".
- The carriage is painted with pieces cut from the waiting room's train (`scripts/cut-carriage.mjs`
  → `SPRITES.carriage`): the snowy roof's bay, the brass rail, a mirrored seamless teak tile, the
  window's brass rim (a 9-slice laid round the glass with `border-image-outset`, so it never paints
  over the game; its rivets repeat), a bogie, the solebar and the bellows. Each shows at half its
  painted size (sharp on a 2× screen; the painting is only 700px tall, so nothing is enlarged).
  They arrive with the theatre when the carriage comes near, over a CSS stand-in drawn until
  then; `data-art` and `--art-*` go on the figure only once the screen's whole-carriage picture
  is decoded (`useDecoded`): switched at once, a cold first visit showed the window and its loader
  alone in the night for seconds (owner, 2026-10-18). The whole scene comes up at once (owner,
  2026-10-18): until the picture is in and the game is painted in its window, the section (the
  night, the board, the carriage, the details) is the house's loading picture (`.gate`,
  `data-ready`), 10 s at most. It is asked for as soon as the page's first screen is up
  (`usePageOpen`), not when it comes near, so it is usually ready before it is seen: a visitor
  who never scrolls now fetches it too (owner's call over the audit of 2026-10-11 §2). The doors stay drawn in CSS over the teak: the
  painting's doors are a third of the height this carriage needs; sharper doors, ends and bogies
  for a desktop want a larger source.
- Performance rules it keeps: nothing decorative is painted over the game's window (an overlay above
  a moving stage is lifted onto layers with it), and the stage is clipped by a plain rectangle (a
  rounded clip round moving layers costs a mask the window's size); the 6px corner is the frame's.
  Every decorative layer is still and capped to what it decorates. The figure spans the screen
  (`margin-inline: calc(50% - 50vw)`) and clips its own sideways overflow; the page clips too while
  the landing is on it (`html:has(.landing)`).

## The landing's rooms (rooms benches, owner 2026-10-14)

- Under the carriage the story, the features and the replay (with the latest games) stand on one
  wall (owner, 2026-10-18): the station's navy panelling, a band of it repeated as far as the
  rooms run, laid upright and mirrored so no join shows (`.navy` in `Rooms.module.css`;
  `scripts/fit_walls.py`, a tall set for a screen taller than wide). Its lamp, cut from the
  picture with the wall round it fading to clear, hangs just above "What makes it different"
  (`.lamped`), and the board runs close into the replay's room. The
  wall rises out of the dark from the carriage above and sinks back into it before the brass
  threshold and the closing word, which stand on the page's own dark. The story opens it: its
  line "Ten puppets share a carriage, but not a destination." as the title, the brand's gold rule
  under it (`HeroRule`), then the rest centred in Literata and the Reveal line in the site's
  sans. The footer follows the closing close (`.last`). The drawn rooms before it (granite under
  a caged wall light, the platform's tile under a pendant) are in git history.
- "What makes it different" is drawn in the owner's material kit (2026-10-18;
  `scripts/fit_kit.py` → `src/assets/site/kit/`, masters in `claude_artifacts/design/rasters/wood/kit/`):
  a walnut board (a 314px tile) in a brass rim with a screw in each corner, each card on one sheet
  of the kit's card paper and each slip on its cream (laid once, never repeated: the masters'
  light falls off to their corners), the brass name plates a 9-slice of the kit's plate (screwed
  ends kept, the middle stretched to the name; narrower ends as the phone's tabs, the unchosen
  ones dimmed by opacity), the paperclip on the lesson slip, and the FOLLOWED stamp masked by the
  worn-ink speckle. About 70 KB, nothing moves. The mock's shorter copy was not taken (owner: the
  card text stays, the lesson and the drafted line are real).
- "At the end of the line" (the replay's exhibit, `ReplayMoment`) in the same kit (owner,
  2026-10-18, mock-replay-moment): a case file on walnut, its "Day 2 · Seat 10, the Chanteuse" on
  a brass plate; in a kraft folder (its top edge the kit's tab as a 9-slice) the line said aloud
  on card paper ruled in red under a red ribbon, a brass pin (`brass-disc` heads) down to its
  private note typed on ruled cream with the paperclip, the note's own "Do not disclose:" marked
  in red pencil, and what came of it inside a ruled edge on the kraft. Copy unchanged.
- The landing's words (owner, 2026-10-15): every quoted agent line is a real one, verbatim, at
  the seq `landing/features.ts` names. The memory card's slip is game 2f19d908's Sigilist
  following a lesson; the replay section's moment is game 68c26e83's Chanteuse claiming the
  Investigator (also the carriage's game, day 2); the draft card's notes are the one thing
  written for the demo, and its caption says so. The closing states the research as it stands:
  the pipeline is built, earlier versions were tested (gains and failures), and the current
  version (v8) has not been tested at scale, so whether it improves play is open. Its "Read the
  case study" plate goes to `SITE.caseStudy`, for now the memory research's history in the repo
  (`evidence/memory_system/store_progression.md` on `main`).

## The other pages' walls

Each site page has its room's wall behind it (`StationWall`, owner 2026-10-18,
`scripts/fit_walls.py`): the guide (`cards`) a green room with a lamp by the title, its wood trim
cut off; the ticket office (`granite`, `/play` and `/play/room`) brick over panelling beside a
window. The archive (`records`) keeps its drawn room, the platform's tile with an oxblood band
under a pendant: its filing-room picture was tried and the owner preferred the drawn one. The
guide's wall runs to the page's foot (the picture, then a mirrored band of its lower wall); the
ticket office's lower wall is panelling and floor, which would stack if repeated, so its picture
fades out. Each has a tall picture for a screen taller than wide. A screen fetches its own
picture and band, about 60–150 KB.

## The departures hall (owner's mock and raster kit, 2026-10-18)

- The night platform's wall, one still picture from the page's top; over it the title beside the
  landing's two paper tickets (`HeroTicket`, a size down). At 860px and under (owner) the title
  is larger and centred alone over the tickets, the lede left out, the tickets stubs. A
  passenger waits on the bench, and the board never stands over them (owner):
  - a screen wide enough (`BESIDE` in rooms/page.tsx, the same three aspect bands in the module:
    width at least 922px + 0.575 × height): the wall is the bench itself (`hall-wide.webp`,
    1774×887) and the column (940px) stands right of the passenger;
  - any other: the wall is empty (`hall-wall.webp` on a landscape screen; on a portrait one the
    tall picture's wall above its bench, `hall-tall.webp`, drawn wide), and the bench is the
    page's last picture, a band after the board (`.bench`: the wide picture's lower part, or the
    tall one's, capped at 420px on a tablet). It is lazy, so a wide screen never fetches it, and
    a phone draws both from its one tall file.
- The board's case is three pictures, backgrounds so a screen fetches only its size's set: the
  head (brass plate, clock, plaque), a middle repeated down as far as the rows go, the foot;
  the phone has its own (thinner rims). The words on the plate and the plaque are live and scale
  with the board (`cqi`); the plaque says whether the board is kept up to date (`Live`,
  `Retrying`, `Reading`, `Offline`), never the count, which is the nav's. Fitted by
  `scripts/fit_hall.py` from `claude_artifacts/design/rasters/wood/rooms/`: it cleans the
  masters' cut-out fringe, builds each middle from its own head's sides, and tapers each foot
  into them. A screen fetches 230–280 KB of pictures; nothing moves.

## Pages come up whole (owner, 2026-10-18)

Every site page (the landing, the departures hall, the archive, the guide, the ticket office)
starts with `PageGate` in its `<main>`: until the pictures on its first screen and its fonts are
decoded, the page under the nav and the footer are hidden (`html[data-gate]`) behind the house's
loading picture, then fade in at once while the loader fades off. A cold first visit had shown
the words on bare black and each wall painting in from the top. The gate finds the pictures
itself (the `<img>`s and the computed backgrounds, `::before`/`::after` included, of whatever is
on the screen), so a page lists nothing; what is further down loads as before. The loader comes
up after 1 s (under a second a wait needs no sign) and, once up, stays at least 2 s so it is seen,
never a blink (owner, 2026-10-18); a page ready before 1 s is simply there, with no fade, so a
cached visit never sees it. A page reached by a click counts that second from the click, and the
site loader (`(site)/loading.tsx`, also 1 s) hands its train to the page's gate without a break;
what the two share is kept on the window (`__gateNav`), since the build gives each its own copy
of PageGate's module, and follows `(site)/loading.tsx`'s at once
(`RouteWaitMark`) so the train never goes and comes back; 8 s ends the wait. The wait itself
(`gate`) is written into the page as its inline script, so it runs as the page arrives, not once
React is up: a cached visit comes up 100–230 ms after the request, a click between pages 100–340
ms, the loader never seen (measured 2026-10-18; waiting for React first had cost a cached visit
over a second). A click runs the same function from React, which does not run a script it puts
on the page. The page is hidden by that script, never by the stylesheet alone, so a crawler or a
reader without script gets the page as it is (a stylesheet fallback shows it after 10 s should
the script never run). The function must stay plain script that uses nothing from outside itself
(`toString`). Next, React and Mantine have nothing for this: Suspense waits on code and data, not
pictures, and `next/image` only knows one picture at a time.

## The tickets on a phone

At 860px and under (the site's phone layout) a `HeroTicket` is its stub: the title and an arrow
on one line, two side by side, centred under the page's title on the departures hall and the
ticket office, under the tagline on the landing. The ticket office's other kind is faded
(`opacity`), full on hover. (`HangTag`, the hung tag before them, is in git history.)

## Tests

- `src/theme/tokens.test.ts` (vitest) checks the token bridge.
- `e2e/site.spec.ts` (Playwright) checks that each site page has the nav with "The Ninth Express" and
  the footer with the GitHub link, and that `/workbench/day` has neither. The theatre's goldens
  must stay identical. `routeChrome` answers the chrome's own reads (the Rooms counter, the
  footer's total) so a page's golden never depends on a running API.
