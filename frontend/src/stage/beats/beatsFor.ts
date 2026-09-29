/**
 * Cuts a seq-ordered log into scene beats (see `types.ts`). Pure: the same log and options
 * always give the same list, so a replay can seek to any beat and a live game can diff the
 * list as events arrive. Every beat names the prefix of the log it shows (`end`), and the
 * prefixes never shrink, so seeking forward only ever reveals more.
 *
 * Tier is not gated here beyond what the options say: a public beat is always in; a seat or
 * faction beat is in for the seat it concerns, or, when marked `aqua`, for the X-ray; X-ray
 * beats exist only with `xray` on. What the log holds is the server's decision.
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

// Holds at normal speed (docs/beat_sheet.md §0).
const HOLD = {
  shutter: 3000,
  chip: 2000,
  card: 2600,
  yourCard: 6000,
  yourPack: 4000,
  verdict: 3200,
  open: 2800,
  held: 2000,
  lid: 1500,
  pass: 4000,
} as const;
const WORDS_PER_SECOND = 3;
const SPEECH_FLOOR_MS = 4000;
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
  // A branch with nothing to show (a consult but no act) is not a spoke.
  return [...byActor.values()]
    .filter((b) => b.target !== null || b.lines.length > 0)
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

  const out: SceneBeat[] = [];
  const shows = (b: Draft): boolean => {
    if (b.liveOnly && !options.live) return false;
    switch (b.sees) {
      case 'public':
        return true;
      case 'xray':
        return options.xray;
      case 'seat':
        return b.seat === me || (options.xray && b.aqua === true);
      case 'faction':
        return isWolf || (options.xray && b.aqua === true);
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
  let nightStart = -1;
  let over = false;

  // The turn on the stand that has not spoken yet. `turn_started` is public, so a turn that
  // ends with no speech is a pass everyone can see; the X-ray's `pass_marker` carries the
  // reason instead, so the derived pass is only cut without it.
  let thinking: EventOf<'turn_started'> | null = null;
  const resolveTurn = (at: number) => {
    if (thinking && !options.xray) {
      pub('day.pass', thinking, at, HOLD.pass, { subject: thinking.player });
    }
    thinking = null;
  };

  for (let i = 0; i < events.length && !over; i++) {
    const e = events[i];
    const next = i + 1;
    switch (e.type) {
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
          pub(options.xray ? 'rnight.hub' : 'night.hub', e, next, HOLD.shutter, {
            chapter: { kind: 'night', n: e.day },
          });
        }
        break;

      case 'day_summary_structured':
        summaries.set(e.day, e);
        break;

      case 'speech': {
        if (thinking?.player === e.player) thinking = null;
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
        } else if (!options.xray) {
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
        if (!options.xray) {
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
        if (options.xray && nightStart >= 0) {
          const branches = nightBranches(events, nightStart, i, wolves);
          branches.forEach((b, rank) => {
            const steps = b.lines.length + (b.target ? 1 : 0);
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
            if (b.target) {
              push({
                id: 'rnight.spoke',
                day: e.day,
                seq: b.lastSeq,
                end: i,
                sees: 'xray',
                subject: b.target,
                holdMs: HOLD.chip,
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
        if (e.deaths.length === 0 && !e.save) pub('morning.quiet', e, next, HOLD.shutter);
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
        pub('over.where-it-ended', e, next, HOLD.held, { chapter: { kind: 'over', n: 0 } });
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
  return out;
}

/** The beats that carry a chapter mark, in order: the seek bar's marks. */
export function chapterMarks(
  beats: readonly SceneBeat[],
): { index: number; beat: SceneBeat }[] {
  return beats.flatMap((beat, index) => (beat.chapter ? [{ index, beat }] : []));
}
