"""Per-game server runtime: run one game, turn its stream into events, deliver them to viewers.

One GameSession per running game. The game runs as a background asyncio task on the server's
event loop, consuming graph.astream(): between parts the task is just parked at its `async
for`, costing the loop nothing. The engine's nodes are synchronous, so LangGraph's async path
runs them in worker threads — their blocking LLM calls never stall the loop (verified on this
langgraph version: loop stays responsive through a blocking node; part semantics identical to
sync stream()). Our own code stays entirely on the loop: no hand-rolled threads, no bridge.

A player-supplied API key (BYOK) plus a model choice from SUPPORTED_GAME_MODELS (tested
models only, each with its same-credential rescue) rides a ContextVar set inside the
game's task: LangGraph copies the task context into its worker threads, so the factory
bills this game's key — applied only to the chosen model's provider — with no key ever
touching RunConfig, the event log, or disk; if the key dies mid-game the error surfaces
(redacted) and the player restarts with a valid one.

Every part goes through the Translator; the resulting events are appended to the game's
in-memory log and pushed to each connected viewer's queue. When the game needs the human's
action, the graph interrupts: the task awaits a queue. POST /turns validates the submitted
action (same rules as the CLI game) and puts it there, which resumes the graph.

Who may see an event is decided at delivery time, per viewer: `entitled()` checks the event's
tier (public / wolves-only / one seat / observer) against the viewer's seat. At game_over
everyone becomes an observer and the held-back events flush out (ruling R7 — game over flips
permissions; it doesn't carry a reveal payload of its own).

The PacingTracker drives the "3/5 players done" progress bars — computed from public
knowledge only, never from the real engine state, so the bar can't leak who acted (padded
20-30s completions make a non-actor indistinguishable from a slow one).
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Any, Callable, NamedTuple

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
from Agents.tracing import Metrics
from Agents.turn.human_turn import validate_human_response

from server.schemas import events as ev
from server.translate import Translator, _read_field

logger = logging.getLogger(__name__)


class GameModel(NamedTuple):
    """One registry row: the same-credential rescue model (None = no rescue; the typed
    technical-pass path still keeps the game moving) + the frontend menu label."""

    rescue: str | None
    label: str


# The BYOK support policy as code: only models that have carried real games are selectable
# (a model enters this registry by surviving live games, not by having a factory branch).
# First row = the default for a bare key. GET /models serves this as the selection menu.
SUPPORTED_GAME_MODELS: dict[str, GameModel] = {
    "gemini-3.1-flash-lite": GameModel("gemini-3.5-flash-lite",
                                       "Gemini 3.1 Flash-Lite (default)"),
    "gemini-3.5-flash-lite": GameModel("gemini-3.1-flash-lite", "Gemini 3.5 Flash-Lite"),
    "gemini-3.6-flash": GameModel("gemini-3.5-flash-lite", "Gemini 3.6 Flash"),
    "gemini-2.5-pro": GameModel("gemini-3.5-flash-lite", "Gemini 2.5 Pro"),
    # DeepSeek official endpoint (CLI games incl. the HITL driver ran on it). No second
    # DeepSeek model is game-tested, so no same-credential rescue exists.
    "deepseek/deepseek-v4-pro": GameModel(None, "DeepSeek V4 Pro"),
}

_SPECIAL_UNITS = ("healer", "investigator", "serial_killer", "vigilante")
_BRANCH_UNITS = {
    "WOLF_NIGHT_PHASE": "wolves",
    "HEALER_NIGHT_PHASE": "healer",
    "INVESTIGATOR_NIGHT_PHASE": "investigator",
    "SERIAL_KILLER_NIGHT_PHASE": "serial_killer",
    "VIGILANTE_NIGHT_PHASE": "vigilante",
}
_PAD_SECONDS = (20.0, 30.0)


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


class PacingTracker:
    """Ephemeral phase_progress snapshots from PUBLIC knowledge only.

    The two bars exist because night and the day vote deliberately withhold their events
    (secrecy tiers, blind voting) — a live viewer needs proof of motion without proof of
    content. Denominators come from the publicly-derivable alive-role census (fixed cast
    minus announced deaths), NEVER the real fan-out. Certain roles, such as vigilante, would
    not have a night phase if their bullets are used up. Showing the real counter would
    leak information to other roles, hence a pseudo role counter will represent them. 
    Night units all complete on a minimal padded 20-30s so that pseudo counters will not complete
    instantly, which is another role leak. 
    Runs entirely on the event loop."""

    def __init__(self, publish: Callable[[ev.PhaseProgress], None]) -> None:
        # The one capability the tracker gets: emit a snapshot (GameSession.publish_pacing).
        # A callback, not the session object — the signature IS the coupling contract.
        self._publish = publish
        # Game-lifetime facts.
        self._public_alive: dict[str, int] = {}  # role -> alive count the AUDIENCE can derive
        self._day = 1
        # Per-stage scratch: one bar's worth of state, wiped together by _reset_stage().
        self._stage: str | None = None  # "night" | "day_vote" | None = no bar showing
        self._stage_total = 0
        self._completed_units: set[str] = set()  # night numerator; a set so double marks no-op
        self._ballots = 0  # vote numerator; anonymous ticks, so a plain counter
        self._padding_timers: list[asyncio.TimerHandle] = []

    # -- public-event feed ----------------------------------------------------------------

    def on_event(self, event: ev.DurableEvent) -> None:
        if event.type == "game_started":
            self._public_alive = dict(event.cast_role_counts)
        elif event.type == "lynch_result" and event.role:
            self._public_alive[event.role] = max(0, self._public_alive.get(event.role, 0) - 1)
        elif event.type == "night_result":
            for death in event.deaths:
                self._public_alive[death.role] = max(0, self._public_alive.get(death.role, 0) - 1)
            self._finish_stage()  # dawn: force the night bar full, whatever the timers did
        elif event.type == "phase_change":
            self._day = event.day
            if event.phase == "night":
                self._start_night()
            elif event.phase == "voting":
                self._start_voting()
            else:
                self._reset_stage()
        elif event.type == "vote_cast":
            self._finish_stage()  # result announced: the vote bar is over

    # -- part-level ticks (via GameSession) -----------------------------------------------

    def on_branch_done(self, unit: str) -> None:
        self._complete_unit(unit)

    def on_ballot(self) -> None:
        if self._stage == "day_vote":
            self._ballots = min(self._ballots + 1, self._stage_total)
            self._publish_snapshot(self._ballots)

    # -- internals ------------------------------------------------------------------------

    def _start_night(self) -> None:
        self._reset_stage()
        units = [u for u in _SPECIAL_UNITS if self._public_alive.get(u, 0) > 0]
        if self._public_alive.get("wolf", 0) > 0:
            units.append("wolves")  # the pack is one unit: per-wolf ticks would size the pack
        self._stage, self._stage_total, self._completed_units = "night", len(units), set()
        self._publish_snapshot(0)
        # Padding timers do two jobs: complete units that never tick (zero-bullet
        # vigilante), and make a padded completion indistinguishable from a real slow one.
        loop = asyncio.get_running_loop()
        for unit in units:
            self._padding_timers.append(
                loop.call_later(random.uniform(*_PAD_SECONDS), self._complete_unit, unit)
            )

    def _start_voting(self) -> None:
        self._reset_stage()
        self._stage, self._stage_total, self._ballots = (
            "day_vote", sum(self._public_alive.values()), 0)
        self._publish_snapshot(0)

    def _complete_unit(self, unit: str) -> None:
        """Idempotent: the real branch tick and the padding timer both land here."""
        if self._stage != "night" or unit in self._completed_units:
            return
        self._completed_units.add(unit)
        self._publish_snapshot(len(self._completed_units))

    def _publish_snapshot(self, done: int) -> None:
        """Absolute done/total frames, never increments — a late joiner needs one full frame."""
        if self._stage is None or self._stage_total == 0:
            return
        self._publish(ev.PhaseProgress(
            day=self._day, stage=self._stage, done=done, total=self._stage_total
        ))

    def _finish_stage(self) -> None:
        """The stage's result went public: leave the bar complete, then reset."""
        if self._stage is not None:
            self._publish_snapshot(
                self._stage_total if self._stage == "night" else self._ballots)
        self._reset_stage()

    def _reset_stage(self) -> None:
        for timer in self._padding_timers:
            timer.cancel()  # a dawn that beats the timers must not leave callbacks pending
        self._padding_timers.clear()
        self._stage, self._stage_total, self._completed_units, self._ballots = None, 0, set(), 0


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
                   this list. In-memory only for now (durability is the parked M2).
      game_over    the permission flip (ruling R7): once True, entitled() treats
                   every viewer as an observer and the withheld backlog may flush.

    The human seat (HITL):
      human_player     which seat the ENGINE assigned the human (read from the
                       INITIALIZE_GAME part); served by GET /games so the client
                       knows whose seat to render.
      pending_request  the parked interrupt payload. The full prompt-bearing request
                       stays server-side; the wire carries only the slim
                       input_request event.
      _resume_q        the hand-off: POST /turns validates the action and puts it
                       here; the game task is parked awaiting it.

    Delivery + lifecycle:
      _subscribers  one queue per connected viewer; _deliver fans events into these.
      _tracker      the PacingTracker (public-knowledge progress bars).
      error         the death report: a game task that dies lands its exception here
                    (key-redacted) instead of vanishing; GET /games serves it.
      _finished     awaitable "ended or died" signal, set in _run's finally.
      _task         the game's asyncio task handle (created by start()).
    """

    def __init__(self, run_config: RunConfig | dict[str, Any], *,
                 api_key: str = "", model: str = "", graph=None) -> None:
        # BYOK billing (memory-only; model must come from SUPPORTED_GAME_MODELS).
        self._api_key = api_key
        if api_key and not model:
            model = next(iter(SUPPORTED_GAME_MODELS))  # a bare key runs the default model
        row = SUPPORTED_GAME_MODELS.get(model)
        self._llm_override = GameLLM(
            api_key=api_key, model=model,
            rescue_model=row.rescue if row else None,
        ) if api_key else None

        # Engine bootstrap (+ the memory-seeding side effect).
        run = normalize_run_config(run_config)
        seed_memory_from_config(run.memory_persistence, target_store=store)
        self.config = build_runnable_config(run)
        self.game_id: str = self.config["configurable"]["game_id"]
        self._graph = graph if graph is not None else parent_graph_compiled
        self._context = {"metrics": Metrics(), "eval_sink": EvalCaseSink()}

        # The wire: converter machine, durable record, R7 permission flip.
        self.translator = Translator()
        self.log: list[ev.DurableEvent] = []
        self.game_over = False

        # The human seat (HITL).
        self.human_player: str = ""
        self.pending_request: HumanTurnRequest | None = None
        self._resume_q: asyncio.Queue = asyncio.Queue()

        # Delivery + lifecycle.
        self._subscribers: set[asyncio.Queue] = set()
        self._tracker = PacingTracker(self.publish_pacing)
        self.error: str | None = None
        self._finished = asyncio.Event()
        self._task: asyncio.Task | None = None

    # -- lifecycle ------------------------------------------------------------------------

    def start(self) -> None:
        self._task = asyncio.get_running_loop().create_task(
            self._run(), name=f"game-{self.game_id}")
        logger.info("game %s: task started (byok=%s, model=%s)",
                    self.game_id, bool(self._api_key),
                    self._llm_override.model if self._llm_override else "server-default")

    async def shutdown(self) -> None:
        """Cancel the running game task (server shutdown). Cancellation lands at the
        task's next await; a sync node already inside LangGraph's executor runs its
        current step to completion in its worker thread — accepted, since the game's
        state is RAM-only anyway (durability is the parked M2)."""
        if self._task is not None and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            logger.info("game %s: cancelled on server shutdown", self.game_id)

    async def _run(self) -> None:
        if self._llm_override is not None:
            GAME_LLM.set(self._llm_override)
        # Fresh state initialization each game
        graph_input: Any = fresh_game_state()
        try:
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
                if not interrupted:
                    break
                # Resume with user input
                graph_input = Command(resume=await self._resume_q.get())
        except Exception as exc:  # surface, don't vanish: the session reports its death
            detail = repr(exc)
            if self._api_key:
                # Provider auth errors can echo the credential; viewers see error text.
                detail = detail.replace(self._api_key, "***")
            self.error = detail
            logger.error("game %s: task died: %s", self.game_id, detail)
        finally:
            self._finished.set()
            if self.error is None:
                logger.info("game %s: finished (game_over=%s, %d events)",
                            self.game_id, self.game_over, len(self.log))

    def _on_part(self, part) -> bool:
        """Translate, record, publish. Returns True on an interrupt part."""
        data = part.get("data") or {}
        events = self.translator.translate(part)
        for event in events:
            self.log.append(event)
            if event.type == "game_over":
                self.game_over = True
            self._deliver(event)

        # Pacing ticks ride part identity: a root wrapper part = that night branch finished;
        # a vote-node part = one ballot cast. (Both are otherwise ignored/buffered.)
        ns = part.get("ns") or ()
        scope = ns[0].split(":")[0] if ns else "root"
        for node in data:
            if scope == "root" and node in _BRANCH_UNITS:
                self._tracker.on_branch_done(_BRANCH_UNITS[node])
            if node == "vote" and scope == "DAY_PHASE":
                self._tracker.on_ballot()
            if node == "INITIALIZE_GAME":
                self.human_player = _read_field(data[node], "human_player", "") or ""

        if "__interrupt__" in data:
            value = _read_field(data["__interrupt__"][0], "value")
            self.pending_request = HumanTurnRequest.model_validate(value)
            return True
        return False

    # -- fan-out --------------------------------------------------------------------------

    def _deliver(self, event: ev.DurableEvent) -> None:
        self._tracker.on_event(event)
        for q in self._subscribers:
            q.put_nowait(("game", event))

    def publish_pacing(self, snapshot: ev.PhaseProgress) -> None:
        for q in self._subscribers:
            q.put_nowait(("pacing", snapshot))

    def subscribe(self) -> asyncio.Queue:
        q: asyncio.Queue = asyncio.Queue()
        self._subscribers.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue) -> None:
        self._subscribers.discard(q)

    async def wait_finished(self) -> None:
        await self._finished.wait()

    # -- the human turn (from POST /turns) ------------------------------------------------

    def submit_turn(self, body: dict) -> None:
        """Validate against the pending request (the CLI's HITL contract, reused) and
        resume the parked game task. Raises HumanTurnContractError on a bad action."""
        if self.pending_request is None:
            raise LookupError("no pending input_request for this game")
        response = validate_human_response(self.pending_request, body)
        self.pending_request = None
        self._resume_q.put_nowait(response.model_dump())
        logger.info("game %s: human turn accepted, resuming", self.game_id)

    # -- census exposure (GET /games/{id}) ------------------------------------------------

    def public_alive_counts(self) -> dict[str, int]:
        started = next((e for e in self.log if e.type == "game_started"), None)
        if started is None:
            return {}
        dead = [d for n in self.log if n.type == "night_result" for d in n.deaths]
        dead += [e for e in self.log if e.type == "lynch_result" and e.role]
        return alive_role_counts(started.cast_role_counts, dead)
