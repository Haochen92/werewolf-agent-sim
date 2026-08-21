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

export const apiUrl = (path: string): string => `${API_BASE_URL}${path}`;
