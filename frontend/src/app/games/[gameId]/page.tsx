import { Suspense } from 'react';
import { StationStill } from '@/stage/scenes/StationStill';
import { GameClient } from './_components/GameClient';

export const metadata = { title: 'Table' };

/**
 * ONE route, three states. Dynamic and client-rendered below this boundary: the live game
 * needs EventSource (browser-only) and the HttpOnly seat cookie, and the skeleton IS the
 * first paint (build_plan §3). While it loads, the empty platform (`StationStill`, beat sheet §1a).
 */
export default async function GamePage({
  params,
}: {
  params: Promise<{ gameId: string }>;
}) {
  const { gameId } = await params;
  return (
    <Suspense fallback={<StationStill what="game" line="Boarding…" />}>
      <GameClient gameId={gameId} />
    </Suspense>
  );
}
