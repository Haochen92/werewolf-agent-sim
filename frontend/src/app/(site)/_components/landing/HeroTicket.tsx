/**
 * The hero's paper ticket (owner, 2026-10-18): cream card stock lying flat on the night scene,
 * its short ends scalloped and notched and a bite out of its top, a door into the game. The
 * shape is cut from the paper by a mask, so it stays round at any size; the paper's fibre is one
 * small tile (ticket-paper.webp) under both tickets. On a wide screen the printed kicker, the
 * line and a ruled foot; on a phone the title and the way in alone, with `note` (a live line,
 * such as the tables boarding) under the title when there is one.
 */
import Link from 'next/link';
import type { ReactNode } from 'react';
import classes from './HeroTicket.module.css';

export function HeroTicket({
  href,
  kicker,
  title,
  children,
  foot,
  note,
}: {
  href: string;
  /** The small printed line above the title, e.g. "Admit one". */
  kicker: string;
  title: string;
  /** The italic line under the title. */
  children: ReactNode;
  /** The ruled foot's left side (the arrow is its right). */
  foot?: ReactNode;
  /** A live line for the phone's ticket, under its title. */
  note?: ReactNode;
}) {
  return (
    <Link href={href} className={classes.ticket}>
      <span className={classes.face}>
        <span className={classes.kicker}>{kicker}</span>
        <span className={classes.title}>{title}</span>
        <span className={classes.line}>{children}</span>
        {note ? <span className={classes.note}>{note}</span> : null}
        <span className={classes.foot}>
          <span>{foot}</span>
          <span className={classes.go} aria-hidden="true">
            &rarr;
          </span>
        </span>
      </span>
    </Link>
  );
}
