import { describe, expect, it } from 'vitest';
import { ENDING, LYNCH, beatAt, isLoop, measure, startOf, timeline } from './timelines';

describe('the music bench timelines', () => {
  it('lays the lynch out as the replay plays it: 24 s, Voted out at 6 s, the truth at 14 s', () => {
    const line = timeline(LYNCH, 'normal');
    expect(line.at(-1)?.end).toBe(24);
    expect(startOf(line, 'named')).toBe(6);
    expect(startOf(line, 'truth')).toBe(14);
  });

  it('halves every hold on Fast', () => {
    const line = timeline(LYNCH, 'fast');
    expect(line.at(-1)?.end).toBe(12);
    expect(startOf(line, 'truth')).toBe(7);
  });

  it("finds the beat at a time, and the winners' hour 8 s into the ending", () => {
    const line = timeline(ENDING, 'normal');
    expect(beatAt(line, 9)?.id).toBe('winners-hour');
    expect(beatAt(line, -1)).toBeNull();
    expect(beatAt(line, 999)).toBeNull();
  });
});

describe('measuring a track', () => {
  const sr = 1000;
  const tone = (s: number, amp: number) =>
    Float32Array.from({ length: s * sr }, (_, i) => amp * Math.sin(i / 3));

  it('reads a steady tone as a loop at its level', () => {
    const m = measure([tone(2, 0.1), tone(2, 0.1)], sr);
    expect(m.duration).toBe(2);
    expect(m.rms).toBeCloseTo(-23, 0);
    expect(isLoop(m)).toBe(true);
  });

  it('reads a tone that ends in a second of silence as a one-shot', () => {
    const c = new Float32Array(3 * sr);
    c.set(tone(2, 0.1));
    const m = measure([c], sr);
    expect(m.silentTail).toBeCloseTo(1, 1);
    expect(isLoop(m)).toBe(false);
  });
});
