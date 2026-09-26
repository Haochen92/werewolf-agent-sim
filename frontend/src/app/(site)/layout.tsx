import type { ReactNode } from 'react';
import { IconSprite, SiteFooter, TopNav } from '@/components/site';
import classes from './layout.module.css';

/**
 * The site shell: the top nav and the footer around every page that is not the theatre
 * (`/`, `/play`, `/rooms`, `/rooms/new`, `/replays`). `(site)` is a route group, so it adds
 * nothing to the URLs; the theatre's routes (`/games/[id]`, `/replays/[id]`, `/workbench`) sit
 * outside it and get no chrome.
 */
export default function SiteLayout({ children }: { children: ReactNode }) {
  return (
    <div className={classes.site}>
      <IconSprite />
      <TopNav />
      {children}
      <SiteFooter />
    </div>
  );
}
