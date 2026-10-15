/**
 * A role card's back: the stitched ring and, inside it, the plain felt doll the ticket office
 * shows for "dealt at random" (owner, 2026-10-15), so a card nobody may read looks the same
 * on every page: no role yet, so no costume and no prop. Its own file so that a page drawing
 * only the picture does not pull in the card's flip and its animation library.
 */
export function BackArt() {
  return (
    <svg viewBox="0 0 100 100" aria-hidden="true">
      <circle cx="50" cy="50" r="40" fill="none" stroke="#cbb992" strokeWidth="2" />
      <circle
        cx="50"
        cy="50"
        r="33"
        fill="none"
        stroke="#8d7a55"
        strokeWidth="1.6"
        strokeDasharray="3 3"
      />
      {/* the doll of RoleCards' BlankDoll (120 × 160), set inside the ring */}
      <g
        transform="translate(50 52) scale(0.36) translate(-60 -92)"
        fill="#96805a"
        fillOpacity=".62"
      >
        <ellipse cx="22" cy="98" rx="11" ry="15" transform="rotate(-28 22 98)" />
        <ellipse cx="98" cy="98" rx="11" ry="15" transform="rotate(28 98 98)" />
        <path d="M33 76C40 66 80 66 87 76L103 146C82 157 38 157 17 146Z" />
        <circle cx="60" cy="45" r="33" />
      </g>
    </svg>
  );
}
