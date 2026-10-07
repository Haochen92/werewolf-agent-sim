import { renderToStaticMarkup } from 'react-dom/server';
import { describe, expect, it } from 'vitest';
import type { Faction } from '../roles';
import { FactionMark, type MarkFormat } from './FactionMark';
import { MARKS } from './Sigil';

const SIDES: Faction[] = ['villagers', 'wolves', 'serial_killer', 'neutral_benign'];
const FORMATS: MarkFormat[] = ['badge', 'pennant', 'mark'];
const html = (el: React.ReactElement) => renderToStaticMarkup(el);

describe('FactionMark', () => {
  it.each(SIDES)('draws %s in every format, felt and stamp', (f) => {
    for (const format of FORMATS) {
      const felt = html(<FactionMark faction={f} format={format} />);
      expect(felt).toContain(`data-faction="${f}"`);
      expect(felt).toContain(`data-format="${format}"`);
      expect(felt).toContain(MARKS[f].base);
      expect(felt).not.toContain('<mask');
      expect(felt).toContain('stroke-dasharray'); // stitched at full size
      const stamp = html(<FactionMark faction={f} format={format} variant="stamp" />);
      expect(stamp).toMatch(
        /<mask id="([^"]+)"[\s\S]*fill="currentColor"[^>]*mask="url\(#\1\)"/,
      );
    }
  });

  it('seats the mark inside a badge or a pennant, and leaves the bare mark unmoved', () => {
    expect(html(<FactionMark faction="wolves" format="badge" />)).toContain(
      'transform="translate(24 24) scale(0.640) translate(-24 -23.5)"',
    );
    expect(html(<FactionMark faction="neutral_benign" format="pennant" />)).toContain(
      'transform="translate(24 21) scale(0.502) translate(-24 -23.73)"',
    );
    expect(html(<FactionMark faction="wolves" format="mark" />)).not.toContain(
      'translate(',
    );
  });

  it('cuts the mark out of a stamped badge: the ground is white, the mark black', () => {
    const out = html(<FactionMark faction="villagers" format="badge" variant="stamp" />);
    expect(out).toMatch(/<mask[^>]*><path d="M2.5 24[^"]*" fill="#fff"/);
    expect(out).toMatch(new RegExp(`<path d="${MARKS.villagers.base}" fill="#000"`));
  });

  it('drops the stitching when small, and a numeric width under 26 means small', () => {
    expect(html(<FactionMark faction="villagers" format="badge" small />)).not.toContain(
      'stroke-dasharray',
    );
    expect(
      html(<FactionMark faction="villagers" format="badge" width={20} />),
    ).not.toContain('stroke-dasharray');
  });

  it('paints the raven’s wing in the deeper purple, not the sigils’ pale tone', () => {
    const out = html(<FactionMark faction="serial_killer" format="mark" />);
    expect(out).toContain('fill="#5b44a6"');
    expect(out).not.toContain('#cdc6e2');
  });

  it('gives each instance its own mask', () => {
    const out = html(
      <>
        <FactionMark faction="wolves" variant="stamp" />
        <FactionMark faction="wolves" variant="stamp" />
      </>,
    );
    const ids = [...out.matchAll(/<mask id="([^"]+)"/g)].map((m) => m[1]);
    expect(new Set(ids).size).toBe(2);
    for (const id of ids) expect(id).toMatch(/^[\w-]+$/);
  });
});
