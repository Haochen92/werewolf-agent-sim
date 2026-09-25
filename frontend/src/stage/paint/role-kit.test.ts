import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { describe, expect, it } from 'vitest';
import { CARD_TEXT } from '../card-text';
import { roleAvatar, roleFigure } from './role-kit';

/* The port must draw the kit's dolls: the frozen kit, evaluated as-is, is the reference. */
describe('fidelity to kits/role-kit.js', () => {
  const src = readFileSync(
    fileURLToPath(
      new URL('../../../docs/design_2026-09-25/kits/role-kit.js', import.meta.url),
    ),
    'utf8',
  );
  const Kit = new Function(`${src}; return RoleKit;`)();
  // prettier re-spaced the template literals; the markup is the same once whitespace is folded
  const fold = (s: string) => s.replace(/\s+/g, ' ').replace(/> </g, '><').trim();

  for (const role of Object.keys(CARD_TEXT)) {
    it(`draws the ${role} as the kit does`, () => {
      expect(fold(roleFigure(role))).toBe(fold(Kit.fig(role)));
      expect(fold(roleAvatar(role))).toBe(fold(Kit.avatar(role)));
    });
  }
});
