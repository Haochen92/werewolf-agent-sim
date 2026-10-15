'use client';

/**
 * What a game's URL shows once the game has ended and left the server's live registry.
 * The status poll then answers from the database row (`archived: true`): enough to say
 * how the game ended and, for a finished one, to point at its replay under the same id.
 * There is no stream to open, so this card is the whole page. Not a redirect: someone
 * who followed a link should see where they landed and why.
 */
import Link from 'next/link';
import { Anchor } from '@mantine/core';
import { Button } from '@/components/site';
import type { GameStatus } from '@/types/contracts';
import { humanise } from '@/lib/format';
import { WINNER_NAME } from '@/stage/roles';
import classes from './Lobby.module.css';

export function GameEndedCard({ gameId, status }: { gameId: string; status: GameStatus }) {
  const finished = status.state === 'finished';
  return (
    <div className={classes.wrap}>
      <div className={`${classes.card} ${finished ? '' : classes.terminal}`}>
        <h1 className={classes.name}>
          {finished ? 'This game has finished' : 'This game was dropped'}
        </h1>
        {finished && status.winner ? (
          <p className={classes.note}>Winner: {WINNER_NAME[status.winner]}</p>
        ) : null}
        {status.you ? <p className={classes.note}>You played as {humanise(status.you)}.</p> : null}
        {!finished && status.error ? <p className={classes.note}>{status.error}</p> : null}
        <div className={classes.ways}>
          {finished ? (
            <>
              <Button component={Link} href={`/replays/${gameId}`} variant="plate">
                Watch the replay
              </Button>
              <Anchor component={Link} href="/">
                Back to the start
              </Anchor>
            </>
          ) : (
            <Button component={Link} href="/" variant="plate">
              Back to the start
            </Button>
          )}
        </div>
      </div>
    </div>
  );
}
