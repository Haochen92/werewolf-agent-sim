/**
 * The puppet picker: the plush characters a player may stand as, each a small head chip, on the
 * boarding pass and the solo ticket. A pick is a wish until the deal: the server lands it on
 * whichever seat it deals the player and draws a puppet for everyone who did not pick.
 *
 * Kept free of hooks and of the server: the screen holds the choice and says what is taken, so
 * the same row serves a room (where others' picks are held) and the solo door (where none are).
 * A puppet another player holds is dimmed with their name and cannot be tapped; your own is
 * ringed in amber, and tapping it again gives it up. Without `onChange` the row is only shown.
 *
 * The catalogue may list a puppet this build has no sprites for yet (it can lead a deploy), so a
 * head the manifest does not know is drawn as its initials on a plain disc.
 */
import { VisuallyHidden } from '@mantine/core';
import { ChipSprite } from '@/stage/cast/ChipSprite';
import { isCharacter } from '@/stage/cast/castForGame';
import type { CharacterCard, GameStatus } from '@/types/contracts';
import classes from './PuppetPicker.module.css';

/** "Lion cub" → "LC": what a puppet without sprites shows in place of its head. */
function initials(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  return words
    .slice(0, 2)
    .map((w) => [...w][0]?.toUpperCase() ?? '')
    .join('');
}

/** A puppet's head in a round window; `id` null draws the empty, dashed ring. */
export function PuppetHead({ id, name }: { id: string | null; name: string }) {
  if (!id) return <span className={classes.head} data-empty aria-hidden="true" />;
  return (
    <span className={classes.head} aria-hidden="true">
      {isCharacter(id) ? (
        <ChipSprite character={id} />
      ) : (
        <span className={classes.initials}>{initials(name)}</span>
      )}
    </span>
  );
}

/**
 * What a waiting room's snapshot says about picks: the puppets other players hold (by name) and
 * this viewer's own, from `characters`, which lines up with `players`.
 */
export function roomPicks(status: GameStatus): {
  held: Map<string, string>;
  mine: string | null;
} {
  const players = status.players ?? [];
  const picks = status.characters ?? [];
  const you = status.you_aboard ?? null;
  const held = new Map<string, string>();
  players.forEach((name, i) => {
    const pick = picks[i];
    if (pick && i !== you) held.set(pick, name);
  });
  return { held, mine: you !== null ? (picks[you] ?? null) : null };
}

export function PuppetPicker({
  cards,
  value,
  held,
  onChange,
  disabled = false,
  labelledBy,
}: {
  /** The catalogue's puppets on offer, in its order (retired ones already left out). */
  cards: readonly CharacterCard[];
  /** This player's pick, or null for "the house draws". */
  value: string | null;
  /** Puppets other players hold: id → the holder's name. */
  held?: ReadonlyMap<string, string>;
  /** Tapping a puppet: its id, or null when it was already yours. Absent = shown only. */
  onChange?: (id: string | null) => void;
  /** Hold the row still (a press on its way). */
  disabled?: boolean;
  labelledBy?: string;
}) {
  const chosen = cards.find((c) => c.id === value);
  return (
    <>
      <div className={classes.row} role="group" aria-labelledby={labelledBy}>
        {cards.map((card) => {
          const holder = held?.get(card.id) ?? null;
          const mine = card.id === value;
          return (
            <button
              key={card.id}
              type="button"
              className={classes.chip}
              data-puppet={card.id}
              data-held={holder !== null || undefined}
              aria-pressed={mine}
              aria-label={
                holder ? `${card.display_name}, taken by ${holder}` : card.display_name
              }
              disabled={!onChange || disabled || holder !== null}
              onClick={onChange ? () => onChange(mine ? null : card.id) : undefined}
            >
              <PuppetHead id={card.id} name={card.display_name} />
              <span className={classes.name}>{card.display_name}</span>
              {holder !== null ? <span className={classes.holder}>{holder}</span> : null}
            </button>
          );
        })}
      </div>
      {onChange ? (
        <p className={classes.note} aria-live="polite">
          {chosen
            ? `You stand as the ${chosen.display_name}; tap it again to let the house draw.`
            : 'None picked: the house draws your puppet.'}
        </p>
      ) : null}
    </>
  );
}

/** The roster with each name's puppet beside it; an empty ring where nobody has picked yet. */
export function PickedRoster({
  players,
  picks,
  cards,
}: {
  players: readonly string[];
  picks: readonly (string | null)[];
  cards: readonly CharacterCard[];
}) {
  return (
    <ul className={classes.roster}>
      {players.map((name, i) => {
        const pick = picks[i] ?? null;
        const card = pick ? cards.find((c) => c.id === pick) : undefined;
        return (
          <li key={i}>
            <PuppetHead id={pick} name={card?.display_name ?? pick ?? ''} />
            <span>
              {name}
              {pick ? (
                <VisuallyHidden>{`, as the ${card?.display_name ?? pick}`}</VisuallyHidden>
              ) : null}
            </span>
          </li>
        );
      })}
    </ul>
  );
}
