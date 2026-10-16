/**
 * While the replay's page loads: nothing of its own, as the layout's departure is already over
 * it (`DepartureHost`). The file is still needed: without it a click waits on the page from the
 * server before the departure can start.
 */
export default function ReplayLoading() {
  return null;
}
