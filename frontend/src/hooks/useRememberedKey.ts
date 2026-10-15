'use client';
/**
 * The BYOK key's "remember on this device" behaviour, shared by the two key fields: the
 * theatre-side `ByokField` (the restart card) and the ticket office's key row. Only the look
 * differs between them.
 *
 * Remembering is opt-in and purely client-side (`byokKey` in `lib/storage`); the server never
 * stores keys. A saved key loads after mount, is shown masked until the field is focused, and
 * can be forgotten from the field itself.
 */
import { useEffect, useState } from 'react';
import { byokKey } from '@/lib/storage';

export function useRememberedKey(value: string, onChange: (key: string) => void) {
  const [remember, setRemember] = useState(false);
  const [loadedFromStorage, setLoadedFromStorage] = useState(false);

  // localStorage is client-only: read after mount so server and client markup agree.
  useEffect(() => {
    const saved = byokKey.get();
    if (saved) {
      onChange(saved);
      setRemember(true);
      setLoadedFromStorage(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const masked = loadedFromStorage && value.length > 8;

  return {
    remember,
    /** A saved key filled the field and has not been touched since. */
    loadedFromStorage,
    masked,
    /** What the input shows: the key, or its first and last four characters when masked. */
    shown: masked ? `${value.slice(0, 4)}••••••••${value.slice(-4)}` : value,
    update: (next: string) => {
      onChange(next);
      setLoadedFromStorage(false);
      if (remember && next) byokKey.set(next);
    },
    unmask: () => setLoadedFromStorage(false),
    /** Forget the saved key and empty the field. */
    clearSaved: () => {
      byokKey.clear();
      onChange('');
      setRemember(false);
      setLoadedFromStorage(false);
    },
    setRemember: (on: boolean) => {
      setRemember(on);
      if (on && value) byokKey.set(value);
      else byokKey.clear();
    },
  };
}
