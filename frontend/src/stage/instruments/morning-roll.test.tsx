import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { MorningRoll, causeOf, type RollRow } from './MorningRoll';

const html = (rows: RollRow[], me: string | null = null) =>
  renderToStaticMarkup(<MorningRoll rows={rows} cast={[]} me={me} />);

describe('MorningRoll', () => {
  it('reads a row per death: who, the role, how, with the attacker’s sigil', () => {
    const out = html([
      { kind: 'death', player: 'player_1', role: 'villager', types: ['wolves'] },
      { kind: 'death', player: 'player_9', role: 'healer', types: ['vigilante'] },
    ]);
    expect(out.match(/data-roll-row="death"/g)).toHaveLength(2);
    expect(out).toContain('Seat 1 · Villager');
    expect(out).toContain('killed by the wolves');
    expect(out).toContain('Seat 9 · Healer');
    expect(out).toContain('shot by the vigilante');
    expect(out).toMatch(/data-sigil="wolf"[\s\S]*data-sigil="vigilante"/);
  });

  it('holds the roles back until the cards have come down', () => {
    const out = renderToStaticMarkup(
      <MorningRoll
        rows={[{ kind: 'death', player: 'player_1', role: 'villager', types: ['wolves'] }]}
        cast={[]}
        me={null}
        roles={false}
      />,
    );
    expect(out).toContain('Seat 1');
    expect(out).not.toContain('Villager');
    expect(out).not.toContain(' · ');
    expect(out).toContain('killed by the wolves');
  });

  it('uses the game’s words for each attacker type', () => {
    const d = (types: Extract<RollRow, { kind: 'death' }>['types']): RollRow => ({
      kind: 'death',
      player: 'player_2',
      role: 'wolf',
      types,
    });
    expect(causeOf(d(['serial_killer']))).toBe('stabbed by the serial killer');
    expect(causeOf(d(['wolves', 'serial_killer']))).toBe(
      'attacked by the wolves and the serial killer, and fell',
    );
  });

  it('gives a seat saved its row, with no role and the healer’s cross', () => {
    const out = html(
      [{ kind: 'save', player: 'player_1', types: ['wolves', 'serial_killer'] }],
      'player_1',
    );
    expect(out).toContain('data-roll-row="save"');
    expect(out).toContain('Seat 1 (you)');
    expect(out).not.toContain(' · ');
    expect(out).toContain(
      'attacked by the wolves and the serial killer, saved by the healer',
    );
    expect(out).toMatch(
      /data-sigil="wolf"[\s\S]*data-sigil="serial_killer"[\s\S]*data-sigil="healer"/,
    );
  });

  it('is one line on a quiet night', () => {
    const out = html([]);
    expect(out).toContain('No one died in the night.');
    expect(out).not.toContain('data-roll');
  });
});
