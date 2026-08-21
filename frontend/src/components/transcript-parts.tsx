'use client';

/**
 * The transcript's atoms — ux_journeys D10–D15, D19–D20, all presentational and all fed
 * `GameView` slices as typed props (never fetching, never deriving entitlement).
 *
 * They live in one module because they share one stylesheet and are only ever composed
 * together by `DayTranscript`; splitting fourteen ten-line components across fourteen files
 * would be filing, not structure.
 */
import { useState } from 'react';
import { PixelGlyph } from '@/assets/glyphs/PixelGlyph';
import type { DeathGlyphKind } from '@/assets/manifest';
import { SeatChip } from './SeatChip';
import { humanise } from '@/lib/format';
import type {
  Ballot,
  DayVote,
  GmSlot,
  NightView,
  PassSlot,
  SlotAnnotations,
  SpeechSlot,
  WolfEntry,
} from '@/game/types';
import type { NightDeath } from '@/types/contracts';
import classes from './Transcript.module.css';

// --- annotations (X-ray) -----------------------------------------------------

/**
 * The observer-tier tags that hang under a speech or pass: why the scheduler fired this
 * turn, and who the speech addressed. Machine-world styling — this is the instrument
 * reading, sitting directly beneath the story it explains.
 */
export function Annotations({ annotations }: { annotations: SlotAnnotations | undefined }) {
  if (!annotations) return null;
  const { firing, addressed } = annotations;
  if (!firing && addressed.length === 0) return null;

  return (
    <div className={classes.annotations}>
      {firing ? (
        <span className={classes.tag}>
          fired {firing.tier}
          {firing.owes.length > 0 ? ` · owes ${firing.owes.join(', ')}` : ''}
        </span>
      ) : null}
      {addressed.map((target, i) => (
        <span
          key={`${target.target}-${i}`}
          className={`${classes.tag} ${target.stance === 'accusation' ? classes.tagAccusation : ''}`}
        >
          {target.addressed_form} → {target.target}
          {target.stance !== 'neutral' ? ` (${target.stance})` : ''}
        </span>
      ))}
    </div>
  );
}

// --- D10 speech --------------------------------------------------------------

export function SpeechBubble({
  slot,
  role,
  isSelf,
  merged,
  dead,
  annotations,
  onInspect,
}: {
  slot: SpeechSlot;
  role?: string;
  isSelf?: boolean;
  merged?: boolean;
  dead?: boolean;
  annotations?: SlotAnnotations;
  onInspect?: () => void;
}) {
  return (
    <div
      className={[
        classes.speech,
        merged ? classes.merged : '',
        isSelf ? classes.ownSpeech : '',
      ]
        .filter(Boolean)
        .join(' ')}
    >
      <div className={classes.speaker}>
        <SeatChip
          seat={slot.player}
          role={role}
          isSelf={isSelf}
          dead={dead}
          onClick={onInspect}
        />
      </div>
      <div className={classes.bubble}>{slot.message}</div>
      <Annotations annotations={annotations} />
    </div>
  );
}

// --- D11 GM narration --------------------------------------------------------

export function GmLine({ slot }: { slot: GmSlot }) {
  return (
    <p className={classes.gm}>
      <span className={classes.gmMark} aria-hidden="true">
        ❖
      </span>
      <span>{slot.text}</span>
    </p>
  );
}

// --- D12 turn marker (replay X-ray) -----------------------------------------

export function TurnMarkerRow({ player }: { player: string }) {
  return <div className={classes.turnMarker}>— {player} takes a turn —</div>;
}

// --- pass rows + the vetoed speech ------------------------------------------

/**
 * The differentiator, per ux_baseline §3: a novelty-gated pass expands to show what the
 * agent WOULD have said. Collapsed by default so the transcript stays readable, but the
 * toggle is a visible affordance rather than a hover secret — 11 of these exist in the
 * seeded game and they are the reason the X-ray is worth building.
 */
export function PassRow({
  slot,
  annotations,
}: {
  slot: PassSlot;
  annotations?: SlotAnnotations;
}) {
  const [open, setOpen] = useState(false);
  const hasCandidate = slot.gated && Boolean(slot.gatedCandidate);

  return (
    <div>
      <div className={classes.pass}>
        <div className={classes.passHead}>
          <span>{slot.player}</span>
          <span>passed</span>
          {slot.passReason ? (
            <span className={classes.passReason}>
              · {slot.passReason.replace(/_/g, ' ')}
            </span>
          ) : null}
          {hasCandidate ? (
            <button
              type="button"
              className={classes.gatedToggle}
              onClick={() => setOpen((v) => !v)}
              aria-expanded={open}
            >
              {open ? 'hide vetoed line' : 'show vetoed line'}
            </button>
          ) : null}
        </div>
        {open && hasCandidate ? (
          <div className={classes.gatedBody}>
            <span className={classes.gatedLabel}>
              suppressed by the novelty gate — it would have said
            </span>
            {slot.gatedCandidate}
          </div>
        ) : null}
      </div>
      <Annotations annotations={annotations} />
    </div>
  );
}

// --- D13 recap ---------------------------------------------------------------

/**
 * The previous day's summary, shown next morning per the wire's own render rule. Collapsed
 * in replay (the reader just read that day); the live view opens it, since there it is a
 * genuine morning briefing after a night away.
 */
export function RecapCard({
  summary,
  defaultOpen,
}: {
  summary: string;
  defaultOpen?: boolean;
}) {
  return (
    <details className={classes.recap} open={defaultOpen}>
      <summary className={classes.recapSummary}>Previous day</summary>
      <div className={classes.recapBody}>{summary}</div>
    </details>
  );
}

// --- D15 / D20 deaths --------------------------------------------------------

export function DeathBanner({
  player,
  role,
  causes,
  flavour,
}: {
  player: string;
  role: string | null;
  causes: DeathGlyphKind[];
  /** 'lynched' for the day verdict, 'found dead' for dawn. */
  flavour: 'lynched' | 'found dead';
}) {
  return (
    <div className={classes.deathBanner}>
      <span className={classes.deathGlyphs}>
        {causes.map((cause) => (
          <PixelGlyph key={cause} kind={cause} size={18} />
        ))}
      </span>
      <span className={classes.deathText}>
        <strong>{player}</strong> was {flavour}.
        {role ? (
          <>
            {' '}
            They were <span className={classes.deathRole}>{humanise(role)}</span>.
          </>
        ) : null}
      </span>
    </div>
  );
}

export function QuietLine({ children }: { children: React.ReactNode }) {
  return (
    <p className={classes.quietLine}>
      <span className={classes.gmMark} aria-hidden="true">
        ❖
      </span>
      <span>{children}</span>
    </p>
  );
}

// --- D14 vote block ----------------------------------------------------------

/**
 * Ballots arrive as ONE batch at the tally (the server buffers them), so they render as one
 * block grouped per votee — never as one-by-one ballot theater, which is replay-autoplay
 * polish and explicitly parked.
 */
export function VoteBlock({
  vote,
  roles,
}: {
  vote: DayVote;
  roles: Record<string, string>;
}) {
  if (vote.outcome === null) return null;

  const byVotee = new Map<string, Ballot[]>();
  for (const ballot of vote.ballots) {
    const list = byVotee.get(ballot.votee) ?? [];
    list.push(ballot);
    byVotee.set(ballot.votee, list);
  }
  const ordered = [...byVotee.entries()].sort((a, b) => b[1].length - a[1].length);

  return (
    <>
      <div className={classes.sectionRule}>The vote</div>
      {ordered.length > 0 ? (
        <div className={classes.voteBlock}>
          <div className={classes.voteHead}>Ballots</div>
          {ordered.map(([votee, ballots]) => (
            <div key={votee} className={classes.voteRow}>
              <SeatChip seat={votee} role={roles[votee]} />
              <span className={classes.voteArrow}>←</span>
              <span className={classes.voters}>
                {ballots.map((b) => (
                  <SeatChip key={b.seq} seat={b.voter} role={roles[b.voter]} />
                ))}
              </span>
              <span className={classes.voteCount}>×{ballots.length}</span>
            </div>
          ))}
        </div>
      ) : null}
      <VoteOutcome vote={vote} />
    </>
  );
}

function VoteOutcome({ vote }: { vote: DayVote }) {
  if (vote.outcome === 'lynched' && vote.lynched) {
    return (
      <DeathBanner
        player={vote.lynched}
        role={vote.lynchedRole}
        causes={['lynch']}
        flavour="lynched"
      />
    );
  }
  // tie / abstain / no_vote — a quiet GM line, never a banner (D15).
  const streak =
    vote.noLynchStreak > 1 ? ` — ${vote.noLynchStreak} days now without a lynch` : '';
  const reason =
    vote.outcome === 'tie'
      ? 'the village split its vote'
      : vote.outcome === 'abstain'
        ? 'the village chose no one'
        : 'no one called for a vote';
  return (
    <QuietLine>
      The village couldn’t decide: {reason}
      {streak}.
    </QuietLine>
  );
}

// --- D19 night ---------------------------------------------------------------

export function NightCard({ children }: { children?: React.ReactNode }) {
  return <div className={classes.nightCard}>{children ?? 'The village sleeps.'}</div>;
}

export function WolfChannelSection({
  entries,
  wolfKill,
  roles,
}: {
  entries: WolfEntry[];
  wolfKill: string | null;
  roles: Record<string, string>;
}) {
  if (entries.length === 0 && !wolfKill) return null;
  return (
    <div className={classes.wolfChannel}>
      <div className={classes.wolfHead}>The pack</div>
      {entries.map((entry) =>
        entry.wolf === 'game_master' ? (
          // The server-authored SK-whiff note: a GM line INSIDE the tint.
          <p key={entry.seq} className={classes.wolfGm}>
            <span className={classes.gmMark} aria-hidden="true">
              ❖
            </span>
            <span>{entry.message}</span>
          </p>
        ) : (
          <div key={entry.seq} className={classes.wolfEntry}>
            <SeatChip seat={entry.wolf} role={roles[entry.wolf]} />
            <div className={classes.wolfBubble}>{entry.message}</div>
          </div>
        ),
      )}
      {wolfKill ? (
        <div className={classes.packBanner}>the pack has chosen: {wolfKill}</div>
      ) : null}
    </div>
  );
}

export function MachineCard({
  label,
  children,
}: {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <div className={classes.machineCard}>
      <span className={classes.machineLabel}>{label}</span>
      {children}
    </div>
  );
}

// --- D20 dawn ----------------------------------------------------------------

export function DawnResults({ night }: { night: NightView }) {
  if (!night.resolved) return null;
  return (
    <>
      {night.deaths.map((death: NightDeath) => (
        <DeathBanner
          key={death.player}
          player={death.player}
          role={death.role}
          causes={death.attacker_types as DeathGlyphKind[]}
          flavour="found dead"
        />
      ))}
      {night.save ? (
        <QuietLine>Someone was attacked in the night — and survived.</QuietLine>
      ) : null}
      {night.deaths.length === 0 && !night.save ? (
        <QuietLine>A quiet night.</QuietLine>
      ) : null}
    </>
  );
}

export function SectionRule({ children }: { children: React.ReactNode }) {
  return <div className={classes.sectionRule}>{children}</div>;
}

export { classes as transcriptClasses };
