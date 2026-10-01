'use client';

/**
 * The vote (handoff §4.3, beat sheet §3, bench 64): the trap's first act. The puppet drops
 * behind the stand and the stand goes; the car goes to dusk and the shutter comes down; the
 * trap's leaves open and stand, and the table rises through it on the lift with the glass jar
 * on it; the lid comes down on its string and lifts off. The ballots go in anonymous, backs up
 * (the vote is blind and parallel: in the replay they all drop at once), the lid goes back on,
 * and the count begins: the lid flies out, the shot pushes in, the jar tips over at the back
 * rail and the plates come out along the front edge. One chip at a time rolls out of the jar,
 * turns face up and lands on its plate, the one that settles it last; the winner's plate is
 * lit; the lift takes the table down with the count on it. A lynch leaves the trap open for
 * the lynch scene; a day with no one voted out folds the leaves, pulls back, and gathers the
 * shutter up on the night.
 *
 * The seated human votes from a row of the candidates' chips (`vote.your-ballot`): tap one,
 * confirm on the plate; their own chip drops into the jar face up, on their screen only.
 */
import { useState } from 'react';
import type { GameView } from '@/game/types';
import { Atmosphere } from '../Atmosphere';
import { Camera, Layer } from '../Stage';
import { SideSlot } from '../SideSlot';
import { Puppet, puppetBox } from '../cast/Puppet';
import { BallotLine, BallotRow } from '../instruments/BallotRow';
import { countText } from '../countdown';
import { CountPill } from '../instruments/CountPill';
import { Trap } from '../instruments/Floor';
import { Lift } from '../instruments/Lift';
import { CardButton, Notice, NoticeButton, NoticeZone } from '../instruments/Notice';
import { Shutter } from '../instruments/Shutter';
import { Plaque, Stand } from '../instruments/Stand';
import { TopStrip } from '../instruments/TopStrip';
import { VoteTable } from '../instruments/VoteTable';
import {
  countShot,
  jarGeometry,
  plateSpots,
  voteGeometry,
} from '../instruments/vote-geometry';
import type { LidState } from '../instruments/Jar';
import { motion } from 'motion/react';
import { StageMotion, useMotionScale } from '../motion';
import type { Special } from '../paint/draw';
import { seatNumber, seatify } from '../roles';
import { bandNarrows, fileTap, sideOpen, stripButtons } from '../slot';
import { STAGE_H, STAGE_W, geometry } from '../units';
import { CarPaint, HouseLights, TableWing } from './DiningCarParts';
import { notebookGame } from '../notebook';
import { VOTE_STOP } from '../containers/stops';
import type { SceneProps } from './types';
import {
  candidatesOf,
  landOrder,
  lastLine,
  litPlates,
  resultWords,
  tally,
} from './vote-count';

export function VoteScene(props: SceneProps) {
  const { beat, turn, me } = props;
  return (
    <StageMotion speed={props.presentation.motion}>
      <VoteBeat
        key={`${beat.id}:${beat.seq}:${beat.ordinal ?? ''}:${me ?? ''}:${turn?.chosen ?? ''}`}
        {...props}
      />
      <SideSlot {...props} />
    </StageMotion>
  );
}

/** The last turn of the day before the vote: whose puppet leaves the stand as voting opens. */
function lastTurn(view: GameView, day: number): string | null {
  const slots = view.days[day]?.slots ?? [];
  for (let i = slots.length - 1; i >= 0; i--) {
    const s = slots[i];
    if (s.kind !== 'gm') return s.player;
  }
  return null;
}

/** The game master's line about the vote (the last line of its tally message), seatified. */
function gmVoteLine(view: GameView, day: number): string | null {
  const gm = (view.days[day]?.slots ?? []).filter((s) => s.kind === 'gm').at(-1);
  return gm?.kind === 'gm' ? seatify(lastLine(gm.text) ?? '') || null : null;
}

const CAMERA_EASE: [number, number, number, number] = [0.4, 0.2, 0.3, 1];

function VoteBeat({
  view,
  beat,
  me,
  presentation,
  onAct,
  turn,
  slot: slotInput,
  stop,
}: SceneProps) {
  const { hud, xray, animate, cast } = presentation;
  const k = useMotionScale();
  const id = beat.id,
    day = beat.day;
  const side = sideOpen(presentation);
  const g = geometry(hud, side);
  const v = voteGeometry(g);
  const J = jarGeometry(v);
  const vote = view.days[day]?.vote;
  const ballots = vote?.ballots ?? [];
  const order = landOrder(ballots);
  const cands = candidatesOf(ballots);
  const counts = tally(ballots);

  const prompt = id === 'vote.your-ballot';
  const opening = id === 'vote.opens' || prompt;
  const resolved = id === 'vote.result' || id === 'vote.table-down';
  const counting = id === 'vote.count-begins' || id === 'vote.chip-counted' || resolved;
  const lynched = vote?.outcome === 'lynched' ? vote.lynched : null;
  const nightFalls = id === 'vote.table-down' && !lynched;
  const counted =
    id === 'vote.chip-counted' ? (beat.ordinal ?? 0) : resolved ? ballots.length : 0;

  // the seated human's ballot, live: chosen, then sent
  const pending = prompt ? view.me.pending : null;
  const offered = pending?.candidates ?? [];
  const [chosen, setChosen] = useState<string | null>(
    turn?.chosen && offered.includes(turn.chosen) ? turn.chosen : null,
  );
  const [sent, setSent] = useState(false);
  const confirm = () => {
    if (!chosen || sent) return;
    setSent(true);
    onAct?.(chosen === 'abstain' ? null : chosen);
  };

  // the jar: how many are in, and which is this viewer's own
  const living = view.alive.length;
  const liveIn = sent ? Math.max(1, turn?.progress?.n ?? 1) : (turn?.progress?.n ?? 0);
  // live, the ballots drop in as they are cast (`phase_progress`); the replay's jar opens empty
  const ballotsIn = prompt ? liveIn : opening ? (turn?.progress?.n ?? 0) : ballots.length;
  const myIndex = prompt
    ? sent
      ? ballotsIn - 1
      : null
    : me
      ? ballots.findIndex((b) => b.voter === me)
      : -1;
  const lid: LidState = id === 'vote.closes' ? 'down' : counting ? 'gone' : 'up';
  const lidFrom: LidState | undefined = !animate
    ? undefined
    : id === 'vote.opens'
      ? 'down'
      : id === 'vote.closes'
        ? 'up'
        : id === 'vote.count-begins'
          ? 'down'
          : undefined;
  const falling =
    animate && id === 'vote.ballots-drop'
      ? ballots.map((_, i) => i)
      : prompt && sent && myIndex != null
        ? [myIndex]
        : undefined;
  const winner = resolved && vote ? litPlates(vote) : null;
  const tableShown = !(id === 'vote.table-down' && !animate);
  const travel = v.holeBot - J.top + 0.03 * STAGE_H;
  // going down, the table fades from when its cloth's hem meets the lip to when the back of
  // its top does, so nothing on it is left standing over the hole once the table has gone in
  const sinkFade = [v.topY + v.drop, v.topY - v.depth] as const;

  // the shot: wide while the ballots go in, pushed in for the count, back out if night follows
  const shot = countShot(v);
  const wide = { scale: 1, x: 0, y: 0 };
  let camera: Parameters<typeof Camera>[0] | null = null;
  if (id === 'vote.count-begins')
    camera = animate
      ? { to: shot, from: wide, duration: 1.1 * k, delay: 0.25 * k, ease: CAMERA_EASE }
      : { to: shot };
  else if (counting && !nightFalls) camera = { to: shot };
  else if (nightFalls && animate)
    camera = { to: wide, from: shot, duration: 1.2 * k, delay: 2.2 * k, ease: CAMERA_EASE };

  // the light: a pool over the table; a special on the jar while it stands, on the winner at the end
  const specials: Special[] = [];
  if (!counting && tableShown) specials.push([v.cx, 0, J.top, 0.03 * STAGE_W, 0.8]);
  if (id === 'vote.result' && winner)
    for (const p of plateSpots(v, cands, counts))
      if (winner.includes(p.c)) specials.push([p.x, 0, p.y, p.rx * 1.3, 1]);
  const pool = { x: v.cx, y: v.topY - 0.3 * g.ph, rx: v.tw * 0.62, ry: 0.56 * g.ph };

  // the wing: the voter of the chip just counted; the voted-out seat, not yet dead to the table
  const newest = id === 'vote.chip-counted' && counted > 0 ? order[counted - 1] : null;
  const litSeat = newest ? newest.voter : resolved ? lynched : null;
  const untold = new Set(lynched ? [lynched] : []);

  // the stand leaving as voting opens: the day's last turn drops behind it
  const leaving = animate && id === 'vote.opens' ? lastTurn(view, day) : null;
  const ln = leaving ? seatNumber(leaving) : 0;
  const leavingChar = ln ? cast[ln - 1] : null;

  const myCard = me ? (view.me.role?.role ?? null) : null;
  const words =
    resolved && vote
      ? resultWords(vote, vote.outcome === 'tie' ? gmVoteLine(view, day) : null)
      : null;

  return (
    <>
      {camera ? <Camera {...camera} /> : null}
      <Atmosphere room="car" phase={nightFalls ? 'night' : 'dusk'} hud={hud} side={side} />
      <Layer name="paint">
        <CarPaint
          phase={nightFalls ? 'night' : 'dusk'}
          from={animate ? (id === 'vote.opens' ? 'day' : nightFalls ? 'dusk' : null) : null}
          hud={hud}
          fadeDelay={nightFalls ? 2.4 : 0.15}
          side={side}
        />
        <Shutter
          g={g}
          state={nightFalls ? 'open' : 'closed'}
          animate={animate && (id === 'vote.opens' || nightFalls)}
          delay={nightFalls ? 2.5 : undefined}
        />
      </Layer>

      <Layer name="floor">
        <Trap
          g={g}
          phase={nightFalls ? 'night' : 'dusk'}
          state={nightFalls ? 'closed' : 'open'}
          animate={animate && (id === 'vote.opens' || nightFalls)}
        />
      </Layer>

      {leavingChar ? (
        <>
          <Layer name="figures">
            <motion.div
              style={{ position: 'absolute', inset: 0 }}
              initial={{ y: 0, opacity: 1 }}
              animate={{
                y: puppetBox(g, leavingChar, 'base').h * 0.55,
                opacity: 0,
              }}
              transition={{ duration: 0.45 * k, ease: 'easeIn' }}
            >
              <Puppet g={g} shadow character={leavingChar} seat={null} state="base" />
            </motion.div>
          </Layer>
          <Layer name="stand">
            <motion.div
              style={{ position: 'absolute', inset: 0 }}
              initial={{ opacity: 1 }}
              animate={{ opacity: 0 }}
              transition={{ duration: 0.3 * k, delay: 0.38 * k, ease: 'easeIn' }}
            >
              <Stand g={g}>
                <Plaque seat={ln} />
              </Stand>
            </motion.div>
          </Layer>
        </>
      ) : null}

      <Layer name="instruments">
        {tableShown ? (
          <Lift
            g={g}
            travel={travel}
            slab
            fade={id === 'vote.table-down' ? sinkFade : undefined}
            move={
              animate && id === 'vote.opens'
                ? 'rise'
                : animate && id === 'vote.table-down'
                  ? 'sink'
                  : null
            }
          >
            <VoteTable
              v={v}
              cast={cast}
              me={me}
              ballotsIn={ballotsIn}
              mine={myIndex != null && myIndex >= 0 ? myIndex : null}
              lid={lid}
              tipped={counting}
              counted={counted}
              order={order}
              candidates={cands}
              counts={counts}
              winner={winner}
              play={{
                lidFrom,
                arriving: animate && id === 'vote.opens',
                falling,
                tipping: animate && id === 'vote.count-begins',
                platesIn: animate && id === 'vote.count-begins',
                landing: animate && id === 'vote.chip-counted',
                lighting: animate && id === 'vote.result',
              }}
            />
          </Lift>
        ) : null}
      </Layer>

      <Layer name="light">
        <HouseLights
          phase={nightFalls ? 'night' : 'dusk'}
          hud={hud}
          pool={pool}
          specials={specials}
          dark={30}
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
          edit={slotInput?.notebook}
          opts={{
            untold,
            lit: (seat) => seat === litSeat,
            truth: (seat) => (xray ? (view.xray.roles[seat] ?? null) : null),
            // nobody speaks here: a card opens its seat's file
            file: fileTap(presentation, slotInput, true),
          }}
        />
        <TopStrip
          hud={hud}
          title={`Day ${day}`}
          sub={`${nightFalls ? 'Night falls' : 'The vote'} · ${beat.label}`}
          disc={nightFalls ? 'moon' : 'sun'}
          {...stripButtons(presentation, slotInput)}
          side={side}
          count={
            opening || id === 'vote.ballots-drop' || id === 'vote.closes' ? (
              <CountPill
                hud={hud}
                label={id === 'vote.closes' ? 'All in' : 'Ballots in'}
                n={opening ? ballotsIn : ballots.length}
                total={
                  prompt
                    ? (turn?.progress?.total ?? living)
                    : opening
                      ? living
                      : ballots.length
                }
                mine={myIndex != null && myIndex >= 0 && ballotsIn > 0 ? myIndex : null}
                side={side}
              />
            ) : null
          }
        />
        <NoticeZone hud={hud} side={bandNarrows(presentation, beat)} aside={side}>
          {myCard ? (
            <CardButton
              role={myCard}
              gone={view.dead.some((d) => d.player === me && d.player !== lynched)}
              onOpen={turn?.onCard}
            />
          ) : null}
          {prompt && me && pending ? (
            <BallotRow
              candidates={offered}
              cast={cast}
              chosen={chosen}
              onChoose={sent ? undefined : setChosen}
              onConfirm={confirm}
              sent={sent}
              me={me}
              left={turn?.clock ? countText(turn.clock.remainingMs) : null}
              arrive={animate}
            />
          ) : null}
          {newest ? (
            <BallotLine
              voter={newest.voter}
              votee={newest.votee}
              cast={cast}
              arrive={animate}
            />
          ) : null}
          {/* the replay's stop (the X-ray on): the ballots are in, each seat's file a tap away */}
          {stop && id === VOTE_STOP && ballots.length ? (
            <Notice
              walnut
              title={`${ballots.length} ballots in.`}
              arrive={animate}
              delay={0.6}
              actions={
                <NoticeButton lead onPress={stop.onPlay}>
                  Count the votes ▶
                </NoticeButton>
              }
            >
              Tap a seat to read what it voted on.
            </Notice>
          ) : null}
          {words ? (
            <Notice
              chip={lynched ? cast[seatNumber(lynched) - 1] : null}
              title={lynched === me && lynched ? `${words.title} (you)` : words.title}
              arrive={animate && id === 'vote.result'}
              delay={0.7}
            >
              {words.body}
            </Notice>
          ) : null}
        </NoticeZone>
      </Layer>
    </>
  );
}
