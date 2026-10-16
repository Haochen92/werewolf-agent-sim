import { Suspense, type ReactNode } from 'react';
import { stageFonts } from '@/stage/fonts';
import { DepartureHost } from './_components/DepartureHost';

/**
 * The stage's fonts, for the replay's page (the stage reads them as CSS variables), and its way
 * in, the train's departure: a link prefetches the layout, so the departure starts at the click
 * and is never drawn twice (`DepartureHost`). The Suspense boundary is what its
 * `useSearchParams` asks for.
 */
export default function ReplayLayout({ children }: { children: ReactNode }) {
  return (
    <div className={stageFonts}>
      <Suspense fallback={null}>
        <DepartureHost>{children}</DepartureHost>
      </Suspense>
    </div>
  );
}
