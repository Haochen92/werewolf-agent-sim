'use client';

/**
 * The site's top bar (the landing mockup's `nav`): the brand, the mark (a brass escutcheon
 * whose keyhole is a 9, `scripts/brand-mark.mjs`) beside the product name, and the three
 * doors under a brass rule. The name is set in the paper serif, in brass, so the bar never
 * reads as part of the page's own heavy sans headings; the doors are small-caps signage.
 * The brand is the way home (there is no Home door). Pointing at the brand lights a lamp in
 * the carriage: the keyhole glows amber. The current page's link is marked with
 * `aria-current`, which also underlines it.
 */
import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import mark from '@/assets/brand/mark-md.svg';
import markLamp from '@/assets/brand/mark-lamp-md.svg';
import { SITE } from '@/lib/site';
import classes from './TopNav.module.css';

export function TopNav() {
  const path = usePathname() ?? '/';
  return (
    <nav className={classes.nav} aria-label="Site">
      <Link href="/" className={classes.brand}>
        <span className={classes.mark} aria-hidden="true">
          <Image src={mark} alt="" width={28} height={28} priority />
          <Image src={markLamp} alt="" width={28} height={28} className={classes.lamp} />
        </span>
        {SITE.name}
      </Link>
      <ul className={classes.links}>
        {SITE.nav.map((item) => (
          <li key={item.href}>
            <Link
              href={item.href}
              className={classes.link}
              aria-current={path.startsWith(item.match) ? 'page' : undefined}
            >
              {item.label}
            </Link>
          </li>
        ))}
      </ul>
    </nav>
  );
}
