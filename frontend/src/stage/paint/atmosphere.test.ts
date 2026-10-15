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
      (carHaze({ id: 'h', phase, hud: 'live' }).match(/fill="url\(#h-h\d+\)"/g) ?? [])
        .length;
    // a pool each (and, where two pools overlap, a helper between them: holes.ts)
    expect(holes('night')).toBeGreaterThanOrEqual(3);
    expect(holes('day')).toBe(0);
    // the veil itself, its pools cut out of it
    expect(carHaze({ id: 'h', phase: 'night', hud: 'live' })).toMatch(
      /<path d="[^"]+" fill="url\(#h-v\)" fill-rule="evenodd"\/>/,
    );
  });

  it('casts the shutter’s pelmet’s shadow, and leaves the painted frame to its painting', () => {
    const html = carHaze({ id: 'c', phase: 'day', hud: 'live' });
    expect(html).toContain('url(#c-bframe)');
    // clipped round the pelmet, so it lies on the wall only
    expect(html).toMatch(
      /<clipPath id="c-m"[^>]*><path d="M0,0H1600V900H0ZM[^"]+" clip-rule="evenodd"\/>/,
    );
    expect(html).toContain('<g clip-path="url(#c-m)">');
  });

  // iPhone Safari kills a page that masks the stage (2026-10-01, stage_architecture.md §6)
  it('draws no SVG mask', () => {
    for (const phase of ['day', 'dusk', 'night', 'dawn'] as const)
      for (const side of [false, true]) {
        const html = carHaze({ id: 'n', phase, hud: 'live', side });
        expect(html).not.toContain('<mask');
        expect(html).not.toContain('mask="url(');
      }
  });
});
