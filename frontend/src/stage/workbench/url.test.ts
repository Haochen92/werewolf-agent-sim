import { describe, expect, it } from 'vitest';
import { DEFAULT_QUERY, parseQuery, writeQuery, type WorkbenchQuery } from './url';

const parse = (s: string) => parseQuery(new URLSearchParams(s));

describe('the workbench URL', () => {
  const cases: WorkbenchQuery[] = [
    DEFAULT_QUERY,
    {
      beat: 19,
      viewer: { kind: 'seat', seat: 'player_7' },
      motion: 'fast',
      slot: 'film',
      hud: 'replay',
      animate: true,
    },
    { ...DEFAULT_QUERY, beat: 3, viewer: { kind: 'xray' }, motion: 'skip', hud: 'none' },
  ];

  it('round-trips every state through the query string', () => {
    for (const q of cases) expect(parse(writeQuery(q))).toEqual(q);
  });

  it('writes canonically: all six keys, in order, with a readable seat', () => {
    expect(writeQuery(cases[1])).toBe(
      'beat=19&viewer=seat:player_7&motion=fast&slot=film&hud=replay&animate=1',
    );
    const canonical = writeQuery(cases[2]);
    expect(writeQuery(parse(canonical))).toBe(canonical);
  });

  it('reads the loose spellings and falls back to the defaults', () => {
    expect(parse('')).toEqual(DEFAULT_QUERY);
    expect(parse('viewer=seat:7&motion=1').viewer).toEqual({
      kind: 'seat',
      seat: 'player_7',
    });
    expect(parse('motion=0').motion).toBe('skip');
    expect(parse('motion=1').motion).toBe('normal');
    expect(parse('beat=-2&hud=wide&slot=x&viewer=wolf')).toEqual(DEFAULT_QUERY);
  });

  it('writes `live=1` only when on, after the six', () => {
    const live = { ...DEFAULT_QUERY, beat: 2, live: true };
    expect(writeQuery(live)).toBe(
      'beat=2&viewer=spect&motion=normal&slot=none&hud=live&animate=0&live=1',
    );
    expect(parse(writeQuery(live))).toEqual(live);
    expect(parse('live=0')).toEqual(DEFAULT_QUERY);
  });

  it('keeps keys it does not own', () => {
    const rest = new URLSearchParams('strip=0&beat=5&phase=night');
    expect(writeQuery(DEFAULT_QUERY, rest)).toBe(
      'beat=0&viewer=spect&motion=normal&slot=none&hud=live&animate=0&strip=0&phase=night',
    );
  });
});
