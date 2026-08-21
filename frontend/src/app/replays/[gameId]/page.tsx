import { Suspense } from 'react';
import { TheaterClient } from './_components/TheaterClient';

export const metadata = { title: 'Replay — Werewolf' };

// Dynamic segment, rendered on demand; everything below this boundary is client-side —
// the theater is interaction-bound (scrubber, X-ray) and the skeleton IS the first paint
// (build_plan §3). The Suspense boundary is also what `useSearchParams` requires.
export default async function ReplayTheaterPage({
  params,
}: {
  params: Promise<{ gameId: string }>;
}) {
  const { gameId } = await params;
  return (
    <Suspense fallback={null}>
      <TheaterClient gameId={gameId} />
    </Suspense>
  );
}
