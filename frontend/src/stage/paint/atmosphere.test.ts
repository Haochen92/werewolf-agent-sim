import { describe, expect, it } from 'vitest';
import { carHaze } from './atmosphere';

describe('carHaze', () => {
  it('prefixes every id it makes, so two stages can share a page', () => {
    const html = carHaze({ id: 'q7', phase: 'night', hud: 'live' });
    const ids = [...html.matchAll(/id="([^"]+)"/g)].map((m) => m[1]);
    expect(ids.length).toBeGreaterThan(0);
    for (const id of ids) expect(id.startsWith('q7-')).toBe(true);
    for (const ref of html.matchAll(/url\(#([^)]+)\)/g)) expect(ids).toContain(ref[1]);
  });

  it('leaves the veil open round the painted lamps only when they are lit', () => {
    const holes = (phase: 'day' | 'night') =>
      (carHaze({ id: 'h', phase, hud: 'live' }).match(/fill="url\(#h-h\)"/g) ?? []).length;
    expect(holes('night')).toBe(3);
    expect(holes('day')).toBe(0);
  });

  it('casts the shutter’s pelmet’s shadow, and leaves the painted frame to its painting', () => {
    const html = carHaze({ id: 'c', phase: 'day', hud: 'live' });
    expect(html).toContain('url(#c-bframe)');
  });
});
