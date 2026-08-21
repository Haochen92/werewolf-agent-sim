import { Suspense } from 'react';
import { PlayClient } from './_components/PlayClient';

export const metadata = { title: 'Quick game — Werewolf' };

export default function PlayPage() {
  return (
    <Suspense fallback={null}>
      <PlayClient />
    </Suspense>
  );
}
