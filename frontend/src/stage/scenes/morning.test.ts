import { describe, expect, it } from 'vitest';
import { foldEvents } from '@/game/foldEvents';
import type { NightView } from '@/game/types';
import type { DurableGameEvent } from '@/types/contracts';
import { pickLine } from '../instruments/MorningRoll';
import {
  FIXTURE_EVENTS,
  PHASE2_GAME,
  PHASE3_GAME,
  PHASE3_NECRO_GAME,
} from '../workbench/fixture';
import { morningPrivates, privateAt, reportOf } from './MorningScene';

const p3 = PHASE3_GAME.events;
const necro = PHASE3_NECRO_GAME.events;
const nightOf = (events: readonly DurableGameEvent[], day: number) =>
  foldEvents(events).days[day].night!;

describe('the morning’s report (reportOf)', () => {
  it('tells every save, a concealed body without its role, and the pick last', () => {
    // night 2 of the phase-3 game: one concealed body; two saves added for the case
    const night: NightView = {
      ...nightOf(p3, 2),
      save: { player: 'player_4', attacker_types: ['wolves'] },
      saves: [
        { player: 'player_4', attacker_types: ['wolves'] },
        { player: 'player_8', attacker_types: ['serial_killer'] },
      ],
      pick: 'town',
    };
    expect(reportOf(night)).toEqual([
      {
        kind: 'death',
        player: 'player_3',
        role: null,
        types: ['wolves', 'serial_killer'],
      },
      { kind: 'save', player: 'player_4', types: ['wolves'] },
      { kind: 'save', player: 'player_8', types: ['serial_killer'] },
      { kind: 'pick', pick: 'town' },
    ]);
  });

  it('reads the necromancer game’s save and the speculator’s pick in the game master’s words', () => {
    const night = nightOf(necro, 2);
    expect(reportOf(night).map((r) => r.kind)).toEqual(['death', 'save', 'pick']);
    const gm = necro.find((e) => e.type === 'gm_message' && e.seq === 310);
    expect(gm && 'text' in gm ? gm.text : '').toContain(pickLine('wolves'));
  });

  it('keeps a nine-seat night as it was: deaths, then the one save', () => {
    const view = foldEvents(PHASE2_GAME.events);
    for (const day of Object.values(view.days)) {
      const night = day.night;
      if (!night) continue;
      const report = reportOf(night);
      expect(report.filter((r) => r.kind === 'save')).toHaveLength(night.save ? 1 : 0);
      expect(report.some((r) => r.kind === 'pick')).toBe(false);
    }
  });
});

describe('what only one seat learns at the morning (morningPrivates)', () => {
  it('a seat’s night record, in the engine’s words, with the seat it names', () => {
    const view = foldEvents(p3, { mySeat: 'player_9' });
    expect(morningPrivates(view, view.days[1].night, 1, 'player_9', false)).toEqual([
      {
        kind: 'record',
        seat: 'player_9',
        target: 'player_5',
        outcome: 'Tonight player_5 was visited by player_3 and player_4.',
        pack: false,
      },
    ]);
  });

  it('a count of uses left is not news, and a record naming no seat brings no chip down', () => {
    // the vigilante, roleblocked on night 1: a record and a uses count
    const view = foldEvents(p3, { mySeat: 'player_1' });
    const mine = morningPrivates(view, view.days[1].night, 1, 'player_1', false);
    expect(mine).toHaveLength(1);
    expect(mine[0]).toMatchObject({ kind: 'record', target: null });
  });

  it('the pack’s kill is one note, however many wolves hold it', () => {
    // night 1 of the necromancer game: both wolves (6 and 10) are sent the pack's kill
    const xray = foldEvents(necro);
    const all = morningPrivates(xray, xray.days[1].night, 1, null, true);
    expect(all.filter((p) => p.kind === 'record' && p.pack)).toHaveLength(1);
    // the chanteuse has the pack's kill and its own block
    const seat = foldEvents(necro, { mySeat: 'player_10' });
    expect(
      morningPrivates(seat, seat.days[1].night, 1, 'player_10', false).map((p) =>
        p.kind === 'record' ? [p.pack, p.outcome] : p.kind,
      ),
    ).toEqual([
      [true, 'player_4 died. They were a sigilist.'],
      [false, 'player_5 was roleblocked tonight.'],
    ]);
  });

  it('a game master’s pack note on a night with the pack’s record does not double it', () => {
    const at = necro.findIndex((e) => e.seq === 100);
    const note = {
      type: 'wolf_message',
      seq: 100.5,
      day: 1,
      round: 0,
      wolf: 'game_master',
      message: 'Your kill failed.',
    } as unknown as DurableGameEvent;
    const events = [...necro.slice(0, at + 1), note, ...necro.slice(at + 1)];
    const seat = foldEvents(events, { mySeat: 'player_6' });
    const mine = morningPrivates(seat, seat.days[1].night, 1, 'player_6', false);
    expect(
      mine.filter((p) => p.kind === 'pack' || (p.kind === 'record' && p.pack)),
    ).toHaveLength(1);
  });
});

describe('the nine-seat private results keep their paths', () => {
  const view = foldEvents(FIXTURE_EVENTS);

  it('the investigator’s reading and the pack’s failed kill', () => {
    expect(privateAt(view, view.days[1].night, { seq: 59 })).toEqual({
      kind: 'investigation',
      seat: 'player_4',
      target: 'player_1',
      role: 'villager',
    });
    expect(privateAt(view, view.days[3].night, { seq: 271 })).toEqual({
      kind: 'pack',
      target: 'player_2',
    });
    expect(morningPrivates(view, view.days[3].night, 3, null, true)).toContainEqual({
      kind: 'pack',
      target: 'player_2',
    });
  });
});
