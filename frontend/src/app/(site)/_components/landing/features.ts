/**
 * The landing's three features (owner, 2026-10-15), each told from a real moment where one
 * exists. The agents' words are the logs' own, copied at the seqs given; they describe those
 * moments, so they are fixed here rather than read from whatever game the carriage plays.
 */

/**
 * The lesson card: game 2f19d908 (Claude Haiku 5.5, memory on, ten seats, in the public
 * archive), night 2. Seat 4, the Sigilist, consults its lessons (`memory_consulted` seq 270)
 * and follows the third; that night seat 7, the Chanteuse, attacks into the sigil and dies (the
 * morning's report, `gm_message` seq 305). The lesson is cut after its first sentence.
 */
export const LESSON = {
  game: '2f19d908-a6b3-4faf-8f16-c2a009bb0428',
  /** The game's recorded cast, index 0 = seat 1. */
  cast: ['hare', 'polarBear', 'cat', 'dragon', 'shade', 'onion', 'mushroom', 'owl', 'kitsune', 'whale'],
  seat: 4,
  lesson:
    'With both sigils left and no hard leads, place one sigil each night on the player most plausibly carrying a night attack (a suspected wolf or killer), and keep the second in reserve…',
  why: 'The investigator read is only partly trusted and no visits are confirmed, so placing one sigil on a likely attacker while keeping one in reserve fits.',
  struck: 7,
} as const;

/**
 * A real draft (captured 2026-09-28): seat 6's day 3 discussion turn, rebuilt from the log
 * at the moment the seat passed (after seat 8's second line), drafted by the server's own
 * `draft_from_notes` on the game's model, Gemini 3.5 Flash-Lite. Seat 6 was a villager, and
 * the table lynched it that day. Verbatim, the second of two drafts
 * (`docs/design_2026-09-28/landing_features.md`). Nobody played that seat: the notes were
 * written for the demo, and the card says so.
 */
export const DRAFT = {
  game: '9369a5c1-3c28-42ce-86a1-9d594dfa4804',
  seat: 6,
  notes: "8 changed tack the second 5 pushed back. that's what a wolf does. push on 8",
  line: 'Player 8 instantly flipped their stance the moment player_5 pushed back on them, which is classic wolf behavior, so we need to put pressure on player_8 right now.',
};

/** An illustrative room, not a record: three people aboard, agents in the other seats; the
 *  third person's timer has run out, and their agent is taking the turn. */
export const ROOM_PEOPLE = ['You', 'Mei', 'Sam'] as const;

/** The three plates: each card's name, and its tab on a narrow bench. */
export const PLATES = ['Memory', 'Your agent', 'Friends'] as const;

/**
 * The replay section's moment: game 68c26e83 (Gemini 3.5 Flash-Lite, ten seats, the carriage's
 * game), day 2. Seat 10, the Chanteuse, claims the Investigator (`speech` seq 161) and writes
 * down the lie it is keeping (`strategy_update` seq 164); seat 8, the real Investigator, calls
 * it a fake claim, and the table votes seat 8 out, 6 to 2 (`lynch_result`, day 2).
 */
export const BLUFF = {
  game: '68c26e83-f5c9-50d5-92b7-3589312a0cb9',
  day: 2,
  seat: 10,
  role: 'Chanteuse',
  said: "I used my investigator check on player_5 during night one to secure an early read. Player_1's watch accurately catches that visit, and the check result came back not suspicious.",
  note: "Public cover: investigator. Public account: checked player_5 on night 1 and found them not suspicious. Do not disclose: my block on player_5, the pack's kill on player_4.",
  victim: 8,
  votes: '6 to 2',
} as const;
