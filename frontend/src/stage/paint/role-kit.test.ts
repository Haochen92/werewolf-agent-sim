import { describe, expect, it } from 'vitest';
import { SPRITES } from '@/assets/manifest';
import { CARD_TEXT } from '../card-text';
import { roleAvatar, roleFigure } from './role-kit';

/* Every card role draws its painted doll; consumers size the <svg>, so its frame is the contract. */
describe('role figures', () => {
  for (const role of Object.keys(CARD_TEXT)) {
    it(`draws the ${role} from its sprite, whole and cropped`, () => {
      const src = SPRITES.roles[role as keyof typeof SPRITES.roles].src;
      const fig = roleFigure(role);
      expect(fig).toContain('viewBox="0 0 720 960"');
      expect(fig).toContain('aria-hidden="true"');
      expect(fig).toContain(`<image href="${src}" x="0" y="0" width="720" height="960"/>`);

      const av = roleAvatar(role);
      expect(av).toContain(`href="${src}"`);
      expect(av).toContain('preserveAspectRatio="xMidYMin slice"');
      // the crop stays inside the canvas and keeps the avatar box's 92:96
      const [x, y, w, h] = av.match(/viewBox="([^"]*)"/)![1].split(' ').map(Number);
      expect(x >= 0 && y >= 0 && x + w <= 720 && y + h <= 960).toBe(true);
      expect(w / h).toBeCloseTo(92 / 96, 2);
    });
  }

  it('draws nothing for a role without a sprite', () => {
    expect(roleFigure('mayor')).toBe('');
    expect(roleFigure('toString')).toBe('');
    expect(roleAvatar('mayor')).toBe('');
  });
});
