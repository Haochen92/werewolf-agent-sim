/**
 * What the transcript drawer lists, read out of the folded view (handoff §2 "The transcript";
 * beat sheet §11 "The drawer"). The drawer is history, so it is built from what the view
 * holds up to the beat on stage: in the replay it stops at the beat for free.
 *
 * Three tiers, each shown only to whoever has it:
 *
 * - public, for everyone: the speeches; the game master's lines verbatim (they are the record,
 *   so the lynch and the night that follow one only lend it their sigils, and nothing is said
 *   twice); the votes as one line per day at the count, voter → votee pairs, because the vote
 *   is blind and the ballots arrive as one batch; the day's brief in its morning (the summary
 *   is public, owner 2026-09-29); the ending;
 * - private: a seated human's own results as "Only you" lines (what happened to their act and
 *   when; only the investigator's reading names a role); a wolf's pack chat and the kill; with
 *   the X-ray, everyone's private results as "Only seat 4";
 * - X-ray, in verdigris: the passes with their reason and held-back draft, the night acts,
 *   and the pack's talk.
 *
 * The chapters (Day N · discussion, the vote, Night N, Morning N, Game over) run down it as
 * rules, the seek bar's marks read downwards; a rule with nothing under it after the filters
 * is dropped. `firing_reason` and `addressed_targets` are deferred by decision.
 */
import type { GameView, GmSlot, PassSlot, PrivateResult } from '@/game/types';
import type { PassReason } from '@/types/contracts';
import type { SceneBeat } from '../beats/types';
import { seatNumber, seatify } from '../roles';

export type LineTier = 'public' | 'private' | 'xray';

/** The drawer's three filters (handoff §2): a day tab, one seat, and which tiers show. */
export interface DrawerFilters {
  day: number | 'all';
  /** One seat's lines, or every seat's (null). */
  seat: string | null;
  show: Record<LineTier, boolean>;
}

export const DEFAULT_FILTERS: DrawerFilters = {
  day: 'all',
  seat: null,
  show: { public: true, private: true, xray: true },
};

interface LineBase {
  /** Stable across beats, so the lit line and the brief's open state survive a step. */
  key: string;
  seq: number;
  day: number;
  tier: LineTier;
  /** The seats the line is about, for the seat filter. */
  seats: string[];
  /** Other seqs the line stands for (the ballots of the vote line, the lynch a GM line tells). */
  covers?: number[];
}

/** "You checked seat 1 [chip]: a villager." as three parts, so the chip can sit in the words. */
export interface OnlyText {
  lead: string;
  chip?: string;
  rest: string;
}

/** Which chapter a rule opens: the drawer draws each as its own kind of heading. */
export type Chapter = 'day' | 'vote' | 'night' | 'morning' | 'over';

export type DrawerLine =
  | (LineBase & { kind: 'rule'; text: string; chapter: Chapter })
  | (LineBase & { kind: 'speech'; player: string; text: string })
  | (LineBase & {
      kind: 'pass';
      player: string;
      reason: PassReason | null;
      draft: string | null;
    })
  | (LineBase & {
      kind: 'gm';
      text: string;
      /** The roles of the lynch or the night deaths this line tells: their sigils, lent. */
      roles: string[];
      about: 'vote' | 'dawn' | 'over' | null;
    })
  | (LineBase & { kind: 'votes'; pairs: { voter: string; votee: string }[] })
  | (LineBase & { kind: 'act'; actor: string; role: string; target: string })
  | (LineBase & { kind: 'pack'; wolf: string; round: number; text: string; mine: boolean })
  | (LineBase & { kind: 'kill'; target: string; mine: boolean })
  | (LineBase & {
      kind: 'only';
      /** The seat's own line (dashed, amber) rather than someone else's (the X-ray's verdigris). */
      mine: boolean;
      /** "Only you", "Only seat 4", "Only the pack". */
      who: string;
      /** "Night 1", "the investigator's reading". */
      about: string;
      text: OnlyText | string;
    })
  | (LineBase & { kind: 'brief'; text: string })
  | (LineBase & { kind: 'over'; winner: string });

export type LineKind = DrawerLine['kind'];

/** What each act does, as a line says it (bench 74 `VERB`). */
export const ACT_VERB: Record<string, string> = {
  healer: 'protects',
  investigator: 'checks',
  vigilante: 'shoots',
  serial_killer: 'marks',
  wolf: 'chooses',
};

const ARTICLE: Record<string, string> = {
  villager: 'a villager',
  healer: 'the healer',
  investigator: 'the investigator',
  vigilante: 'the vigilante',
  wolf: 'a wolf',
  serial_killer: 'the serial killer',
};

/** The ending, as the drawer's last line says it when no game-master line says it first. */
export const WINNER_TEXT: Record<string, string> = {
  villagers: 'The village has won.',
  wolves: 'The wolves have won.',
  serial_killer: 'The serial killer has won.',
};

const GAME_OVER = /^\s*game over/i;
/** The vote's beats from the ballots dropping to the last chip: the votes line waits. */
const COUNT_BEATS: ReadonlySet<string> = new Set([
  'vote.ballots-drop',
  'vote.closes',
  'vote.count-begins',
  'vote.chip-counted',
]);
/**
 * The morning's beats from the shutter to the last card: the game master's dawn line names
 * who died and what they were, which the stage tells a chip at a time, so the line waits for
 * the roll (owner, 2026-10-02: on the drawer at the shutter it read as a spoiler).
 */
const REPORT_BEATS: ReadonlySet<string> = new Set([
  'morning.shutter-down',
  'morning.chip-attacked',
  'morning.chip-fell',
  'morning.card-down',
  'morning.chip-saved',
]);
/**
 * The beats between the result and the card being read: the game master's vote line names the
 * lynched seat's role, which the stage tells only at `lynch.truth`, so on a day with a lynch
 * the line waits for that (same ruling as the votes line).
 */
const UNTIL_TRUTH: ReadonlySet<string> = new Set([
  'vote.result',
  'vote.table-down',
  'lynch.stand-returns',
  'lynch.named',
  'lynch.drop',
  'lynch.card-up',
]);

export interface LineOptions {
  me: string | null;
  xray: boolean;
  /**
   * The beat on stage: the carried summary's beat shows its brief a moment before the day; an
   * X-ray night's spoke shows that night only as far as the spokes have got (see `spokeCut`).
   */
  beat?: (Pick<SceneBeat, 'id' | 'day'> & Partial<Pick<SceneBeat, 'seq' | 'spoke'>>) | null;
}

/** Every line this viewer's drawer holds at this view, in the log's order, rules included. */
export function drawerLines(view: GameView, o: LineOptions): DrawerLine[] {
  const { me, xray } = o;
  const out: { at: number; line: DrawerLine }[] = [];
  const push = (at: number, line: DrawerLine) => out.push({ at, line });
  const wolfMe = !!me && (view.me.role?.role === 'wolf' || !!view.me.role?.pack);

  const phaseSeq = (day: number, phase: string) =>
    view.timeline.find((t) => t.day === day && t.phase === phase)?.seq ?? null;

  for (const t of view.timeline) {
    const text =
      t.phase === 'day'
        ? `Day ${t.day} · discussion`
        : t.phase === 'voting'
          ? `Day ${t.day} · the vote`
          : t.phase === 'night'
            ? `Night ${t.day}`
            : null;
    if (text)
      push(t.seq, {
        kind: 'rule',
        key: `rule-${t.phase}-${t.day}`,
        seq: t.seq,
        day: t.day,
        tier: 'public',
        seats: [],
        text,
        chapter: t.phase === 'day' ? 'day' : t.phase === 'voting' ? 'vote' : 'night',
      });
  }

  const overGm = overLine(view);
  const days = Object.values(view.days).sort((a, b) => a.day - b.day);
  for (const d of days) {
    const nightStart = phaseSeq(d.day, 'night') ?? Infinity;
    const openedAt = phaseSeq(d.day, 'voting') ?? phaseSeq(d.day, 'day') ?? -Infinity;
    const gms = d.slots.filter((s): s is GmSlot => s.kind === 'gm');
    const dawn = d.night ? gms.find((s) => s.seq > nightStart) : undefined;
    const vote = gms
      .filter((s) => s.seq < nightStart && s.seq > openedAt && s !== overGm)
      .at(-1);
    const lynch = view.dead.find((x) => x.day === d.day && x.causes.includes('lynch'));
    const nightDead = view.dead.filter(
      (x) => x.day === d.day && !x.causes.includes('lynch'),
    );

    for (const s of d.slots) {
      if (s.kind === 'speech')
        push(s.seq, {
          kind: 'speech',
          key: `say-${s.seq}`,
          seq: s.seq,
          day: d.day,
          tier: 'public',
          seats: [s.player],
          player: s.player,
          text: s.message,
        });
      else if (s.kind === 'pass') {
        if (xray) push(s.seq, passLine(s, d.day));
      } else {
        const about =
          s === overGm ? 'over' : s === dawn ? 'dawn' : s === vote ? 'vote' : null;
        if (
          about === 'vote' &&
          lynch &&
          o.beat?.day === d.day &&
          UNTIL_TRUTH.has(o.beat.id)
        )
          continue;
        if (about === 'dawn' && o.beat?.day === d.day && REPORT_BEATS.has(o.beat.id))
          continue;
        const roles =
          about === 'vote'
            ? lynch?.role
              ? [lynch.role]
              : []
            : about === 'dawn'
              ? (d.night?.deaths ?? []).map((x) => x.role)
              : [];
        const seats =
          about === 'vote'
            ? lynch
              ? [lynch.player]
              : []
            : about === 'dawn'
              ? [
                  ...(d.night?.deaths ?? []).map((x) => x.player),
                  ...(d.night?.save ? [d.night.save.player] : []),
                ]
              : [];
        const covers =
          about === 'vote'
            ? lynch
              ? [lynch.seq]
              : []
            : about === 'dawn'
              ? nightDead.map((x) => x.seq)
              : about === 'over' && view.winnerSeq !== null
                ? [view.winnerSeq]
                : [];
        if (about === 'dawn')
          push(s.seq - 0.5, {
            kind: 'rule',
            key: `rule-morning-${d.day}`,
            seq: s.seq,
            day: d.day,
            tier: 'public',
            seats: [],
            text: `Morning ${d.day}`,
            chapter: 'morning',
          });
        if (about === 'over') pushOverRule(push, s.seq - 0.5, d.day);
        push(s.seq, {
          kind: 'gm',
          key: `gm-${s.seq}`,
          seq: s.seq,
          day: d.day,
          tier: 'public',
          seats,
          covers,
          text: s.text.trim(),
          roles,
          about,
        });
      }
    }

    // The votes are a batch in the log, so the view holds every pair from the moment the
    // ballots drop; the stage reveals them one chip at a time. Held back through the count so
    // the drawer does not tell the result first (owner, 2026-09-26): the line lands with it.
    const ballots = d.vote.ballots;
    const counting = o.beat?.day === d.day && COUNT_BEATS.has(o.beat.id);
    if (ballots.length && !counting)
      push(ballots[0].seq, {
        kind: 'votes',
        key: `votes-${d.day}`,
        seq: ballots[0].seq,
        day: d.day,
        tier: 'public',
        seats: [
          ...new Set(
            ballots.flatMap((b) => [b.voter, b.votee]).filter((s) => s !== 'abstain'),
          ),
        ],
        covers: ballots.map((b) => b.seq),
        pairs: ballots.map((b) => ({ voter: b.voter, votee: b.votee })),
      });

    const night = d.night;
    if (night) {
      if (xray)
        for (const a of night.actions)
          push(a.seq, {
            kind: 'act',
            key: `act-${a.seq}`,
            seq: a.seq,
            day: d.day,
            tier: 'xray',
            seats: [a.actor, a.target],
            actor: a.actor,
            role: a.role,
            target: a.target,
          });
      const packTier: LineTier = wolfMe ? 'private' : 'xray';
      if (wolfMe || xray) {
        for (const m of night.wolfChannel) {
          if (m.wolf !== 'game_master')
            push(m.seq, {
              kind: 'pack',
              key: `pack-${m.seq}`,
              seq: m.seq,
              day: d.day,
              tier: packTier,
              seats: [m.wolf],
              wolf: m.wolf,
              round: m.round,
              text: m.message,
              mine: wolfMe,
            });
          else if (wolfMe && night.wolfKill)
            push(m.seq, {
              kind: 'only',
              key: `only-${m.seq}`,
              seq: m.seq,
              day: d.day,
              tier: 'private',
              seats: [night.wolfKill],
              mine: true,
              who: 'Only you',
              about: `Night ${d.day}`,
              text: failedKill(night.wolfKill, 'Your'),
            });
          else if (xray)
            push(m.seq, {
              kind: 'only',
              key: `only-${m.seq}`,
              seq: m.seq,
              day: d.day,
              tier: 'private',
              seats: night.wolfKill ? [night.wolfKill] : [],
              mine: false,
              who: 'Only the pack',
              about: 'the game master’s note, verbatim',
              text: m.message,
            });
        }
        if (night.wolfKill) {
          const last = Math.max(
            ...night.wolfVotes.map((v) => v.seq),
            ...night.wolfChannel.filter((m) => m.wolf !== 'game_master').map((m) => m.seq),
            nightStart === Infinity ? 0 : nightStart,
          );
          push(last + 0.25, {
            kind: 'kill',
            key: `kill-${d.day}`,
            seq: last,
            day: d.day,
            tier: packTier,
            seats: [night.wolfKill],
            target: night.wolfKill,
            mine: wolfMe,
          });
        }
      }
    }

    // The day's brief plays in its morning, once the agents have read it (§4.2): when the
    // next day begins, or at the carried summary's own beat (the X-ray's). A day that ended
    // the game has no morning after it, and its brief is dropped. It is public: everyone's.
    const next = phaseSeq(d.day + 1, 'day');
    const carried = o.beat?.id === 'morning.carried-summary' && o.beat.day === d.day;
    if (d.summary && (next !== null || carried))
      push(next !== null ? next - 0.5 : view.lastSeq + 0.5, {
        kind: 'brief',
        key: `brief-${d.day}`,
        seq: next ?? view.lastSeq,
        day: d.day,
        tier: 'public',
        seats: [],
        text: d.summary,
      });
  }

  for (const p of privateResultsFor(view, me, xray)) push(p.seq, onlyLine(p, me));

  if (view.winner && view.winnerSeq !== null && !overGm) {
    pushOverRule(push, view.winnerSeq - 0.5, view.day);
    push(view.winnerSeq, {
      kind: 'over',
      key: 'over',
      seq: view.winnerSeq,
      day: view.day,
      tier: 'public',
      seats: [],
      winner: view.winner,
    });
  }

  const lines = out
    .map((x, i) => ({ ...x, i }))
    .sort((a, b) => a.at - b.at || a.i - b.i)
    .map((x) => x.line);
  const spoke = o.beat?.spoke;
  return spoke && o.beat?.seq !== undefined
    ? spokeCut(lines, o.beat.day, o.beat.seq, spoke.actor)
    : lines;
}

/**
 * The X-ray night plays its branches one after another, each seat's act and the pack's talk,
 * in the order each branch finished; but every spoke's view holds the whole night. So at a
 * spoke the night's lines are cut to where the spokes have got: the branches before this one
 * whole, this one up to the beat, none after it. A branch is known by its actor (the pack's
 * talk and kill are the pack's), and ordered by its last line, as the spokes are.
 */
function spokeCut(
  lines: DrawerLine[],
  day: number,
  seq: number,
  actor: string,
): DrawerLine[] {
  const branchOf = (l: DrawerLine): string | null =>
    l.day !== day
      ? null
      : l.kind === 'act'
        ? l.actor
        : l.kind === 'pack' || l.kind === 'kill'
          ? 'pack'
          : null;
  const last = new Map<string, number>();
  for (const l of lines) {
    const b = branchOf(l);
    if (b) last.set(b, Math.max(last.get(b) ?? -Infinity, l.seq));
  }
  const mine = last.get(actor) ?? seq;
  return lines.filter((l) => {
    const b = branchOf(l);
    if (b === null) return true;
    return b === actor ? l.seq <= seq : last.get(b)! < mine;
  });
}

/** The game master's closing line ("Game over! …"), which stands for `game_over` itself. */
function overLine(view: GameView): GmSlot | undefined {
  if (view.winnerSeq === null) return undefined;
  const gms = Object.values(view.days)
    .flatMap((d) => d.slots)
    .filter((s): s is GmSlot => s.kind === 'gm' && s.seq < view.winnerSeq!);
  const last = gms.sort((a, b) => a.seq - b.seq).at(-1);
  return last && GAME_OVER.test(last.text) ? last : undefined;
}

function pushOverRule(
  push: (at: number, line: DrawerLine) => void,
  at: number,
  day: number,
) {
  push(at, {
    kind: 'rule',
    key: 'rule-over',
    seq: Math.ceil(at),
    day,
    tier: 'public',
    seats: [],
    text: 'Game over',
    chapter: 'over',
  });
}

function passLine(s: PassSlot, day: number): DrawerLine {
  return {
    kind: 'pass',
    key: `pass-${s.seq}`,
    seq: s.seq,
    day,
    tier: 'xray',
    seats: [s.player],
    player: s.player,
    reason: s.passReason,
    draft: s.gatedCandidate,
  };
}

function failedKill(target: string, whose: string): OnlyText {
  const n = seatNumber(target);
  return {
    lead: `${whose} kill on seat ${n}`,
    chip: target,
    rest: ` failed. Seat ${n} survived.`,
  };
}

/** The private results this viewer holds: its own seated; everyone's with the X-ray. */
function privateResultsFor(
  view: GameView,
  me: string | null,
  xray: boolean,
): PrivateResult[] {
  const all = [
    ...(me ? view.me.privateResults.filter((p) => p.player === me) : []),
    ...(xray ? Object.values(view.xray.privateResults).flat() : []),
  ];
  const seen = new Set<number>();
  return all.filter((p) => (seen.has(p.seq) ? false : (seen.add(p.seq), true)));
}

function onlyLine(p: PrivateResult, me: string | null): DrawerLine {
  const mine = p.player === me;
  const n = seatNumber(p.player);
  const base = {
    kind: 'only' as const,
    key: `only-${p.seq}`,
    seq: p.seq,
    day: p.day,
    tier: 'private' as const,
    mine,
    who: mine ? 'Only you' : `Only seat ${n}`,
  };
  if (p.kind === 'investigation') {
    const t = seatNumber(p.target);
    const role = ARTICLE[p.role] ?? p.role;
    return {
      ...base,
      seats: [p.player, p.target],
      about: mine ? `Night ${p.day}` : 'the investigator’s reading',
      text: mine
        ? { lead: `You checked seat ${t}`, chip: p.target, rest: `: ${role}.` }
        : { lead: `Seat ${t}`, chip: p.target, rest: ` is ${role}.` },
    };
  }
  if (p.kind === 'vigilante_confirmation') {
    const t = seatNumber(p.target);
    return {
      ...base,
      seats: [p.player, p.target],
      about: `Night ${p.day}`,
      text: {
        lead: `${mine ? 'You' : `Seat ${n}`} shot seat ${t}`,
        chip: p.target,
        rest: `. Seat ${t} survived.`,
      },
    };
  }
  return {
    ...base,
    seats: [p.player],
    about: `Night ${p.day}`,
    text: p.count === 1 ? 'One cap left.' : `${p.count} caps left.`,
  };
}

/** The line a beat is about: lit, and scrolled to. Null when the beat has no line of its own. */
export function litKey(
  lines: readonly DrawerLine[],
  beat: Pick<SceneBeat, 'id' | 'day' | 'seq'>,
): string | null {
  if (COUNT_BEATS.has(beat.id)) return null; // the votes line is held back until the result
  // a lynch's game-master line is held back until the card is read: light the votes meanwhile
  if (
    UNTIL_TRUTH.has(beat.id) &&
    !lines.some((l) => l.kind === 'gm' && l.about === 'vote' && l.day === beat.day) &&
    lines.some((l) => l.kind === 'votes' && l.day === beat.day)
  )
    return `votes-${beat.day}`;
  const direct = lines.find(
    (l) => l.kind !== 'rule' && (l.seq === beat.seq || l.covers?.includes(beat.seq)),
  );
  if (direct) return direct.key;
  const gm = (about: 'vote' | 'dawn' | 'over') =>
    lines.find(
      (l) =>
        l.kind === 'gm' && l.about === about && (about === 'over' || l.day === beat.day),
    )?.key ?? null;
  switch (beat.id) {
    case 'vote.result':
    case 'vote.table-down':
    case 'lynch.stand-returns':
    case 'lynch.named':
    case 'lynch.drop':
    case 'lynch.card-up':
    case 'lynch.truth':
    case 'lynch.card-to-wing':
      return gm('vote');
    case 'morning.shutter-down':
    case 'morning.chip-attacked':
    case 'morning.chip-fell':
    case 'morning.card-down':
    case 'morning.chip-saved':
    case 'morning.roll':
    case 'morning.quiet':
      return gm('dawn');
    case 'morning.carried-summary':
      return `brief-${beat.day}`;
    case 'pack.decided':
      return `kill-${beat.day}`;
    default:
      if (beat.id.startsWith('over.'))
        return gm('over') ?? (lines.some((l) => l.key === 'over') ? 'over' : null);
      return null;
  }
}

/** The line matches the filters (rules are judged by what is under them, in `filterLines`). */
function passes(l: DrawerLine, f: DrawerFilters): boolean {
  if (f.day !== 'all' && l.day !== f.day) return false;
  if (l.kind === 'rule') return true;
  if (!f.show[l.tier]) return false;
  return f.seat === null || l.seats.includes(f.seat);
}

/** The lines left under the filters; a rule with nothing under it goes. */
export function filterLines(lines: readonly DrawerLine[], f: DrawerFilters): DrawerLine[] {
  const kept = lines.filter((l) => passes(l, f));
  return kept.filter(
    (l, i) => l.kind !== 'rule' || (i + 1 < kept.length && kept[i + 1].kind !== 'rule'),
  );
}

/** The day tabs along the foot: every day the drawer has a line for, in order. */
export function drawerDays(lines: readonly DrawerLine[]): number[] {
  return [...new Set(lines.map((l) => l.day))].filter((d) => d > 0).sort((a, b) => a - b);
}

/**
 * The Show toggles this viewer has: none for a spectator; Public and Private for a seat, or with
 * the X-ray (everyone's private lines). The X-ray's own lines have no toggle: they follow the
 * X-ray's one switch (owner, 2026-09-29).
 */
export function showRow(me: string | null, xray: boolean): LineTier[] {
  return me || xray ? ['public', 'private'] : [];
}

/*
 * How the drawer tells what it holds (HUD pass 3a, owner 2026-09-29): the lines are the same,
 * but a run of passes reads as one quiet line, the vote as a tally per seat voted for, and the
 * game master's reports as short sentences, one per seat they name.
 */

type PassLine = DrawerLine & { kind: 'pass' };

/** A run of passes one after another, told as one line ("Seat 7 passed. Seat 9 passed."). */
export interface PassRun {
  kind: 'passes';
  /** The first pass's key, so the run keeps its place while more passes join it. */
  key: string;
  day: number;
  tier: 'xray';
  passes: PassLine[];
}

export type ShownLine = DrawerLine | PassRun;

/** The lines as the drawer draws them: every run of consecutive passes folded into one. */
export function groupPasses(lines: readonly DrawerLine[]): ShownLine[] {
  const out: ShownLine[] = [];
  for (const l of lines) {
    const prev = out.at(-1);
    if (l.kind !== 'pass') out.push(l);
    else if (prev?.kind === 'passes' && prev.day === l.day) prev.passes.push(l);
    else
      out.push({
        kind: 'passes',
        key: `passes-${l.key}`,
        day: l.day,
        tier: 'xray',
        passes: [l],
      });
  }
  return out;
}

/** A shown line's own keys: a run answers to each of its passes (the lit line, the scroll). */
export function shownKeys(l: ShownLine): string[] {
  return l.kind === 'passes' ? l.passes.map((p) => p.key) : [l.key];
}

/** One seat's pass, as the run says it: the public part, what the table saw. */
export function passSentence(p: Pick<PassLine, 'player'>): string {
  return `Seat ${seatNumber(p.player)} passed`;
}

/** Why the seat passed, when it was not by choice: the X-ray's part of the run (verdigris). */
export function passWhy(p: Pick<PassLine, 'reason'>): string | null {
  if (p.reason === 'novelty_gated') return 'held back: nothing new to say';
  if (p.reason === 'generation_failed') return 'no line came';
  return null;
}

/** One seat voted for (or the abstentions), and who voted for it, in seat order. */
export interface TallyRow {
  votee: string;
  voters: string[];
}

/** The day's ballots as a tally: the most votes first, abstentions last, ties in seat order. */
export function voteTally(pairs: readonly { voter: string; votee: string }[]): TallyRow[] {
  const rows = new Map<string, string[]>();
  for (const p of pairs) rows.set(p.votee, [...(rows.get(p.votee) ?? []), p.voter]);
  const bySeat = (a: string, b: string) => seatNumber(a) - seatNumber(b);
  return [...rows.entries()]
    .map(([votee, voters]) => ({ votee, voters: voters.sort(bySeat) }))
    .sort(
      (a, b) =>
        Number(a.votee === 'abstain') - Number(b.votee === 'abstain') ||
        b.voters.length - a.voters.length ||
        bySeat(a.votee, b.votee),
    );
}

/** "Seats 1, 2 and 5 voted for seat 6. Seat 6 voted for seat 7.", in the tally's order. */
export function voteSentence(rows: readonly TallyRow[]): string {
  return rows
    .map((r) => {
      const ns = r.voters.map(seatNumber);
      const who =
        ns.length === 1
          ? `Seat ${ns[0]}`
          : `Seats ${ns.slice(0, -1).join(', ')} and ${ns.at(-1)}`;
      return r.votee === 'abstain'
        ? `${who} abstained.`
        : `${who} voted for seat ${seatNumber(r.votee)}.`;
    })
    .join(' ');
}

/** One sentence of a game master's report: the seat it is about, and the role it told. */
export interface ReportPart {
  text: string;
  /** The first seat the sentence names, if it names one. */
  seat: string | null;
  /** That seat's role, when the line tells it (a death at dawn, the lynch): its sigil. */
  role: string | null;
}

const SEAT_AT_START = /^seat (\d+)/i;
const BALLOT = /\bvoted for\b/i;
const VOTE_HEAD = /^here's the vote result/i;
const NIGHT_HEAD = /^night of day \d+:\s*/i;

/**
 * The game master's line as the drawer sets it: its words, split into one sentence per seat it
 * names ("Seat 3 was stabbed by the serial killer last night. They were a wolf."). The heading
 * the drawer already draws goes ("Here's the vote result for day 3:", "Night of day 2:"), and so
 * do the ballots when the day's votes line tells them (`ballotsTold`); nothing else changes.
 */
export function reportParts(
  l: Pick<DrawerLine & { kind: 'gm' }, 'text' | 'about' | 'seats' | 'roles'>,
  ballotsTold: boolean,
): ReportPart[] {
  const vote = l.about === 'vote';
  let kept = seatify(l.text)
    .replace(/\bPlayer seat (\d+)/g, 'Seat $1')
    .replace(/\bserial_killer\b/g, 'serial killer')
    // the game master writes "a" before every role; the drawer reads "an investigator"
    .replace(/\b([Aa]) (?=[aeiou])/g, '$1n ')
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean)
    .filter((s) => !vote || !(VOTE_HEAD.test(s) || (ballotsTold && BALLOT.test(s))))
    .join(vote && !ballotsTold ? '\n' : ' ');
  if (l.about === 'dawn') kept = kept.replace(NIGHT_HEAD, '');
  // a new part where a sentence opens on a seat; the ballots keep their own lines
  const parts: string[] = [];
  for (const line of kept.split('\n'))
    for (const s of line.split(/(?<=[.!?])\s+/)) {
      if (!s) continue;
      if (!parts.length || SEAT_AT_START.test(s) || BALLOT.test(s)) parts.push(s);
      else parts[parts.length - 1] += ` ${s}`;
    }
  // the dead are the first seats, in the order their roles are told (drawerLines)
  const dead = l.seats.slice(0, l.roles.length);
  const used = new Set<number>();
  const out = parts.map((p) => {
    const m = /\bseat (\d+)/i.exec(p);
    const seat = m ? `player_${m[1]}` : null;
    const i = seat ? dead.indexOf(seat) : -1;
    const told = i >= 0 && !used.has(i) && !BALLOT.test(p);
    if (told) used.add(i);
    return {
      text: p.charAt(0).toUpperCase() + p.slice(1),
      seat,
      role: told ? l.roles[i] : null,
    };
  });
  // a role the words never reached still lends its sigil, at the end
  const left = l.roles.filter((_, i) => !used.has(i));
  if (left.length && out.length && !out.at(-1)!.role) out[out.length - 1].role = left[0];
  return out;
}

/** The day's brief, as the drawer sets it: a labelled row per section, or one quiet line. */
export type BriefRow =
  { kind: 'row'; label: string; items: string[] } | { kind: 'none'; text: string };

/** The four headings `day_summary` always opens its lines with, in order, and how each reads. */
const BRIEF_HEADINGS = [
  {
    head: 'Key accusations and defenses:',
    label: 'Accusations and defences',
    none: 'accusations',
  },
  { head: 'Role claims:', label: 'Role claims', none: 'claims' },
  { head: 'Alliances and blocs:', label: 'Alliances and blocs', none: 'alliances' },
  { head: 'Village dynamics:', label: 'Village dynamics', none: 'village dynamics' },
] as const;

const NONE = /^none\.?$/i;

/** "a", "a or b", "a, b or c". */
const orList = (xs: readonly string[]) =>
  xs.length < 2 ? (xs[0] ?? '') : `${xs.slice(0, -1).join(', ')} or ${xs.at(-1)}`;

/**
 * The brief split at its four headings: a row per section with something in it (the accusations
 * one item each, the summary joins them with " | "), and the sections that say only "None."
 * folded into one quiet line where the first of them stood ("No accusations, claims or
 * alliances yet"). Null when the text does not open its lines with the four headings, in order:
 * the drawer then sets it as it came.
 */
export function briefRows(text: string): BriefRow[] | null {
  const bodies: string[] = [];
  for (const line of text
    .split('\n')
    .map((s) => s.trim())
    .filter(Boolean)) {
    const next = BRIEF_HEADINGS[bodies.length];
    if (next && line.startsWith(next.head))
      bodies.push(line.slice(next.head.length).trim());
    else if (bodies.length) bodies[bodies.length - 1] += ` ${line}`;
    else return null;
  }
  if (bodies.length !== BRIEF_HEADINGS.length) return null;
  const empty = BRIEF_HEADINGS.filter((_, i) => NONE.test(bodies[i]));
  const out: BriefRow[] = [];
  BRIEF_HEADINGS.forEach((h, i) => {
    const body = bodies[i];
    if (NONE.test(body)) {
      if (h === empty[0])
        out.push({ kind: 'none', text: `No ${orList(empty.map((e) => e.none))} yet` });
      return;
    }
    const items = i === 0 ? body.split(/\s+\|\s+/) : [body];
    out.push({ kind: 'row', label: h.label, items: items.filter(Boolean) });
  });
  return out;
}
