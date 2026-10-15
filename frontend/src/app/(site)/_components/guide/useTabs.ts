'use client';

/**
 * The guide's tab sets (the game modes, the day's stops, the case file's tabs, the tools): one
 * tab shown, the arrows step along them. Not Mantine's Tabs: its idle panels are `display:
 * none`, and the guide stacks every panel in one grid cell (`.stack`) so the box is as tall as
 * the tallest and a switch never moves the page; an idle panel here is hidden and inert instead.
 */
import { useId, useRef, useState, type KeyboardEvent } from 'react';

export function useTabs<T extends string>(ids: readonly T[]) {
  const base = useId();
  const [at, setAt] = useState<T>(ids[0]);
  const tabs = useRef(new Map<T, HTMLButtonElement | null>());
  const tabId = (id: T) => `${base}-tab-${id}`;
  const panelId = (id: T) => `${base}-panel-${id}`;

  /** Shows `id`; `focus` moves the keyboard to its tab (a "next stop" button, the arrows). */
  const pick = (id: T, focus = false) => {
    setAt(id);
    if (focus) tabs.current.get(id)?.focus();
  };

  const onKeyDown = (e: KeyboardEvent) => {
    const i = ids.indexOf(at);
    const to = {
      ArrowRight: ids[(i + 1) % ids.length],
      ArrowLeft: ids[(i - 1 + ids.length) % ids.length],
      Home: ids[0],
      End: ids[ids.length - 1],
    }[e.key];
    if (!to) return;
    e.preventDefault();
    pick(to, true);
  };

  return {
    at,
    index: ids.indexOf(at),
    pick,
    tab: (id: T) => ({
      ref: (el: HTMLButtonElement | null) => {
        tabs.current.set(id, el);
      },
      type: 'button' as const,
      role: 'tab',
      id: tabId(id),
      'aria-controls': panelId(id),
      'aria-selected': id === at,
      tabIndex: id === at ? 0 : -1,
      onClick: () => pick(id),
      onKeyDown,
    }),
    panel: (id: T) => ({
      role: 'tabpanel',
      id: panelId(id),
      'aria-labelledby': tabId(id),
      'data-off': id === at ? undefined : true,
      inert: id !== at,
    }),
    /** Something that belongs to a panel but sits outside it (a button in the panel's header). */
    with: (id: T) => ({ 'data-off': id === at ? undefined : true, inert: id !== at }),
  };
}
