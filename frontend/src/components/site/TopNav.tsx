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
 * The pinned strip keeps the book on a phone too, at its right end (owner, 2026-10-15).
 * On a page whose music is the viewer's to turn on (the landing, the guide, the archive, the
 * rooms), the music's switch follows the sign: a speaker alone, so it fits the phone's strip
 * (owner, 2026-10-15).
 *
 * Once the board has scrolled out of view, a slim strip of the same board slides down and pins
 * to the top (an IntersectionObserver on the board; hidden, the strip is `inert`). In the strip
 * the name stays while it fits whole: the brand is a one-line-high box that wraps the name onto
 * a hidden second line the moment the doors need the room, so it goes cleanly with no
 * breakpoint, leaving the mark.
 *
 * A page may put its own bar in the strip's place on a phone (SiteStrip: the guide's section
 * bar); the strip then stays up there, and the page's bar comes down instead.
 *
 * The strip says how tall it is on the page's root, for what a page pins to the top under it
 * (the guide's section line, its side nav): `--site-strip` while it is down (0 while it is up),
 * `--site-strip-reach` always (where an anchor must land clear of it).
 */
import { useEffect, useRef } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import mark from '@/assets/brand/mark-md.svg';
import markLamp from '@/assets/brand/mark-lamp-md.svg';
import { useBoarding } from '@/hooks/useBoarding';
import { SITE } from '@/lib/site';
import { useMusicState } from '@/music/music';
import { SoundButton } from '@/music/SoundButton';
import { Book } from './GuideSign';
import { useSiteStrip } from './SiteStrip';
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

function GuideSign({ path }: { path: string }) {
  return (
    <>
      <span className={classes.divider} aria-hidden="true" />
      <Link
        href={SITE.guide.href}
        className={classes.guide}
        aria-current={path.startsWith(SITE.guide.match) ? 'page' : undefined}
      >
        <Book className={classes.book} />
        <span className={classes.guideWord}>{SITE.guide.label}</span>
      </Link>
    </>
  );
}

/** The music's switch, on a page with music of its own (`useMusicBed`, an opt-in bed). */
function Music() {
  const here = useMusicState((s) => s.optInPages > 0);
  return here ? <SoundButton optIn className={classes.music} /> : null;
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
  const { pinned, setPinned, replaced, board } = useSiteStrip();
  const strip = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = board.current;
    if (!el) return;
    const io = new IntersectionObserver(([entry]) => setPinned(!entry.isIntersecting), {
      threshold: 0,
    });
    io.observe(el);
    return () => io.disconnect();
  }, [board, setPinned]);

  useEffect(() => {
    const el = strip.current;
    if (!el) return;
    const root = document.documentElement.style;
    // its layout height: the slide is a transform, so this is the height it has when down
    const set = () => {
      root.setProperty('--site-strip-reach', `${el.offsetHeight}px`);
      root.setProperty('--site-strip', pinned ? `${el.offsetHeight}px` : '0px');
    };
    set();
    const ro = new ResizeObserver(set);
    ro.observe(el);
    return () => {
      ro.disconnect();
      root.removeProperty('--site-strip');
      root.removeProperty('--site-strip-reach');
    };
  }, [pinned]);

  return (
    <>
      <div className={classes.hang}>
        <nav ref={board} className={classes.board} aria-label="Site">
          <Brand size={34} />
          <Doors path={path} boarding={boarding} />
          <GuideSign path={path} />
          <Music />
        </nav>
      </div>
      <div
        ref={strip}
        className={classes.strip}
        data-on={pinned || undefined}
        data-replaced={replaced || undefined}
        inert={!pinned}
        aria-hidden={!pinned}
      >
        <nav className={classes.stripRow} aria-label="Pinned">
          <Brand size={28} />
          <Doors path={path} boarding={boarding} />
          <GuideSign path={path} />
          <Music />
        </nav>
      </div>
    </>
  );
}
