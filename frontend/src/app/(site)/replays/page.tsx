import { ArchiveClient } from './_components/ArchiveClient';
import classes from './_components/Archive.module.css';

export const metadata = { title: 'Replays' };

/** The archive: every finished game, filtered in the browser (replays mockup, review §A2). */
export default function ReplaysPage() {
  return (
    <main className={classes.archive}>
      <header className={classes.head}>
        <h1 className={classes.title}>The archive</h1>
        <p className={classes.lede}>
          Every finished game, with the X-ray open: every role from the first minute, the
          wolves&rsquo; private talk, and what each agent was thinking. Pick one to watch it
          in the theatre.
        </p>
      </header>
      <ArchiveClient />
    </main>
  );
}
