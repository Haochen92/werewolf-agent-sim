'use client';

/**
 * D23: the game task died, shown by `/games/[id]` in place of the stage. Moved here from the
 * old lobby card when the waiting room became a stage scene (the platform); unchanged.
 */
import Link from 'next/link';
import classes from './Lobby.module.css';

/** D23: the game task died. No retry affordance — the server holds no way back. */
export function TerminalError({ message, byok }: { message: string; byok?: boolean }) {
  return (
    <div className={classes.wrap}>
      <div className={`${classes.card} ${classes.terminal}`}>
        <h1 className={classes.name}>This game has ended unexpectedly</h1>
        <p className={classes.note}>{message}</p>
        {byok ? (
          <p className={classes.note}>
            Games started with your own API key don’t survive a server restart — the key is
            never stored, which is exactly why.
          </p>
        ) : null}
        <Link href="/" className={classes.primary}>
          Back to the start
        </Link>
      </div>
    </div>
  );
}
