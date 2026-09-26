import { describe, expect, it } from 'vitest';
import { foldEvents } from '@/game/foldEvents';
import { beatsFor } from '../beats/beatsFor';
import type { SceneBeat } from '../beats/types';
import { FIXTURE_EVENTS } from '../workbench/fixture';
import {
  DEFAULT_FILTERS,
  drawerDays,
  drawerLines,
  filterLines,
  litKey,
  showRow,
  type DrawerLine,
} from './drawer-lines';

const whole = foldEvents(FIXTURE_EVENTS);
const kinds = (lines: DrawerLine[]) => new Set(lines.map((l) => l.kind));
const count = (lines: DrawerLine[], kind: DrawerLine['kind']) =>
  lines.filter((l) => l.kind === kind).length;
const byKey = (lines: DrawerLine[], key: string) => lines.find((l) => l.key === key);

/** The fold at a beat, as the scene gets it. */
function at(
  id: SceneBeat['id'],
  pick: (b: SceneBeat) => boolean,
  me: string | null = null,
) {
  const beat = beatsFor(FIXTURE_EVENTS, { xray: true, me }).find(
    (b) => b.id === id && pick(b),
  )!;
  return { beat, view: foldEvents(FIXTURE_EVENTS.slice(0, beat.end), { mySeat: me }) };
}

describe('the drawer: which lines a viewer holds', () => {
  it('gives a spectator the public record only', () => {
    const lines = drawerLines(whole, { me: null, xray: false });
    expect([...kinds(lines)].sort()).toEqual(['gm', 'rule', 'speech', 'votes']);
    expect(count(lines, 'speech')).toBe(20);
    expect(lines.every((l) => l.tier === 'public')).toBe(true);
  });

  it('adds, with the X-ray, the passes, the acts, the pack, the briefs and everyone’s private lines', () => {
    const lines = drawerLines(whole, { me: null, xray: true });
    expect(count(lines, 'pass')).toBe(12);
    expect(count(lines, 'act')).toBe(10);
    expect(count(lines, 'pack')).toBe(8);
    expect(count(lines, 'kill')).toBe(4);
    // day 4 ended the game at its morning: its brief was never read, so it is dropped
    expect(lines.filter((l) => l.kind === 'brief').map((l) => l.day)).toEqual([1, 2, 3]);
    const only = lines.filter((l) => l.kind === 'only');
    expect(only.map((l) => [l.seq, l.kind === 'only' && l.who])).toEqual([
      [59, 'Only seat 4'],
      [271, 'Only the pack'],
      [402, 'Only seat 7'],
    ]);
    expect(only.every((l) => l.tier === 'private')).toBe(true);
    expect(lines.filter((l) => l.kind === 'pass').every((l) => l.tier === 'xray')).toBe(
      true,
    );
  });

  it('gives a seated investigator its own reading as an Only-you line', () => {
    const view = foldEvents(FIXTURE_EVENTS, { mySeat: 'player_4' });
    const only = drawerLines(view, { me: 'player_4', xray: false }).filter(
      (l) => l.kind === 'only',
    );
    expect(only).toHaveLength(1);
    expect(only[0]).toMatchObject({
      who: 'Only you',
      about: 'Night 1',
      mine: true,
      text: { lead: 'You checked seat 1', chip: 'player_1', rest: ': a villager.' },
    });
  });

  it('gives a seated wolf the pack’s chat and says the failed kill without naming a role', () => {
    const view = foldEvents(FIXTURE_EVENTS, { mySeat: 'player_8' });
    const lines = drawerLines(view, { me: 'player_8', xray: false });
    expect(count(lines, 'act')).toBe(0);
    const pack = lines.filter((l) => l.kind === 'pack');
    expect(pack).toHaveLength(8);
    expect(pack.every((l) => l.tier === 'private' && l.kind === 'pack' && l.mine)).toBe(
      true,
    );
    const note = byKey(lines, 'only-271');
    expect(note).toMatchObject({
      who: 'Only you',
      text: { lead: 'Your kill on seat 2', rest: ' failed. Seat 2 survived.' },
    });
  });

  it('writes the vote as one line per day, the pairs as chips', () => {
    const lines = drawerLines(whole, { me: null, xray: false });
    const d2 = byKey(lines, 'votes-2');
    const d3 = byKey(lines, 'votes-3');
    expect(d2?.kind === 'votes' && d2.pairs.every((p) => p.votee === 'abstain')).toBe(true);
    expect(d3?.kind === 'votes' && d3.pairs).toHaveLength(7);
    expect(d3?.covers).toEqual([242, 243, 244, 245, 246, 247, 248]);
    expect(d3?.seats).toContain('player_7');
    expect(byKey(lines, 'votes-1')).toBeUndefined();
  });

  it('lends the game master’s lines the sigils of the lynch and the night they tell', () => {
    const lines = drawerLines(whole, { me: null, xray: false });
    expect(byKey(lines, 'gm-249')).toMatchObject({ about: 'vote', roles: ['villager'] });
    expect(byKey(lines, 'gm-383')).toMatchObject({
      about: 'vote',
      roles: ['serial_killer'],
    });
    expect(byKey(lines, 'gm-155')).toMatchObject({
      about: 'dawn',
      roles: ['wolf', 'investigator'],
    });
    expect(byKey(lines, 'gm-57')).toMatchObject({
      about: 'dawn',
      roles: [],
      seats: ['player_1'],
    });
    expect(byKey(lines, 'gm-405')).toMatchObject({ about: 'over', covers: [406] });
  });

  it('runs the chapters down it as rules, in the log’s order', () => {
    const rules = drawerLines(whole, { me: null, xray: false })
      .filter((l) => l.kind === 'rule')
      .map((l) => (l.kind === 'rule' ? l.text : ''));
    expect(rules).toEqual([
      'Day 1 · discussion',
      'Night 1',
      'Morning 1',
      'Day 2 · discussion',
      'Day 2 · the vote',
      'Night 2',
      'Morning 2',
      'Day 3 · discussion',
      'Day 3 · the vote',
      'Night 3',
      'Morning 3',
      'Day 4 · discussion',
      'Day 4 · the vote',
      'Night 4',
      'Morning 4',
      'Game over',
    ]);
  });

  it('stops at the beat: a day-3 speech holds nothing of the vote', () => {
    const { beat, view } = at('day.speech', (b) => b.seq === 200);
    const lines = drawerLines(view, { me: null, xray: true, beat });
    expect(byKey(lines, 'votes-3')).toBeUndefined();
    expect(lines.at(-1)?.key).toBe('say-200');
    expect(litKey(lines, beat)).toBe('say-200');
  });

  it('shows a day’s brief from its own morning beat on, not before', () => {
    const only = at('morning.only-you', (b) => b.day === 1);
    expect(
      byKey(drawerLines(only.view, { me: null, xray: true, beat: only.beat }), 'brief-1'),
    ).toBeUndefined();
    const carried = at('morning.carried-summary', (b) => b.day === 1);
    const lines = drawerLines(carried.view, { me: null, xray: true, beat: carried.beat });
    expect(lines.at(-1)?.key).toBe('brief-1');
    expect(litKey(lines, carried.beat)).toBe('brief-1');
  });
});

describe('the drawer: the lit line', () => {
  const lines = drawerLines(whole, { me: null, xray: true });
  const beat = (id: SceneBeat['id'], day: number, seq = -1) =>
    ({ id, day, seq }) as Pick<SceneBeat, 'id' | 'day' | 'seq'>;

  it('lights the line the beat is about', () => {
    expect(litKey(lines, beat('vote.chip-counted', 3, 242))).toBeNull();
    expect(litKey(lines, beat('lynch.card-up', 4, 384))).toBe('gm-383');
    expect(litKey(lines, beat('vote.result', 2, 119))).toBe('gm-118');
    expect(litKey(lines, beat('morning.chip-fell', 2, 156))).toBe('gm-155');
    expect(litKey(lines, beat('morning.quiet', 1, 58))).toBe('gm-57');
    expect(litKey(lines, beat('pack.decided', 1, 56))).toBe('kill-1');
    expect(litKey(lines, beat('morning.only-you', 3, 271))).toBe('only-271');
    expect(litKey(lines, beat('over.verdict', 4, 406))).toBe('gm-405');
    expect(litKey(lines, beat('night.hub', 2, 120))).toBeNull();
  });
});

describe('the drawer: the filters', () => {
  const lines = drawerLines(whole, { me: null, xray: true });

  it('keeps everything by default', () => {
    expect(filterLines(lines, DEFAULT_FILTERS)).toHaveLength(lines.length);
  });

  it('filters by day, and a rule with nothing under it goes', () => {
    const d3 = filterLines(lines, { ...DEFAULT_FILTERS, day: 3 });
    expect(d3.every((l) => l.day === 3)).toBe(true);
    const spect = filterLines(
      drawerLines(whole, { me: null, xray: false }),
      DEFAULT_FILTERS,
    );
    const texts = spect
      .filter((l) => l.kind === 'rule')
      .map((l) => l.kind === 'rule' && l.text);
    // day 2's discussion was all passes, which a spectator does not have
    expect(texts).not.toContain('Day 2 · discussion');
    expect(texts).toContain('Day 2 · the vote');
  });

  it('filters by seat: the seat’s own lines, the lines about it', () => {
    const s6 = filterLines(lines, { ...DEFAULT_FILTERS, seat: 'player_6' });
    const keys = s6.map((l) => l.key);
    expect(keys).toContain('votes-3');
    expect(keys).toContain('gm-249');
    expect(keys).toContain('pass-207');
    expect(keys).not.toContain('say-200');
  });

  it('filters by tier', () => {
    const noXray = filterLines(lines, {
      ...DEFAULT_FILTERS,
      show: { public: true, private: true, xray: false },
    });
    expect(count(noXray, 'pass') + count(noXray, 'act') + count(noXray, 'brief')).toBe(0);
    expect(count(noXray, 'only')).toBe(3);
    const nothing = filterLines(lines, {
      ...DEFAULT_FILTERS,
      show: { public: false, private: false, xray: false },
    });
    expect(nothing).toEqual([]);
  });

  it('has a day tab per day and the Show toggles the viewer holds', () => {
    expect(drawerDays(lines)).toEqual([1, 2, 3, 4]);
    expect(showRow(null, false)).toEqual([]);
    expect(showRow('player_4', false)).toEqual(['public', 'private']);
    expect(showRow(null, true)).toEqual(['public', 'private', 'xray']);
  });
});

describe('the drawer at an X-ray night’s spoke', () => {
  const night1 = (beat: SceneBeat, view: ReturnType<typeof foldEvents>) =>
    drawerLines(view, { me: null, xray: true, beat })
      .filter(
        (l) => l.day === 1 && (l.kind === 'act' || l.kind === 'pack' || l.kind === 'kill'),
      )
      .map((l) => l.key);

  it('shows the branches before it whole, its own up to the step, none after it', () => {
    // night 1: the three single acts (seqs 36, 39, 44), then the pack (33, 46, 48, 50, the kill)
    const first = at('rnight.spoke', (b) => b.day === 1 && b.spoke?.rank === 0);
    expect(night1(first.beat, first.view)).toEqual(['act-36']);
    const pack2 = at(
      'rnight.spoke',
      (b) => b.day === 1 && b.spoke?.actor === 'pack' && b.spoke.step === 1,
    );
    expect(night1(pack2.beat, pack2.view)).toEqual([
      'pack-33',
      'act-36',
      'act-39',
      'act-44',
      'pack-46',
    ]);
    const mark = at(
      'rnight.spoke',
      (b) => b.day === 1 && b.spoke?.actor === 'pack' && b.spoke.step === 4,
    );
    expect(night1(mark.beat, mark.view)).toContain('kill-1');
    expect(night1(mark.beat, mark.view)).toContain('pack-50');
  });
});

describe('the drawer: the votes line waits for the count', () => {
  it('holds the pairs back while the chips are being counted', () => {
    const counting = at('vote.count-begins', (b) => b.day === 3);
    const lines = drawerLines(counting.view, { me: null, xray: false, beat: counting.beat });
    expect(byKey(lines, 'votes-3')).toBeUndefined();
    expect(litKey(lines, counting.beat)).toBeNull();
    const chip = at('vote.chip-counted', (b) => b.day === 3 && b.ordinal === 3);
    expect(
      byKey(drawerLines(chip.view, { me: null, xray: false, beat: chip.beat }), 'votes-3'),
    ).toBeUndefined();
  });

  it('lands with the result, and stays for the days after', () => {
    const result = at('vote.result', (b) => b.day === 3);
    const lines = drawerLines(result.view, { me: null, xray: false, beat: result.beat });
    expect(byKey(lines, 'votes-3')).toBeDefined();
    const later = at('vote.count-begins', (b) => b.day === 4);
    expect(
      byKey(drawerLines(later.view, { me: null, xray: false, beat: later.beat }), 'votes-3'),
    ).toBeDefined();
  });
});

describe('the drawer: the game master’s vote line waits for the card', () => {
  it('holds a lynch’s line back until the truth, but a no-lynch day gets it with the result', () => {
    const named = at('lynch.named', (b) => b.day === 3);
    const held = drawerLines(named.view, { me: null, xray: false, beat: named.beat });
    expect(byKey(held, 'votes-3')).toBeDefined();
    expect(byKey(held, 'gm-249')).toBeUndefined();
    expect(litKey(held, named.beat)).toBe('votes-3');
    const truth = at('lynch.truth', (b) => b.day === 3);
    const told = drawerLines(truth.view, { me: null, xray: false, beat: truth.beat });
    expect(byKey(told, 'gm-249')).toBeDefined();
    expect(litKey(told, truth.beat)).toBe('gm-249');
    const abstained = at('vote.result', (b) => b.day === 2);
    const lines = drawerLines(abstained.view, { me: null, xray: false, beat: abstained.beat });
    expect(byKey(lines, 'gm-118')).toBeDefined();
  });
});
