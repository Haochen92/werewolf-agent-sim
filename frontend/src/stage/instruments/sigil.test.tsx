import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import { PATHS, Sigil } from './Sigil';

const ROLES = ['villager', 'healer', 'investigator', 'vigilante', 'wolf', 'serial_killer'];
const html = (el: React.ReactElement) => renderToStaticMarkup(el);

describe('Sigil', () => {
  it.each(ROLES)('draws %s as felt and as a stamp', (role) => {
    const felt = html(<Sigil role={role} variant="felt" />);
    expect(felt).toContain(`data-sigil="${role}"`);
    expect(felt).toContain('viewBox="-2 -2 52 52"');
    expect(felt).not.toContain('<mask');
    expect(felt).toContain('stroke-dasharray'); // stitched at full size

    const stamp = html(<Sigil role={role} />);
    expect(stamp).toContain('data-variant="stamp"');
    expect(stamp).toMatch(
      /<mask id="([^"]+)"[\s\S]*fill="currentColor"[^>]*mask="url\(#\1\)"/,
    );
  });

  it('drops the stitching and the fine lines when small', () => {
    const big = html(<Sigil role="vigilante" variant="felt" />);
    const small = html(<Sigil role="vigilante" variant="felt" small />);
    expect(small).not.toContain('stroke-dasharray');
    expect(small).not.toContain('M17 37.6H31');
    expect(big).toContain('M17 37.6H31');
    // a numeric width under 26 means small; the stamp drops its fine knockouts too
    expect(html(<Sigil role="vigilante" width={20} />)).not.toContain('M17 37.6H31');
    expect(html(<Sigil role="vigilante" width={40} />)).toContain('M17 37.6H31');
  });

  it('draws nothing for a role it does not know', () => {
    expect(html(<Sigil role="mayor" />)).toBe('');
    expect(html(<Sigil role="mayor" variant="felt" />)).toBe('');
  });

  it('gives each instance its own mask', () => {
    const out = html(
      <>
        <Sigil role="wolf" />
        <Sigil role="wolf" />
      </>,
    );
    const ids = [...out.matchAll(/<mask id="([^"]+)"/g)].map((m) => m[1]);
    expect(ids).toHaveLength(2);
    expect(new Set(ids).size).toBe(2);
    for (const id of ids) expect(id).toMatch(/^[\w-]+$/);
  });

  it('hands the site sprite self-painting stamps with a mask per role', () => {
    const ids = ROLES.map((role) => {
      const out = html(<svg>{PATHS[role]}</svg>);
      expect(out).toContain('viewBox="-2 -2 52 52"');
      expect(out).toContain('width="40"');
      expect(out).toMatch(/fill="currentColor" stroke="none"/);
      return /<mask id="([^"]+)"/.exec(out)?.[1];
    });
    expect(new Set(ids).size).toBe(ROLES.length);
  });
});
