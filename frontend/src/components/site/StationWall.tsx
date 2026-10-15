/**
 * A page's wall in the station (owner, 2026-10-14): the landing's rooms behind the other site
 * pages, so every page is a room you have already walked through. `records` is the latest
 * games' room for the archive (the platform's tile, an oxblood band, a pendant); `granite` is
 * the reading room for the ticket office (granite blocks under a caged wall light); `cards` is
 * the roles' card room for the guide (the green tile, lit from above). The departures hall uses
 * the landing's platform itself (`PlatformBackdrop`).
 *
 * It spans the screen from the very top of the page, behind the nav's board, as the landing's
 * platform does: placed against the site layout's `.station` (the screen's width, the page's
 * height, which cuts it off at the page's foot), under everything in the page's own stacking
 * context (give the page's `<main>` `wallPage`). Still, no masks or filters, and capped where
 * its light runs out (StationWall.module.css).
 */
import { Pendant, WallLight } from './StationLamps';
import classes from './StationWall.module.css';

/** The class a page's `<main>` takes so its wall paints above the page's ground. */
export const wallPage = classes.page;

export function StationWall({ kind }: { kind: 'records' | 'granite' | 'cards' }) {
  return (
    <div className={`${classes.wall} ${classes[kind]}`} aria-hidden="true">
      {kind === 'records' ? <Pendant className={classes.pendant} /> : null}
      {kind === 'granite' ? <WallLight className={classes.wallLight} /> : null}
    </div>
  );
}
