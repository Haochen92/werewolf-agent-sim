import { describe, expect, it } from 'vitest';
import { foldEvents } from '@/game/foldEvents';
import type { CarriedSummary } from '@/game/types';
import type { DurableGameEvent, LedgerDay, LedgerEntry } from '@/types/contracts';
import { beatsFor } from '../beats/beatsFor';
import type { SceneBeat } from '../beats/types';
import { FIXTURE_EVENTS, PHASE3_GAME, PHASE3_NECRO_GAME } from '../workbench/fixture';
import {
  claimedActionText,
  nightRecords,
  planKind,
  recordMornings,
  recordPage,
  shownMorning,
  summaryClaims,
  type RecordViewer,
} from './record-model';

const xray = beatsFor(FIXTURE_EVENTS, { xray: true });
const pub = beatsFor(FIXTURE_EVENTS, { xray: false });

function at(beats: readonly SceneBeat[], pick: (b: SceneBeat) => boolean) {
  const beat = beats.find(pick)!;
  return { beat, view: foldEvents(FIXTURE_EVENTS.slice(0, beat.end)) };
}

describe('the mornings the Record has reached', () => {
  it('has none before the first summary is read', () => {
    const { view, beat } = at(pub, (b) => b.scene === 'night' && b.day === 1);
    expect(recordMornings(view, beat)).toEqual([]);
  });

  it('opens a morning once its day begins, never one past the stage', () => {
    const { view, beat } = at(pub, (b) => b.id === 'day.speech' && b.day === 3);
    expect(recordMornings(view, beat)).toEqual([2, 3]);
  });

  it('opens it a moment early at the X-ray’s carried summary', () => {
    const { view, beat } = at(
      xray,
      (b) => b.id === 'morning.carried-summary' && b.day === 3,
    );
    // day 4 has not begun in this view: the carried beat alone reaches morning 4
    expect(view.timeline.some((t) => t.day === 4 && t.phase === 'day')).toBe(false);
    expect(recordMornings(view, beat)).toEqual([2, 3, 4]);
  });

  it('never opens the summary of the day the game ended on', () => {
    const view = foldEvents(FIXTURE_EVENTS);
    expect(recordMornings(view, xray.at(-1)!)).toEqual([2, 3, 4]);
  });
});

describe('the morning the Record opens on', () => {
  it('is the latest, unless the viewer paged back since it arrived', () => {
    expect(shownMorning([], null)).toBeNull();
    expect(shownMorning([2, 3], null)).toBe(3);
    expect(shownMorning([2, 3], { morning: 2, latest: 3 })).toBe(2);
    // a new morning arrived: the pick is dropped
    expect(shownMorning([2, 3, 4], { morning: 2, latest: 3 })).toBe(4);
    // the stage stepped back past the latest the pick was made under
    expect(shownMorning([2], { morning: 2, latest: 3 })).toBe(2);
  });
});

const entry = (over: Partial<LedgerEntry>): LedgerEntry => ({
  night: 1,
  action: 'investigate',
  target: 'player_5',
  result: 'wolf',
  said_on_day: 2,
  reported: true,
  earlier: [],
  also: [],
  planned: null,
  reason: '',
  text: '',
  checks: [],
  ...over,
});

describe('one morning’s page', () => {
  const summary: CarriedSummary = {
    accusations: [
      {
        accusers: ['player_6'],
        target: 'player_5',
        reasoning: 'player_6 said he checked player_5.',
        evidenceType: 'concrete_claim',
        defense: '',
        disputedBy: '',
        recordCheck: '',
      },
    ],
    roleClaims: [
      {
        player: 'player_6',
        claimedRole: 'investigator',
        evidence: '',
        retracted: false,
        nightActions: [
          { night: 1, action: 'investigate', target: 'player_5', result: 'wolf' },
        ],
      },
      {
        player: 'player_2',
        claimedRole: 'healer',
        evidence: 'No one can confirm it.',
        retracted: true,
        nightActions: [],
      },
    ],
    blocs: null,
    dynamics: null,
  };
  const view = { days: { 2: { summaryStructured: summary } } } as never;
  const ledger: LedgerDay[] = [
    { day: 2, players: [] },
    {
      day: 3,
      players: [
        {
          player: 'player_6',
          history: 'claimed investigator (day 2)',
          roles: [{ day: 2, role: 'investigator', kind: 'claimed' }],
          checks: [],
          entries: [entry({})],
        },
      ],
    },
  ];

  it('takes the ledger’s claims, checked, and the day before’s accusations', () => {
    const p = recordPage(view, 3, ledger);
    expect([p.morning, p.day, p.checked]).toEqual([3, 2, true]);
    expect(p.players.map((x) => x.player)).toEqual(['player_6']);
    expect(p.accusations).toHaveLength(1);
  });

  it('falls back to the summary’s own claims, unchecked, without a ledger', () => {
    for (const l of [null, [{ day: 3, players: [] }]]) {
      const p = recordPage(view, 3, l);
      expect(p.checked).toBe(false);
      expect(p.players.map((x) => x.player)).toEqual(['player_6', 'player_2']);
    }
    // an empty morning is just empty
    expect(recordPage(view, 2, ledger)).toMatchObject({ players: [], accusations: [] });
  });

  it('reads a summary’s claims in the ledger’s shape: a withdrawal, an old verdict as a note', () => {
    const [six, two] = summaryClaims(summary, 2);
    expect(six.roles).toEqual([{ day: 2, role: 'investigator', kind: 'claimed' }]);
    expect(six.entries[0]).toMatchObject({
      night: 1,
      said_on_day: 2,
      reported: true,
      planned: null,
      checks: [],
      text: 'Night 1: investigated player_5 — wolf',
    });
    expect(two.roles[0].kind).toBe('retracted');
    expect(two.checks).toEqual([{ text: 'No one can confirm it.', fits: null }]);
  });
});

describe('a plan beside a claimed action', () => {
  it('reads as planned, changed, or the whole line when never reported', () => {
    expect(planKind(entry({}))).toBe('none');
    expect(planKind(entry({ planned: 'player_5' }))).toBe('as-planned');
    expect(planKind(entry({ planned: 'player_2' }))).toBe('changed');
    expect(planKind(entry({ reported: false, result: '', planned: 'player_5' }))).toBe(
      'only',
    );
  });
});

describe('a claimed night action in one line', () => {
  it('reads a v4 action in plain words, and a v3 free-text result as written', () => {
    expect(
      claimedActionText({
        night: 1,
        action: 'investigate',
        target: 'player_7',
        result: 'wolf',
      }),
    ).toBe('Night 1: investigated player_7 — wolf');
    expect(
      claimedActionText({
        night: 2,
        action: 'protect',
        target: 'player_1',
        result: 'saved_from_attack',
      }),
    ).toBe('Night 2: protected player_1 — saved them from an attack');
    expect(
      claimedActionText({
        night: 0,
        action: 'shoot',
        target: 'player_4',
        result: 'not_said',
      }),
    ).toBe('Night not stated: shot player_4');
    expect(
      claimedActionText({ night: 1, action: '', target: 'player_7', result: 'is a wolf' }),
    ).toBe('Night 1: player_7 is a wolf');
  });
});

describe('the night records on the Record (ten-seat)', () => {
  const p3 = foldEvents(PHASE3_GAME.events, { mySeat: 'player_9' });

  it('gives a seat its own night, one line in the engine’s words, on the morning after it', () => {
    const p = recordPage(p3, 2, null, { me: 'player_9', xray: false });
    expect(p.nights).toEqual([
      {
        seat: 'player_9',
        night: 1,
        outcome: 'Tonight player_5 was visited by player_3 and player_4.',
        mine: true,
      },
    ]);
    // night 2's watch is the next morning's
    expect(recordPage(p3, 3, null, { me: 'player_9', xray: false }).nights[0].outcome).toBe(
      'Tonight player_3 was visited by player_6 and player_10.',
    );
  });

  it('gives every seat’s with the X-ray, the pack’s kill once, and none to a spectator', () => {
    const all = nightRecords(p3, 2, null, true);
    expect(all.filter((l) => l.seat === 'wolves')).toHaveLength(1);
    expect(all.map((l) => l.seat)).toEqual([
      'player_8',
      'wolves',
      'player_6',
      'player_9',
      'player_10',
      'player_1',
    ]);
    expect(nightRecords(p3, 2, null, false)).toEqual([]);
    // no viewer: a page as before
    expect(recordPage(p3, 2, null).nights).toEqual([]);
  });

  it('keeps a concealed body hidden in the pack’s line; only the illusionist’s own line names it', () => {
    const lines = nightRecords(p3, 2, null, true);
    expect(lines.find((l) => l.seat === 'wolves')?.outcome).toBe(
      'player_3 died. Their role was concealed.',
    );
    expect(lines.find((l) => l.seat === 'player_6')?.outcome).toContain('trailseer');
  });

  it('marks a wolf’s pack line as its own: both wolves hold it, one line', () => {
    const wolf = foldEvents(PHASE3_NECRO_GAME.events, { mySeat: 'player_10' });
    expect(nightRecords(wolf, 1, 'player_10', false)).toEqual([
      {
        seat: 'wolves',
        night: 1,
        outcome: 'player_4 died. They were a sigilist.',
        mine: true,
      },
      {
        seat: 'player_10',
        night: 1,
        outcome: 'player_5 was roleblocked tonight.',
        mine: true,
      },
    ]);
  });
});

describe('the game over’s last page: the final night’s records', () => {
  const last = (events: readonly DurableGameEvent[], seen: RecordViewer) => {
    const beats = beatsFor(events, { xray: seen.xray });
    const view = foldEvents(events, { mySeat: seen.me ?? undefined });
    return {
      view,
      beat: beats.at(-1)!,
      mornings: recordMornings(view, beats.at(-1)!, seen),
    };
  };

  it('adds a page after night 3 when the game ended at its dawn, the night alone (both ten-seat games)', () => {
    for (const events of [PHASE3_GAME.events, PHASE3_NECRO_GAME.events]) {
      const xr = { me: null, xray: true };
      const { view, mornings } = last(events, xr);
      expect(view.over).toBe(true);
      expect(mornings).toEqual([2, 3, 4]);
      const page = recordPage(view, 4, null, xr);
      expect(page).toMatchObject({
        morning: 4,
        day: 3,
        final: true,
        players: [],
        accusations: [],
      });
      expect(page.nights.length).toBeGreaterThan(0);
      expect(page.nights.every((n) => n.night === 3)).toBe(true);
      // the mornings before it keep their summaries
      expect(recordPage(view, 3, null, xr).final).toBeUndefined();
    }
  });

  it('gives a seat its own last night, and a spectator (who holds none) no extra page', () => {
    const seat = { me: 'player_9', xray: false };
    const { view, mornings } = last(PHASE3_GAME.events, seat);
    expect(mornings).toEqual([2, 3, 4]);
    expect(recordPage(view, 4, null, seat).nights).toEqual([
      {
        seat: 'player_9',
        night: 3,
        outcome: 'Tonight player_6 was visited by player_1.',
        mine: true,
      },
    ]);
    expect(last(PHASE3_GAME.events, { me: null, xray: false }).mornings).toEqual([2, 3]);
  });

  it('waits for game over: the night resolved but the game not yet ended has no extra page', () => {
    const events = PHASE3_GAME.events;
    const before = events.slice(
      0,
      events.findIndex((e) => e.type === 'game_over'),
    );
    expect(last(before, { me: null, xray: true }).mornings).toEqual([2, 3]);
  });

  it('adds none for a game that ended at a lynch: its last night is that day’s morning', () => {
    // the ten-seat game cut at day 3's lynch, and ended there
    const events = PHASE3_GAME.events;
    const night3 = events.findIndex(
      (e) => e.type === 'phase_change' && e.phase === 'night' && e.day === 3,
    );
    const ended = [
      ...events.slice(0, night3),
      {
        seq: events[night3].seq,
        day: 3,
        type: 'game_over',
        winner: 'villagers',
        neutral_result: null,
      } as unknown as DurableGameEvent,
    ];
    const xr = { me: null, xray: true };
    const { view, mornings } = last(ended, xr);
    expect(view.over).toBe(true);
    expect(mornings).toEqual([2, 3]);
    expect(recordPage(view, 3, null, xr).final).toBeUndefined();
    expect(recordPage(view, 3, null, xr).nights.every((n) => n.night === 2)).toBe(true);
  });
});
