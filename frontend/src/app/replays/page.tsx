import { Suspense } from 'react';
import { ReplayListClient } from './_components/ReplayListClient';

export const metadata = { title: 'Replays — Werewolf' };

export default function ReplaysPage() {
  return (
    <main style={{ padding: 24, fontFamily: 'system-ui' }}>
      <h1>Replays</h1>
      <Suspense fallback={<p>Loading…</p>}>
        <ReplayListClient />
      </Suspense>
    </main>
  );
}
