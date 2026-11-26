/**
 * The replay section's exhibit (owner, 2026-10-15): one real moment, what a seat said out loud
 * beside what it wrote down privately. In the owner's material kit (2026-10-18): a case file on
 * walnut under the stage's Reveal switch, shown on (owner, 2026-10-22: it was a brass plate with
 * the file's name; the switch says what shows this, and the name moved beside it); in a kraft
 * folder, the line said aloud on card under a red ribbon, pinned to its private note clipped on
 * cream, and what came of it. The words are the log's (features.ts `BLUFF`), seats named as the
 * landing names them; the note's own "Do not disclose" is marked, as a reader of the file would.
 */
import { ChipSprite } from '@/stage/cast/ChipSprite';
import { castForGame } from '@/stage/cast/castForGame';
import { stageFonts } from '@/stage/fonts';
import { RevealSign } from '@/stage/instruments/RevealSign';
import { BLUFF } from './features';
import classes from './ReplayMoment.module.css';

const CAST = castForGame(BLUFF.game, 10);

/** The log's "player_5" as the landing's "Seat 5". */
const seats = (text: string) => text.replace(/player_(\d+)/gi, 'Seat $1');

/** The note, its "Do not disclose" marked. */
function marked(text: string) {
  return text.split(/(Do not disclose:?)/).map((part, i) =>
    i % 2 ? (
      <mark key={i} className={classes.mark}>
        {part}
      </mark>
    ) : (
      part
    ),
  );
}

export function ReplayMoment() {
  return (
    <figure className={`${classes.moment} ${stageFonts}`}>
      <figcaption className={classes.when}>
        <RevealSign />
        <span className={classes.who}>
          Day {BLUFF.day} &middot; Seat {BLUFF.seat}, the {BLUFF.role}
        </span>
      </figcaption>
      <div className={classes.folder}>
        <blockquote className={classes.felt}>
          <span className={classes.head}>
            <span className={classes.chip}>
              <ChipSprite character={CAST[BLUFF.seat - 1]} small />
            </span>
            Out loud
          </span>
          {seats(BLUFF.said)}
        </blockquote>
        <span className={classes.pin} aria-hidden="true" />
        <blockquote className={classes.note}>
          <span className={classes.noteHead}>Its private notes</span>
          {marked(seats(BLUFF.note))}
        </blockquote>
        <p className={classes.after}>
          <b>Seat {BLUFF.victim} was the real Investigator.</b> It had checked Seat{' '}
          {BLUFF.seat} and found it Suspicious, and the table voted Seat {BLUFF.victim} out
          with {BLUFF.votes}.
        </p>
      </div>
    </figure>
  );
}
