import type { DurableGameEvent } from '@/types/contracts';

export type ResolutionEvent = Extract<
  DurableGameEvent,
  { type: 'lynch_result' | 'night_result' }
>;

export function nextLiveResolution(
  events: readonly DurableGameEvent[],
  liveSeqs: ReadonlySet<number>,
  seenSeqs: ReadonlySet<number>,
): ResolutionEvent | null {
  return (
    events.find(
      (event): event is ResolutionEvent =>
        (event.type === 'lynch_result' || event.type === 'night_result') &&
        liveSeqs.has(event.seq) &&
        !seenSeqs.has(event.seq),
    ) ?? null
  );
}

export function resolutionAnnouncement(
  resolution: ResolutionEvent,
  events: readonly DurableGameEvent[],
): string {
  const gm = [...events]
    .reverse()
    .find(
      (event) =>
        event.type === 'gm_message' &&
        event.day === resolution.day &&
        event.seq < resolution.seq,
    );
  if (gm?.type === 'gm_message') return gm.text.trim();

  if (resolution.type === 'lynch_result') {
    if (resolution.player) {
      return `${resolution.player} was voted out${
        resolution.role ? ` and was a ${resolution.role.replaceAll('_', ' ')}` : ''
      }.`;
    }
    return 'No one was eliminated today.';
  }

  if (resolution.deaths.length > 0) {
    return resolution.deaths
      .map(
        (death) =>
          `${death.player} died during the night. They were a ${death.role.replaceAll('_', ' ')}.`,
      )
      .join(' ');
  }
  return resolution.save ? 'Someone was attacked and saved.' : 'No one died last night.';
}

export function resolutionLabel(resolution: ResolutionEvent): string {
  return resolution.type === 'lynch_result'
    ? `Day ${resolution.day} verdict`
    : `Dawn after Night ${resolution.day}`;
}
