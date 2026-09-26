import { Suspense } from 'react';
import { PlayClient } from './_components/PlayClient';

export const metadata = { title: 'Play' };

export default function PlayPage() {
  return (
    <Suspense fallback={null}>
      <PlayClient />
    </Suspense>
  );
}
