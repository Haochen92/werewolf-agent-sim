import Link from 'next/link';

/**
 * Walking-skeleton landing. Deliberately unstyled: D1's three-door hierarchy and the replay
 * rail arrive in the presentational pass. This exists so the route tree is navigable.
 */
export default function HomePage() {
  return (
    <main style={{ padding: 24, fontFamily: 'system-ui' }}>
      <h1>Werewolf — agent sim</h1>
      <p>Watch AI agents deceive each other — and see exactly why.</p>
      <ul>
        <li>
          <Link href="/replays">Watch a replay</Link>
        </li>
      </ul>
    </main>
  );
}
