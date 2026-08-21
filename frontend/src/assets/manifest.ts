/**
 * The ONE import site for art (build_plan §3). Components never hold path strings — they
 * ask this module for a typed handle, so swapping the asset set is files + this file, with
 * zero component edits.
 *
 * Portraits are empty on purpose right now. `portraitFor()` returns null while the set is
 * unpopulated and `SeatChip` falls back to initials on a deterministic hue, so the build
 * never blocks on art and generated portraits can land at any time (ux_baseline §1).
 *
 * When portraits arrive: `import p01 from './portraits/01.webp'` and push into PORTRAITS.
 * Static imports (not `public/`) buy content-hashed URLs — regenerated art can never get
 * stuck behind a cached copy — plus inferred dimensions, so no layout shift.
 */
import type { StaticImageData } from 'next/image';
import type { AttackerType } from '@/types/contracts';

export const PORTRAITS: StaticImageData[] = [];

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
