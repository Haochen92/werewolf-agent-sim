import { describe, expect, it } from 'vitest';
import type { DurableGameEvent } from '@/types/contracts';
import {
  nextLiveResolution,
  resolutionAnnouncement,
  resolutionLabel,
} from './resolutionBeat';

const events = [
  {
    seq: 10,
    day: 2,
    type: 'gm_message',
    channel_seq: 4,
    text: 'The village voted out player_4.',
  },
  {
    seq: 11,
    day: 2,
    type: 'lynch_result',
    outcome: 'lynched',
    player: 'player_4',
    role: 'wolf',
    vote_counts: { player_4: 5 },
    no_lynch_streak: 0,
  },
  {
    seq: 20,
    day: 2,
    type: 'gm_message',
    channel_seq: 5,
    text: 'Night of day 2: no one died.',
  },
  {
    seq: 21,
    day: 2,
    type: 'night_result',
    deaths: [],
    save: null,
  },
] as DurableGameEvent[];

describe('live resolution queue', () => {
  it('queues live resolutions in order and never replays catch-up', () => {
    expect(nextLiveResolution(events, new Set(), new Set())).toBeNull();

    const live = new Set([11, 21]);
    const first = nextLiveResolution(events, live, new Set());
    expect(first?.seq).toBe(11);
    expect(resolutionLabel(first!)).toBe('Day 2 verdict');
    expect(resolutionAnnouncement(first!, events)).toBe('The village voted out player_4.');

    const second = nextLiveResolution(events, live, new Set([11]));
    expect(second?.seq).toBe(21);
    expect(resolutionLabel(second!)).toBe('Dawn after Night 2');
    expect(resolutionAnnouncement(second!, events)).toBe('Night of day 2: no one died.');
  });
});
