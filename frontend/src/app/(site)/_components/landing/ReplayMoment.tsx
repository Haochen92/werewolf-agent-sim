/**
 * The replay section's exhibit (owner, 2026-10-15): one real moment, what a seat said out loud
 * beside what it wrote down privately, in the stage's own materials: the felt speech patch and
 * the Reveal's ruled note. The words are the log's (features.ts `BLUFF`), seats named as the
 * landing names them.
 */
import { ChipSprite } from '@/stage/cast/ChipSprite';
import { castForGame } from '@/stage/cast/castForGame';
import { BLUFF } from './features';
import classes from './ReplayMoment.module.css';

const CAST = castForGame(BLUFF.game, 10);

/** The log's "player_5" as the landing's "Seat 5". */
const seats = (text: string) => text.replace(/player_(\d+)/gi, 'Seat $1');

export function ReplayMoment() {
  return (
    <figure className={classes.moment}>
      <figcaption className={classes.when}>
        Day {BLUFF.day} &middot; Seat {BLUFF.seat}, the {BLUFF.role}
      </figcaption>
      <blockquote className={classes.felt}>
        <span className={classes.head}>
          <span className={classes.chip}>
            <ChipSprite character={CAST[BLUFF.seat - 1]} small />
          </span>
          Out loud
        </span>
        {seats(BLUFF.said)}
      </blockquote>
      <blockquote className={classes.note}>
        <span className={classes.noteHead}>Its private notes</span>
        {seats(BLUFF.note)}
      </blockquote>
      <p className={classes.after}>
        <b>Seat {BLUFF.victim} was the real Investigator.</b> It called the claim a fake, and the
        table voted it out, {BLUFF.votes}.
      </p>
    </figure>
  );
}
