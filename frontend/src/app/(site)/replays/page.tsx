import { StationWall, wallPage } from '@/components/site';
import { listReplaysWithTotal, type ReplayPage } from '@/lib/api';
import { SERVER_API_URL } from '@/lib/config';
import { ARCHIVE_LIMIT } from '@/lib/replay-filters';
import { PageMusic } from '@/music/PageMusic';
import { ArchiveClient } from './_components/ArchiveClient';
import classes from './_components/Archive.module.css';

export const metadata = { title: 'Replays' };

/** The page is drawn again, with the newest list, at most every 30 s (a game ends rarely). */
export const revalidate = 30;

/**
 * The list, asked for here on the server and sent in the page, so a phone draws the slates with
 * the first paint: asked for from the browser, it waited on the page's code, 4–10 s on a slow
 * phone (2026-10-15). Without the API's inside address (dev, the tests, the build) or when the
 * API does not answer, the page goes without, and the browser asks as before.
 */
async function firstList(): Promise<ReplayPage | null> {
  if (!SERVER_API_URL) return null;
  try {
    return await listReplaysWithTotal({ limit: ARCHIVE_LIMIT });
  } catch {
    return null;
  }
}

/**
 * The archive: every finished game, filtered in the browser (replays mockup, review §A2), in the
 * latest games' room (the platform's tile, an oxblood band, a pendant).
 */
export default async function ReplaysPage() {
  const initial = await firstList();
  return (
    <main className={`${classes.archive} ${wallPage}`}>
      <StationWall kind="records" />
      <PageMusic bed="lobby" />
      <header className={classes.head}>
        <h1 className={classes.title}>The archive</h1>
        <p className={classes.lede}>
          Every finished game with Reveal on: every role, the wolves&rsquo; private talk,
          each agent&rsquo;s thinking. Pick one to watch.
        </p>
      </header>
      <ArchiveClient initial={initial} />
    </main>
  );
}
