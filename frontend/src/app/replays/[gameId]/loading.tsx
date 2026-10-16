/**
 * While the replay's page loads: nothing of its own, as the layout's cover is already over it
 * (`ReplayCover`). The file is still needed: without it a click waits on the page from the
 * server before the cover can show.
 */
export default function ReplayLoading() {
  return null;
}
