"""Per-game server runtime: run one game, turn its stream into events, deliver them to viewers.

One GameSession per running game. The game runs as a background asyncio task on the server's
event loop, consuming graph.astream(): between parts the task is just parked at its `async
for`, costing the loop nothing. The engine's nodes are synchronous, so LangGraph's async path
runs them in worker threads — their blocking LLM calls never stall the loop (verified on this
langgraph version: loop stays responsive through a blocking node; part semantics identical to
sync stream()). Our own code stays entirely on the loop: no hand-rolled threads, no bridge.

A model choice from SUPPORTED_GAME_MODELS (server/model_catalog.py: tested models only,
each with its compatible rescue) rides a ContextVar set inside the game's task. House-funded rows use the server's
configured backend; the others require a player API key (BYOK). LangGraph copies the task
context into its worker threads, so a BYOK game's key is applied only to the chosen model's
provider and never touches RunConfig, the event log, or disk; if it dies mid-game the error
surfaces redacted and the player restarts with a valid one.

Every part goes through the Translator; the resulting events are appended to the game's
in-memory log and pushed to each connected viewer's queue. When the game needs human
action, the graph interrupts — one write-once Future per interrupted seat. POST /turns
validates the submitted action (same rules as the CLI game) and fulfils that seat's
promise; once every promise resolves, the batch resumes the graph.

Who may see an event is decided at delivery time, per viewer: `entitled()` checks the event's
tier (public / wolves-only / one seat / observer) against the viewer's seat. At game_over
everyone becomes an observer and the held-back events flush out (ruling R7 — game over flips
permissions; it doesn't carry a reveal payload of its own).

The PacingTracker (server/pacing.py) drives the "3/5 players done" progress bars — computed from public
knowledge only, never from the real engine state, so the bar can't leak who acted (padded
20-30s completions make a non-actor indistinguishable from a slow one).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Sequence

from langgraph.types import Command

from Agents.config import RunConfig, build_runnable_config, normalize_run_config
from Agents.llm_factory import GAME_LLM, GameLLM
from Agents.memory import store
from Agents.memory.persistence import seed_memory_from_config
from Agents.observability import EvalCaseSink
from Agents.graphs.parent import parent_graph_compiled
from Agents.rules.board_clocks import alive_role_counts
from Agents.schemas.human_player import HumanTurnRequest
from Agents.state import fresh_game_state
from Agents.tracing import Metrics, create_langfuse_handler, flush, langfuse
from Agents.turn.human_turn import validate_human_response

from server.game_repository import GameRepository
from server.model_catalog import SUPPORTED_GAME_MODELS
from server.pacing import BRANCH_UNITS, PacingTracker
from server.schemas import events as ev
from server.seat_clocks import SeatClocks
from server.translate import Translator, _read_field

logger = logging.getLogger(__name__)


def entitled(event: ev.DurableEvent, seat: str, roles: dict[str, str],
             game_over: bool) -> bool:
    """May this viewer receive this event LIVE? Spectators have seat ""; at game_over
    everyone is an observer (the backlog flush relies on re-asking this per event)."""
    if game_over:
        return True
    tier = ev.EVENT_TIERS[event.type]
    if tier is ev.Tier.PUBLIC:
        return True
    if tier is ev.Tier.FACTION:
        return bool(seat) and roles.get(seat) == "wolf"
    if tier is ev.Tier.SEAT:
        return bool(seat) and getattr(event, "player", None) == seat
    return False  # OBSERVER: log-only until the unlock


class GameSession:
    """One running game: the stream-driving task + translator + log + subscriber fan-out.

    Field guide, by job:

    Engine bootstrap — the arguments one graph run needs (same entry path as the CLI):
      config        the LangGraph runnable config (thread id, checkpointer wiring).
      game_id       the game's identity, minted by RunConfig; also the URL key.
      _graph        the compiled parent graph (tests inject a fake).
      _context      runtime context handed to every node: metrics + eval-case sink.
      (seed_memory_from_config in __init__ is a pre-run SIDE EFFECT, not setup — it
      writes the process-global memory store the graph will read.)

    BYOK billing — separate from RunConfig on purpose (fingerprints would persist a key):
      _api_key       the player's key: session memory only, dies with the session;
                     also the string the error report scrubs.
      _llm_override  the (key, model, registry rescue) triple set on the GAME_LLM
                     ContextVar inside the game task; None = the server's env pays.

    The wire — what viewers consume:
      translator   the converter MACHINE: stream parts in, 0..N typed events out.
                   Stateful (its own shadow of game state + the global seq counter).
      log          the RECORD: every durable event in seq order. Reconnect = replay
                   this list; the injected repository persists each streamed tail.
      game_over    the permission flip (ruling R7): once True, entitled() treats
                   every viewer as an observer and the withheld backlog may flush.

    The human seat (HITL):
      human_players    which seats the ENGINE dealt to humans (read from the
                       INITIALIZE_GAME part); served by GET /games so the client
                       knows whose seats to render.
      _seat_tokens     the per-joiner secrets, in join order. Join order IS deal
                       order, so token i owns human_players[i] — seat_for_token()
                       is the proof-of-identity lookup behind turns, private event
                       tiers, and the status "you" field.
      pending_requests the parked interrupt payloads, keyed by seat — a dict because a
                       parallel superstep (night fan-out, votes) can interrupt for
                       several human seats at once; sequential phases just hold one
                       entry. The full prompt-bearing request stays server-side; the
                       wire carries only the slim input_request event.
      _pending_ids     seat -> LangGraph interrupt id, for the id-addressed batch
                       resume (multi-seat only; a lone answer resumes bare-value,
                       the path proven in live HITL games).
      _promises        the hand-off: one write-once Future per parked seat (created
                       at park time). submit_turn crosses the seat off pending and
                       fulfils its promise; _collect_answers awaits them all
                       (gather = the barrier) and resumes the graph with the batch
                       in one Command. The future object is the wire between the
                       HTTP world and the game task — always fulfil it in place,
                       never replace the registry entry.

    Delivery + lifecycle:
      _subscribers  one queue per connected viewer; _deliver fans events into these.
      _tracker      the PacingTracker (public-knowledge progress bars).
      error         the death report: a game task that dies lands its exception here
                    (key-redacted) instead of vanishing; GET /games serves it.
      _finished     awaitable "ended or died" signal, set in _run's finally.
      _task         the game's asyncio task handle (created by start()).
    """

    def __init__(self, run_config: RunConfig | dict[str, Any], *,
                 api_key: str = "", model: str = "",
                 seat_tokens: Sequence[str] = (), graph=None,
                 repository: GameRepository | None = None) -> None:
        # A selected model runs task-locally on either the ephemeral BYOK credential or,
        # for house-funded registry rows, the server's configured backend. No selection
        # means the environment/default accessor path remains in charge.
        self._api_key = api_key
        if api_key and not model:
            model = next(iter(SUPPORTED_GAME_MODELS))  # a bare key runs the default model
        row = SUPPORTED_GAME_MODELS.get(model)
        self._llm_override = GameLLM(
            api_key=api_key, model=model,
            rescue_model=row.rescue_model if row else None,
        ) if api_key or model else None

        # Engine bootstrap (+ the memory-seeding side effect).
        run = normalize_run_config(run_config)
        seed_memory_from_config(run.memory_persistence, target_store=store)
        self.config = build_runnable_config(run)
        self.game_id: str = self.config["configurable"]["game_id"]
        self._session_id = run.session_id
        self._graph = graph if graph is not None else parent_graph_compiled
        self._repository = repository
        self._context = {"metrics": Metrics(), "eval_sink": EvalCaseSink()}

        # The wire: converter machine, durable record, R7 permission flip.
        self.translator = Translator()
        self.log: list[ev.DurableEvent] = []
        self.game_over = False
        # Durable-plane cursors: how much of the log / seat knowledge is on disk.
        self._persisted = 0
        self._persisted_humans: list[str] = []

        # The human seat (HITL).
        self._seat_tokens = list(seat_tokens)
        self.human_players: list[str] = []
        self.pending_requests: dict[str, HumanTurnRequest] = {}
        self._pending_ids: dict[str, str] = {}
        self._promises: dict[str, asyncio.Future] = {}
        # AFK (seat_continuity.md §4–§5): the stopwatches live in SeatClocks; the session
        # lends it presence and the delegate action. Multi-human tables only.
        self.clocks = SeatClocks(
            self.game_id, self.pending_requests, enabled=len(self._seat_tokens) > 1,
            seat_present=self.seat_present, anyone_present=self.humans_present,
            delegate=lambda seat: self.submit_turn({"delegate": True}, seat=seat))
        # When the current batch of questions was asked; None while the graph runs. The
        # retention sweeper reads it: a parked game nobody is watching has a shelf life.
        self.parked_since: datetime | None = None

        # Delivery + lifecycle. Each viewer queue keeps its seat resolver (re-resolved per
        # check, never frozen at connect) — that is what makes presence answerable.
        self._subscribers: dict[asyncio.Queue, Callable[[], str]] = {}
        self._tracker = PacingTracker(self.publish_pacing)
        self.error: str | None = None
        self._finished = asyncio.Event()
        self._task: asyncio.Task | None = None

    # -- lifecycle ------------------------------------------------------------------------

    def start(self) -> None:
        self._task = asyncio.get_running_loop().create_task(
            self._run(fresh_game_state()), name=f"game-{self.game_id}")
        logger.info("game %s: task started (byok=%s, model=%s)",
                    self.game_id, bool(self._api_key),
                    self._llm_override.model if self._llm_override else "server-default")

    def start_recovered(self, *, waiting_on_humans: bool) -> None:
        """Resume a revived session (server restart). Parked-at-interrupt games wait
        for /turns first — the caller re-parked pending_requests from the checkpoint —
        while mid-generation crashes continue from the last committed superstep
        (astream(None) on an existing thread). Probe-verified 2026-08-20: the resume
        re-runs the interrupted phase (abort-and-re-execute across the grave)."""
        self._task = asyncio.get_running_loop().create_task(
            self._run(None, wait_answers_first=waiting_on_humans),
            name=f"game-{self.game_id}")
        logger.info("game %s: recovered (waiting_on_humans=%s, %d events rehydrated)",
                    self.game_id, waiting_on_humans, len(self.log))

    async def shutdown(self) -> None:
        """Cancel the running game task (server shutdown). Cancellation lands at the
        task's next await; a sync node already inside LangGraph's executor runs its
        current step to completion in its worker thread. Its last committed checkpoint
        and event tail are recovered on the next startup."""
        self.clocks.cancel_all()
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("game %s: cancelled on server shutdown", self.game_id)

    async def _run(self, graph_input: Any, wait_answers_first: bool = False) -> None:
        if self._llm_override is not None:
            GAME_LLM.set(self._llm_override)
        recovered = graph_input is None
        trace_input = {"game_id": self.game_id, "recovered": recovered}
        # Stable across process restarts: a recovered GameSession adds a new root segment to
        # the SAME game trace rather than creating a second trace for the continuation.
        trace_id = langfuse.create_trace_id(seed=f"werewolf-game:{self.game_id}")
        try:
            with langfuse.start_as_current_observation(
                trace_context={"trace_id": trace_id}, as_type="span",
                name="werewolf-game", input=trace_input,
            ) as root:
                # Pin LangGraph/LangChain observations to this root explicitly. The manual
                # node spans inherit the active OTEL context; the callback also carries the
                # IDs, so worker-thread context propagation is not a correctness dependency.
                self.config["callbacks"] = [create_langfuse_handler(trace_context={
                    "trace_id": trace_id, "parent_span_id": root.id})]
                root.update_trace(
                    name="werewolf_game", session_id=self._session_id,
                    input=trace_input, output={"status": "running"},
                    metadata={
                        "game_id": self.game_id,
                        "model": (self._llm_override.model if self._llm_override
                                  else "server-default"),
                        "byok": bool(self._api_key),
                        "recovered": recovered,
                    },
                )
                try:
                    await self._drive_graph(graph_input, wait_answers_first)
                    final_output = {
                        "status": "success", "game_over": self.game_over,
                        "event_count": len(self.log),
                    }
                    root.update(output=final_output)
                    root.update_trace(output=final_output)
                except asyncio.CancelledError:
                    # A restart is an interrupted trace segment, not a failed game. The
                    # recovered process reattaches to trace_id and eventually writes success.
                    interrupted_output = {
                        "status": "interrupted", "event_count": len(self.log)}
                    root.update(output=interrupted_output)
                    root.update_trace(output=interrupted_output)
                    raise
                except Exception as exc:  # surface, don't vanish: report task death
                    detail = repr(exc)
                    if self._api_key:
                        # Provider auth errors can echo the credential; viewers see error text.
                        detail = detail.replace(self._api_key, "***")
                    self.error = detail
                    error_output = {"status": "error", "error": detail}
                    root.update(output=error_output, level="ERROR", status_message=detail)
                    root.update_trace(output=error_output)
                    logger.error("game %s: task died: %s", self.game_id, detail)
                    if self._repository is not None:
                        await self._repository.upsert_game(
                            self.game_id, status="dropped", error=detail)
                finally:
                    # No phase upsert here: cancellation must leave the durable row
                    # 'running' so the next boot's recovery picks the game up.
                    self._finished.set()
                    if self.error is None:
                        logger.info("game %s: finished (game_over=%s, %d events)",
                                    self.game_id, self.game_over, len(self.log))
        finally:
            flush()

    async def _drive_graph(self, graph_input: Any, wait_answers_first: bool) -> None:
        """Stream/resume the graph while _run owns the one game-level trace context."""
        if wait_answers_first:
            # Recovered at an interrupt: the seats were re-parked from the checkpoint
            # before this task started; wait for their answers.
            graph_input = Command(resume=await self._collect_answers())
        while True:
            interrupted = False
            async for part in self._graph.astream(
                graph_input, config=self.config, context=self._context,
                stream_mode=["updates", "custom"], subgraphs=True, version="v2",
            ):
                if self._on_part(part):
                    # Sticky: the interrupt part is often NOT last (siblings keep
                    # streaming after it), so keep consuming and remember it.
                    interrupted = True
                # Synchronous per part: a crash loses at most this part's events.
                await self._persist_tail()
            if not interrupted:
                break
            # Resume with user input, once every interrupted seat has answered.
            graph_input = Command(resume=await self._collect_answers())
        if self.game_over and self._repository is not None:
            # Existing EventRows become the replay: completion only finalizes metadata
            # and lifecycle on their parent GameRow, never copies the log.
            await self._repository.complete_game(
                self.game_id, self.log, len(self.human_players))

    async def _persist_tail(self) -> None:
        """Push the log's unpersisted suffix + newly-learned human seats to the
        game repository (both helpers no-op when Postgres is unconfigured and never
        raise — durability failing must not cost the running game)."""
        if self._repository is None:
            return
        if len(self.log) > self._persisted:
            await self._repository.record_events(
                self.game_id, self.log[self._persisted:])
            self._persisted = len(self.log)
        if self.human_players != self._persisted_humans:
            await self._repository.upsert_game(
                self.game_id, human_players=self.human_players)
            self._persisted_humans = list(self.human_players)

    def _on_part(self, part) -> bool:
        """Translate, record, publish. Returns True on an interrupt part."""
        data = part.get("data") or {}

        # Park BEFORE translating: the input_request events translated from this very
        # part must carry their seats' AFK deadlines, so the timers are armed first.
        # Root mirror only — subgraphs=True streams each interrupt twice (child ns +
        # root), and parking the child copy could re-park a seat that answered in the
        # gap. Falling back to the seat as the answer key covers items without ids.
        interrupted = "__interrupt__" in data and not (part.get("ns") or ())
        if interrupted:
            self.parked_since = datetime.now(timezone.utc)
            # A parallel superstep can carry several interrupts (one per human seat).
            for item in data["__interrupt__"]:
                request = HumanTurnRequest.model_validate(_read_field(item, "value"))
                self.pending_requests[request.player_id] = request
                self._pending_ids[request.player_id] = (
                    _read_field(item, "id", "") or request.player_id)
                self._promises[request.player_id] = asyncio.get_running_loop().create_future()
                self.clocks.arm(request)

        events = self.translator.translate(part)
        for event in events:
            if event.type == "input_request" and event.player in self.turn_deadlines:
                # Events are frozen; the stamped copy (same seq) is what gets recorded.
                event = event.model_copy(
                    update={"deadline": self.turn_deadlines[event.player]})
            self.log.append(event)
            if event.type == "game_over":
                self.game_over = True
            self._deliver(event)

        # Pacing ticks ride part identity: a root wrapper part = that night branch finished;
        # a vote-node part = one ballot cast. (Both are otherwise ignored/buffered.)
        # Cached parts are re-deliveries (post-resume replays / cache hits) — their events
        # were dropped by the translator and their ticks must not double the bars.
        if isinstance(data, dict) and _read_field(
                _read_field(data, "__metadata__", {}) or {}, "cached"):
            return interrupted
        ns = part.get("ns") or ()
        scope = ns[0].split(":")[0] if ns else "root"
        for node in data:
            if scope == "root" and node in BRANCH_UNITS:
                self._tracker.on_branch_done(BRANCH_UNITS[node])
            if node in ("vote", "vote_human") and scope == "DAY_PHASE":
                self._tracker.on_ballot()
            if node == "INITIALIZE_GAME":
                self.human_players = list(
                    _read_field(data[node], "human_players", ()) or ())
        return interrupted

    async def abandon(self, reason: str) -> None:
        """Retention (seat_continuity.md §7): stop a parked game nobody is watching. The
        reason becomes the epitaph viewers see; the caller flips the row to dropped."""
        self.error = reason
        await self.shutdown()
        self._finished.set()  # a never-started shell has no task to settle it

    @property
    def turn_deadlines(self) -> dict[str, str]:
        """Effective deadline per parked seat (ISO), served in status and stamped on
        input_request — the client's countdown source."""
        return self.clocks.deadlines

    # -- presence (seat_continuity.md §3) --------------------------------------------------

    def connected_seats(self) -> set[str]:
        """Human seats with at least one open stream RIGHT NOW. Spectators resolve to
        "" and never count; a snapshot, not a history of the window."""
        return {seat for resolve in self._subscribers.values() if (seat := resolve())}

    def seat_present(self, seat: str) -> bool:
        return seat in self.connected_seats()

    def humans_present(self) -> bool:
        return bool(self.connected_seats())

    # -- fan-out --------------------------------------------------------------------------

    def _deliver(self, event: ev.DurableEvent) -> None:
        self._tracker.on_event(event)
        for q in self._subscribers:
            q.put_nowait(("game", event))

    def publish_pacing(self, snapshot: ev.PhaseProgress) -> None:
        for q in self._subscribers:
            q.put_nowait(("pacing", snapshot))

    def subscribe(self, viewer_seat: Callable[[], str] | None = None) -> asyncio.Queue:
        """Register a viewer queue with its seat resolver. A human seat connecting is the
        presence signal that lifts a grace or un-parks the table."""
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers[q] = viewer_seat or (lambda: "")
        seat = self._subscribers[q]()
        if seat:
            self.clocks.on_seat_returned(seat)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        """A stream closed. If that was the seat's last stream mid-question, its clock
        drops to the absence grace — the tab may be retrying, or may be gone."""
        resolve = self._subscribers.pop(q, None)
        seat = resolve() if resolve is not None else ""
        if seat and not self.seat_present(seat):
            self.clocks.on_seat_left(seat)

    async def wait_finished(self) -> None:
        await self._finished.wait()

    # -- seat identity (the token minted at /join or the solo /games door) -----------------

    def seat_for_token(self, token: str) -> str | None:
        """Resolve a seat token to its proven engine seat.

        None = unknown token (the routes 403). "" = valid token but INITIALIZE_GAME
        hasn't dealt seats yet — a real window: viewers connect to /events the moment
        /start returns, so SSE re-resolves per entitlement check rather than freezing
        the connect-time answer (the same lesson as the roles rebind)."""
        try:
            i = self._seat_tokens.index(token)
        except ValueError:
            return None
        return self.human_players[i] if i < len(self.human_players) else ""

    def position_of(self, token: str) -> int | None:
        """1-based join position owning this token (mirrors GameLobby.position_of,
        so /rejoin serves both registry phases through one call)."""
        try:
            return self._seat_tokens.index(token) + 1
        except ValueError:
            return None

    # -- the human turn (from POST /turns) ------------------------------------------------

    def submit_turn(self, body: dict, seat: str = "") -> None:
        """Validate against the seat's pending request (the CLI's HITL contract, reused)
        and, once every interrupted seat has answered, resume the parked game task.
        Raises HumanTurnContractError on a bad action, LookupError on a bad seat."""
        if not self.pending_requests:
            raise LookupError("no pending input_request for this game")
        if not seat:
            # A lone pending seat needs no addressing (the solo-game path).
            if len(self.pending_requests) > 1:
                raise LookupError(
                    f"several seats owe input ({sorted(self.pending_requests)}); "
                    "identify one with ?seat=")
            seat = next(iter(self.pending_requests))
        request = self.pending_requests.get(seat)
        if request is None:
            raise LookupError(f"no pending input_request for seat {seat!r}")
        response = validate_human_response(request, body)
        # Cross the seat off FIRST: a duplicate submission then bounces at the
        # LookupError above and can never reach set_result (futures are write-once —
        # a second set would raise InvalidStateError).
        del self.pending_requests[seat]
        self.clocks.clear(seat)
        self._promises[seat].set_result(response.model_dump())
        logger.info("game %s: turn accepted for %s (%d seat(s) still owe input)",
                    self.game_id, seat, len(self.pending_requests))

    async def _collect_answers(self) -> Any:
        """Await every seat's promise, then hand the batch to the graph.

        gather is the barrier (eager answers are already-resolved futures and cost
        nothing); each future then carries its own value, so the harvest is
        self-describing — no ordering to trust. Iterating the live registry (no
        snapshot) and wholesale reset are safe because no park can happen between
        the stream settling and this return: submit_turn fulfils futures, it never
        adds or removes registry entries."""
        await asyncio.gather(*self._promises.values())
        self.parked_since = None
        answers = {self._pending_ids.pop(seat): fut.result()
                   for seat, fut in self._promises.items()}
        self._promises = {}
        if len(answers) == 1:
            # The bare-value resume — the single-interrupt path proven in live HITL
            # games. The id-addressed mapping only engages for true parallel batches.
            return next(iter(answers.values()))
        return answers

    # -- census exposure (GET /games/{id}) ------------------------------------------------

    def public_alive_counts(self) -> dict[str, int]:
        started = next((e for e in self.log if e.type == "game_started"), None)
        if started is None:
            return {}
        dead = [d for n in self.log if n.type == "night_result" for d in n.deaths]
        dead += [e for e in self.log if e.type == "lynch_result" and e.role]
        return alive_role_counts(started.cast_role_counts, dead)
