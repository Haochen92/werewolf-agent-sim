import type { ReactNode } from 'react';
import { IconSprite, SiteFooter, TopNav } from '@/components/site';
import classes from './layout.module.css';

/**
 * The site shell: the top nav and the footer around every page that is not the theatre
 * (`/`, `/play`, `/rooms`, `/rooms/new`, `/replays`). `(site)` is a route group, so it adds
 * nothing to the URLs; the theatre's routes (`/games/[id]`, `/replays/[id]`, `/workbench`) sit
 * outside it and get no chrome. The station round the column is what a page's wall is placed
 * in and clipped to (StationWall, PlatformBackdrop): the screen's width, the page's height, so a
 * wall taller than a short page never lengthens it.
 */
export default function SiteLayout({ children }: { children: ReactNode }) {
  return (
    <div className={classes.station}>
      <div className={classes.site}>
        <IconSprite />
        <TopNav />
        {children}
        <SiteFooter />
      </div>
    </div>
  );
}
