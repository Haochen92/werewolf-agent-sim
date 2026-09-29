/**
 * Typed endpoint functions. Thin by design — the only thing they add over `request<T>()` is
 * that every URL string in the app is written exactly once, here.
 */
import { request, requestWithHeaders } from './request';
import type {
  ActionKind,
  DraftResponse,
  GameCreated,
  GameStatus,
  ModelsMenu,
  NewSoloGame,
  NewRoom,
  ReplayGame,
  ReplaySummary,
  RoomCreated,
  RoomSummary,
  SeatJoined,
  TurnAccepted,
} from '@/types/contracts';

export interface ReplayListParams {
  limit?: number;
  offset?: number;
}

function replaysPath(params: ReplayListParams): string {
  const query = new URLSearchParams();
  if (params.limit !== undefined) query.set('limit', String(params.limit));
  if (params.offset !== undefined) query.set('offset', String(params.offset));
  const suffix = query.toString();
  return `/replays${suffix ? `?${suffix}` : ''}`;
}

export function listReplays(params: ReplayListParams = {}): Promise<ReplaySummary[]> {
  return request<ReplaySummary[]>(replaysPath(params));
}

export interface ReplayPage {
  replays: ReplaySummary[];
  /** Finished games in all, across every page (`X-Total-Count`); the page's length if absent. */
  total: number;
}

/** `listReplays` plus the archive's total, which rides in a header rather than the body. */
export async function listReplaysWithTotal(
  params: ReplayListParams = {},
): Promise<ReplayPage> {
  const { body, headers } = await requestWithHeaders<ReplaySummary[]>(replaysPath(params));
  const total = Number.parseInt(headers.get('X-Total-Count') ?? '', 10);
  return { replays: body, total: Number.isFinite(total) ? total : body.length };
}

export function getReplay(gameId: string): Promise<ReplayGame> {
  return request<ReplayGame>(`/replays/${encodeURIComponent(gameId)}`);
}

export function getGameStatus(gameId: string): Promise<GameStatus> {
  return request<GameStatus>(`/games/${encodeURIComponent(gameId)}`);
}

export function listRooms(): Promise<RoomSummary[]> {
  return request<RoomSummary[]>('/rooms');
}

export function getModels(): Promise<ModelsMenu> {
  return request<ModelsMenu>('/models');
}

// --- games: create, join, rejoin, start, lock ------------------------------

/** Solo / instant-start door. Returns the seat token ONCE — stash it immediately. */
export function createGame(body: NewSoloGame): Promise<GameCreated> {
  return request<GameCreated>('/games', { method: 'POST', body });
}

/** The room's creator passes its host key, which marks their seat as the host's. */
export function joinGame(
  gameId: string,
  name: string,
  hostKey?: string | null,
): Promise<SeatJoined> {
  const query = hostKey ? `?host_key=${encodeURIComponent(hostKey)}` : '';
  return request<SeatJoined>(`/games/${encodeURIComponent(gameId)}/join${query}`, {
    method: 'POST',
    body: { name },
  });
}

/** Give up this device's seat in a waiting room (the seat cookie says which). The host closes instead. */
export function leaveRoom(gameId: string): Promise<void> {
  return request<void>(`/games/${encodeURIComponent(gameId)}/leave`, { method: 'POST' });
}

/** Close a waiting room for everyone; its URL answers 410 from then on. Host only. */
export function closeRoom(gameId: string, hostKey: string): Promise<void> {
  const query = `?host_key=${encodeURIComponent(hostKey)}`;
  return request<void>(`/games/${encodeURIComponent(gameId)}/close${query}`, {
    method: 'POST',
  });
}

/** Re-prove seat ownership after cookie loss, using the localStorage copy of the token. */
export function rejoinGame(gameId: string, token: string): Promise<SeatJoined> {
  return request<SeatJoined>(`/games/${encodeURIComponent(gameId)}/rejoin`, {
    method: 'POST',
    body: { token },
  });
}

/** Resume a game that lost its key in a restart; any seat holder may. 422 = the provider refused it. */
export function fundGame(gameId: string, apiKey: string): Promise<GameStatus> {
  return request<GameStatus>(`/games/${encodeURIComponent(gameId)}/key`, {
    method: 'POST',
    body: { api_key: apiKey },
  });
}

/** host_key rides as a QUERY parameter, not a body — the server's contract. */
export function startGame(gameId: string, hostKey?: string | null): Promise<unknown> {
  const query = hostKey ? `?host_key=${encodeURIComponent(hostKey)}` : '';
  return request(`/games/${encodeURIComponent(gameId)}/start${query}`, { method: 'POST' });
}

export function lockRoom(
  gameId: string,
  locked: boolean,
  hostKey: string,
): Promise<RoomSummary> {
  const query = `?host_key=${encodeURIComponent(hostKey)}&locked=${locked}`;
  return request<RoomSummary>(`/games/${encodeURIComponent(gameId)}/lock${query}`, {
    method: 'POST',
  });
}

export function createRoom(body: NewRoom): Promise<RoomCreated> {
  return request<RoomCreated>('/rooms', { method: 'POST', body });
}

// --- turns ------------------------------------------------------------------

/**
 * The turn payload shapes, taken from the engine's own contract
 * (`Agents/turn/human_turn.py::validate_human_response`) rather than guessed:
 *
 *   delegate       → `{delegate: true}` and NOTHING else. Legal in every phase.
 *   discuss        → `{message}` or `{pass_turn: true}` (pass needs the turn to be passable)
 *   wolf_discuss   → `{message}` only — wolf talk cannot be passed and takes no target
 *   every other kind → `{target}`, which must be one of the request's candidates
 */
export type TurnPayload =
  { delegate: true } | { pass_turn: true } | { message: string } | { target: string };

export function submitTurn(gameId: string, payload: TurnPayload): Promise<TurnAccepted> {
  return request<TurnAccepted>(`/games/${encodeURIComponent(gameId)}/turns`, {
    method: 'POST',
    body: payload,
  });
}

/**
 * The seat's agent writes one line for the discussion turn it owes (D25): from rough notes
 * (up to 500 chars), or, with the notes empty, a line of its own. Nothing enters the game: the
 * line goes back into the box and is sent with `submitTurn` like any typed line. 409 = no turn
 * or no drafts left; 503 = the model failed.
 */
export function draftLine(gameId: string, notes: string): Promise<DraftResponse> {
  return request<DraftResponse>(`/games/${encodeURIComponent(gameId)}/draft`, {
    method: 'POST',
    body: { notes },
  });
}

/** Which of the two dock shapes an action_kind takes (D17 — the list is closed at 8). */
export function isTextTurn(kind: ActionKind): boolean {
  return kind === 'discuss' || kind === 'wolf_discuss';
}
