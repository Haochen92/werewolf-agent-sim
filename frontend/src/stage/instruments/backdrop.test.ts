/**
 * The backdrop's sheet is chosen by the pixels the stage is drawn at (`pickScale`): the stage's
 * measured width × the screen's density × the camera's closest push-in, against the sheets'
 * widths (2200, 3300, 4400), a small stage capped at 1.5. The cases are the audit's
 * (docs/frontend-audit-2026-10-11.md §1).
 */
import { describe, expect, it } from 'vitest';
import { pickScale } from './Backdrop';

const PHONE_CAP = 1.5;
const DESK_CAP = 2;

describe('pickScale', () => {
  it("gives the landing's carriage on an upright phone the 2200 sheet, not the 3300", () => {
    // the carriage's stage is 334 css px wide at 390: 334 × 3 × 1.32 ≈ 1323 px
    expect(pickScale(334, 3, PHONE_CAP)).toBe('1');
  });

  it('keeps the 3300 sheet for a landscape theatre on the same phone', () => {
    // the sheet shows 953 css px with its bleed, so the stage is 693: 693 × 3 × 1.32 ≈ 2744
    expect(pickScale(693, 3, PHONE_CAP)).toBe('1.5');
    // and never the 4400 on a small stage, however dense the screen
    expect(pickScale(1100, 3, PHONE_CAP)).toBe('1.5');
  });

  it('gives a 1600 px desktop stage the 2200 sheet at density 1 and the 4400 at 2', () => {
    expect(pickScale(1600, 1, DESK_CAP)).toBe('1'); // 2112
    expect(pickScale(1600, 2, DESK_CAP)).toBe('2'); // 4224
    // the landing's carriage on a desktop: 1052 css px
    expect(pickScale(1052, 1, DESK_CAP)).toBe('1'); // 1389
    expect(pickScale(1052, 2, DESK_CAP)).toBe('1.5'); // 2777
  });

  it('takes the largest sheet when even it falls short', () => {
    expect(pickScale(2560, 2, DESK_CAP)).toBe('2');
  });

  it('trades up at once but down only once the smaller sheet fits with room', () => {
    // 1667 css px at density 1 needs 2200.4: just over the 1× sheet
    expect(pickScale(1667, 1, DESK_CAP, '1')).toBe('1.5');
    // back under the boundary by a pixel: the 3300 sheet stays
    expect(pickScale(1666, 1, DESK_CAP, '1.5')).toBe('1.5');
    expect(pickScale(1550, 1, DESK_CAP, '1.5')).toBe('1.5');
    // 10% under (1490 css px, 1967 px): the 2200 sheet comes back
    expect(pickScale(1490, 1, DESK_CAP, '1.5')).toBe('1');
    // with nothing shown yet, the plain pick
    expect(pickScale(1666, 1, DESK_CAP)).toBe('1');
  });

  it('drops a kept sheet the cap no longer allows', () => {
    // a desktop stage shrunk to a phone's size: the 4400 sheet goes at once
    expect(pickScale(1100, 3, PHONE_CAP, '2')).toBe('1.5');
  });
});
