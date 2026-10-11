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
    { ...DEFAULT_QUERY, beat: 3, viewer: { kind: 'xray' }, motion: 'fast', hud: 'none' },
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
    expect(parse('motion=0').motion).toBe('fast');
    expect(parse('motion=skip').motion).toBe('fast');
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

  it('writes `game` and `ledger=off` only when set, after `summary`', () => {
    const q = {
      ...DEFAULT_QUERY,
      summaryV4: true,
      game: '140610ad' as const,
      noLedger: true,
    };
    expect(writeQuery(q)).toBe(
      'beat=0&viewer=spect&motion=normal&slot=none&hud=live&animate=0&summary=v4&game=140610ad&ledger=off',
    );
    expect(parse(writeQuery(q))).toEqual(q);
    expect(parse('game=nope&ledger=on')).toEqual(DEFAULT_QUERY);
    // the old default, the nine-seat fixture, is a game of its own now
    expect(parse('game=9369a5c1')).toEqual({ ...DEFAULT_QUERY, game: '9369a5c1' });
  });

  it('writes `memory=off` only when set, after `live`', () => {
    const off = { ...DEFAULT_QUERY, live: true, memoryOff: true };
    expect(writeQuery(off)).toBe(
      'beat=0&viewer=spect&motion=normal&slot=none&hud=live&animate=0&live=1&memory=off',
    );
    expect(parse(writeQuery(off))).toEqual(off);
    expect(parse('memory=on')).toEqual(DEFAULT_QUERY);
  });

  it('writes `summary=v4` only when set, after `memory`', () => {
    const v4 = { ...DEFAULT_QUERY, memoryOff: true, summaryV4: true };
    expect(writeQuery(v4)).toBe(
      'beat=0&viewer=spect&motion=normal&slot=none&hud=live&animate=0&memory=off&summary=v4',
    );
    expect(parse(writeQuery(v4))).toEqual(v4);
    expect(parse('summary=v3')).toEqual(DEFAULT_QUERY);
  });

  it('reads a phone frame, a preset by its key or a free WxH, and writes it only when set', () => {
    expect(parse('frame=iphone14').frame).toEqual({
      id: 'iphone14',
      name: 'iPhone 14',
      w: 844,
      h: 390,
    });
    expect(parse('frame=iphone15max').frame).toMatchObject({ w: 932, h: 430 });
    expect(parse('frame=pixel8').frame).toMatchObject({ name: 'Pixel 8', w: 915, h: 412 });
    expect(parse('frame=1000x500').frame).toEqual({ id: '1000x500', w: 1000, h: 500 });
    expect(parse('frame=0800X0400').frame).toEqual({ id: '800x400', w: 800, h: 400 });
    for (const q of [
      { ...DEFAULT_QUERY, frame: parse('frame=iphone15max').frame },
      { ...DEFAULT_QUERY, beat: 4, live: true, frame: parse('frame=1000x500').frame },
    ])
      expect(parse(writeQuery(q))).toEqual(q);
    expect(
      writeQuery({ ...DEFAULT_QUERY, live: true, frame: parse('frame=pixel8').frame }),
    ).toBe(
      'beat=0&viewer=spect&motion=normal&slot=none&hud=live&animate=0&live=1&frame=pixel8',
    );
    for (const bad of [
      'fill',
      '',
      'iphone',
      '0x400',
      '800x0',
      '-800x400',
      '800x',
      '8.5x4',
      'x',
    ])
      expect(parse(`frame=${bad}`)).toEqual(DEFAULT_QUERY);
    expect(writeQuery(parse('frame=fill'))).not.toContain('frame');
  });

  it('keeps keys it does not own', () => {
    const rest = new URLSearchParams('strip=0&beat=5&phase=night');
    expect(writeQuery(DEFAULT_QUERY, rest)).toBe(
      'beat=0&viewer=spect&motion=normal&slot=none&hud=live&animate=0&strip=0&phase=night',
    );
  });
});
