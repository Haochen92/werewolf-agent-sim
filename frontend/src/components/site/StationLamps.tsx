/**
 * The station's two lamps: the caged wall light (the landing's reading room, the ticket office)
 * and the pendant (the latest games, the archive). Plain SVG, still; their light is the room's
 * own gradient, not part of the drawing, and where they stand is the room's (`className`).
 * Decoration only, so hidden from readers.
 */

/** A caged bulkhead light on the wall: an iron rim, the lit glass, two bars and a stile over it. */
export function WallLight({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 56 72" aria-hidden="true">
      <defs>
        <radialGradient id="wl-glow">
          <stop offset="0" stopColor="#fff6dc" />
          <stop offset=".55" stopColor="#ffd38a" />
          <stop offset="1" stopColor="#8a5a22" />
        </radialGradient>
        <linearGradient id="wl-iron" x1="0" x2="1">
          <stop offset="0" stopColor="#22180b" />
          <stop offset=".5" stopColor="#8a6630" />
          <stop offset="1" stopColor="#22180b" />
        </linearGradient>
      </defs>
      <ellipse
        cx="28"
        cy="36"
        rx="26"
        ry="34"
        fill="#1a120a"
        stroke="url(#wl-iron)"
        strokeWidth="3"
      />
      <ellipse cx="28" cy="36" rx="17" ry="24" fill="url(#wl-glow)" />
      <ellipse
        cx="28"
        cy="36"
        rx="17"
        ry="24"
        fill="none"
        stroke="#8a6630"
        strokeWidth="2"
      />
      <path d="M11 27 H45 M11 45 H45 M28 12 V60" stroke="url(#wl-iron)" strokeWidth="2.4" />
      <circle cx="28" cy="6" r="1.8" fill="#8a6630" />
      <circle cx="28" cy="66" r="1.8" fill="#8a6630" />
    </svg>
  );
}

/** A brass pendant shade on its cord, hung from the top of the room. */
export function Pendant({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 60 96" aria-hidden="true">
      <defs>
        <radialGradient id="pd-glow">
          <stop offset="0" stopColor="#fff2cf" />
          <stop offset=".6" stopColor="#ffc56a" />
          <stop offset="1" stopColor="#ffc56a" stopOpacity="0" />
        </radialGradient>
        <linearGradient id="pd-brass" x1="0" x2="1">
          <stop offset="0" stopColor="#4e340e" />
          <stop offset=".5" stopColor="#d9a64a" />
          <stop offset="1" stopColor="#4e340e" />
        </linearGradient>
      </defs>
      <line x1="30" y1="0" x2="30" y2="60" stroke="#3a2a14" strokeWidth="2" />
      <path d="M14 78 Q16 62 30 60 Q44 62 46 78 Z" fill="url(#pd-brass)" />
      <ellipse cx="30" cy="82" rx="18" ry="10" fill="url(#pd-glow)" />
    </svg>
  );
}
