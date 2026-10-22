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
  cast: [
    'hare',
    'polarBear',
    'cat',
    'dragon',
    'shade',
    'onion',
    'mushroom',
    'owl',
    'kitsune',
    'whale',
  ],
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
 * The replay section's moment: game e45eda20 (DeepSeek Flash, ten seats, the carriage's game;
 * owner's pick, 2026-10-22), day 3. Seat 10, the Illusionist and the last wolf, has claimed the
 * Investigator since day 2; it calls the real one's claim a story built to fit (`speech` seq
 * 335) and writes down the cover it is keeping (`strategy_update` seq 338, trimmed where the
 * "…" are: its plans for the SK and the night). Seat 1, the real Investigator, had checked it
 * and found it Suspicious; the table votes seat 1 out with 3 of the 5 votes (`lynch_result`,
 * day 3).
 */
export const BLUFF = {
  game: 'e45eda20-ccbf-4d38-8be0-c18ccacd028f',
  day: 3,
  seat: 10,
  role: 'Illusionist',
  said: "player_1, by the book: I published my Investigator claim on day 2 with an empty night to show. You sat silent and surfaced yours only after the chanteuse was confirmed wolf. That's not two investigators at dawn — that's one man correcting his story. I'll be voting player_1; the SK hunt can wait until the liar is off the board.",
  note: "Lone wolf. Public cover: Investigator, held nights 1 and 2. player_1 counter-claims Investigator, so the day's fight is his word against mine — lean on the fact his block story mirrors the dead chanteuse's and that he surfaced the claim only after mine. … vote player_1 today. … Do not disclose the conceal or the pack kill.",
  victim: 1,
  votes: '3 of the 5 votes',
} as const;
