'use client';

/**
 * What a scene tells the Stage about the set it stands in, and what the Stage tells a scene
 * about the screen. Both live here, apart from Stage.tsx, so the instruments that read them
 * (the backdrop, the ledger, the stand) and the Stage that provides them share no cycle.
 *
 * `BackdropContext`: a scene describes its baked backdrop (`Backdrop`, the registrar) and the
 * Stage draws one persistent sheet from the description (`BackdropSheet`, at the foot of the
 * paint layer). The sheet outlives the scene's beats and the scene itself, so a beat that
 * remounts its scene never remounts the picture: a remounted `<img>` on iPhone Safari shows
 * nothing until its decode lands, a black frame per beat, and decodes the sheet again each
 * time (build log §8.8).
 */
import { createContext, useContext } from 'react';
import type { Phase } from './paint/materials';
import type { Hud } from './units';

/** The stage is drawn small (`data-small`): a phone, or a window that draws it under three-quarter size. */
export const SmallContext = createContext(false);

/**
 * Whether the stage is drawn small (`data-small`, under three-quarter size: a phone, or the
 * workbench's phone frame). What takes a cheaper form on a phone for its memory (the backdrop's
 * cut, the stand's and the ledger's arrival at once) reads this, the same measurement the css
 * rules key on, so the phone-rule gate (e2e/phone-rule.spec.ts) sees what a phone sees.
 */
export function useSmall(): boolean {
  return useContext(SmallContext);
}

/** A scene's backdrop, as it describes it (instruments/Backdrop.tsx). */
export interface BackdropSpec {
  phase: Phase;
  hud: Hud;
  /** The side slot is open: the room is moved left. */
  side: boolean;
  /** Played: the hour the car was at before this beat. */
  from: Phase | null;
  fadeDelay: number;
  /** The motion speed the scene plays at (the sheet is drawn outside the scene's provider). */
  k: number;
}

export const BackdropContext = createContext<((spec: BackdropSpec | null) => void) | null>(
  null,
);
