/**
 * The landing's three features, told from game 9369a5c1 (the featured replay). The agents'
 * words are the log's own, copied from `src/stage/fixtures/replay-9369a5c1.json` at the seqs
 * given, and the count was taken from the same file (2026-09-28: 158 lessons across 53
 * `memory_consulted`). They describe that one game, so they are fixed here rather than
 * recounted from whatever game the carriage happens to play.
 */

/** The game all of this is from (the chips are its cast). */
export const FEATURE_GAME = '9369a5c1-3c28-42ce-86a1-9d594dfa4804';

/** Seat 8, the wolf, before the day 2 vote: `memory_consulted` seq 100, lesson 1 and its
 *  verdict ("override": it went with a past observation, abstaining with the table). */
export const WEIGHED = {
  seat: 8,
  lesson:
    'In information-starved early game states where a no-elimination consensus is forming, the wolf team must intentionally split their votes. One wolf should join the majority to maintain a low profile, while the other wolf should cast a dissenting vote on a viable behavioral target…',
  why: '…abstaining with the majority is safer than splitting votes on Day 2.',
};

/** What the game taught the wolf about that same vote: `memory_extracted` seq 407,
 *  observation 20 (the wolf's day 2 abstention), its outcome's first two sentences. */
export const TAUGHT =
  'Negative. While maintaining cover, this passivity cost two full cycles that could have been used to mis-eliminate villagers, unnecessarily extending the game and risking loss of tempo.';

/** The loop the lessons go round, in plain words (the pipeline's names are the write-up's). */
export const LOOP = [
  {
    step: 'Reflect',
    text: 'after a game, each agent writes down what worked and what didn’t',
  },
  { step: 'Distill', text: 'the lessons are merged with earlier ones' },
  { step: 'Recall', text: 'next game, it pulls the lessons that fit where it is' },
  { step: 'Weigh', text: 'it decides whether each one applies, and says why' },
] as const;

/**
 * A real draft (captured 2026-09-28): seat 6's day 3 discussion turn, rebuilt from the log
 * at the moment the seat passed (after seat 8's second line), drafted by the server's own
 * `draft_from_notes` on the game's model, Gemini 3.5 Flash-Lite. Seat 6 was a villager, and
 * the table lynched it that day. Verbatim, the second of two drafts
 * (`docs/design_2026-09-28/landing_features.md`).
 */
export const DRAFT = {
  seat: 6,
  notes: "8 changed tack the second 5 pushed back. that's what a wolf does. push on 8",
  line: 'Player 8 instantly flipped their stance the moment player_5 pushed back on them, which is classic wolf behavior, so we need to put pressure on player_8 right now.',
};

/** What a seat's agent is handed, and what it never is (the Send builders' role gating). */
export const SEES = [
  'your role',
  'your own night results',
  'everything said at the table',
  'your pack’s talk, if you’re a wolf',
] as const;
export const NEVER_SEES = [
  'anyone else’s role',
  'anyone else’s results',
  'the wolves’ talk, unless you’re one',
] as const;

/** An illustrative room, not a record: three people aboard, agents in the other seats. */
export const ROOM_PEOPLE = ['You', 'Mei', 'Sam'] as const;

/** The three brass plates: the number, what it counts, and its short name as a tab. */
export const PLATES = [
  { num: '158', cap: 'lessons weighed in one game', tab: 'lessons' },
  { num: '3', cap: 'drafts a turn', tab: 'drafts' },
  { num: '1 link', cap: 'is all your friends need', tab: 'friends' },
] as const;
