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
