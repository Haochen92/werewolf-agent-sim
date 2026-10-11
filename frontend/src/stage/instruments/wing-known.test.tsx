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
  it('a wolf knows its pack mates as the pack, not by role, and not itself', () => {
    const k = knownRoles(
      'player_3',
      me({
        role: { role: 'wolf', pack: ['player_3', 'player_8'], bullets: null, uses: null },
      }),
    );
    expect([...k]).toEqual([['player_8', { how: 'pack' }]]);
  });

  it('an investigator knows the seats its own readings named', () => {
    const k = knownRoles(
      'player_4',
      me({
        role: { role: 'investigator', pack: null, bullets: null, uses: null },
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
      knownRoles(
        'player_5',
        me({ role: { role: 'villager', pack: null, bullets: null, uses: null } }),
      ).size,
    ).toBe(0);
    // a spectator has no seat: whatever the view holds, nothing is its own
    expect(
      knownRoles(
        null,
        me({
          role: { role: 'wolf', pack: ['player_3', 'player_8'], bullets: null, uses: null },
        }),
      ).size,
    ).toBe(0);
  });
});

describe('the wing’s known band', () => {
  const html = (tiles: Parameters<typeof Wing>[0]['tiles']) =>
    renderToStaticMarkup(<Wing width={192} tiles={tiles} />);

  it('bands a pack mate (the pack’s mark) and a reading (the role’s felt sigil) in brass', () => {
    const out = html([
      { seat: 8, known: { how: 'pack' } },
      { seat: 1, known: { role: 'villager', how: 'seen' } },
    ]);
    expect(out).toMatch(/data-known="pack"[^>]*>.*data-faction="wolves".*Your pack/);
    expect(out).not.toContain('data-sigil="wolf"');
    expect(out).toMatch(
      /data-known="seen"[^>]*>.*data-sigil="villager".*Seen · .*Villager/,
    );
    expect(out).toContain('data-variant="felt"');
  });

  it('gives the band to a death, "You" and the X-ray’s truth first', () => {
    const out = html([
      { seat: 8, dead: { role: 'wolf' }, known: { how: 'pack' } },
      { seat: 3, you: true, known: { how: 'pack' } },
      { seat: 1, truth: 'villager', known: { role: 'villager', how: 'seen' } },
    ]);
    expect(out).not.toContain('data-known');
  });
});

describe('a concealed body on the wing', () => {
  const html = (tiles: Parameters<typeof Wing>[0]['tiles']) =>
    renderToStaticMarkup(<Wing width={192} tiles={tiles} />);

  it('turns to "Role hidden", no role and no side', () => {
    const out = html([{ seat: 3, dead: { role: null } }]);
    expect(out).toMatch(/data-hidden="true"[^>]*>Role hidden</);
    expect(out).not.toContain('data-sigil');
    expect(out).not.toMatch(/c-(villagers|wolves|serial_killer|neutral_benign)/);
  });

  it('shows the role to a viewer who holds the truth (the X-ray, the game over)', () => {
    const out = html([{ seat: 3, dead: { role: null }, truth: 'trailseer' }]);
    expect(out).toContain('Trailseer');
    expect(out).not.toContain('Role hidden');
  });
});
