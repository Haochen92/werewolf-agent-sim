'use client';

/**
 * A prompt's countdown as text (`1:14`), ticking on its own: the one piece that renders again
 * every tick, so the dock, the ballot or the pack's line around it stays still.
 */
import { useTimeLeft } from '@/hooks/useCountdown';
import { countText, type TurnClock } from '../countdown';

export function CountText({ clock }: { clock: TurnClock }) {
  return <>{countText(useTimeLeft(clock.deadline, clock.at))}</>;
}
