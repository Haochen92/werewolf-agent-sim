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
 */
import { useEffect, useState } from 'react';

/** Server-minus-client milliseconds, measured once per session. */
let clockOffset = 0;

export function recordServerClock(serverIso: string | undefined | null): void {
  if (!serverIso) return;
  const server = Date.parse(serverIso);
  if (!Number.isNaN(server)) clockOffset = server - Date.now();
}

export interface Countdown {
  /** Whole seconds left, floored at 0. Null when there is no deadline. */
  secondsLeft: number | null;
  /** 1 → just issued, 0 → expired. Null when there is no deadline. */
  fraction: number | null;
  expired: boolean;
}

export function useCountdown(deadline: string | null, windowSeconds = 60): Countdown {
  const [, force] = useState(0);

  useEffect(() => {
    if (!deadline) return;
    const id = setInterval(() => force((n) => n + 1), 250);
    return () => clearInterval(id);
  }, [deadline]);

  if (!deadline) return { secondsLeft: null, fraction: null, expired: false };

  const target = Date.parse(deadline);
  if (Number.isNaN(target)) return { secondsLeft: null, fraction: null, expired: false };

  const msLeft = target - (Date.now() + clockOffset);
  const secondsLeft = Math.max(0, Math.ceil(msLeft / 1000));
  const fraction = Math.max(0, Math.min(1, msLeft / (windowSeconds * 1000)));
  return { secondsLeft, fraction, expired: msLeft <= 0 };
}
