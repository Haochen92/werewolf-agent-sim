'use client';

/**
 * Decodes the next speaker's poses while the current turn plays (cast/ahead.ts). The images
 * are held off the page, one speaker at a time; `decode()` runs off the main thread, and a
 * picture the page then mounts is painted from the decoded copy. A phone may still discard a
 * held decode under memory pressure: this is a strong hint, not a promise.
 */
import { useEffect, useMemo, useRef } from 'react';
import { SPRITES, type Character } from '@/assets/manifest';
import type { SceneBeat } from '../beats/types';
import { useSmall } from '../set';
import { spritesAhead, type Pose } from './ahead';

export function DecodeAhead({
  beats,
  index,
  cast,
}: {
  beats: readonly SceneBeat[];
  index: number;
  cast: readonly Character[];
}) {
  const small = useSmall();
  const srcs = useMemo(
    () =>
      spritesAhead(beats, index, cast, (c: Character, pose: Pose) =>
        poseSrc(c, pose, small),
      ),
    [beats, index, cast, small],
  );
  const held = useRef(new Map<string, HTMLImageElement>());
  useEffect(() => {
    if (typeof Image === 'undefined') return;
    const map = held.current;
    for (const k of [...map.keys()]) if (!srcs.includes(k)) map.delete(k);
    for (const s of srcs) {
      if (map.has(s)) continue;
      const img = new Image();
      img.decoding = 'async';
      img.src = s;
      map.set(s, img);
      img.decode().catch(() => {});
    }
  }, [srcs]);
  return null;
}

/** The pose's picture for this screen: the phone's copy on a small stage, as Puppet draws it. */
function poseSrc(c: Character, pose: Pose, small: boolean): string {
  return (small ? SPRITES.small.day : SPRITES.day)[c][pose].src;
}
