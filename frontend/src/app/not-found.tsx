import Link from 'next/link';
import { Button, Flapword } from '@/components/site';
import SiteLayout from './(site)/layout';
import classes from './not-found.module.css';

export const metadata = { title: 'Not found' };

/**
 * Any URL the app has no page for: the departures board's CANCELLED, inside the site's own
 * shell (the nav and footer), with the two ways back on. The root `not-found` renders under
 * the root layout only, so it borrows the `(site)` layout to get the chrome.
 */
export default function NotFound() {
  return (
    <SiteLayout>
      <main className={classes.main}>
        <p className={classes.board}>
          <Flapword text="CANCELLED" tone="hot" />
        </p>
        <h1 className={classes.title}>This page isn&rsquo;t on the train</h1>
        <p className={classes.lede}>The link may be mistyped, or the page has moved on.</p>
        <div className={classes.ways}>
          <Button component={Link} href="/" variant="primary">
            Back to the platform
          </Button>
          <Button component={Link} href="/replays">
            Browse the replays
          </Button>
        </div>
      </main>
    </SiteLayout>
  );
}
