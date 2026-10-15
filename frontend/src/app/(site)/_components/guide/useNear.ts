'use client';

/**
 * Whether a box has come within a screen of the view, and stays true once it has: the day
 * line's seven demos are small stages each, and building them on load kept a phone busy for
 * seconds, so the role cards stuttered under it (2026-10-15). They mount when the line is near;
 * its slot is a fixed height, so nothing moves. The tools' and the case file's demos still
 * mount on load: their boxes grow with them, and a late mount would move the page.
 */
import { useEffect, useState, type RefObject } from 'react';

export function useNear(ref: RefObject<HTMLElement | null>): boolean {
  const [near, setNear] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || near) return;
    const io = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setNear(true);
      },
      { rootMargin: '100% 0px' },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [ref, near]);
  return near;
}
