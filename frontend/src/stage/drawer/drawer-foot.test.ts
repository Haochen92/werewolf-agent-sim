import { describe, expect, it } from 'vitest';
import { atFoot } from './Drawer';

describe('the drawer’s foot', () => {
  it('is the very bottom of the lines, within a few pixels', () => {
    const at = (scrollTop: number) =>
      atFoot({ scrollHeight: 1000, clientHeight: 400, scrollTop });
    expect(at(600)).toBe(true);
    expect(at(596)).toBe(true);
    expect(at(595)).toBe(false);
    expect(at(0)).toBe(false);
    // lines shorter than the drawer: always at the foot
    expect(atFoot({ scrollHeight: 300, clientHeight: 400, scrollTop: 0 })).toBe(true);
  });
});
