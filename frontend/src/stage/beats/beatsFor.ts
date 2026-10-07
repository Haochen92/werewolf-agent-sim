/**
 * Cuts a seq-ordered log into scene beats (see `types.ts`). Pure: the same log and options
 * always give the same list, so a replay can seek to any beat and a live game can diff the
 * list as events arrive. Every beat names the prefix of the log it shows (`end`), and the
 * prefixes never shrink, so seeking forward only ever reveals more.
 *
 * Tier is not gated here beyond what the options say: a public beat is always in; a seat or
 * faction beat is in for the seat it concerns, or, when marked `aqua`, for the X-ray; X-ray
 * beats exist only with `xray` on, and never in a live cut. What the log holds is the server's
 * decision.
 */
import type { DurableGameEvent, EventOf } from '@/types/contracts';
import { pageHold, speechPages } from './pages';
import {
  BEAT_LABELS,
  type BeatId,
  type BeatOptions,
  type SceneBeat,
  type SceneId,
} from './types';

// Holds at normal speed (docs/beat_sheet.md §0). Raised to a reading pace on 2026-09-30
// (shutter 3000, card 2600, open 2800, speech ÷ 3 floor 4 s, a room's mark 2000). Raised again
// on 2026-10-01 for a live game at reading pace; music will sit in these holds (shutter, report,
// verdict 3500/3500/3200, card, open 3200, your card 6000, your pack 4000, mark 2500, lid 1500,
// chip 2000, a report row 1500). The replay shares them.
const HOLD = {
  shutter: 6000,
  chip: 2500,
  card: 4000,
  yourCard: 8000,
  yourPack: 6000,
  verdict: 6000,
  open: 4000,
  held: 2000,
  lid: 2500,
  pass: 4000,
  /** A room's last step in the X-ray night: the mark landing, or the hold. */
  mark: 4000,
  /** The morning roll (2026-09-30; after the chips since 2026-10-02): this, and this much more per row read. */
  report: 6000,
  reportRow: 2000,
} as const;

/** The morning roll's hold: a row per death, and one for a seat saved; a quiet night the base. */
function reportHold(e: EventOf<'night_result'>): number {
  return HOLD.report + HOLD.reportRow * (e.deaths.length + (e.save ? 1 : 0));
}
const WORDS_PER_SECOND = 2.4;
const SPEECH_FLOOR_MS = 5000;
const SPEECH_CAP_MS = 15000;

// A pack line or a night spoke is read in a chat, whole: it holds for all its words. A day
// speech is told in the box a page at a time (`pages.ts`), each page holding for its own.

function speechHold(text: string): number {
  const words = text.trim().split(/\s+/).filter(Boolean).length;
  return Math.min(
    SPEECH_CAP_MS,
    Math.max(SPEECH_FLOOR_MS, Math.round((words / WORDS_PER_SECOND) * 1000)),
  );
}

type Draft = Omit<SceneBeat, 'scene' | 'label'>;

/** What a night's actors did, gathered from the events between "night falls" and the result. */
interface Branch {
  actor: string;
  lastSeq: number;
  /** The pack's lines, in order; empty for a single actor. */
  lines: EventOf<'wolf_message'>[];
  /** The mark that lands: the act's target (or the kill decided). */
  target: string | null;
}

function nightBranches(
  events: readonly DurableGameEvent[],
  from: number,
  to: number,
  wolves: ReadonlySet<string>,
): Branch[] {
  const byActor = new Map<string, Branch>();
  const touch = (actor: string, seq: number) => {
    const b = byActor.get(actor) ?? { actor, lastSeq: seq, lines: [], target: null };
    b.lastSeq = Math.max(b.lastSeq, seq);
    byActor.set(actor, b);
    return b;
  };
  for (let i = from; i < to; i++) {
    const e = events[i];
    switch (e.type) {
      case 'night_action':
        touch(e.actor, e.seq).target = e.target;
        break;
      case 'wolf_message':
        if (e.wolf !== 'game_master') touch('pack', e.seq).lines.push(e);
        break;
      case 'wolf_vote':
        touch('pack', e.seq);
        break;
      case 'wolf_kill_decided':
        touch('pack', e.seq).target = e.target;
        break;
      case 'memory_consulted':
      case 'player_reads':
        // A wolf's consult belongs to the pack's branch; anyone else's to their own.
        touch(wolves.has(e.player) ? 'pack' : e.player, e.seq);
        break;
      default:
        break;
    }
  }
  // A seat that weighed its night and chose no one (a consult or reads, no act: the vigilante
  // holding fire) took a decision: its branch is one spoke with no mark. Only the pack needs
  // talk or a kill to be told.
  return [...byActor.values()]
    .filter((b) => b.actor !== 'pack' || b.target !== null || b.lines.length > 0)
    .sort((a, b) => a.lastSeq - b.lastSeq);
}

export function beatsFor(
  events: readonly DurableGameEvent[],
  options: BeatOptions,
): SceneBeat[] {
  const me = options.me ?? null;
  const wolves = new Set<string>();
  for (const e of events) {
    if (e.type === 'role_assigned' && e.pack) {
      wolves.add(e.player);
      for (const w of e.pack) wolves.add(w);
    }
  }
  const isWolf = me !== null && wolves.has(me);
  // The X-ray's night (its hub, a spoke per actor, the whole) is the replay's telling. A game in
  // play keeps the beats it played when game over turns the X-ray on: no X-ray night (the last
  // night is not told again between the viewer's own night and the morning), and no X-ray or
  // "Only seat n" beat before the ending, so a stage still playing the last night's backlog when
  // `game_over` lands shows nothing the X-ray knows before it reaches `over.*` (2026-10-01).
  const xrayCut = options.xray && !options.live;

  const out: SceneBeat[] = [];
  const shows = (b: Draft): boolean => {
    if (b.liveOnly && !options.live) return false;
    switch (b.sees) {
      case 'public':
        return true;
      case 'xray':
        return xrayCut;
      case 'seat':
        return b.seat === me || (xrayCut && b.aqua === true);
      case 'faction':
        return isWolf || (xrayCut && b.aqua === true);
    }
  };
  const push = (b: Draft) => {
    if (!shows(b)) return;
    out.push({ ...b, scene: b.id.split('.')[0] as SceneId, label: BEAT_LABELS[b.id] });
  };
  const pub = (
    id: BeatId,
    e: DurableGameEvent,
    end: number,
    holdMs: number,
    rest: Partial<Draft> = {},
  ) => push({ id, day: e.day, seq: e.seq, end, sees: 'public', holdMs, ...rest });

  // The structured summary of day N plays in Morning N, so it is held until then.
  const summaries = new Map<number, EventOf<'day_summary_structured'>>();
  // Each day's night result: a game that ends at a morning shows that morning's roll again.
  const reports = new Map<number, EventOf<'night_result'>>();
  let nightStart = -1;
  let over = false;

  // The turn on the stand that has not spoken yet. `turn_started` is public, so a turn that
  // ends with no speech is a pass everyone can see; the X-ray's `pass_marker` carries the
  // reason instead, so the derived pass is only cut without it.
  let thinking: EventOf<'turn_started'> | null = null;
  const resolveTurn = (at: number) => {
    if (thinking && !xrayCut) {
      pub('day.pass', thinking, at, HOLD.pass, { subject: thinking.player });
    }
    thinking = null;
  };

  // A round in progress (Phase 2): its players, and who of them has spoken. The lines of a
  // round arrive as plain speech events right after `round_opened`; the first event that is
  // not one of them (or an annotation of one) ends the round, and the players with no speech
  // are told as one beat, "nothing to add". The X-ray plays each `pass_marker` instead.
  let round: { opened: EventOf<'round_opened'>; spoke: Set<string> } | null = null;
  const resolveRound = (at: number) => {
    if (round && !xrayCut) {
      const quiet: string[] = [];
      for (const player of round.opened.players) {
        if (!round.spoke.has(player)) quiet.push(player);
      }
      if (quiet.length > 0) {
        pub('day.round-passes', round.opened, at, HOLD.pass, { subjects: quiet });
      }
    }
    round = null;
  };
  const ROUND_LINE_EVENTS: ReadonlySet<string> = new Set([
    'speech',
    'pass_marker',
    'addressed_targets',
    'firing_reason',
    'strategy_update',
    'player_reads',
    'memory_consulted',
    // a seated human's ask is sent right after round_opened, before any of the round's lines
    'input_request',
  ]);

  for (let i = 0; i < events.length && !over; i++) {
    const e = events[i];
    const next = i + 1;
    if (round && !ROUND_LINE_EVENTS.has(e.type)) resolveRound(i);
    switch (e.type) {
      case 'round_opened':
        resolveTurn(i);
        if (e.round === 'opening') {
          pub('day.opening-prepares', e, next, HOLD.open, { subjects: [...e.players] });
        } else {
          // the moderator's line is the event before this one; the first accused takes the stand
          pub('day.closing-called', e, next, HOLD.open, {
            subject: e.players[0],
            subjects: [...e.players],
          });
        }
        round = { opened: e, spoke: new Set() };
        break;

      case 'turn_started':
        resolveTurn(i);
        thinking = e;
        if (options.live) {
          // Live, the puppet takes the stand thinking until the speech (or the next turn) arrives.
          pub('day.turn-thinking', e, next, HOLD.held, { subject: e.player });
        }
        break;

      case 'game_started':
        pub('deal.table-seated', e, next, HOLD.shutter);
        pub('deal.cards-dealt', e, next, HOLD.shutter);
        break;

      case 'role_assigned':
        push({
          id: 'deal.your-card',
          day: e.day,
          seq: e.seq,
          end: next,
          sees: 'seat',
          seat: e.player,
          subject: e.player,
          holdMs: HOLD.yourCard,
        });
        if (e.pack) {
          push({
            id: 'deal.your-pack',
            day: e.day,
            seq: e.seq,
            end: next,
            sees: 'faction',
            seat: e.player,
            holdMs: HOLD.yourPack,
          });
        }
        break;

      case 'roles_assigned':
        push({
          id: 'deal.face-up',
          day: e.day,
          seq: e.seq,
          end: next,
          sees: 'xray',
          holdMs: HOLD.card,
        });
        break;

      case 'phase_change':
        resolveTurn(i);
        if (e.phase === 'day') {
          if (e.day === 1) {
            pub('deal.day-begins', e, next, HOLD.shutter, {
              chapter: { kind: 'day', n: 1 },
            });
          } else {
            const carried = summaries.get(e.day - 1);
            if (carried) {
              // Everything before "the day begins" is already revealed: the beat is the film's.
              push({
                id: 'morning.carried-summary',
                day: carried.day,
                seq: carried.seq,
                end: i,
                sees: 'xray',
                holdMs: HOLD.verdict,
              });
            }
            pub('morning.day-begins', e, next, HOLD.shutter, {
              chapter: { kind: 'day', n: e.day },
            });
          }
        } else if (e.phase === 'voting') {
          pub('vote.opens', e, next, HOLD.open, { chapter: { kind: 'vote', n: e.day } });
        } else if (e.phase === 'night') {
          nightStart = next;
          pub(xrayCut ? 'rnight.hub' : 'night.hub', e, next, HOLD.shutter, {
            chapter: { kind: 'night', n: e.day },
          });
        }
        break;

      case 'day_summary_structured':
        summaries.set(e.day, e);
        break;

      case 'speech': {
        if (thinking?.player === e.player) thinking = null;
        if (round) round.spoke.add(e.player);
        const pages = speechPages(e.message);
        pages.forEach((page, index) =>
          pub('day.speech', e, next, pageHold(page), {
            subject: e.player,
            ...(pages.length > 1 ? { page: { index, count: pages.length } } : {}),
          }),
        );
        break;
      }

      case 'pass_marker':
        push({
          id: 'day.pass',
          day: e.day,
          seq: e.seq,
          end: next,
          sees: 'xray',
          subject: e.player,
          holdMs: HOLD.pass,
        });
        break;

      case 'input_request': {
        const id: BeatId =
          e.action_kind === 'discuss'
            ? 'day.your-turn'
            : e.action_kind === 'vote'
              ? 'vote.your-ballot'
              : e.action_kind === 'wolf_discuss'
                ? 'pack.your-line'
                : e.action_kind === 'wolf_vote'
                  ? 'pack.vote'
                  : 'room.opens';
        push({
          id,
          day: e.day,
          seq: e.seq,
          end: next,
          sees: 'seat',
          seat: e.player,
          holdMs: 0,
          liveOnly: true,
        });
        break;
      }

      case 'vote_cast': {
        // Released as one batch at the tally: the drop is one beat, then a chip per ballot.
        let j = i;
        while (j < events.length && events[j].type === 'vote_cast') j++;
        pub('vote.ballots-drop', e, j, HOLD.chip);
        pub('vote.closes', e, j, HOLD.lid);
        pub('vote.count-begins', e, j, HOLD.held);
        for (let k = 1; k <= j - i; k++) {
          pub('vote.chip-counted', e, j, HOLD.chip, { ordinal: k });
        }
        i = j - 1;
        break;
      }

      case 'lynch_result':
        if (e.outcome === 'no_vote') break; // no vote scene on a day nobody voted
        pub('vote.result', e, next, HOLD.verdict, { subject: e.player ?? undefined });
        pub('vote.table-down', e, next, HOLD.shutter);
        if (e.outcome === 'lynched' && e.player) {
          const who = { subject: e.player };
          pub('lynch.stand-returns', e, next, HOLD.shutter, who);
          pub('lynch.named', e, next, HOLD.held, who);
          pub('lynch.drop', e, next, HOLD.held, who);
          pub('lynch.card-up', e, next, HOLD.card, who);
          pub('lynch.truth', e, next, HOLD.card, who);
          // A lynch that ends the game has no night after it: game_over comes before any phase change.
          const after = events
            .slice(next)
            .find((x) => x.type === 'phase_change' || x.type === 'game_over');
          pub('lynch.card-to-wing', e, next, HOLD.shutter, {
            ...who,
            ...(after?.type === 'game_over' ? { endsGame: true } : {}),
          });
        }
        break;

      case 'wolf_message':
        if (e.wolf === 'game_master') {
          // The server's note that the kill failed: private to the pack, arrives in the morning.
          push({
            id: 'morning.only-you',
            day: e.day,
            seq: e.seq,
            end: next,
            sees: 'faction',
            holdMs: HOLD.card,
            aqua: true,
          });
        } else if (!xrayCut) {
          push({
            id: 'pack.line',
            day: e.day,
            seq: e.seq,
            end: next,
            sees: 'faction',
            subject: e.wolf,
            holdMs: speechHold(e.message),
          });
        }
        break;

      case 'wolf_kill_decided':
        if (!xrayCut) {
          push({
            id: 'pack.decided',
            day: e.day,
            seq: e.seq,
            end: next,
            sees: 'faction',
            subject: e.target,
            holdMs: HOLD.held,
          });
        }
        break;

      case 'night_result': {
        if (xrayCut && nightStart >= 0) {
          const branches = nightBranches(events, nightStart, i, wolves);
          branches.forEach((b, rank) => {
            const held = !b.target && b.lines.length === 0;
            const steps = b.lines.length + (b.target || held ? 1 : 0);
            b.lines.forEach((line, step) => {
              push({
                id: 'rnight.spoke',
                day: e.day,
                seq: line.seq,
                end: i,
                sees: 'xray',
                subject: b.actor,
                holdMs: speechHold(line.message),
                spoke: { actor: b.actor, rank, step, steps },
              });
            });
            if (b.target || held) {
              push({
                id: 'rnight.spoke',
                day: e.day,
                seq: b.lastSeq,
                end: i,
                sees: 'xray',
                // the mark's target; a hold's is the seat that held
                subject: b.target ?? b.actor,
                holdMs: HOLD.mark,
                spoke: { actor: b.actor, rank, step: steps - 1, steps },
              });
            }
          });
          push({
            id: 'rnight.whole',
            day: e.day,
            seq: e.seq,
            end: i,
            sees: 'xray',
            holdMs: HOLD.shutter,
          });
        }
        nightStart = -1;
        reports.set(e.day, e);
        pub('morning.shutter-down', e, next, HOLD.shutter, {
          chapter: { kind: 'morning', n: e.day },
        });
        for (const d of e.deaths) {
          const who = { subject: d.player };
          pub('morning.chip-attacked', e, next, HOLD.chip, who);
          pub('morning.chip-fell', e, next, HOLD.chip, who);
          pub('morning.card-down', e, next, HOLD.card, who);
        }
        if (e.save) {
          pub('morning.chip-attacked', e, next, HOLD.chip, { subject: e.save.player });
          pub('morning.chip-saved', e, next, HOLD.card, { subject: e.save.player });
        }
        // the roll with the names comes after the chips have told it (owner, 2026-10-02: on
        // the notice first it read as a spoiler), held for its rows
        if (e.deaths.length || e.save) pub('morning.roll', e, next, reportHold(e));
        else pub('morning.quiet', e, next, HOLD.shutter);
        break;
      }

      case 'investigation_result':
      case 'vigilante_confirmation':
        push({
          id: 'morning.only-you',
          day: e.day,
          seq: e.seq,
          end: next,
          sees: 'seat',
          seat: e.player,
          subject: e.target,
          holdMs: HOLD.card,
          aqua: true,
        });
        break;

      case 'game_over': {
        over = true;
        const report = reports.get(e.day);
        pub('over.where-it-ended', e, next, report ? reportHold(report) : HOLD.held, {
          chapter: { kind: 'over', n: 0 },
        });
        pub('over.winners-hour', e, next, HOLD.shutter);
        pub('over.verdict', e, next, HOLD.verdict);
        pub('over.winners-stand', e, next, HOLD.shutter);
        pub('over.truth', e, next, HOLD.card);
        const taught = events.findIndex((x, k) => k > i && x.type === 'memory_extracted');
        if (taught !== -1) pub('over.epilogue', events[taught], taught + 1, 0);
        pub('over.curtain', e, events.length, 0);
        break;
      }

      default:
        break;
    }
  }
  // a log cut mid-round (live): the round is still open, so nothing is told as a pass yet
  return out;
}

/** The beats that carry a chapter mark, in order: the seek bar's marks. */
export function chapterMarks(
  beats: readonly SceneBeat[],
): { index: number; beat: SceneBeat }[] {
  return beats.flatMap((beat, index) => (beat.chapter ? [{ index, beat }] : []));
}
