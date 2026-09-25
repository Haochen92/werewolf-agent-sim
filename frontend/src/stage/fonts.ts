/**
 * The stage's faces, as the benches use them: Outfit (the sans) for everything on dark,
 * IM Fell English (the old serif) for what is printed on paper, like the seat numerals on the
 * puppets, and Patrick Hand for the agents' own notes on the X-ray film's paper slips.
 * Loaded with next/font so they are self-hosted and never flash in late.
 *
 * Kept out of Stage.tsx on purpose: next/font only works inside a Next build, and the stage's
 * components are also imported by the unit tests. A page that shows a stage puts
 * `stageFonts` on an ancestor; the stage reads the two CSS variables it defines.
 */
import { IM_Fell_English, Outfit, Patrick_Hand } from 'next/font/google';

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

/** Class names that define `--font-stage-sans`, `--font-stage-serif` and `--font-stage-hand`. */
export const stageFonts = `${sans.variable} ${serif.variable} ${hand.variable}`;
