import type { Metadata } from 'next';
import type { ReactNode } from 'react';
import { stageFonts } from '@/stage/fonts';

export const metadata: Metadata = { title: 'Workbench' };

/** The stage's fonts, for every workbench page (the stage reads them as CSS variables). */
export default function WorkbenchLayout({ children }: { children: ReactNode }) {
  return <div className={stageFonts}>{children}</div>;
}
