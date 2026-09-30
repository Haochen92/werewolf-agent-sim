import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import type { MeView } from '@/game/types';
import { knownRoles } from '../roles';
import { Wing } from './Wing';

const me = (over: Partial<MeView> = {}): Pick<MeView, 'role' | 'privateResults'> => ({
  role: null,
  privateResults: [],
  ...over,
});

describe('what a seat already knows, from its own view', () => {
  it('a wolf knows its pack mates, not itself', () => {
    const k = knownRoles(
      'player_3',
      me({ role: { role: 'wolf', pack: ['player_3', 'player_8'], bullets: null } }),
    );
    expect([...k]).toEqual([['player_8', { role: 'wolf', how: 'pack' }]]);
  });

  it('an investigator knows the seats its own readings named', () => {
    const k = knownRoles(
      'player_4',
      me({
        role: { role: 'investigator', pack: null, bullets: null },
        privateResults: [
          {
            kind: 'investigation',
            player: 'player_4',
            seq: 59,
            day: 1,
            target: 'player_1',
            role: 'villager',
          },
          {
            kind: 'investigation',
            player: 'player_4',
            seq: 120,
            day: 2,
            target: 'player_8',
            role: 'wolf',
          },
        ],
      }),
    );
    expect(Object.fromEntries(k)).toEqual({
      player_1: { role: 'villager', how: 'seen' },
      player_8: { role: 'wolf', how: 'seen' },
    });
  });

  it('a villager and a spectator know nothing here', () => {
    expect(
      knownRoles('player_5', me({ role: { role: 'villager', pack: null, bullets: null } }))
        .size,
    ).toBe(0);
    // a spectator has no seat: whatever the view holds, nothing is its own
    expect(
      knownRoles(
        null,
        me({ role: { role: 'wolf', pack: ['player_3', 'player_8'], bullets: null } }),
      ).size,
    ).toBe(0);
  });
});

describe('the wing’s known band', () => {
  const html = (tiles: Parameters<typeof Wing>[0]['tiles']) =>
    renderToStaticMarkup(<Wing width={192} tiles={tiles} />);

  it('bands a pack mate and a reading in brass, with the role’s felt sigil', () => {
    const out = html([
      { seat: 8, known: { role: 'wolf', how: 'pack' } },
      { seat: 1, known: { role: 'villager', how: 'seen' } },
    ]);
    expect(out).toMatch(/data-known="pack"[^>]*>.*data-sigil="wolf".*Your pack/);
    expect(out).toMatch(
      /data-known="seen"[^>]*>.*data-sigil="villager".*Seen · .*Villager/,
    );
    expect(out).toContain('data-variant="felt"');
  });

  it('gives the band to a death, "You" and the X-ray’s truth first', () => {
    const out = html([
      { seat: 8, dead: { role: 'wolf' }, known: { role: 'wolf', how: 'pack' } },
      { seat: 3, you: true, known: { role: 'wolf', how: 'pack' } },
      { seat: 1, truth: 'villager', known: { role: 'villager', how: 'seen' } },
    ]);
    expect(out).not.toContain('data-known');
  });
});
