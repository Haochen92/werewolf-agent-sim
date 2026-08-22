'use client';

/**
 * One day page — the unit the theater paginates by (ux_baseline §3, owner-ruled chat-box
 * UI). Pure presentation over a `DayView` slice; it fetches nothing and gates nothing.
 *
 * Two arrangement decisions worth stating, because the specs leave room:
 *
 * - **Night N renders at the bottom of day N's page, not atop day N+1.** D19 puts the night
 *   section on the current page and D20 puts the night RESULT on the next one; the data
 *   settles it — night N is tagged `day: N` and its GM narration occupies a slot in day N's
 *   own channel. Splitting them would put a day-5 GM line on a day-6 page that does not
 *   exist. Each fact therefore appears in exactly one place, and a scrubber step shows
 *   everything tagged with that day.
 * - **`day_summary` is the one thing that DOES cross the boundary**, because the wire says
 *   so in its own docstring ("shown next morning"): day N's summary renders as the recap
 *   atop day N+1.
 */
import { Fragment } from 'react';
import type { DayView, PrivateResult } from '@/game/types';
import {
  DawnResults,
  GmLine,
  MachineCard,
  NightCard,
  PassRow,
  PrivateResultCard,
  RecapCard,
  SectionRule,
  SpeechBubble,
  VoteBlock,
  WolfChannelSection,
} from './transcript-parts';
import classes from './Transcript.module.css';

export interface DayTranscriptProps {
  day: DayView;
  /** Supplies the recap: day N's page opens with day N−1's summary. */
  previousDay?: DayView;
  roles: Record<string, string>;
  xray: boolean;
  mySeat?: string | null;
  deadSeats?: Set<string>;
  /** Live view expands the recap (it is a real morning briefing); replay collapses it. */
  expandRecap?: boolean;
  /** The live seat's own cards; replay exposes every seat's cards in the inspector instead. */
  privateResults?: PrivateResult[];
  /** Live faction/seat data is already entitled by the server and must not wait for X-ray. */
  showEntitledMachine?: boolean;
  onInspect?: (seat: string) => void;
}

export function DayTranscript({
  day,
  previousDay,
  roles,
  xray,
  mySeat,
  deadSeats,
  expandRecap = false,
  privateResults = [],
  showEntitledMachine = false,
  onInspect,
}: DayTranscriptProps) {
  const visibleSlots = day.slots.filter((slot) => slot.kind !== 'pass' || xray);
  const hasNight = day.night !== null;

  return (
    <div className={`${classes.transcript} ${classes.dayEnter}`} key={day.day}>
      {previousDay?.summary ? (
        <RecapCard summary={previousDay.summary} defaultOpen={expandRecap} />
      ) : null}

      {visibleSlots.length === 0 ? (
        <p className={classes.empty}>
          Nobody spoke on this day.
          {!xray && day.slots.length > 0
            ? ' Turn the X-ray on to see the turns that produced nothing.'
            : ''}
        </p>
      ) : null}

      {visibleSlots.map((slot, index) => {
        const annotations = day.annotations[slot.channelSeq];
        if (slot.kind === 'gm') return <GmLine key={slot.seq} slot={slot} />;
        if (slot.kind === 'pass')
          return <PassRow key={slot.seq} slot={slot} annotations={annotations} />;

        // Consecutive speeches by one speaker merge under a single chip (D10).
        const previous = visibleSlots[index - 1];
        const merged = previous?.kind === 'speech' && previous.player === slot.player;

        return (
          <SpeechBubble
            key={slot.seq}
            slot={slot}
            role={xray ? roles[slot.player] : undefined}
            isSelf={slot.player === mySeat}
            dead={deadSeats?.has(slot.player)}
            merged={merged}
            annotations={xray ? annotations : undefined}
            onInspect={onInspect ? () => onInspect(slot.player) : undefined}
          />
        );
      })}

      <VoteBlock vote={day.vote} roles={xray ? roles : {}} />

      {hasNight ? (
        <NightSection
          day={day}
          roles={roles}
          xray={xray}
          privateResults={privateResults.filter((result) => result.day === day.day)}
          showEntitledMachine={showEntitledMachine}
        />
      ) : null}
    </div>
  );
}

function NightSection({
  day,
  roles,
  xray,
  privateResults,
  showEntitledMachine,
}: {
  day: DayView;
  roles: Record<string, string>;
  xray: boolean;
  privateResults: PrivateResult[];
  showEntitledMachine: boolean;
}) {
  const night = day.night!;
  const showMachine = xray || showEntitledMachine;
  return (
    <div className={`nightPhase ${classes.nightSection}`}>
      <SectionRule>Night {day.day}</SectionRule>
      <div className={classes.transcript} style={{ padding: 0, gap: 'var(--space-4)' }}>
        <NightCard />

        {showMachine ? (
          <>
            <WolfChannelSection
              entries={night.wolfChannel}
              votes={night.wolfVotes}
              wolfKill={night.wolfKill}
              packRoster={night.packRoster}
              roles={roles}
            />
            {night.actions.length > 0 ? (
              <MachineCard label="night actions">
                {night.actions.map((action) => (
                  <Fragment key={action.seq}>
                    {action.actor} ({action.role}) → {action.target}
                    <br />
                  </Fragment>
                ))}
              </MachineCard>
            ) : null}
            {privateResults.map((result) => (
              <PrivateResultCard key={result.seq} result={result} />
            ))}
          </>
        ) : null}

        <DawnResults night={night} />
      </div>
    </div>
  );
}
