/**
 * `foldEvents` — the heart of the app. One pure function folding the durable event log into
 * a `GameView`, serving all three surfaces (build_plan §4):
 *
 *   replay → fetch the whole log, fold once, the scrubber selects a day page
 *   live   → SSE events folded incrementally into the same shape
 *   R7     → the post-game observer backlog folds through the same path, no special case
 *
 * Two rules it holds to:
 *
 * - **It renders what arrived and never gates.** Tier filtering is the server's job; there
 *   is nothing to hide because withheld events simply never appear. `xray.available` reports
 *   whether observer-tier data has *arrived* — it is not a permission check.
 * - **It does not know about liveness.** Whether an event just streamed in or is being
 *   replayed from history is the store's business (ux_journeys §0: the store flags
 *   live-arrived seqs, the beat layer keys off that). Keeping the reducer ignorant is what
 *   makes refresh-mid-game and replay-scrub share one code path.
 *
 * Updates are immutable along the touched path — a live fold must change object identity
 * for the day it wrote to, or memoised components subscribed to that day never re-render.
 */
import type { DurableGameEvent } from '@/types/contracts';
import type {
  ChannelSlot,
  DayView,
  DeathCause,
  DeathRecord,
  FoldOptions,
  GameView,
  NightView,
  SlotAnnotations,
} from './types';

// --- empties ---------------------------------------------------------------

export function emptyDay(day: number): DayView {
  return {
    day,
    slots: [],
    annotations: {},
    turnMarkers: [],
    vote: {
      ballots: [],
      outcome: null,
      lynched: null,
      lynchedRole: null,
      voteCounts: {},
      noLynchStreak: 0,
    },
    night: null,
    summary: null,
    phases: [],
  };
}

function emptyNight(day: number): NightView {
  return {
    day,
    wolfChannel: [],
    wolfVotes: [],
    wolfKill: null,
    actions: [],
    deaths: [],
    save: null,
    resolved: false,
  };
}

export function emptyGameView(options: FoldOptions = {}): GameView {
  return {
    seats: [],
    castRoleCounts: {},
    day: 1,
    phase: 'day',
    timeline: [],
    winner: null,
    winnerSeq: null,
    alive: [],
    dead: [],
    packRoster: [],
    days: {},
    thinking: null,
    me: {
      seat: options.mySeat ?? null,
      role: null,
      roleSeq: null,
      pending: null,
      privateResults: [],
      alive: true,
    },
    xray: { available: false, roles: {}, agents: {} },
    lastSeq: 0,
    droppedEventTypes: [],
  };
}

// --- immutable path helpers ------------------------------------------------

function withDay(view: GameView, day: number, fn: (d: DayView) => DayView): GameView {
  const current = view.days[day] ?? emptyDay(day);
  return { ...view, days: { ...view.days, [day]: fn(current) } };
}

function withNight(view: GameView, day: number, fn: (n: NightView) => NightView): GameView {
  return withDay(view, day, (d) => ({ ...d, night: fn(d.night ?? emptyNight(day)) }));
}

const emptyAnnotations = (): SlotAnnotations => ({ firing: null, addressed: [] });

function withAnnotation(
  view: GameView,
  day: number,
  channelSeq: number,
  fn: (a: SlotAnnotations) => SlotAnnotations,
): GameView {
  return withDay(view, day, (d) => ({
    ...d,
    annotations: {
      ...d.annotations,
      [channelSeq]: fn(d.annotations[channelSeq] ?? emptyAnnotations()),
    },
  }));
}

/**
 * Append a transcript slot, resolving any pending `turn_started` from the same player into
 * it. `turn_started` always precedes its slot on the wire; a marker left unresolved when
 * the next one fires is recorded as unresolved rather than dropped.
 */
function pushSlot(
  view: GameView,
  day: number,
  build: (turnStartedSeq: number | null) => ChannelSlot,
): GameView {
  const pending = view.thinking;
  const slot = build(pending && pending.day === day ? pending.seq : null);
  const resolves =
    pending !== null &&
    pending.day === day &&
    'player' in slot &&
    slot.player === pending.player;

  const next = withDay(view, day, (d) => ({
    ...d,
    slots: [...d.slots, slot],
    turnMarkers: resolves
      ? [
          ...d.turnMarkers,
          {
            seq: pending.seq,
            day,
            player: pending.player,
            resolvedChannelSeq: slot.channelSeq,
          },
        ]
      : d.turnMarkers,
  }));

  return resolves ? { ...next, thinking: null } : next;
}

function recordDeaths(view: GameView, deaths: DeathRecord[]): GameView {
  if (deaths.length === 0) return view;
  const known = new Set(view.dead.map((d) => d.player));
  const fresh = deaths.filter((d) => !known.has(d.player));
  if (fresh.length === 0) return view;
  const dead = [...view.dead, ...fresh];
  const deadNames = new Set(dead.map((d) => d.player));
  return {
    ...view,
    dead,
    // Belt and braces: roster_update is authoritative, but a death is knowable before it.
    alive: view.alive.filter((p) => !deadNames.has(p)),
    me: {
      ...view.me,
      alive: view.me.seat === null ? true : !deadNames.has(view.me.seat),
    },
  };
}

const OBSERVER_TIER_EVENTS = new Set([
  'roles_assigned',
  'pass_marker',
  'firing_reason',
  'addressed_targets',
  'strategy_update',
  'night_action',
  'day_summary_structured',
]);

// --- the fold --------------------------------------------------------------

export function foldEvent(
  view: GameView,
  event: DurableGameEvent,
  options: FoldOptions = {},
): GameView {
  const mySeat = options.mySeat ?? view.me.seat;

  let next: GameView = {
    ...view,
    lastSeq: Math.max(view.lastSeq, event.seq),
    xray: OBSERVER_TIER_EVENTS.has(event.type)
      ? { ...view.xray, available: true }
      : view.xray,
  };

  switch (event.type) {
    case 'game_started': {
      return {
        ...next,
        seats: event.seats,
        castRoleCounts: event.cast_role_counts,
        alive: event.seats,
      };
    }

    case 'role_assigned': {
      // A REPLAY carries every seat's role_assigned, so this never decides who "me" is —
      // it files the card by player and `me.role` is derived from the caller's seat hint.
      const card = {
        role: event.role,
        pack: event.pack ?? null,
        bullets: event.bullets ?? null,
      };
      // Deliberately NOT filed into `xray.roles`: that map is observer-tier truth
      // (`roles_assigned`) and nothing else. A live seat receives exactly one
      // `role_assigned` — its own — and mixing that in would leave `xray.roles`
      // half-populated with a single entry that isn't observer knowledge at all. Your
      // own role lives on `me.role`; the view reads that for your own badge.
      if (event.player === mySeat) {
        next = { ...next, me: { ...next.me, role: card, roleSeq: event.seq } };
        if (event.pack) next = { ...next, packRoster: event.pack };
      }
      return next;
    }

    case 'roles_assigned': {
      return {
        ...next,
        xray: { ...next.xray, roles: { ...next.xray.roles, ...event.roles } },
      };
    }

    case 'phase_change': {
      next = {
        ...next,
        day: Math.max(next.day, event.day),
        phase: event.phase,
        timeline: [
          ...next.timeline,
          { day: event.day, phase: event.phase, seq: event.seq },
        ],
      };
      return withDay(next, event.day, (d) =>
        d.phases.includes(event.phase) ? d : { ...d, phases: [...d.phases, event.phase] },
      );
    }

    case 'game_over': {
      return { ...next, winner: event.winner, winnerSeq: event.seq };
    }

    case 'turn_started': {
      // An unresolved predecessor is filed as such rather than silently dropped.
      const stale = next.thinking;
      if (stale) {
        next = withDay(next, stale.day, (d) => ({
          ...d,
          turnMarkers: [
            ...d.turnMarkers,
            {
              seq: stale.seq,
              day: stale.day,
              player: stale.player,
              resolvedChannelSeq: null,
            },
          ],
        }));
      }
      return {
        ...next,
        thinking: { seq: event.seq, day: event.day, player: event.player },
      };
    }

    case 'speech': {
      return pushSlot(next, event.day, (turnStartedSeq) => ({
        kind: 'speech',
        day: event.day,
        channelSeq: event.channel_seq,
        seq: event.seq,
        player: event.player,
        message: event.message,
        turnStartedSeq,
      }));
    }

    case 'pass_marker': {
      return pushSlot(next, event.day, (turnStartedSeq) => ({
        kind: 'pass',
        day: event.day,
        channelSeq: event.channel_seq,
        seq: event.seq,
        player: event.player,
        passReason: event.pass_reason ?? null,
        gated: event.gated,
        gatedCandidate: event.gated_candidate ?? null,
        turnStartedSeq,
      }));
    }

    case 'gm_message': {
      return pushSlot(next, event.day, (turnStartedSeq) => ({
        kind: 'gm',
        day: event.day,
        channelSeq: event.channel_seq,
        seq: event.seq,
        text: event.text,
        turnStartedSeq,
      }));
    }

    case 'firing_reason': {
      return withAnnotation(next, event.day, event.about_channel_seq, (a) => ({
        ...a,
        firing: { tier: event.tier, owes: event.owes ?? [] },
      }));
    }

    case 'addressed_targets': {
      return withAnnotation(next, event.day, event.about_channel_seq, (a) => ({
        ...a,
        addressed: [...a.addressed, ...event.targets],
      }));
    }

    case 'strategy_update': {
      const agent = next.xray.agents[event.player] ?? { strategy: [] };
      return {
        ...next,
        xray: {
          ...next.xray,
          agents: {
            ...next.xray.agents,
            [event.player]: {
              strategy: [
                ...agent.strategy,
                { seq: event.seq, day: event.day, text: event.strategy },
              ],
            },
          },
        },
      };
    }

    case 'input_request': {
      return {
        ...next,
        me: {
          ...next.me,
          pending: {
            seq: event.seq,
            day: event.day,
            actionKind: event.action_kind,
            candidates: event.candidates ?? [],
            deadline: event.deadline ?? null,
          },
        },
      };
    }

    case 'day_summary': {
      return withDay(next, event.day, (d) => ({ ...d, summary: event.summary }));
    }

    case 'vote_cast': {
      return withDay(next, event.day, (d) => ({
        ...d,
        vote: {
          ...d.vote,
          ballots: [
            ...d.vote.ballots,
            { seq: event.seq, voter: event.voter, votee: event.votee },
          ],
        },
      }));
    }

    case 'lynch_result': {
      next = withDay(next, event.day, (d) => ({
        ...d,
        vote: {
          ...d.vote,
          outcome: event.outcome,
          lynched: event.player ?? null,
          lynchedRole: event.role ?? null,
          voteCounts: event.vote_counts,
          noLynchStreak: event.no_lynch_streak,
        },
      }));
      if (event.outcome === 'lynched' && event.player) {
        next = recordDeaths(next, [
          {
            player: event.player,
            role: event.role ?? null,
            day: event.day,
            seq: event.seq,
            causes: ['lynch'],
          },
        ]);
      }
      return next;
    }

    case 'roster_update': {
      const alive = new Set(event.surviving_players);
      return {
        ...next,
        alive: event.surviving_players,
        me: {
          ...next.me,
          alive: next.me.seat === null ? true : alive.has(next.me.seat),
        },
      };
    }

    case 'pack_roster_update': {
      return { ...next, packRoster: event.surviving_wolves };
    }

    case 'night_action': {
      return withNight(next, event.day, (n) => ({
        ...n,
        actions: [
          ...n.actions,
          { seq: event.seq, actor: event.actor, role: event.role, target: event.target },
        ],
      }));
    }

    case 'wolf_message': {
      return withNight(next, event.day, (n) => ({
        ...n,
        wolfChannel: [
          ...n.wolfChannel,
          { seq: event.seq, round: event.round, wolf: event.wolf, message: event.message },
        ],
      }));
    }

    case 'wolf_vote': {
      return withNight(next, event.day, (n) => ({
        ...n,
        wolfVotes: [
          ...n.wolfVotes,
          { seq: event.seq, wolf: event.wolf, votee: event.votee },
        ],
      }));
    }

    case 'wolf_kill_decided': {
      return withNight(next, event.day, (n) => ({ ...n, wolfKill: event.target }));
    }

    case 'night_result': {
      next = withNight(next, event.day, (n) => ({
        ...n,
        deaths: event.deaths,
        save: event.save ?? null,
        resolved: true,
      }));
      return recordDeaths(
        next,
        event.deaths.map((d) => ({
          player: d.player,
          role: d.role,
          day: event.day,
          seq: event.seq,
          causes: d.attacker_types as DeathCause[],
        })),
      );
    }

    case 'investigation_result': {
      return {
        ...next,
        me: {
          ...next.me,
          privateResults: [
            ...next.me.privateResults,
            {
              kind: 'investigation',
              seq: event.seq,
              day: event.day,
              target: event.target,
              role: event.role,
            },
          ],
        },
      };
    }

    case 'vigilante_confirmation': {
      return {
        ...next,
        me: {
          ...next.me,
          privateResults: [
            ...next.me.privateResults,
            {
              kind: 'vigilante_confirmation',
              seq: event.seq,
              day: event.day,
              target: event.target,
            },
          ],
        },
      };
    }

    case 'bullets_remaining': {
      next = {
        ...next,
        me: {
          ...next.me,
          privateResults: [
            ...next.me.privateResults,
            { kind: 'bullets', seq: event.seq, day: event.day, count: event.count },
          ],
        },
      };
      // The role chip shows the live count (D19), so the card tracks it too.
      if (event.player === mySeat && next.me.role) {
        next = {
          ...next,
          me: { ...next.me, role: { ...next.me.role, bullets: event.count } },
        };
      }
      return next;
    }

    default: {
      // `day_summary_structured` lands here by design: the schema exists but the engine
      // never emits it (build_plan §4), confirmed by zero occurrences in the seed. Recorded
      // rather than ignored so a wire surprise is visible instead of silent.
      const unknown = event as { type: string };
      return next.droppedEventTypes.includes(unknown.type)
        ? next
        : { ...next, droppedEventTypes: [...next.droppedEventTypes, unknown.type] };
    }
  }
}

/** Fold a whole log. Replay calls this once; the store calls `foldEvent` per arrival. */
export function foldEvents(
  events: readonly DurableGameEvent[],
  options: FoldOptions = {},
): GameView {
  return events.reduce<GameView>(
    (view, event) => foldEvent(view, event, options),
    emptyGameView(options),
  );
}
