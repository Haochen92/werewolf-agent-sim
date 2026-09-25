/**
 * A role's sigil: the small line mark that stands for a role wherever there is no room for
 * its figure (a dead seat's tile in the wing, the X-ray badge, a card's corner). Drawn in
 * `currentColor` with no stroke width of its own, so the place that shows it decides the
 * colour (usually the faction's) and the weight.
 *
 * Ported from the design bundle's role kit (kits/role-kit.js, `RoleKit.sigil`), same paths.
 */
import type { SVGProps } from 'react';

const PATHS: Record<string, React.ReactNode> = {
  villager: <path d="M6 20 L20 8 L34 20 M10 18 V32 H30 V18 M17 32 V24 H23 V32" />,
  healer: <path d="M16 7 H24 V16 H33 V24 H24 V33 H16 V24 H7 V16 H16 Z" />,
  investigator: (
    <>
      <circle cx="17" cy="17" r="9" />
      <path d="M24 24 L34 34" />
    </>
  ),
  vigilante: (
    <>
      <path d="M14.5 29 V17 Q14.5 7.5 20 5.5 Q25.5 7.5 25.5 17 V29 Z" />
      <path d="M14.5 23 H25.5" />
      <path d="M12 33 H28" />
    </>
  ),
  wolf: <path d="M25 5 A15.5 15.5 0 1 0 35 27 A12 12 0 0 1 25 5 Z" />,
  serial_killer: (
    <>
      <path d="M30 37 L24 4" />
      <path d="M24.5 5 C14 2 5 8 4 19 C9 11.5 16 9.5 25.3 11" />
    </>
  ),
};

export function Sigil({ role, ...rest }: { role: string } & SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 40 40"
      fill="none"
      stroke="currentColor"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
      {...rest}
    >
      {PATHS[role] ?? null}
    </svg>
  );
}
