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
 *   is blind and the ballots arrive as one batch; the ending;
 * - private: a seated human's own results as "Only you" lines (what happened to their act and
 *   when; only the investigator's reading names a role); a wolf's pack chat and the kill; with
 *   the X-ray, everyone's private results as "Only seat 4";
 * - X-ray, in aqua: the passes with their reason and held-back draft, the night acts, the
 *   pack's talk, and the day's brief in its morning.
 *
 * The chapters (Day N · discussion, the vote, Night N, Morning N, Game over) run down it as
 * rules, the seek bar's marks read downwards; a rule with nothing under it after the filters
 * is dropped. `firing_reason` and `addressed_targets` are deferred by decision.
 */
import type { GameView, GmSlot, PassSlot, PrivateResult } from '@/game/types';
import type { PassReason } from '@/types/contracts';
import type { SceneBeat } from '../beats/types';
import { seatNumber } from '../roles';

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

export type DrawerLine =
  | (LineBase & { kind: 'rule'; text: string })
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
      /** The seat's own line (dashed, amber) rather than someone else's (aqua). */
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

    const ballots = d.vote.ballots;
    if (ballots.length)
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
    // next day begins, or at the carried summary's own beat. A day that ended the game has
    // no morning after it, and its brief is dropped.
    const next = phaseSeq(d.day + 1, 'day');
    const carried = o.beat?.id === 'morning.carried-summary' && o.beat.day === d.day;
    if (xray && d.summary && (next !== null || carried))
      push(next !== null ? next - 0.5 : view.lastSeq + 0.5, {
        kind: 'brief',
        key: `brief-${d.day}`,
        seq: next ?? view.lastSeq,
        day: d.day,
        tier: 'xray',
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
    case 'vote.ballots-drop':
    case 'vote.closes':
    case 'vote.count-begins':
    case 'vote.chip-counted':
      return `votes-${beat.day}`;
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

/** The Show toggles this viewer has: none for a spectator; Private for a seat; all three with the X-ray. */
export function showRow(me: string | null, xray: boolean): LineTier[] {
  if (xray) return ['public', 'private', 'xray'];
  return me ? ['public', 'private'] : [];
}
