'use client';

/**
 * The deal (handoff §4.0, beat sheet §1, bench 75): the first scene of a match, before
 * anyone speaks. The dining car at dawn, the shutter up, the room empty. The flies do the
 * work: the nine chips come down as the seated table, then nine cards on the same strings,
 * face down, one under each chip. What each viewer adds is layered on that one room:
 *
 * - everyone: the table seated; the cards dealt, the plate reading the cast counts;
 * - a seated human: their own card comes down large and turns face up, and the box says who
 *   they are and what they do at night;
 * - a wolf: the packmate's chip takes the red edge and its small card turns to the wolf, and
 *   the pack chat opens with the game master's line;
 * - the X-ray: all nine small cards turn at once and the wing takes its strips and badges;
 * - then the day begins: cards and chips go up, the paint goes to day, the stand returns.
 *
 * Nothing on the wire narrates the deal; every line on this stage is the client's. Played
 * forward, each beat moves from the one before it; arrived at, it is all simply there.
 */
import { Atmosphere } from '../Atmosphere';
import type { SceneBeat } from '../beats/types';
import { Layer } from '../Stage';
import { SideSlot } from '../SideSlot';
import { CardBack, RoleCard, SmallCard } from '../instruments/Card';
import { Chip } from '../instruments/Chip';
import {
  CardButton,
  Caps,
  CastLine,
  Notice,
  NoticeZone,
  PackChat,
} from '../instruments/Notice';
import { Shutter } from '../instruments/Shutter';
import { StringDrop } from '../instruments/StringDrop';
import { TopStrip } from '../instruments/TopStrip';
import { bigCard, chipRow, rowX, smallCards } from '../instruments/flies';
import { StageMotion } from '../motion';
import { CARD_TEXT } from '../card-text';
import { diningCarPlan } from '../paint/dining-car';
import type { Special } from '../paint/draw';
import { ROLE_ARTICLE } from '../paint/role-kit';
import { seatNumber } from '../roles';
import { bandNarrows, sideOpen, stripButtons } from '../slot';
import { STAGE_H, geometry } from '../units';
import { CarPaint, HouseLights, StandReturns, TableWing } from './DiningCarParts';
import type { SceneProps } from './types';

const ORDER: SceneBeat['id'][] = [
  'deal.table-seated',
  'deal.cards-dealt',
  'deal.your-card',
  'deal.your-pack',
  'deal.face-up',
  'deal.day-begins',
];

export function DealScene(props: SceneProps) {
  return (
    <StageMotion speed={props.presentation.motion}>
      <DealBeat key={`${props.beat.id}:${props.beat.seq}`} {...props} />
      <SideSlot {...props} />
    </StageMotion>
  );
}

function DealBeat({ view, beat, me, presentation, slot: slotInput }: SceneProps) {
  const { hud, xray, animate, cast } = presentation;
  const id = beat.id;
  const at = (b: SceneBeat['id']) => ORDER.indexOf(id) >= ORDER.indexOf(b);
  const day = id === 'deal.day-begins';
  const phase = day ? 'day' : 'dawn';
  const side = sideOpen(presentation);
  const g = geometry(hud, side);
  const plan = diningCarPlan({ phase, hud, side });
  const row = chipRow(g, plan, 'high');
  const sc = smallCards(g, row);
  const seats = view.seats;
  const H = STAGE_H;

  const card = me ? view.me.role : null;
  const myRole = card?.role ?? null;
  const mate = card?.pack?.find((p) => p !== me) ?? null;
  const packShown = mate !== null && at('deal.your-pack');

  // what this viewer knows of each small card at this beat
  const known = (seat: string): string | null => {
    if (xray) return view.xray.roles[seat] ?? null;
    if (packShown && seat === mate) return 'wolf';
    return null;
  };
  const yours = id === 'deal.your-card' && !!myRole;
  // your card was the big one from its beat on; its small one is not hung again
  const mineAway = (seat: string) => seat === me && !!myRole && at('deal.your-card');
  // leaving: everything goes up at the day; your big card goes up the beat after its own
  const leaving = day && animate;
  const bigLeaving =
    animate && !!myRole && (id === 'deal.your-pack' || (day && mate === null));

  const specials: Special[] = [];
  const big = bigCard(g, 'deal');
  if (yours) specials.push([g.cx, 0, big.top + big.h, big.w * 0.9, 0.95]);
  if (id === 'deal.your-pack' && mate) {
    const i = seats.indexOf(mate);
    specials.push([rowX(row, i, seats.length), 0, sc.top + sc.h, sc.w * 0.9, 0.95]);
  }
  const pool = day
    ? { x: g.cx, y: g.railY - g.pwid * 0.9, rx: g.pwid * 0.6, ry: g.pwid * 1.1 }
    : yours
      ? { x: g.cx, y: 0.5 * H, rx: 0.3 * H, ry: 0.42 * H }
      : {
          x: row.x0 + row.span / 2,
          y: row.rowY + 0.1 * H,
          rx: row.span * 0.56,
          ry: 0.36 * H,
        };

  const chipsShown = !day || leaving;
  const cardsShown = at('deal.cards-dealt') && (!day || leaving);

  return (
    <>
      <Atmosphere room="car" phase={phase} hud={hud} side={side} />
      <Layer name="paint">
        <CarPaint
          phase={phase}
          from={day && animate ? 'dawn' : null}
          hud={hud}
          side={side}
        />
        <Shutter g={g} state="open" />
      </Layer>

      <Layer name="figures">
        {chipsShown
          ? seats.map((seat, i) => {
              const n = seatNumber(seat);
              return (
                <Chip
                  key={seat}
                  glass={g}
                  x={rowX(row, i, seats.length)}
                  y={row.rowY}
                  r={row.cr}
                  seat={n}
                  character={cast[n - 1]}
                  you={seat === me}
                  edge={packShown && seat === mate ? 'pack' : null}
                  move={
                    id === 'deal.table-seated' && animate
                      ? 'lower'
                      : leaving
                        ? 'raise'
                        : null
                  }
                  delay={0.1 + i * 0.07}
                />
              );
            })
          : null}
        {cardsShown
          ? seats.map((seat, i) => {
              if (mineAway(seat)) return null;
              const n = seatNumber(seat);
              const x = rowX(row, i, seats.length);
              const role = known(seat);
              const turning =
                animate &&
                ((id === 'deal.face-up' && xray) ||
                  (id === 'deal.your-pack' && seat === mate));
              return (
                <StringDrop
                  key={seat}
                  x={x}
                  y={sc.top}
                  w={sc.w}
                  h={sc.h}
                  from={row.rowY + row.cr}
                  move={
                    id === 'deal.cards-dealt' && animate
                      ? 'lower'
                      : leaving
                        ? 'raise'
                        : null
                  }
                  delay={0.2 + i * 0.08}
                >
                  {role ? (
                    <SmallCard
                      role={role}
                      seat={n}
                      w={sc.w}
                      turn={turning}
                      turnDelay={0.3 + i * 0.08}
                    />
                  ) : (
                    <CardBack w={sc.w} />
                  )}
                </StringDrop>
              );
            })
          : null}
        {myRole && me && (yours || bigLeaving) ? (
          <StringDrop
            x={g.cx}
            y={big.top}
            w={big.w}
            h={big.h}
            move={yours ? (animate ? 'lower' : null) : 'raise'}
            delay={yours ? 0.3 : 0.1}
            duration={yours ? 1.2 : 0.9}
          >
            <RoleCard
              role={myRole}
              seat={seatNumber(me)}
              w={big.w}
              turn={yours && animate}
              turnDelay={1.9}
            />
          </StringDrop>
        ) : null}
      </Layer>

      {day ? (
        <StandReturns
          g={g}
          view={view}
          day={beat.day}
          hud={hud}
          cast={cast}
          xray={xray}
          animate={animate}
          delay={2.6}
          narrow={bandNarrows(presentation, beat)}
        />
      ) : null}

      <Layer name="light">
        <HouseLights
          phase={phase}
          hud={hud}
          pool={pool}
          specials={specials}
          dark={day ? 14 : yours ? 40 : 26}
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
          opts={{
            truth: (seat) => (xray ? known(seat) : null),
            pack: (seat) => packShown && seat === mate,
          }}
        />
        <TopStrip
          hud={hud}
          title={day ? `Day ${beat.day}` : `Before day ${beat.day}`}
          sub={`${day ? 'Discussion' : 'The deal'} · ${beat.label}`}
          {...stripButtons(presentation, slotInput)}
        />
        <NoticeZone hud={hud} side={bandNarrows(presentation, beat)} aside={side}>
          {myRole && at('deal.your-card') && !day ? <CardButton role={myRole} /> : null}
          <DealWords
            id={id}
            view={view}
            myRole={myRole}
            mate={mate}
            cast={cast}
            arrive={animate}
          />
        </NoticeZone>
      </Layer>
    </>
  );
}

/** The box at the foot for each beat of the deal. */
function DealWords({
  id,
  view,
  myRole,
  mate,
  cast,
  arrive,
}: {
  id: SceneBeat['id'];
  view: SceneProps['view'];
  myRole: string | null;
  mate: string | null;
  cast: SceneProps['presentation']['cast'];
  arrive: boolean;
}) {
  const t = { arrive, delay: 0.7 };
  switch (id) {
    case 'deal.table-seated':
      return (
        <Notice title="Nine at the table" {...t}>
          The seats are taken, in order. Nothing is known yet.
        </Notice>
      );
    case 'deal.cards-dealt':
      return (
        <Notice
          title="The cards are dealt"
          aside="face down; the table knows only the cast"
          wide
          {...t}
        >
          <CastLine counts={view.castRoleCounts} />
        </Notice>
      );
    case 'deal.your-card': {
      if (!myRole) return null;
      const bullets = view.me.role?.bullets ?? null;
      return (
        <Notice sigil={myRole} title={`You are ${ROLE_ARTICLE[myRole] ?? myRole}`} {...t}>
          {CARD_TEXT[myRole]?.night}
          {myRole === 'vigilante' && bullets !== null ? <Caps n={bullets} /> : null}
        </Notice>
      );
    }
    case 'deal.your-pack': {
      if (!mate) return null;
      const n = seatNumber(mate);
      return <PackChat mate={n} character={cast[n - 1]} arrive={arrive} />;
    }
    case 'deal.face-up':
      return (
        <Notice title="The deal, face up" {...t}>
          Every card from minute zero. Nobody at the table sees this; the film has it.
        </Notice>
      );
    default:
      return null;
  }
}
