/**
 * The site's own facts in one place: the product name, the nav, and the footer's credits and
 * links. The chrome (`components/site/TopNav`, `SiteFooter`) reads only this, so the owner
 * edits one file to change what every page says about the project.
 */

export const SITE = {
  // the mark (the train's headlamp, a keyhole 9 in its glass, `scripts/brand-mark.mjs`) is
  // drawn for this name
  name: 'The Ninth Express',
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
   * The game the landing's carriage plays (review §F7), day 3's vote in the public cut. If the
   * archive no longer has it, the landing plays the newest game instead.
   */
  featuredReplay: '9369a5c1-3c28-42ce-86a1-9d594dfa4804',

  // TODO(owner): the year the footer prints
  year: 2026,
} as const;
