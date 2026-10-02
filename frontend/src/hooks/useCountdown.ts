'use client';

/**
 * The AFK countdown (D18). Ticks locally off a server-issued ISO deadline.
 *
 * The clock delta matters: the deadline is the SERVER's wall clock, and a browser whose
 * clock is a minute fast would show a turn expiring while it is still perfectly live. The
 * offset is measured once from a status response and applied to every deadline after.
 *
 * Solo games send `deadline: null` — no timer, think forever — so a null deadline is a
 * first-class case, not an error.
 *
 * Two hooks, because two different things need the clock. The theatre only needs to know
 * when the turn runs out (`useCountdown`), and it re-renders the whole stage, so it wakes
 * once at the expiry rather than on every tick. The figures shown (`useTimeLeft`) tick, but
 * only in the small piece of text or bar that shows them.
 */
import { useEffect, useState } from 'react';

/** Server-minus-client milliseconds, measured once per session. */
let clockOffset = 0;

export function recordServerClock(serverIso: string | undefined | null): void {
  if (!serverIso) return;
  const server = Date.parse(serverIso);
  if (!Number.isNaN(server)) clockOffset = server - Date.now();
}

/** The server's wall clock as this browser best knows it, in ms. */
export function serverNow(): number {
  return Date.now() + clockOffset;
}

/** How often a shown count is redrawn, and how often the expiry is looked for (ms). */
const TICK_MS = 250;

/**
 * Milliseconds left to a deadline at server time `now`, floored at 0; null with no deadline
 * or one that does not parse.
 */
export function msLeft(deadline: string | null | undefined, now: number): number | null {
  if (!deadline) return null;
  const target = Date.parse(deadline);
  if (Number.isNaN(target)) return null;
  return Math.max(0, target - now);
}

export interface Countdown {
  expired: boolean;
}

/**
 * Whether the deadline has passed. The answer is worked out on every render, so a new
 * deadline is right at once; between renders the hook looks for the expiry on a timer and
 * asks for a render only when it comes, not on every tick.
 */
export function useCountdown(deadline: string | null): Countdown {
  const [, force] = useState(0);
  const expired = msLeft(deadline, serverNow()) === 0;

  useEffect(() => {
    if (!deadline || expired) return;
    const id = setInterval(() => {
      if (msLeft(deadline, serverNow()) === 0) force((n) => n + 1);
    }, TICK_MS);
    return () => clearInterval(id);
  }, [deadline, expired]);

  return { expired };
}

/**
 * The time left to a deadline in ms, ticking, for the piece that shows it; null with no
 * deadline. `at` holds the count still at that server time (the workbench's frames).
 */
export function useTimeLeft(
  deadline: string | null | undefined,
  at?: number,
): number | null {
  const [, force] = useState(0);
  const left = msLeft(deadline, at ?? serverNow());
  const running = left !== null && left > 0 && at === undefined;

  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => force((n) => n + 1), TICK_MS);
    return () => clearInterval(id);
  }, [running, deadline]);

  return left;
}
