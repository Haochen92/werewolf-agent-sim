/**
 * The stage's Reveal switch, shown on, off the stage: for a page that tells what Reveal shows
 * (the landing's exhibit, the guide's Reveal), so a viewer knows the switch when they meet it
 * (owner, 2026-10-22). The switch itself (`RevealSwitch`, the strip's), at its full size, in the stage's
 * materials; a picture of it, not a control.
 */
import type { CSSProperties } from 'react';
import { vars } from '../paint/materials';
import { Reveal } from './RevealSwitch';
import styles from './RevealSign.module.css';

const MATERIAL_VARS = vars() as CSSProperties;

export function RevealSign({ className = '' }: { className?: string }) {
  return (
    <span className={`${styles.sign} ${className}`} style={MATERIAL_VARS} inert>
      <Reveal on />
    </span>
  );
}
