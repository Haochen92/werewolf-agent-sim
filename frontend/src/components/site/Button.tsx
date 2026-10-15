/**
 * The site's button: Mantine's Button narrowed to the controls kit's three variants (owner,
 * 2026-10-15), so a page cannot reach for a stock Mantine variant by accident. The look lives
 * in the theme (`theme/components/Button.module.css`).
 *
 * - `well` (default): the recessed well of the nav's doors; every button that is not the main
 *   action, a way to another page included.
 * - `plate`: the riveted cream plate; the one main action of a view. Page-side only; inside
 *   the stage box use `ActPlate`.
 * - `text`: a word that acts, for small actions.
 *
 * The well and the text take their colours from the surface under them (`data-surface`).
 *
 * Polymorphic like Mantine's own: `<Button component={Link} href="/play">` renders a link.
 */
import { forwardRef } from 'react';
import {
  Button as MantineButton,
  createPolymorphicComponent,
  type ButtonProps as MantineButtonProps,
} from '@mantine/core';

export interface ButtonProps extends Omit<MantineButtonProps, 'variant' | 'size'> {
  variant?: 'well' | 'plate' | 'text';
  /** `sm` 36px, `md` 44px (default), `lg` 52px; a `text` button is as tall as its words. */
  size?: 'sm' | 'md' | 'lg';
}

const SiteButton = forwardRef<HTMLButtonElement, ButtonProps>(function Button(props, ref) {
  return <MantineButton ref={ref} {...props} />;
});

export const Button = createPolymorphicComponent<'button', ButtonProps>(SiteButton);
