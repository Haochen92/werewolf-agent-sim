/**
 * Display formatting. Native `Intl` only — the stack ruling skips dayjs/date-fns, and
 * nothing here needs more than they'd provide.
 */

const RELATIVE = new Intl.RelativeTimeFormat('en', { numeric: 'auto' });

const UNITS: [Intl.RelativeTimeFormatUnit, number][] = [
  ['year', 365 * 24 * 3600],
  ['month', 30 * 24 * 3600],
  ['day', 24 * 3600],
  ['hour', 3600],
  ['minute', 60],
  ['second', 1],
];

/** "3 days ago" from an ISO timestamp. Empty string for a missing one — never "Invalid Date". */
export function timeAgo(iso: string | null | undefined): string {
  if (!iso) return '';
  const then = Date.parse(iso);
  if (Number.isNaN(then)) return '';
  const deltaSeconds = (then - Date.now()) / 1000;
  for (const [unit, size] of UNITS) {
    if (Math.abs(deltaSeconds) >= size || unit === 'second') {
      return RELATIVE.format(Math.round(deltaSeconds / size), unit);
    }
  }
  return '';
}

/** "wolf" → "Wolf", "serial_killer" → "Serial killer". */
export function humanise(value: string): string {
  const spaced = value.replace(/_/g, ' ');
  return spaced.charAt(0).toUpperCase() + spaced.slice(1);
}

/** "2 wolves · 1 healer · 3 villagers" from the cast census. */
export function describeCast(counts: Record<string, number>): string {
  return Object.entries(counts)
    .sort(([, a], [, b]) => b - a)
    .map(([role, n]) => `${n} ${n === 1 ? humanise(role).toLowerCase() : pluralise(role)}`)
    .join(' · ');
}

function pluralise(role: string): string {
  const word = role.replace(/_/g, ' ');
  if (word.endsWith('f')) return `${word.slice(0, -1)}ves`; // wolf → wolves
  return `${word}s`;
}

// spelled out rather than Intl's en-GB, whose September is "Sep" or "Sept" by ICU version
const MONTHS = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
];

/** "17 Sep 2026" from an ISO timestamp, read in UTC so every viewer sees the same day. */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '';
  const then = new Date(iso);
  if (Number.isNaN(then.getTime())) return '';
  return `${then.getUTCDate()} ${MONTHS[then.getUTCMonth()]} ${then.getUTCFullYear()}`;
}

/**
 * The phase a finished game ended in, with its day: "Night 4", "Day 3", or "Day 5 vote" for a
 * game the lynch ended. Null when the archive did not record it (games before the column).
 */
export function endedLabel(
  phase: 'day' | 'voting' | 'night' | null | undefined,
  day: number,
): string | null {
  if (phase === 'night') return `Night ${day}`;
  if (phase === 'day') return `Day ${day}`;
  if (phase === 'voting') return `Day ${day} vote`;
  return null;
}

/** A game's cost in dollars: "$0.27", or "<$0.01" for a sliver. Empty when it is unknown. */
export function formatCost(usd: number | null | undefined): string {
  if (usd == null) return '';
  return usd < 0.01 ? '<$0.01' : `$${usd.toFixed(2)}`;
}

/** A mean model-call time: "4.1 s", or "12 s" from ten seconds up. Empty when it is unknown. */
export function formatCallSeconds(seconds: number | null | undefined): string {
  if (seconds == null) return '';
  return seconds < 10 ? `${seconds.toFixed(1)} s` : `${Math.round(seconds)} s`;
}
