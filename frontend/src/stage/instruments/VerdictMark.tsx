/**
 * How a thing an agent did turned out (`net_verdict`), as a small mark that reads without its
 * colour (owner, 2026-09-29: colour-blind safe): ✓ it worked, ✗ it cost, ± it was mixed, ?
 * nobody could say. Line glyphs drawn in `currentColor`, so the place that shows one gives the
 * ink: the case file's Findings (index and stamp) and the epilogue ledger's rows.
 */
import type { VerdictKind } from './ledger';

const LABEL: Record<VerdictKind, string> = {
  worked: 'positive',
  cost: 'negative',
  mixed: 'mixed',
  unclear: 'unclear',
};

export function VerdictMark({
  kind,
  className,
}: {
  kind: VerdictKind;
  className?: string;
}) {
  return (
    <svg
      viewBox="0 0 16 16"
      className={className}
      role="img"
      aria-label={LABEL[kind]}
      data-mark={kind}
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {kind === 'worked' ? (
        <path d="M3 8.5l3.2 3.2L13 4.5" />
      ) : kind === 'cost' ? (
        <path d="M4 4l8 8M12 4l-8 8" />
      ) : kind === 'mixed' ? (
        <path d="M8 2.5v7M4.5 6h7M4.5 13h7" />
      ) : (
        <>
          <path d="M5.5 5.6a2.6 2.6 0 1 1 3.6 2.4c-.8.4-1.1.9-1.1 1.8" />
          <circle cx="8" cy="12.9" r=".6" fill="currentColor" />
        </>
      )}
    </svg>
  );
}
