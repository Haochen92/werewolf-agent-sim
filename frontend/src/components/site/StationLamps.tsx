/**
 * The archive's pendant: a brass shade on its cord, hung from the top of the room. Plain SVG,
 * still; its light is the room's own gradient, not part of the drawing, and where it hangs is the
 * room's (`className`). Decoration only, so hidden from readers. (The caged wall light that stood
 * beside it is in git history.)
 */

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
