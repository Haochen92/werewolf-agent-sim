import { describe, expect, it } from 'vitest';
import type { DurableGameEvent, ReplayGame } from '@/types/contracts';
import fixture from '@/game/__fixtures__/seed-chunk-catalogue.json';
import {
  cursorAfterNextPhase,
  cursorAtDay,
  dayAtCursor,
  groupBeats,
  visibleEventCount,
} from './replayPlayer';

const events = (fixture as unknown as ReplayGame).events as DurableGameEvent[];
const beats = groupBeats(events);

const LEADS = new Set([
  'game_started',
  'phase_change',
  'speech',
  'pass_marker',
  'gm_message',
  'vote_cast',
  'wolf_vote',
  'wolf_message',
  'night_action',
  'game_over',
]);

describe('groupBeats on the seed game', () => {
  it('tiles the log: every event in exactly one beat, in order, no gaps', () => {
    expect(beats[0].start).toBe(0);
    expect(beats[beats.length - 1].end).toBe(events.length);
    for (let i = 1; i < beats.length; i += 1) {
      expect(beats[i].start).toBe(beats[i - 1].end);
      expect(beats[i].end).toBeGreaterThan(beats[i].start);
    }
  });

  it('starts every beat on a lead, after any markers that announce it', () => {
    for (const beat of beats) {
      const members = events.slice(beat.start, beat.end);
      const first = members.find(
        (e) => e.type !== 'turn_started' && e.type !== 'input_request',
      );
      expect(first, `beat at ${beat.start} has only markers`).toBeDefined();
      expect(LEADS.has(first!.type), `beat at ${beat.start} leads with ${first!.type}`).toBe(true);
    }
  });

  it('keeps a speech together with the annotations about it', () => {
    const speech = events.findIndex((e) => e.type === 'speech');
    const beat = beats.find((b) => b.start <= speech && speech < b.end)!;
    const members = events.slice(beat.start, beat.end);
    expect(members.filter((e) => e.type === 'speech')).toHaveLength(1);
    // Annotations about this speech never open a beat of their own.
    expect(beats.some((b) => events[b.start].type === 'firing_reason')).toBe(false);
    expect(beats.some((b) => events[b.start].type === 'addressed_targets')).toBe(false);
  });

  it('releases each day’s vote batch as one beat', () => {
    const byDay = new Map<number, Set<number>>();
    beats.forEach((beat, index) => {
      for (const event of events.slice(beat.start, beat.end)) {
        if (event.type !== 'vote_cast') continue;
        if (!byDay.has(event.day)) byDay.set(event.day, new Set());
        byDay.get(event.day)!.add(index);
      }
    });
    expect(byDay.size).toBeGreaterThan(0);
    for (const [day, indices] of byDay) {
      expect(indices.size, `day ${day} votes span ${indices.size} beats`).toBe(1);
    }
  });

  it('gives every phase change a beat of its own, and dawn its deaths', () => {
    const phaseBeats = beats.filter((b) => b.kind === 'phase');
    expect(phaseBeats.length).toBe(events.filter((e) => e.type === 'phase_change').length);
    for (const beat of phaseBeats) {
      // Voters' strategy notes stream right after "voting begins" while their ballots
      // are buffered, so they ride on the phase beat; nothing else may.
      const real = events
        .slice(beat.start, beat.end)
        .filter(
          (e) =>
            e.type !== 'turn_started' &&
            e.type !== 'input_request' &&
            e.type !== 'strategy_update',
        );
      expect(real.map((e) => e.type)).toEqual(['phase_change']);
    }
    const dawn = beats.find(
      (b) => events.slice(b.start, b.end).some((e) => e.type === 'night_result'),
    )!;
    expect(dawn.kind).toBe('resolution');
    expect(events[dawn.start].type).toBe('gm_message');
  });

  it('holds for reading time within bounds, longest before a verdict, none after the end', () => {
    for (const beat of beats) {
      if (beat.kind === 'end') expect(beat.holdMs).toBe(0);
      else expect(beat.holdMs).toBeGreaterThanOrEqual(1500);
      expect(beat.holdMs).toBeLessThanOrEqual(8000 + 1500);
    }
    const resolution = beats.find((b) => b.kind === 'resolution')!;
    const turn = beats.find((b) => b.kind === 'turn')!;
    expect(resolution.holdMs).toBeGreaterThan(1500);
    expect(turn.holdMs).toBeGreaterThanOrEqual(1500);
  });
});

describe('cursor arithmetic', () => {
  it('reveals the prefix the cursor names', () => {
    expect(visibleEventCount(beats, 0)).toBe(0);
    expect(visibleEventCount(beats, 1)).toBe(beats[0].end);
    expect(visibleEventCount(beats, beats.length)).toBe(events.length);
    expect(visibleEventCount(beats, beats.length + 5)).toBe(events.length);
  });

  it('reports the day of the last revealed beat', () => {
    expect(dayAtCursor(beats, 0)).toBeNull();
    expect(dayAtCursor(beats, 1)).toBe(1);
    const lastDay = Math.max(...events.map((e) => e.day));
    expect(dayAtCursor(beats, beats.length)).toBe(lastDay);
  });

  it('skips to just past the next phase change, then to the end', () => {
    const firstPhase = beats.findIndex((b) => b.kind === 'phase');
    expect(cursorAfterNextPhase(beats, 0)).toBe(firstPhase + 1);
    const secondPhase = beats.findIndex((b, i) => i > firstPhase && b.kind === 'phase');
    expect(cursorAfterNextPhase(beats, firstPhase + 1)).toBe(secondPhase + 1);
    const lastPhase = beats.length - 1 - [...beats].reverse().findIndex((b) => b.kind === 'phase');
    expect(cursorAfterNextPhase(beats, lastPhase + 1)).toBe(beats.length);
  });

  it('jumps to a day’s first beat, which is the morning phase change', () => {
    const cursor = cursorAtDay(beats, 2);
    expect(beats[cursor - 1].day).toBe(2);
    expect(beats[cursor - 1].kind).toBe('phase');
    expect(cursorAtDay(beats, 99)).toBe(beats.length);
  });
});
