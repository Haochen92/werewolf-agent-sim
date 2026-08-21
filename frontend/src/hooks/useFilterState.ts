'use client';

/**
 * URL search params as the single source of truth for browse/scrub state (build_plan §4).
 * Not component state: a scrubber position that lives in the URL is shareable, survives a
 * refresh, and makes the browser's back button do the obvious thing. "Play of the game"
 * deep links later need exactly this.
 */
import { useCallback } from 'react';
import { usePathname, useRouter, useSearchParams } from 'next/navigation';

export function useFilterState<T extends string | number>(
  key: string,
  fallback: T,
  parse: (raw: string) => T,
): [T, (value: T) => void] {
  const router = useRouter();
  const pathname = usePathname();
  const searchParams = useSearchParams();

  const raw = searchParams.get(key);
  const value = raw === null ? fallback : parse(raw);

  const setValue = useCallback(
    (next: T) => {
      const params = new URLSearchParams(searchParams.toString());
      if (next === fallback) params.delete(key);
      else params.set(key, String(next));
      const query = params.toString();
      // `scroll: false` — a scrubber step should move the transcript, not fling the page.
      router.replace(query ? `${pathname}?${query}` : pathname, { scroll: false });
    },
    [router, pathname, searchParams, key, fallback],
  );

  return [value, setValue];
}

export function useNumberFilter(key: string, fallback: number) {
  return useFilterState<number>(key, fallback, (raw) => {
    const parsed = Number.parseInt(raw, 10);
    return Number.isFinite(parsed) ? parsed : fallback;
  });
}
