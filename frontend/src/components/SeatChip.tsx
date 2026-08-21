'use client';

import Image from 'next/image';
import { hueFor, initialsFor, portraitFor } from '@/assets/manifest';
import { humanise } from '@/lib/format';
import { RoleIcon } from './RoleIcon';
import classes from './SeatChip.module.css';

export interface SeatChipProps {
  seat: string;
  /** Shown only where the viewer is entitled to it — pass undefined and no badge renders. */
  role?: string;
  dead?: boolean;
  isSelf?: boolean;
  size?: 'sm' | 'lg';
  onClick?: () => void;
}

/**
 * The seat's visual identity, used everywhere a player is named: roster, speech bubbles,
 * vote chips, death notices. One component so a death desaturates the seat in every one of
 * those places at once.
 *
 * Portrait or initials is decided by the manifest, not here: while `portraits/` is empty
 * every chip falls back to initials on the seat's deterministic hue, and the day art lands
 * this file does not change.
 */
export function SeatChip({
  seat,
  role,
  dead = false,
  isSelf = false,
  size = 'sm',
  onClick,
}: SeatChipProps) {
  const portrait = portraitFor(seat);
  const dimension = size === 'lg' ? 34 : 22;

  const roleClass =
    role === 'wolf' ? classes.wolfRole : role === 'serial_killer' ? classes.skRole : '';

  const body = (
    <>
      {portrait ? (
        <Image
          className={classes.avatar}
          src={portrait}
          alt=""
          width={dimension}
          height={dimension}
        />
      ) : (
        <span
          className={classes.avatar}
          style={{ background: `hsl(${hueFor(seat)} 38% 62%)` }}
          aria-hidden="true"
        >
          {initialsFor(seat)}
        </span>
      )}
      <span className={classes.name}>{seat}</span>
      {isSelf ? <span className={classes.selfTag}>you</span> : null}
      {role ? (
        <span className={`${classes.role} ${classes.roleXray} ${roleClass}`}>
          <RoleIcon role={role} />
          {humanise(role)}
        </span>
      ) : null}
    </>
  );

  const className = [
    classes.chip,
    size === 'lg' ? classes.large : '',
    dead ? classes.dead : '',
    isSelf ? classes.self : '',
    onClick ? classes.interactive : '',
  ]
    .filter(Boolean)
    .join(' ');

  if (onClick) {
    return (
      <button type="button" className={className} onClick={onClick}>
        {body}
      </button>
    );
  }
  return <span className={className}>{body}</span>;
}
