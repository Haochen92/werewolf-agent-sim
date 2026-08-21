import { Suspense } from 'react';
import Link from 'next/link';
import { ReplayListClient } from './_components/ReplayListClient';
import classes from '@/app/page.module.css';

export const metadata = { title: 'Replays — Werewolf' };

export default function ReplaysPage() {
  return (
    <main className={classes.page}>
      <div className={classes.sectionHead}>
        <h1 className={classes.sectionTitle}>Replays</h1>
        <Link href="/" className={classes.sectionLink}>
          ← home
        </Link>
      </div>
      <Suspense fallback={<div className={classes.skeletonCard} />}>
        <ReplayListClient />
      </Suspense>
    </main>
  );
}
