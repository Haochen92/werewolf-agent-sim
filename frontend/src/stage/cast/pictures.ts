'use client';

/**
 * Which puppet pictures have arrived, so a turn can wait for its speaker's before it shows. On
 * a slow connection the box faded in whole while the figure's picture was still downloading,
 * and the character popped in after it (owner, 2026-10-21, the X-ray's passes). A turn now waits
 * for its poses, at most `PICTURE_WAIT_MS`, then shows whatever has come.
 *
 * Only the sources are kept, never the images: a held decode is megabytes, and the file stays
 * in the browser's cache once fetched, which is what a slow connection lacks.
 */
import { useEffect, useState } from 'react';

/** The longest a turn waits for its pictures before it shows without them. */
export const PICTURE_WAIT_MS = 2000;

const arrived = new Set<string>();
const coming = new Map<string, Promise<void>>();

/** A browser that can decode off the page: anywhere else (the server, a test's DOM) nothing waits. */
const canWait = () =>
  typeof Image !== 'undefined' && typeof Image.prototype.decode === 'function';

/** This source has been fetched and decoded once (DecodeAhead's, or a turn's own wait). */
export function markArrived(src: string): void {
  arrived.add(src);
}

export function hasArrived(src: string): boolean {
  return arrived.has(src);
}

/** Fetch and decode `src` once; the image is let go as soon as it has decoded. */
export function fetchPicture(src: string): Promise<void> {
  if (arrived.has(src)) return Promise.resolve();
  const pending = coming.get(src);
  if (pending) return pending;
  const img = new Image();
  img.decoding = 'async';
  img.src = src;
  const done = img
    .decode()
    .then(() => markArrived(src))
    .finally(() => coming.delete(src));
  coming.set(src, done);
  return done;
}

/**
 * Whether these pictures are in (or the wait has run out). True at once when every one has
 * arrived before, so a speaker already seen never blinks; a new list waits afresh.
 */
export function usePicturesIn(srcs: readonly string[], waitMs = PICTURE_WAIT_MS): boolean {
  const key = srcs.join('|');
  const [done, setDone] = useState<string | null>(null);
  const ready = done === key || !canWait() || srcs.every((s) => arrived.has(s));
  useEffect(() => {
    if (ready) return;
    let live = true;
    const finish = () => {
      if (live) setDone(key);
    };
    const cap = setTimeout(finish, waitMs);
    Promise.all(key.split('|').map(fetchPicture)).then(finish, finish);
    return () => {
      live = false;
      clearTimeout(cap);
    };
  }, [key, ready, waitMs]);
  return ready;
}
