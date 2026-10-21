/**
 * The count, as the table reads it out: which plates there are, the order the chips land in,
 * who is lit at the end, and what the box says. The ballots arrive as one batch (the vote is
 * blind and parallel), so the order is the stage's to choose; the one rule is that the chip
 * that settles the winner lands last, so the count keeps its suspense to the end.
 */
import type { Ballot, DayVote } from '@/game/types';
import { seatNumber } from '../roles';

/** The plates: every seat that got a vote, in seat order, and abstain's plate last. */
export function candidatesOf(ballots: readonly Ballot[]): string[] {
  const set = [...new Set(ballots.map((b) => b.votee))];
  return set.sort((a, b) =>
    a === 'abstain' ? 1 : b === 'abstain' ? -1 : seatNumber(a) - seatNumber(b),
  );
}

/** How many chips each plate gets. */
export function tally(ballots: readonly Ballot[]): Record<string, number> {
  const out: Record<string, number> = {};
  for (const b of ballots) out[b.votee] = (out[b.votee] ?? 0) + 1;
  return out;
}

/** The plates with the most chips (one, or several on a tie). */
export function leaders(ballots: readonly Ballot[]): string[] {
  const t = tally(ballots),
    max = Math.max(0, ...Object.values(t));
  return candidatesOf(ballots).filter((c) => t[c] === max);
}

/**
 * The order the chips land: the log's, except that with one clear winner its last chip is
 * held back to land last. On a tie nothing settles it, so the log's order stands.
 */
export function landOrder(ballots: readonly Ballot[]): Ballot[] {
  const order = [...ballots],
    top = leaders(ballots);
  if (top.length !== 1) return order;
  const i = order.map((b) => b.votee).lastIndexOf(top[0]);
  const [last] = order.splice(i, 1);
  order.push(last);
  return order;
}

/** The score as it is read out: "3 to 2"; a single plate "9 to 0". */
export function score(counts: Record<string, number>): string {
  const ns = Object.values(counts)
    .filter((n) => n > 0)
    .sort((a, b) => b - a);
  if (ns.length === 1) ns.push(0);
  return ns.join(' to ');
}

/** Which plates are lit at the result: the voted-out seat's, abstain's, or the tied ones. */
export function litPlates(vote: DayVote): string[] {
  if (vote.outcome === 'lynched' && vote.lynched) return [vote.lynched];
  if (vote.outcome === 'abstain') return ['abstain'];
  if (vote.outcome === 'tie') return leaders(vote.ballots);
  return [];
}

/** The last line of the game master's message, the one that states the outcome. */
export function lastLine(text: string | null | undefined): string | null {
  const lines = (text ?? '')
    .split('\n')
    .map((l) => l.trim())
    .filter(Boolean);
  return lines.at(-1) ?? null;
}

/** One line of the result's tally: a plate and its chips. */
export interface TallyLine {
  /** A seat, or `abstain`. */
  votee: string;
  n: number;
  /** The plate is lit at the result (the voted-out seat's, abstain's, the tied ones). */
  lit: boolean;
}

/** The result's tally, the most chips first (seat order among equals, abstain's last). */
export function tallyLines(vote: DayVote): TallyLine[] {
  const counts = Object.keys(vote.voteCounts).length
    ? vote.voteCounts
    : tally(vote.ballots);
  const lit = new Set(litPlates(vote));
  return Object.keys(counts)
    .filter((c) => counts[c] > 0)
    .sort(
      (a, b) =>
        counts[b] - counts[a] ||
        (a === 'abstain' ? 1 : b === 'abstain' ? -1 : seatNumber(a) - seatNumber(b)),
    )
    .map((c) => ({ votee: c, n: counts[c], lit: lit.has(c) }));
}

/**
 * The result board's words, the outcome first: "Seat 4 was voted out" (the tally under it says
 * the count); no one out says so, and a tie the game master's own line (the last line of its vote
 * message), because the rule that breaks a tie is the server's to state.
 */
export function outcomeWords(
  vote: DayVote,
  me: string | null,
  gmLine?: string | null,
): { title: string; body: string | null; out: boolean } | null {
  switch (vote.outcome) {
    case 'lynched':
      return vote.lynched
        ? {
            title:
              vote.lynched === me
                ? 'You were voted out'
                : `Seat ${seatNumber(vote.lynched)} was voted out`,
            body: null,
            out: true,
          }
        : null;
    case 'abstain':
      return { title: 'The table abstains', body: 'No one is voted out.', out: false };
    case 'tie':
      return { title: 'A tie', body: gmLine || 'No one is voted out.', out: false };
    default:
      return null;
  }
}
