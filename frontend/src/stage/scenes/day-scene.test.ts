/**
 * The day's turn stays mounted while it is the same turn: the puppet rises once per turn. A
 * live game cuts the beat list afresh for every event, so the beat on the stage comes back as
 * a new copy; that copy, the speech's next page, and the line after its own thinking (or after
 * the seat's own turn at the dock) continue the turn instead of replaying its arrival.
 */
import { describe, expect, it } from 'vitest';
import fixture from '@/stage/fixtures/replay-9369a5c1.json';
import { beatsFor } from '@/stage/beats/beatsFor';
import type { SceneBeat } from '@/stage/beats/types';
import type { DurableGameEvent } from '@/types/contracts';
import { continues } from './DayScene';

const ALL = fixture.events as unknown as DurableGameEvent[];
const cut = (to: number) =>
  beatsFor(
    ALL.filter((e) => e.seq <= to),
    { xray: false, live: true },
  );
const find = (beats: SceneBeat[], id: string, seq: number, page?: number) =>
  beats.find((b) => b.id === id && b.seq === seq && b.page?.index === page)!;

describe('the day’s turn', () => {
  it('a new cut of the list is the same turn, not a new one', () => {
    // seat 2's first page on the stage; seat 1's turn arrives and the list is cut again
    const was = find(cut(163), 'day.speech', 163, 0);
    const now = find(cut(166), 'day.speech', 163, 0);
    expect(now).not.toBe(was);
    expect(continues(was, now)).toBe(true);
  });

  it('continues across pages, and from the thinking or the dock to the line', () => {
    const beats = cut(169);
    expect(
      continues(find(beats, 'day.speech', 163, 0), find(beats, 'day.speech', 163, 1)),
    ).toBe(true);
    expect(
      continues(find(beats, 'day.turn-thinking', 160), find(beats, 'day.speech', 163, 0)),
    ).toBe(true);
    const dock: SceneBeat = {
      ...find(beats, 'day.turn-thinking', 160),
      id: 'day.your-turn',
      subject: undefined,
      seat: 'player_2',
    };
    expect(continues(dock, find(beats, 'day.speech', 163, 0))).toBe(true);
  });

  it('a new turn is a new turn', () => {
    const beats = cut(169);
    expect(
      continues(find(beats, 'day.speech', 163, 1), find(beats, 'day.turn-thinking', 166)),
    ).toBe(false);
    expect(
      continues(find(beats, 'day.turn-thinking', 160), find(beats, 'day.speech', 169, 0)),
    ).toBe(false);
  });
});
