import { Suspense } from 'react';
import { StationStill } from '@/stage/scenes/StationStill';
import { TheaterClient } from './_components/TheaterClient';

export const metadata = { title: 'Replay' };

// Dynamic segment, rendered on demand; everything below this boundary is client-side —
// the theater is interaction-bound (scrubber, X-ray) and the skeleton IS the first paint
// (build_plan §3). The Suspense boundary is also what `useSearchParams` requires; while it
// waits, the empty platform (`StationStill`, beat sheet §1a).
export default async function ReplayTheaterPage({
  params,
}: {
  params: Promise<{ gameId: string }>;
}) {
  const { gameId } = await params;
  return (
    <Suspense
      fallback={<StationStill what="replay" hud="replay" line="Rewinding the reels…" />}
    >
      <TheaterClient gameId={gameId} />
    </Suspense>
  );
}
