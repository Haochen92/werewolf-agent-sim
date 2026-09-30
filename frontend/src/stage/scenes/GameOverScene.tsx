'use client';

/**
 * Game over and the epilogue (handoff §4.10, beat sheet §10, bench 73). The game stops where
 * it stopped, the paint says who won before anything is read, then the verdict is read, the
 * winners take the stand, the truth is everyone's, and (with memory on) the sheet of what the
 * game taught comes down over the whole stage.
 *
 * - `over.where-it-ended`: the last scene's frame, held. After a morning: the night behind the
 *   shutter, the room empty (the last card drawn up). After a lynch: dusk, the shutter down,
 *   the trap's leaves standing open, the card gone.
 * - `over.winners-hour`: the shutter rises on the winners' hour (the village's day, the
 *   wolves' night, the serial killer's dusk); open leaves fold.
 * - `over.verdict`: the walnut board comes down on its two strings.
 * - `over.winners-stand`: the board goes up; the stand comes up widened for the winning
 *   side's survivors, who rise into it; their tiles in the wing are lit, the rest dimmed.
 * - `over.truth`: every living tile takes its faction strip and sigil; the case file's docket
 *   lists the deal and how each seat went.
 * - `over.epilogue`: the ledger over the whole stage.
 * - `over.curtain`: the winners at the stand, the result in the box, and (live) the way out.
 *
 * Arrived at, each beat is simply there; played, it moves from the beat before.
 */
import { motion } from 'motion/react';
import Link from 'next/link';
import type { ReactNode } from 'react';
import type { GameView } from '@/game/types';
import { Atmosphere } from '../Atmosphere';
import { Layer } from '../Stage';
import { SideSlot } from '../SideSlot';
import { ChipSprite } from '../cast/ChipSprite';
import { Puppet } from '../cast/Puppet';
import { RoleCard } from '../instruments/Card';
import { Trap } from '../instruments/Floor';
import { Ledger } from '../instruments/Ledger';
import { MorningRoll } from '../instruments/MorningRoll';
import { CardButton, Notice, NoticeZone } from '../instruments/Notice';
import { Shutter } from '../instruments/Shutter';
import { StringDrop } from '../instruments/StringDrop';
import { Plaque, Stand } from '../instruments/Stand';
import { TopStrip } from '../instruments/TopStrip';
import { VerdictBoard } from '../instruments/VerdictBoard';
import { bigCard } from '../instruments/flies';
import { StageMotion, useMotionScale } from '../motion';
import type { Special } from '../paint/draw';
import type { Phase } from '../paint/materials';
import { ROLE_ARTICLE } from '../paint/role-kit';
import { ROLE_NAME, factionOf, seatNumber, type Faction } from '../roles';
import { bandNarrows, sideOpen, stripButtons } from '../slot';
import { STAGE_H, geometry } from '../units';
import { CarPaint, HouseLights, TableWing } from './DiningCarParts';
import { reportOf } from './MorningScene';
import {
  WINNERS_HOUR,
  WINNER_LINE,
  endedAt,
  knownRole,
  lastStanding,
  standSet,
  winnersOf,
} from './game-over';
import { notebookGame } from '../notebook';
import type { SceneProps } from './types';
import { score, tally } from './vote-count';
import styles from './GameOver.module.css';

/** How far along the ending is. */
const STEP: Partial<Record<SceneProps['beat']['id'], number>> = {
  'over.where-it-ended': 0,
  'over.winners-hour': 1,
  'over.verdict': 2,
  'over.winners-stand': 3,
  'over.truth': 4,
  'over.epilogue': 5,
  'over.curtain': 6,
};

/** When the winners rise into the stand, one after another, and the stand fades in (seconds). */
const RISE_AT = 1.1,
  RISE_STAGGER = 0.22,
  STAND_AT = 0.6;

export function GameOverScene(props: SceneProps) {
  return (
    <StageMotion speed={props.presentation.motion}>
      <OverBeat key={`${props.beat.id}:${props.beat.seq}`} {...props} />
      <SideSlot {...props} />
    </StageMotion>
  );
}

function OverBeat({
  view,
  beat,
  me,
  presentation,
  slot: slotInput,
  turn,
  wayOut,
}: SceneProps) {
  const { hud, xray, animate, cast } = presentation;
  const k = useMotionScale();
  const step = STEP[beat.id] ?? 0;
  const day = beat.day;
  // the side slot open: the room is laid out beside it (bench 73 drew the film up)
  const side = sideOpen(presentation);
  const g = geometry(hud, side);
  const winner = (view.winner ?? 'villagers') as Faction;
  const ended = endedAt(view);
  const left: Phase = ended === 'lynch' ? 'dusk' : 'night';
  const hour = WINNERS_HOUR[winner];
  const phase = step === 0 ? left : hour;
  const onStand = step >= 3;
  const truthOut = step >= 4;
  const winners = winnersOf(view);
  const set = standSet(
    winners.map((w) => cast[seatNumber(w) - 1]),
    g,
    side,
  );
  const H = STAGE_H;

  const fade = (on: boolean, delay: number, duration = 0.5) => ({
    initial: on ? { opacity: 0 } : false,
    animate: { opacity: 1 },
    transition: { duration: duration * k, delay: delay * k },
  });

  // the light: the held frame, the hour, the board, then one special per winner
  const specials: Special[] =
    step === 2
      ? [[g.cx, 0, 0.36 * H + 0.085 * H, g.pwid * 0.7, 0.9]]
      : onStand
        ? set.offsets.map((o) => [
            g.cx + o * g.pwid,
            0,
            g.railY,
            g.pwid * (winners.length === 1 ? 0.5 : 0.36),
            0.85,
          ])
        : [];
  const pool =
    step === 0
      ? { x: g.cx, y: 0.4 * H, rx: g.pwid * 0.7, ry: 0.3 * H }
      : step === 2
        ? { x: g.cx, y: 0.36 * H, rx: g.pwid * 1.1, ry: 0.28 * H }
        : {
            x: g.cx,
            y: g.railY - g.pwid * 0.9,
            rx: g.pwid * (winners.length <= 1 ? 0.6 : winners.length === 2 ? 0.95 : 1.15),
            ry: g.pwid * 0.95,
          };
  const dark = step === 0 ? 44 : step === 1 ? 24 : step === 2 ? 38 : 18;

  const roleOf = (s: string) => knownRole(view, s);
  const myRole = me ? (view.me.role?.role ?? null) : null;
  const myDead = !!me && !view.alive.includes(me);
  const lastCard =
    ended === 'morning' ? (view.days[view.day]?.night?.deaths.at(-1) ?? null) : null;
  const card = bigCard(g, 'morning');

  return (
    <>
      <Atmosphere room="car" phase={phase} hud={hud} side={side} />
      <Layer name="paint">
        <CarPaint
          phase={phase}
          from={animate && step === 1 ? left : null}
          hud={hud}
          fadeDelay={1.2}
          side={side}
        />
        <Shutter
          g={g}
          state={step === 0 ? 'closed' : 'open'}
          animate={animate && step === 1}
          delay={0.4}
        />
      </Layer>

      <Layer name="floor">
        <Trap
          g={g}
          phase={phase}
          state={ended === 'lynch' && step === 0 ? 'open' : 'closed'}
          animate={animate && step === 1 && ended === 'lynch'}
        />
      </Layer>

      <Layer name="figures">
        {step === 0 && animate && lastCard ? (
          <StringDrop
            x={g.cx}
            y={card.top}
            w={card.w}
            h={card.h}
            move="raise"
            delay={0.1}
            duration={0.9}
          >
            <RoleCard role={lastCard.role} seat={seatNumber(lastCard.player)} w={card.w} />
          </StringDrop>
        ) : null}
        {onStand
          ? winners.map((seat, i) => {
              const n = seatNumber(seat);
              const rise = animate && step === 3 ? RISE_AT + i * RISE_STAGGER : false;
              // out of sight below the rail until its rise, while the stand is still fading in
              return (
                <motion.div
                  key={seat}
                  style={{ position: 'absolute', inset: 0 }}
                  {...fade(rise !== false, rise || 0, 0.01)}
                >
                  <Puppet
                    g={g}
                    shadow
                    glass
                    character={cast[n - 1]}
                    // one plate names them all ("Nos. 3 and 8"): with two or three at the
                    // stand the belly still says which is which; alone, the plate does
                    seat={winners.length > 1 ? n : null}
                    state="base"
                    dx={set.offsets[i] * g.pwid}
                    scale={set.scale}
                    arrive={rise}
                  />
                </motion.div>
              );
            })
          : null}
      </Layer>

      {onStand && winners.length ? (
        <Layer name="stand">
          <motion.div
            style={{ position: 'absolute', inset: 0 }}
            {...fade(animate && step === 3, STAND_AT)}
          >
            <Stand g={g} widen={set.widen}>
              <Plaque
                seat={winners.map(seatNumber)}
                tag={
                  truthOut || xray
                    ? winners.map((s) => ROLE_NAME[roleOf(s) ?? ''] ?? '').join(', ')
                    : undefined
                }
                tone={truthOut || xray ? winner : undefined}
              />
            </Stand>
          </motion.div>
        </Layer>
      ) : null}

      <Layer name="instruments">
        {step === 2 || (step === 3 && animate) ? (
          <VerdictBoard
            g={g}
            winner={winner}
            day={day}
            endedAt={ended}
            move={!animate ? null : step === 2 ? 'lower' : 'raise'}
          />
        ) : null}
      </Layer>

      <Layer name="light">
        <HouseLights
          phase={phase}
          hud={hud}
          pool={pool}
          specials={specials}
          dark={dark}
          side={side}
        />
      </Layer>

      <Layer name="hud">
        <TableWing
          view={view}
          cast={cast}
          me={me}
          hud={hud}
          width={g.wingN}
          notes={notebookGame(presentation, me)}
          opts={{
            truth: (s) => (xray || truthOut ? roleOf(s) : null),
            lit: (s) => onStand && winners.includes(s),
            dim: (s) => onStand && !winners.includes(s),
          }}
        />
        <TopStrip
          hud={hud}
          title={
            step < 2 ? (ended === 'lynch' ? `Day ${day}` : `Morning ${day}`) : 'Game over'
          }
          sub={
            step < 2
              ? `${ended === 'lynch' ? 'The vote' : 'The report'} · ${beat.label}`
              : `Day ${day} · ${WINNER_LINE[winner].toLowerCase()} · ${beat.label}`
          }
          {...stripButtons(presentation, slotInput)}
          unlocked={truthOut && hud === 'live'}
        />
        {step !== 5 ? (
          <NoticeZone hud={hud} side={bandNarrows(presentation, beat)} aside={side}>
            {myRole ? (
              <CardButton role={myRole} gone={myDead} onOpen={turn?.onCard} />
            ) : null}
            {step === 0 && ended === 'lynch' ? (
              <Notice title="The vote’s end" arrive={animate} delay={0.7}>
                {endingLine(view)}
              </Notice>
            ) : step === 0 ? (
              // a morning's end: the morning's roll, now with the roles (every card is down)
              <Notice title="The morning roll" walnut arrive={animate} delay={0.7}>
                <MorningRoll
                  rows={reportOf(view.days[view.day]?.night ?? null)}
                  cast={cast}
                  me={me}
                  arrive={animate}
                />
              </Notice>
            ) : onStand ? (
              <EndBox
                winner={winner}
                winners={winners}
                me={me}
                myRole={myRole}
                myDead={myDead}
                cast={cast}
                truth={step === 4}
                way={step === 6 && hud === 'live' ? (wayOut ?? true) : false}
                arrive={animate && step === 3}
              />
            ) : null}
          </NoticeZone>
        ) : null}
        {step === 5 ? (
          <Ledger
            hud={hud}
            extracted={view.xray.extracted}
            roles={view.xray.roles}
            cast={cast}
            winner={winner}
            arrive={animate}
          />
        ) : null}
      </Layer>
    </>
  );
}

/** What the held frame's box says after a lynch: the vote that ended it (a morning has its roll). */
function endingLine(view: GameView): string {
  const vote = view.days[view.day]?.vote;
  const seat = vote?.lynched;
  if (!vote || !seat) return 'The vote is over.';
  const counts = Object.keys(vote.voteCounts).length
    ? vote.voteCounts
    : tally(vote.ballots);
  const role = vote.lynchedRole;
  return `Seat ${seatNumber(seat)} is voted out, ${score(counts)}${role ? `: ${ROLE_ARTICLE[role] ?? role}` : ''}.`;
}

/** The result in the box: who won, their survivors, and for a seated human, how they did. */
function EndBox({
  winner,
  winners,
  me,
  myRole,
  myDead,
  cast,
  truth,
  way,
  arrive,
}: {
  winner: Faction;
  winners: string[];
  me: string | null;
  myRole: string | null;
  myDead: boolean;
  cast: SceneProps['presentation']['cast'];
  truth: boolean;
  /** The curtain's way out (live): where the two buttons go, or `true` for buttons that go nowhere. */
  way: SceneProps['wayOut'] | boolean;
  arrive: boolean;
}) {
  const won = !!myRole && factionOf(myRole) === winner;
  let you: ReactNode = null;
  if (me && myRole)
    you = (
      <span className={won ? styles.you : `${styles.you} ${styles.lost}`}>
        <b>{won ? 'You won.' : 'You lost.'}</b> You were {ROLE_ARTICLE[myRole] ?? myRole}
        {myDead ? '; you were watching from the wing' : ''}.
      </span>
    );
  return (
    <Notice
      title={
        <span className={`${styles.title} ${styles[`c-${winner}`]}`}>
          <span className={styles.result}>{WINNER_LINE[winner]}</span>
          {you}
        </span>
      }
      arrive={arrive}
      delay={1.6}
    >
      <div className={styles.winners}>
        {winners.map((s) => {
          const c = cast[seatNumber(s) - 1];
          return (
            <span key={s} className={styles.chip}>
              {c ? <ChipSprite character={c} /> : null}
            </span>
          );
        })}
        <span>{lastStanding(winners)}</span>
        {way === true ? (
          <span className={styles.acts}>
            <button type="button">Watch the replay</button>
            <button type="button">Back to the lobby</button>
          </span>
        ) : way ? (
          <span className={styles.acts}>
            <Link href={way.replay}>Watch the replay</Link>
            <Link href={way.lobby}>Back to the lobby</Link>
          </span>
        ) : null}
      </div>
      {truth ? (
        <div className={styles.sub}>
          Every card is face up: the wing carries the whole deal, and the case file opens
          for everyone.
        </div>
      ) : null}
    </Notice>
  );
}
