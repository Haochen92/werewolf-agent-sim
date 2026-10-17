'use client';

/**
 * A page that fell over while drawing: reported to Sentry (instrumentation-client.ts), and a way
 * back instead of Next's bare "Application error" (owner, 2026-10-17). It replaces the root
 * layout, so it brings its own html and body, and plain elements: the site's providers and
 * fonts are not here.
 */
import { useEffect } from 'react';
import * as Sentry from '@sentry/browser';
import classes from './global-error.module.css';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <html lang="en">
      <body className={classes.body}>
        <main className={classes.main}>
          <h1 className={classes.title}>This page fell over</h1>
          <p className={classes.lede}>
            It has been reported. A game in play carries on without it.
          </p>
          <div className={classes.ways}>
            <button type="button" className={classes.plate} onClick={() => reset()}>
              Try again
            </button>
            {/* a whole page load, not the app's router: the app is what fell over */}
            {/* eslint-disable-next-line @next/next/no-html-link-for-pages */}
            <a className={classes.link} href="/">
              Back to the platform
            </a>
          </div>
        </main>
      </body>
    </html>
  );
}
