'use client';
/**
 * The BYOK key's "remember on this device" behaviour, shared by the two key fields: the
 * theatre-side `ByokField` (the restart card) and the ticket office's key row. Only the look
 * differs between them.
 *
 * Remembering is opt-in and purely client-side (`byokKeys` in `lib/storage`), one key per
 * company: the field fills with the saved key of the chosen model's company, so a key saved for
 * one model is never sent with another's. A key is saved when the field is left (not per
 * keystroke: a half-typed key's prefix names no company yet), shown masked until the field is
 * focused, and deleted only by the player: the field's button, the saved list, or the switch.
 */
import { useEffect, useState } from 'react';
import { keyProvider, type Provider } from '@/lib/key-provider';
import { byokKeys } from '@/lib/storage';

type Saved = { provider: Provider; key: string };

/** A key's first and last four characters. */
export function maskKey(key: string): string {
  return key.length > 8 ? `${key.slice(0, 4)}••••••••${key.slice(-4)}` : '••••••••';
}

/**
 * `provider`: the company of the model the key is for; null when the field cannot know (the
 * restart card), where a lone saved key is offered.
 */
export function useRememberedKey(
  value: string,
  onChange: (key: string) => void,
  provider: Provider | null,
) {
  const [saved, setSaved] = useState<Saved[]>([]);
  const [remember, setRemember] = useState(false);
  const [loadedFromStorage, setLoadedFromStorage] = useState(false);

  // the slot a key goes in: the company its prefix names, else the model's
  const slotOf = (key: string): Provider | null => keyProvider(key) ?? provider;

  // localStorage is client-only: read after mount so server and client markup agree; again on a
  // change of model, when a saved key in the field gives way to the new company's (a typed one stays).
  useEffect(() => {
    byokKeys.migrate(provider);
    const all = byokKeys.all();
    setSaved(all);
    if (value && !all.some((s) => s.key === value)) return;
    const mine = provider
      ? all.find((s) => s.provider === provider)
      : all.length === 1
        ? all[0]
        : undefined;
    onChange(mine?.key ?? '');
    setRemember(!!mine);
    setLoadedFromStorage(!!mine);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [provider]);

  const masked = loadedFromStorage && value.length > 8;

  /** Forget `key`'s saved copy, if it has one. */
  const forget = (key: string) => {
    const slot = saved.find((s) => s.key === key)?.provider ?? slotOf(key);
    if (slot && byokKeys.get(slot) === key) byokKeys.clear(slot);
    setSaved(byokKeys.all());
  };

  return {
    remember,
    /** A saved key filled the field and has not been touched since. */
    loadedFromStorage,
    masked,
    /** What the input shows: the key, or its first and last four characters when masked. */
    shown: masked ? maskKey(value) : value,
    /** Every key saved on this device, one per company. */
    saved,
    update: (next: string) => {
      onChange(next);
      setLoadedFromStorage(false);
    },
    unmask: () => setLoadedFromStorage(false),
    /** The field was left: a key to remember is saved under its company. */
    commit: () => {
      const slot = slotOf(value);
      if (!remember || !value || !slot) return;
      byokKeys.set(slot, value);
      setSaved(byokKeys.all());
    },
    /** Empty the field and delete the key's saved copy. */
    clear: () => {
      if (value) forget(value);
      onChange('');
      setRemember(false);
      setLoadedFromStorage(false);
    },
    /** Delete one company's saved key; the field empties if it held that key. */
    deleteSaved: (p: Provider) => {
      const key = byokKeys.get(p);
      byokKeys.clear(p);
      setSaved(byokKeys.all());
      if (key && key === value) {
        onChange('');
        setRemember(false);
        setLoadedFromStorage(false);
      }
    },
    setRemember: (on: boolean) => {
      setRemember(on);
      const slot = slotOf(value);
      if (on && value && slot) {
        byokKeys.set(slot, value);
        setSaved(byokKeys.all());
      } else if (!on && value) forget(value);
    },
  };
}
