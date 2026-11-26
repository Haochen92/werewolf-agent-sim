import { RouteWaitMark } from '@/components/site/PageGate';
import { TrainLoader } from '@/components/TrainLoader';
import classes from './loading.module.css';

/**
 * While a page of the site is on its way (its code not yet in the browser): under the nav, the
 * house's loading picture, after 1 s (as PageGate), so a page that comes quickly never shows it. No least
 * hold here (2026-10-16): the nav's pages are fetched ahead and mostly change at once, and a
 * wait added to every click would slow the whole site. The page's own gate (PageGate) carries
 * the train on when this one was up.
 */
export default function SiteLoading() {
  return (
    <div className={classes.wait}>
      <TrainLoader />
      <RouteWaitMark />
    </div>
  );
}
