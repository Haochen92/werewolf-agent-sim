/**
 * The ONE definition of the API base URL (dota2pred copy-pasted its own base URL across
 * eight call sites and paid for it).
 *
 * Dev: an absolute origin (`http://localhost:8001`). Prod: same-origin `/api` behind Caddy
 * — required, not stylistic: the seat cookie is `HttpOnly; SameSite=Lax; Path=/games/{id}`
 * with no `domain`, so the frontend has to be same-site with the API or the cookie is never
 * sent (build_plan §5).
 */
export const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? '/api';

/**
 * On the server, the API by its address inside the deployment's network (`wolf-server:8000`):
 * a page rendered with its data in it calls it from there (the archive). Set only in
 * production's compose; without it nothing is fetched on the server, as in dev and the tests.
 */
export const SERVER_API_URL =
  typeof window === 'undefined' ? (process.env.API_INTERNAL_URL ?? null) : null;

export const apiUrl = (path: string): string => `${SERVER_API_URL ?? API_BASE_URL}${path}`;
