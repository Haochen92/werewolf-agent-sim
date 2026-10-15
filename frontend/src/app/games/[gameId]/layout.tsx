import type { ReactNode } from 'react';
import { stageFonts } from '@/stage/fonts';

/** The stage's fonts, for the live game's page (the stage reads them as CSS variables). */
export default function GameLayout({ children }: { children: ReactNode }) {
  return <div className={stageFonts}>{children}</div>;
}
