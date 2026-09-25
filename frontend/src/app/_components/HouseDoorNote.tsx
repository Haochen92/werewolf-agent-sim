'use client';

/**
 * What a playing door costs, said on the landing page rather than two clicks in.
 *
 * The house pays for a fixed number of games a day (server/house.py), so whether a
 * visitor needs their own API key is live state, not a constant. Before this note a
 * visitor with no key could pick a door, fill in the whole setup form, and only then be
 * told the purse was empty — a dead end that is invisible for testing whenever the purse
 * happens to be full. It reads the same GET /models the setup form reads and trusts the
 * server's own `needs_key` rather than re-deriving who pays.
 */
import { useQuery } from '@tanstack/react-query';
import { getModels } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import type { ModelsMenu } from '@/types/contracts';
import classes from '@/app/page.module.css';

function houseNote(menu: ModelsMenu): { text: string; free: boolean } | null {
  // The door promises nothing about a model the visitor has not chosen yet, so it speaks
  // for the row they would actually get: the live default.
  const row = menu.models.find((r) => r.is_default) ?? menu.models[0];
  if (!row) return null;

  const { enabled, remaining, games_per_day, reset_at } = menu.house;
  if (!row.needs_key) {
    return {
      text: `Free right now · ${remaining} of ${games_per_day} games left today`,
      free: true,
    };
  }
  if (!row.house_funded || !enabled) {
    return { text: 'Bring your own API key', free: false };
  }
  const at = new Date(reset_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  return { text: `Today's free games are spent — bring a key, or return at ${at}`, free: false };
}

export function HouseDoorNote() {
  const { data: menu } = useQuery({
    queryKey: queryKeys.models(),
    queryFn: getModels,
    staleTime: 30_000, // the purse moves as games start; the menu itself is static
  });

  // Nothing is claimed until the server has said it — a door that guessed "free" and was
  // wrong would be the same dead end, one step earlier. The blank holds the line's height
  // so the doors do not jump when the answer lands.
  const note = menu ? houseNote(menu) : null;
  return (
    <p className={`${classes.doorNote} ${note?.free ? classes.doorNoteFree : ''}`}>
      {note ? note.text : ' '}
    </p>
  );
}
