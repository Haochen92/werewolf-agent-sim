'use client';

/**
 * The turn dock (D17) — one component, a form per `action_kind`. The list is closed at
 * eight kinds and each is one of exactly two shapes:
 *
 *   free text  → discuss, wolf_discuss
 *   target pick → vote, wolf_vote, healer_target, investigator_target,
 *                 serial_killer_target, vigilante_target
 *
 * The server's `candidates` list is the ONLY source of legal targets. The client never
 * derives eligibility — abstain and hold-fire appear precisely when the server lists them,
 * because they are sentinels inside that same list.
 *
 * Errors follow the same rule. A 422 is the engine's own contract explaining itself, so it
 * renders VERBATIM; paraphrasing would mean inventing rules the engine never stated. A 409
 * means someone (or the AFK timer) already answered — the form clears and re-syncs.
 */
import { useEffect, useState } from 'react';
import { useMutation } from '@tanstack/react-query';
import { rejoinGame, submitTurn, type TurnPayload, isTextTurn } from '@/lib/api';
import { ApiError } from '@/lib/request';
import { seatToken } from '@/lib/storage';
import { useCountdown } from '@/hooks/useCountdown';
import type { MeView } from '@/game/types';
import type { ActionKind } from '@/types/contracts';
import { SeatChip } from './SeatChip';
import classes from './TurnDock.module.css';

const PROMPTS: Record<ActionKind, string> = {
  discuss: 'Your turn — speak, or pass',
  wolf_discuss: 'Wolf night talk — message your pack',
  vote: 'Cast your vote',
  wolf_vote: 'Wolf night — your binding kill vote',
  healer_target: 'Choose someone to protect tonight',
  investigator_target: 'Choose someone to investigate',
  serial_killer_target: 'Choose tonight’s victim',
  vigilante_target: 'Choose a target, or hold your fire',
};

/** Sentinels the server lists among candidates; they are choices, not people. */
const SENTINEL_LABELS: Record<string, string> = {
  abstain: 'Abstain — vote for no one',
  hold_fire: 'Hold your fire tonight',
  no_target: 'No target',
};

export function TurnDock({
  gameId,
  pending,
  seats,
  onSubmitted,
}: {
  gameId: string;
  pending: NonNullable<MeView['pending']>;
  seats: string[];
  onSubmitted: () => void;
}) {
  const [message, setMessage] = useState('');
  const [target, setTarget] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const kind = pending.actionKind;
  const isText = isTextTurn(kind);
  const isWolf = kind === 'wolf_discuss' || kind === 'wolf_vote';
  const countdown = useCountdown(pending.deadline);

  // A new request means a new turn: never carry a half-typed message across turns.
  useEffect(() => {
    setMessage('');
    setTarget(null);
    setError(null);
  }, [pending.seq]);

  const mutation = useMutation({
    mutationFn: async (payload: TurnPayload) => {
      try {
        return await submitTurn(gameId, payload);
      } catch (err) {
        if (!(err instanceof ApiError) || !err.isSeatLost) throw err;
        const token = seatToken.get(gameId);
        if (!token) throw err;
        try {
          await rejoinGame(gameId, token);
        } catch (rejoinError) {
          seatToken.clear(gameId);
          throw rejoinError;
        }
        // The payload is immutable and the first request was rejected before reaching the
        // engine. Re-submit exactly once now that the HttpOnly cookie has been restored.
        return submitTurn(gameId, payload);
      }
    },
    onSuccess: () => {
      setError(null);
      onSubmitted();
    },
    onError: (err) => {
      if (err instanceof ApiError && err.isConflict) {
        // Already answered — by the AFK delegate, or by a double submit.
        setError('That turn was already answered. Catching up…');
        onSubmitted();
        return;
      }
      setError(err instanceof Error ? err.message : 'Could not submit that turn.');
    },
  });

  const busy = mutation.isPending;
  const send = (payload: TurnPayload) => mutation.mutate(payload);

  return (
    <div className={`${classes.dock} ${isWolf ? classes.wolfDock : ''}`}>
      <div className={classes.prompt}>
        <span>{PROMPTS[kind]}</span>
      </div>

      {isText ? (
        <textarea
          className={classes.textarea}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder={
            kind === 'wolf_discuss' ? 'Say something to your pack…' : 'Say something…'
          }
          disabled={busy}
          autoFocus
        />
      ) : (
        <div className={classes.targets} role="radiogroup" aria-label="Choose a target">
          {pending.candidates.map((candidate) => {
            const isSeat = seats.includes(candidate);
            return (
              <button
                key={candidate}
                type="button"
                role="radio"
                aria-checked={target === candidate}
                className={`${classes.target} ${target === candidate ? classes.targetPicked : ''}`}
                onClick={() => setTarget(candidate)}
                disabled={busy}
              >
                {isSeat ? (
                  <SeatChip seat={candidate} />
                ) : (
                  <span className={classes.sentinel}>
                    {SENTINEL_LABELS[candidate] ?? candidate.replace(/_/g, ' ')}
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      <div className={classes.actions}>
        {countdown.secondsLeft !== null ? (
          <CountdownRing
            seconds={countdown.secondsLeft}
            fraction={countdown.fraction ?? 0}
          />
        ) : null}

        <button
          type="button"
          className={classes.primary}
          disabled={busy || (isText ? message.trim().length === 0 : target === null)}
          onClick={() =>
            send(isText ? { message: message.trim() } : { target: target as string })
          }
        >
          {isText ? 'Speak' : 'Confirm'}
        </button>

        {kind === 'discuss' ? (
          // The wire carries no `can_pass`, so the affordance is offered and the SERVER
          // decides: on a reactive turn it answers 422 and that message renders below,
          // verbatim. Better an honest rejection than a button hidden on a guess.
          <button
            type="button"
            className={classes.secondary}
            disabled={busy}
            onClick={() => send({ pass_turn: true })}
          >
            Pass
          </button>
        ) : null}

        <span className={classes.spacer} />

        <button
          type="button"
          className={classes.secondary}
          disabled={busy}
          onClick={() => send({ delegate: true })}
          title="Hand this turn to your agent — legal in every phase"
        >
          Let my agent decide
        </button>
      </div>

      {error ? (
        <p className={classes.error} role="alert">
          {error}
        </p>
      ) : null}
    </div>
  );
}

/** D18: a ring around the submit action, amber until the last ten seconds, then red. */
function CountdownRing({ seconds, fraction }: { seconds: number; fraction: number }) {
  const radius = 12;
  const circumference = 2 * Math.PI * radius;
  return (
    <div className={`${classes.ring} ${seconds <= 10 ? classes.ringUrgent : ''}`}>
      <svg className={classes.ringSvg} width="30" height="30" viewBox="0 0 30 30">
        <circle
          className={classes.ringTrack}
          cx="15"
          cy="15"
          r={radius}
          fill="none"
          strokeWidth="2"
        />
        <circle
          className={classes.ringProgress}
          cx="15"
          cy="15"
          r={radius}
          fill="none"
          strokeWidth="2"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - fraction)}
        />
      </svg>
      <span className={classes.ringLabel}>{seconds}</span>
    </div>
  );
}

/** D21: the dock's permanent replacement once your seat is dead. */
export function GhostBar() {
  return <div className={classes.ghostBar}>You’re watching as a ghost.</div>;
}

/** D18: the anonymous pacing strip. Never moves backwards — the store enforces that. */
export function PacingStrip({
  stage,
  done,
  total,
}: {
  stage: 'night' | 'day_vote';
  done: number;
  total: number;
}) {
  const label = stage === 'night' ? 'the village stirs' : 'votes are in';
  const pct = total > 0 ? Math.min(100, Math.round((done / total) * 100)) : 0;
  return (
    <div className={classes.pacing}>
      <span>
        {label}: {done} of {total}
      </span>
      <span className={classes.pacingTrack}>
        <span className={classes.pacingFill} style={{ width: `${pct}%` }} />
      </span>
    </div>
  );
}

/** D12: "Ralph is thinking…" at the transcript tail, live only. */
export function ThinkingRow({ player }: { player: string }) {
  return (
    <div className={classes.thinking}>
      <SeatChip seat={player} />
      <span>is thinking</span>
      <span className={classes.thinkingDots}>
        <span>.</span>
        <span>.</span>
        <span>.</span>
      </span>
    </div>
  );
}
