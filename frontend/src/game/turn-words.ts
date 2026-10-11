/**
 * The server's words for a turn that chooses no seat. A night request lists one among its
 * candidates when the turn may be passed ("hold fire", "keep the sigil"); the dock offers it as
 * the turn's "no one", and the night room's plate names it.
 */

/**
 * The no-action words the server may list among the candidates (ten-seat pass §1): never
 * guessed, only taken when the request lists one.
 */
export const NO_ACTION = [
  'hold_fire',
  'no_check',
  'no_watch',
  'keep_sigil',
  'no_conceal',
  'stay_put',
  'not_yet',
  'abstain',
] as const;

/** The request's no-action word, or null when it lists none (the turn has no "no one"). */
export function noActionWord(candidates: readonly string[]): string | null {
  return candidates.find((c) => (NO_ACTION as readonly string[]).includes(c)) ?? null;
}
