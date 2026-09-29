'use client';

/**
 * The day discussion (handoff §4.1, beat sheet §2): the base scene of the game. The dining car
 * by day, the stand in the middle with one puppet in it, the seat's line in the box at the
 * foot, the wing down the left with the speaker lit. Turns run in the log's order; this scene
 * draws one of them, the one the beat is on.
 *
 * - `day.speech`: the speaker talking, the line in the box, a page at a time (a beat per page).
 * - `day.pass`: the speaker idle, the box saying "passes.". Everyone sees a turn that ended
 *   with no line; with the X-ray on, the box also says why, and what was held back.
 * - `day.turn-thinking` (live only): the seat has the stand and has not spoken yet, so the
 *   puppet stands thinking and the box holds a "…" until its line (or its pass) arrives.
 * - `day.your-turn` (live, the seated human's own turn): their puppet at the stand thinking,
 *   and in the box's place the dock to write the line in (instructions to your agent and
 *   Draft, then the line, Send and Pass), its countdown on it.
 * - A line the seat's agent said for this seat, because its turn ran out: on this seat's own
 *   screen the plaque and the box say "your seat's agent spoke for you".
 *
 * Played forward (`presentation.animate`), the puppet rises into the stand thinking (the box
 * holding a "…"), then talks and the line comes into the box. Arrived at (a seek, a refresh), it is all simply there.
 */
import { useEffect, useState } from 'react';
import type { DayState } from '@/assets/manifest';
import type { PassSlot, SpeechSlot } from '@/game/types';
import { Atmosphere } from '../Atmosphere';
import { Layer, Paint } from '../Stage';
import { SideSlot } from '../SideSlot';
import { Puppet } from '../cast/Puppet';
import { ReadCard } from '../film/ReadCard';
import { turnReads } from '../film/film-model';
import { countText } from '../countdown';
import { CardButton, NoticeZone } from '../instruments/Notice';
import { SpeechBox } from '../instruments/SpeechBox';
import { Plaque, Stand } from '../instruments/Stand';
import { TopStrip } from '../instruments/TopStrip';
import { TurnDock } from '../instruments/TurnDock';
import { Wing } from '../instruments/Wing';
import { StageMotion, useMotionScale } from '../motion';
import { diningCarPlan } from '../paint/dining-car';
import { drape } from '../paint/drape';
import { light } from '../paint/light';
import { shutter } from '../paint/window';
import { ROLE_NAME, factionOf, seatNumber } from '../roles';
import { bandNarrows, sideOpen, stripButtons } from '../slot';
import { VELVET, WOOD } from '../textures';
import { BLEED, geometry } from '../units';
import { CarPaint } from './DiningCarParts';
import { notebookGame } from '../notebook';
import type { SceneProps } from './types';

/** How long the arriving puppet stands thinking before it speaks, after the rise (seconds). */
const THINK = 0.6;

/** A turn's key: a new beat is a new turn, except a line (or a pass) after its own thinking. */
const turnKey = (b: SceneProps['beat']) => `${b.id}:${b.seq}`;
const continues = (was: SceneProps['beat'], now: SceneProps['beat']) =>
  was.id === 'day.turn-thinking' &&
  (now.id === 'day.speech' || now.id === 'day.pass') &&
  now.subject === was.subject &&
  now.day === was.day;

export function DayScene(props: SceneProps) {
  // live, the thinking puppet is already at the stand when its line arrives: it does not rise again
  const [on, setOn] = useState({ beat: props.beat, key: turnKey(props.beat) });
  if (on.beat !== props.beat)
    setOn({
      beat: props.beat,
      key: continues(on.beat, props.beat) ? on.key : turnKey(props.beat),
    });
  return (
    <StageMotion speed={props.presentation.motion}>
      {/* a new beat is a new turn: the arrival replays from the start */}
      <DayTurn key={on.key} {...props} />
      <SideSlot {...props} />
    </StageMotion>
  );
}

function DayTurn({
  view,
  beat,
  me,
  presentation,
  slot: slotInput,
  turn,
  onSay,
  onAct,
  onNext,
}: SceneProps) {
  const { hud, xray, animate, cast } = presentation;
  const k = useMotionScale();
  const side = sideOpen(presentation);
  const g = geometry(hud, side);
  const plan = diningCarPlan({ phase: 'day', hud, side });

  // my own turn: the beat is mine (`seat`), with no line yet
  const mine = beat.id === 'day.your-turn';
  const speaker = beat.subject ?? (mine ? (beat.seat ?? null) : null);
  const slot = (view.days[beat.day]?.slots ?? []).find((s) => s.seq === beat.seq) as
    SpeechSlot | PassSlot | undefined;
  const isPass = beat.id === 'day.pass';
  // live: the seat has the stand and no line yet
  const waiting = beat.id === 'day.turn-thinking';

  // Played forward: arrive thinking, then speak. At rest: already speaking.
  const [settled, setSettled] = useState(!animate);
  const [risen, setRisen] = useState(!animate);
  useEffect(() => {
    if (!risen || settled) return;
    const t = setTimeout(() => setSettled(true), THINK * k * 1000);
    return () => clearTimeout(t);
  }, [risen, settled, k]);

  const state: DayState =
    mine || waiting || !settled ? 'thinking' : isPass ? 'base' : 'talking';
  // my line, said by my seat's agent: only my screen is told
  const agent = !mine && speaker !== null && speaker === me && !!turn?.agentSpoke;
  const dock = mine && turn?.dock && !turn.dock.closed ? turn.dock : null;
  const n = speaker ? seatNumber(speaker) : 0;
  const character = n ? cast[n - 1] : null;
  const role = speaker ? view.xray.roles[speaker] : undefined;
  const deadBySeat = new Map(view.dead.map((d) => [d.player, d]));

  // the X-ray's reads on the wing: the speaker's reads of the table when it spoke; a tap on a
  // seat opens its card, level with the tile
  const reads = xray ? turnReads(view, beat) : null;
  const [card, setCard] = useState<{ seat: string; top: number } | null>(null);
  const readOf = (seat: string) => reads?.reads.find((r) => r.player === seat);
  const opened = card ? readOf(card.seat) : undefined;

  return (
    <>
      <Atmosphere room="car" phase="day" hud={hud} side={side} />
      <Layer name="paint">
        <CarPaint phase="day" hud={hud} side={side} />
        <Paint of={shutter} opts={{ hud, side, state: 'open', walnut: WOOD.walnut }} />
      </Layer>

      <Layer name="figures">
        {character ? (
          <Puppet
            g={g}
            shadow
            glass
            character={character}
            seat={n}
            state={state}
            arrive={animate ? 0.1 : false}
            onArrived={() => setRisen(true)}
          />
        ) : null}
      </Layer>

      <Layer name="stand">
        <Stand g={g} speech={!dock}>
          {n ? (
            <Plaque
              seat={n}
              tag={agent ? 'your seat’s agent' : xray && role ? ROLE_NAME[role] : undefined}
              tone={
                agent ? 'agent' : xray && role ? (factionOf(role) ?? undefined) : undefined
              }
            />
          ) : null}
        </Stand>
      </Layer>

      <Layer name="light">
        <Paint
          of={light}
          opts={{
            hud,
            side,
            scene: { glows: plan.glows, specials: plan.specials },
            lamps: plan.lamps,
            // the painted room reads as lit: the speaker's pool says "this one", the room stays warm
            dark: 24,
            bleed: BLEED,
          }}
        />
      </Layer>

      <Layer name="hud">
        {hud === 'replay' ? (
          <Paint of={drape} opts={{ bleed: BLEED, velvet: VELVET }} />
        ) : null}
        <Wing
          width={g.wingN}
          notes={notebookGame(presentation, me)}
          tiles={view.seats.map((seat, i) => {
            const d = deadBySeat.get(seat);
            const rd = readOf(seat);
            return {
              seat: seatNumber(seat),
              character: cast[i],
              dead: d ? { role: d.role } : undefined,
              truth: xray ? (view.xray.roles[seat] ?? null) : null,
              lit: seat === speaker,
              you: seat === me,
              read: rd
                ? {
                    sure: rd.confidence === 'high',
                    open: card?.seat === seat,
                    onRead: (tile: HTMLElement) =>
                      setCard((c) =>
                        c?.seat === seat ? null : { seat, top: tile.offsetTop },
                      ),
                  }
                : undefined,
            };
          })}
        />
        <TopStrip
          hud={hud}
          title={`Day ${beat.day}`}
          sub={`Discussion · ${beat.label}`}
          {...stripButtons(presentation, slotInput)}
        />
        {card && opened ? (
          <ReadCard
            seat={card.seat}
            character={cast[seatNumber(card.seat) - 1]}
            read={opened}
            truth={view.xray.roles[card.seat] ?? null}
            left={g.wingN + 9.6}
            top={card.top - 8}
          />
        ) : null}
        {dock ? (
          <NoticeZone hud={hud} aside={side}>
            {view.me.role ? <CardButton role={view.me.role.role} /> : null}
            <TurnDock
              dock={dock}
              left={turn?.clock ? countText(turn.clock.remainingMs) : null}
              onSay={onSay}
              onPass={() => onAct?.(null)}
              arrive={animate}
            />
          </NoticeZone>
        ) : character ? (
          <SpeechBox
            hud={hud}
            seat={n}
            character={character}
            line={isPass ? null : slot?.kind === 'speech' ? slot.message : ''}
            page={beat.page?.index}
            onNext={beat.id === 'day.speech' && settled ? onNext : undefined}
            tag={
              agent
                ? { text: 'your seat’s agent spoke for you', tone: 'agent' }
                : speaker === me
                  ? { text: 'you' }
                  : undefined
            }
            xray={
              xray && slot?.kind === 'pass'
                ? { reason: slot.passReason, draft: slot.gatedCandidate }
                : undefined
            }
            arrive={animate}
            thinking={mine || waiting || !settled}
            side={bandNarrows(presentation, beat)}
          />
        ) : null}
      </Layer>
    </>
  );
}
