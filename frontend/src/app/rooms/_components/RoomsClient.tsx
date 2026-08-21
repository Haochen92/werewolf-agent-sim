'use client';

/**
 * D5 — the rooms browser. Rows, not cards: a lobby list is SCANNED, and rows scale to many
 * rooms where cards stop working.
 *
 * Locked rooms render visible with the join disabled — locked is not hidden, mirroring the
 * server, which keeps the direct URL working past the browse TTL. Tapping a row expands it
 * inline to a name prompt rather than opening a modal, because this is mobile-first.
 */
import { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useMutation, useQuery } from '@tanstack/react-query';
import { joinGame, listRooms } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import { seatToken } from '@/lib/storage';
import { timeAgo } from '@/lib/format';
import type { RoomSummary } from '@/types/contracts';
import classes from '@/components/Lobby.module.css';
import page from '@/app/page.module.css';

export function RoomsClient() {
  const { data, isPending, error } = useQuery({
    queryKey: queryKeys.rooms.list(),
    queryFn: listRooms,
    refetchInterval: 10_000, // rooms fill up while you look at them
  });

  if (isPending) return <div className={page.skeletonCard} />;
  if (error) {
    return (
      <p role="alert" className={page.note}>
        Could not load rooms: {error.message}
      </p>
    );
  }

  if (data.length === 0) {
    return (
      <div>
        <p className={page.note}>No open tables right now.</p>
        <p className={classes.note}>
          <Link href="/rooms/new" className={classes.inlineLink}>
            Open one →
          </Link>
        </p>
      </div>
    );
  }

  return (
    <ul className={classes.roomList}>
      {data.map((room) => (
        <RoomRow key={room.game_id} room={room} />
      ))}
    </ul>
  );
}

function RoomRow({ room }: { room: RoomSummary }) {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [error, setError] = useState<string | null>(null);

  const full = room.players.length >= room.max_seats;
  const joinable = !room.locked && !full;

  const join = useMutation({
    mutationFn: () => joinGame(room.game_id, name.trim() || 'human'),
    onSuccess: (seat) => {
      seatToken.set(room.game_id, seat.token);
      router.push(`/games/${room.game_id}`);
    },
    // 409/410 (full, locked, started) arrive as words from the server; show them inline
    // and offer the spectate door as the consolation (D23).
    onError: (err) => setError(err instanceof Error ? err.message : 'Could not join.'),
  });

  return (
    <li className={classes.roomRow}>
      <button
        type="button"
        className={classes.roomHead}
        onClick={() =>
          joinable ? setOpen((v) => !v) : router.push(`/games/${room.game_id}`)
        }
      >
        <span className={classes.roomName}>
          {room.name || 'Unnamed table'} {room.locked ? '🔒' : ''}
        </span>
        <span className={classes.roomMeta}>
          {room.players.length}/{room.max_seats} · {timeAgo(room.created_at)}
        </span>
      </button>

      {open && joinable ? (
        <div className={classes.joinRow} style={{ marginTop: 'var(--space-3)' }}>
          <input
            className={classes.nameInput}
            placeholder="your name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            maxLength={24}
            autoFocus
          />
          <button
            type="button"
            className={classes.primary}
            onClick={() => join.mutate()}
            disabled={join.isPending}
          >
            Join
          </button>
        </div>
      ) : null}

      {!joinable ? (
        <p className={classes.note}>
          {room.locked ? 'Locked by the host.' : 'Full.'}{' '}
          <Link href={`/games/${room.game_id}`} className={classes.inlineLink}>
            Watch instead →
          </Link>
        </p>
      ) : null}

      {error ? (
        <p className={classes.error} role="alert">
          {error}{' '}
          <Link href={`/games/${room.game_id}`} className={classes.inlineLink}>
            Watch instead →
          </Link>
        </p>
      ) : null}
    </li>
  );
}
