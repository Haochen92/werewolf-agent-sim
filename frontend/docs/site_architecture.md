# Site architecture: the pages around the theatre

The app has two halves with two toolkits. The **site** is the pages you move between: `/`, `/play`,
`/rooms`, `/rooms/new` and `/replays`. It is built from Mantine components themed from the page
mockups (`claude_artifacts/design/pages/*.html`, with `landing.html` as the style source). The
**theatre** is the stage: `/games/[id]`, `/replays/[id]` and `/workbench`. It is CSS modules over
`stage/paint/materials.ts` and never imports Mantine (stage_architecture.md). Rulings: review
`design_2026-09-26/pages_review.md` §F (F2 name, F3 Mantine stays and Silkscreen goes).

## Routes

`src/app/(site)/` is a route group. The parentheses keep it out of the URL, so the pages keep their
paths. Its `layout.tsx` wraps every site page in the shell: `IconSprite`, `TopNav`, the page, and
`SiteFooter`. The theatre's routes sit outside the group and get no nav. `/replays` (the archive,
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
- Themed components (`theme/components/*.module.css`): Button, Input/TextInput/Select, Switch,
  Tabs (pills), Modal, Notification, Table, Title and Alert. Anything else renders as stock Mantine over
  the warm scale.

## Fonts

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
| `TopNav` | The station's signboard (redesign 2026-10-14 §1): the headlamp mark and the name in EB Garamond, and Play · Rooms · Replays as recessed wells on a board hung from two brass rods; the current page is the cream plate (`aria-current`). Rooms carries a split-flap count of the tables boarding (`hooks/useBoarding`, the same query as the departures board). Once the board scrolls away a slim strip of it pins to the top (`inert` while hidden); its name drops cleanly when the doors need the room. On a phone the doors share a second row. |
| `Board.module.css` | The signage's materials, composed by every board on the site: `board` (wood in a brass frame: what you operate), `rivets`, `well` (a recessed button; `aria-current`/`-pressed`/`-selected` make it the cream plate), `plate` (the primary action) and `flap` (one split-flap tile). Paper carries what you read; brass is for lines and hardware, never a small flat fill. |
| `SiteFooter` | The GitHub link with its icon, the other links, and the credit line, whose "N games archived" is live (`GamesArchived`, the archive's `X-Total-Count`). |
| `Button` | Mantine Button narrowed to three variants: `ghost` (the default), `primary` (amber) and `brass` (a scene control on the page side; inside the stage box, use `ActPlate`). Polymorphic. |
| `HangTag` | The hung paper tag. With `href` it is a link (a door); with `onClick` and `pressed` it is a choice. |
| `Paper` | The paper surface for things inside the fiction. Polymorphic Box. |
| `Flapword` | Split-flap tiles for one word, with `tone` `hot` or `dim`. |
| `Icon` / `IconSprite` | One `<symbol>` sprite, rendered once by the site layout. It holds `i-*` (the mockups' icons plus `i-lock-open`, `i-ticket` and `i-github`) and `sg-*`, whose paths are the stage's `Sigil`. |

The facts the chrome shows (name, author, GitHub, nav, footer links, year, and the landing's featured
replay) live in `src/lib/site.ts`, with TODOs for the owner. Characters and chips come from `src/assets/manifest.ts`
and `ChipSprite`, never from the strips inlined in the mockups (review §B6).

## The landing's platform and carriage (redesign 2026-10-14 §2–4)

- `PlatformBackdrop` puts the hero on a night platform: a glazed-tile wall (`assets/site/wall-tile.svg`)
  under one mask so it shows only where light falls, two wall lamps, roof trusses, a vignette. One
  still box, capped at 1250px, under the landing's own stacking context (`isolation: isolate`: the
  body's ground would otherwise paint over a `z-index: -1` layer). `--lx`/`--rx`/`--ly` on the
  landing place the lamps and their light; the carriage's platform reads them too.
- `FeaturedReplay` is the replay theatre's mini mode in the big window of a carriage standing at the
  platform. Over 860px the whole carriage (end, door, window, door, end) with the replay's controls
  on the stage; at 860px and under, the window edge to edge and the controls on the platform beneath
  it (`CarriageUnder`: a playback board whose sleepers seek, Transcript and Reveal plates, the
  transcript on ruled paper). A roof board names the game (its ID as split-flap tiles, read once as
  `role="img"`) and its model; under the platform, the details and "Watch the whole game".
- The carriage is a CSS stand-in. Each part takes its picture from one variable (`--bay`,
  `--roof-tile`, `--lower-tile`, `--under-tile`, `--end-cap`, `--bogie`, `--door`), so the painted
  pieces cut from the room page's train can replace it without new markup.
- Performance rules it keeps: nothing decorative is painted over the game's window (an overlay above
  a moving stage is lifted onto layers with it), and the stage is clipped by a plain rectangle (a
  rounded clip round moving layers costs a mask the window's size); the 6px corner is the frame's.
  Every decorative layer is still and capped to what it decorates. The figure spans the screen
  (`margin-inline: calc(50% - 50vw)`) and clips its own sideways overflow; the page clips too while
  the landing is on it (`html:has(.landing)`).

## Tests

- `src/theme/tokens.test.ts` (vitest) checks the token bridge.
- `e2e/site.spec.ts` (Playwright) checks that each site page has the nav with "The Ninth Express" and
  the footer with the GitHub link, and that `/workbench/day` has neither. The theatre's goldens
  must stay identical. `routeChrome` answers the chrome's own reads (the Rooms counter, the
  footer's total) so a page's golden never depends on a running API.
