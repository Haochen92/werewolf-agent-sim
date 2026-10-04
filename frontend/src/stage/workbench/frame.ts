/**
 * Everything the workbench needs to draw one URL: the scene's beats for this viewer, the one
 * the URL points at, the log folded up to it, and the presentation. A pure function of the
 * URL (and the fixture), so what the workbench shows and what a test checks cannot drift.
 */
import type { Character } from '@/assets/manifest';
import { foldEvents } from '@/game/foldEvents';
import type { GameView } from '@/game/types';
import type { DurableGameEvent, LedgerDay } from '@/types/contracts';
import { beatsFor } from '../beats/beatsFor';
import { DIM_FACETS, parseSituation } from '../film/case-file';
import type { SceneBeat, SceneId } from '../beats/types';
import type { Presentation, RoomInput, TurnInput } from '../scenes/types';
import { FIXTURE_CAST, FIXTURE_EVENTS, LEDGER_GAME } from './fixture';
import { SYNTHETIC, SYNTHETIC_AFTER, sceneBeats } from './registry';
import { synthesiseAll, type AnySituation } from './synthetic';
import type { WorkbenchQuery } from './url';

const MEMORY_EVENTS = new Set(['memory_consulted', 'memory_extracted']);

/** The workbench's one game, for the notebook a seated viewer keeps (notebook.ts). */
export const WORKBENCH_GAME = 'workbench';

export interface WorkbenchFrame {
  beats: SceneBeat[];
  /** The URL's beat, clamped into the scene's range. */
  index: number;
  beat: SceneBeat | null;
  view: GameView | null;
  me: string | null;
  presentation: Presentation;
  /** A live-only scene: the situation this frame was drawn from, and its prompt's live side. */
  situation?: AnySituation;
  turn?: TurnInput;
  /** The platform's waiting room. */
  room?: RoomInput;
  /**
   * The whole log folded, for the case file: whether memory was on, and what the game taught
   * (see `SlotInput.ahead`). A replay has the whole log, so the workbench hands it all over.
   */
  ahead?: GameView | null;
  /** The claim ledger for the case file's Record (`SlotInput.ledger`); null: none. */
  ledger: readonly LedgerDay[] | null;
}

export function workbenchFrame(
  scene: SceneId,
  q: WorkbenchQuery,
  events: readonly DurableGameEvent[] = q.game ? LEDGER_GAME.events : FIXTURE_EVENTS,
  cast: readonly Character[] = q.game ? LEDGER_GAME.cast : FIXTURE_CAST,
): WorkbenchFrame {
  // the Record's ledger: the second game's own, the v4 redraw's synthetic one, or none
  const ledger = q.noLedger
    ? null
    : q.game
      ? LEDGER_GAME.ledger
      : q.summaryV4
        ? V4_LEDGER
        : null;
  // a memory-off game: the same log without what memory adds
  if (q.memoryOff) events = events.filter((e) => !MEMORY_EVENTS.has(e.type));
  else if (q.memoryFields) events = withFields(events);
  if (q.summaryV4) events = withSummaryV4(events);
  const situations = SYNTHETIC[scene];
  if (situations && !SYNTHETIC_AFTER.has(scene))
    return { ...syntheticFrame(situations, q, events, cast), ledger };
  const me = q.viewer.kind === 'seat' ? q.viewer.seat : null;
  const xray = q.viewer.kind === 'xray';
  const beats = sceneBeats(beatsFor(events, { xray, me, live: q.live }), scene);
  // a live-only prompt among the fixture's beats: its situations follow them in the stepper
  if (situations && q.beat >= beats.length)
    return {
      ...syntheticFrame(
        situations,
        { ...q, beat: q.beat - beats.length },
        events,
        cast,
        beats,
      ),
      ledger,
    };
  const index = Math.max(0, Math.min(q.beat, beats.length - 1));
  const beat = beats[index] ?? null;
  const view = beat ? foldEvents(events.slice(0, beat.end), { mySeat: me }) : null;
  const ahead = beat && xray ? foldEvents(events, { mySeat: me }) : null;
  return {
    beats: situations
      ? [...beats, ...synthesiseAll(situations, events).map((f) => f.beat)]
      : beats,
    index,
    beat,
    view,
    me,
    ahead,
    ledger,
    presentation: {
      xray,
      slot: q.slot === 'none' ? null : q.slot,
      motion: q.motion,
      hud: q.hud,
      animate: q.animate,
      cast,
      // a live cut keeps a seated viewer's notebook, as a live game would
      game: q.live ? WORKBENCH_GAME : undefined,
    },
  };
}

/** The beat's anchor, in one line: "day.speech · seq 163 · public → player_2 · 11250 ms". */
export function anchorLine(b: SceneBeat): string {
  const tier = b.seat ? `${b.sees}@${b.seat}` : b.sees;
  const about = b.subject ? ` → ${b.subject}` : '';
  const nth = b.ordinal ? ` #${b.ordinal}` : '';
  return `${b.id} · seq ${b.seq} · ${tier}${about}${nth} · ${b.holdMs} ms`;
}

/**
 * A live-only scene's frame: `?beat=N` picks the Nth situation, the seat comes from the
 * situation (the viewer control does not apply), and the X-ray is off (a prompt is seat tier).
 * `before` are the fixture's own beats that come first in the stepper, if any.
 */
function syntheticFrame(
  situations: readonly AnySituation[],
  q: WorkbenchQuery,
  events: readonly DurableGameEvent[],
  cast: readonly Character[],
  before: readonly SceneBeat[] = [],
): Omit<WorkbenchFrame, 'ledger'> {
  const frames = synthesiseAll(situations, events);
  const index = Math.max(0, Math.min(q.beat, frames.length - 1));
  const f = frames[index];
  return {
    beats: [...before, ...frames.map((x) => x.beat)],
    index: before.length + index,
    beat: f?.beat ?? null,
    view: f?.view ?? null,
    me: f?.me ?? null,
    presentation: {
      xray: false,
      slot: q.slot === 'none' ? null : q.slot,
      motion: q.motion,
      hud: q.hud,
      animate: q.animate,
      cast,
      // a live-only prompt is a seated player's: their notebook is kept
      game: WORKBENCH_GAME,
    },
    situation: situations[index],
    turn: f?.turn,
    room: f?.room,
  };
}

/**
 * The fixture's memory records with a small synthetic `dimensions` each (the fixture predates
 * them, server 18ebf3e): the composed situation split back into its fields, and made-up but
 * plausible classifications and tags, so the case file's field-reading path can be drawn.
 */
/** Synthetic claims for the v4 redraw, by day: the fixture's summaries recorded none. */
const V4_CLAIMS: Record<number, Record<string, unknown>[]> = {
  3: [
    {
      player: 'player_5',
      claimed_role: 'investigator',
      kind: 'claimed',
      night_actions: [
        { night: 2, action: 'investigate', target: 'player_3', result: 'wolf' },
      ],
    },
  ],
  4: [
    {
      player: 'player_1',
      claimed_role: 'healer',
      kind: 'claimed',
      night_actions: [
        { night: 3, action: 'protect', target: 'player_8', result: 'no_attack' },
      ],
    },
    { player: 'player_9', claimed_role: 'vigilante', kind: 'retracted', night_actions: [] },
  ],
};

/** A synthetic day-3 accusation for the v4 redraw (the fixture's day 3 had none), in both forms. */
const V4_ACCUSATION = {
  accusers: ['player_7'],
  target: 'player_2',
  reasoning: 'player_7 argued that player_2 survived a night attack the others did not.',
  evidence_type: 'concrete_claim',
  defense: 'player_2 said no one attacked them.',
  disputed_by: 'player_5 said surviving a night proves nothing.',
  record_check: 'The game master never announced an attack on player_2.',
};
const V4_ACCUSATION_TEXT =
  'player_7 → player_2: player_7 argued that player_2 survived a night attack the others did ' +
  'not. (evidence type: concrete_claim) Defense: player_2 said no one attacked them. Disputed: ' +
  'player_5 said surviving a night proves nothing. Against the record: The game master never ' +
  'announced an attack on player_2.';

type LedgerLine = LedgerDay['players'][number]['entries'][number];
const check = (text: string, fits: boolean | null) => ({ text, fits });
const line = (over: Partial<LedgerLine>): LedgerLine => ({
  night: 1,
  action: 'investigate',
  target: '',
  result: 'not_said',
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
/** Morning 3's ledger: the claims of day 2. */
const V4_MORNING_3: LedgerDay['players'] = [
  {
    player: 'player_9',
    history: 'claimed healer (day 2)',
    roles: [{ day: 2, role: 'healer', kind: 'claimed' }],
    checks: [],
    entries: [
      line({
        action: 'protect',
        target: 'player_1',
        result: 'saved_from_attack',
        planned: 'player_1',
        text: 'Night 1: protected player_1, says they saved them from an attack (planned on day 1).',
        checks: [
          check('Record: player_1 was attacked and saved by the healer that night.', true),
        ],
      }),
    ],
  },
  {
    player: 'player_1',
    history: 'claimed villager (day 2)',
    roles: [{ day: 2, role: 'villager', kind: 'claimed' }],
    checks: [],
    entries: [],
  },
];

/**
 * A synthetic claim ledger for the v4 redraw (`summary=v4`), with a line of every kind the
 * Record draws: a check that agrees, one that does not, a plain note; an action changed, two
 * targets named for one night, a plan kept, a plan changed with its reason, a plan never
 * reported on; a claim withdrawn, and a role that changed. Built to fit the fixture's deaths
 * (seat 3, a wolf, and seat 4 on night 2; seat 6 voted out on day 3; seat 5 on night 3), not
 * from played claims.
 */
const V4_LEDGER: readonly LedgerDay[] = [
  { day: 2, players: [] },
  { day: 3, players: V4_MORNING_3 },
  {
    day: 4,
    players: [
      {
        ...V4_MORNING_3[0],
        history: 'claimed healer (day 2), retracted healer (day 3)',
        roles: [
          { day: 2, role: 'healer', kind: 'claimed' },
          { day: 3, role: 'healer', kind: 'retracted' },
        ],
      },
      {
        player: 'player_1',
        history: 'claimed villager (day 2), then claimed healer (day 3)',
        roles: [
          { day: 2, role: 'villager', kind: 'claimed' },
          { day: 3, role: 'healer', kind: 'claimed' },
        ],
        checks: [],
        entries: [
          line({
            night: 3,
            action: 'protect',
            target: 'player_5',
            result: '',
            said_on_day: 3,
            reported: false,
            planned: 'player_5',
            text: 'Night 3: on day 3 said they planned to protect player_5.',
            checks: [check('Record: player_5 died that night.', null)],
          }),
        ],
      },
      {
        player: 'player_5',
        history: 'claimed investigator (day 3)',
        roles: [{ day: 3, role: 'investigator', kind: 'claimed' }],
        checks: [
          check(
            'Record: revealed as villager when they died on night 3, not investigator.',
            false,
          ),
        ],
        entries: [
          line({
            night: 2,
            target: 'player_3',
            result: 'wolf',
            said_on_day: 3,
            earlier: ['Night 2: investigated player_8'],
            text:
              'Night 2: investigated player_3, result: wolf (changed on day 3; earlier: ' +
              'Night 2: investigated player_8).',
            checks: [check('Record: player_3 was revealed as wolf, as claimed.', true)],
          }),
        ],
      },
      {
        player: 'player_7',
        history: 'claimed vigilante (day 3)',
        roles: [{ day: 3, role: 'vigilante', kind: 'claimed' }],
        checks: [],
        entries: [
          line({
            night: 2,
            action: 'shoot',
            target: 'player_3',
            result: 'died',
            said_on_day: 3,
            also: ['Night 2: shot player_2'],
            planned: 'player_8',
            reason: 'player_3 pushed the abstain hardest',
            text:
              'Night 2: shot player_3, says they died (on day 3 also named: Night 2: shot ' +
              'player_2). On day 2 said they planned to shoot player_8; reason given on day 3: ' +
              'player_3 pushed the abstain hardest.',
            checks: [
              check('Rules: one shot a night.', false),
              check('Record: player_3 died that night.', true),
            ],
          }),
        ],
      },
    ],
  },
];

/**
 * The fixture's day summaries in the v4 shape (`summary=v4`): the synthetic claims above, a
 * synthetic day-3 accusation with its dispute and record check, and no blocs or mood, in both
 * the typed summary and its text. Other days keep their own accusations.
 */
function withSummaryV4(events: readonly DurableGameEvent[]): DurableGameEvent[] {
  // the text as the summarizer's serializer writes it (summary_agent._serialize_day_summary)
  const claimLine: Record<number, string> = {
    3: 'player_5 claimed investigator — Night 2: investigated player_3, result: wolf',
    4:
      'player_1 claimed healer — Night 3: protected player_8, says there was no attack; ' +
      'player_9 retracted vigilante',
  };
  return events.map((e) => {
    if (e.type === 'day_summary') {
      const first =
        e.day === 3
          ? `Key accusations and defenses: ${V4_ACCUSATION_TEXT}`
          : e.summary.split('\n')[0];
      return { ...e, summary: `${first}\nRole claims: ${claimLine[e.day] ?? 'None.'}` };
    }
    if (e.type !== 'day_summary_structured') return e;
    const data = e.data as Record<string, unknown>;
    const accusations =
      e.day === 3
        ? [V4_ACCUSATION]
        : ((data.accusations as Record<string, unknown>[]) ?? []);
    return { ...e, data: { accusations, role_claims: V4_CLAIMS[e.day] ?? [] } };
  });
}

function withFields(events: readonly DurableGameEvent[]): DurableGameEvent[] {
  const dims = (situation: string, i: number) => {
    const s = parseSituation(situation);
    const out: Record<string, unknown> = { situation: s.lead };
    for (const f of s.facets) {
      const dim = DIM_FACETS.find(([, key]) => key === f.key)?.[0];
      if (dim) out[dim] = f.value;
    }
    out.info_landscape_class = /rich/i.test(String(out.information_landscape ?? ''))
      ? 'info_rich'
      : 'info_starved';
    out.exposure_class = i % 2 ? 'exposed' : 'safe';
    out.consensus_direction = [
      'aligns_with_my_read',
      'opposes_my_read',
      'no_clear_direction',
    ][i % 3];
    out.direction = ['defensive', 'offensive', 'positional'][i % 3];
    out.honesty = i % 2 ? 'deceptive' : 'honest';
    out.players_alive = 9 - (i % 4);
    return out;
  };
  return events.map((e) =>
    e.type === 'memory_consulted'
      ? {
          ...e,
          lessons: e.lessons.map((l, i) => ({ ...l, dimensions: dims(l.situation, i) })),
        }
      : e.type === 'memory_extracted'
        ? {
            ...e,
            observations: e.observations.map((o, i) => ({
              ...o,
              dimensions: dims(o.situation, i),
            })),
            strategy_points: e.strategy_points.map((l, i) => ({
              ...l,
              dimensions: dims(l.situation, i),
            })),
          }
        : e,
  );
}
