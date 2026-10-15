import { StationStill } from '@/stage/scenes/StationStill';

/** While the table's page loads: the empty platform, "Boarding…" (beat sheet §1a). */
export default function GameLoading() {
  return <StationStill what="game" line="Boarding…" />;
}
