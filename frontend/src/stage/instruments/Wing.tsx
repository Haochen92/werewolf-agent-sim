'use client';

/**
 * The seat rail (the wing): every seat down the left edge as a card, so the whole table is
 * always in view while one seat has the stand. HUD pass 2 (owner, 2026-09-29, "B on photo
 * stock"): each card is printed as the same head-portrait photo the night rooms pin up, so a
 * player is the same object by day and by night, and the cards are tacked in two columns to a
 * cork board in a walnut frame with a brass edge. How many rows comes from the number of seats
 * (`railLayout`), never from nine.
 *
 * A card the player keeps a file on has faint ruled lines on its foot, the role the seat claims
 * pencilled on them, never under 11 css px: on a phone the words give way to a pencil scribble.
 *
 * One card stock for every state (owner, 2026-10-18): the seat's number on a brass tag over the
 * photo, and a footer row that holds facts only, as the side's colour and the role's sigil (a
 * neutral stripe while nothing is known). The seat on the stand is edged in amber; a dead seat is
 * the same photo gone grey with its role in the footer (deaths reveal the role on the wire, so
 * everyone may see it) and a black mourning ribbon across the photo's corner; your own seat wears
 * an amber corner on its photo; with the X-ray on, a living seat's footer shows its truth, which
 * only the observer tier holds.
 * With the X-ray on at a beat where nobody speaks, a card opens that seat's case file, and says
 * so with a steady verdigris edge and a small keyhole badge (the Reveal switch's) on its corner
 * (no breathing: nine cards pulsing would be noise). Only the replay's night stop breathes: the
 * seats that acted glow until their room has been visited, then keep a steady mark.
 * Lit and dimmed are light only, never a move or a resize. A card that opens the speaker's read
 * breathes a slow glow while it can be tapped, and flashes once when that read is new or changed
 * since the speaker's previous reads (opacity only, still for reduced motion).
 *
 * The notebook: a seated player (live) taps a seat's card, their own too, to open their file on
 * it in the case file (film/PlayerFile.tsx; owner, 2026-10-18: the notes moved there from a card
 * over the stage). The role they think a seat holds shows as a small pencilled sigil on its
 * photo. The files stay on this device (notebook.ts), reaching the server only with a speech
 * draft sent with "Use my seat notes" ticked. In a replay, and for an observer, the cards are
 * only shown. Since 2026-10-18 a scene describes its wing (`StageWing`) and the Stage keeps one
 * for the whole game.
 *
 * Its width: `width` inside the world, and on a screen wider than 16:9 it grows out into the
 * bleed (the stage's `--spare`) up to the layout's `reach`, so a phone's letterbox holds most of
 * a wider rail and the room keeps its place.
 */
import { useContext, useLayoutEffect, useRef, type CSSProperties } from 'react';
import { SPRITES, type Character } from '@/assets/manifest';
import { ChipSprite } from '../cast/ChipSprite';
import { useNotebook } from '../notebook';
import { ROLE_NAME, factionOf, type KnownRole } from '../roles';
import { WingContext, type WingSpec } from '../set';
import { RAIL_GAP, RAIL_PAD, railLayout } from './rail-layout';
import { FactionMark } from './FactionMark';
import { Sigil } from './Sigil';
import styles from './Wing.module.css';

/** The role names too wide for a desk card's band at full size: they take a step smaller. */
const LONG_BAND = new Set(['Necromancer', 'Fortune teller']);

export interface WingTileProps {
  /** The numeral. */
  seat: number;
  /** The seat's player; none for a place nobody has taken yet (the platform). */
  character?: Character;
  /** Dead: the photo goes grey and carries this role on an ink band. */
  dead?: { role: string | null };
  /** The role this viewer is entitled to see on a living seat (the X-ray's truth). */
  truth?: string | null;
  /** On the stand now. */
  lit?: boolean;
  /** Dimmed: out of the scene's focus (the losers at the end, say). */
  dim?: boolean;
  /** This viewer's own seat. */
  you?: boolean;
  /** A packmate, as a wolf sees it: the red edge. */
  pack?: boolean;
  /**
   * What this seat already knows of that one from its own view (`knownRoles`): the band in
   * brass, "Your pack" or "Seen · Wolf", with the role's sigil. A dead seat's role, "You" and
   * the X-ray's truth take the band first.
   */
  known?: KnownRole;
  /** The X-ray night's lamp: this seat acts tonight. */
  lamp?: boolean;
  /**
   * The replay's night stop: `acted`, this seat acted tonight and its room is a tap away (a
   * breathing verdigris glow); `visited`, its room has been seen (a steady, quieter mark).
   */
  glow?: 'acted' | 'visited';
  /**
   * The replay's night (owner, 2026-09-30): the word on the cream between the photo and the band
   * that says what a tap does, "Visit ▸" (an actor's room is a tap away) or "Seen" (visited).
   */
  word?: 'visit' | 'seen';
  /**
   * The X-ray's read on this seat by the seat at the stand: a verdigris edge, brighter for a sure
   * read. `onRead` makes the card a button that opens the read card (handing over the card, so
   * the read can sit level with it); `open` while its card is out. `fresh`: the read is new or
   * changed since the speaker's previous reads, and the card flashes once (a new key, a new
   * flash).
   */
  read?: {
    sure: boolean;
    open?: boolean;
    onRead?: (tile: HTMLElement) => void;
    fresh?: string | null;
  };
  /**
   * With the X-ray on, at a beat with no speaker: a tap opens this seat's case file (at the
   * night hub, an actor's card jumps to its night instead). A thin steady verdigris edge says
   * so; `label` names what the tap does.
   */
  file?: { onTap: () => void; label: string };
}

export function Wing({
  width,
  tiles,
  notes = null,
  onOpen,
}: {
  width: number;
  /** The seats, in order. */
  tiles: readonly WingTileProps[];
  /** The game whose notebook the seated player keeps here; null: the cards are only shown. */
  notes?: string | null;
  /** A tap on a seat's card opens the player's file on it (live, a seated player); unset: none. */
  onOpen?: (seat: number) => void;
}) {
  const book = useNotebook(notes);
  if (width <= 0) return null;
  const L = railLayout(tiles.length);
  const rail = {
    '--wing': `${width}px`,
    '--reach-max': `${L.reach}px`,
    '--board': `url(${SPRITES.textures.walnut.src})`,
    '--rail-frame': `url(${SPRITES.rail.frame.src})`,
    '--rail-plate': `url(${SPRITES.rail.plate.src})`,
    '--rail-paper': `url(${SPRITES.rail.paper.src})`,
    '--rail-shadow': `url(${SPRITES.rail.shadow.src})`,
    gridTemplateColumns: `repeat(${L.cols}, minmax(0, 1fr))`,
    gridTemplateRows: `auto repeat(${L.rows}, minmax(0, 1fr))`,
    '--rail-pad': `${RAIL_PAD}px`,
    '--rail-gap': `${RAIL_GAP}px`,
  } as CSSProperties;
  const opens = (t: WingTileProps) =>
    !!book && !!onOpen && !!t.character && !t.read && !t.file;
  return (
    <>
      <div className={styles.bleed} style={rail} aria-hidden="true" />
      <div
        className={styles.wing}
        style={rail}
        data-cols={L.cols}
        role="group"
        aria-label="The seats"
      >
        <div className={styles.plate}>{plateWords(tiles, opens)}</div>
        {tiles.map((t) => {
          const claim = book?.claims[t.seat];
          return (
            <WingTile
              key={t.seat}
              {...t}
              note={claim ? (ROLE_NAME[claim] ?? claim) : undefined}
              guess={t.dead || t.you ? undefined : book?.guesses[t.seat]}
              onOpen={opens(t) ? () => onOpen!(t.seat) : undefined}
            />
          );
        })}
      </div>
    </>
  );
}

/**
 * A scene's wing, described to the Stage, which draws one wing for the whole game and updates
 * it in place (set.ts `WingContext`). Described afresh every render: the tiles carry the scene's
 * taps. Outside a Stage it draws the wing itself.
 */
export function StageWing(props: WingSpec) {
  const host = useContext(WingContext);
  const owner = useRef({}).current;
  useLayoutEffect(() => {
    host?.show(owner, props);
  });
  useLayoutEffect(() => (host ? () => host.hide(owner) : undefined), [host, owner]);
  return host ? null : <Wing {...props} />;
}

/**
 * What a tap on a card does, lettered on the rail's plate (owner, 2026-10-18: the plate is the
 * instruction): an actor's night to visit, the player's file to open, a file or a read to open;
 * with no tap, the rail's name.
 */
function plateWords(
  tiles: readonly WingTileProps[],
  opens: (t: WingTileProps) => boolean,
): string {
  if (tiles.some((t) => t.word === 'visit')) return 'Tap to visit';
  if (tiles.some(opens)) return 'Tap to open file';
  if (tiles.some((t) => t.file || t.read?.onRead)) return 'Tap to read';
  return 'Passengers';
}

interface CardProps extends WingTileProps {
  /** The role the player has the seat claim, pencilled on the foot. */
  note?: string;
  /** The role the player thinks this seat holds: a small pencilled sigil on the photo. */
  guess?: string;
  /** Tapping the card opens the player's file on it (a seated player). */
  onOpen?: () => void;
}

function WingTile({
  seat,
  character,
  dead,
  truth,
  lit,
  dim,
  you,
  pack,
  known,
  lamp,
  glow,
  word,
  read,
  file,
  note,
  guess,
  onOpen,
}: CardProps) {
  // a concealed body's role is hidden (`dead.role` null) unless this viewer holds the truth
  const role = dead ? (dead.role ?? truth ?? null) : (truth ?? null);
  const hidden = !!dead && !role;
  const faction = factionOf(role);
  // the footer holds facts only (owner, 2026-10-18): a role the table or this viewer knows; your
  // own seat is the corner's, and a guess stays pencilled on the photo
  const band = role ? (ROLE_NAME[role] ?? role) : hidden ? 'Role hidden' : null;
  const knew = !band && known && !you ? known : null;
  const cls = [
    character ? styles.banded : '',
    styles.tile,
    faction ? styles[`c-${faction}`] : '',
    !character ? styles.empty : '',
    dead ? styles.dead : '',
    lit ? styles.lit : '',
    dim ? styles.dim : '',
    pack ? styles.pack : '',
    read ? styles.read : '',
    read?.sure ? styles.sure : '',
    read?.open ? styles.open : '',
    file && !read ? styles.file : '',
    glow ? styles[glow] : '',
  ]
    .filter(Boolean)
    .join(' ');
  const tap = read?.onRead ?? (file ? () => file.onTap() : onOpen);
  const label = read?.onRead
    ? `The speaker's read of seat ${seat}`
    : file
      ? file.label
      : `Seat ${seat}’s file`;
  const face = (
    <>
      <span className={styles.picture}>
        {character ? <ChipSprite character={character} /> : null}
        {/* your own seat: the amber corner (the footer is for facts) */}
        {you ? (
          <span className={styles.you}>
            <span>You</span>
          </span>
        ) : null}
        {lamp ? <span className={styles.lamp} /> : null}
        {guess ? (
          <span
            className={`${styles.guess} ${styles[`c-${factionOf(guess)}`] ?? ''}`}
            title={`You think: ${ROLE_NAME[guess] ?? guess}`}
            data-guess={guess}
          >
            <Sigil role={guess} small />
          </span>
        ) : null}
        {dead ? <span className={styles.ribbon} aria-hidden="true" /> : null}
      </span>
      <b className={styles.num}>{seat}</b>
      <span
        className={
          note || (onOpen && !dead) ? `${styles.foot} ${styles.ruled}` : styles.foot
        }
      >
        {note ? (
          <>
            <span className={styles.note}>{note}</span>
            <Scribble />
          </>
        ) : null}
        {word ? (
          <span className={`${styles.word} ${word === 'seen' ? styles.seen : ''}`}>
            {word === 'seen' ? 'Seen' : 'Visit ▸'}
          </span>
        ) : null}
      </span>
      {band ? (
        <span
          className={styles.band}
          title={band}
          data-hidden={hidden ? true : undefined}
          data-long={LONG_BAND.has(band) ? true : undefined}
        >
          {role ? <Sigil role={role} variant="felt" small /> : null}
          <span className={styles.bandName}>{band}</span>
        </span>
      ) : null}
      {knew ? (
        <span
          className={`${styles.band} ${styles.knownBand} ${knew.role && (ROLE_NAME[knew.role] ?? knew.role).length > 6 ? styles.knownLong : ''}`}
          data-known={knew.how}
          title={
            knew.role
              ? `${knew.how === 'pack' ? 'Pack' : 'Seen'} · ${ROLE_NAME[knew.role] ?? knew.role}`
              : 'Your pack'
          }
        >
          {/* a pack mate dealt before 2026-10-17 has no role on the wire: the pack's side mark */}
          {knew.role ? (
            <Sigil role={knew.role} variant="felt" small />
          ) : (
            <FactionMark faction="wolves" small />
          )}
          <span className={styles.knownWords}>
            {knew.role ? (
              <>
                <span className={styles.knownSeen}>
                  {knew.how === 'pack' ? 'Pack' : 'Seen'} ·{' '}
                </span>
                {ROLE_NAME[knew.role] ?? knew.role}
              </>
            ) : (
              'Your pack'
            )}
          </span>
        </span>
      ) : null}
      {character && !band && !knew ? (
        <span className={`${styles.band} ${styles.blank}`} aria-hidden="true" />
      ) : null}
      {read?.onRead ? <span className={styles.breathe} aria-hidden="true" /> : null}
      {glow === 'acted' ? <span className={styles.glow} aria-hidden="true" /> : null}
      {/* a card that opens a file wears the Reveal switch's keyhole; an actor's opens its room */}
      {file && !read && !word && glow !== 'acted' ? <Keyhole /> : null}
      {read?.onRead && read.fresh ? (
        <span key={read.fresh} className={styles.flash} aria-hidden="true" />
      ) : null}
    </>
  );
  if (!tap)
    return (
      <div className={cls} data-seat={seat} data-glow={glow} data-word={word}>
        {face}
      </div>
    );
  return (
    <button
      type="button"
      className={styles.tap}
      data-seat={seat}
      data-glow={glow}
      data-word={word}
      aria-label={label}
      aria-expanded={read?.onRead ? !!read.open : undefined}
      onClick={(e) => tap(e.currentTarget)}
    >
      {/* the button holds the card rather than being it (see `.tap`) */}
      <span className={cls}>{face}</span>
    </button>
  );
}

/** The Reveal switch's keyhole, lit in verdigris on a small walnut disc: this card opens a file. */
function Keyhole() {
  return (
    <span className={styles.keyhole} aria-hidden="true">
      <svg viewBox="0 0 16 16">
        <path d="M8 3.6a2.3 2.3 0 0 0-1.2 4.3L6 12.4h4l-.8-4.5A2.3 2.3 0 0 0 8 3.6Z" />
      </svg>
    </span>
  );
}

/** A note too small to read here (a phone): two short pencil strokes; a tap reads it. */
function Scribble() {
  return (
    <svg className={styles.scribble} viewBox="0 0 40 16" aria-hidden="true">
      <path d="M2 5 C7 1.5 11 7.5 16 4 S26 2 31 5 S36 4.5 38 3.5" />
      <path d="M2 12 C6 9 10 14 15 11 S22 9.5 27 11.5" />
    </svg>
  );
}
