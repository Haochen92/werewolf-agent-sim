'use client';

/**
 * The platform (beat sheet §1a, review 2026-09-26 §A5 and ruling F1): the waiting room before a
 * game, as a scene on the same stage the game is played on. The train stands at the platform
 * with the dining car in the middle; its long window holds the nine places, and the people who
 * have boarded wait on the platform, one under each place, their names on paper tags at their
 * feet and on the brass plates under the window. A place nobody has taken has a dashed mark and
 * an "open" plate: at departure an agent takes it.
 *
 * - `station.waiting`: the room filling. Each person who joins rises onto the platform as the
 *   status poll brings their name; their chip takes a tile on the wing. The ledge at the foot
 *   says how many are aboard and carries the brass plates: the host's Lock, Close and Depart,
 *   everyone else's Leave.
 * - `station.locked`: the same, with the brass "Locked" plate under the station's sign.
 * - `station.departing`: Depart was pressed (or the game has begun). The people step off the
 *   platform into their places in the window, the blinds come down on the agents' places with
 *   the agents' shadows on them, the Invite and Ticket tags draw up into the canopy, the ledge
 *   sinks, and the train pulls out to the right. The curtain then falls on the empty platform
 *   and lifts on the deal (`RoomInput.curtain`, timed by `LiveTheatre`).
 *
 * The seats are not dealt yet, so nobody here has a numeral: the i-th person to board stands at
 * the i-th place and wears the cast's i-th puppet, and the server deals the real seats at the
 * start. The scene reads the room from `SceneProps.room` and reports the host's presses through
 * `onAct` (`lock`, `unlock`, `depart`); it never talks to the server.
 *
 * Motion: arrived at, everything is simply there; a person who joins while the page watches
 * rises into place. The train is a picture that slides on its own layer (nothing on this stage
 * fades a live SVG; the curtain is a plain dark sheet). The snow is the only idle motion.
 */
import Image from 'next/image';
import { motion, type Transition } from 'motion/react';
import { useEffect, useRef, useState, type CSSProperties } from 'react';
import { preload } from 'react-dom';
import { BODY, SPRITES } from '@/assets/manifest';
import { Layer, Paint } from '../Stage';
import { ChipSprite } from '../cast/ChipSprite';
import { Puppet } from '../cast/Puppet';
import { Bleed } from '../instruments/Bleed';
import { Wing } from '../instruments/Wing';
import { StageMotion, useMotionScale } from '../motion';
import { stationBack, stationFront, stationPlan } from '../paint/station';
import { STAGE_H, geometry, type StageGeometry } from '../units';
import { CURTAIN, DEPART, canDepart, ledgeLine } from './station';
import type { RoomInput, SceneProps } from './types';
import styles from './Station.module.css';

/** The turn clock every human prompt gets in a room (ux_journeys: the one timeout rule). */
const TURN_CLOCK = '2:00';

type Ease = [number, number, number, number];
const PULL_EASE: Ease = [0.5, 0, 0.85, 0.55];
const UNROLL_EASE: Ease = [0.3, 0.7, 0.3, 1];

export function StationScene(props: SceneProps) {
  return (
    <StageMotion speed={props.presentation.motion}>
      <Station {...props} />
    </StageMotion>
  );
}

function Station({ beat, presentation, room, onAct }: SceneProps) {
  const k = useMotionScale();
  const { hud, cast, animate } = presentation;
  const departing = beat.id === 'station.departing';
  const opening = room?.curtain === 'opening';
  const S = stationPlan(hud);
  const g = geometry(hud);

  // who was already aboard when the platform was first drawn arrives still; anyone after rises
  const aboard = room?.aboard ?? [];
  const keys = aboard.map((name, i) => `${i}:${name}`);
  const [present] = useState(() => new Set(animate ? [] : keys));

  if (!room) return null;
  const n = Math.min(aboard.length, S.places.length);
  // what departure shows in the window, fetched while the room waits, so nothing pops in late
  preload(SPRITES.station.blind.src, { as: 'image' });
  for (const c of cast.slice(0, S.places.length))
    preload(SPRITES.day[c].base.src, { as: 'image' });
  // played forward, a change moves; arrived at, it is simply there
  const T = (
    duration: number,
    delay = 0,
    ease: Transition['ease'] = 'easeInOut',
  ): Transition =>
    animate ? { duration: duration * k, delay: delay * k, ease } : { duration: 0 };
  // a part that leaves at departure starts from the waiting picture only when it is played
  const from = <V,>(v: V): V | false => (animate && departing ? v : false);

  const curtain = (
    <Layer name="hud">
      {room.curtain ? (
        <motion.div
          className={styles.curtain}
          data-curtain={room.curtain}
          initial={{ opacity: 0 }}
          animate={{ opacity: room.curtain === 'closing' ? 1 : 0 }}
          transition={{
            duration: (room.curtain === 'closing' ? CURTAIN.close : CURTAIN.open) * k,
            ease: 'easeInOut',
          }}
        >
          <p>The deal begins in the dining car</p>
        </motion.div>
      ) : null}
    </Layer>
  );
  // lifting off the deal: only the curtain is left of the platform
  if (opening) return curtain;

  const { head, sub } = ledgeLine(room, departing);
  const you = room.you !== null && room.you < n ? room.you : null;
  // the server names the host (the seat that boarded with the host key), not a place: the first
  // tag with that name wears the crown
  const hostAt = room.host === null ? -1 : room.aboard.slice(0, n).indexOf(room.host);

  return (
    <>
      <Layer name="paint">
        <Bleed room="station" />
        <Paint of={stationBack} opts={{ hud, sky: SPRITES.station.sky.src }} />
        {/* the train stays inside the world: past its sides the bleed's dark takes over */}
        <div className={styles.world}>
          <motion.div
            className={styles.train}
            data-train
            style={{ left: S.train.x, top: S.train.y, width: S.train.w, height: S.train.h }}
            initial={from({ x: 0 })}
            animate={{ x: departing ? S.pull : 0 }}
            transition={T(DEPART.pull, DEPART.pullAt, PULL_EASE)}
          >
            <Image
              src={SPRITES.station.train}
              alt=""
              unoptimized
              priority
              draggable={false}
              className={styles.fill}
            />
            <div
              className={styles.glass}
              style={{
                left: S.glass.x - S.train.x,
                top: S.glass.y - S.train.y,
                width: S.glass.w,
                height: S.glass.h,
              }}
            >
              {departing
                ? S.places.map((_, i) => (
                    <WindowPlace
                      key={i}
                      i={i}
                      person={i < n}
                      agentIndex={i - n}
                      pitch={S.pitch}
                      glassH={S.glass.h}
                      character={cast[i]}
                      animate={animate}
                      T={T}
                    />
                  ))
                : null}
            </div>
            <div
              className={styles.plates}
              style={{
                left: S.glass.x - S.train.x,
                top: S.plateY - S.train.y,
                width: S.glass.w,
              }}
            >
              {S.places.map((_, i) => {
                const name = i < n ? aboard[i] : null;
                const cls = name
                  ? styles.plate
                  : departing
                    ? styles.plateAgent
                    : styles.plateOpen;
                return (
                  <span key={i} className={cls} style={{ left: (i + 0.5) * S.pitch }}>
                    {name ?? (departing ? 'agent' : 'open')}
                  </span>
                );
              })}
            </div>
          </motion.div>
        </div>
        <div
          className={styles.paving}
          style={{ top: S.floorY, height: STAGE_H - S.floorY }}
        >
          <div
            className={styles.tile}
            style={{ backgroundImage: `url(${SPRITES.station.floor.src})` }}
          />
        </div>
        <Paint
          of={stationFront}
          opts={{
            hud,
            post: SPRITES.station.post.src,
            lamp: SPRITES.station.lamp.src,
            wood: SPRITES.wood.src,
            stone: SPRITES.station.floor.src,
          }}
        />
      </Layer>

      <Layer name="floor">
        {S.places.map((x, i) => (
          <motion.i
            key={i}
            className={i < n ? styles.mark : styles.markOpen}
            style={{ left: x, top: S.feetY, x: '-50%', y: '-50%' }}
            initial={from({ opacity: 1 })}
            animate={{ opacity: departing ? 0 : 1 }}
            transition={T(0.3)}
          />
        ))}
      </Layer>

      <Layer name="figures">
        <div className={styles.clip} style={{ height: S.feetY }} data-aboard>
          {aboard.slice(0, n).map((name, i) => (
            <motion.div
              key={`${i}:${name}`}
              className={styles.fill}
              initial={from({ y: 0 })}
              animate={{ y: departing ? S.bodyH * 1.6 : 0 }}
              transition={T(0.45, 0, 'easeIn')}
            >
              <Puppet
                g={placeGeometry(g, S.places[i], S.feetY, S.bodyH)}
                character={cast[i]}
                seat={null}
                state="base"
                arrive={present.has(`${i}:${name}`) ? false : 0.05}
              />
            </motion.div>
          ))}
        </div>
      </Layer>

      <Layer name="instruments">
        {aboard.slice(0, n).map((name, i) => (
          <motion.span
            key={`${i}:${name}`}
            className={styles.tag}
            style={{ left: S.places[i], top: S.feetY + 11.7, x: '-50%' }}
            initial={present.has(`${i}:${name}`) ? from({ opacity: 1 }) : { opacity: 0 }}
            animate={{ opacity: departing ? 0 : 1 }}
            transition={T(0.3, departing ? 0 : 0.6)}
            data-tag={i}
          >
            {i === hostAt ? <Crown /> : null}
            <span className={styles.tagName}>
              {name}
              {i === you ? <i> you</i> : null}
            </span>
          </motion.span>
        ))}
        <div className={styles.sign} style={{ left: S.cx }}>
          <span className={styles.chains} aria-hidden="true">
            <i />
            <i />
          </span>
          <span className={styles.board}>
            <b>{room.name || 'Unnamed table'}</b>
            <small>{room.host ? `hosted by ${room.host}` : 'nobody aboard yet'}</small>
          </span>
          {room.locked ? (
            <span className={styles.lockPlate} data-locked>
              <LockIcon />
              Locked
            </span>
          ) : null}
        </div>
      </Layer>

      <Layer name="light">
        <Snow still={k === 0} />
      </Layer>

      <Layer name="hud">
        <Wing
          width={g.wingN}
          tiles={S.places.map((_, i) => ({
            seat: i + 1,
            character: i < n ? cast[i] : undefined,
            you: i < n && i === you,
          }))}
        />
        <HangTags
          room={room}
          left={g.wingN + 112}
          departing={departing}
          T={T}
          from={from}
        />
        <motion.div
          className={styles.ledge}
          role="group"
          aria-label="The platform"
          data-ledge={beat.id}
          style={{
            left: S.cx,
            x: '-50%',
            backgroundImage: `linear-gradient(rgba(60,30,12,.25),rgba(20,10,4,.55)),url(${SPRITES.wood.src})`,
          }}
          initial={from({ y: 0 })}
          animate={{ y: departing ? 160 : 0 }}
          transition={T(1.0, DEPART.pullAt, 'easeIn')}
        >
          <div className={styles.notice}>
            {you !== null ? (
              <span className={styles.noticeChip}>
                <ChipSprite character={cast[you]} />
              </span>
            ) : null}
            <span>
              <b>{head}</b>
              <em>{sub}</em>
              {room.error ? (
                <em className={styles.error} role="alert">
                  {room.error}
                </em>
              ) : null}
            </span>
          </div>
          {room.isHost && !departing ? (
            <>
              <button
                type="button"
                className={`${styles.brass} ${styles.brassSmall}`}
                aria-pressed={room.locked}
                disabled={Boolean(room.busy)}
                onClick={() => onAct?.(room.locked ? 'unlock' : 'lock')}
              >
                {room.locked ? <LockIcon /> : <OpenLockIcon />}
                {room.busy === 'lock'
                  ? 'Locking…'
                  : room.busy === 'unlock'
                    ? 'Unlocking…'
                    : room.locked
                      ? 'Unlock'
                      : 'Lock'}
              </button>
              <ClosePlate
                busy={room.busy === 'close'}
                disabled={Boolean(room.busy)}
                onClose={() => onAct?.('close')}
              />
              <button
                type="button"
                className={`${styles.brass} ${styles.brassBig}`}
                disabled={!canDepart(room)}
                onClick={() => onAct?.('depart')}
              >
                {room.busy === 'depart' ? 'Departing…' : 'Depart'}
              </button>
            </>
          ) : !departing ? (
            <button
              type="button"
              className={`${styles.brass} ${styles.brassSmall}`}
              disabled={Boolean(room.busy)}
              onClick={() => onAct?.('leave')}
            >
              {room.busy === 'leave' ? 'Leaving…' : 'Leave'}
            </button>
          ) : null}
        </motion.div>
      </Layer>
      {curtain}
    </>
  );
}

/**
 * The puppet box's geometry for a place on the platform: the stand's rules (one body height,
 * the kit's head room) with the stand's rail moved to where this person stands, so the feet
 * land on the platform (the kit hides 8% of the body behind the rail: the rail sits that much
 * above the feet here).
 */
function placeGeometry(
  g: StageGeometry,
  x: number,
  feetY: number,
  bodyH: number,
): StageGeometry {
  const ph = bodyH / 0.98;
  return { ...g, cx: x, ph, railY: feetY - 0.08 * bodyH };
}

/** One place in the dining car's window at departure: a person at it, or an agent's blind. */
function WindowPlace({
  i,
  person,
  agentIndex,
  pitch,
  glassH,
  character,
  animate,
  T,
}: {
  i: number;
  person: boolean;
  /** Which of the agents' places this is, left to right: the blinds come down in turn. */
  agentIndex: number;
  pitch: number;
  glassH: number;
  character: SceneProps['presentation']['cast'][number];
  animate: boolean;
  T: (d: number, delay?: number, ease?: Transition['ease']) => Transition;
}) {
  const img = SPRITES.day[character].base;
  const aspect = img.width / img.height;
  const cx = (i + 0.5) * pitch;
  if (person) {
    // the upper body shows over the sill, every body the same height
    const h = 140 / BODY[character].body;
    const w = h * aspect;
    return (
      <motion.div
        className={styles.inWindow}
        style={{ left: cx - w / 2, top: glassH + 40 - h, width: w, height: h }}
        initial={animate ? { opacity: 0, y: 18 } : false}
        animate={{ opacity: 1, y: 0 }}
        transition={T(0.8, 0.3, 'easeOut')}
      >
        <Image
          src={img}
          alt=""
          unoptimized
          loading="eager"
          draggable={false}
          className={styles.fill}
        />
      </motion.div>
    );
  }
  const bw = pitch * 0.86;
  const bh = bw / (1024 / 1465);
  const sh = 99;
  const sw = sh * aspect;
  return (
    <>
      <motion.div
        className={styles.blind}
        style={{ left: cx - bw / 2, top: -3.6, width: bw, height: bh }}
        initial={animate ? { clipPath: 'inset(0% 0% 100% 0%)' } : false}
        animate={{ clipPath: 'inset(0% 0% 0% 0%)' }}
        transition={T(0.9, 0.5 + agentIndex * 0.16, UNROLL_EASE)}
      >
        <Image
          src={SPRITES.station.blind}
          alt=""
          unoptimized
          loading="eager"
          draggable={false}
          className={styles.fill}
        />
      </motion.div>
      <motion.div
        className={styles.shadow}
        style={{ left: cx - sw / 2, top: glassH - 10.8 - sh, width: sw, height: sh }}
        initial={animate ? { opacity: 0 } : false}
        animate={{ opacity: 0.58 }}
        transition={T(0.6, 1.2 + agentIndex * 0.16, 'easeOut')}
      >
        <Image
          src={img}
          alt=""
          unoptimized
          loading="eager"
          draggable={false}
          className={styles.fill}
        />
      </motion.div>
    </>
  );
}

/**
 * The two paper tags hung from the canopy: Invite (the room's link, to copy) at the left and
 * Ticket (the room's terms) at the right, each opening its panel on paper beneath it. At
 * departure they draw up into the canopy.
 */
function HangTags({
  room,
  left,
  departing,
  T,
  from,
}: {
  room: RoomInput;
  left: number;
  departing: boolean;
  T: (d: number, delay?: number, ease?: Transition['ease']) => Transition;
  from: <V>(v: V) => V | false;
}) {
  const [open, setOpen] = useState<'invite' | 'ticket' | null>(null);
  const [copied, setCopied] = useState(false);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => () => clearTimeout(timer.current ?? undefined), []);
  const toggle = (which: 'invite' | 'ticket') =>
    setOpen((o) => (o === which ? null : which));
  const copy = () => {
    void navigator.clipboard?.writeText(room.link).catch(() => {});
    setCopied(true);
    clearTimeout(timer.current ?? undefined);
    timer.current = setTimeout(() => setCopied(false), 1600);
  };
  const shown = departing ? null : open;
  const tag = (
    which: 'invite' | 'ticket',
    x: number,
    tilt: number,
    title: string,
    small: string,
  ) => (
    <motion.div
      className={styles.hang}
      style={{ left: x, x: '-50%' }}
      initial={from({ y: 0 })}
      animate={{ y: departing ? -420 : 0 }}
      transition={T(0.9, 0, 'easeIn')}
    >
      <button
        type="button"
        className={styles.hangButton}
        aria-expanded={shown === which}
        onClick={() => toggle(which)}
        style={{ '--tilt': `${tilt}deg` } as CSSProperties}
      >
        <span className={styles.string} />
        <span className={styles.hangFace}>
          <span className={styles.eye} />
          {which === 'invite' ? <LinkIcon /> : <TicketIcon />}
          <b>{title}</b>
          <small>{small}</small>
        </span>
      </button>
    </motion.div>
  );
  return (
    <>
      {tag('invite', left, -3, 'Invite', 'the link')}
      {tag('ticket', 1600 - 112, 2.5, 'Ticket', 'the terms')}
      {shown === 'invite' ? (
        <div
          className={`${styles.panel} ${styles.invite}`}
          style={{ left: left - 80 }}
          role="dialog"
          aria-label="Invite"
        >
          <h3>Invite</h3>
          <div className={styles.linkRow}>
            <output>{room.link}</output>
            <button type="button" onClick={copy}>
              {copied ? 'Copied' : 'Copy'}
            </button>
          </div>
          <p>
            {room.locked
              ? 'The room is locked: nobody new can board, link or not, until the host unlocks it.'
              : 'Anyone with the link can board until the train departs.'}
          </p>
        </div>
      ) : null}
      {shown === 'ticket' ? (
        <div
          className={`${styles.panel} ${styles.ticket}`}
          role="dialog"
          aria-label="Ticket"
        >
          <span className={styles.ticketKind}>Admit a party</span>
          <h3>{room.name || 'Unnamed table'}</h3>
          <dl>
            <dt>Places</dt>
            <dd>
              {room.places}, {room.aboard.length} taken
            </dd>
            <dt>Turn clock</dt>
            <dd>{TURN_CLOCK}</dd>
            <dt>Hosted by</dt>
            <dd>{room.host ?? '—'}</dd>
            <dt>Room</dt>
            <dd>{room.locked ? 'Locked' : 'Open to all'}</dd>
          </dl>
        </div>
      ) : null}
    </>
  );
}

/**
 * The snow over the platform: the mockup's flakes, falling for as long as anyone stares. The
 * loading still (`StationStill`) lets the same snow fall.
 */
export function Snow({ still }: { still: boolean }) {
  return (
    <div
      className={still ? `${styles.snow} ${styles.still}` : styles.snow}
      aria-hidden="true"
    >
      {FLAKES.map((f, i) => (
        <i key={i} style={f} />
      ))}
    </div>
  );
}

/** Seventy flakes on the mockup's generator (a fixed LCG, so every render is the same snow). */
const FLAKES: CSSProperties[] = (() => {
  const out: CSSProperties[] = [];
  let r = 11;
  for (let i = 0; i < 70; i++) {
    r = (r * 9301 + 49297) % 233280;
    const q = r / 233280;
    const s = (0.18 + ((i * 37) % 10) / 22) * 16;
    out.push({
      left: `${(q * 100).toFixed(1)}%`,
      width: s,
      height: s,
      opacity: 0.35 + ((i * 13) % 10) / 16,
      animationDuration: `${7 + ((i * 7) % 9)}s`,
      animationDelay: `-${(((i * 53) % 90) / 10).toFixed(1)}s`,
      ['--dx' as string]: `${(((i * 29) % 9) - 4) * 16}px`,
    });
  }
  return out;
})();

function LockIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="5" y="11" width="14" height="10" rx="2" />
      <path d="M8 11 V8 a4 4 0 0 1 8 0 V11" />
    </svg>
  );
}

/**
 * The host's Close: it ends the room for everyone, so it takes two presses. The first turns
 * the plate into the question; the second, within a few seconds, closes. Left alone, the
 * plate turns back.
 */
function ClosePlate({
  busy,
  disabled,
  onClose,
}: {
  busy: boolean;
  disabled: boolean;
  onClose: () => void;
}) {
  const [asking, setAsking] = useState(false);
  useEffect(() => {
    if (!asking) return;
    const t = setTimeout(() => setAsking(false), 4000);
    return () => clearTimeout(t);
  }, [asking]);
  return (
    <button
      type="button"
      className={`${styles.brass} ${styles.brassSmall}`}
      data-asking={asking || undefined}
      disabled={disabled}
      onClick={() => (asking ? onClose() : setAsking(true))}
    >
      {busy ? 'Closing…' : asking ? 'Close for everyone?' : 'Close room'}
    </button>
  );
}

/** The host's mark: a small brass crown sitting on their name tag. */
function Crown() {
  return (
    <svg className={styles.crown} viewBox="0 0 22 15" role="img" aria-label="host">
      <path d="M2 13 L1 4 L6.5 8 L11 1.5 L15.5 8 L21 4 L20 13 Z" />
      <circle cx="1" cy="3.4" r="1.4" />
      <circle cx="11" cy="1.4" r="1.4" />
      <circle cx="21" cy="3.4" r="1.4" />
    </svg>
  );
}

function OpenLockIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <rect x="5" y="11" width="14" height="10" rx="2" />
      <path d="M8 11 V8 a4 4 0 0 1 7.6-1.7" />
    </svg>
  );
}

function LinkIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M10 14 a4 4 0 0 0 5.6 0 l3-3 a4 4 0 0 0-5.6-5.6 l-1 1" />
      <path d="M14 10 a4 4 0 0 0-5.6 0 l-3 3 a4 4 0 0 0 5.6 5.6 l1-1" />
    </svg>
  );
}

function TicketIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden="true">
      <path d="M3 7h18v3a2 2 0 0 0 0 4v3H3v-3a2 2 0 0 0 0-4z" />
      <path d="M14 7v10" strokeDasharray="2 2" />
    </svg>
  );
}
