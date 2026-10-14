'use client';

/**
 * The solo ticket's role choice. Nothing chosen deals the role at random, like every other seat;
 * a second click on the chosen role clears it. On a desktop the roles are cards (sigil, name,
 * felt figure, banded in the side's colour) on one six-column grid: the town's six, then the
 * pack's two, the lone killers and the neutrals. On a phone they are sigils grouped under their
 * sides' badges, and the chosen role (`RolePreview`) shows under them; a desktop shows it on the
 * stub. The cards are radio groups: the arrow keys move the choice, as the landing's picker does.
 *
 * The ticket's line for each role is its own (`TICKET_LINE`), a sentence long: the card, the
 * guide and the landing carry the full briefing.
 *
 * Solo only: rooms always deal at random (`NewRoom` has no role field).
 */
import type { KeyboardEvent } from 'react';
import { VisuallyHidden } from '@mantine/core';
import { CARD_TEXT } from '@/stage/card-text';
import { roleFigure } from '@/stage/paint/role-kit';
import { FACTION_NAME, factionOf } from '@/stage/roles';
import { FactionMark } from '@/stage/instruments/FactionMark';
import { Sigil } from '@/stage/instruments/Sigil';
import type { PoolRole } from '@/types/contracts';
import { ARROW_STEP, ROLES, SIDES } from '../sides';
import classes from './Ticket.module.css';

/** What each role does, in one sentence, as the ticket says it. */
const TICKET_LINE: Record<PoolRole, string> = {
  investigator:
    'Twice a game, check a player at night: wolves read suspicious, and so does the necromancer on a night it attacks.',
  sentinel: 'Twice a game, watch a player’s door and learn by morning who visited them.',
  trailseer: 'Each night, follow one player and learn whose door they went to.',
  vigilante: 'You have two bullets for the game. On any night, you may shoot one player.',
  sigilist:
    'Twice a game, mark a player. If they kill that night, your sigil strikes them back.',
  healer: 'Each night, protect one other player from being killed.',
  chanteuse:
    'Choose the kill with your packmate, then enchant one player so they can’t act that night. Your packmate will be an agent.',
  illusionist:
    'Choose the kill with your packmate. Twice a game, conceal your victim completely.',
  serial_killer: 'Kill one player each night. Nothing can kill you at night.',
  necromancer: 'From night 2, borrow a dead player’s night power and use it on anyone.',
  speculator:
    'Bet on which side will win, any night you like. Back the winner and you win, alive or dead.',
  fortune_teller: 'Each night, bet on who dies. Two points and you win, alive or dead.',
};

/** A plain felt doll in the paper's own tone: no role yet, so no costume and no prop. */
function BlankDoll() {
  return (
    <svg className={classes.blankDoll} viewBox="0 0 120 160" aria-hidden="true">
      <ellipse cx="22" cy="98" rx="11" ry="15" transform="rotate(-28 22 98)" />
      <ellipse cx="98" cy="98" rx="11" ry="15" transform="rotate(28 98 98)" />
      <path d="M33 76C40 66 80 66 87 76L103 146C82 157 38 157 17 146Z" />
      <circle cx="60" cy="45" r="33" />
    </svg>
  );
}

/**
 * The role being held, as the ticket prints it: the doll, then side mark, name and role sigil
 * on one line, then the ticket's line for it and the way back to a random deal. With nothing
 * chosen, the blank doll and "Dealt at random". `place` picks where it shows: the stub on a
 * desktop, under the picker on a phone.
 */
export function RolePreview({
  role,
  onClear,
  place,
}: {
  role: PoolRole | null;
  onClear: () => void;
  place: 'stub' | 'field';
}) {
  const faction = role ? factionOf(role) : null;
  return (
    <div className={classes.preview} data-place={place} aria-live="polite">
      <span className={classes.previewDoll}>
        {role ? (
          <span
            key={role}
            className={classes.previewFigure}
            dangerouslySetInnerHTML={{ __html: roleFigure(role) }}
          />
        ) : (
          <BlankDoll />
        )}
      </span>
      {role && faction ? (
        <>
          <span className={classes.previewHead} data-faction={faction}>
            <FactionMark faction={faction} format="mark" className={classes.previewMark} />
            <span className={classes.previewName}>{CARD_TEXT[role].name}</span>
            <Sigil role={role} className={classes.previewSigil} />
            <VisuallyHidden>, {FACTION_NAME[faction]}</VisuallyHidden>
          </span>
          <span className={classes.previewLine}>{TICKET_LINE[role]}</span>
          <button type="button" className={classes.previewClear} onClick={onClear}>
            Deal at random instead
          </button>
        </>
      ) : (
        <>
          <span className={classes.previewHead}>
            <span className={classes.previewName}>Dealt at random</span>
          </span>
          <span className={classes.previewLine}>
            Like every other seat. Pick a role to play it instead; the agents never learn
            you chose.
          </span>
        </>
      )}
    </div>
  );
}

export function RoleCards({
  value,
  onChange,
  labelledBy,
}: {
  value: PoolRole | null;
  onChange: (role: PoolRole | null) => void;
  labelledBy: string;
}) {
  const choose = (role: PoolRole) => onChange(value === role ? null : role);

  // The arrow keys walk the pool and carry the focus; with nothing chosen they start at the top.
  const onKeyDown = (e: KeyboardEvent<HTMLDivElement>) => {
    const step = ARROW_STEP[e.key];
    if (!step) return;
    e.preventDefault();
    const i = value ? ROLES.indexOf(value) + step : step > 0 ? 0 : -1;
    const next = ROLES[(i + ROLES.length) % ROLES.length];
    onChange(next);
    e.currentTarget.querySelector<HTMLElement>(`[data-choice="${next}"]`)?.focus();
  };
  const tabIndex = (role: PoolRole) =>
    value === role || (!value && role === ROLES[0]) ? 0 : -1;
  const label = (role: PoolRole) =>
    `${CARD_TEXT[role].name}, ${FACTION_NAME[factionOf(role)!]}`;

  return (
    <>
      <div
        className={classes.cards}
        role="radiogroup"
        aria-labelledby={labelledBy}
        data-chosen={value ? '' : undefined}
        onKeyDown={onKeyDown}
      >
        {ROLES.map((role) => (
          <button
            key={role}
            type="button"
            role="radio"
            className={classes.card}
            data-faction={factionOf(role) ?? undefined}
            data-choice={role}
            aria-checked={value === role}
            aria-label={label(role)}
            tabIndex={tabIndex(role)}
            onClick={() => choose(role)}
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

      <div
        className={classes.sigils}
        role="radiogroup"
        aria-labelledby={labelledBy}
        data-chosen={value ? '' : undefined}
        onKeyDown={onKeyDown}
      >
        {SIDES.map((side) => (
          <div key={side.faction} className={classes.sigilSide} data-faction={side.faction}>
            <FactionMark
              faction={side.faction}
              format="badge"
              className={classes.sigilBadge}
              aria-hidden="true"
            />
            {side.roles.map((role) => (
              <button
                key={role}
                type="button"
                role="radio"
                className={classes.sigilDisc}
                data-choice={role}
                aria-checked={value === role}
                aria-label={label(role)}
                title={CARD_TEXT[role].name}
                tabIndex={tabIndex(role)}
                onClick={() => choose(role)}
              >
                <Sigil role={role} strokeWidth={2.6} />
              </button>
            ))}
          </div>
        ))}
      </div>

      <RolePreview role={value} onClear={() => onChange(null)} place="field" />
    </>
  );
}
