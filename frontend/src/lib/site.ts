/**
 * The site's own facts in one place: the product name, the nav, and the footer's credits and
 * links. The chrome (`components/site/TopNav`, `SiteFooter`) reads only this, so the owner
 * edits one file to change what every page says about the project.
 */

export const SITE = {
  // TODO(owner): tentative (review §F2); the logo mark follows the name
  name: 'Carriage Nine',
  author: 'Liu Haochen',
  github: 'https://github.com/Haochen92/werewolf-agent-sim',

  /** The top nav, in order. `match` is the path prefix that marks the link as the current page. */
  nav: [
    { label: 'Play', href: '/play', match: '/play' },
    { label: 'Rooms', href: '/rooms', match: '/rooms' },
    { label: 'Replays', href: '/replays', match: '/replays' },
  ],

  /**
   * The footer's other exits. An entry with `href: null` is not rendered, so a link appears
   * the moment it has somewhere to go.
   */
  footerLinks: [
    // TODO(owner): no route yet; point at the write-up once it is published
    { label: "Read how it's built", href: null },
    // TODO(owner): no route yet; a privacy / data-handling page
    { label: 'Privacy & data handling', href: null },
    // TODO(owner): a contact address or page
    { label: 'Contact', href: null },
  ] as { label: string; href: string | null }[],

  /**
   * "[N] games archived" in the footer. `GET /replays` has no total yet (review §A1, server
   * track §F8); until it does, this static count is shown when set, and the phrase is left out
   * when it is null.
   */
  // TODO(owner): replace with the server's total once `GET /replays` returns one
  gamesArchived: null as number | null,

  // TODO(owner): the year the footer prints
  year: 2026,
} as const;
