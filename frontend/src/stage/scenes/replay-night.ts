/**
 * The replay's X-ray night, read back out of the folded view (beat sheet §9): who acted, in
 * what order, and which marks are on the row at a given spoke.
 *
 * The night's acts run at the same time and their events interleave in the log, so the
 * replay tells them one actor at a time: a "branch" per actor (the pack is one), ordered by
 * its last event. The beat cutter (`beatsFor`) orders them from the log; a scene only has the
 * view, so this rebuilds the same order from what the view keeps (the acts, the pack's talk
 * and votes, each agent's consults and reads with their seqs). A test holds the two equal on
 * the fixture.
 */
import type { GameView } from '@/game/types';
import type { Spoke } from '../beats/types';
import type { ActKind } from '../instruments/ActMark';
import { isPackRole, seatNumber } from '../roles';

export interface NightBranch {
  /** A seat, or `pack` for the wolves together. */
  actor: string;
  /** The role acting: `wolf` for the pack. */
  role: string;
  /** Who stands at the stand for this spoke: the seat, or the pack's living wolves. */
  seats: string[];
  /** Where its mark lands (the act's target, the kill decided); null = no mark. */
  target: string | null;
  /** The pack's lines that night (0 for anyone else). */
  lines: number;
  /** Its last event's seq: the order the replay tells the branches in. */
  lastSeq: number;
}

/** The mark each role's act leaves on its target's chip. */
export const ACT_MARK: Record<string, ActKind> = {
  wolf: 'bite',
  serial_killer: 'knife',
  vigilante: 'bullet',
  healer: 'plaster',
  investigator: 'lens',
};

/** What each act does to its target, as the spoke's box says it (bench 67, the role sheet's verbs). */
const VERB: Record<string, string> = {
  wolf: 'chooses',
  healer: 'protects',
  investigator: 'checks',
  sentinel: 'watches',
  trailseer: 'follows',
  vigilante: 'shoots',
  sigilist: 'marks',
  chanteuse: 'blocks',
  serial_killer: 'kills',
  // the act carries only the target; the body it borrowed is not on the wire
  necromancer: 'acts on',
  fortune_teller: 'bets on',
};
/** A seat that weighed its night and chose no one (its consult and reads, no act). */
const HOLDS: Record<string, string> = {
  vigilante: 'holds its fire.',
  investigator: 'keeps its checks.',
  sentinel: 'keeps its watches.',
  sigilist: 'keeps its sigils.',
  necromancer: 'stays put.',
  speculator: 'waits.',
  fortune_teller: 'waits.',
};
/** The speculator's pick is a side word, not a seat. */
const SIDE: Record<string, string> = {
  town: 'Town',
  wolves: 'the Wolves',
  lone_killer: 'the lone killer',
  self: 'itself',
};

/**
 * The spoke's line: "protects seat 3.", "picks the Wolves.", "holds its fire.". The
 * illusionist's act has no target (the engine sends "" for a conceal, and nothing at all for
 * "keep your conceals", whose consult falls to the pack's branch), so its branch with no
 * target is the conceal.
 */
export function actLine(role: string, target: string | null): string {
  if (role === 'illusionist') return 'conceals the body.';
  if (!target) return HOLDS[role] ?? 'does not act.';
  if (role === 'speculator') return `picks ${SIDE[target] ?? target}.`;
  return `${VERB[role] ?? 'acts on'} seat ${seatNumber(target)}.`;
}

/** Every branch of night `day` the view holds, in the order the replay plays them. */
export function nightBranchesOf(view: GameView, day: number): NightBranch[] {
  const night = view.days[day]?.night;
  if (!night) return [];
  const start = view.timeline.find((t) => t.day === day && t.phase === 'night')?.seq ?? -1;
  const wolves = new Set([
    ...night.packRoster,
    ...Object.entries(view.xray.roles)
      .filter(([, r]) => isPackRole(r))
      .map(([s]) => s),
  ]);

  const byActor = new Map<string, NightBranch>();
  const touch = (actor: string, seq: number, role: string) => {
    const b = byActor.get(actor) ?? {
      actor,
      role,
      seats: actor === 'pack' ? [] : [actor],
      target: null,
      lines: 0,
      lastSeq: seq,
    };
    b.lastSeq = Math.max(b.lastSeq, seq);
    byActor.set(actor, b);
    return b;
  };

  // A ten-seat carrier's kill comes as its own act beside its skill's (2026-10-10): the first
  // pack act on the kill's target is the pack's, the rest (a block, a conceal) the seat's own.
  let carried = false;
  for (const a of night.actions) {
    if (
      !carried &&
      night.wolfKill !== null &&
      wolves.has(a.actor) &&
      a.target === night.wolfKill
    ) {
      carried = true;
      touch('pack', a.seq, 'wolf');
    } else {
      // an act with no target (a held fire, a conceal) comes as "": a spoke with no mark
      touch(a.actor, a.seq, a.role).target = a.target || null;
    }
  }
  for (const m of night.wolfChannel)
    if (m.wolf !== 'game_master') touch('pack', m.seq, 'wolf').lines++;
  for (const v of night.wolfVotes) touch('pack', v.seq, 'wolf');
  // an agent's consult and reads before its act belong to its branch (a wolf's to the pack's)
  for (const [seat, agent] of Object.entries(view.xray.agents)) {
    const seqs = [...agent.consulted, ...agent.reads]
      .filter((e) => e.day === day && e.seq > start)
      .map((e) => e.seq);
    if (!seqs.length) continue;
    const actor = wolves.has(seat) ? 'pack' : seat;
    touch(
      actor,
      Math.max(...seqs),
      actor === 'pack' ? 'wolf' : (view.xray.roles[seat] ?? ''),
    );
  }
  const pack = byActor.get('pack');
  if (pack) {
    pack.target = night.wolfKill;
    // the kill is decided just after the last vote
    if (night.wolfKill)
      pack.lastSeq = Math.max(pack.lastSeq, ...night.wolfVotes.map((v) => v.seq + 0.5));
    const living = night.packRoster.length
      ? night.packRoster
      : [...wolves].filter((s) => view.alive.includes(s));
    pack.seats = [...living].sort((a, b) => view.seats.indexOf(a) - view.seats.indexOf(b));
  }
  // a seat that weighed its night and chose no one (the vigilante holding fire: its consult and
  // reads, no act) took a decision too: its branch is a spoke with no mark (owner, 2026-09-30).
  // Only the pack needs talk or a kill to be told.
  return [...byActor.values()]
    .filter((b) => b.actor !== 'pack' || b.target !== null || b.lines > 0)
    .sort((a, b) => a.lastSeq - b.lastSeq);
}

/** The branch chose no one: a seat that held (the vigilante holding fire). */
export function isHeld(branch: NightBranch | undefined): boolean {
  return (
    !!branch && branch.actor !== 'pack' && branch.target === null && branch.lines === 0
  );
}

/** The spoke's step ends its branch: the mark landing, the pack's last line, or the hold. */
export function endsBranch(spoke: Spoke, branch: NightBranch | undefined): boolean {
  return !!branch && spoke.step === spoke.steps - 1;
}

/** Whether a spoke's step is its mark landing (the last step, when the branch has a target). */
export function isMarkStep(spoke: Spoke, branch: NightBranch | undefined): boolean {
  return !!branch?.target && spoke.step === spoke.steps - 1;
}

export interface RowMark {
  seat: string;
  kind: ActKind;
  /** The branch that left it, in play order. */
  rank: number;
  /** Lands on this beat (the rest were already there). */
  landing: boolean;
}

/**
 * The marks on the row at a spoke: every earlier branch's, and this one's if this step is its
 * mark. `null` is the night whole: every mark at once.
 */
export function marksAt(branches: readonly NightBranch[], spoke: Spoke | null): RowMark[] {
  const out: RowMark[] = [];
  branches.forEach((b, rank) => {
    if (!b.target || !ACT_MARK[b.role]) return;
    const here = spoke !== null && rank === spoke.rank;
    if (spoke !== null && rank > spoke.rank) return;
    if (here && !isMarkStep(spoke, b)) return;
    out.push({ seat: b.target, kind: ACT_MARK[b.role], rank, landing: here });
  });
  return out;
}

/**
 * How many of the night's units are in at a spoke (the pill): the branches told
 * so far, counting this one once its mark has landed. The night whole is all of them.
 */
export function actedAt(
  branches: readonly NightBranch[],
  spoke: Spoke | null,
  total: number,
): number {
  if (spoke === null) return total;
  return Math.min(total, spoke.rank + (endsBranch(spoke, branches[spoke.rank]) ? 1 : 0));
}

/**
 * Who acted on night `day`, seat by seat, and the rooms each is in, in the order the replay
 * plays them: a seat's own, and for a wolf the pack's (`pack`) too; a ten-seat wolf's skill, a
 * block or a conceal, is a room of its own beside the pack's. The rooms are read from `ahead`,
 * a view that has reached the night's end (the hub's own view has not); the pack's seats are
 * the wolves living in `view`, not those left at the log's end.
 */
export function actedTonight(
  view: GameView,
  ahead: GameView,
  day: number,
): Map<string, string[]> {
  const out = new Map<string, string[]>();
  for (const b of nightBranchesOf(ahead, day)) {
    const seats =
      b.actor === 'pack'
        ? view.alive.filter((s) => isPackRole(view.xray.roles[s]))
        : b.seats.filter((s) => view.alive.includes(s));
    for (const s of seats) out.set(s, [...(out.get(s) ?? []), b.actor]);
  }
  return out;
}
