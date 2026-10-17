/**
 * The pack's dawn record when it only repeats the morning report (owner, 2026-10-17): the kill
 * landed and its role was announced, or hidden from the pack as from everyone. The wolves are not
 * told it again, at dawn or in the transcript. A save, an immune target and a role the illusionist
 * hid (the record names it in `seen`) are still told.
 */
export function repeatsDawn(r: {
  actor: string;
  result: string;
  seen?: readonly string[] | null;
}): boolean {
  return r.actor === 'wolves' && r.result === 'killed' && !r.seen?.length;
}
