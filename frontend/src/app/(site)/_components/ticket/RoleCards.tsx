/**
 * The solo ticket's role choice (ticket-office mockup, "Your role"): the only cards on the
 * page, because cards mean roles. Face down is "dealt at random"; each face carries the role's
 * sigil, its name and the role kit's felt figure, banded in its faction's colour. The note under
 * the row says what the chosen role does at night, in the card's own words (`CARD_TEXT`).
 *
 * Solo only: rooms always deal at random (`NewRoom` has no role field), so the room ticket
 * never renders this.
 */
import { CARD_TEXT } from '@/stage/card-text';
import { roleFigure } from '@/stage/paint/role-kit';
import { factionOf } from '@/stage/roles';
import { BackArt } from '@/stage/instruments/CardBackArt';
import { Sigil } from '@/stage/instruments/Sigil';
import type { Role } from '@/types/contracts';
import classes from './Ticket.module.css';

/** The castable roles, in the mockup's order: the town's four, then the two killers. */
export const ROLES: Role[] = [
  'villager',
  'healer',
  'investigator',
  'vigilante',
  'wolf',
  'serial_killer',
];

export function RoleCards({
  value,
  onChange,
  labelledBy,
}: {
  value: Role | null;
  onChange: (role: Role | null) => void;
  labelledBy: string;
}) {
  const text = value ? CARD_TEXT[value] : null;
  return (
    <>
      <div className={classes.cards} role="group" aria-labelledby={labelledBy}>
        <button
          type="button"
          className={`${classes.card} ${classes.cardBack}`}
          aria-pressed={value === null}
          onClick={() => onChange(null)}
        >
          <span className={classes.cardIn}>
            <span className={classes.backArt}>
              <BackArt />
            </span>
            <span className={classes.backWords}>
              Dealt at
              <br />
              random
            </span>
          </span>
        </button>
        {ROLES.map((role) => (
          <button
            key={role}
            type="button"
            className={classes.card}
            data-faction={factionOf(role) ?? undefined}
            aria-pressed={value === role}
            onClick={() => onChange(role)}
          >
            <span className={classes.cardIn}>
              <span className={classes.cardHead}>
                <Sigil role={role} strokeWidth={3.2} className={classes.cardSigil} />
                {CARD_TEXT[role].name}
              </span>
              <span
                className={classes.cardFig}
                aria-hidden="true"
                dangerouslySetInnerHTML={{ __html: roleFigure(role) }}
              />
            </span>
          </button>
        ))}
      </div>
      <p className={classes.roleNote} aria-live="polite">
        {text ? (
          <>
            <b>{text.name}.</b> {text.night}
            {value === 'wolf' ? ' Your packmate will be an agent.' : ''}
          </>
        ) : (
          <>
            <b>Dealt at random</b>, like everyone else&rsquo;s, from the usual cast of nine.
          </>
        )}
      </p>
    </>
  );
}
