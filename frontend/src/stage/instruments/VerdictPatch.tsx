/**
 * The verdict on one thing an agent did, as a stitched felt patch sewn beside "How it went"
 * in the epilogue: green with a tick where it worked, red with a cross where it cost, half and
 * half where it was mixed, and an empty outline with a question mark where nobody could say.
 * The verdict is on the outcome, not the scenario, which is why it sits with the outcome.
 *
 * Drawn in vector (bench 73 `patchSVG`): a filled patch, a dashed stitch inside its edge, the
 * mark. It fills whatever box it is put in, at 34:24.
 */
import type { CSSProperties } from 'react';
import type { VerdictKind } from './ledger';

const GREEN = '#7fd6a0',
  RED = '#e3503f',
  MUTED = '#7ea9b6',
  INK = '#0b191f';

export function VerdictPatch({
  kind,
  className,
  style,
}: {
  kind: VerdictKind;
  className?: string;
  style?: CSSProperties;
}) {
  const edge = kind === 'unclear' ? MUTED : INK;
  return (
    <svg
      viewBox="0 0 34 24"
      className={className}
      style={style}
      role="img"
      aria-label={kind}
      data-patch={kind}
    >
      {kind === 'worked' ? (
        <rect x="2" y="2" width="30" height="20" rx="4" fill={GREEN} />
      ) : null}
      {kind === 'cost' ? (
        <rect x="2" y="2" width="30" height="20" rx="4" fill={RED} />
      ) : null}
      {kind === 'mixed' ? (
        <>
          <path d="M6 2h11v20H6a4 4 0 0 1-4-4V6a4 4 0 0 1 4-4z" fill={GREEN} />
          <path d="M17 2h11a4 4 0 0 1 4 4v12a4 4 0 0 1-4 4H17z" fill={RED} />
        </>
      ) : null}
      <rect
        x="2"
        y="2"
        width="30"
        height="20"
        rx="4"
        fill="none"
        stroke={edge}
        strokeWidth="1.6"
      />
      <rect
        x="4.5"
        y="4.5"
        width="25"
        height="15"
        rx="2.5"
        fill="none"
        stroke={edge}
        strokeWidth="1.1"
        strokeDasharray="2.2 2.2"
        opacity=".75"
      />
      {kind === 'worked' ? (
        <path
          d="M10 12l4 4 10-9"
          fill="none"
          stroke={INK}
          strokeWidth="2.6"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ) : kind === 'cost' ? (
        <path
          d="M11 7l12 10M23 7L11 17"
          fill="none"
          stroke={INK}
          strokeWidth="2.6"
          strokeLinecap="round"
        />
      ) : kind === 'mixed' ? (
        <path
          d="M6 12l3 3 6-6M20 8l7 8M27 8l-7 8"
          fill="none"
          stroke={INK}
          strokeWidth="2.4"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      ) : (
        <>
          <path
            d="M13 9.5a4 4 0 1 1 5.5 3.7c-1 .5-1.5 1.2-1.5 2.3"
            fill="none"
            stroke={MUTED}
            strokeWidth="2.4"
            strokeLinecap="round"
          />
          <circle cx="17" cy="19" r="1.5" fill={MUTED} />
        </>
      )}
    </svg>
  );
}
