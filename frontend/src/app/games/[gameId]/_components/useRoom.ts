'use client';

/**
 * The waiting room as the platform draws it (`RoomInput`), and the presses on its ledge.
 * A room has no event stream: everything here is the status poll's `waiting` answer (the
 * roster, the lock, the host's name, and where this viewer stands on the roster) plus what this
 * device holds (the host key, a seat token). Lock, Close and Depart go to the server from here,
 * with the host key; the scene only reports them.
 *
 * Depart spends the host key (it has exactly one use), so once it has gone through the room
 * says `departed` and the train leaves at once, without waiting for the next poll. Close and
 * Leave end this device's part in the room: its host key and seat token go, and the page goes
 * back to the room list. A watcher's Leave only goes back.
 */
import { useCallback, useMemo, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { closeRoom, leaveRoom, lockRoom, startGame } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import { hostKey, seatToken } from '@/lib/storage';
import { MIN_ABOARD } from '@/stage/scenes/station';
import type { RoomAct, RoomInput } from '@/stage/scenes/types';
import type { GameStatus } from '@/types/contracts';

export interface Room {
  /** The platform's input while the status says `waiting`; undefined otherwise. */
  room: RoomInput | undefined;
  /** Depart went through: the game is starting. */
  departed: boolean;
  onRoomAct: (act: RoomAct) => void;
  /** The boarding pass went through: this device now holds a seat. */
  boarded: () => void;
}

export function useRoom(gameId: string, status: GameStatus | undefined): Room {
  const queryClient = useQueryClient();
  const router = useRouter();
  const [busy, setBusy] = useState<RoomAct | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [departed, setDeparted] = useState(false);
  const [joined, setJoined] = useState(false);

  // read on every render: joining sets the seat token, Depart clears the host key
  const key = hostKey.get(gameId);
  const seated = joined || Boolean(seatToken.get(gameId));
  const waiting = status?.state === 'waiting' ? status : null;

  const onRoomAct = useCallback(
    (act: RoomAct) => {
      if (busy) return;
      // leaving needs no key: a watcher just goes, a guest gives up the seat first
      if (act === 'leave') {
        const seat = Boolean(seatToken.get(gameId));
        setBusy(act);
        setError(null);
        (seat ? leaveRoom(gameId) : Promise.resolve())
          .then(() => {
            seatToken.clear(gameId);
            router.push('/rooms');
          })
          .catch((err: unknown) => {
            setError(err instanceof Error ? err.message : 'Could not leave.');
            setBusy(null);
          });
        return;
      }
      if (!key) return;
      if (act === 'close') {
        setBusy(act);
        setError(null);
        closeRoom(gameId, key)
          .then(() => {
            hostKey.clear(gameId);
            seatToken.clear(gameId);
            router.push('/rooms');
          })
          .catch((err: unknown) => {
            setError(err instanceof Error ? err.message : 'Could not close the room.');
            setBusy(null);
          });
        return;
      }
      setBusy(act);
      setError(null);
      const call =
        act === 'depart'
          ? startGame(gameId, key).then(() => {
              // host_key has exactly one use and it is spent; keeping it invites confusion later
              hostKey.clear(gameId);
              setDeparted(true);
            })
          : lockRoom(gameId, act === 'lock', key);
      call
        .catch((err: unknown) => {
          const fallback =
            act === 'depart' ? 'Could not depart.' : 'Could not change the lock.';
          setError(err instanceof Error ? err.message : fallback);
        })
        .finally(() => {
          setBusy(null);
          void queryClient.invalidateQueries({ queryKey: queryKeys.games.status(gameId) });
        });
    },
    [busy, key, gameId, queryClient, router],
  );

  const room = useMemo((): RoomInput | undefined => {
    if (!waiting) return undefined;
    const aboard = waiting.players ?? [];
    // the server's word, from the seat cookie: names can repeat, a place on the roster cannot
    const you = waiting.you_aboard ?? null;
    return {
      name: waiting.name,
      aboard,
      places: waiting.max_seats || 10,
      host: waiting.host ?? null,
      locked: waiting.locked,
      isHost: Boolean(key),
      seated,
      you: you !== null && you < aboard.length ? you : null,
      minAboard: MIN_ABOARD,
      link:
        typeof window === 'undefined' ? '' : `${window.location.origin}/games/${gameId}`,
      busy,
      error,
    };
  }, [waiting, key, seated, gameId, busy, error]);

  const boarded = useCallback(() => setJoined(true), []);
  return { room, departed, onRoomAct, boarded };
}
