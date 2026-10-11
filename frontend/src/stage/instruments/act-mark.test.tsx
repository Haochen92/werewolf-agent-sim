import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { ATTACK_MARK, ActMark, MARK_ROLE, type ActKind } from './ActMark';

const html = (el: React.ReactElement) => renderToStaticMarkup(el);

describe('ActMark', () => {
  it.each([
    ['bite', 'wolf'],
    ['knife', 'serial_killer'],
    ['bullet', 'vigilante'],
    ['sigil', 'sigilist'],
    ['plaster', 'healer'],
    ['lens', 'investigator'],
  ] as [ActKind, string][])('pins %s as the %s’s felt sigil', (kind, role) => {
    expect(MARK_ROLE[kind]).toBe(role);
    const out = html(<ActMark kind={kind} x={100} y={100} k={40} />);
    // still named for the act, never the actor
    expect(out).toContain(`aria-label="${kind}"`);
    expect(out).toContain(`data-sigil="${role}" data-variant="felt"`);
    // its flat shadow is the same silhouette as a one-colour stamp
    expect(out).toContain(`data-sigil="${role}" data-variant="stamp"`);
  });

  it('keeps its box: 2.6 half-sizes square about its centre', () => {
    const out = html(<ActMark kind="bite" x={100} y={200} k={50} />);
    expect(out).toMatch(/left:35px;top:135px;width:130px;height:130px/);
  });

  it('drops the stitching when small', () => {
    expect(html(<ActMark kind="bite" x={0} y={0} k={40} />)).toContain('stroke-dasharray');
    expect(html(<ActMark kind="bite" x={0} y={0} k={20} />)).not.toContain(
      'stroke-dasharray',
    );
  });

  it('maps each attacker type to the mark its role leaves (a reanimated body, its kind’s)', () => {
    expect(ATTACK_MARK).toEqual({
      wolves: 'bite',
      serial_killer: 'knife',
      vigilante: 'bullet',
      sigilist: 'sigil',
      reanimated_wolves: 'bite',
      reanimated_vigilante: 'bullet',
      reanimated_sigilist: 'sigil',
    });
  });
});
