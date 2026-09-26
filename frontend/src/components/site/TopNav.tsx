'use client';

/**
 * The site's top bar (the landing mockup's `nav`): the brand, a paper disc bearing the wolf's
 * crescent beside the product name, and the three doors. The current page's link is marked
 * with `aria-current`, which also underlines it.
 */
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { SITE } from '@/lib/site';
import { Icon } from './Icon';
import classes from './TopNav.module.css';

export function TopNav() {
  const path = usePathname() ?? '/';
  return (
    <nav className={classes.nav} aria-label="Site">
      <Link href="/" className={classes.brand}>
        <span className={classes.mark} aria-hidden="true">
          <Icon name="sg-wolf" size="70%" />
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
