'use client';

/**
 * D23: the game task died, shown by `/games/[id]` in place of the stage. Moved here from the
 * old lobby card when the waiting room became a stage scene (the platform). A game stopped by
 * a refused key (`error_kind: "key_rejected"`) gets its own card: the server's message names
 * the provider and its reason, and the way on is a new game, not the restart note.
 */
import Link from 'next/link';
import type { ReactNode } from 'react';
import { Anchor } from '@mantine/core';
import { Button } from '@/components/site';
import classes from './Lobby.module.css';

/** D23: the game task died. No retry affordance — the server holds no way back. */
export function TerminalError({
  message,
  byok,
  kind,
}: {
  message: string;
  byok?: boolean;
  kind?: 'key_rejected' | null;
}) {
  if (kind === 'key_rejected') return <KeyRejectedCard message={message} />;
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
        <div className={classes.ways}>
          <Button component={Link} href="/" variant="plate">
            Back to the start
          </Button>
        </div>
      </div>
    </div>
  );
}

/**
 * The provider refused the game's key mid-game, live or archived (`GameEndedCard`).
 * `children` go under the title (the archived card's "You played as …").
 */
export function KeyRejectedCard({
  message,
  children,
}: {
  message: string;
  children?: ReactNode;
}) {
  return (
    <div className={classes.wrap}>
      <div className={`${classes.card} ${classes.terminal}`}>
        <h1 className={classes.name}>Your key stopped working</h1>
        {children}
        <p className={classes.note}>
          {message} The agents can’t play without it, so the game stopped there.
        </p>
        <p className={classes.note}>
          Common causes: the key was revoked, its credit ran out, or it belongs to another
          company.
        </p>
        <div className={classes.ways}>
          <Button component={Link} href="/play" variant="plate">
            Start a new game
          </Button>
          <Anchor component={Link} href="/">
            Back to the start
          </Anchor>
        </div>
      </div>
    </div>
  );
}
