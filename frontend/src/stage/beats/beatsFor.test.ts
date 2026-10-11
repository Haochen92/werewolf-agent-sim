/**
 * Holds `beatsFor` to `docs/beat_sheet.md` on the fixture game. The goldens are the whole beat
 * list, one line each, for the two replay tiers; change the sheet, change the cutter, then
 * regenerate them (`npx vitest run -u`) and read the diff — the diff IS the review.
 */
import { describe, expect, it } from 'vitest';
import type { DurableGameEvent } from '@/types/contracts';
import fixture from '@/stage/fixtures/replay-9369a5c1.json';
import phase2 from '@/stage/fixtures/replay-phase2.json';
import phase3 from '@/stage/fixtures/replay-phase3.json';
import necro from '@/stage/fixtures/replay-phase3-necro.json';
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
  const seats = b.subjects
    ? ` {${b.subjects.map((s) => s.replace('player_', '')).join(',')}}`
    : '';
  const chapter = b.chapter ? `  [${b.chapter.kind} ${b.chapter.n}]` : '';
  return `${String(i).padStart(3)}  ${b.id.padEnd(24)} d${b.day} seq${String(b.seq).padStart(3)} end${String(b.end).padStart(3)}  ${b.sees}${who}${about}${seats}${nth}${spoke}${page}  ${b.holdMs}ms${chapter}`;
}

const dump = (beats: SceneBeat[]) => beats.map(line).join('\n') + '\n';

describe('beatsFor on the Phase 2 game (the day with rounds, memory off)', () => {
  const log = phase2.events as unknown as DurableGameEvent[];
  const pub = beatsFor(log, { xray: false });
  const xray = beatsFor(log, { xray: true });

  it('public tier matches the golden', async () => {
    await expect(dump(pub)).toMatchFileSnapshot('./__goldens__/phase2.public.txt');
  });

  it('X-ray tier matches the golden', async () => {
    await expect(dump(xray)).toMatchFileSnapshot('./__goldens__/phase2.xray.txt');
  });

  it('reveals the log monotonically', () => {
    for (const beats of [pub, xray]) {
      for (let i = 1; i < beats.length; i++)
        expect(beats[i].end).toBeGreaterThanOrEqual(beats[i - 1].end);
      expect(beats.at(-1)?.end).toBe(log.length);
    }
  });
});

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
      'morning.roll',
    ]);
    expect(ids(2)).toEqual([
      'morning.shutter-down',
      'morning.chip-attacked',
      'morning.chip-fell',
      'morning.card-down',
      'morning.chip-attacked',
      'morning.chip-fell',
      'morning.card-down',
      'morning.roll',
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

describe('the rounds of the day, on a hand-built log (Phase 2)', () => {
  // A day-2 log built by hand so each rule can be read off a few events: the opening round
  // (four seats, one of them speaks), the first discussion turn, then a closing for two accused.
  const ev = (seq: number, type: string, rest: Record<string, unknown> = {}) =>
    ({ seq, day: 2, type, ...rest }) as unknown as DurableGameEvent;
  const SEATS = ['player_1', 'player_2', 'player_3', 'player_4'];

  const openingRound: DurableGameEvent[] = [
    ev(10, 'phase_change', { phase: 'day' }),
    ev(11, 'round_opened', { round: 'opening', players: SEATS }),
    ev(12, 'pass_marker', {
      channel_seq: 0,
      player: 'player_1',
      pass_reason: 'voluntary',
      gated: false,
    }),
    ev(13, 'speech', {
      channel_seq: 1,
      player: 'player_2',
      message: 'I checked player_4: wolf.',
    }),
    ev(14, 'addressed_targets', {
      about_channel_seq: 1,
      player: 'player_2',
      targets: [{ target: 'player_4', addressed_form: 'mention', stance: 'accusation' }],
    }),
    ev(15, 'pass_marker', {
      channel_seq: 2,
      player: 'player_3',
      pass_reason: 'voluntary',
      gated: false,
    }),
    ev(16, 'pass_marker', {
      channel_seq: 3,
      player: 'player_4',
      pass_reason: 'voluntary',
      gated: false,
    }),
    ev(17, 'turn_started', { player: 'player_4' }),
    ev(18, 'speech', { channel_seq: 4, player: 'player_4', message: 'That is a lie.' }),
  ];

  const closingRound: DurableGameEvent[] = [
    ev(19, 'gm_message', {
      channel_seq: 5,
      text: 'Before the vote: player_4 has been accused by player_2 and player_3; player_3 by player_1 and player_4. Each gets a last word.',
    }),
    ev(20, 'round_opened', { round: 'closing', players: ['player_4', 'player_3'] }),
    ev(21, 'speech', { channel_seq: 6, player: 'player_4', message: 'I am town.' }),
    ev(22, 'pass_marker', {
      channel_seq: 7,
      player: 'player_3',
      pass_reason: 'voluntary',
      gated: false,
    }),
    ev(23, 'day_summary', { summary: 'the day in brief' }),
  ];

  const byId = (beats: SceneBeat[], id: string) => {
    const found: SceneBeat[] = [];
    for (const beat of beats) {
      if (beat.id === id) found.push(beat);
    }
    return found;
  };

  it('opens with everyone preparing their opening, a public beat held open', () => {
    const beats = beatsFor(openingRound, { xray: false });

    const prepares = byId(beats, 'day.opening-prepares');
    expect(prepares).toHaveLength(1);
    expect(prepares[0].subjects).toEqual(SEATS);
    expect(prepares[0].sees).toBe('public');
    expect(prepares[0].seq).toBe(11);
    expect(prepares[0].end).toBe(2); // shows the log up to and including round_opened
    expect(prepares[0].holdMs).toBe(4000);
  });

  it('tells the round’s silent seats as one beat when the round ends, without the one who spoke', () => {
    const beats = beatsFor(openingRound, { xray: false });

    const passes = byId(beats, 'day.round-passes');
    expect(passes).toHaveLength(1);
    expect(passes[0].subjects).toEqual(['player_1', 'player_3', 'player_4']);
    expect(passes[0].sees).toBe('public');
    expect(passes[0].seq).toBe(11); // anchored on the round it closes
    // cut when the first event that is not one of the round's lines arrives (turn_started)
    expect(openingRound[passes[0].end].type).toBe('turn_started');
    // the round's own lines are not told one pass at a time in the public tier
    expect(byId(beats, 'day.pass')).toHaveLength(0);

    const order: string[] = [];
    for (const beat of beats) {
      if (beat.scene === 'day') order.push(beat.id);
    }
    expect(order).toEqual([
      'day.opening-prepares',
      'day.speech',
      'day.round-passes',
      'day.speech',
    ]);
  });

  it('in the X-ray plays each pass marker instead of the grouped beat', () => {
    const beats = beatsFor(openingRound, { xray: true });

    expect(byId(beats, 'day.round-passes')).toHaveLength(0);
    const passed: string[] = [];
    for (const beat of byId(beats, 'day.pass')) passed.push(beat.subject ?? '');
    expect(passed).toEqual(['player_1', 'player_3', 'player_4']);
    expect(byId(beats, 'day.opening-prepares')).toHaveLength(1);
  });

  it('live with the X-ray on (game over) keeps the grouped beat, as the game played it', () => {
    const beats = beatsFor(openingRound, { xray: true, live: true });

    expect(byId(beats, 'day.round-passes')).toHaveLength(1);
  });

  it('calls the first accused to the stand and groups the closing’s silent seat', () => {
    const beats = beatsFor([...openingRound, ...closingRound], { xray: false });

    const called = byId(beats, 'day.closing-called');
    expect(called).toHaveLength(1);
    expect(called[0].subject).toBe('player_4');
    expect(called[0].subjects).toEqual(['player_4', 'player_3']);
    expect(called[0].sees).toBe('public');

    const passes = byId(beats, 'day.round-passes');
    expect(passes).toHaveLength(2);
    expect(passes[1].subjects).toEqual(['player_3']);
    expect(passes[1].seq).toBe(20);
    expect(byId(beats, 'day.opening-prepares')).toHaveLength(1); // the closing is not an opening
  });

  it('tells no grouped beat when everyone in the round spoke', () => {
    const everyone: DurableGameEvent[] = [
      ev(11, 'round_opened', { round: 'opening', players: ['player_1', 'player_2'] }),
      ev(12, 'speech', { channel_seq: 0, player: 'player_1', message: 'I am the healer.' }),
      ev(13, 'speech', {
        channel_seq: 1,
        player: 'player_2',
        message: 'I am the healer too.',
      }),
      ev(14, 'day_summary', { summary: 'the day in brief' }),
    ];

    const beats = beatsFor(everyone, { xray: false });

    expect(byId(beats, 'day.round-passes')).toHaveLength(0);
  });

  it('a log cut mid-round (live) tells no passes yet', () => {
    const cut = openingRound.slice(0, 5); // round_opened, a pass marker, the speech, its tags

    const beats = beatsFor(cut, { xray: false, live: true });

    expect(byId(beats, 'day.round-passes')).toHaveLength(0);
    expect(byId(beats, 'day.speech')).toHaveLength(1);
  });

  // The server announces a human's round turn as soon as the round opens (the human golden:
  // round_opened, then input_request, then the agents' strategy notes, then the lines). The
  // input_request is not one of ROUND_LINE_EVENTS, so the round closes on it, every seat is
  // told as silent before anyone has spoken, and the speeches that follow are outside the round.
  it('a human in the round does not close the round before its lines arrive (fixed 2026-10-07)', () => {
    const withHuman: DurableGameEvent[] = [
      ev(11, 'round_opened', { round: 'opening', players: SEATS }),
      ev(12, 'input_request', {
        player: 'player_3',
        action_kind: 'discuss',
        candidates: [],
        round: 'opening',
        deadline: null,
      }),
      ev(13, 'speech', {
        channel_seq: 0,
        player: 'player_2',
        message: 'I checked player_4: wolf.',
      }),
      ev(14, 'speech', {
        channel_seq: 1,
        player: 'player_3',
        message: 'I am the healer.',
      }),
      ev(15, 'turn_started', { player: 'player_4' }),
    ];

    const beats = beatsFor(withHuman, { xray: false, me: 'player_3', live: true });

    const passes = byId(beats, 'day.round-passes');
    expect(passes).toHaveLength(1);
    expect(passes[0].subjects).toEqual(['player_1', 'player_4']);
  });
});

describe('the ten-seat pack night', () => {
  it('opens the pack’s plate for the carrier’s kill, and decides the kill as the carrier chooses', () => {
    const night = [
      // a faction beat reaches a pack seat: the deal names its pack
      {
        seq: 2,
        day: 1,
        type: 'role_assigned',
        player: 'player_5',
        role: 'chanteuse',
        pack: ['player_5', 'player_6'],
      },
      {
        seq: 20,
        day: 1,
        type: 'input_request',
        player: 'player_5',
        action_kind: 'carrier_kill',
        candidates: ['player_1', 'player_7'],
        deadline: null,
      },
      {
        seq: 21,
        day: 1,
        type: 'wolf_kill_decided',
        target: 'player_7',
        carrier: 'player_5',
      },
    ] as DurableGameEvent[];
    const beats = beatsFor(night, { xray: false, me: 'player_5', live: true });
    expect(beats.filter((b) => b.id === 'pack.vote')).toHaveLength(1);
    expect(beats.find((b) => b.id === 'pack.decided')).toMatchObject({
      subject: 'player_7',
    });
  });
});

describe('the ten-seat morning (night records, every save, the pick)', () => {
  const p3Log = phase3.events as unknown as DurableGameEvent[];
  const necroLog = necro.events as unknown as DurableGameEvent[];
  const records = (log: DurableGameEvent[]) =>
    log.filter(
      (e): e is Extract<DurableGameEvent, { type: 'night_record' }> =>
        e.type === 'night_record',
    );
  const onlyYou = (beats: SceneBeat[]) => beats.filter((b) => b.id === 'morning.only-you');

  it('gives the X-ray one only-you beat per record, the pack’s kill once a night at its first copy', () => {
    for (const log of [p3Log, necroLog]) {
      const all = records(log);
      const packFirst = new Map<number, number>();
      for (const r of all)
        if (r.actor === 'wolves' && !packFirst.has(r.day)) packFirst.set(r.day, r.seq);
      const expected = all.filter(
        (r) => r.actor !== 'wolves' || packFirst.get(r.day) === r.seq,
      );
      const beats = onlyYou(beatsFor(log, { xray: true }));
      expect(beats.map((b) => [b.seq, b.sees, b.seat, b.aqua])).toEqual(
        expected.map((r) => [r.seq, 'seat', r.player, true]),
      );
      // the subject is the record's target when it is a seat (a held fire, a pick: none)
      expect(beats.map((b) => b.subject)).toEqual(
        expected.map((r) => (r.target?.startsWith('player_') ? r.target : undefined)),
      );
    }
    // the necromancer game's night 1: the pack's record reached both wolves (99, 100)
    const n1 = onlyYou(beatsFor(necroLog, { xray: true })).filter((b) => b.day === 1);
    expect(n1.map((b) => b.seq)).toEqual([97, 98, 99, 101, 102, 103, 104]);
  });

  it('keeps every record out of the public replay', () => {
    expect(onlyYou(beatsFor(p3Log, { xray: false }))).toEqual([]);
  });

  it('gives a seat its own records only, and each wolf the pack’s kill once a night', () => {
    const seer = onlyYou(beatsFor(p3Log, { xray: false, me: 'player_9', live: true }));
    expect(seer.map((b) => [b.seq, b.subject])).toEqual([
      [100, 'player_5'],
      [228, 'player_3'],
      [340, 'player_6'],
    ]);
    // the illusionist: the pack's kill each night, and its own conceal (no seat named)
    const illusionist = onlyYou(
      beatsFor(p3Log, { xray: false, me: 'player_6', live: true }),
    );
    expect(illusionist.map((b) => [b.seq, b.seat, b.subject])).toEqual([
      [99, 'player_6', 'player_7'],
      [226, 'player_6', 'player_3'],
      [227, 'player_6', undefined],
    ]);
    // the chanteuse holds the second copy: the beat is hers, at the night's first copy
    const chanteuse = onlyYou(
      beatsFor(necroLog, { xray: false, me: 'player_10', live: true }),
    );
    expect(chanteuse.filter((b) => b.day === 1).map((b) => [b.seq, b.seat])).toEqual([
      [99, 'player_10'],
      [101, 'player_10'],
    ]);
  });

  it('tells every save a chip at a time, and holds the roll for the pick’s row too', () => {
    const night2 = beatsFor(necroLog, { xray: false }).filter(
      (b) => b.scene === 'morning' && b.day === 2 && b.id !== 'morning.day-begins',
    );
    expect(night2.map((b) => [b.id, b.subject])).toEqual([
      ['morning.shutter-down', undefined],
      ['morning.chip-attacked', 'player_10'],
      ['morning.chip-fell', 'player_10'],
      ['morning.card-down', 'player_10'],
      ['morning.chip-attacked', 'player_1'],
      ['morning.chip-saved', 'player_1'],
      ['morning.roll', undefined],
    ]);
    // a death, a save and the speculator's pick: three rows
    expect(night2.at(-1)?.holdMs).toBe(6000 + 3 * 2000);
  });

  it('lets the pack’s kill record stand for the game master’s note', () => {
    const log = [
      {
        seq: 1,
        day: 1,
        type: 'role_assigned',
        player: 'player_5',
        role: 'chanteuse',
        pack: ['player_5', 'player_6'],
      },
      {
        seq: 2,
        day: 1,
        type: 'wolf_message',
        round: 1,
        wolf: 'game_master',
        message: 'Your kill failed.',
      },
      {
        seq: 3,
        day: 1,
        type: 'night_record',
        player: 'player_5',
        actor: 'wolves',
        action: 'kill',
        target: 'player_7',
        result: 'saved',
        outcome: 'player_7 survived: the healer saved them.',
        seen: [],
      },
    ] as DurableGameEvent[];
    const beats = onlyYou(beatsFor(log, { xray: false, me: 'player_5', live: true }));
    expect(beats.map((b) => [b.seq, b.subject])).toEqual([[3, 'player_7']]);
  });

  it('makes the chips for every entry of `saves`, in order', () => {
    const result = necroLog.find(
      (e) => e.type === 'night_result' && e.day === 2,
    ) as Extract<DurableGameEvent, { type: 'night_result' }>;
    const two = {
      ...result,
      deaths: [],
      pick: null,
      saves: [
        { player: 'player_1', attacker_types: ['wolves'] },
        { player: 'player_3', attacker_types: ['serial_killer'] },
      ],
    } as DurableGameEvent;
    const beats = beatsFor([two], { xray: false });
    expect(beats.map((b) => [b.id, b.subject])).toEqual([
      ['morning.shutter-down', undefined],
      ['morning.chip-attacked', 'player_1'],
      ['morning.chip-saved', 'player_1'],
      ['morning.chip-attacked', 'player_3'],
      ['morning.chip-saved', 'player_3'],
      ['morning.roll', undefined],
    ]);
    expect(beats.at(-1)?.holdMs).toBe(6000 + 2 * 2000);
  });
});
