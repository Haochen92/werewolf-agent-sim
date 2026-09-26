/**
 * Paper (the mockups' `.paper`): the surface for anything inside the fiction, like a ticket,
 * a boarding pass or a notice. Printed in IM Fell English in the theatre's paper ink.
 * Polymorphic through Mantine's Box: `<Paper component="form">`.
 */
import { forwardRef } from 'react';
import { Box, createPolymorphicComponent, type BoxProps } from '@mantine/core';
import classes from './Paper.module.css';

export type PaperProps = BoxProps;

const SitePaper = forwardRef<HTMLDivElement, PaperProps>(function Paper(
  { className, ...rest },
  ref,
) {
  return (
    <Box
      ref={ref}
      className={className ? `${classes.paper} ${className}` : classes.paper}
      {...rest}
    />
  );
});

export const Paper = createPolymorphicComponent<'div', PaperProps>(SitePaper);
