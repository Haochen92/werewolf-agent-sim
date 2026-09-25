import { describe, expect, it } from 'vitest';
import { catchUpBoundary } from './catch-up-boundary';

describe('the catch-up boundary', () => {
  it('on the first connection, history is everything up to the status’s last seq', () => {
    const b = catchUpBoundary(200);
    expect(b.isHistory(200)).toBe(true);
    expect(b.isHistory(201)).toBe(false);
  });

  it('after a drop, what the reconnect catches up on is history, news only after it', () => {
    const b = catchUpBoundary(200);
    expect(b.isHistory(210)).toBe(false); // news while connected
    b.dropped();
    // the server resends what was missed, newer than anything the page has: history
    expect(b.isHistory(215)).toBe(true);
    expect(b.resuming()).toBe(true);
    // the fresh status says the log has reached 230
    b.resumed(230);
    expect(b.resuming()).toBe(false);
    expect(b.isHistory(230)).toBe(true);
    expect(b.isHistory(231)).toBe(false);
  });

  it('a stale status never moves the boundary back', () => {
    const b = catchUpBoundary(200);
    b.dropped();
    b.resumed(150);
    expect(b.isHistory(200)).toBe(true);
  });
});
