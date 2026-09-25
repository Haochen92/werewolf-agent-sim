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
