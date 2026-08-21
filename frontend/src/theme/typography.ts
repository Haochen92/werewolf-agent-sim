/**
 * Typography slice. The non-negotiable from ux_baseline §1: ALL dialogue and UI text stays
 * on the clean sans stack — pixel display type is for titles/chrome only, and monospace is
 * reserved exclusively for machine-world panes. The contrast collapses if either leaks into
 * body text, and this is a reading app first.
 */
import { createTheme } from '@mantine/core';

export const typographyTheme = createTheme({
  fontFamily: 'system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
  fontFamilyMonospace: 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace',
  headings: {
    fontFamily:
      'system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
  },
  // Generous line height: transcripts are read, not scanned.
  lineHeights: { md: '1.65' },
});
