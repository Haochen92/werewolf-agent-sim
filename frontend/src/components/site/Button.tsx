/**
 * The site's button: Mantine's Button with the landing mockup's API. The look lives in the
 * theme (`theme/components/Button.module.css`); this wrapper only narrows the choices to the
 * three the design has, so a page cannot reach for a stock Mantine variant by accident.
 *
 * - `ghost` (default): the quiet pill on a panel.
 * - `primary`: the amber pill; at most one per view.
 * - `brass`: the engraved brass plate, for controls that belong to a scene's fiction (the
 *   waiting room's Lock and Depart). Page-side only; inside the stage box use `ActPlate`.
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
  variant?: 'ghost' | 'primary' | 'brass';
  /** `sm` 36px, `md` 44px (default), `lg` 52px: the mockups' three heights. */
  size?: 'sm' | 'md' | 'lg';
}

const SiteButton = forwardRef<HTMLButtonElement, ButtonProps>(function Button(props, ref) {
  return <MantineButton ref={ref} {...props} />;
});

export const Button = createPolymorphicComponent<'button', ButtonProps>(SiteButton);
