/**
 * Crash reports from the player's browser to Sentry (owner, 2026-10-17): a page that falls over
 * on someone's phone is otherwise invisible to us (the server never hears of it). Errors only, no
 * session replay and no tracing, and only in the deployed build: the image's build bakes in
 * NEXT_PUBLIC_SENTRY_DSN, so local and e2e builds send nothing. Next runs this file before the
 * page starts.
 */
import * as Sentry from '@sentry/browser';

const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN;

if (dsn) {
  Sentry.init({
    dsn,
    environment: 'production',
    // every category of collected data named and off: the SDK's own default collects
    dataCollection: {
      userInfo: false,
      cookies: false,
      httpHeaders: false,
      httpBodies: [],
      urlQueryParams: false,
      stackFrameVariables: false,
    },
    tracesSampleRate: 0,
    // typing is never kept, even as "a key was pressed in this field": the ticket's key field
    // and the player's lines are the page's only private input
    beforeBreadcrumb: (crumb) => (crumb.category === 'ui.input' ? null : crumb),
  });
}
