'use client';

/**
 * Night, the pack (handoff §4.7, beat sheet §7): the same room as the acting seat's, painted as
 * the wolves' red-lit compartment. Your packmate is in the chat, not on the line; the photos
 * are the seats the pack may choose, which never include a wolf.
 *
 * - `pack.your-line`: your round to talk: a line and "Say it" at the foot of the room.
 * - `pack.line`: a line arrives in the chat, in the order it was said.
 * - `pack.vote`: the plate is live at once; your packmate's tooth is on their photo if their
 *   vote has arrived; yours lands when you confirm.
 * - `pack.decided`: the second tooth lands and the kill is named; the chosen photo is lit.
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
import { PackChat, type PackEntry } from '../instruments/PackChat';
import { Tooth } from '../instruments/Tooth';
import { StageMotion } from '../motion';
import { seatNumber } from '../roles';
import { geometry } from '../units';
import { NightRoom } from './NightRoom';
import {
  AGENT_SEALED,
  CHANGE_NOTE,
  LONE_WOLF_SEALED,
  NightCount,
  sealedLabel,
} from './ShelfRoomScene';
import type { SceneProps } from './types';

/** How long after arriving a tooth that came with the beat lands (seconds). */
const TOOTH_DELAY = 0.3;

/** The night's pack talk and votes as chat entries, in the order they happened. */
export function packEntries(night: NightView | null | undefined): PackEntry[] {
  if (!night) return [];
  const out: PackEntry[] = [
    ...night.wolfChannel.map((m): PackEntry =>
      m.wolf === 'game_master'
        ? { kind: 'gm', seq: m.seq, message: m.message }
        : { kind: 'line', seq: m.seq, wolf: m.wolf, round: m.round, message: m.message },
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
    // the decision follows the last vote; the game master's morning note (if any) follows it
    const at = Math.max(0, ...night.wolfVotes.map((v) => v.seq)) + 0.5;
    out.push({ kind: 'decided', seq: at, target: night.wolfKill });
    out.sort((a, b) => a.seq - b.seq);
  }
  return out;
}

export function PackScene(props: SceneProps) {
  const t = props.turn;
  const at = `${props.beat.id}:${props.beat.seq}`;
  // the beat the stage came into the room on: the photos arrive with it, and not again
  const [entry] = useState(at);
  return (
    <StageMotion speed={props.presentation.motion}>
      <Pack
        key={`${at}:${props.me}:${t?.chosen ?? ''}:${t?.cardOpen ? 1 : 0}`}
        {...props}
        entering={at === entry}
      />
      <SideSlot {...props} />
    </StageMotion>
  );
}

function Pack({ entering, ...props }: SceneProps & { entering: boolean }) {
  const { view, beat, me, presentation, onAct, onSay, turn } = props;
  const { animate, cast, hud } = presentation;
  const g = geometry(hud, false);
  const night = view.days[beat.day]?.night ?? null;
  const pack = view.packRoster.length ? view.packRoster : (night?.packRoster ?? []);
  const mate = pack.find((s) => s !== me) ?? null;
  const alone = mate === null;
  const pending = view.me.pending;
  const voting = beat.id === 'pack.vote' && pending?.actionKind === 'wolf_vote';
  const talking = beat.id === 'pack.your-line';

  // the photos: the server's list while it asks for the vote; otherwise the seats it would offer
  const photos =
    pending?.actionKind === 'wolf_vote'
      ? pending.candidates
      : view.alive.filter((s) => s !== me && !pack.includes(s));

  const [chosen, setChosen] = useState<string | null>(
    voting && turn?.chosen && photos.includes(turn.chosen) ? turn.chosen : null,
  );
  // my vote as sent from here (the server takes one: a sent vote cannot be changed)
  const [sentVote, setSentVote] = useState<string | null>(
    voting && turn?.sent === 'you' ? (turn.chosen ?? null) : null,
  );
  // a failed send reopens the plate; a vote the agent (or another tab) gave seals it
  const failed = !!turn?.sendError && !turn.sent;
  const elsewhere = voting && (turn?.sent === 'agent' || turn?.sent === 'closed');
  const mine = failed ? null : sentVote;
  const [cardOpen, setCardOpen] = useState(!!turn?.cardOpen);

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
        <Tooth key={side} side={side} land={land} />
      </>
    );
  };
  const arrived = animate ? TOOTH_DELAY : false;
  // the kill decided after this seat voted from here: its own tooth is already in
  const votedHere = decided !== null && turn?.sent === 'you';
  add(mateVote, 'left', beat.id === 'pack.vote' || decided ? arrived : false);
  add(myVote, 'right', mine ? 0 : decided && !votedHere ? arrived : false);

  const entries = packEntries(night);
  if (mine && !votes.some((v) => v.wolf === me) && me)
    entries.push({ kind: 'vote', seq: Number.MAX_SAFE_INTEGER, wolf: me, votee: mine });

  const lit = decided ?? (voting ? (mine ?? chosen) : null);
  const verb = alone ? 'Kill' : 'Vote';
  const empty = alone
    ? 'You hunt alone now: no talk tonight, and the vote is yours.'
    : talking && entries.length === 0
      ? 'Two rounds of talk, then the vote. Round 1 is yours to open.'
      : 'Two rounds of talk, then the vote.';

  return (
    <NightRoom
      {...props}
      presentation={{ ...presentation, animate: animate && entering }}
      role="wolf"
      alone={alone}
      photos={photos}
      lit={lit}
      pin={lit}
      pinHome={!!mine || !!decided}
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
      {me ? (
        <PackChat
          entries={entries}
          you={me}
          mate={mate}
          cast={cast}
          empty={empty}
          arriving={beat.id === 'pack.line' ? beat.seq : undefined}
          arrive={animate}
          input={
            talking
              ? {
                  draft: turn?.draft ?? '',
                  onSay,
                  left: g.wingN + 22.4,
                  note: turn?.clock ? (
                    <>
                      <CountText clock={turn.clock} /> to say it
                    </>
                  ) : undefined,
                }
              : undefined
          }
        />
      ) : null}
      {/* once the vote is in, the lobby's count: the others acting, until the morning */}
      {mine || elsewhere || decided || votes.some((v) => v.wolf === me) ? (
        <NightCount {...props} />
      ) : null}
      {voting ? (
        <ActPlate
          left={g.wingN + 22.4}
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
            setSentVote(chosen);
            onAct?.(chosen);
          }}
          note={chosen ? CHANGE_NOTE : undefined}
          error={failed ? turn?.sendError : null}
          sealed={
            mine || elsewhere
              ? {
                  label: mine
                    ? alone
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
