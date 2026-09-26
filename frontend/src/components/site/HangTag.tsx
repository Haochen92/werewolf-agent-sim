/**
 * The hung paper tag (the mockups' `.hang`): a luggage tag on a string, a punched hole, a
 * printed kicker, title and line, and a rule with a footer. Used as a door (a link) on the
 * landing and rooms pages, and as a choice (a pressed button) on the ticket office.
 *
 * Tags tilt alternately while hung; below 700px they hang flat, full width, string hidden.
 */
import Link from 'next/link';
import type { ReactNode } from 'react';
import classes from './HangTag.module.css';

interface HangTagBase {
  /** The small printed line above the title, e.g. "Admit one". */
  kicker: ReactNode;
  title: ReactNode;
  /** The italic line under the title. */
  children?: ReactNode;
  /** The ruled footer: left and right. */
  foot?: [ReactNode, ReactNode?];
  className?: string;
}

type HangTagProps = HangTagBase &
  (
    | { href: string; onClick?: never; pressed?: never }
    | { href?: never; onClick: () => void; pressed?: boolean }
  );

export function HangTag({
  kicker,
  title,
  children,
  foot,
  className,
  ...action
}: HangTagProps) {
  const face = (
    <>
      <span className={classes.string} aria-hidden="true" />
      <span className={classes.hole} aria-hidden="true" />
      <span className={classes.face}>
        <span className={classes.kicker}>{kicker}</span>
        <span className={classes.title}>{title}</span>
        {children ? <span className={classes.line}>{children}</span> : null}
        {foot ? (
          <span className={classes.foot}>
            <span>{foot[0]}</span>
            {foot[1] !== undefined ? (
              <span className={classes.footRight}>{foot[1]}</span>
            ) : null}
          </span>
        ) : null}
      </span>
    </>
  );
  const cls = className ? `${classes.hang} ${className}` : classes.hang;

  if (action.href !== undefined) {
    return (
      <Link href={action.href} className={cls}>
        {face}
      </Link>
    );
  }
  return (
    <button
      type="button"
      className={cls}
      onClick={action.onClick}
      aria-pressed={action.pressed}
    >
      {face}
    </button>
  );
}
