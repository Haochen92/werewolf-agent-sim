/**
 * The case file's docket: what the X-ray's pane holds at a beat with no seat in focus (the
 * file's own pages, per seat, are case-file.ts). Worked out from the folded view alone, so the
 * docket can be drawn at any beat, seeking or playing, like the rest of the stage.
 *
 * - the count: what each voter weighed before its ballot;
 * - the lynch's card: "Who had them right", each voter's read of the voted-out seat against
 *   the truth, and the seat's own last note;
 * - a morning: the brief the agents carry into the next day, in its typed form;
 * - the night whole: what each actor did;
 * - the deal face up; at the end the case closed ("the deal, and how each seat went"), and
 *   the winners' last notes at their stand.
 *
 * The epilogue has no docket: the ledger comes down over the whole stage instead. The reads a
 * turn was made from are also on the wing (`turnReads`), where a tap opens the read card.
 */
import type { CarriedSummary, GameView, SummaryNightAction } from '@/game/types';
import type { MemoryConsulted, PlayerReads } from '@/types/contracts';
import type { SceneBeat } from '../beats/types';
import { nightBranchesOf } from '../scenes/replay-night';
import { fateOf, knownRole, winnersOf } from '../scenes/game-over';
import { factionOf } from '../roles';

export type Verdict = 'follow' | 'override' | 'not_relevant';

export interface FilmLesson {
  /** No. 1–3, in the order the agent was handed them. */
  n: number;
  situation: string;
  action: string;
  verdict: Verdict | null;
  why: string | null;
  /** The record's structured situation (case-file.ts `Dimensions`); null for a legacy record. */
  dimensions: { [key: string]: unknown } | null;
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

export type DocketModel =
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
  /** A beat with nothing of its own on file; `title` names the sheet where "Nothing on file"
   *  would mislead (the night hub is "The night"). */
  | { kind: 'empty'; label: string; title?: string };

/**
 * What the no-seat sheet is called, by what it holds (owner, 2026-09-30: "the docket" was
 * nobody's word): its name on the cover, its tab and the phone's chooser.
 */
const CLAIM_VERB: Record<string, string> = {
  investigate: 'investigated',
  protect: 'protected',
  shoot: 'shot',
  kill: 'attacked',
};
const CLAIM_SAYS: Record<string, string> = {
  saved_from_attack: 'saved them from an attack',
  no_attack: 'no attack came',
  died: 'they died',
  survived: 'they survived',
  not_a_wolf: 'not a wolf',
};

/**
 * A claimed night action as the brief sets it: "Night 1: investigated player_7 — wolf". A v3
 * summary's free-text result reads as it was written; a result the player never gave is left off.
 */
export function claimedActionText(n: SummaryNightAction): string {
  const night = n.night ? `Night ${n.night}` : 'Night not stated';
  if (!n.action) return `${night}: ${n.target} ${n.result}`.trim();
  const verb = CLAIM_VERB[n.action] ?? n.action;
  const result =
    n.result && n.result !== 'not_said'
      ? (CLAIM_SAYS[n.result] ?? n.result.replace(/_/g, ' '))
      : '';
  return `${night}: ${verb} ${n.target}${result ? ` — ${result}` : ''}`;
}

export function docketTitle(model: DocketModel): string {
  switch (model.kind) {
    case 'night':
      return 'The night';
    case 'vote':
      return 'The vote';
    case 'lynch':
      return 'The lynch';
    case 'brief':
      return `Day ${model.day}’s brief`;
    case 'deal':
      return model.truth ? 'The case, closed' : 'The deal';
    case 'notes':
      return 'The winners’ notes';
    case 'empty':
      return model.title ?? 'Nothing on file';
  }
}

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
      dimensions: l.dimensions ?? null,
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
 * The wing wears them as verdigris edges; a tap opens the read card.
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

/**
 * The seats a turn's reads say something new about: a read the speaker's previous
 * `player_reads` (any phase) did not hold, or held with another guess or another certainty.
 * The wing flashes these once. On a seat's first reads, every one is new.
 */
export function freshReads(view: GameView, reads: PlayerReads | null): Set<string> {
  if (!reads) return new Set();
  const all = view.xray.agents[reads.player]?.reads ?? [];
  const before = all.filter((r) => r.seq < reads.seq).at(-1);
  const was = new Map(before?.reads.map((r) => [r.player, r]) ?? []);
  return new Set(
    reads.reads
      .filter((r) => {
        const w = was.get(r.player);
        return !w || w.suspected_role !== r.suspected_role || w.confidence !== r.confidence;
      })
      .map((r) => r.player),
  );
}

/** The last note a seat wrote in a window of the log. */
function lastNote(view: GameView, seat: string, from: number, to: number): FilmNote | null {
  const n = (view.xray.agents[seat]?.strategy ?? [])
    .filter((s) => s.seq > from && s.seq < to)
    .at(-1);
  return n ? { seq: n.seq, text: n.text } : null;
}

const VOTE_DOCKET: readonly SceneBeat['id'][] = [
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
 * The docket for a beat with no seat in focus (a turn and a night spoke open a seat's file
 * instead, case-file.ts `fileFocus`). Null at the epilogue.
 */
export function docketFor(view: GameView, beat: SceneBeat): DocketModel | null {
  const day = beat.day;
  const phaseAt = (d: number, p: string) =>
    view.timeline.find((t) => t.day === d && t.phase === p)?.seq ?? null;

  if (VOTE_DOCKET.includes(beat.id)) {
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

  if (beat.id === 'rnight.whole')
    return {
      kind: 'night',
      day,
      rows: nightBranchesOf(view, day).map((b) => ({
        actor: b.actor,
        seats: b.seats,
        role: b.role,
        target: b.target,
      })),
    };

  if (
    beat.id === 'deal.face-up' ||
    beat.id === 'over.truth' ||
    // the curtain is where a live game rests: the case, closed
    beat.id === 'over.curtain'
  ) {
    const truth = beat.id !== 'deal.face-up';
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

  if (beat.id === 'over.winners-stand')
    return {
      kind: 'notes',
      rows: winnersOf(view).map((s) => ({
        seat: s,
        role: knownRole(view, s),
        note: lastNote(view, s, -Infinity, Infinity),
      })),
    };

  if (beat.id === 'over.epilogue') return null;
  // the night's hub holds nothing yet, but the sheet is the night's (2026-09-30)
  if (beat.id === 'rnight.hub')
    return { kind: 'empty', label: beat.label, title: 'The night' };
  return { kind: 'empty', label: beat.label };
}
