/**
 * The site's one SVG sprite: every icon the pages use, as `<symbol>`s that `Icon` points at
 * with `<use>`. Rendered once, by the site layout, so each page ships the paths a single time.
 *
 * Two families. `i-*` are the mockups' interface icons, on a 24 grid, stroked at 1.9 (plus
 * `i-github`, a filled mark). `sg-*` are the six role sigils on a 40 grid, stroked at 3.2; their
 * paths are the stage's own (`stage/instruments/Sigil`), so the site and the stage cannot drift.
 */
import type { ReactNode } from 'react';
import { PATHS as SIGIL_PATHS } from '@/stage/instruments/Sigil';

/** The interface icons, from the page mockups' sprite; `i-lock-open` and `i-ticket` are new. */
const ICONS = {
  'i-lock': (
    <>
      <rect x="5" y="11" width="14" height="10" rx="2" />
      <path d="M8 11 V8 a4 4 0 0 1 8 0 V11" />
    </>
  ),
  'i-lock-open': (
    <>
      <rect x="5" y="11" width="14" height="10" rx="2" />
      <path d="M8 11 V8 a4 4 0 0 1 7.6-1.7" />
    </>
  ),
  'i-link': (
    <>
      <path d="M10 14 a4 4 0 0 0 5.6 0 l3-3 a4 4 0 0 0-5.6-5.6 l-1 1" />
      <path d="M14 10 a4 4 0 0 0-5.6 0 l-3 3 a4 4 0 0 0 5.6 5.6 l1-1" />
    </>
  ),
  'i-eye': (
    <>
      <path d="M2 12 C5 6 19 6 22 12 C19 18 5 18 2 12 Z" />
      <circle cx="12" cy="12" r="3" />
    </>
  ),
  'i-copy': (
    <>
      <rect x="8" y="8" width="12" height="12" rx="2" />
      <path d="M16 8 V6 a2 2 0 0 0-2-2 H6 a2 2 0 0 0-2 2 v8 a2 2 0 0 0 2 2 h2" />
    </>
  ),
  'i-key': (
    <>
      <circle cx="8" cy="15" r="4" />
      <path d="M11 12 L20 3 M17 6 l2 2 M15 8 l2 2" />
    </>
  ),
  'i-x': <path d="M6 6 L18 18 M18 6 L6 18" />,
  'i-search': (
    <>
      <circle cx="11" cy="11" r="6" />
      <path d="M16 16 L21 21" />
    </>
  ),
  'i-minus': <path d="M6 12 H18" />,
  'i-plus': <path d="M6 12 H18 M12 6 V18" />,
  'i-play': <path d="M8 5 L19 12 L8 19 Z" />,
  'i-grid': (
    <>
      <rect x="4" y="4" width="7" height="7" rx="1" />
      <rect x="13" y="4" width="7" height="7" rx="1" />
      <rect x="4" y="13" width="7" height="7" rx="1" />
      <rect x="13" y="13" width="7" height="7" rx="1" />
    </>
  ),
  'i-list': <path d="M4 6 H20 M4 12 H20 M4 18 H20" />,
  'i-door': <path d="M6 21 V4 H15 V21 M15 12 H18 M3 21 H21" />,
  // an admission ticket: notched at both ends, perforated before the stub
  'i-ticket': (
    <>
      <path d="M3 7 H21 V10 a2 2 0 0 0 0 4 V17 H3 V14 a2 2 0 0 0 0-4 Z" />
      <path d="M15 7.5 V9 M15 11.25 V12.75 M15 15 V16.5" />
    </>
  ),
} satisfies Record<string, ReactNode>;

// the footer's GitHub mark (the landing mockup's), filled rather than stroked
const GITHUB =
  'M12 2a10 10 0 0 0-3.16 19.49c.5.09.68-.22.68-.48v-1.7c-2.78.6-3.37-1.34-3.37-1.34-.45-1.16-1.11-1.47-1.11-1.47-.91-.62.07-.61.07-.61 1 .07 1.53 1.03 1.53 1.03.89 1.53 2.34 1.09 2.91.83.09-.65.35-1.09.63-1.34-2.22-.25-4.55-1.11-4.55-4.94 0-1.09.39-1.98 1.03-2.68-.1-.25-.45-1.27.1-2.64 0 0 .84-.27 2.75 1.02a9.5 9.5 0 0 1 5 0c1.91-1.29 2.75-1.02 2.75-1.02.55 1.37.2 2.39.1 2.64.64.7 1.03 1.59 1.03 2.68 0 3.84-2.34 4.68-4.57 4.93.36.31.68.92.68 1.85v2.74c0 .27.18.58.69.48A10 10 0 0 0 12 2z';

export const SIGIL_ROLES = [
  'villager',
  'healer',
  'investigator',
  'vigilante',
  'wolf',
  'serial_killer',
] as const;

export type IconName =
  keyof typeof ICONS | 'i-github' | `sg-${(typeof SIGIL_ROLES)[number]}`;

export function IconSprite() {
  return (
    <svg
      width="0"
      height="0"
      style={{ position: 'absolute' }}
      aria-hidden="true"
      focusable="false"
    >
      {Object.entries(ICONS).map(([id, paths]) => (
        <symbol key={id} id={id} viewBox="0 0 24 24">
          <g
            fill="none"
            stroke="currentColor"
            strokeWidth="1.9"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            {paths}
          </g>
        </symbol>
      ))}
      <symbol id="i-github" viewBox="0 0 24 24">
        <path fill="currentColor" d={GITHUB} />
      </symbol>
      {/* the slate's printed-ink wobble (Slate.module.css); seeded, so every render is the same */}
      <filter id="inkwobble" x="-5%" y="-5%" width="110%" height="110%">
        <feTurbulence
          type="fractalNoise"
          baseFrequency="0.9"
          numOctaves="2"
          seed="7"
          result="n"
        />
        <feDisplacementMap
          in="SourceGraphic"
          in2="n"
          scale="1.6"
          xChannelSelector="R"
          yChannelSelector="G"
        />
      </filter>
      {SIGIL_ROLES.map((role) => (
        <symbol key={role} id={`sg-${role}`} viewBox="0 0 40 40">
          <g
            fill="none"
            stroke="currentColor"
            strokeWidth="3.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            {SIGIL_PATHS[role]}
          </g>
        </symbol>
      ))}
    </svg>
  );
}
