/**
 * What the X-ray film holds at a beat: *this beat, inside* (handoff §2 "The film"; beat sheet
 * §2, §3 row 6, §4, §8 row 8, §9, §10). Worked out from the folded view alone, so the film
 * can be drawn at any beat, seeking or playing, like the rest of the stage.
 *
 * - a turn: the speaker's note (written just after the turn, so it is read from the view a
 *   little ahead), and the lessons it weighed before speaking with its verdict on each;
 * - the count: what each voter weighed before its ballot;
 * - the lynch's card: "Who had them right", each voter's read of the voted-out seat against
 *   the truth, and the seat's own last note;
 * - a morning: the brief the agents carry into the next day, in its typed form;
 * - a night spoke: the actor's lessons and note (the pack's two notes); the night whole;
 * - the deal face up, the truth at the end ("the deal, and how it went"), the winners' notes.
 *
 * The epilogue has no slot film: the ledger comes down over the whole stage instead.
 * Reads are not in the film; they are on the wing (`turnReads`).
 */
import type { CarriedSummary, GameView } from '@/game/types';
import type { MemoryConsulted, PlayerReads } from '@/types/contracts';
import type { SceneBeat } from '../beats/types';
import { nightBranchesOf } from '../scenes/replay-night';
import { fateOf, knownRole, winnersOf } from '../scenes/game-over';
import { factionOf } from '../roles';

export type Verdict = 'follow' | 'override' | 'not_relevant';

export interface FilmLesson {
  /** L1–L3, in the order the agent was handed them. */
  n: number;
  situation: string;
  action: string;
  verdict: Verdict | null;
  why: string | null;
}

export interface FilmNote {
  seq: number;
  text: string;
}

export type ReadMark = 'role' | 'side' | 'none';

/** One seat as another read it: the guess, how sure, why. */
export type SeatRead = PlayerReads['reads'][number];

export interface HadThemRight {
  voter: string;
  /** The voter's own role, if the viewer holds it. */
  role: string | null;
  suspected: string | null;
  confidence: string | null;
  why: string | null;
  mark: ReadMark;
}

export type FilmModel =
  | {
      kind: 'inside';
      /** At a day turn, or an actor's act at night. */
      when: 'turn' | 'night';
      seat: string;
      role: string | null;
      note: FilmNote | null;
      lessons: FilmLesson[];
      consultSeq: number | null;
      readsSeq: number | null;
      /** The lessons were weighed at the seat's first turn that day and carried over. */
      carried: boolean;
    }
  | {
      kind: 'pack';
      seats: string[];
      notes: { seat: string; note: FilmNote | null }[];
      lines: number;
    }
  | {
      kind: 'night';
      day: number;
      rows: { actor: string; seats: string[]; role: string; target: string | null }[];
    }
  | {
      kind: 'vote';
      day: number;
      rows: {
        voter: string;
        role: string | null;
        votee: string;
        verdicts: (Verdict | null)[];
      }[];
    }
  | {
      kind: 'lynch';
      seat: string;
      role: string;
      rows: HadThemRight[];
      note: FilmNote | null;
    }
  | { kind: 'brief'; day: number; summary: CarriedSummary | null }
  | {
      kind: 'deal';
      /** The end's truth: each seat's fate too. */
      truth: boolean;
      rows: { seat: string; role: string | null; fate: string | null }[];
    }
  | { kind: 'notes'; rows: { seat: string; role: string | null; note: FilmNote | null }[] }
  | { kind: 'empty'; label: string };

/** The lessons of one consult, with the agent's verdict on each. */
export function lessonsOf(consult: MemoryConsulted | undefined): FilmLesson[] {
  if (!consult) return [];
  return consult.lessons.map((l, i) => {
    const v = consult.verdicts.find((x) => x.strategy_index === l.index);
    return {
      n: i + 1,
      situation: l.situation,
      action: l.action,
      verdict: v?.verdict ?? null,
      why: v?.why ?? null,
    };
  });
}

/**
 * How near a read came to the truth: the role itself (●), the right side (◐: town, or not
 * town), or nothing or wrong (○). Bench 65's rule: the wolves and the killer are one side
 * here, the side the village is hunting.
 */
export function readMark(suspected: string | null | undefined, truth: string): ReadMark {
  if (!suspected || suspected === 'unclear') return 'none';
  if (suspected === truth) return 'role';
  const town = (r: string) => factionOf(r) === 'villagers';
  return factionOf(suspected) && town(suspected) === town(truth) ? 'side' : 'none';
}

export const MARK: Record<ReadMark, string> = { role: '●', side: '◐', none: '○' };

/**
 * Each voter's read of the voted-out seat, from the last `player_reads` it made that day
 * before the ballots were released (the read it voted on).
 */
export function whoHadThemRight(view: GameView, day: number, seat: string, truth: string) {
  const ballots = view.days[day]?.vote.ballots ?? [];
  const cut = ballots[0]?.seq ?? Infinity;
  return ballots
    .filter((b) => b.voter !== seat)
    .map((b): HadThemRight => {
      const last = (view.xray.agents[b.voter]?.reads ?? [])
        .filter((r) => r.day === day && r.seq < cut)
        .at(-1);
      const read = last?.reads.find((r) => r.player === seat) ?? null;
      return {
        voter: b.voter,
        role: view.xray.roles[b.voter] ?? null,
        suspected: read?.suspected_role ?? null,
        confidence: read?.confidence ?? null,
        why: read?.why ?? null,
        mark: readMark(read?.suspected_role, truth),
      };
    });
}

/** The day's last consult/reads of one kind before `seq`: what a decision was made from. */
function lastBefore<T extends MemoryConsulted | PlayerReads>(
  list: readonly T[] | undefined,
  day: number,
  phase: T['action_phase'],
  seq: number,
  after = -Infinity,
): T | undefined {
  return (list ?? [])
    .filter(
      (e) => e.day === day && e.action_phase === phase && e.seq < seq && e.seq > after,
    )
    .at(-1);
}

/**
 * The reads a speaker's turn was made from: its last `player_reads` that day before the line.
 * The wing wears them as blue edges; a tap opens the read card.
 */
export function turnReads(
  view: GameView,
  beat: Pick<SceneBeat, 'id' | 'day' | 'seq' | 'subject'>,
) {
  if ((beat.id !== 'day.speech' && beat.id !== 'day.pass') || !beat.subject) return null;
  return (
    lastBefore(
      view.xray.agents[beat.subject]?.reads,
      beat.day,
      'day_discussion',
      beat.seq,
    ) ?? null
  );
}

/** The note a turn wrote: after the line, before the next slot of the day. */
function noteAfter(
  view: GameView,
  seat: string,
  day: number,
  seq: number,
): FilmNote | null {
  const next =
    view.days[day]?.slots.find((s) => s.seq > seq)?.seq ??
    view.timeline.find((t) => t.seq > seq)?.seq ??
    Infinity;
  const n = (view.xray.agents[seat]?.strategy ?? []).find(
    (s) => s.day === day && s.seq > seq && s.seq < next,
  );
  return n ? { seq: n.seq, text: n.text } : null;
}

/** The last note a seat wrote in a window of the log. */
function lastNote(view: GameView, seat: string, from: number, to: number): FilmNote | null {
  const n = (view.xray.agents[seat]?.strategy ?? [])
    .filter((s) => s.seq > from && s.seq < to)
    .at(-1);
  return n ? { seq: n.seq, text: n.text } : null;
}

const VOTE_FILM: readonly SceneBeat['id'][] = [
  'vote.ballots-drop',
  'vote.closes',
  'vote.count-begins',
  'vote.chip-counted',
  'vote.result',
  'vote.table-down',
  'lynch.stand-returns',
  'lynch.named',
  'lynch.drop',
];

/**
 * The film for a beat. `ahead` is the view a little past the beat (see `SlotInput.ahead`);
 * without it the note written after a turn is simply not there yet. Null at the epilogue.
 */
export function filmFor(
  view: GameView,
  beat: SceneBeat,
  ahead?: GameView | null,
): FilmModel | null {
  const day = beat.day;
  const later = ahead ?? view;
  const phaseAt = (d: number, p: string) =>
    view.timeline.find((t) => t.day === d && t.phase === p)?.seq ?? null;

  if ((beat.id === 'day.speech' || beat.id === 'day.pass') && beat.subject) {
    const seat = beat.subject;
    const agent = view.xray.agents[seat];
    const consult = lastBefore(agent?.consulted, day, 'day_discussion', beat.seq);
    const reads = lastBefore(agent?.reads, day, 'day_discussion', beat.seq);
    // an earlier turn of this seat since the consult: the lessons were carried over from it
    const carried =
      !!consult &&
      (view.days[day]?.slots ?? []).some(
        (s) =>
          s.kind !== 'gm' && s.player === seat && s.seq > consult.seq && s.seq < beat.seq,
      );
    return {
      kind: 'inside',
      when: 'turn',
      seat,
      role: view.xray.roles[seat] ?? null,
      note: noteAfter(later, seat, day, beat.seq),
      lessons: lessonsOf(consult),
      consultSeq: consult?.seq ?? null,
      readsSeq: reads?.seq ?? null,
      carried,
    };
  }

  if (VOTE_FILM.includes(beat.id)) {
    const ballots = view.days[day]?.vote.ballots ?? [];
    if (!ballots.length) return { kind: 'empty', label: beat.label };
    const opened = phaseAt(day, 'voting') ?? -Infinity;
    return {
      kind: 'vote',
      day,
      rows: [...ballots]
        .sort((a, b) => a.voter.localeCompare(b.voter, 'en', { numeric: true }))
        .map((b) => {
          const c = lastBefore(
            view.xray.agents[b.voter]?.consulted,
            day,
            'day_vote',
            Infinity,
            opened,
          );
          return {
            voter: b.voter,
            role: view.xray.roles[b.voter] ?? null,
            votee: b.votee,
            verdicts: lessonsOf(c).map((l) => l.verdict),
          };
        }),
    };
  }

  if (beat.id.startsWith('lynch.')) {
    const vote = view.days[day]?.vote;
    const seat = beat.subject ?? vote?.lynched ?? null;
    const role = vote?.lynchedRole ?? null;
    if (!seat || !role) return { kind: 'empty', label: beat.label };
    return {
      kind: 'lynch',
      seat,
      role,
      rows: whoHadThemRight(view, day, seat, role),
      // the note it went into the vote with, as the reads are the ones the voters voted on
      note: lastNote(view, seat, -Infinity, vote?.ballots[0]?.seq ?? beat.seq),
    };
  }

  if (beat.id === 'morning.carried-summary')
    return { kind: 'brief', day, summary: view.days[day]?.summaryStructured ?? null };

  if (beat.id === 'rnight.spoke' || beat.id === 'rnight.whole') {
    const branches = nightBranchesOf(view, day);
    const start = phaseAt(day, 'night') ?? -Infinity;
    // the night ends where the next day begins, which only the view ahead may hold yet
    const end =
      later.timeline.find((t) => t.day === day + 1 && t.phase === 'day')?.seq ??
      later.winnerSeq ??
      Infinity;
    const cur = beat.spoke ? branches[beat.spoke.rank] : undefined;
    if (beat.id === 'rnight.whole' || !cur)
      return {
        kind: 'night',
        day,
        rows: branches.map((b) => ({
          actor: b.actor,
          seats: b.seats,
          role: b.role,
          target: b.target,
        })),
      };
    if (cur.actor === 'pack')
      return {
        kind: 'pack',
        seats: cur.seats,
        notes: cur.seats.map((s) => ({ seat: s, note: lastNote(later, s, start, end) })),
        lines: cur.lines,
      };
    const consult = lastBefore(
      view.xray.agents[cur.actor]?.consulted,
      day,
      'night_action',
      Infinity,
      start,
    );
    return {
      kind: 'inside',
      when: 'night',
      seat: cur.actor,
      role: cur.role,
      note: lastNote(later, cur.actor, start, end),
      lessons: lessonsOf(consult),
      consultSeq: consult?.seq ?? null,
      readsSeq:
        lastBefore(view.xray.agents[cur.actor]?.reads, day, 'night_action', Infinity, start)
          ?.seq ?? null,
      carried: false,
    };
  }

  if (beat.id === 'deal.face-up' || beat.id === 'over.truth') {
    const truth = beat.id === 'over.truth';
    return {
      kind: 'deal',
      truth,
      rows: view.seats.map((s) => ({
        seat: s,
        role: knownRole(view, s),
        fate: truth ? fateOf(view, s) : null,
      })),
    };
  }

  if (beat.id === 'over.winners-stand' || beat.id === 'over.curtain')
    return {
      kind: 'notes',
      rows: winnersOf(view).map((s) => ({
        seat: s,
        role: knownRole(view, s),
        note: lastNote(view, s, -Infinity, Infinity),
      })),
    };

  if (beat.id === 'over.epilogue') return null;
  return { kind: 'empty', label: beat.label };
}
