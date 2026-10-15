import type { ReactNode } from 'react';
import { stageFonts } from '@/stage/fonts';

/** The stage's fonts, for the replay's page (the stage reads them as CSS variables). */
export default function ReplayLayout({ children }: { children: ReactNode }) {
  return <div className={stageFonts}>{children}</div>;
}
