'use client';

/**
 * The morning (handoff §4.8, beat sheet §8, bench 67): the night's report, told one chip at
 * a time in an empty room. The shutter comes down over the window and the lobby's row of
 * chips goes up, the morning roll on the notice (a row per seat the night touched); the report
 * plays behind the shutter, still in the night's paint. Then, for each seat that had something
 * done to it, in the log's order:
 *
 * - attacked: its chip comes down alone, at the centre, large;
 * - fell: the act mark appears beneath it (the attacker's felt sigil tacked on: what was done,
 *   never by whom), the string gives way, the chip drops;
 * - the card: once the chip is gone, its role card comes down large and centred and the
 *   wing's tile turns to the sigil; the card is drawn up as the next beat begins;
 * - saved: the attackers' marks small and the healer's cross large beneath it, the ribbon on
 *   its string; it goes back up whole as the next beat begins.
 *
 * A quiet night is the line alone. After the report, what only one seat learns plays on that
 * seat's screen (and, in aqua, in the X-ray): the investigator's target turns to its sigil
 * over the lens; a vigilante's or the pack's target comes down whole, "survived". The X-ray
 * then has the carried summary in the film (film/film-model.ts), and the day begins: the shutter rises on the
 * day's paint and the stand comes back up.
 */
import type { GameView, NightView } from '@/game/types';
import { Atmosphere } from '../Atmosphere';
import type { SceneBeat } from '../beats/types';
import { Layer } from '../Stage';
import { SideSlot } from '../SideSlot';
import { ATTACK_MARK, ActMark } from '../instruments/ActMark';
import { RoleCard } from '../instruments/Card';
import { Chip } from '../instruments/Chip';
import { BY, DIED, MorningRoll, type RollRow } from '../instruments/MorningRoll';
import { CardButton, Caps, Notice, NoticeZone } from '../instruments/Notice';
import { Shutter } from '../instruments/Shutter';
import { StringDrop } from '../instruments/StringDrop';
import { TopStrip } from '../instruments/TopStrip';
import { bigCard, chipRow, featuredChip, rowX } from '../instruments/flies';
import { StageMotion } from '../motion';
import { diningCarPlan } from '../paint/dining-car';
import type { Special } from '../paint/draw';
import { ROLE_ARTICLE } from '../paint/role-kit';
import { seatNumber } from '../roles';
import { bandNarrows, fileTap, sideOpen, stripButtons } from '../slot';
import { STAGE_H, geometry } from '../units';
import { CarPaint, HouseLights, StandReturns, TableWing } from './DiningCarParts';
import { notebookGame } from '../notebook';
import type { SceneProps } from './types';

/** One line of the report: a death, or the save (a row of the morning roll). */
type Told = RollRow;

/** What one seat alone learns this morning. */
type Private =
  | { kind: 'investigation'; seat: string; target: string; role: string }
  | { kind: 'vigilante'; seat: string; target: string }
  | { kind: 'pack'; target: string };

export function reportOf(night: NightView | null): Told[] {
  if (!night) return [];
  const told: Told[] = night.deaths.map((d) => ({
    kind: 'death',
    player: d.player,
    role: d.role,
    types: d.attacker_types,
  }));
  if (night.save)
    told.push({ kind: 'save', ...night.save, types: night.save.attacker_types });
  return told;
}

/** The private result a beat is about, by its seq; or, for the pack's note, the night's kill. */
function privateAt(
  view: GameView,
  night: NightView | null,
  beat: SceneBeat,
): Private | null {
  const all = [
    ...view.me.privateResults,
    ...Object.values(view.xray.privateResults).flat(),
  ];
  const r = all.find((p) => p.seq === beat.seq);
  if (r?.kind === 'investigation')
    return { kind: 'investigation', seat: r.player, target: r.target, role: r.role };
  if (r?.kind === 'vigilante_confirmation')
    return { kind: 'vigilante', seat: r.player, target: r.target };
  const note = night?.wolfChannel.find(
    (w) => w.seq === beat.seq && w.wolf === 'game_master',
  );
  if (note && night?.wolfKill) return { kind: 'pack', target: night.wolfKill };
  return null;
}

/**
 * The private beats this viewer has for a night (the last one's result), so a later beat can
 * tell what was hanging just before it: the X-ray has everyone's; a seat only its own; a wolf
 * the pack's note.
 */
function lastPrivate(
  view: GameView,
  night: NightView | null,
  day: number,
  me: string | null,
  xray: boolean,
): Private | null {
  const pack = view.me.role?.pack ?? null;
  const results = (
    xray ? Object.values(view.xray.privateResults).flat() : view.me.privateResults
  )
    .filter((p) => p.day === day && p.kind !== 'bullets')
    .filter((p) => xray || p.player === me);
  const notes =
    (xray || pack) && night
      ? night.wolfChannel.filter((w) => w.wolf === 'game_master').map((w) => w.seq)
      : [];
  const seqs = [...results.map((p) => p.seq), ...notes].sort((a, b) => a - b);
  const last = seqs.at(-1);
  return last === undefined ? null : privateAt(view, night, { seq: last } as SceneBeat);
}

export function MorningScene(props: SceneProps) {
  return (
    <StageMotion speed={props.presentation.motion}>
      {/* the set stays up across the beats: a phone's browser cannot afford its pictures
          rebuilt beat after beat (build log §8.3); the figures are the beat's and play afresh */}
      <MorningSet {...props} />
      <MorningBeat
        key={`${props.beat.id}:${props.beat.seq}:${props.beat.subject ?? ''}`}
        {...props}
      />
      <SideSlot {...props} />
    </StageMotion>
  );
}

/** What the beat is about, read off the view: the set and the beat's figures share it. */
function morningFacts({ view, beat, presentation }: SceneProps) {
  const { hud } = presentation;
  const id = beat.id;
  const dayBegins = id === 'morning.day-begins';
  const nightDay = dayBegins ? beat.day - 1 : beat.day;
  const night = view.days[nightDay]?.night ?? null;
  const phase: 'day' | 'night' = dayBegins ? 'day' : 'night';
  const side = sideOpen(presentation);
  const g = geometry(hud, side);
  const plan = diningCarPlan({ phase: 'night', hud, side });
  const low = chipRow(g, plan, 'low');
  const F = featuredChip(g, low);

  const report = reportOf(night);
  const deaths = report.filter((t) => t.kind === 'death');
  const cur = beat.subject ? report.findIndex((t) => t.player === beat.subject) : -1;
  const told = cur >= 0 ? report[cur] : null;
  // how many of the night's deaths the wing has been told (its tile turns at the card)
  const toldDead =
    id === 'morning.shutter-down'
      ? 0
      : cur >= 0
        ? Math.min(deaths.length, cur + (id === 'morning.card-down' ? 1 : 0))
        : deaths.length;
  const untold = new Set(deaths.slice(toldDead).map((d) => d.player));
  const mine = id === 'morning.only-you' ? privateAt(view, night, beat) : null;
  return {
    id,
    dayBegins,
    nightDay,
    night,
    phase,
    side,
    g,
    plan,
    low,
    F,
    report,
    deaths,
    cur,
    told,
    untold,
    mine,
  };
}

/**
 * The room round the report: the car at its hour (crossfading to the day's as it begins),
 * the shutter, the house lights, the wing and the strip. Mounted once for the scene and
 * updated in place as the beats go by.
 */
function MorningSet(props: SceneProps) {
  const { view, beat, me, presentation, slot: slotInput } = props;
  const { hud, xray, animate, cast } = presentation;
  const { id, dayBegins, nightDay, phase, side, g, low, F, told, untold, mine } =
    morningFacts(props);
  const H = STAGE_H;

  const centred = !!told || !!mine || id === 'morning.card-down';
  const specials: Special[] = centred ? [[F.x, 0, F.y + F.r, F.r * 1.7, 0.95]] : [];
  const pool = dayBegins
    ? { x: g.cx, y: g.railY - g.pwid * 0.9, rx: g.pwid * 0.6, ry: g.pwid * 0.95 }
    : id === 'morning.shutter-down'
      ? {
          x: low.x0 + low.span / 2,
          y: low.rowY - 0.06 * H,
          rx: low.span * 0.56,
          ry: 0.3 * H,
        }
      : { x: F.x, y: F.y, rx: F.r * 3.2, ry: F.r * 3 };

  return (
    <>
      <Atmosphere room="car" phase={phase} hud={hud} side={side} />
      <Layer name="paint">
        <CarPaint
          phase={phase}
          from={dayBegins && animate ? 'night' : null}
          hud={hud}
          fadeDelay={1.4}
          side={side}
        />
        <Shutter
          g={g}
          state={dayBegins ? 'open' : 'closed'}
          animate={animate && (dayBegins || id === 'morning.shutter-down')}
          delay={dayBegins ? 1.4 : 0.35}
        />
      </Layer>

      <Layer name="light">
        <HouseLights
          phase={phase}
          hud={hud}
          pool={pool}
          specials={specials}
          dark={dayBegins ? 14 : 38}
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
            truth: (seat) => (xray ? (view.xray.roles[seat] ?? null) : null),
            // nobody speaks here: a card opens its seat's file
            file: fileTap(presentation, slotInput, true),
          }}
        />
        <TopStrip
          hud={hud}
          title={dayBegins ? `Day ${beat.day}` : `Morning ${nightDay}`}
          sub={`${dayBegins ? 'Discussion' : 'The report'} · ${beat.label}`}
          {...stripButtons(presentation, slotInput)}
        />
      </Layer>
    </>
  );
}

/** The beat's figures: the chips, the cards and the marks on their strings, and the words. */
function MorningBeat(props: SceneProps) {
  const { view, beat, me, presentation, turn } = props;
  const { hud, xray, animate, cast } = presentation;
  const {
    id,
    dayBegins,
    nightDay,
    night,
    side,
    g,
    low,
    F,
    report,
    deaths,
    cur,
    told,
    mine,
  } = morningFacts(props);
  const card = bigCard(g, 'morning');
  const H = STAGE_H;
  const mk = 0.07 * H,
    markY = F.y + F.r + mk * 1.15;

  // what hung at the centre just before this beat, to draw up as this one begins
  const lastTold = report.at(-1) ?? null;
  const prevPrivate = lastPrivate(view, night, nightDay, me, xray);
  const summaryBeat = xray && !!view.days[nightDay]?.summaryStructured;
  let before:
    { kind: 'card'; t: Told } | { kind: 'chip'; seat: string; saved?: boolean } | null =
    null;
  if (animate) {
    const fromReport = (t: Told | null) =>
      !t
        ? null
        : t.kind === 'death'
          ? ({ kind: 'card', t } as const)
          : ({ kind: 'chip', seat: t.player, saved: true } as const);
    if (id === 'morning.chip-attacked' && cur > 0) before = fromReport(report[cur - 1]);
    else if (id === 'morning.only-you') before = fromReport(lastTold);
    else if (id === 'morning.carried-summary')
      before = prevPrivate
        ? { kind: 'chip', seat: prevPrivate.target }
        : fromReport(lastTold);
    else if (dayBegins && !summaryBeat)
      before = prevPrivate
        ? { kind: 'chip', seat: prevPrivate.target }
        : fromReport(lastTold);
  }

  // the lobby's row, as it hung before the report: the living at dusk, with tonight's dead
  const rowSeats = view.seats.filter(
    (s) => view.alive.includes(s) || deaths.some((d) => d.player === s),
  );

  const featured = (seat: string, o: Partial<Parameters<typeof Chip>[0]> = {}) => {
    const n = seatNumber(seat);
    return (
      <Chip
        key={`f-${seat}-${o.move ?? ''}-${o.state ?? ''}`}
        x={F.x}
        y={F.y}
        r={F.r}
        seat={n}
        character={cast[n - 1]}
        you={seat === me}
        {...o}
      />
    );
  };
  const roleCard = (t: Told, move: 'lower' | 'raise' | null) =>
    t.kind === 'death' ? (
      <StringDrop
        key={`card-${t.player}-${move ?? ''}`}
        x={g.cx}
        y={card.top}
        w={card.w}
        h={card.h}
        move={move}
        delay={move === 'raise' ? 0.1 : 0.2}
        duration={move === 'lower' ? 1.2 : 0.9}
      >
        <RoleCard role={t.role} seat={seatNumber(t.player)} w={card.w} />
      </StringDrop>
    ) : null;

  const figures: React.ReactNode[] = [];
  const marks: React.ReactNode[] = [];
  if (before?.kind === 'card') figures.push(roleCard(before.t, 'raise'));
  if (before?.kind === 'chip')
    figures.push(
      featured(before.seat, {
        move: 'raise',
        delay: 0.1,
        state: before.saved ? 'saved' : 'whole',
      }),
    );

  if (id === 'morning.shutter-down' && animate) {
    rowSeats.forEach((seat, i) => {
      const n = seatNumber(seat);
      figures.push(
        <Chip
          key={`row-${seat}`}
          x={rowX(low, i, rowSeats.length)}
          y={low.rowY}
          r={low.cr}
          seat={n}
          character={cast[n - 1]}
          you={seat === me}
          move="raise"
          delay={1.3 + i * 0.05}
        />,
      );
    });
  }
  if (told && id === 'morning.chip-attacked')
    figures.push(featured(told.player, { move: animate ? 'lower' : null, delay: 0.3 }));
  if (told && id === 'morning.chip-fell') {
    if (animate) figures.push(featured(told.player, { state: 'fallen', fallDelay: 1.3 }));
    told.types.forEach((t, i) =>
      marks.push(
        <ActMark
          key={`w-${t}`}
          kind={ATTACK_MARK[t]}
          x={F.x + (i - (told.types.length - 1) / 2) * mk * 2.6}
          y={markY}
          k={mk}
          arrive={animate ? 0.2 : false}
        />,
      ),
    );
  }
  if (told && id === 'morning.card-down')
    figures.push(roleCard(told, animate ? 'lower' : null));
  if (told && id === 'morning.chip-saved') {
    figures.push(featured(told.player, { state: 'saved' }));
    told.types.forEach((t, i) =>
      marks.push(
        <ActMark
          key={`w-${t}`}
          kind={ATTACK_MARK[t]}
          x={F.x + (i - (told.types.length - 1) / 2) * mk * 1.9}
          y={markY - mk * 0.1}
          k={mk * 0.55}
          arrive={animate ? 0.2 : false}
        />,
      ),
    );
    marks.push(
      <ActMark
        key="plaster"
        kind="plaster"
        x={F.x}
        y={markY + mk * 1.6}
        k={mk * 1.45}
        arrive={animate ? 1.1 : false}
      />,
    );
  }
  if (mine) {
    const known = mine.kind === 'investigation' ? mine.role : null;
    figures.push(
      featured(mine.target, {
        move: animate ? 'lower' : null,
        delay: 0.3,
        sigil: known,
        turn: animate && !!known,
        turnDelay: 1.4,
      }),
    );
    if (known)
      marks.push(
        <ActMark
          key="lens"
          kind="lens"
          x={F.x}
          y={markY}
          k={mk}
          arrive={animate ? 1.2 : false}
        />,
      );
  }

  const myCard = me ? (view.me.role?.role ?? null) : null;

  return (
    <>
      <Layer name="figures">{figures}</Layer>
      <Layer name="instruments">{marks}</Layer>

      {dayBegins ? (
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

      <Layer name="hud">
        {!dayBegins ? (
          <NoticeZone hud={hud} side={bandNarrows(presentation, beat)} aside={side}>
            {myCard ? <CardButton role={myCard} onOpen={turn?.onCard} /> : null}
            <MorningWords
              id={id}
              report={report}
              told={told}
              mine={mine}
              me={me}
              view={view}
              cast={cast}
              arrive={animate}
            />
          </NoticeZone>
        ) : null}
      </Layer>
    </>
  );
}

/** The box at the foot for each beat of the morning. */
function MorningWords({
  id,
  report,
  told,
  mine,
  me,
  view,
  cast,
  arrive,
}: {
  id: SceneBeat['id'];
  report: Told[];
  told: Told | null;
  mine: Private | null;
  me: string | null;
  view: GameView;
  cast: SceneProps['presentation']['cast'];
  arrive: boolean;
}) {
  const t = { arrive, delay: 0.7 };
  const chipOf = (seat: string) => cast[seatNumber(seat) - 1];
  const seatName = (seat: string) =>
    `Seat ${seatNumber(seat)}${seat === me ? ' (you)' : ''}`;
  switch (id) {
    case 'morning.shutter-down':
      // the roll: the whole night at a glance, before it is told a chip at a time; the
      // roles wait for the cards
      return (
        <Notice title="The morning roll" walnut {...t}>
          <MorningRoll rows={report} cast={cast} me={me} arrive={arrive} roles={false} />
        </Notice>
      );
    case 'morning.chip-attacked':
      if (!told) return null;
      return (
        <Notice chip={chipOf(told.player)} title={seatName(told.player)} {...t}>
          was attacked in the night.
        </Notice>
      );
    case 'morning.chip-fell': {
      if (!told) return null;
      const how =
        told.types.length === 1
          ? `was ${DIED[told.types[0]]}`
          : `was attacked by ${told.types.map((x) => BY[x]).join(' and ')}, and fell`;
      return (
        <Notice
          chip={chipOf(told.player)}
          title={`${seatName(told.player)} ${how}`}
          {...t}
        />
      );
    }
    case 'morning.card-down':
      if (!told || told.kind !== 'death') return null;
      return (
        <Notice
          sigil={told.role}
          title={`Seat ${seatNumber(told.player)} was ${ROLE_ARTICLE[told.role] ?? told.role}`}
          {...t}
        >
          {told.player === me ? 'You stay at the table as a spectator.' : null}
        </Notice>
      );
    case 'morning.chip-saved':
      if (!told) return null;
      return (
        <Notice
          chip={chipOf(told.player)}
          title={`${seatName(told.player)} was attacked by ${told.types.map((x) => BY[x]).join(' and ')}`}
          {...t}
        >
          And saved by the healer.
        </Notice>
      );
    case 'morning.quiet':
      return (
        <Notice title="A quiet night" {...t}>
          No one died.
        </Notice>
      );
    case 'morning.only-you': {
      if (!mine) return null;
      const target = seatNumber(mine.target);
      const yours = mine.kind === 'pack' ? !!view.me.role?.pack && !!me : mine.seat === me;
      const aqua = yours
        ? null
        : mine.kind === 'pack'
          ? 'Only the pack'
          : `Only seat ${seatNumber(mine.seat)}`;
      const bullets =
        mine.kind === 'vigilante'
          ? ((
              [...view.me.privateResults, ...(view.xray.privateResults[mine.seat] ?? [])]
                .filter((p) => p.kind === 'bullets')
                .at(-1) as { count: number } | undefined
            )?.count ??
            view.me.role?.bullets ??
            null)
          : null;
      const text =
        mine.kind === 'investigation'
          ? `${yours ? 'Your reading' : `Seat ${seatNumber(mine.seat)}'s reading`}: seat ${target} is ${ROLE_ARTICLE[mine.role] ?? mine.role}.`
          : mine.kind === 'vigilante'
            ? `${yours ? 'You' : `Seat ${seatNumber(mine.seat)}`} shot seat ${target}. Seat ${target} survived.`
            : `${yours ? 'Your' : "The pack's"} kill on seat ${target} failed. Seat ${target} survived.`;
      return (
        <Notice
          title={yours ? 'What only you learn' : 'What only they learn'}
          aqua={aqua}
          {...t}
        >
          {text}
          {mine.kind === 'vigilante' && bullets !== null ? <Caps n={bullets} /> : null}
        </Notice>
      );
    }
    default:
      return null;
  }
}
