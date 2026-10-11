import { describe, expect, it } from 'vitest';
import { workbenchFrame } from '../workbench/frame';
import { DEFAULT_QUERY } from '../workbench/url';
import { beatsFor } from '../beats/beatsFor';
import { FIXTURE_EVENTS, PHASE3_GAME, PHASE3_NECRO_GAME } from '../workbench/fixture';
import type { DurableGameEvent } from '@/types/contracts';
import { foldEvents } from '@/game/foldEvents';
import liveGame from '@/game/__fixtures__/live-ab44887a-p3.json';
import { usableBodies } from '../roles';
import {
  actorsTonight,
  nightUnits,
  noAskLine,
  roomsToTry,
  spokeOf,
} from './NightLobbyScene';
import { actedTonight } from './replay-night';

// the nine-seat fixture (the workbench's default is the ten-seat game)
const NINE = { ...DEFAULT_QUERY, game: '9369a5c1' as const };
const hubs = (xray: boolean) =>
  workbenchFrame(xray ? 'rnight' : 'night', {
    ...NINE,
    viewer: { kind: xray ? 'xray' : 'spect' },
  });

describe('the night lobby on the fixture', () => {
  it('counts the night as the server paces it: one unit per living seat', () => {
    const f = hubs(false);
    const totals = f.beats.map((_, i) =>
      nightUnits(workbenchFrame('night', { ...NINE, beat: i }).view!),
    );
    // nine seats through night 2; night 3 has lost a wolf, the investigator and a villager;
    // night 4 a villager and the serial killer too
    expect(totals).toEqual([9, 9, 6, 4]);
  });

  it('lights the X-ray hub on every seat that acts tonight', () => {
    const f = hubs(true);
    const first = actorsTonight(f.view!, f.beat!.day);
    // healer 9, investigator 4, vigilante 7, serial killer 2, wolves 3 and 8
    expect([...first].sort()).toEqual(
      ['player_2', 'player_3', 'player_4', 'player_7', 'player_8', 'player_9'].sort(),
    );
  });

  it('takes a lit card at the hub to that actor’s first spoke; a wolf’s to the pack’s', () => {
    const f = hubs(true);
    const beats = beatsFor(FIXTURE_EVENTS, { xray: true });
    const first = (seat: string) =>
      roomsToTry(f.view!, seat)
        .map((actor) => beats.find(spokeOf(1, actor)))
        .find(Boolean);
    expect(first('player_4')?.spoke).toMatchObject({ actor: 'player_4', step: 0 });
    expect(first('player_3')?.spoke).toMatchObject({ actor: 'pack', step: 0 });
    expect(first('player_8')).toBe(first('player_3'));
    // the vigilante held fire on night 1: a decision too, so a room of its own (2026-09-30)
    expect(first('player_7')?.spoke).toMatchObject({
      actor: 'player_7',
      step: 0,
      steps: 1,
    });
  });
});

describe('the replay’s night stop: who acted', () => {
  it('counts each seat that acted, the pack as its wolves living at the hub', () => {
    const all = FIXTURE_EVENTS;
    const ahead = foldEvents(all);
    const hubAt = (day: number) =>
      foldEvents(
        all.slice(
          0,
          all.findIndex(
            (e) => e.type === 'phase_change' && e.phase === 'night' && e.day === day,
          ) + 1,
        ),
      );
    // night 1: the serial killer, the investigator, the healer, the vigilante (holding its
    // fire) and both wolves
    const n1 = actedTonight(hubAt(1), ahead, 1);
    expect([...n1.keys()].sort()).toEqual(
      ['player_2', 'player_3', 'player_4', 'player_7', 'player_8', 'player_9'].sort(),
    );
    expect([n1.get('player_3'), n1.get('player_8'), n1.get('player_4')]).toEqual([
      ['pack'],
      ['pack'],
      ['player_4'],
    ]);
  });
});

describe('the night lobby on the ten-seat games', () => {
  const hub = (events: readonly DurableGameEvent[], day: number) =>
    foldEvents(
      events.slice(
        0,
        events.findIndex(
          (e) => e.type === 'phase_change' && e.phase === 'night' && e.day === day,
        ) + 1,
      ),
    );

  it('counts every living seat, acting tonight or not, a concealed body lowering it too', () => {
    // night 1: all ten; night 2: the healer, the chanteuse, the investigator, the sigilist gone;
    // night 3: the concealed trailseer and the lynched serial killer gone as well
    expect([1, 2, 3].map((d) => nightUnits(hub(PHASE3_GAME.events, d)))).toEqual([
      10, 6, 4,
    ]);
  });

  it('takes the live frame’s total when one has landed', () => {
    expect(nightUnits(hub(PHASE3_GAME.events, 2), { total: 7 })).toBe(7);
  });

  it('lights every pack role, and no necromancer on night 1', () => {
    const n1 = actorsTonight(hub(PHASE3_NECRO_GAME.events, 1), 1);
    expect(n1.has('player_6')).toBe(true); // illusionist
    expect(n1.has('player_10')).toBe(true); // chanteuse
    expect(n1.has('player_7')).toBe(true); // speculator, not yet picked
    expect(n1.has('player_9')).toBe(false); // necromancer: no body on night 1
    expect(n1.size).toBe(9);
    // night 3: the necromancer acts; the speculator picked on night 2 and has nothing to do
    const n3 = actorsTonight(hub(PHASE3_NECRO_GAME.events, 3), 3);
    expect(n3.has('player_9')).toBe(true);
    expect(n3.has('player_7')).toBe(false);
  });

  it('takes a wolf’s card to its own skill’s spoke, then the pack’s; one without a skill tonight to the pack’s', () => {
    const events = PHASE3_GAME.events;
    const beats = beatsFor(events, { xray: true });
    const acted = actedTonight(hub(events, 1), foldEvents(events), 1);
    // night 1: the chanteuse (seat 5) carried the kill and blocked seat 1; the illusionist
    // (seat 6) did not conceal
    expect(acted.get('player_5')).toEqual(['pack', 'player_5']);
    expect(acted.get('player_6')).toEqual(['pack']);
    const view = hub(events, 1);
    const into = (seat: string, visited: string[] = []) =>
      roomsToTry(view, seat, acted.get(seat), visited)
        .map((actor) => beats.find(spokeOf(1, actor)))
        .find(Boolean)?.spoke;
    // the block's own room first, then the pack's kill once the block is seen
    expect(into('player_5')).toMatchObject({ actor: 'player_5', step: 0 });
    expect(into('player_5', ['player_5'])).toMatchObject({ actor: 'pack', step: 0 });
    // both seen: the same seat plays its own room again
    expect(into('player_5', ['player_5', 'pack'])).toMatchObject({ actor: 'player_5' });
    expect(into('player_6')).toMatchObject({ actor: 'pack', step: 0 });
    expect(into('player_9')).toMatchObject({ actor: 'player_9' }); // sentinel
    // without the log ahead (no stop), a wolf tries its own spoke, then the pack's
    expect(roomsToTry(view, 'player_6')).toEqual(['player_6', 'pack']);
    expect(roomsToTry(view, 'player_9')).toEqual(['player_9']);
  });

  it('keeps the pack’s kill reachable when its one wolf has a skill of its own that night', () => {
    const events = PHASE3_GAME.events;
    const beats = beatsFor(events, { xray: true });
    // night 2: the illusionist (seat 6), the pack's last wolf, carried the kill and concealed
    const acted = actedTonight(hub(events, 2), foldEvents(events), 2);
    expect(acted.get('player_6')).toEqual(['pack', 'player_6']);
    const view = hub(events, 2);
    const order = (visited: string[]) =>
      roomsToTry(view, 'player_6', acted.get('player_6'), visited);
    expect(order([])).toEqual(['player_6', 'pack']);
    expect(order(['player_6'])).toEqual(['pack', 'player_6']);
    for (const actor of ['player_6', 'pack'])
      expect(beats.some(spokeOf(2, actor))).toBe(true);
  });
});

describe('why the seat is asked nothing tonight', () => {
  // live game ab44887a (2026-10-11), seat 3 the necromancer, as the server streamed it
  const seatEvents = liveGame.events as unknown as DurableGameEvent[];
  const atNightfall = (day: number) => {
    const fall = seatEvents.find(
      (e) => e.type === 'phase_change' && e.phase === 'night' && e.day === day,
    )!;
    return foldEvents(
      seatEvents.filter((e) => e.seq <= fall.seq),
      { mySeat: 'player_3' },
    );
  };

  it('the necromancer: its power wakes on night 2, and needs a body it can use', () => {
    const n1 = atNightfall(1);
    expect(noAskLine(n1.me, n1.dead, 1)).toBe('Your power wakes on night 2.');
    // night 1 killed the speculator (seat 2), whose body gives nothing
    const n2 = atNightfall(2);
    expect(n2.dead.map((d) => [d.player, d.role])).toEqual([['player_2', 'speculator']]);
    expect(noAskLine(n2.me, n2.dead, 2)).toBe('No body you can use tonight.');
    // a revealed healer's body is one: the ask may still come, so the card's line stays
    const healer = [
      ...n2.dead,
      { player: 'player_6', role: 'healer', day: 2, seq: 1, causes: [] },
    ];
    expect(noAskLine(n2.me, healer, 2)).toBeNull();
  });

  it('a body counts only revealed, and only with an ability to give', () => {
    const body = (player: string, role: string | null) => ({ player, role });
    expect(
      usableBodies([
        body('player_1', 'villager'),
        body('player_2', 'wolf'),
        body('player_3', 'serial_killer'),
        body('player_4', 'speculator'),
        body('player_5', null), // concealed
        body('player_6', 'chanteuse'),
        body('player_7', 'trailseer'),
      ]),
    ).toEqual(['player_6', 'player_7']);
  });

  it('a spent ability, in the card note’s words; an ask that has come wins', () => {
    const me = (role: string, uses: number | null, bullets: number | null = null) => ({
      role: { role, pack: null, bullets, uses },
      alive: true,
      pending: null,
    });
    expect(noAskLine(me('investigator', 0), [], 3)).toBe('No checks left.');
    expect(noAskLine(me('sentinel', 0), [], 3)).toBe('No watches left.');
    expect(noAskLine(me('vigilante', 0), [], 3)).toBe('No caps left.');
    expect(noAskLine(me('vigilante', null, 0), [], 3)).toBe('No caps left.'); // nine-seat
    expect(noAskLine(me('sigilist', 0), [], 3)).toBe('No sigils left.');
    expect(noAskLine(me('speculator', 0), [], 3)).toBe('You have made your pick.');
    // a use left, a role whose turn comes spent or not, a dead seat: nothing to say
    expect(noAskLine(me('investigator', 1), [], 3)).toBeNull();
    expect(noAskLine(me('fortune_teller', 0), [], 3)).toBeNull();
    expect(noAskLine(me('healer', null), [], 3)).toBeNull();
    expect(noAskLine({ ...me('sigilist', 0), alive: false }, [], 3)).toBeNull();
    const asked = {
      ...me('necromancer', null),
      pending: {
        seq: 9,
        day: 1,
        actionKind: 'necromancer_target' as const,
        candidates: [],
        deadline: null,
        round: null,
        bodies: [],
      },
    };
    expect(noAskLine(asked, [], 1)).toBeNull();
  });
});
