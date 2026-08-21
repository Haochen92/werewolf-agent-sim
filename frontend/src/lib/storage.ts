/**
 * The complete client-side persistence surface (build_plan §5). All of it is device-local
 * — the server never reads any of these. One module owns the key names so the inventory
 * stays checkable against the plan's table.
 *
 * SSR-safe: every accessor no-ops when `window` is absent, so these can be called from
 * component bodies that also render on the server.
 */

const KEYS = {
  seat: (gameId: string) => `seat_${gameId}`,
  host: (gameId: string) => `host_${gameId}`,
  byok: 'byok_key',
  ghost: (gameId: string) => `ghost_${gameId}`,
} as const;

function read(key: string): string | null {
  if (typeof window === 'undefined') return null;
  try {
    return window.localStorage.getItem(key);
  } catch {
    // Private-mode / disabled storage: the app degrades, it does not crash.
    return null;
  }
}

function write(key: string, value: string): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.setItem(key, value);
  } catch {
    /* quota or disabled storage — nothing here is load-bearing */
  }
}

function remove(key: string): void {
  if (typeof window === 'undefined') return;
  try {
    window.localStorage.removeItem(key);
  } catch {
    /* see above */
  }
}

/** Seat-token backup for the HttpOnly cookie; the input to the rejoin flow after 403. */
export const seatToken = {
  get: (gameId: string) => read(KEYS.seat(gameId)),
  set: (gameId: string, token: string) => write(KEYS.seat(gameId), token),
  clear: (gameId: string) => remove(KEYS.seat(gameId)),
};

/** Room creator's host_key — returned only once by POST /rooms; used only by /start. */
export const hostKey = {
  get: (gameId: string) => read(KEYS.host(gameId)),
  set: (gameId: string, key: string) => write(KEYS.host(gameId), key),
  clear: (gameId: string) => remove(KEYS.host(gameId)),
};

/**
 * BYOK key, OPT-IN only: never written unless the player ticks "remember on this device".
 * The key's only wire appearance is the create-request body — the server never stores it.
 */
export const byokKey = {
  get: () => read(KEYS.byok),
  set: (key: string) => write(KEYS.byok, key),
  clear: () => remove(KEYS.byok),
};

/** Ghost-mode guesses, keyed by phase within a game. Never cleared — it is the player's own record. */
export const ghostGuesses = {
  get: (gameId: string): Record<string, string> => {
    const raw = read(KEYS.ghost(gameId));
    if (!raw) return {};
    try {
      const parsed: unknown = JSON.parse(raw);
      return parsed && typeof parsed === 'object' ? (parsed as Record<string, string>) : {};
    } catch {
      return {};
    }
  },
  set: (gameId: string, guesses: Record<string, string>) =>
    write(KEYS.ghost(gameId), JSON.stringify(guesses)),
};
