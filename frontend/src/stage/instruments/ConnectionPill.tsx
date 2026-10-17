'use client';

/**
 * The connection pill under the stage's top strip (owner, 2026-10-17, board 3): a pulsing amber
 * dot and "Reconnecting…" while the stream comes back; after `BLIP_MS` still down, or with the
 * browser offline, a grey dot, "You’re offline." and "Try now", which reopens the stream at
 * once instead of waiting on the next retry. What follows the words says whether the game
 * waits (a game for one) or the seat's clock runs (a room). Words in `connection-pill.ts`.
 */
import { useEffect, useState, useSyncExternalStore } from 'react';
import type { ConnectionState } from '@/game/store';
import { BLIP_MS } from '@/hooks/catch-up-boundary';
import { pillLine, pillState, type PillTable } from './connection-pill';
import styles from './ConnectionPill.module.css';

const onLineChange = (then: () => void) => {
  window.addEventListener('online', then);
  window.addEventListener('offline', then);
  return () => {
    window.removeEventListener('online', then);
    window.removeEventListener('offline', then);
  };
};

/** The browser's word on the network; online until it says otherwise. */
function useOnline(): boolean {
  return useSyncExternalStore(
    onLineChange,
    () => navigator.onLine,
    () => true,
  );
}

export function ConnectionPill({
  connection,
  table,
  onRetry,
}: {
  connection: ConnectionState;
  table: PillTable;
  /** "Try now": reopen the stream at once. */
  onRetry?: () => void;
}) {
  const online = useOnline();
  const down = connection === 'reconnecting' || (!online && connection !== 'idle');
  // mounted per drop, so each one counts its 20 s from its own start
  return down ? (
    <Pill connection={connection} online={online} table={table} onRetry={onRetry} />
  ) : null;
}

function Pill({
  connection,
  online,
  table,
  onRetry,
}: {
  connection: ConnectionState;
  online: boolean;
  table: PillTable;
  onRetry?: () => void;
}) {
  const [long, setLong] = useState(false);
  // a press of "Try now" starts the count again: the pill says it is reconnecting
  const [tries, setTries] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setLong(true), BLIP_MS);
    return () => clearTimeout(t);
  }, [tries]);
  const state = pillState(connection, online, long);
  if (!state) return null;
  return (
    <div className={styles.pill} role="status" data-connection={state}>
      <i className={styles.dot} data-state={state} aria-hidden="true" />
      <span>{pillLine(state, table)}</span>
      {state === 'offline' && onRetry ? (
        <button
          type="button"
          className={styles.retry}
          onClick={() => {
            setLong(false);
            setTries((n) => n + 1);
            onRetry();
          }}
        >
          Try now
        </button>
      ) : null}
    </div>
  );
}
