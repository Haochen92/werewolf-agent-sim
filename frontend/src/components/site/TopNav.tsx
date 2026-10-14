'use client';

/**
 * The site's nav as the station's signboard (redesign handoff 2026-10-14, §1): the brand (the
 * train's headlamp mark, `scripts/brand-mark.mjs`, and the name in EB Garamond) and the three
 * doors as recessed wells on a wooden board in a brass frame, hung from two brass rods. The
 * current page's door is the cream plate (`aria-current`). The Rooms door carries a split-flap
 * counter of the tables boarding right now (`useBoarding`), blank until the server answers.
 * Pointing at the brand turns the headlamp up. On a phone the brand takes the first row and the
 * doors share the second.
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
        </nav>
      </div>
    </>
  );
}
