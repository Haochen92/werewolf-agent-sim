/**
 * The hero's paper ticket (owner, 2026-10-18): cream card stock lying flat on the night scene,
 * its short ends scalloped and notched and a bite out of its top, a door into the game. The
 * shape is cut from the paper by a mask, so it stays round at any size; the paper's fibre is one
 * small tile (ticket-paper.webp) under both tickets. On a wide screen the printed kicker, the
 * title, the line and a rule ending in the way in; on a phone the title and the way in alone.
 */
import Link from 'next/link';
import type { ReactNode } from 'react';
import classes from './HeroTicket.module.css';

export function HeroTicket({
  href,
  kicker,
  title,
  children,
}: {
  href: string;
  /** The small printed line above the title, e.g. "Admit one". */
  kicker: string;
  title: string;
  /** The italic line under the title. */
  children: ReactNode;
}) {
  return (
    <Link href={href} className={classes.ticket}>
      <span className={classes.face}>
        <span className={classes.kicker}>{kicker}</span>
        <span className={classes.title}>{title}</span>
        <span className={classes.line}>{children}</span>
        <span className={classes.foot} aria-hidden="true">
          <span className={classes.go}>&rarr;</span>
        </span>
      </span>
    </Link>
  );
}
