/**
 * The stage's faces (docs/typography.md, owner 2026-10-16): EB Garamond for the signs and
 * headings (the day plaque, the nameplates, the seat tab, the drawer's titles) and Literata for
 * everything said and read, and at 600 for the small text and the controls (the tabs, the
 * buttons, the seat numbers). IM Fell English stays for what is printed on paper, like the seat
 * numerals on the puppets and the case file's titles; Patrick Hand for pencil (the case file's
 * margin notes); Courier Prime, the case file's typewriter, for its labels, tabs and stamps only
 * (its long text is Literata); Outfit (the sans) for the few plates that still ask for it by
 * name. Young Serif, the engraved voice until 2026-10-16, is gone. Loaded with next/font so they
 * are self-hosted and never flash in late.
 *
 * Kept out of Stage.tsx on purpose: next/font only works inside a Next build, and the stage's
 * components are also imported by the unit tests. A page that shows a stage puts
 * `stageFonts` on an ancestor; the stage reads the CSS variables they define.
 */
import {
  Courier_Prime,
  EB_Garamond,
  IM_Fell_English,
  Literata,
  Outfit,
  Patrick_Hand,
} from 'next/font/google';

const sans = Outfit({
  weight: ['400', '500', '600', '700'],
  subsets: ['latin'],
  variable: '--font-stage-sans',
  display: 'swap',
});

const serif = IM_Fell_English({
  weight: '400',
  style: ['normal', 'italic'],
  subsets: ['latin'],
  variable: '--font-stage-serif',
  display: 'swap',
});

const hand = Patrick_Hand({
  weight: '400',
  subsets: ['latin'],
  variable: '--font-stage-hand',
  display: 'swap',
});

const display = EB_Garamond({
  weight: '600',
  subsets: ['latin'],
  variable: '--font-stage-display',
  display: 'swap',
});

const body = Literata({
  weight: ['400', '500', '600'],
  style: ['normal', 'italic'],
  subsets: ['latin'],
  variable: '--font-stage-body',
  display: 'swap',
});

const type = Courier_Prime({
  weight: ['400', '700'],
  subsets: ['latin'],
  variable: '--font-stage-type',
  display: 'swap',
});

/**
 * Class names that define `--font-stage-sans`, `--font-stage-serif`, `--font-stage-hand`,
 * `--font-stage-display`, `--font-stage-body` and `--font-stage-type`.
 */
export const stageFonts = `${sans.variable} ${serif.variable} ${hand.variable} ${display.variable} ${body.variable} ${type.variable}`;
