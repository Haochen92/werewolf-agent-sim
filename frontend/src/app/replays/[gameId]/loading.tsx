import { StationStill } from '@/stage/scenes/StationStill';

/** While the replay's page loads: the empty platform, "Rewinding the reels…" (beat sheet §1a). */
export default function ReplayLoading() {
  return <StationStill what="replay" hud="replay" line="Rewinding the reels…" />;
}
