/**
 * The site's design tokens, from the landing mockup's `:root` (claude_artifacts/design/pages/
 * landing.html), as one table that both the Mantine theme and `styles/tokens.css` follow.
 *
 * Two kinds of token live here. Site-only roles (the page ground, panels, text, radii) keep the
 * landing's names and values. Materials the site shares with the theatre (paper, ink, bone, the
 * faction colours) take the theatre's name and the theatre's value, read straight from the
 * stage's `vars()`, so a site page and the stage can never disagree about what "wolf" looks like.
 * `tokens.test.ts` holds `tokens.css` to this table.
 */
import { vars } from '@/stage/paint/materials';

type CssVar = `--${string}`;

/** Site-only tokens: the landing mockup's names and values. */
export const SITE_TOKENS = {
  '--bg': '#0c0a07',
  '--panel': '#17130e',
  '--panel-2': '#211b14',
  '--line': 'rgba(255, 235, 200, 0.08)',
  '--text': '#f1e8d6',
  '--muted': '#a3947c',
  '--paper-dk': '#cbb992',
  '--ink2': '#5e4a33',
  '--brass': '#c9a25e',
  '--red': '#c8392b',
  '--amber-hi': '#f0b94a',
  '--r-s': '12px',
  '--r-m': '20px',
  '--r-l': '28px',
  '--shadow': '0 24px 44px -22px rgba(0, 0, 0, 0.9)',
  '--site-max': '1160px',
  '--gutter': '28px',
} as const satisfies Record<CssVar, string>;

/**
 * The theatre's materials the site uses too. The mockups disagree with the theatre on some of
 * these (`--bone2` #a3947c, `--bone3` #7f735f; `--killer` for `--sk`); the theatre wins.
 */
export const THEATRE_NAMES = [
  '--ink',
  '--bone',
  '--bone2',
  '--bone3',
  '--cloak1',
  '--cloak2',
  '--paper',
  '--amber',
  '--town',
  '--wolf',
  '--sk',
  '--town-ink',
  '--wolf-ink',
  '--sk-ink',
  '--benign',
  '--benign-ink',
  '--film',
  '--sure',
] as const satisfies readonly CssVar[];

const STAGE = vars();

export const THEATRE_ALIASES = Object.fromEntries(
  THEATRE_NAMES.map((name) => [name, STAGE[name]]),
) as Record<(typeof THEATRE_NAMES)[number], string>;

/** Every token the site defines, by CSS custom property name. */
export const TOKENS: Record<CssVar, string> = { ...SITE_TOKENS, ...THEATRE_ALIASES };

/** The type stacks. The `--font-site-*` variables are set by next/font in `theme/fonts.ts`. */
export const FONT_SANS =
  'var(--font-site-sans, Outfit), "Helvetica Neue", Arial, sans-serif';
export const FONT_SERIF = 'var(--font-site-serif, "IM Fell English"), Georgia, serif';
