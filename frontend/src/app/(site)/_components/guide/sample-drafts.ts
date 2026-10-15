/**
 * The guide's composer demo answers Draft with sample lines, written here, never a model's: the
 * guide calls no model and sends nothing. The line follows what the reader did, as an agent's
 * would: a steer naming a seat or asking for a tone, the line in the box (a redraft revises
 * it), and, with "Use my seat notes" ticked, their note or guess on a seat in the demo above.
 */
import { ROLE_NAME } from '@/stage/roles';

export interface SampleAsk {
  /** The steer, as typed. */
  steer: string;
  /** The line in the box. */
  current: string;
  /** The notebook, when "Use my seat notes" is ticked and it holds anything. */
  book: {
    notes: Readonly<Record<number, string>>;
    guesses?: Readonly<Record<number, string>>;
  } | null;
  /** Drafts already taken this turn: the plain openers take turns. */
  taken: number;
}

const OPENERS = [
  'No read from me yet. Seats 7 and 9 have said the least today; I want to hear from them before we vote.',
  'The wolves left the loudest voices alone last night. Who gains from that? That is where I would look.',
  'I will be open: I am not claiming a role yet. Seat 3, you agreed with everyone so far. Why?',
];

/** The seat the reader wrote on or guessed at, its note cut short, and the guessed role. */
function noted(book: SampleAsk['book']) {
  if (!book) return null;
  const guesses = book.guesses ?? {};
  const seats = [...Object.keys(guesses), ...Object.keys(book.notes)].map(Number);
  const seat = seats.find((n) => guesses[n] || book.notes[n]?.trim());
  if (seat === undefined) return null;
  const note = book.notes[seat]?.trim() ?? '';
  return {
    seat,
    note: note.length > 60 ? `${note.slice(0, 57).trimEnd()}…` : note,
    role: guesses[seat] ? (ROLE_NAME[guesses[seat]] ?? guesses[seat]).toLowerCase() : null,
  };
}

export function sampleDraft({ steer, current, book, taken }: SampleAsk): string {
  const s = steer.trim();
  const named = /seat\s*(\d{1,2})/i.exec(s)?.[1];
  const from = noted(book);
  const seat = named ? Number(named) : (from?.seat ?? 5);
  const soft = /soft|gentle|kind|calm|polite/i.test(s);
  const hard = /push|press|hard|accuse|blunt/i.test(s);
  const short = /short|brief|one line/i.test(s);
  // a steer, or a line to revise: a line about that seat, in the tone asked for
  if (s || current.trim()) {
    if (short) return `Seat ${seat}: who did you vote for, and why?`;
    if (soft)
      return `I may be reading too much into it, but seat ${seat} has me uneasy. Seat ${seat}, would you walk us through your thinking?`;
    if (hard)
      return `Seat ${seat}, that is twice now you have steered us away from yourself. Explain it, or my vote is on you.`;
    if (current.trim())
      return `Put another way: seat ${seat} has not given us a single read today. Seat ${seat}, who do you suspect, and why?`;
  }
  // the reader's own notes, shared for this draft
  if (from?.role)
    return `I think seat ${from.seat} could be the ${from.role}. Seat ${from.seat}, if I am right, tell us what you saw last night; if I am wrong, tell us what you are.`;
  if (from?.note)
    return `I have been watching seat ${from.seat}. My note on them: "${from.note}". Seat ${from.seat}, want to answer that?`;
  if (named)
    return `Seat ${seat}, you have been quiet on the one thing I want to know: where were you pointing before the vote?`;
  return OPENERS[taken % OPENERS.length];
}
