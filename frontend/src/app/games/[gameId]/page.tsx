import { Suspense } from 'react';
import { GameClient } from './_components/GameClient';

export const metadata = { title: 'Table — Werewolf' };

/**
 * ONE route, three states. Dynamic and client-rendered below this boundary: the live game
 * needs EventSource (browser-only) and the HttpOnly seat cookie, and the skeleton IS the
 * first paint (build_plan §3).
 */
export default async function GamePage({
  params,
}: {
  params: Promise<{ gameId: string }>;
}) {
  const { gameId } = await params;
  return (
    <Suspense fallback={null}>
      <GameClient gameId={gameId} />
    </Suspense>
  );
}
