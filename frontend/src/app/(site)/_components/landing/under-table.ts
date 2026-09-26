/**
 * "What's under the table": three things the agents do that the table never sees, told from
 * game 9369a5c1 (the featured replay). The words are the log's own, copied from
 * `src/stage/fixtures/replay-9369a5c1.json` at the seqs given; the counts were taken from the
 * same file (2026-09-26: 77 `strategy_update`; 329 reads in 52 `player_reads` checked against
 * `roles_assigned`; 12 `pass_marker`, 6 of them `gated`). They describe that one game, so they
 * are fixed here rather than recounted from whatever game the carriage happens to play.
 */

/** The game all of this is from (the chips are its cast). */
export const UNDER_GAME = '9369a5c1-3c28-42ce-86a1-9d594dfa4804';

/** Seat 8 (a wolf) rewriting its note, one per day: `strategy_update` seqs 53, 151, 179, 294. */
export const NOTES = [
  {
    day: 1,
    tilt: '-1.2deg',
    text: 'Coordinate with my wolf ally to eliminate player_1 tonight as planned, removing a potential vocal village leader. Continue blending in with the village during the day and avoiding suspicious patterns.',
  },
  {
    day: 2,
    tilt: '.8deg',
    text: 'Blend in with the village majority and maintain a low profile. On Night 2, avoid attacking player_1 since they were saved by the healer, and target player_4 as agreed with my partner to secure a safe elimination.',
  },
  {
    day: 3,
    tilt: '-.6deg',
    text: "Maintain a low profile as the last surviving wolf after player_3's death. Blend in with the village's analysis of player_3's past interactions without drawing heat or manufacturing false leads.",
  },
  {
    day: 4,
    tilt: '1.1deg',
    text: 'Keep pushing to eliminate player_2, who is the confirmed serial killer, by highlighting their voting pattern. Blend in with the village consensus to ensure player_2 is voted out today. Protect my cover as a quiet, helpful villager.',
  },
] as const;

/** The seat whose notes are pinned: seat 8, the wolf. */
export const NOTE_SEAT = 8;

export type ReadMark = 'right' | 'side' | 'wrong' | 'none';
export const READ_MARKS: readonly ReadMark[] = ['right', 'side', 'wrong', 'none'];

/** Every read in the game, sorted by how sure the agent said it was and how it turned out. */
export const READS: Record<'sure' | 'unsure', Record<ReadMark, number>> = {
  sure: { right: 10, side: 0, wrong: 1, none: 0 },
  unsure: { right: 26, side: 11, wrong: 34, none: 247 },
};

/** Seat 1's line on day 4 that the novelty gate held back: `pass_marker` seq 342. */
export const HELD = {
  seat: 1,
  text: "player_8 points out player_2's voting record, and player_2 keeps trying to brush it off by talking about board states. If we look at Day 3, everyone except player_7 voted for player_6, but player_7 actually kicked off the push. We need to look closely at whether player_2 or player_7 is trying to hide their alignment behind this argument.",
};

/** Day 3: five lines in a row held back, the start of each: `pass_marker` seqs 183 to 215. */
export const DAY3_HELD: readonly [seat: number, start: string][] = [
  [7, "Player 2 and Player 8 are right to point at player_3's connections"],
  [9, "Building on player_8's point about player_3's voting"],
  [6, 'Building on what player_5 and player_8 discussed'],
  [2, 'Player 5 is right that looking at chat interactions'],
  [1, "Building on player_5 and player_8's point"],
];

/** The three brass plates: the number, what it counts, and its short name as a tab. */
export const PLATES = [
  { num: '77', cap: 'private notes in one game', tab: 'notes' },
  { num: '10 of 11', cap: 'sure reads were right', tab: 'sure & right' },
  { num: '6 of 12', cap: 'passes were the gate', tab: 'gated' },
] as const;
