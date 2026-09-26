/**
 * A word on split-flap tiles (the mockups' `.flapword` / `.flap`), as on the departures board:
 * one tile per character, a gap for a space. Screen readers get the word once, not the tiles.
 * The tiles scale with the surrounding font size.
 */
import classes from './Flapword.module.css';

export function Flapword({
  text,
  tone,
  className,
}: {
  text: string;
  /** `hot` lights the letters amber (BOARDING); `dim` greys them (a hidden code). */
  tone?: 'hot' | 'dim';
  className?: string;
}) {
  const cls = [classes.word, tone ? classes[tone] : '', className ?? '']
    .filter(Boolean)
    .join(' ');
  return (
    <span className={cls}>
      <span className={classes.sr}>{text}</span>
      {[...text].map((c, i) =>
        c === ' ' ? (
          <span key={i} className={classes.space} aria-hidden="true" />
        ) : (
          <span key={i} className={classes.flap} aria-hidden="true">
            {c}
          </span>
        ),
      )}
    </span>
  );
}
