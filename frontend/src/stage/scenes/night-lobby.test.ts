import { describe, expect, it } from 'vitest';
import { workbenchFrame } from '../workbench/frame';
import { DEFAULT_QUERY } from '../workbench/url';
import { beatsFor } from '../beats/beatsFor';
import { FIXTURE_EVENTS } from '../workbench/fixture';
import { foldEvents } from '@/game/foldEvents';
import { actorsTonight, nightUnits, spokeOf } from './NightLobbyScene';
import { actedTonight } from './replay-night';

const hubs = (xray: boolean) =>
  workbenchFrame(xray ? 'rnight' : 'night', {
    ...DEFAULT_QUERY,
    viewer: { kind: xray ? 'xray' : 'spect' },
  });

describe('the night lobby on the fixture', () => {
  it('counts the night as the server paces it: special roles alive, the pack as one', () => {
    const f = hubs(false);
    const totals = f.beats.map((_, i) =>
      nightUnits(workbenchFrame('night', { ...DEFAULT_QUERY, beat: i }).view!),
    );
    // night 3 has lost the investigator (seat 4, night 2); night 4 the serial killer (lynched)
    expect(totals).toEqual([5, 5, 4, 3]);
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
    const first = (seat: string) => beats.find(spokeOf(f.view!, 1, seat));
    expect(first('player_4')?.spoke).toMatchObject({ actor: 'player_4', step: 0 });
    expect(first('player_3')?.spoke).toMatchObject({ actor: 'pack', step: 0 });
    expect(first('player_8')).toBe(first('player_3'));
    // the vigilante held fire on night 1: a decision too, so a room of its own (2026-09-30)
    expect(first('player_7')?.spoke).toMatchObject({ actor: 'player_7', step: 0, steps: 1 });
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
      'pack',
      'pack',
      'player_4',
    ]);
  });
});
