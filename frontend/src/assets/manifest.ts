/**
 * The ONE import site for art (build_plan §3). Components never hold path strings — they
 * ask this module for a typed handle, so swapping the asset set is files + this file, with
 * zero component edits.
 *
 * The v1 set is twelve compact pixel avatars, owner-ruled from Sample E on 2026-08-22.
 * `portraitFor()` still returns null when the list is empty, preserving the deterministic
 * initials fallback if an asset set is deliberately removed or replaced.
 *
 * Static imports (not `public/`) buy content-hashed URLs — regenerated art can never get
 * stuck behind a cached copy — plus inferred dimensions, so no layout shift.
 */
import type { StaticImageData } from 'next/image';
import type { AttackerType } from '@/types/contracts';
import p01 from './portraits/01.webp';
import p02 from './portraits/02.webp';
import p03 from './portraits/03.webp';
import p04 from './portraits/04.webp';
import p05 from './portraits/05.webp';
import p06 from './portraits/06.webp';
import p07 from './portraits/07.webp';
import p08 from './portraits/08.webp';
import p09 from './portraits/09.webp';
import p10 from './portraits/10.webp';
import p11 from './portraits/11.webp';
import p12 from './portraits/12.webp';

export const PORTRAITS: StaticImageData[] = [
  p01,
  p02,
  p03,
  p04,
  p05,
  p06,
  p07,
  p08,
  p09,
  p10,
  p11,
  p12,
];

/** Deterministic per-seat pick, so a seat wears the same face in every view and every session. */
export function hashSeat(seat: string): number {
  let hash = 0;
  for (let i = 0; i < seat.length; i += 1) {
    hash = (hash << 5) - hash + seat.charCodeAt(i);
    hash |= 0;
  }
  return Math.abs(hash);
}

export function portraitFor(seat: string): StaticImageData | null {
  if (PORTRAITS.length === 0) return null;
  return PORTRAITS[hashSeat(seat) % PORTRAITS.length];
}

/** The initials fallback's hue — same hash, so face and fallback are the same identity. */
export function hueFor(seat: string): number {
  return hashSeat(seat) % 360;
}

export function initialsFor(seat: string): string {
  const parts = seat.split(/[_\s-]+/).filter(Boolean);
  if (parts.length === 0) return '??';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  // "player_5" → "P5", which keeps a nine-seat table distinguishable at chip size.
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

/**
 * Kill glyphs, keyed by how the death happened. Death notices carry the attacker type as a
 * typed mark rather than as grey text (ux_baseline §1) — the glyphs are hand-authored
 * pixel SVGs on one 16px grid, imported here as React components.
 */
export type DeathGlyphKind = AttackerType | 'lynch';
