/**
 * The site's footer (the inner mockups' `.foot`, the landing's exits): a row of links with the
 * GitHub mark, then the credit line. Everything it says comes from `lib/site.ts`; links the
 * owner has not pointed anywhere yet are left out rather than shown dead. The one live fact,
 * how many games the archive holds, is `GamesArchived`'s.
 */
import { SITE } from '@/lib/site';
import { GamesArchived } from './GamesArchived';
import { Icon } from './Icon';
import classes from './SiteFooter.module.css';

export function SiteFooter() {
  return (
    <footer className={classes.foot}>
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
      <p className={classes.meta}>
        Built by {SITE.author}
        <GamesArchived />
        {' · '}
        {SITE.year}
      </p>
    </footer>
  );
}
