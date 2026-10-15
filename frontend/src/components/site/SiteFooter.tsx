/**
 * The site's footer: one row under one rule. At the left the credit line, with how many games
 * the archive holds (`GamesArchived`, the one live fact); at the right the links, the GitHub
 * mark first. Everything it says comes from `lib/site.ts`; links the owner has not pointed
 * anywhere yet are left out rather than shown dead, and join the row once they have somewhere
 * to go.
 */
import { SITE } from '@/lib/site';
import { GamesArchived } from './GamesArchived';
import { Icon } from './Icon';
import classes from './SiteFooter.module.css';

export function SiteFooter() {
  return (
    <footer className={classes.foot}>
      <p className={classes.meta}>
        Built by {SITE.author}
        <GamesArchived />
        {' · '}
        {SITE.year}
      </p>
      <div className={classes.links}>
        <a className={classes.link} href={SITE.github} target="_blank" rel="noreferrer">
          <Icon name="i-github" size={15} />
          GitHub
        </a>
        {SITE.footerLinks.map((l) =>
          l.href ? (
            <a key={l.label} className={classes.link} href={l.href}>
              {l.label}
            </a>
          ) : null,
        )}
      </div>
    </footer>
  );
}
