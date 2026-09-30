/**
 * The role figures: the felt doll on each role's card, and the head-and-shoulders crop the
 * "your card" button shows. The dolls are painted sprites (SPRITES.roles, 720×960, feet on the
 * bottom edge); this wraps each in SVG markup so every consumer, stage and site, keeps sizing
 * one `<svg>` by CSS and injecting it as-is. The card that frames them (name, sigil, front
 * line, faction colour) is an instrument and is drawn in JSX around them.
 *
 * The dolls were once vector drawings ported from the design bundle's role kit
 * (docs/design_2026-09-25/kits/role-kit.js); git history keeps that drawing. The card's words
 * (the front line, what the role does at night) are in `card-text.ts`.
 */
import { SPRITES, type RoleSprite } from '@/assets/manifest';

const W = 720;
const H = 960;

/** The role's felt figure, as SVG markup (empty for a role without a sprite). */
export function roleFigure(role: string): string {
  if (!Object.hasOwn(SPRITES.roles, role)) return '';
  const img = SPRITES.roles[role as RoleSprite];
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${W} ${H}" aria-hidden="true"><image href="${img.src}" x="0" y="0" width="${W}" height="${H}"/></svg>`;
}

/*
 * Head and shoulders: the top ~56% of the canvas at the avatar box's 92:96, centred. The
 * vigilante's feather and the reaper's hood sit right of the canvas's centre line, so their
 * windows slide right (the reaper's also drops a little, under the scythe's blade).
 */
const CROP_DEFAULT = '101 0 518 540';
const CROP: Record<string, string> = {
  vigilante: '150 0 518 540',
  serial_killer: '135 30 518 540',
};

/** The figure cropped to head and shoulders: the card at rest beside the box ("your card"). */
export function roleAvatar(role: string): string {
  return roleFigure(role).replace(
    /viewBox="[^"]*"/,
    `viewBox="${CROP[role] || CROP_DEFAULT}" preserveAspectRatio="xMidYMin slice"`,
  );
}

/** "a villager", "the healer": how the table says what a seat was. */
export const ROLE_ARTICLE: Record<string, string> = {
  villager: 'a villager',
  healer: 'the healer',
  investigator: 'the investigator',
  vigilante: 'the vigilante',
  wolf: 'a wolf',
  serial_killer: 'the serial killer',
};
