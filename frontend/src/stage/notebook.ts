'use client';

/**
 * The seated player's file on each seat for one game (owner, 2026-10-18: the notes moved into
 * the case file, picks over writing): the role a seat claims, the role the player thinks it
 * holds ("I think they are…"), what it said it did each night, and the player's own lines for
 * each day. On their own seat the claim and the nights are their cover: what they have said.
 * (A single "suspect" mark went 2026-10-14; a free note per seat went 2026-10-18, its words
 * read back as the seat's lines on day 1, so a notebook kept before then still loads.)
 *
 * It lives on this device only (localStorage, `notes_{gameId}`), and every scene reads the same
 * copy, so what was noted in the day is in the file at night. Storage may be missing or refuse
 * a write (a private window): the notebook then lasts as long as the page, and nothing breaks.
 * It reaches the server only when the player asks their agent for a draft with "Use my seat
 * notes" ticked (`notebookForAgent`), for that one draft, each seat's file told in one line so
 * the request keeps its shape.
 */
import { useCallback, useMemo, useSyncExternalStore } from 'react';
import { seatNotes } from '@/lib/storage';
import { ROLE_NAME, ROLE_ORDER } from './roles';

/** What a seat said it did one night: the seat it named, whom it saw, what it learned. */
export interface NightClaim {
  /** The seat it said it acted on. */
  target?: number;
  /** The seats it said it saw (a watch's visitors, a follow's visits). */
  seen?: readonly number[];
  /** It said it saw no one. */
  none?: boolean;
  /** What it said it learned, as `CLAIM_FORM`'s results name it (`suspicious`, `saved`). */
  result?: string;
}

type BySeat<T> = Readonly<Record<number, T>>;

export interface NotebookState {
  /** The role the player thinks a seat holds, per seat number (a role id); none: not sure. */
  guesses: BySeat<string>;
  /** The role a seat claims, per seat number; on the player's own seat, the role they claim. */
  claims: BySeat<string>;
  /** Per seat, per night: what it said it did. */
  nights: BySeat<BySeat<NightClaim>>;
  /** Per seat, per day: the player's own lines. */
  lines: BySeat<BySeat<string>>;
}

export interface Notebook extends NotebookState {
  /** "I think they are…": a role id, or null for "not sure". */
  setGuess: (seat: number, role: string | null) => void;
  /** The role a seat claims; null: none yet. */
  setClaim: (seat: number, role: string | null) => void;
  /** What a seat said it did one night; null clears it. */
  setNight: (seat: number, night: number, claim: NightClaim | null) => void;
  setLine: (seat: number, day: number, text: string) => void;
}

const EMPTY: NotebookState = { guesses: {}, claims: {}, nights: {}, lines: {} };

const seatKey = (k: string) => Number.isInteger(Number(k)) && Number(k) > 0;
const entries = (v: unknown) =>
  v && typeof v === 'object' ? Object.entries(v as Record<string, unknown>) : [];
const seatList = (v: unknown) =>
  Array.isArray(v) ? v.filter((n) => Number.isInteger(n) && n > 0) : undefined;

/** A stored record read back, whatever state it is in. */
export function parseNotebook(raw: unknown): NotebookState {
  if (!raw || typeof raw !== 'object') return EMPTY;
  const r = raw as Record<string, unknown>;
  const roles = (v: unknown) => {
    const out: Record<number, string> = {};
    for (const [k, x] of entries(v))
      if (typeof x === 'string' && x in ROLE_NAME && seatKey(k)) out[Number(k)] = x;
    return out;
  };
  // added 2026-09-30: a notebook kept before then has none, and reads as "not sure" throughout
  const guesses = roles(r.guesses);
  const claims = roles(r.claims);
  const nights: Record<number, Record<number, NightClaim>> = {};
  for (const [k, byNight] of entries(r.nights)) {
    if (!seatKey(k)) continue;
    for (const [n, c] of entries(byNight)) {
      if (!seatKey(n) || !c || typeof c !== 'object') continue;
      const x = c as Record<string, unknown>;
      const claim: NightClaim = {
        ...(Number.isInteger(x.target) ? { target: x.target as number } : {}),
        ...(seatList(x.seen)?.length ? { seen: seatList(x.seen) } : {}),
        ...(x.none === true ? { none: true } : {}),
        ...(typeof x.result === 'string' ? { result: x.result } : {}),
      };
      (nights[Number(k)] ??= {})[Number(n)] = claim;
    }
  }
  const lines: Record<number, Record<number, string>> = {};
  for (const [k, byDay] of entries(r.lines))
    if (seatKey(k))
      for (const [d, t] of entries(byDay))
        if (seatKey(d) && typeof t === 'string') (lines[Number(k)] ??= {})[Number(d)] = t;
  // a free note per seat (before 2026-10-18) is that seat's lines on day 1
  for (const [k, t] of entries(r.notes))
    if (seatKey(k) && typeof t === 'string' && t.trim() && !lines[Number(k)]?.[1])
      (lines[Number(k)] ??= {})[1] = t;
  // a `suspect` kept before 2026-10-14, or a `hinted` before 2026-10-18 (the rail's first-time
  // hint, gone now its plate says what a tap does), is not read, and goes with the next write
  return { guesses, claims, nights, lines };
}


/** The roles in the order the cast is read out (the cast plate's), for the guess's choices. */
const GUESS_ORDER = ROLE_ORDER;

/**
 * The roles a living seat could still hold, as the table knows it: the cast's counts less the
 * roles the dead have shown (deaths reveal the role), each with how many are left.
 */
export function guessChoices(
  cast: Readonly<Record<string, number>>,
  deadRoles: readonly (string | null)[],
): { role: string; left: number }[] {
  const left: Record<string, number> = { ...cast };
  for (const r of deadRoles) if (r) left[r] = (left[r] ?? 0) - 1;
  const roles = [
    ...GUESS_ORDER.filter((r) => r in left),
    ...Object.keys(left).filter((r) => !GUESS_ORDER.includes(r)),
  ];
  return roles.filter((r) => left[r] > 0).map((role) => ({ role, left: left[role] }));
}

const books = new Map<string, NotebookState>();
const listeners = new Map<string, Set<() => void>>();

function current(gameId: string): NotebookState {
  let b = books.get(gameId);
  if (!b) {
    b = parseNotebook(seatNotes.get(gameId));
    books.set(gameId, b);
  }
  return b;
}

/** Change one game's notebook, keep it, and tell every rail that shows it. */
export function updateNotebook(
  gameId: string,
  change: (b: NotebookState) => NotebookState,
): void {
  const next = change(current(gameId));
  books.set(gameId, next);
  seatNotes.set(gameId, next);
  listeners.get(gameId)?.forEach((f) => f());
}

/** The notebook for a game, or null when there is none to keep (no seated human, no game). */
export function useNotebook(gameId: string | null): Notebook | null {
  const subscribe = useCallback(
    (f: () => void) => {
      if (!gameId) return () => {};
      const set = listeners.get(gameId) ?? new Set();
      listeners.set(gameId, set);
      set.add(f);
      return () => set.delete(f);
    },
    [gameId],
  );
  const state = useSyncExternalStore(
    subscribe,
    () => (gameId ? current(gameId) : EMPTY),
    () => EMPTY,
  );
  return useMemo(() => {
    if (!gameId) return null;
    const role = (key: 'guesses' | 'claims') => (seat: number, r: string | null) =>
      updateNotebook(gameId, (b) => {
        const next = { ...b[key] };
        if (r) next[seat] = r;
        else delete next[seat];
        return { ...b, [key]: next };
      });
    return {
      ...state,
      setGuess: role('guesses'),
      setClaim: role('claims'),
      setNight: (seat, night, claim) =>
        updateNotebook(gameId, (b) => {
          const mine = { ...b.nights[seat] };
          if (claim && (claim.target || claim.seen?.length || claim.none || claim.result))
            mine[night] = claim;
          else delete mine[night];
          return { ...b, nights: { ...b.nights, [seat]: mine } };
        }),
      setLine: (seat, day, text) =>
        updateNotebook(gameId, (b) => {
          const mine = { ...b.lines[seat] };
          if (text.trim()) mine[day] = text;
          else delete mine[day];
          return { ...b, lines: { ...b.lines, [seat]: mine } };
        }),
    };
  }, [gameId, state]);
}

/**
 * What a claimed role's night looks like in the file (the engine's night actions,
 * Agents/schemas/roles.py): what it did, in the past tense, to one seat, whom that showed it, and
 * what it may have learned. A role with none (the villager, the speculator's pick of a side)
 * has no night to note.
 */
export interface ClaimForm {
  verb: string;
  /** The seats the action shows, when it shows any: "saw them visit". */
  seen?: string;
  results?: readonly { id: string; words: string }[];
  /** The first night it acts (the necromancer sits out night 1). */
  from?: number;
}

export const CLAIM_FORM: Readonly<Record<string, ClaimForm>> = {
  investigator: {
    verb: 'checked',
    results: [
      { id: 'suspicious', words: 'reads Suspicious' },
      { id: 'not_suspicious', words: 'reads Not suspicious' },
    ],
  },
  sentinel: { verb: 'watched', seen: 'saw at their door' },
  trailseer: { verb: 'followed', seen: 'saw them visit' },
  vigilante: { verb: 'shot' },
  sigilist: { verb: 'set a sigil on' },
  healer: { verb: 'protected', results: [{ id: 'saved', words: 'saved them from an attack' }] },
  chanteuse: { verb: 'blocked' },
  illusionist: { verb: 'concealed' },
  wolf: { verb: 'attacked' },
  serial_killer: { verb: 'attacked' },
  necromancer: { verb: 'raised', from: 2 },
  fortune_teller: { verb: 'bet on' },
};

/** "followed player_5; saw player_7, player_1; reads Suspicious": one night, in words. */
export function nightWords(role: string | undefined, c: NightClaim, seat = (n: number) => `player_${n}`) {
  const form = role ? CLAIM_FORM[role] : undefined;
  const parts: string[] = [];
  if (c.target) parts.push(`${form?.verb ?? 'acted on'} ${seat(c.target)}`);
  if (c.none) parts.push('saw no one');
  else if (c.seen?.length) parts.push(`saw ${c.seen.map(seat).join(', ')}`);
  const result = form?.results?.find((r) => r.id === c.result);
  if (result) parts.push(result.words);
  return parts.join('; ');
}

/** The server's cap on one shared note (DraftRequest.seat_notes). */
const SHARED_NOTE_MAX = 300;

/**
 * What the notebook gives the seat's agent with a draft, by the seat ids the agents use
 * (`player_5`), or null when it holds nothing to give: each seat's file in one line, the guess
 * first ("(I think: serial killer) Claims healer. Night 1: says they protected player_4. Day 2:
 * …"), so the request's shape is the server's as it was. On the player's own seat (`me`) it is
 * what they have claimed so far, for the agent to keep their story straight. `dead` drops the
 * guess on a seat that has died, as the rail does.
 */
export function notebookForAgent(
  book: Partial<NotebookState> | null,
  dead: (seat: number) => boolean = () => false,
  me: number | null = null,
): { seat_notes: Record<string, string> } | null {
  if (!book) return null;
  const { guesses = {}, claims = {}, nights = {}, lines = {} } = book;
  const seatNotes: Record<string, string> = {};
  const seats = new Set(
    [guesses, claims, nights, lines].flatMap((m) => Object.keys(m)).map(Number),
  );
  for (const seat of seats) {
    const own = seat === me;
    // a dead seat's role is on the table: a guess at it says nothing
    const guess = own || dead(seat) ? undefined : guesses[seat];
    const claim = claims[seat];
    const role = (r: string) => (ROLE_NAME[r] ?? r).toLowerCase();
    const parts = [
      guess ? `(I think: ${role(guess)})` : '',
      claim ? (own ? `What I have claimed: ${role(claim)}.` : `Claims ${role(claim)}.`) : '',
      ...Object.entries(nights[seat] ?? {}).map(([n, c]) => {
        const words = nightWords(claim, c);
        return words ? `Night ${n}: ${own ? 'I said I' : 'says they'} ${words}.` : '';
      }),
      ...Object.entries(lines[seat] ?? {}).map(([d, t]) =>
        t.trim() ? `Day ${d}: ${t.trim().replace(/\s+/g, ' ')}` : '',
      ),
    ];
    const note = parts.filter(Boolean).join(' ').slice(0, SHARED_NOTE_MAX);
    if (note) seatNotes[`player_${seat}`] = note;
  }
  return Object.keys(seatNotes).length ? { seat_notes: seatNotes } : null;
}

/** The game whose notebook this viewer keeps: a seated human in a live game, else none. */
export function notebookGame(
  p: { hud: string; game?: string },
  me: string | null,
): string | null {
  return p.hud === 'live' && me && p.game ? p.game : null;
}
