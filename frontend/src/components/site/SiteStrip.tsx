'use client';

/**
 * What the site's nav shares with a page about its pinned strip (TopNav): whether the hanging
 * board has scrolled out of view (`pinned`), and a page's wish to put its own bar there on a
 * phone in place of the strip (the guide, owner 2026-10-15: two stacked bars read badly). A page
 * that replaces the strip shows its bar while `pinned`, and gives `backToTop` a button, so the
 * nav is one tap away. Every other page leaves it alone and keeps the strip.
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
  type RefObject,
} from 'react';

interface SiteStrip {
  pinned: boolean;
  setPinned: (pinned: boolean) => void;
  /** A page has its own bar in the strip's place on a phone. */
  replaced: boolean;
  setReplaced: (replaced: boolean) => void;
  /** The hanging board (TopNav attaches it): where `backToTop` puts the focus. */
  board: RefObject<HTMLElement | null>;
  /** Back to the top of the page, the focus on the board's first link. */
  backToTop: () => void;
}

const Ctx = createContext<SiteStrip | null>(null);

export function SiteStripProvider({ children }: { children: ReactNode }) {
  const [pinned, setPinned] = useState(false);
  const [replaced, setReplaced] = useState(false);
  const board = useRef<HTMLElement | null>(null);
  const backToTop = useCallback(() => {
    const still = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    window.scrollTo({ top: 0, behavior: still ? 'auto' : 'smooth' });
    board.current?.querySelector<HTMLElement>('a')?.focus({ preventScroll: true });
  }, []);
  const value = useMemo(
    () => ({ pinned, setPinned, replaced, setReplaced, board, backToTop }),
    [pinned, replaced, backToTop],
  );
  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useSiteStrip(): SiteStrip {
  const strip = useContext(Ctx);
  if (!strip) throw new Error('useSiteStrip: outside the site layout (SiteStripProvider)');
  return strip;
}

/** For a page with its own bar in the strip's place on a phone: while it is mounted. */
export function useReplaceSiteStrip() {
  const strip = useSiteStrip();
  const { setReplaced } = strip;
  useEffect(() => {
    setReplaced(true);
    return () => setReplaced(false);
  }, [setReplaced]);
  return strip;
}
