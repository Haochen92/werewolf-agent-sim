/**
 * A role card's back: the stitched ring and the star, in paper and ink. Its own file so that a
 * page drawing only the picture (the ticket office's "dealt at random" card) does not pull in
 * the card's flip and its animation library.
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
      <path
        d="M50 22 L56 44 L78 50 L56 56 L50 78 L44 56 L22 50 L44 44Z"
        fill="#cbb992"
        stroke="#24180c"
        strokeWidth="1.4"
        strokeLinejoin="round"
      />
      <circle cx="50" cy="50" r="5" fill="#efe4cb" stroke="#24180c" strokeWidth="1.2" />
    </svg>
  );
}
