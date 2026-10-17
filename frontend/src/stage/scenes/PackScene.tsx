'use client';

/**
 * Night, the pack (handoff §4.7, beat sheet §7): the same room as the acting seat's, painted as
 * the wolves' red-lit compartment. The photos are the seats the pack may choose, which never
 * include a wolf. The pack's talk is in the transcript, its Wolf lines (owner, 2026-10-17: the
 * chat was too small, on a phone most of all); the live game opens it on them for the night.
 *
 * - `pack.your-line`: your round to talk: a line and "Say it" at the foot of the room, or
 *   "Pass" (the ten-seat chat ends once every wolf passed a round).
 * - `pack.line`: a line arrives in the transcript, in the order it was said.
 * - `pack.vote`: the plate is live at once; your packmate's tooth is on their photo if their
 *   vote has arrived; yours lands when you confirm. In the ten-seat game there is no vote: the
 *   carrier alone names the kill here (`carrier_kill`), and each wolf's own skill (the block,
 *   the conceal) is asked after it, in the acting seat's room with the pack's painting.
 * - `pack.decided`: the second tooth lands and the kill is named; the chosen photo is lit (the
 *   ten-seat carrier's one tooth).
 * - A lone wolf: no talk, one tooth.
 * - A tap on the empty room closes the card and clears a vote not yet sent.
 *
 * Arrived at, it is all simply there; played forward, the newest line fades in and the teeth
 * that arrived with the beat land. The room itself (its photos) arrives once, on the first beat
 * the stage comes in on; the pack's beats after it play in the room. A tooth the seat put in
 * from here (its vote, then the kill decided) is already in and does not land again.
 */
import { useState, type ReactNode } from 'react';
import type { NightView } from '@/game/types';
import { SideSlot } from '../SideSlot';
import { ActPlate } from '../instruments/ActPlate';
import { CountText } from '../instruments/CountText';
import { pinColour } from '../instruments/Pin';
import { SayLine, type PackEntry } from '../instruments/PackChat';
import { Tooth } from '../instruments/Tooth';
import { StageMotion } from '../motion';
import { isPackRole, seatNumber } from '../roles';
import { sideOpen } from '../slot';
import { geometry } from '../units';
import { NightRoom } from './NightRoom';
import {
  AGENT_SEALED,
  SENDING_SEALED,
  CHANGE_NOTE,
  LONE_WOLF_SEALED,
  NightCount,
  sealedLabel,
  useSeeded,
} from './ShelfRoomScene';
import type { SceneProps } from './types';

/** How long after arriving a tooth that came with the beat lands (seconds). */
const TOOTH_DELAY = 0.3;

/** The ten-seat pack's night, as the empty chat tells it. */
export const PACK_FLOW =
  'Up to three rounds of talk, then the carrier names the kill, then each wolf’s own skill.';

/** The night's pack talk and votes as chat entries, in the order they happened. */
export function packEntries(night: NightView | null | undefined): PackEntry[] {
  if (!night) return [];
  const out: PackEntry[] = [
    ...night.wolfChannel.map((m): PackEntry =>
      m.wolf === 'game_master'
        ? { kind: 'gm', seq: m.seq, message: m.message }
        : {
            kind: 'line',
            seq: m.seq,
            wolf: m.wolf,
            round: m.round,
            message: m.message,
            passed: m.passed,
          },
    ),
    ...night.wolfVotes.map((v): PackEntry => ({
      kind: 'vote',
      seq: v.seq,
      wolf: v.wolf,
      votee: v.votee,
    })),
  ];
  out.sort((a, b) => a.seq - b.seq);
  if (night.wolfKill) {
    // the decision follows the last vote (the ten-seat carrier's: the last line of talk); the
    // game master's morning note (if any) follows it
    const talk = night.wolfChannel
      .filter((m) => m.wolf !== 'game_master')
      .map((m) => m.seq);
    const at = Math.max(0, ...night.wolfVotes.map((v) => v.seq), ...talk) + 0.5;
    out.push({ kind: 'decided', seq: at, target: night.wolfKill, carrier: night.carrier });
    out.sort((a, b) => a.seq - b.seq);
  }
  return out;
}

export function PackScene(props: SceneProps) {
  const at = `${props.beat.id}:${props.beat.seq}`;
  // the beat the stage came into the room on: the photos arrive with it, and not again
  const [entry] = useState(at);
  return (
    <StageMotion speed={props.presentation.motion}>
      {/* the room stays up across the pack's beats: each line in the chat rebuilt it */}
      <Pack {...props} entering={at === entry} />
      <SideSlot {...props} />
    </StageMotion>
  );
}

function Pack({ entering, ...props }: SceneProps & { entering: boolean }) {
  const { view, beat, me, presentation, onAct, onSay, onDelegate, turn } = props;
  // a new beat, another viewer or a new seeded choice starts the vote and the card afresh
  const seed = `${beat.id}:${beat.seq}:${me}:${turn?.chosen ?? ''}:${turn?.cardOpen ? 1 : 0}`;
  const { animate, hud } = presentation;
  const g = geometry(hud, false);
  const night = view.days[beat.day]?.night ?? null;
  const pack = view.packRoster.length ? view.packRoster : (night?.packRoster ?? []);
  const mate = pack.find((s) => s !== me) ?? null;
  const alone = mate === null;
  const pending = view.me.pending;
  // the nine-seat pack's vote, or the ten-seat carrier naming the kill
  const asked =
    pending?.actionKind === 'wolf_vote' || pending?.actionKind === 'carrier_kill';
  const carrying = pending?.actionKind === 'carrier_kill';
  const voting = beat.id === 'pack.vote' && asked;
  const talking = beat.id === 'pack.your-line';
  // the ten-seat game (its lineup is on the wire): up to three rounds, the carrier, the skills
  const tenSeat = view.lineup.length > 0;
  const myRole = view.me.role?.role;

  // the photos: the server's list while it asks for the kill; otherwise the seats it would offer
  const photos = asked
    ? pending.candidates
    : view.alive.filter((s) => s !== me && !pack.includes(s));

  const [chosen, setChosen] = useSeeded<string | null>(seed, () =>
    voting && turn?.chosen && photos.includes(turn.chosen) ? turn.chosen : null,
  );
  // my vote as sent from here (the server takes one: a sent vote cannot be changed)
  const [sentVote, setSentVote] = useSeeded<string | null>(seed, () =>
    voting && turn?.sent === 'you' ? (turn.chosen ?? null) : null,
  );
  // a failed send reopens the plate; a vote the agent (or another tab) gave seals it
  const failed = !!turn?.sendError && !turn.sent;
  // handed to the seat's agent from the plate: sealed in the agent's words, until a failure
  const [handed, setHanded] = useSeeded(seed, () => false);
  const elsewhere =
    voting && (turn?.sent === 'agent' || turn?.sent === 'closed' || (handed && !failed));
  const mine = failed ? null : sentVote;
  // shut on the choice while it is on its way, but not yet said to be in
  const sending = voting && (!!mine || elsewhere) && !!turn?.sending;
  const [cardOpen, setCardOpen] = useSeeded(seed, () => !!turn?.cardOpen);

  const votes = night?.wolfVotes ?? [];
  const mateVote = mate ? (votes.find((v) => v.wolf === mate)?.votee ?? null) : null;
  const myVote = votes.find((v) => v.wolf === me)?.votee ?? mine;
  const decided =
    beat.id === 'pack.decided' ? (night?.wolfKill ?? beat.subject ?? null) : null;

  // teeth: the packmate's on the left, yours on the right; the ones that came with this beat land
  const marks: Partial<Record<string, ReactNode>> = {};
  const add = (seat: string | null, side: 'left' | 'right', land: number | false) => {
    if (!seat) return;
    marks[seat] = (
      <>
        {marks[seat]}
        {/* the one piece a beat plays again: the teeth that came with it land */}
        <Tooth key={`${side}:${beat.seq}`} side={side} land={land} />
      </>
    );
  };
  const arrived = animate ? TOOTH_DELAY : false;
  // the kill decided after this seat voted from here: its own tooth is already in
  const votedHere = decided !== null && turn?.sent === 'you';
  add(mateVote, 'left', beat.id === 'pack.vote' || decided ? arrived : false);
  add(myVote, 'right', mine ? 0 : decided && !votedHere ? arrived : false);
  // the ten-seat kill has no votes: the carrier's one tooth, on the left when it is the mate's
  const carrier = night?.carrier ?? null;
  if (decided && carrier && !votes.length && !mine)
    add(
      decided,
      carrier === me ? 'right' : 'left',
      carrier === me && votedHere ? false : arrived,
    );

  const lit = decided ?? (voting ? (mine ?? chosen) : null);
  const verb = alone || carrying ? 'Kill' : 'Vote';
  // how the pack's night goes, told until someone has spoken: over your line, or a lone wolf's plate
  const quiet = packEntries(night).length === 0;
  const flow = tenSeat
    ? alone
      ? 'You hunt alone now: no talk tonight. The kill is yours, then your own skill.'
      : `${PACK_FLOW} Round 1 is yours to open.`
    : alone
      ? 'You hunt alone now: no talk tonight, and the vote is yours.'
      : 'Two rounds of talk, then the vote. Round 1 is yours to open.';

  return (
    <NightRoom
      {...props}
      presentation={{ ...presentation, animate: animate && entering }}
      role={myRole && isPackRole(myRole) ? myRole : 'wolf'}
      alone={alone}
      photos={photos}
      lit={lit}
      pin={lit}
      pinHome={!!mine || !!decided}
      seed={seed}
      onChoose={
        voting && !mine && !elsewhere
          ? (seat) => setChosen((c) => (c === seat ? null : seat))
          : undefined
      }
      marks={marks}
      pack={pack}
      cardOpen={cardOpen}
      onCard={setCardOpen}
      onEmpty={() => {
        setCardOpen(false);
        if (!mine && !elsewhere) setChosen(null);
      }}
    >
      {me && talking ? (
        <SayLine
          key={beat.seq}
          draft={turn?.draft ?? ''}
          onSay={onSay}
          // a pass is the act that names no one: `{pass_turn: true}`
          onPass={onAct ? () => onAct(null) : undefined}
          onAgent={onDelegate}
          left={g.wingN + 22.4}
          // the request's own state: shut while on its way or in, reopened on a failure
          seq={beat.seq}
          sent={!!turn?.sent}
          error={turn?.sendError}
          cue={quiet ? flow : undefined}
          note={
            turn?.clock ? (
              <>
                <CountText clock={turn.clock} /> to say it
              </>
            ) : undefined
          }
          hidden={presentation.footHidden}
        />
      ) : null}
      {/* once the vote is in, the lobby's count: the others acting, until the morning */}
      {!sending && (mine || elsewhere || decided || votes.some((v) => v.wolf === me)) ? (
        <NightCount {...props} />
      ) : null}
      {voting ? (
        <ActPlate
          left={g.wingN + 22.4}
          maxWidth={geometry(hud, sideOpen(presentation)).room - 2 * 22.4}
          hidden={presentation.footHidden}
          label={
            mine
              ? `${verb} seat ${seatNumber(mine)}`
              : chosen
                ? `${verb} seat ${seatNumber(chosen)}`
                : 'Choose a seat to kill'
          }
          clock={mine || elsewhere ? null : turn?.clock}
          disabled={!chosen || !!mine}
          onConfirm={() => {
            if (!chosen || mine || elsewhere) return;
            setHanded(false);
            setSentVote(chosen);
            onAct?.(chosen);
          }}
          agent={
            onDelegate && !mine && !elsewhere
              ? {
                  label: 'Let my agent choose',
                  onClick: () => {
                    setHanded(true);
                    onDelegate();
                  },
                }
              : undefined
          }
          note={chosen ? CHANGE_NOTE : alone && quiet && !mine ? flow : undefined}
          error={failed ? turn?.sendError : null}
          sealed={
            mine || elsewhere
              ? {
                  label: sending
                    ? SENDING_SEALED
                    : mine
                      ? carrying
                        ? sealedLabel('carrier_kill', mine)
                        : alone
                          ? LONE_WOLF_SEALED(seatNumber(mine))
                          : sealedLabel('wolf_vote', mine)
                      : AGENT_SEALED,
                  colour: pinColour('wolf'),
                }
              : null
          }
        />
      ) : null}
    </NightRoom>
  );
}
