'use client';

/**
 * Night, the pack (handoff §4.7, beat sheet §7): the same room as the acting seat's, with the
 * wolves' kit on the shelf. Your packmate is in the chat, not on the shelf; the dolls are the
 * seats the pack may choose, which never include a wolf.
 *
 * - `pack.your-line`: your round to talk: a line and "Say it" at the foot of the room.
 * - `pack.line`: a line arrives in the chat, in the order it was said.
 * - `pack.vote`: the plate is live at once; your packmate's tooth is on their doll if their
 *   vote has arrived; yours lands when you confirm.
 * - `pack.decided`: the second tooth lands and the kill is named; the chosen doll is lit.
 * - A lone wolf: no talk, one tooth.
 *
 * Arrived at, it is all simply there; played forward, the newest line fades in and the teeth
 * that arrived with the beat land.
 */
import { useState, type ReactNode } from 'react';
import type { NightView } from '@/game/types';
import { SideSlot } from '../SideSlot';
import { countText } from '../countdown';
import { ActPlate } from '../instruments/ActPlate';
import { PackChat, type PackEntry } from '../instruments/PackChat';
import { Tooth } from '../instruments/Tooth';
import { StageMotion } from '../motion';
import { seatNumber } from '../roles';
import { geometry } from '../units';
import { NightRoom } from './NightRoom';
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
  return (
    <StageMotion speed={props.presentation.motion}>
      <Pack
        key={`${props.beat.id}:${props.beat.seq}:${props.me}:${t?.chosen ?? ''}:${t?.cardOpen ? 1 : 0}`}
        {...props}
      />
      <SideSlot {...props} />
    </StageMotion>
  );
}

function Pack(props: SceneProps) {
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

  // the dolls: the server's list while it asks for the vote; otherwise the seats it would offer
  const dolls =
    pending?.actionKind === 'wolf_vote'
      ? pending.candidates
      : view.alive.filter((s) => s !== me && !pack.includes(s));

  const [chosen, setChosen] = useState<string | null>(
    voting && turn?.chosen && dolls.includes(turn.chosen) ? turn.chosen : null,
  );
  const [mine, setMine] = useState<string | null>(null);
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
  add(mateVote, 'left', beat.id === 'pack.vote' || decided ? arrived : false);
  add(myVote, 'right', mine ? 0 : decided ? arrived : false);

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
      role="wolf"
      alone={alone}
      dolls={dolls}
      lit={lit}
      pin={lit}
      onChoose={
        voting && !mine ? (seat) => setChosen((c) => (c === seat ? null : seat)) : undefined
      }
      marks={marks}
      pack={pack}
      cardOpen={cardOpen}
      onCard={setCardOpen}
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
                  note: turn?.clock
                    ? `${countText(turn.clock.remainingMs)} to say it`
                    : undefined,
                }
              : undefined
          }
        />
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
          clock={mine ? null : turn?.clock}
          disabled={!chosen || !!mine}
          onConfirm={() => {
            if (!chosen || mine) return;
            setMine(chosen);
            onAct?.(chosen);
          }}
        />
      ) : null}
    </NightRoom>
  );
}
