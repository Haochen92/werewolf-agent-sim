import { describe, expect, it } from 'vitest';
import { foldEvents } from '@/game/foldEvents';
import { beatsFor } from '../beats/beatsFor';
import type { SceneBeat } from '../beats/types';
import { FIXTURE_EVENTS } from '../workbench/fixture';
import {
  briefRows,
  DEFAULT_FILTERS,
  drawerDays,
  drawerLines,
  filterLines,
  groupPasses,
  litKey,
  passSentence,
  passWhy,
  reportParts,
  shownKeys,
  showRow,
  voteSentence,
  voteTally,
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
  it('gives a spectator the public record only, the day’s briefs among it', () => {
    const lines = drawerLines(whole, { me: null, xray: false });
    expect([...kinds(lines)].sort()).toEqual(['brief', 'gm', 'rule', 'speech', 'votes']);
    expect(count(lines, 'speech')).toBe(20);
    expect(lines.every((l) => l.tier === 'public')).toBe(true);
    // day 4 ended the game at its morning: its brief was never read, so it is dropped
    expect(lines.filter((l) => l.kind === 'brief').map((l) => l.day)).toEqual([1, 2, 3]);
  });

  it('adds, with the X-ray, the passes, the acts, the pack and everyone’s private lines', () => {
    const lines = drawerLines(whole, { me: null, xray: true });
    expect(count(lines, 'pass')).toBe(12);
    expect(count(lines, 'act')).toBe(10);
    expect(count(lines, 'pack')).toBe(8);
    expect(count(lines, 'kill')).toBe(4);
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
    expect(count(noXray, 'pass') + count(noXray, 'act')).toBe(0);
    // the brief is public: it stays
    expect(count(noXray, 'brief')).toBe(3);
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
    // the X-ray's lines have no toggle of their own: they follow the X-ray's switch
    expect(showRow(null, true)).toEqual(['public', 'private']);
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
    const lines = drawerLines(counting.view, {
      me: null,
      xray: false,
      beat: counting.beat,
    });
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
      byKey(
        drawerLines(later.view, { me: null, xray: false, beat: later.beat }),
        'votes-3',
      ),
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
    const lines = drawerLines(abstained.view, {
      me: null,
      xray: false,
      beat: abstained.beat,
    });
    expect(byKey(lines, 'gm-118')).toBeDefined();
  });
});

describe('the drawer: how it tells what it holds', () => {
  const xray = drawerLines(whole, { me: null, xray: true });
  const gm = (key: string) => byKey(xray, key) as DrawerLine & { kind: 'gm' };

  it('folds a run of passes into one line, and a pass between speeches stays alone', () => {
    const runs = groupPasses(xray).filter((l) => l.kind === 'passes');
    expect(runs.map((r) => r.kind === 'passes' && r.passes.map((p) => p.player))).toEqual([
      ['player_1', 'player_5', 'player_4'],
      ['player_2', 'player_7', 'player_9'],
      ['player_7', 'player_9'],
      ['player_6', 'player_2', 'player_1'],
      ['player_1'],
    ]);
    // nothing else is touched, and every pass is still in a run
    expect(groupPasses(xray).filter((l) => l.kind !== 'passes')).toEqual(
      xray.filter((l) => l.kind !== 'pass'),
    );
    expect(runs.flatMap(shownKeys)).toEqual(
      xray.filter((l) => l.kind === 'pass').map((l) => l.key),
    );
    // the key is the run's first pass, so it holds while later passes join
    expect(runs[2].key).toBe('passes-pass-183');
  });

  it('runs the passes under the filters: one seat’s passes are its own', () => {
    const seat7 = groupPasses(filterLines(xray, { ...DEFAULT_FILTERS, seat: 'player_7' }));
    const runs = seat7.filter((l) => l.kind === 'passes');
    expect(runs.map((r) => r.kind === 'passes' && r.passes.length)).toEqual([1, 1]);
  });

  it('says each pass as the table saw it, and why only where the X-ray knows', () => {
    expect(passSentence({ player: 'player_7' })).toBe('Seat 7 passed');
    expect(passWhy({ reason: 'voluntary' })).toBeNull();
    expect(passWhy({ reason: null })).toBeNull();
    expect(passWhy({ reason: 'novelty_gated' })).toBe('held back: nothing new to say');
    expect(passWhy({ reason: 'generation_failed' })).toBe('no line came');
  });

  it('reads "an" before a role that opens on a vowel, and leaves the rest', () => {
    const texts = reportParts(gm('gm-155'), true).map((p) => p.text);
    expect(texts[1]).toBe(
      'Seat 4 was killed by the wolves last night. They were an investigator.',
    );
    expect(texts[0]).toMatch(/They were a wolf\.$/);
  });

  it('tallies the vote: most votes first, voters in seat order, abstentions last', () => {
    const votes = (day: number) =>
      (byKey(xray, `votes-${day}`) as DrawerLine & { kind: 'votes' }).pairs;
    expect(voteTally(votes(3))).toEqual([
      {
        votee: 'player_6',
        voters: ['player_1', 'player_2', 'player_5', 'player_7', 'player_8', 'player_9'],
      },
      { votee: 'player_7', voters: ['player_6'] },
    ]);
    expect(voteSentence(voteTally(votes(3)))).toBe(
      'Seats 1, 2, 5, 7, 8 and 9 voted for seat 6. Seat 6 voted for seat 7.',
    );
    expect(voteSentence(voteTally(votes(4)))).toBe(
      'Seats 1, 7 and 8 voted for seat 2. Seats 2 and 9 voted for seat 7.',
    );
    const mixed = voteTally([
      { voter: 'player_3', votee: 'abstain' },
      { voter: 'player_2', votee: 'player_5' },
    ]);
    expect(mixed.map((r) => r.votee)).toEqual(['player_5', 'abstain']);
    expect(voteSentence(mixed)).toBe('Seat 2 voted for seat 5. Seat 3 abstained.');
  });

  it('sets the morning report as one sentence per seat, each with the role it tells', () => {
    expect(reportParts(gm('gm-155'), true)).toEqual([
      {
        text: 'Seat 3 was stabbed by the serial killer last night. They were a wolf.',
        seat: 'player_3',
        role: 'wolf',
      },
      {
        text: 'Seat 4 was killed by the wolves last night. They were an investigator.',
        seat: 'player_4',
        role: 'investigator',
      },
    ]);
    // a save names a seat that did not die: no role
    expect(reportParts(gm('gm-57'), true)).toEqual([
      {
        text: 'Seat 1 was attacked by the wolves and the serial killer but was saved by the healer!',
        seat: 'player_1',
        role: null,
      },
    ]);
  });

  it('drops the vote line’s heading and the ballots the votes line already told', () => {
    expect(reportParts(gm('gm-249'), true)).toEqual([
      {
        text: 'Seat 6 has been voted out and was a villager.',
        seat: 'player_6',
        role: 'villager',
      },
    ]);
    expect(reportParts(gm('gm-383'), true).map((p) => p.text)).toEqual([
      'Seat 2 has been voted out and was a serial killer.',
    ]);
    // with no votes line to tell them, the ballots stay, one to a line
    expect(
      reportParts(gm('gm-249'), false)
        .map((p) => p.text)
        .slice(0, 2),
    ).toEqual(['Seat 1 voted for seat 6', 'Seat 2 voted for seat 6']);
    expect(reportParts(gm('gm-30'), false).map((p) => p.text)).toEqual([
      'No vote was held today; no one is eliminated.',
    ]);
  });

  it('marks each rule with its chapter', () => {
    const rules = xray.filter((l) => l.kind === 'rule');
    expect(new Set(rules.map((l) => l.kind === 'rule' && l.chapter))).toEqual(
      new Set(['day', 'vote', 'night', 'morning', 'over']),
    );
  });
});

describe('the day’s brief as rows', () => {
  const day1 =
    'Key accusations and defenses: None.\nRole claims: None.\nAlliances and blocs: None.\n' +
    'Village dynamics: The village is information-starved.';

  it('folds the sections that say "None." into one quiet line where the first stood', () => {
    expect(briefRows(day1)).toEqual([
      { kind: 'none', text: 'No accusations, claims or alliances yet' },
      {
        kind: 'row',
        label: 'Village dynamics',
        items: ['The village is information-starved.'],
      },
    ]);
  });

  it('splits the accusations one per item and keeps the order of the headings', () => {
    const rows = briefRows(
      'Key accusations and defenses: player_7 → player_6: pushed. | player_8 → player_2: hid.\n' +
        'Role claims: None.\nAlliances and blocs: player_1 and player_2.\n' +
        'Village dynamics: Split.\nStill split.',
    );
    expect(rows).toEqual([
      {
        kind: 'row',
        label: 'Accusations and defences',
        items: ['player_7 → player_6: pushed.', 'player_8 → player_2: hid.'],
      },
      { kind: 'none', text: 'No claims yet' },
      { kind: 'row', label: 'Alliances and blocs', items: ['player_1 and player_2.'] },
      // a line with no heading carries on the section above it
      { kind: 'row', label: 'Village dynamics', items: ['Split. Still split.'] },
    ]);
  });

  it('says nothing is there when every section is "None."', () => {
    expect(
      briefRows(
        'Key accusations and defenses: None.\nRole claims: None.\nAlliances and blocs: None.\nVillage dynamics: None.',
      ),
    ).toEqual([
      { kind: 'none', text: 'No accusations, claims, alliances or village dynamics yet' },
    ]);
  });

  it('gives up on a text that does not open with the four headings, in order', () => {
    expect(briefRows('The village argued all day.')).toBeNull();
    expect(briefRows('Role claims: None.\nKey accusations and defenses: None.')).toBeNull();
    expect(briefRows('Key accusations and defenses: None.\nRole claims: None.')).toBeNull();
  });
});
