'use client';

/**
 * A site page's music, for a viewer who turned it on with the nav's switch (owner, 2026-10-15):
 * the guide's piece on the landing (the guide plays it itself), the platform's lobby on the
 * archive and the rooms' list. Pages with one bed between them hand it on without a break.
 */
import { useState } from 'react';
import { GUIDE_BED, TRACKS, siteLobbyBed } from './cues';
import { useMusicBed } from './music';

export function PageMusic({ bed }: { bed: 'guide' | 'lobby' }) {
  // the lobby's three in turn, from one picked for this visit
  const [start] = useState(() => Math.floor(Math.random() * TRACKS.lobby.length));
  const [lobby] = useState(() => siteLobbyBed(start));
  useMusicBed(bed === 'guide' ? GUIDE_BED : lobby);
  return null;
}
