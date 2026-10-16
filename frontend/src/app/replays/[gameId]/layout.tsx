import { Suspense, type ReactNode } from 'react';
import { stageFonts } from '@/stage/fonts';
import { ReplayCover } from './_components/ReplayCover';

/**
 * The stage's fonts, for the replay's page (the stage reads them as CSS variables), and its way
 * in, the house's loading picture: a link prefetches the layout, so the cover is up at the click
 * and is never drawn twice (`ReplayCover`). The Suspense boundary is what its `useSearchParams`
 * asks for.
 */
export default function ReplayLayout({ children }: { children: ReactNode }) {
  return (
    <div className={stageFonts}>
      <Suspense fallback={null}>
        <ReplayCover>{children}</ReplayCover>
      </Suspense>
    </div>
  );
}
