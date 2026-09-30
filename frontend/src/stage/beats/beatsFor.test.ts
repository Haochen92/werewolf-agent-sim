/**
 * Holds `beatsFor` to `docs/beat_sheet.md` on the fixture game. The goldens are the whole beat
 * list, one line each, for the two replay tiers; change the sheet, change the cutter, then
 * regenerate them (`npx vitest run -u`) and read the diff — the diff IS the review.
 */
import { describe, expect, it } from 'vitest';
import type { DurableGameEvent } from '@/types/contracts';
import fixture from '@/stage/fixtures/replay-9369a5c1.json';
import { beatsFor, chapterMarks } from './beatsFor';
import type { SceneBeat } from './types';

const events = fixture.events as unknown as DurableGameEvent[];

function line(b: SceneBeat, i: number): string {
  const who = b.seat ? `@${b.seat}` : '';
  const about = b.subject ? ` →${b.subject}` : '';
  const nth = b.ordinal ? ` #${b.ordinal}` : '';
  const spoke = b.spoke
    ? ` spoke ${b.spoke.actor} r${b.spoke.rank} ${b.spoke.step + 1}/${b.spoke.steps}`
    : '';
  const page = b.page ? ` p${b.page.index + 1}/${b.page.count}` : '';
  const chapter = b.chapter ? `  [${b.chapter.kind} ${b.chapter.n}]` : '';
  return `${String(i).padStart(3)}  ${b.id.padEnd(24)} d${b.day} seq${String(b.seq).padStart(3)} end${String(b.end).padStart(3)}  ${b.sees}${who}${about}${nth}${spoke}${page}  ${b.holdMs}ms${chapter}`;
}

const dump = (beats: SceneBeat[]) => beats.map(line).join('\n') + '\n';

describe('beatsFor on the fixture (9369a5c1, memory on)', () => {
  const pub = beatsFor(events, { xray: false });
  const xray = beatsFor(events, { xray: true });

  it('public tier matches the golden', async () => {
    await expect(dump(pub)).toMatchFileSnapshot('./__goldens__/9369a5c1.public.txt');
  });

  it('X-ray tier matches the golden', async () => {
    await expect(dump(xray)).toMatchFileSnapshot('./__goldens__/9369a5c1.xray.txt');
  });

  it('reveals the log monotonically', () => {
    for (const beats of [pub, xray]) {
      for (let i = 1; i < beats.length; i++)
        expect(beats[i].end).toBeGreaterThanOrEqual(beats[i - 1].end);
      expect(beats.at(-1)?.end).toBe(events.length);
    }
  });

  it('the X-ray adds beats and never drops a public one', () => {
    const key = (b: SceneBeat) => `${b.id}|${b.seq}|${b.ordinal ?? ''}|${b.subject ?? ''}`;
    const inXray = new Set(xray.map(key));
    // The public pass is derived from `turn_started`; the X-ray carries it as `pass_marker`.
    for (const b of pub)
      if (b.sees === 'public' && b.id !== 'night.hub' && b.id !== 'day.pass')
        expect(inXray.has(key(b))).toBe(true);
    expect(xray.length).toBeGreaterThan(pub.length);
  });

  it('shows a pass to everyone: a turn that ends with no speech', () => {
    // Day 1 of the fixture is three passes and nothing else.
    const day1 = pub.filter((b) => b.scene === 'day' && b.day === 1);
    expect(day1.map((b) => [b.id, b.subject])).toEqual([
      ['day.pass', 'player_1'],
      ['day.pass', 'player_5'],
      ['day.pass', 'player_4'],
    ]);
    // One derived pass per X-ray pass_marker, over the whole game.
    expect(pub.filter((b) => b.id === 'day.pass').length).toBe(
      xray.filter((b) => b.id === 'day.pass').length,
    );
    // A pass reveals the log up to, not including, what resolved it.
    const first = day1[0];
    expect(events[first.end].type).toMatch(/turn_started|phase_change/);
  });

  it('live, the puppet thinks on the stand until the turn resolves', () => {
    const live = beatsFor(events, { xray: false, live: true });
    const day3 = live.filter((b) => b.scene === 'day' && b.day === 3).map((b) => b.id);
    // day 3's first two speeches are two pages each (pages.ts): a beat per page
    expect(day3.slice(0, 6)).toEqual([
      'day.turn-thinking',
      'day.speech',
      'day.speech',
      'day.turn-thinking',
      'day.speech',
      'day.speech',
    ]);
    expect(pub.some((b) => b.id === 'day.turn-thinking')).toBe(false);
  });

  it('marks the chapters the sheet lists', () => {
    const marks = chapterMarks(pub).map(
      ({ beat }) => `${beat.chapter!.kind} ${beat.chapter!.n}`,
    );
    expect(marks).toEqual([
      'day 1',
      'night 1',
      'morning 1',
      'day 2',
      'vote 2',
      'night 2',
      'morning 2',
      'day 3',
      'vote 3',
      'night 3',
      'morning 3',
      'day 4',
      'vote 4',
      'night 4',
      'morning 4',
      'over 0',
    ]);
  });

  it('plays the morning shapes the fixture has', () => {
    // "The day begins" opens Day N+1 and is tagged with it, so it is not part of Morning N here.
    const ids = (day: number) =>
      pub
        .filter(
          (b) => b.scene === 'morning' && b.day === day && b.id !== 'morning.day-begins',
        )
        .map((b) => b.id);
    expect(ids(1)).toEqual([
      'morning.shutter-down',
      'morning.chip-attacked',
      'morning.chip-saved',
    ]);
    expect(ids(2)).toEqual([
      'morning.shutter-down',
      'morning.chip-attacked',
      'morning.chip-fell',
      'morning.card-down',
      'morning.chip-attacked',
      'morning.chip-fell',
      'morning.card-down',
    ]);
  });

  it('keeps private results out of the public replay and in the X-ray, in aqua', () => {
    expect(pub.some((b) => b.id === 'morning.only-you')).toBe(false);
    const only = xray.filter((b) => b.id === 'morning.only-you');
    expect(only.map((b) => [b.seq, b.sees, b.seat ?? b.subject])).toEqual([
      [59, 'seat', 'player_4'],
      [271, 'faction', undefined],
    ]);
  });

  it('gives the seated human their own beats and the wolf the pack', () => {
    const villager = beatsFor(events, { xray: false, me: 'player_1', live: true });
    expect(villager.filter((b) => b.id === 'deal.your-card').map((b) => b.seat)).toEqual([
      'player_1',
    ]);
    expect(villager.some((b) => b.scene === 'pack')).toBe(false);
    const wolf = beatsFor(events, { xray: false, me: 'player_3', live: true });
    expect(wolf.some((b) => b.id === 'deal.your-pack')).toBe(true);
    expect(wolf.filter((b) => b.id === 'pack.decided').map((b) => b.subject)).toEqual([
      'player_1',
      'player_4',
      'player_2',
      'player_1',
    ]);
    // The failed-kill note is the pack's, so the wolf has it without X-ray.
    expect(wolf.filter((b) => b.id === 'morning.only-you').map((b) => b.seq)).toEqual([
      271,
    ]);
  });

  it('tells a long speech a page at a time, each page held for its own words', () => {
    const first = pub.filter((b) => b.id === 'day.speech' && b.seq === 163);
    expect(first.map((b) => b.page)).toEqual([
      { index: 0, count: 2 },
      { index: 1, count: 2 },
    ]);
    // the pages share the speech's anchor, so they show the same log
    expect(new Set(first.map((b) => b.end)).size).toBe(1);
    for (const b of first) {
      expect(b.holdMs).toBeGreaterThanOrEqual(5000);
      expect(b.holdMs).toBeLessThanOrEqual(15000);
    }
    // a speech that fits the box is one beat, with no page mark
    const one = pub.filter((b) => b.id === 'day.speech' && !b.page);
    expect(one.length).toBeGreaterThan(0);
  });

  it('marks a lynch that ends the game, so no night is played after it', () => {
    // The fixture's lynches are all followed by a night. Cut the log after day 4's lynch and
    // end the game there instead.
    const lynch = events.findIndex((e) => e.type === 'lynch_result' && e.seq === 384);
    const over = events.find((e) => e.type === 'game_over')!;
    const ended = [...events.slice(0, lynch + 1), { ...over, seq: 385 }];
    const last = beatsFor(ended, { xray: false }).find(
      (b) => b.id === 'lynch.card-to-wing' && b.day === 4,
    );
    expect(last?.endsGame).toBe(true);
    expect(
      pub.find((b) => b.id === 'lynch.card-to-wing' && b.day === 4)?.endsGame,
    ).toBeUndefined();
  });

  it('orders the X-ray night by each branch’s last event, the whole night last', () => {
    const night2 = xray.filter((b) => b.scene === 'rnight' && b.day === 2);
    expect(night2[0].id).toBe('rnight.hub');
    expect(night2.at(-1)?.id).toBe('rnight.whole');
    const ranks = night2.filter((b) => b.spoke).map((b) => b.spoke!.rank);
    expect(ranks).toEqual([...ranks].sort((a, b) => a - b));
    // Night 2: the pack (two wolves) talks, then votes; it closes the night.
    const pack = night2.filter((b) => b.spoke?.actor === 'pack');
    expect(pack.at(-1)?.spoke?.rank).toBe(Math.max(...ranks));
    expect(pack.length).toBeGreaterThan(1);
  });
});
