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

/** Every branch of night `day` the view holds, in the order the replay plays them. */
export function nightBranchesOf(view: GameView, day: number): NightBranch[] {
  const night = view.days[day]?.night;
  if (!night) return [];
  const start = view.timeline.find((t) => t.day === day && t.phase === 'night')?.seq ?? -1;
  const wolves = new Set([
    ...night.packRoster,
    ...Object.entries(view.xray.roles)
      .filter(([, r]) => r === 'wolf')
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

  for (const a of night.actions) touch(a.actor, a.seq, a.role).target = a.target;
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
  // a branch with nothing to show (a consult but no act) is not a spoke
  return [...byActor.values()]
    .filter((b) => b.target !== null || b.lines > 0)
    .sort((a, b) => a.lastSeq - b.lastSeq);
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
  return Math.min(total, spoke.rank + (isMarkStep(spoke, branches[spoke.rank]) ? 1 : 0));
}
