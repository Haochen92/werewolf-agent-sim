import { Suspense } from 'react';
import { TheaterClient } from './_components/TheaterClient';

export const metadata = { title: 'Replay — Werewolf' };

// Dynamic segment, rendered on demand; everything below this boundary is client-side
// (the theater is interaction-bound and the skeleton IS the first paint) — build_plan §3.
export default async function ReplayTheaterPage({
  params,
}: {
  params: Promise<{ gameId: string }>;
}) {
  const { gameId } = await params;
  return (
    <main style={{ padding: 24, fontFamily: 'system-ui' }}>
      <Suspense fallback={<p>Loading replay…</p>}>
        <TheaterClient gameId={gameId} />
      </Suspense>
    </main>
  );
}
