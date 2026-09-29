/**
 * The stage's faces. The HUD speaks in two voices (owner, 2026-09-29): Young Serif for what is
 * engraved or announced (the day plaque, the nameplates, the tabs, the seat numerals on brass)
 * and Literata for what people say and read (the speeches, the transcript, the dock). IM Fell
 * English (the old serif) stays for what is printed on paper, like the seat numerals on the
 * puppets and the case file's titles; Patrick Hand for pencil (the case file's margin notes);
 * Courier Prime, the case file's typewriter, for its labels, tabs and stamps only (its long
 * text is Literata); Outfit (the sans) for the few plates that still ask for it by name.
 * Loaded with next/font so they are self-hosted and never flash in late.
 *
 * Kept out of Stage.tsx on purpose: next/font only works inside a Next build, and the stage's
 * components are also imported by the unit tests. A page that shows a stage puts
 * `stageFonts` on an ancestor; the stage reads the CSS variables they define.
 */
import {
  Courier_Prime,
  IM_Fell_English,
  Literata,
  Outfit,
  Patrick_Hand,
  Young_Serif,
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

const display = Young_Serif({
  weight: '400',
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
