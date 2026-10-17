import { describe, expect, it, vi } from 'vitest';
import {
  BLIP_MS,
  briefDrop,
  CATCH_UP_GATHER_MS,
  catchUpBatch,
  catchUpBoundary,
  reopenNow,
  STREAM_RETRY_MS,
  STREAM_SILENT_MS,
  streamStalled,
} from './catch-up-boundary';

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

describe('reopening the stream when the page comes back', () => {
  it('reopens a stream that is reconnecting or closed, at once', () => {
    expect(reopenNow(0, false)).toBe(true); // the browser's own retry, still waiting
    expect(reopenNow(2, false)).toBe(true); // the browser gave up
  });

  it('leaves an open stream alone, and does nothing while the page is hidden', () => {
    expect(reopenNow(1, false)).toBe(false);
    expect(reopenNow(0, true)).toBe(false);
    expect(reopenNow(2, true)).toBe(false);
  });
});

describe('the catch-up block', () => {
  it('hands on the frames that arrive together as one block, and news flushes it first', () => {
    vi.useFakeTimers();
    const blocks: number[][] = [];
    const batch = catchUpBatch<number>((b) => blocks.push(b));
    for (let seq = 1; seq <= 300; seq++) batch.add(seq);
    expect(blocks).toEqual([]);
    vi.advanceTimersByTime(CATCH_UP_GATHER_MS);
    expect(blocks).toHaveLength(1);
    expect(blocks[0]).toHaveLength(300);
    // more history, then news: the history goes on at once, before the news is applied
    batch.add(301);
    batch.flush();
    expect(blocks.at(-1)).toEqual([301]);
    batch.flush();
    expect(blocks).toHaveLength(2);
    // a closed stream's held frames go nowhere
    batch.add(302);
    batch.drop();
    vi.advanceTimersByTime(CATCH_UP_GATHER_MS);
    expect(blocks).toHaveLength(2);
    vi.useRealTimers();
  });
});

describe('a stalled stream', () => {
  it('is an open stream that has said nothing past a few pings, or a closed one, retried', () => {
    // open and pinging: alive
    expect(streamStalled(1, 15_000, false)).toBe(false);
    // open and silent past the pings: a dead connection held open (a phone's sleep)
    expect(streamStalled(1, STREAM_SILENT_MS + 1, false)).toBe(true);
    // closed for good by the browser: tried again, but not more than every few seconds
    expect(streamStalled(2, STREAM_RETRY_MS - 1, false)).toBe(false);
    expect(streamStalled(2, STREAM_RETRY_MS + 1, false)).toBe(true);
    // never while the page is hidden
    expect(streamStalled(2, STREAM_SILENT_MS * 10, true)).toBe(false);
  });
});

describe('briefDrop (2026-10-17)', () => {
  it('a drop under 20 s is a blip; longer is an absence', () => {
    expect(briefDrop(0)).toBe(true);
    expect(briefDrop(19_999)).toBe(true);
    expect(briefDrop(BLIP_MS)).toBe(false);
    expect(briefDrop(5 * 60_000)).toBe(false);
  });
});
