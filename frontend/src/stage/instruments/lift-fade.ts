/**
 * How much of a load on the lift shows, so that it reads as one thing going into the floor.
 *
 * The lift cuts its load off at the trap's front lip. For a table that is right for the table
 * itself, but not for what stands on it: the table's top goes under the lip while the jar and
 * the chip towers, taller and further back, are still above it, and for a moment they hang over
 * the dark hole with nothing under them. So the whole load fades as it goes down: whole until
 * one line of it (the cloth's hem) reaches the lip, gone by the time a second, higher one (the
 * back of the table's top) does. By then the table under the props has gone in, so nothing is
 * left standing over the hole.
 *
 * The fade follows where the load is, not the clock, so it can never run ahead of the move or
 * lag behind it, and a rise plays it backwards for free. Kept apart from the component so it
 * can be tested.
 */

/**
 * The load's opacity when it is `offset` units below its resting place. `lines` are two of its
 * lines at rest, in world units: the one whose reaching the lip starts the fade (lower on the
 * screen), and the one whose reaching it ends the fade (higher).
 */
export function loadOpacity(
  offset: number,
  lip: number,
  lines: readonly [number, number],
): number {
  const [start, end] = lines;
  // the offsets at which each line reaches the lip
  const from = lip - start,
    to = lip - end;
  // one line (or the two swapped): a clean cut where the first meets the lip
  if (to <= from) return offset < from ? 1 : 0;
  return Math.min(1, Math.max(0, (to - offset) / (to - from)));
}
