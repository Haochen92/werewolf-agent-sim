import { Suspense } from 'react';
import { NewRoomClient } from './_components/NewRoomClient';

export const metadata = { title: 'Open a table — Werewolf' };

export default function NewRoomPage() {
  return (
    <Suspense fallback={null}>
      <NewRoomClient />
    </Suspense>
  );
}
