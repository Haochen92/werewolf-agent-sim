'use client';
/**
 * True once the given pictures are loaded and decoded: the landing carriage's painted picture
 * replaces its drawn stand-in only then (FeaturedReplay). A whole page's or section's wait for
 * its pictures is PageGate's.
 *
 * `srcs` null asks nothing yet. A picture that fails counts as done; `cap` ms, when given, ends
 * the wait anyway. Once true it stays true.
 */
import { useEffect, useState } from 'react';

export function useDecoded(srcs: readonly string[] | null, cap?: number): boolean {
  const [done, setDone] = useState(false);
  useEffect(() => {
    if (!srcs || done) return;
    let live = true;
    const finish = () => live && setDone(true);
    const all = srcs.map((src) => {
      const img = new Image();
      img.src = src;
      return img.decode().catch(() => {});
    });
    void Promise.all(all).then(finish);
    const t = cap === undefined ? undefined : setTimeout(finish, cap);
    return () => {
      live = false;
      clearTimeout(t);
    };
  }, [srcs, done, cap]);
  return done;
}
