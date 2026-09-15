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
(tagged cached, dropped whole), an interrupt (streamed under the subgraph and again at the
root; only the root copy is sent), and the two votes (the game's only parallel steps, which
re-run when a human answers; they are buffered until the tally, last write per voter wins).

The lynch and the night deaths are computed here with the engine's own rule functions and
compared with what the node recorded; a mismatch raises rather than sending a wrong event.
Not yet emitted: day_summary_structured, whose structured form never reaches state.

The node-by-node table of what is sent, and to whom, is frontend/docs/event_derivation.md,
titled with the same node names as the registry below. The exact output on a recorded game
is pinned by the goldens in tests/fixtures; when the two disagree, the goldens are right.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping
from typing import Any

from pydantic_core import to_jsonable_python

from Agents.rules.resolution import collect_attacks, resolve_attacks, tally_day_vote
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


# Human-turn `phase` -> wire action_kind (the two channel-named turns get UX names).
_ACTION_KINDS = {
    "day_channel": "discuss",
    "day_votes": "vote",
    "wolf_channel": "wolf_discuss",
    "wolf_vote": "wolf_vote",
    "healer_target": "healer_target",
    "investigator_target": "investigator_target",
    "serial_killer_target": "serial_killer_target",
    "vigilante_target": "vigilante_target",
}

# The parent state's night-role bookkeeping, re-committed by the resolution nodes.
_ROLE_HOLDERS = {"healer_player", "investigator_player", "serial_killer_player",
                 "vigilante_player"}
_SURVIVORS = {"surviving_wolves", "surviving_villagers"}


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
      _targets      tonight's committed night targets by state key, cleared at
                    ONE_MORE_DAY; the input to the night-death derivation.

    Vote buffers, held until the tally node commits. Keyed by voter and last write wins, so
    a ballot re-run after a human interrupt replaces the aborted one.
      _day_ballots       voter -> votee for the day vote in progress.
      _last_day_ballots  the ballots just flushed, kept until DAY_RESOLUTION recomputes
                         the lynch from them.
      _wolf_votes        wolf -> kill vote for the night in progress.

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
        self._targets: dict[str, str | None] = {}
        # Vote buffers.
        self._day_ballots: dict[str, str] = {}
        self._last_day_ballots: list[tuple[str, str]] = []
        self._wolf_votes: dict[str, str] = {}
        # Ship-once guards.
        self._seen_day_entries: set[tuple[int, int]] = set()
        self._seen_wolf_msgs: set[tuple[int, int, str]] = set()
        self._strategies: dict[str, str] = {}

    def hydrate(self, log: list) -> None:
        """Rebuild the shadow state from a durable event log (server-restart recovery).

        What rebuilds vs what deliberately stays empty:
        - seq counter, current_day, roles/wolves, send-once guards, strategy notes:
          all derivable from sent events — REBUILT (without the guards, the resume's
          abort-and-re-execute re-run would re-send every already-delivered message
          under fresh seqs).
        - ballot buffers and tonight's targets: LEFT EMPTY on purpose — an in-flight
          round's buffers are provisional state that the resume re-run re-streams from
          scratch, which is exactly the in-process abort-and-re-execute behavior; a
          committed round's ballots already sent as tally events and never re-run.
        """
        dead: set[str] = set()
        for e in log:
            self.seq = max(self.seq, e.seq)
            self.current_day = max(self.current_day, e.day)
            if e.type == "roles_assigned":
                self.roles = dict(e.roles)
                self.wolves = [p for p, r in self.roles.items() if r == "wolf"]
            elif e.type in ("speech", "pass_marker"):
                self._seen_day_entries.add((e.day, e.channel_seq))
            elif e.type == "wolf_message":
                self._seen_wolf_msgs.add((e.day, e.round, e.wolf))
            elif e.type == "strategy_update":
                self._strategies[e.player] = e.strategy
            elif e.type == "night_result":
                dead.update(d.player for d in e.deaths)
            elif e.type == "lynch_result" and e.player:
                dead.add(e.player)
        # wolves tracks SURVIVING wolves live (the chunks update it); replay the deaths.
        self.wolves = [w for w in self.wolves if w not in dead]

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
            return self._turn_tick(chunk["data"])
        if chunk["type"] != "updates":
            raise TranslationError(f"unexpected stream chunk type: {chunk['type']}")
        if is_cached(chunk):
            return []  # a re-streamed committed step: its events already sent

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

    def _turn_tick(self, payload: Mapping[str, Any]) -> list[ev.DurableEvent]:
        # The one custom chunk: the engine's "X is thinking" tick, written from a routing
        # edge so a re-run node cannot fire it twice.
        if payload.get("event") == "turn_started":
            return [self._emit(ev.TurnStarted, day=payload["day"], player=payload["player"])]
        raise TranslationError(f"unknown custom payload: {payload!r}")

    def _input_requests(self, interrupts, deadlines: Mapping[str, str]) -> list[ev.DurableEvent]:
        out = []
        for item in interrupts:
            req = item["value"]
            kind = _ACTION_KINDS.get(req["phase"])
            if kind is None:
                raise TranslationError(f"unknown human-turn phase: {req['phase']!r}")
            player = req["player_id"]
            out.append(self._emit(
                ev.InputRequest, day=req["day"], player=player, action_kind=kind,
                candidates=list(req.get("valid_targets") or []),
                deadline=deadlines.get(player),
            ))
        return out

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
        # The public roster is the union; the split by faction stays off the public tier.
        return [
            self._emit(ev.RosterUpdate, surviving_players=sorted([*villagers, *wolves])),
            self._emit(ev.PackRosterUpdate, surviving_wolves=list(wolves)),
        ]

    # ---- lifecycle --------------------------------------------------------------------

    @node("INITIALIZE_GAME", writes={
        "roles", "vigilante_bullets", "current_day", "human_players", "winner",
        "day_channel", "day_summaries", "wolf_channel", "day_votes", "investigator_results",
        "no_lynch_streak", *_ROLE_HOLDERS, *_SURVIVORS,
        "human_player",  # pre-rename spelling: the captured game predates multi-human
    })
    def _initialize_game(self, delta):
        self.roles = dict(delta.get("roles") or {})
        self.wolves = [p for p, r in self.roles.items() if r == "wolf"]
        self.current_day = delta.get("current_day", 1)
        bullets = delta.get("vigilante_bullets", 0)
        cast_counts: dict[str, int] = {}
        for role in self.roles.values():
            cast_counts[role] = cast_counts.get(role, 0) + 1

        out = [self._emit(ev.GameStarted, seats=list(self.roles), cast_role_counts=cast_counts)]
        for player, role in self.roles.items():
            out.append(self._emit(
                ev.RoleAssigned, player=player, role=role,
                pack=list(self.wolves) if role == "wolf" else None,
                bullets=bullets if role == "vigilante" else None,
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
                                      player=player, message=entry["message"]))
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

    @node("SUMMARIZE_DAY_DISCUSSION", writes={"day_summaries"})
    def _summarize_day_discussion(self, delta):
        return [self._emit(ev.DaySummary, day=s["day"], summary=s["summary"])
                for s in delta.get("day_summaries") or []]

    @node("START_VOTING")
    def _start_voting(self, delta):
        return [self._emit(ev.PhaseChange, phase="voting")]

    @node("vote", writes={"day_votes", "agent_strategies"})
    def _vote(self, delta):
        for ballot in delta.get("day_votes") or []:
            # Last write wins: a human interrupt re-runs this step, and the engine keeps
            # the re-run's ballot, which may differ from the one streamed before.
            self._day_ballots[ballot["voter"]] = ballot["votee"]
        return self._strategy_updates(delta)

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
        *_SURVIVORS, *_ROLE_HOLDERS,
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

    silent_node("PREPARE_WOLF_NIGHT", writes={"current_round"})

    @node("WOLF_NIGHT_DISCUSS", writes={"wolf_channel", "agent_strategies"})
    def _wolf_night_discuss(self, delta):
        out = []
        for entry in delta.get("wolf_channel") or []:
            if entry.get("passed"):
                continue  # technical pass: hidden from the pack, no wire event defined
            day, round_, wolf = entry["day"], entry["round"], entry["wolf"]
            if not _first_time(self._seen_wolf_msgs, (day, round_, wolf)):
                continue  # already sent (a re-run or a restart replay)
            out.append(self._emit(ev.WolfMessage, day=day, round=round_, wolf=wolf,
                                  message=entry["message"]))
        out.extend(self._strategy_updates(delta))
        return out

    silent_node("START_WOLF_VOTE")

    @node("WOLF_NIGHT_VOTE", writes={"wolf_channel", "agent_strategies"})
    def _wolf_night_vote(self, delta):
        # Buffered: blind while voting, flushed with the tally. The runtime streams each
        # wolf's vote as it lands, so the holding has to happen here.
        for entry in delta.get("wolf_channel") or []:
            if entry.get("vote"):
                # Last write wins per wolf, as with day ballots.
                self._wolf_votes[entry["wolf"]] = entry["vote"]
        return self._strategy_updates(delta)

    # A human wolf votes through the uncached twin node: same delta, same handling.
    node("WOLF_NIGHT_VOTE_HUMAN", writes={"wolf_channel", "agent_strategies"})(_wolf_night_vote)

    @node("COLLECT_WOLF_VOTES", writes={"wolves_kill_target"})
    def _collect_wolf_votes(self, delta):
        out = [self._emit(ev.WolfVote, wolf=wolf, votee=votee)
               for wolf, votee in self._wolf_votes.items()]
        self._wolf_votes.clear()
        target = delta.get("wolves_kill_target")
        if target is not None:
            self._targets["wolves_kill_target"] = target
            out.append(self._emit(ev.WolfKillDecided, target=target))
        return out

    def _night_act(self, role: str, delta):
        target_key = f"{role}_target"
        target = delta.get(target_key)
        # The vigilante's no-shot sentinel. The wrapper node turns it into None before it
        # reaches root state; the subgraph chunk still carries it raw. No act, no event.
        if target == "hold_fire":
            target = None
        out = []
        if target is not None:
            self._targets[target_key] = target
            out.append(self._emit(ev.NightAction,
                                  actor=self._role_holder(role), role=role, target=target))
        strategy = delta.get("updated_strategy")
        if strategy:
            # Same guard as the day path: send on change and remember what was sent, so
            # a restart can rebuild the map from the log.
            out.extend(self._strategy_updates(
                {"agent_strategies": {self._role_holder(role): strategy}}))
        return out

    silent_node("WOLF_NIGHT_PHASE", writes={
        "wolf_channel", "wolves_kill_target", "agent_strategies"})

    for _role in ("healer", "investigator", "serial_killer", "vigilante"):
        node(f"{_role}_act", writes={f"{_role}_target", "updated_strategy"})(
            lambda self, delta, role=_role: self._night_act(role, delta))
        # The root wrapper's commit: the target, and the strategy under the parent's key.
        silent_node(f"{_role.upper()}_NIGHT_PHASE",
                    writes={f"{_role}_target", "agent_strategies"})
    del _role

    @node("NIGHT_RESOLUTION", writes={
        "day_channel", "dead_roster", "wolf_channel", "investigator_results",
        "vigilante_results", "vigilante_bullets", "day_summaries",
        *_SURVIVORS, *_ROLE_HOLDERS,
    })
    def _night_resolution(self, delta):
        out = self._gm_messages(delta)

        # Compute the deaths with the engine's own rules, then compare with what the
        # node recorded.
        attacks = collect_attacks(self._targets.get("wolves_kill_target"),
                                  self._targets.get("serial_killer_target"),
                                  self._targets.get("vigilante_target"))
        verdicts = resolve_attacks(attacks, self._targets.get("healer_target"),
                                   self._role_holder("serial_killer"))
        deaths = [ev.NightDeath(player=t, role=self.roles.get(t, ""), attacker_types=attacks[t])
                  for t in sorted(attacks) if verdicts[t] == "killed"]
        recorded = {d["player"] for d in delta.get("dead_roster") or []}
        if {d.player for d in deaths} != recorded:
            raise TranslationError(
                f"kernel/delta mismatch: derived night deaths {[d.player for d in deaths]} "
                f"but the node recorded {sorted(recorded)}; refusing to send")
        save = next((ev.NightSave(player=t, attacker_types=attacks[t])
                     for t in attacks if verdicts[t] == "saved"), None)
        out.append(self._emit(ev.NightResult, deaths=deaths, save=save))

        # The GM's whiff note to the pack arrives on the wolf channel.
        for entry in delta.get("wolf_channel") or []:
            out.append(self._emit(ev.WolfMessage, day=entry["day"], round=entry["round"],
                                  wolf=entry["wolf"], message=entry["message"]))

        # Seat events: the investigation (the node omits it when the investigator is
        # dead, so no event either), the vigilante's private confirmation, the bullets.
        for result in delta.get("investigator_results") or []:
            out.append(self._emit(
                ev.InvestigationResult, day=result["day"],
                player=self._role_holder("investigator"),
                target=result["player_investigated"], role=result["role_revealed"],
            ))
        for _note in delta.get("vigilante_results") or []:
            out.append(self._emit(ev.VigilanteConfirmation, player=self._role_holder("vigilante"),
                                  target=self._targets.get("vigilante_target")))
        if "vigilante_bullets" in delta:
            out.append(self._emit(ev.BulletsRemaining, player=self._role_holder("vigilante"),
                                  count=delta["vigilante_bullets"]))

        out.extend(self._roster_updates(delta))
        return out

    @node("ONE_MORE_DAY", writes={
        "current_day", "day_votes", "voted_player", "wolves_kill_target", "healer_target",
        "investigator_target", "serial_killer_target", "vigilante_target",
    })
    def _one_more_day(self, delta):
        self.current_day = delta.get("current_day", self.current_day + 1)
        self._targets = {}
        self._wolf_votes.clear()
        return [self._emit(ev.PhaseChange, phase="day")]

    # ---- end --------------------------------------------------------------------------

    @node("END_GAME", writes={"day_channel", "winner"})
    def _end_game(self, delta):
        out = self._gm_messages(delta)
        out.append(self._emit(ev.GameOver, winner=delta.get("winner")))
        return out

    # Post-game memory work is not part of the game record; whatever it writes is ignored.
    silent_node("POST_GAME_ANALYSIS", writes=None)
