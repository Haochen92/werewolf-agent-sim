import { describe, expect, it } from 'vitest';
import { CHARACTERS, REACH, type Character } from '@/assets/manifest';
import { foldEvents } from '@/game/foldEvents';
import type { GameView } from '@/game/types';
import { geometry, standBox } from '../units';
import { FIXTURE_EVENTS, PHASE3_GAME, PHASE3_NECRO_GAME } from '../workbench/fixture';
import {
  WINNERS_HOUR,
  WINNER_LINE,
  endedAt,
  fateOf,
  knownRole,
  knownSide,
  lastStanding,
  neutralLine,
  roleWon,
  standSet,
  winnersOf,
} from './game-over';

const over = FIXTURE_EVENTS.findIndex((e) => e.type === 'game_over') + 1;
const view = foldEvents(FIXTURE_EVENTS.slice(0, over));

describe('the ending, from the fixture (the wolves win at the morning of day 4)', () => {
  it('stands the winning side’s survivors only: seat 8, not the vigilante beside it', () => {
    expect(view.winner).toBe('wolves');
    expect(view.alive).toEqual(['player_7', 'player_8']);
    expect(winnersOf(view)).toEqual(['player_8']);
  });

  it('stands every survivor of the side, and none of the fallen', () => {
    const v: GameView = { ...view, winner: 'villagers' };
    expect(winnersOf(v)).toEqual(['player_7']);
    const all: GameView = {
      ...view,
      winner: 'villagers',
      alive: ['player_1', 'player_7', 'player_8', 'player_9'],
    };
    expect(winnersOf(all)).toEqual(['player_1', 'player_7', 'player_9']);
  });

  it('knows where it stopped', () => {
    expect(endedAt(view)).toBe('morning');
    const lynch = FIXTURE_EVENTS.findIndex((e) => e.type === 'lynch_result' && e.day === 4);
    expect(endedAt(foldEvents(FIXTURE_EVENTS.slice(0, lynch + 1)))).toBe('lynch');
  });

  it('says how each seat went', () => {
    expect(fateOf(view, 'player_8')).toBe('survived');
    expect(fateOf(view, 'player_2')).toBe('day 4, voted out');
    expect(fateOf(view, 'player_3')).toBe('night 2, the serial killer');
    expect(fateOf(view, 'player_9')).toBe('night 4, the vigilante');
  });

  it('names the last standing', () => {
    expect(lastStanding(['player_8'])).toBe('Seat 8 is the last of them standing');
    expect(lastStanding(['player_3', 'player_8'])).toBe(
      'Seats 3 and 8 are the last of them standing',
    );
    expect(lastStanding(['player_1', 'player_7', 'player_9'])).toBe(
      'Seats 1, 7 and 9 are the last of them standing',
    );
  });
});

describe('the stand for the winners', () => {
  const g = geometry('live'),
    body = g.ph * 0.98;
  // the gap between neighbours' widest reaches, in units (0 = they just meet)
  const gaps = (cast: Character[], set: ReturnType<typeof standSet>) =>
    cast.slice(1).map((c, i) => {
      const between = (set.offsets[i + 1] - set.offsets[i]) * g.pwid;
      return between - (REACH[cast[i]].right + REACH[c].left) * body * set.scale;
    });

  it('stands one alone at full size on the plain box', () => {
    expect(standSet(['owl'], g)).toEqual({ scale: 1, offsets: [0], widen: 1 });
    expect(standSet(['owl'], g, true).scale).toBe(0.84);
  });

  it('spaces two and three so their widest reaches just meet, wide or narrow', () => {
    for (const cast of [
      ['polarBear', 'dragon'],
      ['onion', 'threeEyes'],
      ['cat', 'badger', 'shade'],
      ['hare', 'onion', 'owl'],
    ] as Character[][]) {
      const set = standSet(cast, g);
      for (const gap of gaps(cast, set)) expect(gap).toBeCloseTo(0, 6);
      // centred on the stand, and held inside its widened box
      const reach = (REACH[cast[0]].left + REACH[cast.at(-1)!].right) * body * set.scale;
      const outer = (set.offsets.at(-1)! - set.offsets[0]) * g.pwid + reach;
      expect(outer).toBeLessThanOrEqual(standBox(g).w * set.widen + 1e-6);
    }
    const wide = standSet(['badger', 'cat'], g),
      narrow = standSet(['onion', 'threeEyes'], g);
    expect(wide.offsets[1] - wide.offsets[0]).toBeGreaterThan(
      narrow.offsets[1] - narrow.offsets[0],
    );
  });

  it('keeps an instrument its own place on the rail right of the figures', () => {
    const cast: Character[] = ['owl', 'cyclops'],
      set = standSet(cast, g, false, 110);
    const right = set.offsets[1] * g.pwid + REACH.cyclops.right * body * set.scale;
    expect(set.beside! * g.pwid - 55).toBeCloseTo(right, 6);
    expect(standSet(['owl'], g, false, 110).beside).toBeUndefined();
  });

  it('shrinks them together rather than let the stand outgrow the room beside the slot', () => {
    const side = geometry('live', true);
    for (const n of [2, 3]) {
      for (const cast of [CHARACTERS.slice(0, n), CHARACTERS.slice(-n)] as Character[][]) {
        const set = standSet(cast, side, true);
        expect(standBox(side).w * set.widen).toBeLessThanOrEqual(side.room - 80 + 1e-6);
        expect(set.scale).toBeLessThanOrEqual(n === 2 ? 0.78 * 0.84 : 0.6 * 0.84);
      }
    }
  });
});

describe('the ending per winner (ten-seat pass §1)', () => {
  it('rises on each winner’s hour, with its own line', () => {
    expect(WINNERS_HOUR).toEqual({
      villagers: 'day',
      wolves: 'night',
      serial_killer: 'dusk',
      necromancer: 'dusk',
      draw: 'dawn',
    });
    expect(WINNER_LINE).toEqual({
      villagers: 'The town has won',
      wolves: 'The wolves have won',
      serial_killer: 'The serial killer has won',
      necromancer: 'The necromancer has won',
      draw: 'No side has won',
    });
  });

  const p3 = foldEvents(PHASE3_GAME.events);
  const necro = foldEvents(PHASE3_NECRO_GAME.events);

  it('stands the town’s survivors, never the neutral beside them', () => {
    expect(p3.winner).toBe('villagers');
    // the fortune teller (seat 8) is alive and lost nothing, but it is not the town's
    expect(p3.alive).toContain('player_8');
    expect(winnersOf(p3)).not.toContain('player_8');
    expect(winnersOf(p3).every((s) => p3.xray.roles[s] !== 'fortune_teller')).toBe(true);
  });

  it('stands the necromancer alone for a necromancer win, and nobody for a draw', () => {
    const won = {
      ...necro,
      winner: 'necromancer' as const,
      alive: ['player_2', 'player_9'],
    };
    expect(winnersOf(won)).toEqual(['player_9']);
    // the serial killer's win is not the necromancer's
    expect(winnersOf({ ...won, winner: 'serial_killer' as const })).toEqual([]);
    expect(winnersOf({ ...necro, winner: null })).toEqual([]);
  });

  it('knows a pack mate by its side, not a role', () => {
    // seat 6 (the illusionist) on day 1, before the X-ray's roles: its mate is seat 10
    const wolf = foldEvents(
      PHASE3_NECRO_GAME.events.filter((e) => e.seq < 90 && e.type !== 'roles_assigned'),
      { mySeat: 'player_6' },
    );
    expect(knownRole(wolf, 'player_10')).toBeNull();
    expect(knownSide(wolf, 'player_10')).toBe('wolves');
    const packWin = {
      ...wolf,
      over: true,
      winner: 'wolves' as const,
      alive: ['player_6', 'player_10'],
    };
    expect(winnersOf(packWin)).toEqual(['player_6', 'player_10']);
  });

  it('says whether a role won, a neutral on its own result', () => {
    expect(roleWon('illusionist', 'wolves')).toBe(true);
    expect(roleWon('healer', 'wolves')).toBe(false);
    expect(roleWon('necromancer', 'necromancer')).toBe(true);
    expect(roleWon('necromancer', 'serial_killer')).toBe(false);
    expect(roleWon('healer', 'draw')).toBe(false);
    expect(roleWon('fortune_teller', 'villagers', 'won (2 points)')).toBe(true);
    expect(roleWon('speculator', 'villagers', 'lost')).toBe(false);
  });

  it('reads the neutral’s result as the line under the winner’s', () => {
    expect(neutralLine(p3)).toBe('The fortune teller won, with 2 points');
    expect(neutralLine(necro)).toBe('The speculator lost');
    expect(neutralLine({ ...necro, neutralResult: 'won' })).toBe(
      'The speculator’s pick won',
    );
    expect(neutralLine({ ...p3, neutralResult: 'lost (1 points)' })).toBe(
      'The fortune teller lost, with 1 point',
    );
    // a nine-seat game has no neutral
    expect(neutralLine(view)).toBeNull();
  });

  it('names the ten-seat causes in the case file’s fates', () => {
    expect(fateOf(p3, 'player_5')).toBe('night 1, a sigil');
  });
});
