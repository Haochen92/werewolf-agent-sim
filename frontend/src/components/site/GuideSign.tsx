/**
 * The guide's one look, wherever a page points at it (owner, 2026-10-15): the navy enamel sign
 * with the open book, the nav's sign at a size for a page. The nav draws its own sign from the
 * same kit (TopNav, Board.module.css `enamel`) and the same book, so the guide reads as one
 * object across the site: something to read, never a door to play.
 */
import Link from 'next/link';
import { SITE } from '@/lib/site';
import classes from './GuideSign.module.css';

/** An open book, the sign's picture. */
export function Book({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 16 16" aria-hidden="true">
      <path
        d="M1.5 3.6c2.2-1 4.4-.9 6.5.6 2.1-1.5 4.3-1.6 6.5-.6v9c-2.2-1-4.4-.9-6.5.6-2.1-1.5-4.3-1.6-6.5-.6z"
        fill="#f2ead6"
      />
      <path d="M8 4.3v9" stroke="#16243f" strokeWidth="1.1" />
      <path
        d="M3.3 6h3M3.3 8h3M3.3 10h3M9.7 6h3M9.7 8h3M9.7 10h3"
        stroke="#16243f"
        strokeWidth=".7"
        strokeOpacity=".55"
      />
    </svg>
  );
}

/** The sign on a page: the book and "Gameplay guide", linking to the guide. */
export function GuideSign({ className }: { className?: string }) {
  return (
    <Link href={SITE.guide.href} className={`${classes.sign} ${className ?? ''}`}>
      <Book className={classes.book} />
      Gameplay guide
    </Link>
  );
}
