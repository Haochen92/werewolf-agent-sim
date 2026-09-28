'use client';

/**
 * The site's top bar (the landing mockup's `nav`): the brand, the mark (a brass escutcheon
 * whose keyhole is a 9, `scripts/brand-mark.mjs`) beside the product name, and the three
 * doors. Pointing at the brand X-rays the mark: the keyhole shows the film's cyan grid. The
 * current page's link is marked with `aria-current`, which also underlines it.
 */
import Image from 'next/image';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import mark from '@/assets/brand/mark-md.svg';
import markXray from '@/assets/brand/mark-xray-md.svg';
import { SITE } from '@/lib/site';
import classes from './TopNav.module.css';

export function TopNav() {
  const path = usePathname() ?? '/';
  return (
    <nav className={classes.nav} aria-label="Site">
      <Link href="/" className={classes.brand}>
        <span className={classes.mark} aria-hidden="true">
          <Image src={mark} alt="" width={28} height={28} priority />
          <Image src={markXray} alt="" width={28} height={28} className={classes.xray} />
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
