'use client';

/**
 * The seat rail (the wing): every seat down the left edge as a card, so the whole table is
 * always in view while one seat has the stand. HUD pass 2 (owner, 2026-09-29, "B on photo
 * stock"): each card is printed as the same head-portrait photo the night rooms pin up, so a
 * player is the same object by day and by night, and the cards are tacked in two columns to a
 * cork board in a walnut frame with a brass edge. How many rows, and where the suspect slot goes, comes from
 * the number of seats (`railLayout`), never from nine.
 *
 * A card the player may write on has faint ruled lines on its foot, their note's first words on
 * them, never under 11 css px: on a phone the words give way to a pencil scribble.
 *
 * One card stock for every state. The seat on the stand is edged in brass; a dead seat is the
 * same photo gone grey with its role on an ink band (deaths reveal the role on the wire, so
 * everyone may see it) and a black mourning ribbon across the photo's corner; your own seat wears an amber "You" band; with the X-ray on, a living
 * seat wears its faction's band and a sigil badge, the truth only the observer tier holds.
 * With the X-ray on at a beat where nobody speaks, a card opens that seat's case file, and says
 * so with a steady verdigris edge and a small keyhole badge (the Reveal switch's) on its corner
 * (no breathing: nine cards pulsing would be noise). Only the replay's night stop breathes: the
 * seats that acted glow until their room has been visited, then keep a steady mark.
 * Lit and dimmed are light only, never a move or a resize. A card that opens the speaker's read
 * breathes a slow glow while it can be tapped, and flashes once when that read is new or changed
 * since the speaker's previous reads (opacity only, still for reduced motion).
 *
 * The notebook: a seated player (live) can tap any other seat's card to write a note on it,
 * guess its role (only roles that could still be alive, with how many are left; the guess
 * shows as a small pencilled sigil on the card), and
 * mark one seat as the suspect (a wax seal on its card, its head in the suspect slot). The
 * notes stay on this device (notebook.ts), reaching the server only with a speech draft sent
 * with "Use my seat notes" ticked; the suspect never preselects a ballot. In a replay, and for an observer, the cards are only shown.
 *
 * Its width: `width` inside the world, and on a screen wider than 16:9 it grows out into the
 * bleed (the stage's `--spare`) up to the layout's `reach`, so a phone's letterbox holds most of
 * a wider rail and the room keeps its place.
 */
import {
  useEffect,
  useId,
  useRef,
  useState,
  type CSSProperties,
  type KeyboardEvent as ReactKeyboardEvent,
} from 'react';
import { SPRITES, type Character } from '@/assets/manifest';
import { ChipSprite } from '../cast/ChipSprite';
import { guessChoices, useNotebook, type Notebook } from '../notebook';
import { ROLE_NAME, factionOf, type KnownRole } from '../roles';
import { RAIL_GAP, RAIL_PAD, RAIL_STRIP, railLayout } from './rail-layout';
import { Sigil } from './Sigil';
import styles from './Wing.module.css';

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
  castCounts,
}: {
  width: number;
  /** The seats, in order. */
  tiles: readonly WingTileProps[];
  /** The game whose notebook the seated player keeps here; null: the cards are only shown. */
  notes?: string | null;
  /** The cast's role counts (`view.castRoleCounts`): what the notebook's role guess offers. */
  castCounts?: Readonly<Record<string, number>>;
}) {
  const book = useNotebook(notes);
  const [editing, setEditing] = useState<number | null>(null);
  const opener = useRef<HTMLElement | null>(null);
  if (width <= 0) return null;
  const L = railLayout(tiles.length, { suspect: !!book });
  const rail = {
    '--wing': `${width}px`,
    '--reach-max': `${L.reach}px`,
    gridTemplateColumns: `repeat(${L.cols}, minmax(0, 1fr))`,
    gridTemplateRows: `repeat(${L.rows}, minmax(0, 1fr))${L.suspect?.kind === 'strip' ? ` ${RAIL_STRIP}px` : ''}`,
    '--rail-pad': `${RAIL_PAD}px`,
    '--rail-gap': `${RAIL_GAP}px`,
    '--board': `url(${SPRITES.textures.walnut.src})`,
    '--cork': `url(${SPRITES.textures.cork.src})`,
  } as CSSProperties;
  const bySeat = new Map(tiles.map((t) => [t.seat, t]));
  // the suspect is a living seat's mark: once that seat dies, the slot is empty again
  const suspect = book?.suspect && !bySeat.get(book.suspect)?.dead ? book.suspect : null;
  const editable = (t: WingTileProps) =>
    !!book && !!t.character && !t.you && !t.read && !t.file;
  const open = (seat: number, el: HTMLElement) => {
    opener.current = el;
    book?.dismissHint();
    setEditing(seat);
  };
  const close = () => {
    setEditing(null);
    opener.current?.focus();
  };
  const hint = !!book && !book.hinted && tiles.some(editable);
  const edited = editing != null ? bySeat.get(editing) : undefined;
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
        {tiles.map((t) => (
          <WingTile
            key={t.seat}
            {...t}
            note={book?.notes[t.seat]}
            guess={t.dead ? undefined : book?.guesses[t.seat]}
            suspect={suspect === t.seat}
            onOpen={editable(t) ? (el) => open(t.seat, el) : undefined}
          />
        ))}
        {L.suspect && book ? (
          <SuspectSlot
            strip={L.suspect.kind === 'strip'}
            seat={suspect}
            character={suspect ? bySeat.get(suspect)?.character : undefined}
            onOpen={suspect ? (el) => open(suspect, el) : undefined}
          />
        ) : null}
      </div>
      {hint ? (
        <p className={styles.hint} style={rail} aria-hidden="true">
          Tap a card to write notes
        </p>
      ) : null}
      {book && edited?.character ? (
        <NoteEditor
          key={edited.seat}
          seat={edited.seat}
          character={edited.character}
          dead={edited.dead}
          book={book}
          choices={guessChoices(
            castCounts ?? {},
            tiles.map((t) => t.dead?.role ?? null),
          )}
          suspect={suspect === edited.seat}
          onClose={close}
          style={rail}
        />
      ) : null}
    </>
  );
}

interface CardProps extends WingTileProps {
  /** The seated player's note on this seat. */
  note?: string;
  /** The role the player thinks this seat holds: a small pencilled sigil on the photo. */
  guess?: string;
  /** Marked as the suspect: the wax seal. */
  suspect?: boolean;
  /** Tapping the card opens its note editor (a seated player, another seat). */
  onOpen?: (card: HTMLElement) => void;
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
  suspect,
  onOpen,
}: CardProps) {
  const role = dead ? dead.role : (truth ?? null);
  const faction = factionOf(role);
  const band = you ? 'You' : role ? (ROLE_NAME[role] ?? role) : null;
  const knew = !band && known ? known : null;
  const cls = [
    band || knew ? styles.banded : '',
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
      : `Seat ${seat}, notes`;
  const face = (
    <>
      <span className={styles.picture}>
        {character ? <ChipSprite character={character} /> : null}
        {truth && !dead ? (
          <span className={styles.badge}>
            {/* the X-ray's truth: a felt badge on paper; the guess below stays a pencilled stamp */}
            <Sigil role={truth} variant="felt" small />
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
        <span className={`${styles.band} ${you ? styles.youBand : ''}`}>{band}</span>
      ) : null}
      {knew ? (
        <span
          className={`${styles.band} ${styles.knownBand} ${(ROLE_NAME[knew.role] ?? knew.role).length > 6 ? styles.knownLong : ''}`}
          data-known={knew.how}
          title={
            knew.how === 'pack'
              ? 'Your pack'
              : `Seen · ${ROLE_NAME[knew.role] ?? knew.role}`
          }
        >
          <Sigil role={knew.role} variant="felt" small />
          <span className={styles.knownWords}>
            {knew.how === 'pack' ? (
              'Your pack'
            ) : (
              <>
                <span className={styles.knownSeen}>Seen · </span>
                {ROLE_NAME[knew.role] ?? knew.role}
              </>
            )}
          </span>
        </span>
      ) : null}
      {read?.onRead ? <span className={styles.breathe} aria-hidden="true" /> : null}
      {glow === 'acted' ? <span className={styles.glow} aria-hidden="true" /> : null}
      {/* a card that opens a file wears the Reveal switch's keyhole; an actor's opens its room */}
      {file && !read && !word && glow !== 'acted' ? <Keyhole /> : null}
      {read?.onRead && read.fresh ? (
        <span key={read.fresh} className={styles.flash} aria-hidden="true" />
      ) : null}
      {suspect ? <span className={styles.seal} aria-hidden="true" /> : null}
      {character ? <span className={styles.tack} aria-hidden="true" /> : null}
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
      className={`${cls} ${styles.tap}`}
      data-seat={seat}
      data-glow={glow}
      data-word={word}
      aria-label={label}
      aria-expanded={read?.onRead ? !!read.open : undefined}
      aria-haspopup={read?.onRead || file ? undefined : 'dialog'}
      onClick={(e) => tap(e.currentTarget)}
    >
      {face}
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

/**
 * "I think they are…": the roles a living seat could still hold, as the table knows it (the
 * cast less the roles the dead have shown), with how many are left, and "not sure". A guess
 * kept from before its role ran out stays listed, marked so.
 */
function GuessSelect({
  id,
  seat,
  guess,
  choices,
  onGuess,
}: {
  id: string;
  seat: number;
  guess: string | null;
  choices: readonly { role: string; left: number }[];
  onGuess: (role: string | null) => void;
}) {
  const stale = guess && !choices.some((c) => c.role === guess);
  return (
    <label className={styles.guessRow} htmlFor={id}>
      <span>I think they are…</span>
      <select
        id={id}
        className={styles.guessSelect}
        value={guess ?? ''}
        data-seat-guess={seat}
        onChange={(e) => onGuess(e.target.value || null)}
      >
        <option value="">not sure</option>
        {choices.map((c) => (
          <option key={c.role} value={c.role}>
            {ROLE_NAME[c.role] ?? c.role} · {c.left} left
          </option>
        ))}
        {stale ? (
          <option value={guess}>{ROLE_NAME[guess] ?? guess} · none left</option>
        ) : null}
      </select>
    </label>
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

/** The suspect slot: the grid's spare cell, or a strip at the rail's foot. */
function SuspectSlot({
  strip,
  seat,
  character,
  onOpen,
}: {
  strip: boolean;
  seat: number | null;
  character?: Character;
  onOpen?: (el: HTMLElement) => void;
}) {
  const cls = `${styles.suspect} ${strip ? styles.strip : ''} ${seat ? styles.marked : ''}`;
  const body = (
    <>
      <span className={styles.suspectLabel}>Suspect</span>
      {seat && character ? (
        <span className={styles.suspectCard}>
          <span className={styles.suspectHead}>
            <ChipSprite character={character} />
          </span>
          <span className={styles.suspectSeat}>Seat {seat}</span>
          <span className={styles.seal} aria-hidden="true" />
          <span className={styles.tack} aria-hidden="true" />
        </span>
      ) : (
        <span className={styles.suspectNone}>none marked</span>
      )}
    </>
  );
  return onOpen && seat ? (
    <button
      type="button"
      className={cls}
      aria-label={`Suspect: seat ${seat}, notes`}
      aria-haspopup="dialog"
      onClick={(e) => onOpen(e.currentTarget)}
    >
      {body}
    </button>
  ) : (
    <div className={cls}>{body}</div>
  );
}

/**
 * The note editor for one seat: its head, number and whether it lives; a ruled writing area;
 * "Mark as suspect" (not for the dead); Done. Escape, Done or a tap outside closes it; what is
 * written is kept as it is typed.
 */
function NoteEditor({
  seat,
  character,
  dead,
  book,
  choices,
  suspect,
  onClose,
  style,
}: {
  seat: number;
  character: Character;
  dead?: { role: string | null };
  book: Notebook;
  /** The roles a living seat could still hold, with how many are left. */
  choices: readonly { role: string; left: number }[];
  suspect: boolean;
  onClose: () => void;
  style: CSSProperties;
}) {
  const id = useId();
  const area = useRef<HTMLTextAreaElement>(null);
  useEffect(() => {
    const el = area.current;
    if (!el) return;
    el.focus();
    el.setSelectionRange(el.value.length, el.value.length);
  }, []);
  const onKey = (e: ReactKeyboardEvent) => {
    if (e.key === 'Escape') {
      e.stopPropagation();
      onClose();
    }
  };
  const status = dead
    ? `Dead${dead.role ? ` · ${ROLE_NAME[dead.role] ?? dead.role}` : ''}`
    : 'Alive';
  return (
    <>
      <div className={styles.scrim} onClick={onClose} aria-hidden="true" />
      <div
        className={styles.editor}
        style={style}
        role="dialog"
        aria-modal="true"
        aria-labelledby={`${id}-h`}
        onKeyDown={onKey}
      >
        <div className={styles.editorHead}>
          <span className={`${styles.editorFace} ${dead ? styles.dead : ''}`}>
            <ChipSprite character={character} />
          </span>
          <span className={styles.editorWho}>
            <strong id={`${id}-h`}>Seat {seat}</strong>
            <small>{status}</small>
          </span>
        </div>
        <label className={styles.srOnly} htmlFor={`${id}-t`}>
          Your notes on seat {seat}
        </label>
        <textarea
          id={`${id}-t`}
          ref={area}
          className={styles.paper}
          value={book.notes[seat] ?? ''}
          placeholder="What have they said? Who did they vote for?"
          onChange={(e) => book.setNote(seat, e.target.value)}
          rows={4}
          maxLength={600}
        />
        {!dead ? (
          <GuessSelect
            id={`${id}-g`}
            seat={seat}
            guess={book.guesses[seat] ?? null}
            choices={choices}
            onGuess={(role) => book.setGuess(seat, role)}
          />
        ) : null}
        <div className={styles.editorFoot}>
          {!dead ? (
            <button
              type="button"
              className={styles.mark}
              aria-pressed={suspect}
              onClick={() => book.setSuspect(suspect ? null : seat)}
            >
              <span className={styles.markSeal} aria-hidden="true" />
              {suspect ? 'Marked as suspect' : 'Mark as suspect'}
            </button>
          ) : (
            <span />
          )}
          <button type="button" className={styles.done} onClick={onClose}>
            Done
          </button>
        </div>
      </div>
    </>
  );
}
