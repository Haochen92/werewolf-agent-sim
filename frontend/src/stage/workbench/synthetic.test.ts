import { describe, expect, it } from 'vitest';
import { FIXTURE_EVENTS } from './fixture';
import { workbenchFrame } from './frame';
import { SYNTHETIC } from './registry';
import { STILL_AT, synthesise, synthesiseAll } from './synthetic';
import { isSeat } from '../scenes/ShelfRoomScene';
import { payloadFor } from '../containers/live-state';
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
      // the fortune teller's own seat is its self-bet; the server's words are not seats
      if (s.actionKind !== 'bet_target') expect(c).not.toContain(s.me);
      for (const seat of c!.filter(isSeat)) expect(f.view.alive).toContain(seat);
      if (s.actionKind.startsWith('wolf_') || s.actionKind === 'carrier_kill')
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
    expect(vig.view.me.pending?.candidates).toEqual([
      'player_1',
      'player_8',
      'player_9',
      'hold_fire',
    ]);

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
    expect(first.turn.clock).toEqual({
      deadline: '2026-09-25T10:01:14.000Z',
      totalMs: 120_000,
      at: STILL_AT,
    });
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

describe('the ten-seat kinds (ten-seat pass §2)', () => {
  const all = [...room, ...pack];
  const NIGHT_KINDS = [
    'wolf_discuss',
    'carrier_kill',
    'block_target',
    'conceal',
    'healer_target',
    'investigator_target',
    'sentinel_target',
    'trailseer_target',
    'vigilante_target',
    'sigil_target',
    'serial_killer_target',
    'necromancer_target',
    'speculator_pick',
    'bet_target',
  ] as const;

  it('has a situation for every night kind, each answerable with the server’s words', () => {
    for (const kind of NIGHT_KINDS) {
      const situations = all.filter((s) => s.actionKind === kind);
      expect(situations.length, kind).toBeGreaterThan(0);
      for (const s of situations) {
        const f = synthesise(s, FIXTURE_EVENTS);
        const pending = f.view.me.pending!;
        if (kind === 'wolf_discuss') {
          expect(payloadFor(pending, { act: null })).toEqual({ pass_turn: true });
          continue;
        }
        const target = s.chosen ?? pending.candidates.find(isSeat) ?? pending.candidates[0];
        const body =
          kind === 'necromancer_target' ? (s.body ?? pending.bodies[0]) : undefined;
        expect(
          payloadFor(pending, { act: target, body, roleNamed: s.roleNamed }),
          s.label,
        ).not.toBeNull();
      }
    }
  });

  it('draws them from the ten-seat games, with their own cast and the server’s lists', () => {
    const by = (label: string) => synthesise(byLabel(room, label), FIXTURE_EVENTS);
    const sentinel = by('ten seats: sentinel, night 1');
    expect(sentinel.cast).toHaveLength(10);
    expect(sentinel.view.me.role?.role).toBe('sentinel');
    expect(sentinel.view.me.pending?.candidates.at(-1)).toBe('no_watch');
    expect(sentinel.view.me.pending?.candidates).toHaveLength(10); // nine seats and the word

    const block = by('ten seats: chanteuse’s block, night 1, seat 1 chosen');
    expect(block.beat.id).toBe('room.opens');
    expect(block.view.me.pending?.candidates).not.toContain('player_6'); // the packmate

    expect(
      by('ten seats: illusionist’s conceal, night 2').view.me.pending?.candidates,
    ).toEqual(['conceal', 'no_conceal']);
    expect(
      by('ten seats: speculator, night 1, the wolves chosen').view.me.pending?.candidates,
    ).toEqual(['town', 'wolves', 'lone_killer', 'self', 'not_yet']);

    const bet = by('ten seats: fortune teller, night 1, a self-bet chosen');
    expect(bet.view.me.pending?.candidates).toContain('player_8');
    expect(bet.turn.chosen).toBe('player_8');

    const necro = by('ten seats: necromancer, through seat 4 on seat 1');
    expect(necro.view.me.pending?.bodies).toEqual(['player_4', 'player_8']);
    expect(necro.view.me.pending?.candidates.at(-1)).toBe('stay_put');
    expect(necro.turn).toMatchObject({ chosen: 'player_1', body: 'player_4' });

    const carrier = synthesise(
      byLabel(pack, 'ten seats: the carrier names the kill, seat 7 chosen'),
      FIXTURE_EVENTS,
    );
    expect(carrier.beat.id).toBe('pack.vote');
    expect(carrier.view.me.pending?.candidates).not.toContain('player_6');
  });

  it('hands a ten-seat situation’s cast to the workbench frame', () => {
    const i = room.findIndex((s) => s.label === 'ten seats: sentinel, night 1');
    const f = workbenchFrame('room', { ...DEFAULT_QUERY, beat: i });
    expect(f.presentation.cast).toHaveLength(10);
    expect(f.me).toBe('player_9');
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
