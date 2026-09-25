import { describe, expect, it } from 'vitest';
import { FIXTURE_EVENTS } from './fixture';
import { workbenchFrame } from './frame';
import { SYNTHETIC } from './registry';
import { synthesise, synthesiseAll } from './synthetic';
import { DEFAULT_QUERY } from './url';

const room = SYNTHETIC.room!;
const pack = SYNTHETIC.pack!;
const byLabel = (list: typeof room, label: string) => list.find((s) => s.label === label)!;

describe('synthetic night situations', () => {
  it('offers every living seat but me, and never a wolf to the pack', () => {
    for (const s of [...room, ...pack]) {
      const f = synthesise(s, FIXTURE_EVENTS);
      const c = f.view.me.pending?.candidates;
      if (!s.actionKind) {
        expect(f.view.me.pending).toBeNull();
        continue;
      }
      expect(c).not.toContain(s.me);
      for (const seat of c!) expect(f.view.alive).toContain(seat);
      if (s.actionKind.startsWith('wolf_'))
        for (const w of f.view.packRoster) expect(c).not.toContain(w);
    }
  });

  it('builds the fixture’s nights as they were', () => {
    const healer = synthesise(room[0], FIXTURE_EVENTS);
    expect(healer.view.me.pending?.candidates).toEqual([
      'player_1',
      'player_2',
      'player_3',
      'player_4',
      'player_5',
      'player_6',
      'player_7',
      'player_8',
    ]);
    expect(healer.view.me.role?.role).toBe('healer');
    expect(healer.beat).toMatchObject({
      id: 'room.opens',
      scene: 'room',
      day: 2,
      seat: 'player_9',
    });

    const vig = synthesise(byLabel(room, 'vigilante, night 4'), FIXTURE_EVENTS);
    expect(vig.view.me.pending?.candidates).toEqual(['player_1', 'player_8', 'player_9']);

    const wolf = synthesise(pack[0], FIXTURE_EVENTS);
    expect(wolf.beat.id).toBe('pack.your-line');
    expect(wolf.view.me.pending?.candidates).toEqual([
      'player_1',
      'player_2',
      'player_4',
      'player_5',
      'player_6',
      'player_7',
      'player_9',
    ]);
    expect(wolf.turn.draft).toMatch(/^Hey seat 8/);

    const vote = synthesise(
      byLabel(pack, 'wolf, the vote, packmate voted'),
      FIXTURE_EVENTS,
    );
    expect(vote.beat.id).toBe('pack.vote');
    expect(vote.view.days[2].night?.wolfVotes).toEqual([
      { seq: 152, wolf: 'player_3', votee: 'player_4' },
    ]);

    const lone = synthesise(byLabel(pack, 'lone wolf, night 3'), FIXTURE_EVENTS);
    expect(lone.view.packRoster).toEqual(['player_8']);
    expect(lone.view.me.pending?.candidates).toEqual([
      'player_1',
      'player_2',
      'player_5',
      'player_7',
      'player_9',
    ]);

    const line = synthesise(
      byLabel(pack, 'wolf, the packmate’s line arrives'),
      FIXTURE_EVENTS,
    );
    expect(line.beat).toMatchObject({ id: 'pack.line', subject: 'player_8', seq: 46 });
    const decided = synthesise(byLabel(pack, 'wolf, the kill decided'), FIXTURE_EVENTS);
    expect(decided.beat).toMatchObject({ id: 'pack.decided', subject: 'player_4' });
  });

  it('carries the clock: 1:14 of two minutes by default, none for a solo game', () => {
    const [first] = synthesiseAll(room, FIXTURE_EVENTS);
    expect(first.turn.clock).toEqual({ remainingMs: 74_000, totalMs: 120_000 });
    const solo = synthesise(
      byLabel(room, 'healer, night 3, no deadline (solo game)'),
      FIXTURE_EVENTS,
    );
    expect(solo.turn.clock).toBeNull();
  });

  it('steps the workbench through the situations with ?beat=N', () => {
    const f = workbenchFrame('room', { ...DEFAULT_QUERY, beat: 1 });
    expect(f.beats).toHaveLength(room.length);
    expect(f.situation?.label).toBe('healer, night 2, seat 1 chosen');
    expect(f.me).toBe('player_9');
    expect(f.turn?.chosen).toBe('player_1');
    const clamped = workbenchFrame('pack', { ...DEFAULT_QUERY, beat: 99 });
    expect(clamped.index).toBe(pack.length - 1);
    expect(clamped.beat?.id).toBe('pack.decided');
  });
});

describe('the seated human’s ballot', () => {
  const vote = SYNTHETIC.vote!;

  it('opens at the vote with every living seat but mine, and abstain', () => {
    const f = synthesise(vote[0], FIXTURE_EVENTS);
    expect(f.beat.id).toBe('vote.your-ballot');
    expect(f.beat.seq).toBe(220);
    expect(f.view.me.pending?.candidates).toEqual([
      'player_1',
      'player_2',
      'player_5',
      'player_6',
      'player_8',
      'player_9',
      'abstain',
    ]);
  });

  it('comes after the fixture’s own vote beats in the stepper', () => {
    const fixtureOnly = workbenchFrame('vote', DEFAULT_QUERY).beats.filter(
      (b) => !b.liveOnly,
    ).length;
    const f = workbenchFrame('vote', { ...DEFAULT_QUERY, beat: fixtureOnly + 1 });
    expect(f.beat?.id).toBe('vote.your-ballot');
    expect(f.index).toBe(fixtureOnly + 1);
    expect(f.beats).toHaveLength(fixtureOnly + vote.length);
    expect(f.turn?.chosen).toBe('player_6');
    expect(workbenchFrame('vote', DEFAULT_QUERY).beat?.id).toBe('vote.opens');
  });
});
