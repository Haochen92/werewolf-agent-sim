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
 * - The rounds (Phase 2, beat sheet §2 rows 7-10): `day.opening-prepares`, the stand empty and
 *   a walnut notice where the box would be, every seat of the round lit on the wing;
 *   `day.round-passes`, the same notice naming the seats of the round that said nothing;
 *   `day.closing-called`, the first accused at the stand thinking while the box carries the
 *   moderator's line, then the accused's own lines play as any turn, without rising again.
 *
 * Played forward (`presentation.animate`), the puppet rises into the stand thinking (the box
 * holding a "…"), then talks and the line comes into the box. Arrived at (a seek, a refresh), it is all simply there.
 */
import { useEffect, useState } from 'react';
import { type DayState } from '@/assets/manifest';
import type { GameView, PassSlot, SpeechSlot } from '@/game/types';
import { Layer } from '../Stage';
import { Puppet } from '../cast/Puppet';
import { ReadCard } from '../film/ReadCard';
import { freshReads, turnReads } from '../film/film-model';
import { CardButton, Notice, NoticeZone } from '../instruments/Notice';
import { SpeechBox } from '../instruments/SpeechBox';
import { Plaque, Stand } from '../instruments/Stand';
import { TurnDock } from '../instruments/TurnDock';
import { useMotionScale } from '../motion';
import { ROLE_NAME, factionOf, seatNumber } from '../roles';
import { bandNarrows, sideOpen } from '../slot';
import { geometry } from '../units';
import { CarSetSpec } from './CarScene';
import type { SceneProps } from './types';

/** How long the arriving puppet stands thinking before it speaks, after the rise (seconds). */
const THINK = 0.6;

/**
 * A turn's key: a new beat is a new turn, except a line (or a pass) after its own thinking (or
 * after the seat's own turn at the dock), and the same beat again: its next page, or the live
 * list cut afresh as an event arrives (a new copy of the beat, not a new beat).
 */
const turnKey = (b: SceneProps['beat']) => `${b.id}:${b.seq}`;
export const continues = (was: SceneProps['beat'], now: SceneProps['beat']) =>
  turnKey(was) === turnKey(now) ||
  ((was.id === 'day.turn-thinking' ||
    was.id === 'day.your-turn' ||
    was.id === 'day.closing-called') &&
    (now.id === 'day.speech' || now.id === 'day.pass') &&
    now.subject === (was.subject ?? was.seat) &&
    now.day === was.day);

/** The beats with nobody at the stand: a notice stands where the box would be. */
const isNotice = (beat: SceneProps['beat']) =>
  beat.id === 'day.opening-prepares' || beat.id === 'day.round-passes';

/** "seats 2, 5 and 8", with the viewer's own seat as "you" (first). */
function seatsPhrase(seats: readonly string[], me: string | null): string {
  const others: string[] = [];
  let you = false;
  for (const seat of seats) {
    if (seat === me) you = true;
    else others.push(`${seatNumber(seat)}`);
  }
  const numbers =
    others.length === 0
      ? ''
      : others.length === 1
        ? `seat ${others[0]}`
        : `seats ${others.slice(0, -1).join(', ')} and ${others[others.length - 1]}`;
  if (you && numbers) return `you and ${numbers}`;
  if (you) return 'you';
  return numbers;
}

/** The notice's line for a round's passes (beat sheet §2 row 9). */
function passesLine(
  round: 'opening' | 'closing' | null,
  quiet: readonly string[],
  players: readonly string[],
  me: string | null,
): string {
  const everyone = players.length > 0 && quiet.length === players.length;
  if (round === 'closing') {
    const who = seatsPhrase(quiet, me);
    return `${who[0].toUpperCase()}${who.slice(1)} said nothing in defence.`;
  }
  if (everyone) return 'Nobody had anything to put on the table.';
  const who = seatsPhrase(quiet, me);
  return `${who[0].toUpperCase()}${who.slice(1)} had nothing to put on the table.`;
}

/** The round a beat belongs to, as the fold recorded it (`round_opened`). */
function roundOf(view: GameView, beat: SceneProps['beat']) {
  const rounds = view.days[beat.day]?.rounds ?? [];
  for (const round of rounds) {
    if (round.seq === beat.seq) return round;
  }
  return null;
}

/** The moderator's line the closing was called with: the last game-master slot before the beat. */
function moderatorLine(view: GameView, beat: SceneProps['beat']): string | null {
  let text: string | null = null;
  for (const slot of view.days[beat.day]?.slots ?? []) {
    if (slot.kind === 'gm' && slot.seq < beat.seq) text = slot.text;
  }
  return text;
}

/** The day's body under the car's host (CarScene.tsx). */
export function DayBody(props: SceneProps) {
  // live, the thinking puppet is already at the stand when its line arrives: it does not rise again
  const [on, setOn] = useState({ beat: props.beat, key: turnKey(props.beat) });
  if (on.beat !== props.beat)
    setOn({
      beat: props.beat,
      key: continues(on.beat, props.beat) ? on.key : turnKey(props.beat),
    });
  return (
    <>
      {/* the set stays up from turn to turn: nothing on it plays again, and a phone's browser
          cannot afford its pictures rebuilt beat after beat (build log §8.3) */}
      <DaySet {...props} turnKey={on.key} />
      {/* a new beat is a new turn: the arrival replays from the start */}
      <DayTurn key={on.key} {...props} />
    </>
  );
}

/** Whose turn the beat is: my own (the dock), or the speaker's seat and its puppet. */
function speakerOf(beat: SceneProps['beat'], cast: SceneProps['presentation']['cast']) {
  const mine = beat.id === 'day.your-turn';
  const speaker = beat.subject ?? (mine ? (beat.seat ?? null) : null);
  const n = speaker ? seatNumber(speaker) : 0;
  return { mine, speaker, n, character: n ? cast[n - 1] : null };
}

/**
 * The car round the turn: the paint, the house light, the wing and the strip, described to the
 * car's host (CarScene.tsx), which keeps them up from turn to turn and from scene to scene, so a
 * beat costs the browser the puppet and the box, not the car's pictures over again. `turnKey`
 * is the turn on the stage: a read card opened on the wing belongs to it and goes with it.
 */
function DaySet({
  view,
  beat,
  presentation,
  turnKey: at,
}: SceneProps & { turnKey: string }) {
  const { hud, xray, cast } = presentation;
  const side = sideOpen(presentation);
  const g = geometry(hud, side);
  const { speaker, character } = speakerOf(beat, cast);

  // the X-ray's reads on the wing: the speaker's reads of the table when it spoke; a tap on a
  // seat opens its card, level with the tile
  const reads = xray ? turnReads(view, beat) : null;
  // the reads new or changed since the speaker's previous ones flash once on their tiles
  const fresh = freshReads(view, reads);
  const [card, setCard] = useState<{ seat: string; top: number; turn: string } | null>(
    null,
  );
  const readOf = (seat: string) => reads?.reads.find((r) => r.player === seat);
  const open = card?.turn === at ? card : null;
  const opened = open ? readOf(open.seat) : undefined;

  // the speaker's pool, where the light falls with no pool given (paint/light.ts `poolOf`)
  const pool = {
    x: g.cx,
    y: g.railY - g.pwid * 0.1,
    rx: g.pwid * 0.66,
    ry: g.pwid * 0.82,
  };
  return (
    <>
      <CarSetSpec
        phase="day"
        shutter={{ state: 'open' }}
        // the painted room reads as lit: the speaker's pool says "this one", the room stays warm
        light={{ pool, dark: 24 }}
        wing={{
          truth: (seat) => (xray ? (view.xray.roles[seat] ?? null) : null),
          // the speaker; or, at a round's notice, every seat the notice is about
          lit: (seat) => seat === speaker || (beat.subjects?.includes(seat) ?? false),
          read: (seat) => {
            const rd = readOf(seat);
            return rd
              ? {
                  sure: rd.confidence === 'high',
                  open: open?.seat === seat,
                  fresh: fresh.has(seat) ? `${reads?.seq}` : null,
                  onRead: (tile: HTMLElement) =>
                    setCard((c) =>
                      c?.seat === seat && c.turn === at
                        ? null
                        : { seat, top: tile.offsetTop, turn: at },
                    ),
                }
              : undefined;
          },
        }}
        strip={{ title: `Day ${beat.day}`, sub: `Discussion · ${beat.label}` }}
      />
      <Layer name="hud">
        {open && opened ? (
          <ReadCard
            seat={open.seat}
            character={cast[seatNumber(open.seat) - 1]}
            speaker={reads?.player ?? speaker ?? open.seat}
            speakerCharacter={character ?? undefined}
            read={opened}
            truth={view.xray.roles[open.seat] ?? null}
            left={g.wingN + 9.6}
            top={open.top - 8}
          />
        ) : null}
      </Layer>
    </>
  );
}

/** The turn itself: the puppet at the stand, its plate, and the box (or the dock) at the foot. */
function DayTurn({ view, beat, me, presentation, turn, onSay, onAct, onNext }: SceneProps) {
  const { hud, xray, animate, cast } = presentation;
  const k = useMotionScale();
  const side = sideOpen(presentation);
  const g = geometry(hud, side);

  // my own turn: the beat is mine (`seat`), with no line yet
  const { mine, speaker, n, character } = speakerOf(beat, cast);
  const slot = (view.days[beat.day]?.slots ?? []).find((s) => s.seq === beat.seq) as
    SpeechSlot | PassSlot | undefined;
  const isPass = beat.id === 'day.pass';
  // live: the seat has the stand and no line yet
  const waiting = beat.id === 'day.turn-thinking';
  // the accused called to answer: at the stand thinking, the moderator's line in the box
  const called = beat.id === 'day.closing-called';
  const notice = isNotice(beat);

  // Played forward: arrive thinking, then speak. At rest: already speaking.
  const [settled, setSettled] = useState(!animate);
  const [risen, setRisen] = useState(!animate);
  useEffect(() => {
    if (!risen || settled) return;
    const t = setTimeout(() => setSettled(true), THINK * k * 1000);
    return () => clearTimeout(t);
  }, [risen, settled, k]);

  const state: DayState =
    mine || waiting || called || !settled ? 'thinking' : isPass ? 'base' : 'talking';
  // my line, said by my seat's agent: only my screen is told
  const agent = !mine && speaker !== null && speaker === me && !!turn?.agentSpoke;
  const dock = mine && turn?.dock && !turn.dock.closed ? turn.dock : null;
  const role = speaker ? view.xray.roles[speaker] : undefined;

  return (
    <>
      <Layer name="figures">
        {character ? (
          <Puppet
            g={g}
            shadow
            glass
            character={character}
            // the stand's plate names the seat: no numeral on the belly
            seat={null}
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

      <Layer name="hud">
        {dock ? (
          <NoticeZone hud={hud} aside={side}>
            {view.me.role ? (
              <CardButton role={view.me.role.role} onOpen={turn?.onCard} />
            ) : null}
            <TurnDock
              dock={dock}
              clock={turn?.clock ?? null}
              onSay={onSay}
              onPass={() => onAct?.(null)}
              arrive={animate}
            />
          </NoticeZone>
        ) : notice ? (
          <NoticeZone hud={hud} aside={side}>
            <Notice
              walnut
              wide
              arrive={animate}
              title={
                beat.id === 'day.opening-prepares'
                  ? beat.day === 1
                    ? 'Everyone is writing their opening, before the first night.'
                    : 'Everyone is writing their opening.'
                  : passesLine(
                      roundOf(view, beat)?.round ?? null,
                      beat.subjects ?? [],
                      roundOf(view, beat)?.players ?? [],
                      me,
                    )
              }
            />
          </NoticeZone>
        ) : character ? (
          <SpeechBox
            hud={hud}
            seat={n}
            character={character}
            line={
              called
                ? moderatorLine(view, beat)
                : isPass
                  ? null
                  : slot?.kind === 'speech'
                    ? slot.message
                    : ''
            }
            page={beat.page?.index}
            onNext={beat.id === 'day.speech' && settled ? onNext : undefined}
            tag={
              called
                ? { text: 'the moderator' }
                : agent
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
            // the called seat thinks while the box carries the moderator's line, not a "…"
            thinking={mine || waiting || (!settled && !called)}
            side={bandNarrows(presentation, beat)}
          />
        ) : null}
      </Layer>
    </>
  );
}
