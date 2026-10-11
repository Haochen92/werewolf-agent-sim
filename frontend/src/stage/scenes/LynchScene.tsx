'use client';

/**
 * The lynch (handoff §4.4, beat sheet §4, bench 65): the trap's second act. The table has gone
 * down and the trap stands open. The shot pulls back; the stand comes up with the voted-out
 * seat's puppet rising into it, the open leaves either side of it, and the light closes to one
 * special. A held beat ("voted out"), then the drop: straight down through the trap, no fade,
 * the plaque left lit over an empty box. The lift brings the seat's role card up in the
 * puppet's place, and the wing's tile turns to the role's sigil once the card has cleared the
 * rail. The truth is held; then the card flies up and away, the stand goes, the shutter
 * gathers up on the night, and the leaves fold.
 *
 * With the X-ray on, the case file's docket holds "Who had them right": each voter's last
 * read of this seat before the vote, against the truth, and the seat's own last note
 * (film/film-model.ts).
 */
import { motion } from 'motion/react';
import { useEffect, useState } from 'react';
import { Camera, Layer } from '../Stage';
import { isNineSeat } from '../card-text';
import { Puppet, puppetBox } from '../cast/Puppet';
import { Bounded, standBand } from '../instruments/Bounded';
import { RoleCard } from '../instruments/Card';
import { trapGeometry } from '../instruments/Floor';
import { Lift } from '../instruments/Lift';
import { CardButton, Notice, NoticeZone } from '../instruments/Notice';
import { Plaque, Stand } from '../instruments/Stand';
import { countShot, voteGeometry } from '../instruments/vote-geometry';
import { useMotionScale, useSteps } from '../motion';
import type { Special } from '../paint/draw';
import { ROLE_ARTICLE } from '../paint/role-kit';
import { ROLE_NAME, factionOf, seatNumber } from '../roles';
import { bandNarrows, fileTap, sideOpen } from '../slot';
import { STAGE_H, STAGE_W, geometry, type StageGeometry } from '../units';
import { CarSetSpec } from './CarScene';
import type { SceneProps } from './types';
import { score, tally } from './vote-count';

/** The lynch's body under the car's host (CarScene.tsx): up across its beats, playing by its props. */
export function LynchBody(props: SceneProps) {
  return <LynchBeat {...props} />;
}

/** How far along the lynch is: before the drop, the drop, the card up, the truth, the card away. */
const STEP: Partial<Record<SceneProps['beat']['id'], number>> = {
  'lynch.stand-returns': 0,
  'lynch.named': 0,
  'lynch.drop': 1,
  'lynch.card-up': 2,
  'lynch.truth': 3,
  'lynch.card-to-wing': 4,
};

/** The role card on the lift: where the puppet stood, as tall as the puppet's box (bench 65). */
export function liftCard(g: StageGeometry) {
  const w = g.pwid * 0.62,
    h = g.ph * 0.86;
  return { x: g.cx - w / 2, top: g.railY - h, w, h };
}

function LynchBeat({ view, beat, me, presentation, slot: slotInput, turn }: SceneProps) {
  const { hud, xray, animate, cast } = presentation;
  const k = useMotionScale();
  const steps = useSteps();
  const id = beat.id,
    day = beat.day,
    step = STEP[id] ?? 0;
  const side = sideOpen(presentation);
  const g = geometry(hud, side);
  const v = voteGeometry(g);
  const t = trapGeometry(g);
  const vote = view.days[day]?.vote;
  const seat = beat.subject ?? vote?.lynched ?? '';
  const n = seatNumber(seat),
    character = n ? cast[n - 1] : null;
  const role = vote?.lynchedRole ?? view.dead.find((d) => d.player === seat)?.role ?? null;
  const mine = !!me && me === seat;
  // A lynch that ends the game: the card still goes to the wing and the stand goes, but no
  // night falls — the game-over scene takes the dusk frame from here.
  const ended = id === 'lynch.card-to-wing' && beat.endsGame === true;
  const night = id === 'lynch.card-to-wing' && !ended;
  const read = score(
    Object.keys(vote?.voteCounts ?? {}).length
      ? vote!.voteCounts
      : tally(vote?.ballots ?? []),
  );

  // the wing keeps the live face until the card clears the rail, then turns to the sigil;
  // the wait starts over each time the card-up beat is played (the scene stays mounted)
  const waits = animate && id === 'lynch.card-up';
  const [told, setTold] = useState({ beat: beat.seq, done: !waits });
  if (told.beat !== beat.seq) setTold({ beat: beat.seq, done: !waits });
  useEffect(() => {
    if (!waits) return;
    const tm = setTimeout(() => setTold({ beat: beat.seq, done: true }), 1.45 * k * 1000);
    return () => clearTimeout(tm);
  }, [waits, beat.seq, k]);
  const untold = new Set(step < 2 || !told.done ? [seat] : []);

  const card = liftCard(g);
  const fade = (from: number, to: number, duration: number, delay: number) => ({
    initial: animate ? { opacity: from } : false,
    animate: { opacity: to },
    transition: { duration: duration * k, delay: delay * k },
  });

  // the plaque: "voted out" while the puppet is there and gone; the role once the card is up
  const tag =
    step >= 2 && role
      ? ROLE_NAME[role]
      : id !== 'lynch.stand-returns'
        ? 'voted out'
        : undefined;
  const tone =
    step >= 2 && role ? (factionOf(role) ?? undefined) : tag ? 'agent' : undefined;

  // the light: one special on the seat, a little on the standing leaves; night takes it down
  const specials: Special[] = night ? [] : [[g.cx, 0, g.railY, g.pwid * 0.22, 1]];
  const quiet: Special[] = night
    ? []
    : [-1, 1].map((s) => [
        v.cx + (s * t.trapW) / 2,
        t.holeTop - t.leafH * 2,
        t.holeBot,
        0.03 * STAGE_W,
        0.7,
      ]);
  const pool = night
    ? { x: g.cx, y: g.railY - g.pwid * 0.6, rx: g.pwid * 0.45, ry: g.pwid * 0.6 }
    : { x: g.cx, y: g.railY - g.pwid * 0.9, rx: g.pwid * 0.5, ry: g.pwid * 0.9 };
  const dark = night ? 54 : id === 'lynch.named' || id === 'lynch.drop' ? 52 : 36;

  const myCard = me ? (view.me.role?.role ?? null) : null;
  const article = role ? (ROLE_ARTICLE[role] ?? role) : 'unknown';

  return (
    <>
      {id === 'lynch.stand-returns' ? (
        <Camera
          to={{ scale: 1, x: 0, y: 0 }}
          from={animate ? countShot(v) : null}
          duration={animate ? 1.0 * k : 0}
          delay={animate ? 0.1 * k : 0}
          ease={[0.4, 0.2, 0.3, 1]}
        />
      ) : null}
      <CarSetSpec
        phase={night ? 'night' : 'dusk'}
        backdrop={{ from: night && animate ? 'dusk' : null, fadeDelay: 1.3 }}
        shutter={{
          state: night ? 'open' : 'closed',
          animate: night && animate,
          delay: 1.4,
        }}
        trap={{ state: night ? 'closed' : 'open', animate: night && animate }}
        light={{ pool, specials, quiet, dark }}
        wing={{
          untold,
          lit: (s) => s === seat,
          truth: (s) => (xray ? (view.xray.roles[s] ?? null) : null),
          // nobody speaks here: a card opens its seat's file
          file: fileTap(presentation, slotInput, true),
        }}
        strip={{
          title: `Day ${day}`,
          sub: `${night ? 'Night falls' : 'The lynch'} · ${beat.label}`,
          disc: night ? 'moon' : 'sun',
        }}
      />

      <Layer name="figures">
        {character && step === 0 ? (
          <Puppet
            g={g}
            shadow
            character={character}
            // the stand's plate names the seat: no numeral on the belly
            seat={null}
            state="base"
            arrive={animate && id === 'lynch.stand-returns' ? 1.05 : false}
          />
        ) : null}
        {character && id === 'lynch.drop' && animate ? (
          // the box: the figure's column down to the stage's foot, so the drop is never cut
          <Bounded
            box={dropBox(puppetBox(g, character, 'out'))}
            pad={40}
            initial={{ y: 0 }}
            animate={{ y: 1.15 * STAGE_H }}
            transition={steps({
              duration: 0.5 * k,
              delay: 0.35 * k,
              ease: [0.55, 0, 0.95, 0.55],
            })}
          >
            <Puppet g={g} shadow character={character} seat={null} state="out" />
          </Bounded>
        ) : null}
        {role && (id === 'lynch.card-up' || id === 'lynch.truth') ? (
          <Lift
            g={g}
            travel={card.h * 1.15}
            move={animate && id === 'lynch.card-up' ? 'rise' : null}
            delay={0.3}
            duration={1.3}
            // the card and its shadow's throw
            box={{
              x: card.x - card.h * 0.1,
              y: card.top - card.h * 0.1,
              w: card.w + card.h * 0.3,
              h: card.h + card.h * 0.3,
            }}
          >
            {/* the key light's shadow of the card on the wall behind it, down and to the right */}
            <div
              aria-hidden="true"
              style={{
                position: 'absolute',
                left: card.x,
                top: card.top,
                width: card.w,
                height: card.h,
                boxShadow: `${card.h * 0.07}px ${card.h * 0.045}px ${card.h * 0.06}px rgba(12,7,4,.5)`,
              }}
            />
            <div
              style={{
                position: 'absolute',
                left: card.x,
                top: card.top,
                width: card.w,
                height: card.h,
              }}
              data-lift-card=""
            >
              <RoleCard role={role} seat={n} w={card.w} legacy={isNineSeat(view)} />
            </div>
          </Lift>
        ) : null}
        {role && (night || ended) && animate ? (
          <motion.div
            style={{
              position: 'absolute',
              left: card.x,
              top: card.top,
              width: card.w,
              height: card.h,
            }}
            initial={{ y: 0, opacity: 1 }}
            animate={{ y: -1.7 * card.h, opacity: 0.6 }}
            transition={steps({
              duration: 0.8 * k,
              delay: 0.3 * k,
              ease: [0.5, 0, 0.8, 0.5],
            })}
          >
            <RoleCard role={role} seat={n} w={card.w} legacy={isNineSeat(view)} />
          </motion.div>
        ) : null}
      </Layer>

      {!(night || ended) || animate ? (
        <Layer name="stand">
          <Bounded
            box={standBand(g.railY)}
            {...(id === 'lynch.stand-returns'
              ? fade(0, 1, 0.5, 0.5)
              : night || ended
                ? fade(1, 0, 0.6, 1.3)
                : {})}
          >
            <Stand g={g} lit={!night}>
              {n ? <Plaque seat={n} tag={tag} tone={tone} /> : null}
            </Stand>
          </Bounded>
        </Layer>
      ) : null}

      <Layer name="hud">
        <NoticeZone hud={hud} side={bandNarrows(presentation, beat)} aside={side}>
          {myCard ? (
            <CardButton role={myCard} gone={mine && step >= 2} onOpen={turn?.onCard} />
          ) : null}
          {step < 2 ? (
            <Notice
              chip={mine ? null : character}
              title={mine ? 'You are voted out' : `Seat ${n}`}
              arrive={animate && id === 'lynch.named'}
              delay={0.7}
            >
              {mine
                ? `${read}. Your role is shown to the table next.`
                : `Voted out, ${read}.`}
            </Notice>
          ) : (
            <Notice
              sigil={role}
              title={mine ? `You were ${article}` : `Seat ${n} was ${article}`}
              arrive={animate && id === 'lynch.card-up'}
              delay={0.7}
            >
              {mine
                ? id === 'lynch.card-up'
                  ? 'The table sees your card now.'
                  : 'You stay at the table as a spectator.'
                : night
                  ? 'Night falls.'
                  : `Voted out, ${read}.`}
            </Notice>
          )}
        </NoticeZone>
      </Layer>
    </>
  );
}

/** The dropping figure's box: its own column, down to the stage's foot. */
function dropBox(pb: ReturnType<typeof puppetBox>) {
  return { x: pb.left, y: pb.top, w: pb.w, h: STAGE_H - pb.top };
}
