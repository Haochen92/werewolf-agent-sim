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

Titles: the root layout's `metadata.title.template` is `Carriage Nine · %s`, so a page sets only its
own part (`'Rooms'`). `/` gets the default, `Carriage Nine`.

## Tokens: one table, the theatre wins

- `src/theme/tokens.ts` is the table. `SITE_TOKENS` holds the site-only roles, with the landing's
  names and values (`--bg --panel --panel-2 --line --text --muted --paper-dk --ink2 --brass --red
  --amber-hi --r-s/m/l --shadow --site-max --gutter`). `THEATRE_ALIASES` holds the names the site
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
  `--font-site-sans`, and IM Fell English (roman and italic) as `--font-site-serif`. They are set
  on `<html>` so that Mantine's portals get them too. `--font-sans` and `--font-serif` are the
  stacks, each with a fallback.
- The theatre keeps its own instances in `src/stage/fonts.ts` (`--font-stage-*`), applied by the
  theatre layouts. The Silkscreen pixel face is gone.

## Components (`src/components/site/`)

| Component | What it is |
|---|---|
| `TopNav` | The brand (the wolf's crescent on a paper disc, then the product name) and Play · Rooms · Replays. The current page's link carries `aria-current`. |
| `SiteFooter` | The GitHub link with its icon, the other links, and the credit line, whose "N games archived" is live (`GamesArchived`, the archive's `X-Total-Count`). |
| `Button` | Mantine Button narrowed to three variants: `ghost` (the default), `primary` (amber) and `brass` (a scene control on the page side; inside the stage box, use `ActPlate`). Polymorphic. |
| `HangTag` | The hung paper tag. With `href` it is a link (a door); with `onClick` and `pressed` it is a choice. |
| `Paper` | The paper surface for things inside the fiction. Polymorphic Box. |
| `Flapword` | Split-flap tiles for one word, with `tone` `hot` or `dim`. |
| `Icon` / `IconSprite` | One `<symbol>` sprite, rendered once by the site layout. It holds `i-*` (the mockups' icons plus `i-lock-open`, `i-ticket` and `i-github`) and `sg-*`, whose paths are the stage's `Sigil`. |

The facts the chrome shows (name, author, GitHub, nav, footer links, year, and the landing's featured
replay) live in `src/lib/site.ts`, with TODOs for the owner. Characters and chips come from `src/assets/manifest.ts`
and `ChipSprite`, never from the strips inlined in the mockups (review §B6).

## Tests

- `src/theme/tokens.test.ts` (vitest) checks the token bridge.
- `e2e/site.spec.ts` (Playwright) checks that each site page has the nav with "Carriage Nine" and
  the footer with the GitHub link, and that `/workbench/day` has neither. The theatre's goldens
  must stay identical.
