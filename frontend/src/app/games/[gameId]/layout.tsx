import type { ReactNode } from 'react';
import { stageFonts } from '@/stage/fonts';
import { GameCover } from './_components/GameCover';

/**
 * The stage's fonts, for the live game's page (the stage reads them as CSS variables), and the
 * way in, the house's loading picture, held here so it is drawn once from the click (or a
 * reload's first paint) until the page has something to show (`GameCover`).
 */
export default function GameLayout({ children }: { children: ReactNode }) {
  return (
    <div className={stageFonts}>
      <GameCover>{children}</GameCover>
    </div>
  );
}
