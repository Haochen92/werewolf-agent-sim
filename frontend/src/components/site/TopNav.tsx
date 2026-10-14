'use client';

/**
 * The site's nav as the station's signboard (redesign handoff 2026-10-14, §1): the brand (the
 * train's headlamp mark, `scripts/brand-mark.mjs`, and the name in EB Garamond) and the three
 * doors as recessed wells on a wooden board in a brass frame, hung from two brass rods. The
 * current page's door is the cream plate (`aria-current`). The Rooms door carries a split-flap
 * counter of the tables boarding right now (`useBoarding`), blank until the server answers.
 * Pointing at the brand turns the headlamp up. The guide is not a door but an enamel sign
 * screwed to the board (owner, 2026-10-14): after the doors on a desktop, reading "Guide" beside
 * an open book; on a phone the book alone, at the end of the name's row, so the board keeps two
 * rows. On a phone the brand and the sign take the first row and the doors share the second.
 * The pinned strip leaves the sign out on a phone.
 *
 * Once the board has scrolled out of view, a slim strip of the same board slides down and pins
 * to the top (an IntersectionObserver on the board; hidden, the strip is `inert`). In the strip
 * the name stays while it fits whole: the brand is a one-line-high box that wraps the name onto
 * a hidden second line the moment the doors need the room, so it goes cleanly with no
 * breakpoint, leaving the mark.
 */
import { useEffect, useRef, useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import mark from '@/assets/brand/mark-md.svg';
import markLamp from '@/assets/brand/mark-lamp-md.svg';
import { useBoarding } from '@/hooks/useBoarding';
import { SITE } from '@/lib/site';
import classes from './TopNav.module.css';

function Brand({ size }: { size: number }) {
  return (
    <Link href="/" className={classes.brand}>
      <span className={classes.mark} aria-hidden="true">
        <Image src={mark} alt="" width={size} height={size} priority />
        <Image src={markLamp} alt="" width={size} height={size} className={classes.lamp} />
      </span>
      <span className={classes.wordmark}>{SITE.name}</span>
    </Link>
  );
}

/** An open book, the sign's picture. */
function Book() {
  return (
    <svg className={classes.book} viewBox="0 0 16 16" aria-hidden="true">
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

function GuideSign({ path }: { path: string }) {
  return (
    <>
      <span className={classes.divider} aria-hidden="true" />
      <Link
        href={SITE.guide.href}
        className={classes.guide}
        aria-current={path.startsWith(SITE.guide.match) ? 'page' : undefined}
      >
        <Book />
        <span className={classes.guideWord}>{SITE.guide.label}</span>
      </Link>
    </>
  );
}

function Doors({ path, boarding }: { path: string; boarding: number | undefined }) {
  return (
    <ul className={classes.doors}>
      {SITE.nav.map((item) => (
        <li key={item.href}>
          <Link
            href={item.href}
            className={classes.door}
            aria-current={path.startsWith(item.match) ? 'page' : undefined}
          >
            {item.label}
            {item.href === '/rooms' ? (
              <span className={classes.flap}>
                {boarding === undefined ? (
                  <span aria-hidden="true">&nbsp;</span>
                ) : (
                  <>
                    <span className={classes.sr}>{boarding} boarding</span>
                    <span aria-hidden="true">{boarding}</span>
                  </>
                )}
              </span>
            ) : null}
          </Link>
        </li>
      ))}
    </ul>
  );
}

export function TopNav() {
  const path = usePathname() ?? '/';
  const boarding = useBoarding();
  const board = useRef<HTMLElement>(null);
  const [pinned, setPinned] = useState(false);

  useEffect(() => {
    const el = board.current;
    if (!el) return;
    const io = new IntersectionObserver(([entry]) => setPinned(!entry.isIntersecting), {
      threshold: 0,
    });
    io.observe(el);
    return () => io.disconnect();
  }, []);

  return (
    <>
      <div className={classes.hang}>
        <nav ref={board} className={classes.board} aria-label="Site">
          <Brand size={34} />
          <Doors path={path} boarding={boarding} />
          <GuideSign path={path} />
        </nav>
      </div>
      <div
        className={classes.strip}
        data-on={pinned || undefined}
        inert={!pinned}
        aria-hidden={!pinned}
      >
        <nav className={classes.stripRow} aria-label="Pinned">
          <Brand size={28} />
          <Doors path={path} boarding={boarding} />
          <GuideSign path={path} />
        </nav>
      </div>
    </>
  );
}
