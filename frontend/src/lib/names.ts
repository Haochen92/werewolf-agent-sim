/**
 * A player's name, as the server takes it (`JoinGame.name` in server/schemas/requests.py):
 * spaces trimmed and collapsed, at most 12 characters, of letters in any script, digits,
 * spaces and the marks names use (- ' .). The boxes check it as it is typed, so a name the
 * server would refuse never leaves the page; the server checks again.
 */

/** The longest name, what a platform name tag holds at full size (server `MAX_PLAYER_NAME`). */
export const MAX_NAME = 12;

const ALLOWED = /^[\p{L}\p{M}\p{N} \-'.’]$/u;

/** The name as it will be sent and shown: trimmed, one space between words. */
export function tidyName(raw: string): string {
  return raw.trim().split(/\s+/).filter(Boolean).join(' ');
}

/** Why this name cannot board, or null when it can. Characters count as the server counts them. */
export function nameProblem(raw: string): string | null {
  const chars = [...tidyName(raw)];
  if (chars.length === 0) return 'A name is needed.';
  if (chars.length > MAX_NAME) return `At most ${MAX_NAME} characters.`;
  const bad = [...new Set(chars.filter((c) => !ALLOWED.test(c)))];
  if (bad.length) return `Letters, digits, spaces and - ' . only (not ${bad.join(' ')}).`;
  return null;
}
