"""Turn the chunks a running game streams out into the events the browser receives.

The engine is a LangGraph graph. As it runs it streams one chunk each time a node finishes,
holding every state field that node wrote, in the engine's own shapes; nothing arrives
mid-node, though a chunk can arrive before its step is final (the votes, below). The
Translator, one per game, reduces each chunk to its JSON shape, turns it into zero or more
of the typed events in server.schemas.events, and stamps each with the game's running
``seq``. It reads nothing else and emits nothing else. Who may see an event
is decided at delivery, and the progress bars are built in game/pacing.py.

Every graph node has one entry below, in the order the nodes run in a game, listing the
state fields it writes. A node with a handler turns its delta into events; a node without
one writes nothing the browser needs. If the engine adds a node, or a field on a node,
that has no entry here, the first chunk carrying it raises TranslationError naming it,
so a new state field forces a decision: send it to the browser, or list it as
server-only. The root wrapper nodes (DAY_PHASE and the five night phases) are listed
without a handler: their delta repeats what their subgraph already streamed.

The translator keeps a small copy of game state, rebuilt from the chunks alone, and never
asks the graph for it: the stream runs ahead of the checkpoint, and behind a slow viewer
the graph would answer from steps the viewer has not been shown. Three things arrive on the
stream more than once, and each is handled at its guard: a re-streamed committed step
(tagged cached, no new events; its ballots still refill recovery buffers), an interrupt
(streamed under the subgraph and again at the root; only the root copy is sent), and the
two votes (parallel steps which re-run when a human answers; buffered until the tally,
last write per voter wins).

The lynch is computed here with the engine's own tally and compared with what the node
recorded; a mismatch raises rather than sending a wrong event. The night is not recomputed:
the resolution node commits the night report it produced, and that is what is sent.
The day summary is sent twice from its node: the flattened text the agents read, and the
summarizer's structured answer (accusations, claims, blocs, dynamics) for the observer
tier, skipped only when the summarizer failed and the raw channel was stored instead.

The node-by-node table of what is sent, and to whom, is frontend/docs/event_derivation.md,
titled with the same node names as the registry below. The exact output on a recorded game
is pinned by the goldens in tests/fixtures; when the two disagree, the goldens are right.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any

from pydantic_core import to_jsonable_python

from Agents.rules.resolution import tally_day_vote
from Agents.schemas.roles import ROLE_SPECS, roles as POOL
from server.schemas import events as ev


class TranslationError(RuntimeError):
    """A stream chunk the wire contract does not account for. Fail loudly, never skip."""


def get_source_graph(chunk: Mapping[str, Any]) -> str:
    """The graph a chunk came from: a phase subgraph's name (``DAY_PHASE``,
    ``WOLF_NIGHT_PHASE``, ...) or ``root`` for the parent graph. Read from the chunk's
    namespace, which lists the path down to the subgraph as ``NODE:task-id`` entries."""
    ns = chunk.get("ns") or ()
    return ns[0].split(":")[0] if ns else "root"


def is_cached(chunk: Mapping[str, Any]) -> bool:
    """True for a chunk the engine is re-emitting from its cache rather than producing,
    tagged ``__metadata__: {cached: True}``. Its events and pacing ticks already went out."""
    data = chunk.get("data")
    if not isinstance(data, Mapping):
        return False
    return bool((data.get("__metadata__") or {}).get("cached"))


# --- the node registry --------------------------------------------------------------------

Handler = Callable[["Translator", Mapping[str, Any]], list[ev.DurableEvent]]

# node name (lower-cased) -> (handler or None, the state fields the node may write;
# None = unchecked)
_NODES: dict[str, tuple[Handler | None, frozenset[str] | None]] = {}


def _register(name: str, writes: Iterable[str] | None, handler: Handler | None) -> None:
    key = name.lower()
    if key in _NODES:
        raise RuntimeError(f"node {name!r} registered twice")
    _NODES[key] = (handler, None if writes is None else frozenset(writes))


def node(name: str, *, writes: Iterable[str] | None = ()):
    """Register the decorated method as the handler for graph node ``name``. ``writes`` is
    every state field the node may commit, translated or not."""
    def register(handler: Handler) -> Handler:
        _register(name, writes, handler)
        return handler
    return register


def silent_node(name: str, *, writes: Iterable[str] | None = ()) -> None:
    """Register a graph node that produces no events. Its writes are still checked."""
    _register(name, writes, None)


# Human-turn `phase` -> wire action_kind (the channel-named turns get UX names; a night turn's
# phase is its role's field, Agents/schemas/roles.py).
_ACTION_KINDS = {
    "day_channel": "discuss",
    "day_votes": "vote",
    "wolf_channel": "wolf_discuss",
    "wolf_vote": "wolf_vote",
    "kill_target": "carrier_kill",
    **{spec.target_field: spec.target_field for spec in ROLE_SPECS.values() if spec.target_field},
}

# The parent state's survivor buckets, re-committed by the resolution nodes.
_SURVIVORS = {"surviving_wolves", "surviving_villagers"}
# What the night leaves in parent state beside the records: the night report the wire reads,
# and the roles' running counts.
_NIGHT_BOOKKEEPING = {"night_report", "uses_left", "speculator_pick", "fortune_points"}
# Keys the engine no longer writes but recorded games still carry: accepted and ignored on a
# replay, never a live field. last_body: the necromancer's previous body, retired 2026-10-09
# when the same body became usable night after night.
_RETIRED_KEYS = {"last_body"}
_PACK_ROLES = tuple(name for name, spec in ROLE_SPECS.items() if spec.pack)


def _is_pack(role: str | None) -> bool:
    return role in _PACK_ROLES


def _first_time(seen: set, key) -> bool:
    """Record ``key`` and say whether it was new. The send-once guard."""
    if key in seen:
        return False
    seen.add(key)
    return True


class Translator:
    """One game's translator. Feed every stream chunk to translate(); it returns the events.

    Attributes, by job. Every one is set in __init__; this is the only place they are
    explained.

    Wire bookkeeping the engine has no reason to keep.
      seq           the last seq handed out. Every event gets the next number.

    Copies of engine state, captured from the chunks because a single chunk does not carry
    them.
      current_day   bumped at ONE_MORE_DAY; the day stamped on events that carry none.
      roles         seat -> role, from INITIALIZE_GAME. Names the holder of a night role.
      wolves        the wolves still alive, kept current by the roster updates.

    Vote buffers, held until the tally node commits. Keyed by voter and last write wins, so
    a ballot re-run after a human interrupt replaces the aborted one.
      _day_ballots       voter -> votee for the day vote in progress.
      _last_day_ballots  the ballots just flushed, kept until DAY_RESOLUTION recomputes
                         the lynch from them.

    Send-once guards for the kinds that are sent as they arrive.
      _seen_day_entries  (day, channel seq) of every speech or pass already sent.
      _seen_wolf_msgs    (day, round, wolf) of every wolf-chat line already sent.
      _strategies        the last note sent per player; a note is sent only when it
                         changes.
    """

    def __init__(self) -> None:
        # Wire bookkeeping.
        self.seq = 0
        # Copies of engine state.
        self.current_day = 1
        self.roles: dict[str, str] = {}
        self.wolves: list[str] = []
        self._villagers: list[str] | None = None  # the non-wolves alive, once a roster update came
        # Vote buffers.
        self._day_ballots: dict[str, str] = {}
        self._last_day_ballots: list[tuple[str, str]] = []
        # Ship-once guards.
        self._seen_day_entries: set[tuple[int, int]] = set()
        self._seen_wolf_msgs: set[tuple[int, int, str]] = set()
        self._seen_memory: set[tuple[str, int, int, str]] = set()
        # Human turns announced ahead of their interrupt, (player, day, phase): the
        # interrupt that follows sends no second input_request.
        self._announced: set[tuple[str, int, str]] = set()
        self._deadlines: Mapping[str, str] = {}  # the session's, for an announced prompt
        self._seen_reads: set[tuple[str, int, int, str]] = set()
        self._memory_extracted_sent = False
        self._strategies: dict[str, str] = {}

    def hydrate(self, log: list) -> None:
        """Rebuild the shadow state from a durable event log (server-restart recovery).

        What rebuilds vs what deliberately stays empty:
        - seq counter, current_day, roles/wolves, send-once guards (day entries, wolf
          lines, memory consultations), strategy notes:
          all derivable from sent events — REBUILT (without the guards, the resume's
          abort-and-re-execute re-run would re-send every already-delivered message
          under fresh seqs).
        - the day's ballots: REBUILT from today's vote_cast events. The vote may already
          be committed while the resolution that needs them has not run yet. The night
          needs nothing: the resolution node commits the night report the wire reads.
        - in-flight ballot buffers: not public until collection, so absent from the
          log. The resumed vote step refills them, including from cached chunks;
          cached ballots produce no duplicate events.
        """
        dead: set[str] = set()
        for e in log:
            self.seq = max(self.seq, e.seq)
            self.current_day = max(self.current_day, e.day)
            if e.type == "phase_change":
                if e.phase in ("day", "voting"):
                    self._last_day_ballots.clear()
            if e.type == "roles_assigned":
                self.roles = dict(e.roles)
                self.wolves = [p for p, r in self.roles.items() if _is_pack(r)]
            elif e.type in ("speech", "pass_marker"):
                self._seen_day_entries.add((e.day, e.channel_seq))
            elif e.type == "wolf_message":
                self._seen_wolf_msgs.add((e.day, e.round, e.wolf))
            elif e.type == "strategy_update":
                self._strategies[e.player] = e.strategy
            elif e.type == "memory_consulted":
                self._seen_memory.add((e.player, e.day, e.round, e.action_phase))
            elif e.type == "player_reads":
                self._seen_reads.add((e.player, e.day, e.round, e.action_phase))
            elif e.type == "memory_extracted":
                self._memory_extracted_sent = True
            elif e.type == "vote_cast":
                self._last_day_ballots.append((e.voter, e.votee))
            elif e.type == "night_result":
                dead.update(d.player for d in e.deaths)
            elif e.type == "lynch_result" and e.player:
                dead.add(e.player)
        # wolves tracks SURVIVING wolves live (the chunks update it); replay the deaths.
        self.wolves = [w for w in self.wolves if w not in dead]
        if self.roles:
            self._villagers = [p for p, r in self.roles.items() if not _is_pack(r) and p not in dead]

    # ---- entry point ------------------------------------------------------------------

    def translate(self, chunk: Mapping[str, Any], *,
                  deadlines: Mapping[str, str] | None = None) -> list[ev.DurableEvent]:
        """Turn one stream chunk, live or saved, into its wire events. ``deadlines`` is
        the session's seat -> countdown map, so a turn prompt is born with its deadline;
        replays and solo tables pass nothing and the field stays None."""
        # A live chunk carries engine objects (Pydantic models, LangGraph's Interrupt,
        # enums); the fixture carries their JSON. The handlers read the JSON shape.
        chunk = to_jsonable_python(chunk)
        if chunk["type"] == "custom":
            self._deadlines = deadlines or {}
            return self._turn_tick(chunk["data"])
        if chunk["type"] != "updates":
            raise TranslationError(f"unexpected stream chunk type: {chunk['type']}")
        if is_cached(chunk):
            self.restore_cached_inputs(chunk)
            return []  # bookkeeping only: this step's events have already been sent

        graph = get_source_graph(chunk)
        out: list[ev.DurableEvent] = []
        for name, delta in chunk["data"].items():
            if name == "__interrupt__":
                # Every interrupt streams twice (subgraph namespace, then the root
                # mirror). Only the root copy is sent, or each input_request would go
                # out twice under two seqs.
                if graph == "root":
                    out.extend(self._input_requests(delta, deadlines or {}))
            elif name.startswith("__"):
                continue  # engine metadata, never a node
            else:
                out.extend(self._dispatch(name, delta or {}))
        return out

    def restore_cached_inputs(self, chunk: Mapping[str, Any]) -> None:
        """Refill an interrupted vote's buffers from cached results, without emitting.

        AI siblings can have finished before a human interrupted the step. After a
        restart their votes are absent from the log (the tally has not published them),
        but LangGraph re-streams their cached results. Keep those ballots so collection
        includes every voter. Last write wins, just as for a newly produced ballot.
        """
        for name, delta in chunk["data"].items():
            if name.lower() in ("vote", "vote_human"):
                self._buffer_day_votes(delta or {})

    def _dispatch(self, name: str, delta: Mapping[str, Any]) -> list[ev.DurableEvent]:
        try:
            handler, writes = _NODES[name.lower()]
        except KeyError:
            raise TranslationError(f"unregistered graph node {name!r}") from None
        unexpected = set(delta) - writes if writes is not None else set()
        if unexpected:
            raise TranslationError(
                f"{name} committed unexpected keys {sorted(unexpected)}: add an event or "
                "register the key as a write (frontend/docs/event_derivation.md)")
        return handler(self, delta) if handler else []

    # ---- helpers ----------------------------------------------------------------------

    def _emit(self, cls, *, day: int | None = None, **fields) -> ev.DurableEvent:
        self.seq += 1
        return cls(seq=self.seq, day=self.current_day if day is None else day, **fields)

    def _role_holder(self, role: str) -> str | None:
        return next((p for p, r in self.roles.items() if r == role), None)

    def _non_wolves_alive(self) -> list[str]:
        """The non-wolves still alive: the last roster update's, or everyone at the start."""
        if self._villagers is not None:
            return list(self._villagers)
        return [p for p, r in self.roles.items() if not _is_pack(r)]

    def _turn_tick(self, payload: Mapping[str, Any]) -> list[ev.DurableEvent]:
        # The custom chunks. "X is thinking" is written from a routing edge, so a re-run
        # node cannot fire it twice. The others are written from inside their nodes and
        # CAN fire again on a re-run: sent once, like a re-run speech.
        if payload.get("event") == "turn_started":
            return [self._emit(ev.TurnStarted, day=payload["day"], player=payload["player"])]
        if payload.get("event") == "human_turn_opened":
            # A human's vote or night action, announced before its parallel step ends so
            # the prompt opens at once (announce_human_turn). Same event as the interrupt
            # would send; the interrupt then sends none. A router runs again on a resume,
            # so the key dedupes that too.
            key = (payload["player"], payload["day"], payload["phase"])
            if not _first_time(self._announced, key):
                return []
            return [self._input_request(payload["player"], payload["day"], payload["phase"],
                                        payload["valid_targets"], self._deadlines,
                                        day_round=payload.get("day_round"),
                                        bodies=payload.get("bodies"))]
        if payload.get("event") == "player_reads":
            key = (payload["player"], payload["day"], payload["round"], payload["action_phase"])
            if not _first_time(self._seen_reads, key):
                return []
            fields = {k: payload[k] for k in ("player", "role", "round", "action_phase", "reads")}
            return [self._emit(ev.PlayerReads, day=payload["day"], **fields)]
        if payload.get("event") == "memory_consulted":
            key = (payload["player"], payload["day"], payload["round"], payload["action_phase"])
            if not _first_time(self._seen_memory, key):
                return []
            fields = {k: payload[k] for k in ("player", "role", "round", "action_phase",
                                               "lessons", "verdicts", "observations",
                                               "applicability")}
            return [self._emit(ev.MemoryConsulted, day=payload["day"], **fields)]
        if payload.get("event") == "memory_extracted":
            if self._memory_extracted_sent:
                return []
            self._memory_extracted_sent = True
            return [self._emit(ev.MemoryExtracted, day=payload["day"],
                               observations=payload["observations"],
                               strategy_points=payload["strategy_points"])]
        raise TranslationError(f"unknown custom payload: {payload!r}")

    def _input_requests(self, interrupts, deadlines: Mapping[str, str]) -> list[ev.DurableEvent]:
        out = []
        for item in interrupts:
            req = item["value"]
            key = (req["player_id"], req["day"], req["phase"])
            if key in self._announced:
                self._announced.discard(key)  # the prompt went out when the step began
                continue
            out.append(self._input_request(req["player_id"], req["day"], req["phase"],
                                           req.get("valid_targets") or [], deadlines,
                                           day_round=req.get("day_round"),
                                           bodies=req.get("bodies")))
        return out

    def _input_request(self, player: str, day: int, phase: str, candidates,
                       deadlines: Mapping[str, str], *,
                       day_round: str | None = None, bodies=None) -> ev.DurableEvent:
        kind = _ACTION_KINDS.get(phase)
        if kind is None:
            raise TranslationError(f"unknown human-turn phase: {phase!r}")
        # Only a discussion turn belongs to a round; the engine sends None for the rest, and a
        # record from before the rounds has no field at all.
        if kind != "discuss":
            day_round = None
        return self._emit(ev.InputRequest, day=day, player=player, action_kind=kind,
                          candidates=list(candidates), bodies=list(bodies or []),
                          round=day_round, deadline=deadlines.get(player))

    def _gm_messages(self, delta):
        return [self._emit(ev.GmMessage, day=e["day"], channel_seq=e["seq"], text=e["message"])
                for e in delta.get("day_channel") or [] if e["player"] == "game_master"]

    def _strategy_updates(self, delta):
        # A strategy note is an overwrite, so a re-delivered identical note sends nothing.
        strategies = delta.get("agent_strategies") or {}
        out = [self._emit(ev.StrategyUpdate, player=player, strategy=text)
               for player, text in strategies.items()
               if self._strategies.get(player) != text]
        self._strategies.update(strategies)
        return out

    def _roster_updates(self, delta):
        wolves = delta.get("surviving_wolves")
        villagers = delta.get("surviving_villagers")
        if wolves is None and villagers is None:
            return []  # no death: rosters unchanged, no event
        if wolves is None or villagers is None:
            raise TranslationError(
                "resolution committed only one survivor bucket; the engine always commits "
                "both together, refusing to send a partial roster")
        self.wolves = list(wolves)
        self._villagers = list(villagers)
        # The public roster is the union; the split by faction stays off the public tier.
        return [
            self._emit(ev.RosterUpdate, surviving_players=sorted([*villagers, *wolves])),
            self._emit(ev.PackRosterUpdate, surviving_wolves=list(wolves)),
        ]

    # ---- lifecycle --------------------------------------------------------------------

    @node("INITIALIZE_GAME", writes={
        "roles", "lineup", "current_day", "human_players", "winner", "neutral_result",
        "day_channel", "day_summaries", "wolf_channel", "day_votes", "night_actions",
        "night_choices", "no_lynch_streak", *_NIGHT_BOOKKEEPING, *_RETIRED_KEYS, *_SURVIVORS,
    })
    def _initialize_game(self, delta):
        self.roles = dict(delta.get("roles") or {})
        self.wolves = [p for p, r in self.roles.items() if _is_pack(r)]
        self.current_day = delta.get("current_day", 1)
        uses = dict(delta.get("uses_left") or {})
        cast_counts: dict[str, int] = {}
        for role in self.roles.values():
            cast_counts[role] = cast_counts.get(role, 0) + 1

        out = [self._emit(ev.GameStarted, seats=list(self.roles), cast_role_counts=cast_counts,
                          lineup=list(delta.get("lineup") or []))]
        for player, role in self.roles.items():
            out.append(self._emit(
                ev.RoleAssigned, player=player, role=role,
                pack=list(self.wolves) if _is_pack(role) else None,
                bullets=uses.get("vigilante") if role == "vigilante" else None,
                uses=uses.get(role),
            ))
        out.append(self._emit(ev.RolesAssigned, roles=dict(self.roles)))
        out.append(self._emit(ev.PhaseChange, phase="day"))
        return out

    # ---- day --------------------------------------------------------------------------

    silent_node("SCHEDULE")

    @node("discuss", writes={"day_channel", "agent_strategies"})
    def _discuss(self, delta):
        out = []
        for entry in delta.get("day_channel") or []:
            day, cseq, player = entry["day"], entry["seq"], entry["player"]
            if not _first_time(self._seen_day_entries, (day, cseq)):
                continue  # already sent (a re-run or a restart replay)
            if entry.get("passed"):
                out.append(self._emit(
                    ev.PassMarker, day=day, channel_seq=cseq, player=player,
                    pass_reason=entry.get("pass_reason"),
                    gated=bool(entry.get("gated")),
                    gated_candidate=entry.get("gated_candidate") or None,
                ))
            else:
                out.append(self._emit(ev.Speech, day=day, channel_seq=cseq,
                                      player=player, message=entry["message"],
                                      claim=entry.get("claim") or "none"))
            firing = entry.get("firing_reason")
            if firing is not None:
                out.append(self._emit(
                    ev.FiringReasonAnnotation, day=day, about_channel_seq=cseq, player=player,
                    tier=firing["tier"], owes=list(firing.get("owes") or []),
                ))
            targets = entry.get("addressed_targets") or []
            if targets:
                out.append(self._emit(
                    ev.AddressedTargetsAnnotation, day=day, about_channel_seq=cseq,
                    player=player,
                    targets=[ev.WireAddressedTarget(
                        target=t["target"], addressed_form=t["addressed_form"],
                        stance=t["stance"]) for t in targets],
                ))
        out.extend(self._strategy_updates(delta))
        return out

    # ---- the rounds (Phase 2): the opening and the closing -------------------------------
    # A round's turns run at once and hold their lines in round_candidates; COLLECT_ROUND
    # numbers them into day_channel, so the lines are sent from there, through the same loop
    # as a discussion turn. The entry node sets which round runs and lists its players, which
    # is the round_opened event; START_CLOSING also writes the moderator's announcement. The
    # scheduler's sweep turns are ordinary ``discuss`` turns (firing_reason proactive).

    def _round_opened(self, which: str, delta):
        return [self._emit(ev.RoundOpened, round=which,
                           players=list(delta.get("round_players") or []))]

    @node("START_OPENING", writes={"day_round", "round_players"})
    def _start_opening(self, delta):
        return self._round_opened("opening", delta)

    @node("START_CLOSING", writes={"day_round", "day_channel", "round_players"})
    def _start_closing(self, delta):
        out = self._gm_messages(delta)
        out.extend(self._round_opened("closing", delta))
        return out

    @node("round_turn", writes={"round_candidates", "agent_strategies"})
    def _round_turn(self, delta):
        return self._strategy_updates(delta)

    # The human seat's round turn goes through the uncached twin: same delta, same handling.
    node("round_turn_human", writes={"round_candidates", "agent_strategies"})(_round_turn)

    @node("COLLECT_ROUND", writes={"day_channel"})
    def _collect_round(self, delta):
        return self._discuss(delta)

    @node("SUMMARIZE_DAY_DISCUSSION", writes={"day_summaries"})
    def _summarize_day_discussion(self, delta):
        # The summarizer stores its typed answer next to the flattened text the agents
        # read. The structured copy is empty when the summarizer failed and the raw
        # channel was stored instead, and then only the text is sent.
        out = []
        for s in delta.get("day_summaries") or []:
            out.append(self._emit(ev.DaySummary, day=s["day"], summary=s["summary"]))
            if s.get("structured"):
                out.append(self._emit(
                    ev.DaySummaryStructured, day=s["day"], data=s["structured"]))
        return out

    @node("START_VOTING")
    def _start_voting(self, delta):
        return [self._emit(ev.PhaseChange, phase="voting")]

    @node("vote", writes={"day_votes", "agent_strategies"})
    def _vote(self, delta):
        self._buffer_day_votes(delta)
        return self._strategy_updates(delta)

    def _buffer_day_votes(self, delta):
        for ballot in delta.get("day_votes") or []:
            # Last write wins: a human interrupt re-runs this step, and the engine keeps
            # the re-run's ballot, which may differ from the one streamed before.
            self._day_ballots[ballot["voter"]] = ballot["votee"]

    # The human seat votes through the uncached twin node: same delta, same handling.
    node("vote_human", writes={"day_votes", "agent_strategies"})(_vote)

    @node("COLLECT_VOTES")
    def _collect_votes(self, delta):
        # Content from the buffer, timing from node identity (its own delta is empty).
        out = [self._emit(ev.VoteCast, voter=voter, votee=votee)
               for voter, votee in self._day_ballots.items()]
        self._last_day_ballots = list(self._day_ballots.items())
        self._day_ballots.clear()
        return out

    # The root wrapper's commit: the day subgraph's result, already translated above.
    silent_node("DAY_PHASE", writes={
        "day_channel", "day_summaries", "day_votes", "agent_strategies"})

    @node("DAY_RESOLUTION", writes={
        "day_channel", "dead_roster", "voted_player", "no_lynch_streak", "day_summaries",
        *_SURVIVORS,
    })
    def _day_resolution(self, delta):
        out = self._gm_messages(delta)
        tally = tally_day_vote(votee for _, votee in self._last_day_ballots)
        voted = delta.get("voted_player")
        if tally.lynched != voted:
            raise TranslationError(
                f"kernel/delta mismatch: tally lynched {tally.lynched!r} but the node "
                f"committed voted_player={voted!r}; inputs drifted, refusing to send")
        # dead_roster: the lynch death record rides inside lynch_result (player + role).
        out.append(self._emit(
            ev.LynchResult, outcome=tally.outcome, player=voted,
            role=self.roles.get(voted) if voted else None,
            vote_counts=tally.vote_counts,
            no_lynch_streak=delta.get("no_lynch_streak", 0),
        ))
        out.extend(self._roster_updates(delta))
        return out

    @node("NIGHT_START")
    def _night_start(self, delta):
        # NIGHT_START runs only when the day did not end the game, so emitting here can
        # never announce a night after a game-ending day.
        return [self._emit(ev.PhaseChange, phase="night")]

    # ---- night ------------------------------------------------------------------------

    silent_node("PREPARE_PACK_NIGHT", writes={"current_round"})

    @node("PACK_CHAT", writes={"wolf_channel", "agent_strategies"})
    def _pack_chat(self, delta):
        out = []
        for entry in delta.get("wolf_channel") or []:
            if entry.get("pass_reason") == "generation_failed":
                continue  # technical pass: hidden from the pack, no wire event
            day, round_, wolf = entry["day"], entry["round"], entry["wolf"]
            if not _first_time(self._seen_wolf_msgs, (day, round_, wolf)):
                continue  # already sent (a re-run or a restart replay)
            out.append(self._emit(ev.WolfMessage, day=day, round=round_, wolf=wolf,
                                  message=entry["message"], passed=bool(entry.get("passed"))))
        out.extend(self._strategy_updates(delta))
        return out

    silent_node("START_CARRIER")

    def _night_choices(self, delta):
        """The choices a night node committed, as night_action events (observer tier)."""
        out = []
        for choice in delta.get("night_choices") or []:
            out.append(self._emit(ev.NightAction, actor=choice["actor"], role=choice["role"],
                                  target=choice.get("target") or ""))
        return out

    @node("CARRIER_KILL", writes={"wolf_channel", "night_choices", "wolves_target", "agent_strategies"})
    def _carrier_kill(self, delta):
        out = []
        target = delta.get("wolves_target")
        carrier = next((c["actor"] for c in delta.get("night_choices") or []), None)
        if target:
            out.append(self._emit(ev.WolfKillDecided, target=target, carrier=carrier))
        out.extend(self._night_choices(delta))
        out.extend(self._strategy_updates(delta))
        return out

    # A human carrier goes through the uncached twin node: same delta, same handling.
    node("CARRIER_KILL_HUMAN", writes={"wolf_channel", "night_choices", "wolves_target", "agent_strategies"})(_carrier_kill)

    @node("PACK_SKILL", writes={"night_choices", "agent_strategies"})
    def _pack_skill(self, delta):
        return [*self._night_choices(delta), *self._strategy_updates(delta)]

    node("PACK_SKILL_HUMAN", writes={"night_choices", "agent_strategies"})(_pack_skill)
    silent_node("COLLECT_PACK")

    # The root wrapper's commit: the pack's result, already translated above.
    silent_node("PACK_NIGHT_PHASE", writes={"wolf_channel", "night_choices", "agent_strategies"})

    # One named node per solo night role: its choice and its strategy note.
    for _role in POOL:
        if ROLE_SPECS[_role].night_action and not ROLE_SPECS[_role].pack:
            node(f"{_role.upper()}_NIGHT_PHASE", writes={"night_choices", "agent_strategies"})(
                lambda self, delta: [*self._night_choices(delta), *self._strategy_updates(delta)])
    del _role

    @node("NIGHT_RESOLUTION", writes={
        "day_channel", "dead_roster", "day_summaries",
        # The private night record: engine input for later turns, and each seat's own
        # night_record event below.
        "night_actions",
        *_NIGHT_BOOKKEEPING, *_RETIRED_KEYS, *_SURVIVORS,
    })
    def _night_resolution(self, delta):
        out = self._gm_messages(delta)

        # The night's public outcome, as the node committed it (the authoritative report).
        report = delta.get("night_report") or {}
        deaths = [ev.NightDeath(player=p, role=role, attacker_types=types, concealed=not role)
                  for p, role, types in report.get("deaths") or []]
        saves = [ev.NightSave(player=p, attacker_types=types) for p, types in report.get("saves") or []]
        out.append(self._emit(ev.NightResult, deaths=deaths, save=saves[0] if saves else None,
                              saves=saves, pick=report.get("pick")))

        # Seat events: each actor's own record (the pack's kill to every wolf still alive at
        # dawn), and what each limited ability has left, to a living holder. The delta carries
        # the survivor buckets only when someone died; otherwise the shadow copies stand.
        wolves_alive = delta.get("surviving_wolves")
        if wolves_alive is None:
            wolves_alive = list(self.wolves)
        alive = set(wolves_alive) | set(delta.get("surviving_villagers") or self._non_wolves_alive())
        for record in delta.get("night_actions") or []:
            recipients = list(wolves_alive) if record["actor"] == "wolves" else [record["actor"]]
            for seat in recipients:
                out.append(self._emit(
                    ev.NightRecord, player=seat, actor=record["actor"], action=record["action"],
                    target=record.get("target"), result=record.get("result", ""),
                    outcome=record.get("outcome", ""), seen=list(record.get("seen") or []),
                ))
        for role, count in (delta.get("uses_left") or {}).items():
            holder = self._role_holder(role)
            if holder is not None and holder in alive:
                out.append(self._emit(ev.UsesRemaining, player=holder, role=role, count=count))

        out.extend(self._roster_updates(delta))
        return out

    @node("ONE_MORE_DAY", writes={
        "current_day", "day_votes", "voted_player", "night_choices", "night_report",
    })
    def _one_more_day(self, delta):
        self.current_day = delta.get("current_day", self.current_day + 1)
        self._day_ballots.clear()
        self._last_day_ballots.clear()
        return [self._emit(ev.PhaseChange, phase="day")]

    # ---- end --------------------------------------------------------------------------

    @node("END_GAME", writes={"day_channel", "winner", "neutral_result"})
    def _end_game(self, delta):
        out = self._gm_messages(delta)
        out.append(self._emit(ev.GameOver, winner=delta.get("winner"),
                              neutral_result=delta.get("neutral_result")))
        return out

    # Post-game memory work is not part of the game record; whatever it writes is ignored.
    silent_node("POST_GAME_ANALYSIS", writes=None)
