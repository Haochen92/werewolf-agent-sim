import { StationWall, wallPage } from '@/components/site';
import { ArchiveClient } from './_components/ArchiveClient';
import classes from './_components/Archive.module.css';

export const metadata = { title: 'Replays' };

/**
 * The archive: every finished game, filtered in the browser (replays mockup, review §A2), in the
 * latest games' room (the platform's tile, an oxblood band, a pendant).
 */
export default function ReplaysPage() {
  return (
    <main className={`${classes.archive} ${wallPage}`}>
      <StationWall kind="records" />
      <header className={classes.head}>
        <h1 className={classes.title}>The archive</h1>
        <p className={classes.lede}>
          Every finished game with Reveal on: every role, the wolves&rsquo; private talk, each
          agent&rsquo;s thinking. Pick one to watch.
        </p>
      </header>
      <ArchiveClient />
    </main>
  );
}
