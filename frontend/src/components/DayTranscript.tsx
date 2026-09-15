'use client';

/**
 * One day page — the unit the theater paginates by (ux_baseline §3, owner-ruled chat-box
 * UI). Pure presentation over a `DayView` slice; it fetches nothing and gates nothing.
 *
 * Two arrangement decisions worth stating, because the specs leave room:
 *
 * - **Night N's actions render on day N; its result renders as dawn atop day N+1.** While
 *   the next day does not exist yet (or the game ends at night), the result remains at the
 *   bottom of day N so it cannot disappear. Once day N+1 arrives, the same structured
 *   result moves to its natural reading position as that day's opening fact.
 * - **Day N's summary renders atop day N+1, under the X-ray only.** It is what the agents
 *   carry into that day, the one memory of day N they keep, so it belongs with the machine
 *   view. It is not a recap for the reader (ruled 2026-09-15): a human just lived through
 *   day N, and the text is written for a context window, not a page.
 */
import { Fragment } from 'react';
import type { DayView, PrivateResult } from '@/game/types';
import {
  CarriedSummaryCard,
  DawnResults,
  GmLine,
  MachineCard,
  NightCard,
  PassRow,
  PrivateResultCard,
  SectionRule,
  SpeechBubble,
  VoteBlock,
  WolfChannelSection,
} from './transcript-parts';
import classes from './Transcript.module.css';

export interface DayTranscriptProps {
  day: DayView;
  /** Supplies dawn and the carried summary: day N's page opens with what day N−1 left. */
  previousDay?: DayView;
  /** Lets the night section move a settled result forward instead of rendering it twice. */
  nextDay?: DayView;
  roles: Record<string, string>;
  xray: boolean;
  mySeat?: string | null;
  deadSeats?: Set<string>;
  /** The live seat's own cards; replay exposes every seat's cards in the inspector instead. */
  privateResults?: PrivateResult[];
  /** Live faction/seat data is already entitled by the server and must not wait for X-ray. */
  showEntitledMachine?: boolean;
  onInspect?: (seat: string) => void;
}

export function DayTranscript({
  day,
  previousDay,
  nextDay,
  roles,
  xray,
  mySeat,
  deadSeats,
  privateResults = [],
  showEntitledMachine = false,
  onInspect,
}: DayTranscriptProps) {
  const visibleSlots = day.slots.filter((slot) => slot.kind !== 'pass' || xray);
  const hasNight = day.night !== null;

  return (
    <div className={`${classes.transcript} ${classes.dayEnter}`} key={day.day}>
      {previousDay?.night?.resolved ? (
        <div className={classes.dawnArrival}>
          <SectionRule>Dawn of Day {day.day}</SectionRule>
          <DawnResults night={previousDay.night} />
        </div>
      ) : null}

      {xray && previousDay ? (
        <CarriedSummaryCard
          day={previousDay.day}
          structured={previousDay.summaryStructured}
          text={previousDay.summary}
        />
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
          showDawn={!nextDay}
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
  showDawn,
}: {
  day: DayView;
  roles: Record<string, string>;
  xray: boolean;
  privateResults: PrivateResult[];
  showEntitledMachine: boolean;
  showDawn: boolean;
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

        {showDawn ? <DawnResults night={night} /> : null}
      </div>
    </div>
  );
}
