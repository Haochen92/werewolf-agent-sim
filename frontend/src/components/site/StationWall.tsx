/**
 * A page's wall in the station: a picture of the room's wall behind the whole page (owner,
 * 2026-10-18), so every page is a room of the station. `records` is the archive (navy panels
 * between filing drawers, a pendant); `granite` the ticket office (brick over panelling, its
 * window and lamp); `cards` the guide (the green room). The landing and the departures hall have
 * pictures of their own (Rooms.module.css, rooms/page.tsx).
 *
 * It spans the screen from the very top of the page, behind the nav's board: placed against the
 * site layout's `.station` (the screen's width, the page's height, which cuts it off at the
 * page's foot), under everything in the page's own stacking context (give the page's `<main>`
 * `wallPage`). Still, no masks or filters (StationWall.module.css).
 */
import classes from './StationWall.module.css';

/** The class a page's `<main>` takes so its wall paints above the page's ground. */
export const wallPage = classes.page;

export function StationWall({ kind }: { kind: 'records' | 'granite' | 'cards' }) {
  return <div className={`${classes.wall} ${classes[kind]}`} aria-hidden="true" />;
}
