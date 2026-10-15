/**
 * One icon from the site's sprite (`IconSprite`, rendered once by the site layout). Drawn in
 * `currentColor`, so the text around it decides the colour. Decorative by default; pass
 * `label` when the icon is the only thing saying what a control does.
 */
import type { SVGProps } from 'react';
import type { IconName } from './IconSprite';
import classes from './Icon.module.css';

export function Icon({
  name,
  size = 18,
  label,
  className,
  ...rest
}: {
  name: IconName;
  size?: number | string;
  label?: string;
} & Omit<SVGProps<SVGSVGElement>, 'name'>) {
  return (
    <svg
      width={size}
      height={size}
      className={className ? `${classes.icon} ${className}` : classes.icon}
      {...(label ? { role: 'img', 'aria-label': label } : { 'aria-hidden': true })}
      focusable="false"
      {...rest}
    >
      <use href={`#${name}`} />
    </svg>
  );
}
