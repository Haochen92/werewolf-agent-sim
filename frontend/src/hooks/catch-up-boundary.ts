/**
 * Which events on the live stream are history and which are news (beat sheet §12). Only news
 * plays on the stage; history lands still.
 *
 * On the first connection the boundary is the status's `last_seq`, read just before the stream
 * opened: the stream sends the whole log first, and everything up to that seq is history.
 *
 * A reconnect is the other case. The browser reopens the stream by itself and tells the server
 * the last event it got, so the server sends only what was missed, then carries on. Those
 * missed events are newer than anything this page has, so the first boundary cannot catch
 * them. From the moment the stream drops until a fresh status says how far the log has got,
 * every event counts as history; after that, anything up to the status's `last_seq` does.
 */
export interface CatchUpBoundary {
  /** This seq arrived as history (catch-up), not as news. */
  isHistory: (seq: number) => boolean;
  /** The stream dropped and the browser is reconnecting. */
  dropped: () => void;
  /** A fresh status after the reopen: everything up to its `last_seq` is history. */
  resumed: (lastSeq: number) => void;
  /** Whether the stream is between a drop and its fresh status. */
  resuming: () => boolean;
}

export function catchUpBoundary(connectedAt: number): CatchUpBoundary {
  let through = connectedAt;
  let away = false;
  return {
    isHistory: (seq) => away || seq <= through,
    dropped: () => {
      away = true;
    },
    resumed: (lastSeq) => {
      through = Math.max(through, lastSeq);
      away = false;
    },
    resuming: () => away,
  };
}

/**
 * Whether to reopen the stream at once, now that the page is back (shown again, or online):
 * yes while it is not open, rather than wait on the browser's own retry, which backs off and
 * on a phone woken from sleep left a player two minutes behind (live testing 2026-10-11). An
 * open stream is left alone, and nothing reconnects while the page is hidden. `readyState` is
 * the EventSource's (0 connecting, 1 open, 2 closed).
 */
export function reopenNow(readyState: number, hidden: boolean): boolean {
  return !hidden && readyState !== 1;
}

/** How long the first held catch-up frame waits for those arriving behind it, in ms. */
export const CATCH_UP_GATHER_MS = 50;

export interface CatchUpBatch<E> {
  /** Hold one catch-up frame; the block goes on once the frames stop coming together. */
  add: (event: E) => void;
  /** Hand on what is held now: before news, so it never lands ahead of the history under it. */
  flush: () => void;
  /** Forget what is held (the stream is closed for good). */
  drop: () => void;
}

/**
 * Gathers the catch-up frames that arrive together and hands them on as one block. The stream
 * sends a game's history a frame at a time, and each frame on its own was a store write and a
 * render over the whole log so far: work that grows with the square of the game's length, so
 * a phone rejoining a long game froze. In blocks it is a handful of renders, each over the log.
 */
export function catchUpBatch<E>(
  apply: (events: E[]) => void,
  wait = CATCH_UP_GATHER_MS,
): CatchUpBatch<E> {
  let held: E[] = [];
  let timer: ReturnType<typeof setTimeout> | null = null;
  const flush = () => {
    if (timer) clearTimeout(timer);
    timer = null;
    if (held.length === 0) return;
    const block = held;
    held = [];
    apply(block);
  };
  return {
    add: (event) => {
      held.push(event);
      timer ??= setTimeout(flush, wait);
    },
    flush,
    drop: () => {
      if (timer) clearTimeout(timer);
      timer = null;
      held = [];
    },
  };
}
