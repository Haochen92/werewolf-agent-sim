import { TrainLoader } from '@/components/TrainLoader';
import classes from './loading.module.css';

/**
 * While a page of the site is on its way (its code not yet in the browser): under the nav, the
 * house's loading picture, after 0.3 s, so a page that comes at once never shows it. No least
 * hold here (2026-10-16): the nav's pages are fetched ahead and mostly change at once, and a
 * wait added to every click would slow the whole site.
 */
export default function SiteLoading() {
  return (
    <div className={classes.wait}>
      <TrainLoader />
    </div>
  );
}
