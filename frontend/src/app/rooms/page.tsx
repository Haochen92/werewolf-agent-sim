import { Suspense } from 'react';
import Link from 'next/link';
import { RoomsClient } from './_components/RoomsClient';
import classes from '@/app/page.module.css';

export const metadata = { title: 'Rooms — Werewolf' };

export default function RoomsPage() {
  return (
    <main className={classes.page}>
      <div className={classes.sectionHead}>
        <h1 className={classes.sectionTitle}>Open tables</h1>
        <Link href="/rooms/new" className={classes.sectionLink}>
          open a table →
        </Link>
        <Link href="/" className={classes.sectionLink}>
          ← home
        </Link>
      </div>
      <Suspense fallback={<div className={classes.skeletonCard} />}>
        <RoomsClient />
      </Suspense>
    </main>
  );
}
