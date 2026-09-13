"""One running game: run it, turn its stream into events, deliver them to viewers.

One GameSession per running game. The game runs as a background asyncio task on the
server's event loop, consuming graph.astream(): between chunks the task is parked at its
`async for`, costing the loop nothing. The engine's nodes are synchronous, so LangGraph's
async path runs them in worker threads, and their blocking LLM calls never stall the loop
(verified on this LangGraph version: the loop stays responsive through a blocking node, and
chunk semantics are identical to the sync stream()). Our own code stays on the loop: no
hand-rolled threads, no bridge.

Which model runs, and on whose key, is a choice from SUPPORTED_GAME_MODELS
(game/model_catalog.py: tested models only, each with its compatible rescue). It rides a
ContextVar set inside the game's task; LangGraph copies the task context into its worker
threads, so a player's key reaches only the chosen model's provider and never touches
RunConfig, the event log, or disk. If the game dies mid-run the error surfaces with the key
redacted. After a restart the key is gone, and the game waits for a seat holder to supply it
again (see the live registry).

Every chunk goes through the Translator; the resulting events are appended to the game's
in-memory log and pushed to each connected viewer's queue. When the game needs human
action, the graph interrupts, and the session holds one empty slot per interrupted seat.
POST /turns validates the submitted action (same rules as the CLI game) and fills that
seat's slot; once every slot is filled, the batch resumes the graph.

Who may see an event is decided at delivery time, per viewer, by the stream route using
`entitlement.entitled()`; the session only fans every event into every viewer's queue. At
game over everyone becomes an observer and the held-back events flush out.

The PacingTracker (game/pacing.py) drives the "3/5 players done" progress bars, computed
from public knowledge only, never from the real engine state, so the bar cannot leak who
acted (padded 20-30 s completions make a non-actor indistinguishable from a slow one).
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

from server.storage.game_repository import GameRepository
from server.game.model_catalog import SUPPORTED_GAME_MODELS
from server.game.pacing import PacingTracker
from server.schemas import events as ev
from server.game.seat_clocks import SeatClocks
from server.game.translate import Translator, _read_field, is_replayed, scope_of

logger = logging.getLogger(__name__)


class GameSession:
    """One running game: the task that drives the engine, the log of what it produced,
    and the browsers watching it.

    Two lifecycles live here, and they run independently of each other:

    * The game's: one task, from start() to _end(). It runs whether or not anyone is
      watching, pauses while a human seat owes an answer, and ends when the game is
      over, dropped, or crashed.
    * The streams': one open event stream per browser tab, from subscribe() to
      unsubscribe(). There are zero to many at once, they come and go at any point in
      the game, and each is a queue that _deliver() feeds.

    They meet in two places only: a seat holder's stream opening or closing tells the
    AFK clocks whether that seat is present, and the last stream closing after the game
    has ended fires on_idle so the registry can forget this object.

    Attributes, by job. Every one is set in __init__; this is the only place they are
    explained.

    Which model runs, and who pays. Kept out of RunConfig on purpose: RunConfig is
    fingerprinted and recorded, and a key must never be written down.
      _api_key        the player's key, if a player paid. Session memory only; also the
                      string the error report scrubs.
      _llm_selection  this game's model, its rescue model from the catalogue, and the key
                      if any. A bare key with no model runs the catalogue's first row.
                      Set on the GAME_LLM ContextVar as the task's first act, so the
                      model factory uses it instead of the environment. None = nothing
                      was chosen and the environment decides (CLI, batch).

    Engine bootstrap: what one graph run needs, the same entry path as the CLI.
      config        the LangGraph runnable config: thread id, checkpointer wiring.
      game_id       the game's identity, minted by RunConfig; also the URL key.
      _session_id   the tracing session id, so Langfuse groups this game's traces.
      _graph        the compiled parent graph; tests inject a fake.
      _repository   the database gateway; None means nothing is written down.
      _context      runtime context handed to every node: metrics and the eval-case
                    sink.
      Building the config also seeds the process-wide memory store the graph reads.
      That is a side effect of construction, not part of this object's state.

    What travels to the browsers.
      translator    turns each engine chunk into zero or more typed events. Stateful:
                    it keeps its own view of roles and the running seq counter.
      log           every durable event, in seq order. A reconnecting viewer is caught
                    up from this list; the repository is fed its tail as it grows.
      game_over     flips True on the game_over event. From then on the stream route
                    treats every viewer as an observer and sends the held-back events.

    Bookmarks for the write-through: how much of the above is already in the database,
    so each save writes only what came after.
      _saved_event_count  how many events from the front of the log are saved.
      _saved_humans       the human seat list as last written to the game row.

    The human turn, where the game waits.
      human_players     which seats the engine dealt to humans, read from its first
                        chunk. Served by GET /games so the client knows whose seats to
                        draw.
      _seat_tokens      each joiner's secret, in join order. Join order is deal order,
                        so token i owns human_players[i]; seat_for_token() is the
                        proof of identity behind turns, private event tiers and the
                        status "you" field.
      pending_requests  the questions the engine is waiting on, keyed by seat. A dict
                        because a parallel step (night actions, votes) can ask several
                        human seats at once. Two jobs: the keys say which seats still
                        owe an answer (the status route, the sweeper and recovery read
                        that), and each value holds that turn's rules, which the
                        answer is checked against. The full request never leaves the
                        server; the wire carries only the slim input_request event.
      _pending_ids      the engine's own id for each parked question, so a batch of
                        answers can be filed back under the names the engine expects.
      _pending_answers  one empty Future per parked seat, created at park time: the
                        hand-off between the HTTP world and the game task. submit_turn
                        sets the answer on it; _collect_answers waits for all of them
                        and resumes the engine with the batch. A Future takes one
                        value only, and the task waits on the exact object created at
                        park time, so the answer is always set in place, never by
                        replacing the entry.
      clocks            the SeatClocks: one AFK timer per waiting seat. It shares the
                        pending_requests dict, asks the session who is present, and
                        answers an expired turn through submit_turn as a delegate.
                        Multi-human tables only.
      parked_since      when the current batch of questions was asked; None while the
                        engine runs. The retention sweeper reads it.
      awaiting_key      True for a key-funded game rebuilt after a restart, until a
                        seat holder supplies the key again (the live registry's
                        resume_with_key). No task runs during the wait; the sweeper
                        treats it like a parked turn.

    The streams' lifecycle.
      _subscribers  one queue per open event stream, keyed by the queue because that is
                    the handle the route holds. The value is the connection's seat
                    token, "" for a spectator, mapped to a seat on every check rather
                    than once at connect time, since seats are dealt after streams open.
      _tracker      the PacingTracker; its snapshots are pushed into the same queues.

    The game's own lifecycle.
      _task       the asyncio task running the game, created by start() or
                  resume_game().
      _finished   the "ended" flag, set by _end() on every way out; wait_finished()
                  awaits it, ended reads it.
      error       why the game died, with the key redacted, or the reason it was
                  dropped. GET /games serves it as the ended card's text.
      on_idle     set by the live registry. Fired once, when the game has ended and its
                  last viewer has gone, so the registry can forget this object.
    """

    def __init__(self, run_config: RunConfig | dict[str, Any], *,
                 api_key: str = "", model: str = "",
                 seat_tokens: Sequence[str] = (), graph=None,
                 repository: GameRepository | None = None) -> None:

        # Which model runs, and who pays.
        self._api_key = api_key
        if api_key and not model:
            model = next(iter(SUPPORTED_GAME_MODELS))
        row = SUPPORTED_GAME_MODELS.get(model)
        self._llm_selection = GameLLM(
            api_key=api_key, model=model,
            rescue_model=row.rescue_model if row else None,
        ) if api_key or model else None

        # Engine bootstrap.
        run = normalize_run_config(run_config)
        seed_memory_from_config(run.memory_persistence, target_store=store)
        self.config = build_runnable_config(run)
        self.game_id: str = self.config["configurable"]["game_id"]
        self._session_id = run.session_id
        self._graph = graph if graph is not None else parent_graph_compiled
        self._repository = repository
        self._context = {"metrics": Metrics(), "eval_sink": EvalCaseSink()}

        # What travels to the browsers, and how much of it is already saved.
        self.translator = Translator()
        self.log: list[ev.DurableEvent] = []
        self.game_over = False
        self._saved_event_count = 0
        self._saved_humans: list[str] = []

        # The human turn.
        self._seat_tokens = list(seat_tokens)
        self.human_players: list[str] = []
        self.pending_requests: dict[str, HumanTurnRequest] = {}
        self._pending_ids: dict[str, str] = {}
        self._pending_answers: dict[str, asyncio.Future] = {}
        self.clocks = SeatClocks(
            self.game_id, self.pending_requests, enabled=len(self._seat_tokens) > 1,
            seat_present=self.seat_present, anyone_present=lambda: self.humans_present,
            delegate=lambda seat: self.submit_turn({"delegate": True}, seat=seat))
        self.parked_since: datetime | None = None
        self.awaiting_key: bool = False

        # The streams' lifecycle.
        self._subscribers: dict[asyncio.Queue, str] = {}
        self._tracker = PacingTracker(self.publish_pacing)

        # The game's own lifecycle.
        self._task: asyncio.Task | None = None
        self._finished = asyncio.Event()
        self.error: str | None = None
        self.on_idle: Callable[[], None] | None = None

    # -- the game's lifecycle: start, run, end ---------------------------------------------

    def start(self) -> None:
        self._task = asyncio.get_running_loop().create_task(
            self._run(fresh_game_state()), name=f"game-{self.game_id}")
        logger.info("game %s: task started (byok=%s, model=%s)",
                    self.game_id, bool(self._api_key), self.model or "server-default")

    async def _run(self, graph_input: Any, waiting_on_humans: bool = False) -> None:
        if self._llm_selection is not None:
            GAME_LLM.set(self._llm_selection)
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
                        "model": (self._llm_selection.model if self._llm_selection
                                  else "server-default"),
                        "byok": bool(self._api_key),
                        "recovered": recovered,
                    },
                )
                try:
                    await self._drive_graph(graph_input, waiting_on_humans)
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
                    if self.error is None:
                        logger.info("game %s: finished (game_over=%s, %d events)",
                                    self.game_id, self.game_over, len(self.log))
        finally:
            # Whatever way the task leaves, including a failure in the tracing setup
            # above: mark the game ended, then push the buffered spans out.
            self._end()
            flush()

    async def _drive_graph(self, graph_input: Any, waiting_on_humans: bool) -> None:
        """The streaming loop. Run the engine until the game ends, handling each chunk as
        it arrives. Each time the engine pauses for a human seat, the stream ends; wait
        for every parked seat's answer, then resume it with the batch. Returns only when
        the game is over, or a restart cancels the task, or the engine raises."""
        if waiting_on_humans:
            # Recovered at an interrupt: the seats were re-parked from the checkpoint
            # before this task started; wait for their answers.
            graph_input = Command(resume=await self._collect_answers())
        while True:
            interrupted = False
            async for chunk in self._graph.astream(
                graph_input, config=self.config, context=self._context,
                stream_mode=["updates", "custom"], subgraphs=True, version="v2",
            ):
                if self._on_chunk(chunk):
                    # Sticky: the interrupt chunk is often NOT last (siblings keep
                    # streaming after it), so keep consuming and remember it.
                    interrupted = True
                # Synchronous per chunk: a crash loses at most this chunk's events.
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
        if len(self.log) > self._saved_event_count:
            await self._repository.record_events(
                self.game_id, self.log[self._saved_event_count:])
            self._saved_event_count = len(self.log)
        if self.human_players != self._saved_humans:
            await self._repository.upsert_game(
                self.game_id, human_players=self.human_players)
            self._saved_humans = list(self.human_players)

    def _on_chunk(self, chunk) -> bool:
        """Handle one chunk from the engine's stream. Returns True when the chunk is an
        interrupt, which tells the streaming loop the engine is about to pause.

        Upon interrupt, the engine surfaces the same interrupt event twice, first in the
        subgraph, followed by the parent graph, because the stream reports nested graphs
        at every level. Only the parent graph's interrupt is parked for human input.

        Translates the chunk into events the browser understands, appends them to the
        event log, and sends them to every connected stream. Upon game over, allows all
        viewers access to all event types.

        Updates the progress bar.

        A chunk marked cached is skipped: the engine already produced it once and this
        session handled it then.
        """
        data = chunk.get("data") or {}
        if is_replayed(data):
            return False

        interrupted = "__interrupt__" in data and not (chunk.get("ns") or ())
        if interrupted:
            self.parked_since = datetime.now(timezone.utc)
            for item in data["__interrupt__"]:
                self.park(HumanTurnRequest.model_validate(_read_field(item, "value")),
                          _read_field(item, "id", ""))

        for event in self.translator.translate(chunk, deadlines=self.turn_deadlines):
            self.log.append(event)
            if event.type == "game_over":
                self.game_over = True
            self._deliver(event)

        self._tracker.on_chunk(scope_of(chunk), data)

        if "INITIALIZE_GAME" in data:  # the deal: which seats went to humans
            self.human_players = list(
                _read_field(data["INITIALIZE_GAME"], "human_players", ()) or ())
        return interrupted

    async def drop(self, reason: str) -> None:
        """Give this game up for good: stop it and record why. Retention calls this on a
        parked game nobody is watching. The reason is what viewers see on the ended
        card; the live registry marks the row dropped."""
        self.error = reason
        await self.suspend()
        self._end()  # a never-started shell has no task to settle it

    async def suspend(self) -> None:
        """Stop the task because the process is going down; the game is not over. Its row
        stays running and the next boot rebuilds it from the last checkpoint and the
        saved events. Cancellation lands at the task's next await; a sync node already
        inside LangGraph's executor finishes its current step in its worker thread."""
        self.clocks.cancel_all()
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("game %s: cancelled on server shutdown", self.game_id)

    async def wait_finished(self) -> None:
        """Block until the game has ended, whichever way."""
        await self._finished.wait()

    @property
    def ended(self) -> bool:
        """The game reached its end, its task died, or it was abandoned. Read-only: the
        session ends itself through _end, and nothing outside sets it."""
        return self._finished.is_set()

    def _end(self) -> None:
        """Mark the game ended, wake anyone waiting on it, and let the registry know if
        nobody is watching. The only place the ended flag is set."""
        self._finished.set()
        self._maybe_idle()

    # -- the human turn, where the game waits (POST /turns) --------------------------------

    def park(self, request: HumanTurnRequest, interrupt_id: str = "") -> None:
        """Hold one question for a human seat until /turns answers it, and start the
        seat's AFK clock. The question is kept so the answer can be checked against its
        rules; the empty Future is what the game task waits on. The interrupt id is what
        the engine wants the answer filed under; without one, the seat is used."""
        seat = request.player_id
        self.pending_requests[seat] = request
        self._pending_ids[seat] = interrupt_id or seat
        self._pending_answers[seat] = asyncio.get_running_loop().create_future()
        self.clocks.arm(request)  # a no-op for solo tables

    def submit_turn(self, body: dict, seat: str) -> None:
        """Take one seat's answer and validate it against the question that seat was
        asked (the same rules as the CLI game). Raises HumanTurnContractError on an
        illegal move, LookupError when the seat owes nothing."""
        if not self.pending_requests:
            raise LookupError("no pending input_request for this game")
        request = self.pending_requests.get(seat)
        if request is None:
            raise LookupError(f"no pending input_request for seat {seat!r}")
        response = validate_human_response(request, body)
        # Crosses the seat off so a duplicate response (second tab opened, restart lag)
        # raises LookupError. The answer is set right after: nothing between can fail.
        del self.pending_requests[seat]
        self._pending_answers[seat].set_result(response.model_dump())
        self.clocks.clear(seat)
        logger.info("game %s: turn accepted for %s (%d seat(s) still owe input)",
                    self.game_id, seat, len(self.pending_requests))

    async def _collect_answers(self) -> Any:
        """Wait until every seat that was asked has answered, then return the answers in
        the shape the engine resumes with. Seats that answered early cost nothing to
        wait on; the last one to answer is what wakes this.

        The engine wants a single answer as a bare value, and several answers as a
        dict keyed by the interrupt id it gave each question, so it knows which answer
        belongs to which seat."""
        await asyncio.gather(*self._pending_answers.values())
        self.parked_since = None
        answers = {self._pending_ids.pop(seat): fut.result()
                   for seat, fut in self._pending_answers.items()}
        self._pending_answers = {}
        if len(answers) == 1:
            return next(iter(answers.values()))
        return answers

    @property
    def turn_deadlines(self) -> dict[str, str]:
        """Effective deadline per parked seat (ISO), served in status and stamped on
        input_request — the client's countdown source."""
        return self.clocks.deadlines

    # -- after a restart: rebuilt by the live registry -------------------------------------

    def reload_history(self, log: list[ev.DurableEvent], human_players: list[str]) -> None:
        """Put back what the database holds for a game that had already started: the
        events the players were sent, and which seats are human. The live registry reads
        both from the events table and the game row and passes them in. Both count as
        already saved, so the next save writes only what comes after."""
        self.log = list(log)
        self.translator.hydrate(self.log)
        self.human_players = list(human_players)
        self.game_over = any(e.type == "game_over" for e in self.log)
        self._saved_event_count = len(self.log)
        self._saved_humans = list(self.human_players)

    def take_key(self, api_key: str) -> None:
        """Take a player's key for the model this game runs on. Only meaningful while
        awaiting a key; the registry validates the key with the provider first."""
        row = SUPPORTED_GAME_MODELS.get(self.model)
        self._api_key = api_key
        self._llm_selection = GameLLM(
            api_key=api_key, model=self.model, rescue_model=row.rescue_model if row else None)
        self.awaiting_key = False

    def resume_game(self, *, waiting_on_humans: bool) -> None:
        """Start the task for a game rebuilt after a restart. The engine continues from
        its last checkpoint, re-running the step that was cut off.

        ``waiting_on_humans`` means the game was paused on a human's turn when the
        process died. The live registry has already parked those questions again, so the
        task waits for the answers first and only then resumes the engine."""
        self._task = asyncio.get_running_loop().create_task(
            self._run(None, waiting_on_humans=waiting_on_humans),
            name=f"game-{self.game_id}")
        logger.info("game %s: recovered (waiting_on_humans=%s, %d events rehydrated)",
                    self.game_id, waiting_on_humans, len(self.log))

    @property
    def model(self) -> str:
        """The model this game runs on; empty when the server default is in charge."""
        return self._llm_selection.model if self._llm_selection else ""

    # -- the streams' lifecycle: human player's presence -----------------------------------

    @property
    def connected_seats(self) -> set[str]:
        """Human seats with at least one open stream RIGHT NOW. Spectators resolve to
        "" and never count; a snapshot, not a history of the window."""
        return {seat for token in self._subscribers.values()
                if (seat := self.seat_of_viewer(token))}

    def seat_present(self, seat: str) -> bool:
        return seat in self.connected_seats

    @property
    def humans_present(self) -> bool:
        return bool(self.connected_seats)

    # -- the streams' lifecycle: open, deliver, close; _maybe_idle is where the two meet ---

    def subscribe(self, token: str = "") -> asyncio.Queue:
        """Open a stream: make its queue and file it with the connection's seat token,
        "" for a spectator. A human seat connecting is the presence signal that lifts
        a grace or un-parks the table."""
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers[q] = token
        seat = self.seat_of_viewer(token)
        if seat:
            self.clocks.on_seat_returned(seat)
        return q

    def _deliver(self, event: ev.DurableEvent) -> None:
        self._tracker.on_event(event)
        for q in self._subscribers:
            q.put_nowait(("game", event))

    def publish_pacing(self, snapshot: ev.PhaseProgress) -> None:
        for q in self._subscribers:
            q.put_nowait(("pacing", snapshot))

    def unsubscribe(self, q: asyncio.Queue) -> None:
        """A stream closed. If that was the seat's last stream mid-question, its clock
        drops to the absence grace — the tab may be retrying, or may be gone."""
        seat = self.seat_of_viewer(self._subscribers.pop(q, ""))
        if seat and not self.seat_present(seat):
            self.clocks.on_seat_left(seat)
        self._maybe_idle()

    @property
    def watched(self) -> bool:
        """Whether any stream, seat or spectator, is open on this game right now."""
        return bool(self._subscribers)

    def _maybe_idle(self) -> None:
        """Fire on_idle exactly once: the first moment the game is ended and unwatched."""
        if self.ended and not self.watched and self.on_idle is not None:
            hook, self.on_idle = self.on_idle, None
            hook()

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

    def seat_of_viewer(self, token: str) -> str:
        """The seat behind one connection: its token's seat, or "" when there is no token
        (a spectator), the token is unknown, or the seats are not dealt yet."""
        return (self.seat_for_token(token) or "") if token else ""

    def owns(self, token: str) -> bool:
        """Whether this token belongs to one of the game's human seats. The same
        question GameLobby.owns answers, so status and rejoin serve both stages alike."""
        return token in self._seat_tokens

    # -- census exposure (GET /games/{id}) -------------------------------------------------

    @property
    def public_alive_counts(self) -> dict[str, int]:
        started = next((e for e in self.log if e.type == "game_started"), None)
        if started is None:
            return {}
        dead = [d for n in self.log if n.type == "night_result" for d in n.deaths]
        dead += [e for e in self.log if e.type == "lynch_result" and e.role]
        return alive_role_counts(started.cast_role_counts, dead)
