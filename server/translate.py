"""The translator: LangGraph v2 stream parts in, tier-ready durable wire events out.

One Translator instance per game. It consumes exactly what the production stream call yields —
``graph.stream(..., stream_mode=["updates", "custom"], subgraphs=True, version="v2")`` — and
emits ``server.schemas.events`` durable events with a per-game monotone ``seq``. The ephemeral
pacing channel is NOT built here (it needs asyncio timers → server layer).

The load-bearing rules, each verified against notebooks/fixtures/chunk_catalogue.jsonl:

- **Cached drop**: a replayed part (interrupt resume / crash recovery) arrives tagged
  ``__metadata__: {cached: True}`` and is dropped whole — its events already shipped.
- **One authoritative scope per key**: every subgraph commit streams twice (fine-grained under
  its namespace, then the wrapper node's folded delta at root). Per-turn keys translate from
  the subgraph parts; the root wrapper re-emissions are ignored wholesale.
- **Entitlement buffers**: day ballots and wolf kill votes are held until their tally commits
  (COLLECT_VOTES / COLLECT_WOLF_VOTES) — blind voting for the interrupted human seat, full
  reveal after (the spike proved sibling deltas surface mid-superstep, so the runtime does
  NOT buffer for us).
- **Shared kernel, no drift**: lynch_result and night_result are derived with the SAME rule
  functions the engine nodes call (Agents.rules.resolution) and cross-checked against the
  delta's own record (voted_player / dead_roster) — a mismatch raises instead of shipping a
  wrong (or leaky) event.
- **Exhaustiveness**: every (scope, node, key) must be consumed by a handler or listed in
  _FOLDS. Anything else raises TranslationError — silence is never accidental.

Not yet emitted (schema rows without a stream source, deferred): day_summary_structured (the
structured summary never reaches state — summarizer returns prose only).
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from Agents.rules.resolution import collect_attacks, resolve_attacks, tally_day_vote
from server.schemas import events as ev


class TranslationError(RuntimeError):
    """A stream part the wire contract does not account for — fail loudly, never skip."""


def _field(obj: Any, name: str, default: Any = None) -> Any:
    """Tolerant accessor: live parts carry Pydantic models, fixture replays carry dicts."""
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)


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

# Root-level wrapper nodes whose deltas are re-emissions of subgraph commits (ignored whole),
# and the subgraph namespaces those commits authoritatively translate under.
_WRAPPER_NODES = {
    "DAY_PHASE",
    "WOLF_NIGHT_PHASE",
    "HEALER_NIGHT_PHASE",
    "INVESTIGATOR_NIGHT_PHASE",
    "SERIAL_KILLER_NIGHT_PHASE",
    "VIGILANTE_NIGHT_PHASE",
}
_NIGHT_SCOPES = {
    "WOLF_NIGHT_PHASE",
    "HEALER_NIGHT_PHASE",
    "INVESTIGATOR_NIGHT_PHASE",
    "SERIAL_KILLER_NIGHT_PHASE",
    "VIGILANTE_NIGHT_PHASE",
}

# Explicitly-folded keys per (scope, node): committed state whose information content already
# ships in another form (or is pure engine bookkeeping). See frontend/event_derivation.md.
_FOLDS: dict[tuple[str, str], set[str]] = {
    ("root", "INITIALIZE_GAME"): {
        "day_channel", "day_summaries", "wolf_channel", "day_votes",
        "investigator_results", "surviving_wolves", "surviving_villagers",
        "current_day", "human_player", "no_lynch_streak", "winner",
    },
    ("root", "DAY_RESOLUTION"): {
        "day_summaries", "voted_player", "no_lynch_streak",
        "healer_player", "investigator_player", "serial_killer_player", "vigilante_player",
    },
    ("root", "NIGHT_RESOLUTION"): {
        "day_summaries",
        "healer_player", "investigator_player", "serial_killer_player", "vigilante_player",
    },
    ("root", "ONE_MORE_DAY"): {
        "day_votes", "voted_player", "wolves_kill_target", "healer_target",
        "investigator_target", "serial_killer_target", "vigilante_target",
    },
    ("DAY_PHASE", "SCHEDULE"): set(),
    ("WOLF_NIGHT_PHASE", "PREPARE_WOLF_NIGHT"): {"current_round"},
    ("WOLF_NIGHT_PHASE", "START_WOLF_VOTE"): set(),
}


class Translator:
    """Stateful per-game translator. Feed every stream part to translate(); collect events."""

    def __init__(self) -> None:
        self.seq = 0
        self.current_day = 1
        # Captured at INITIALIZE_GAME; the context single parts don't carry.
        self.roles: dict[str, str] = {}
        self.wolves: list[str] = []
        # Entitlement buffers (flushed at the respective tally commit).
        self._day_ballots: list[tuple[str, str]] = []
        self._last_day_ballots: list[tuple[str, str]] = []
        self._wolf_votes: list[tuple[str, str]] = []
        # Tonight's committed targets, tracked for the kernel-derived night_result.
        self._targets: dict[str, str | None] = {}
        self._night_announced = False

    # ---- context helpers --------------------------------------------------------------

    def _role_holder(self, role: str) -> str | None:
        return next((p for p, r in self.roles.items() if r == role), None)

    def _emit(self, cls, *, day: int | None = None, **fields) -> ev.DurableEvent:
        self.seq += 1
        return cls(seq=self.seq, day=self.current_day if day is None else day, **fields)

    # ---- entry point ------------------------------------------------------------------

    def translate(self, part: Mapping[str, Any]) -> list[ev.DurableEvent]:
        data = part["data"]
        if part["type"] == "custom":
            return self._custom(data)
        if part["type"] != "updates":
            raise TranslationError(f"unexpected stream part type: {part['type']}")
        if isinstance(data, Mapping) and _field(_field(data, "__metadata__", {}), "cached"):
            return []  # replayed part: its events already shipped (spike verdict b)

        ns = part.get("ns") or ()
        scope = ns[0].split(":")[0] if ns else "root"

        out: list[ev.DurableEvent] = []
        # Night entry marker is lazy: the first night-scoped part opens the night — emitting
        # at DAY_RESOLUTION would need winner lookahead (END_GAME emits no night).
        if scope in _NIGHT_SCOPES and not self._night_announced:
            self._night_announced = True
            out.append(self._emit(ev.PhaseChange, phase="night"))

        for node, delta in data.items():
            if node == "__interrupt__":
                out.extend(self._interrupt(delta))
                continue
            if node.startswith("__"):
                continue
            out.extend(self._node(scope, node, delta or {}))
        return out

    # ---- per-source translation -------------------------------------------------------

    def _custom(self, payload: Mapping[str, Any]) -> list[ev.DurableEvent]:
        if _field(payload, "event") == "turn_started":
            return [self._emit(ev.TurnStarted,
                               day=_field(payload, "day"), player=_field(payload, "player"))]
        raise TranslationError(f"unknown custom payload: {payload!r}")

    def _interrupt(self, interrupts) -> list[ev.DurableEvent]:
        out = []
        for item in interrupts:
            req = _field(item, "value", item)
            phase = _field(req, "phase")
            kind = _ACTION_KINDS.get(phase)
            if kind is None:
                raise TranslationError(f"unknown human-turn phase: {phase!r}")
            out.append(self._emit(
                ev.InputRequest,
                day=_field(req, "day"),
                player=_field(req, "player_id"),
                action_kind=kind,
                candidates=list(_field(req, "valid_targets", []) or []),
            ))
        return out

    def _node(self, scope: str, node: str, delta: Mapping[str, Any]) -> list[ev.DurableEvent]:
        if scope == "root" and node in _WRAPPER_NODES:
            return []  # re-emission of subgraph commits already translated at their own scope
        handler = getattr(self, f"_h_{node.lower()}", None)
        if handler is None:
            if (scope, node) in _FOLDS:
                self._check_folds(scope, node, delta, consumed=set())
                return []
            raise TranslationError(f"no handler or fold entry for ({scope}, {node})")
        return handler(scope, node, delta)

    def _check_folds(self, scope: str, node: str, delta: Mapping[str, Any],
                     consumed: set[str]) -> None:
        folded = _FOLDS.get((scope, node), set())
        unaccounted = set(delta) - consumed - folded
        if unaccounted:
            raise TranslationError(
                f"({scope}, {node}) committed unaccounted keys {sorted(unaccounted)} — "
                "add an event or an explicit fold (frontend/event_derivation.md)"
            )

    # ---- handlers: lifecycle ----------------------------------------------------------

    def _h_initialize_game(self, scope, node, delta):
        self.roles = dict(_field(delta, "roles", {}))
        self.wolves = [p for p, r in self.roles.items() if r == "wolf"]
        self.current_day = _field(delta, "current_day", 1)
        bullets = _field(delta, "vigilante_bullets", 0)
        cast_counts: dict[str, int] = {}
        for role in self.roles.values():
            cast_counts[role] = cast_counts.get(role, 0) + 1

        out = [self._emit(ev.GameStarted,
                          seats=list(self.roles), cast_role_counts=cast_counts)]
        for player, role in self.roles.items():
            out.append(self._emit(
                ev.RoleAssigned, player=player, role=role,
                pack=list(self.wolves) if role == "wolf" else None,
                bullets=bullets if role == "vigilante" else None,
            ))
        out.append(self._emit(ev.RolesAssigned, roles=dict(self.roles)))
        out.append(self._emit(ev.PhaseChange, phase="day"))
        self._check_folds(scope, node, delta,
                          consumed={"roles", "vigilante_bullets", "healer_player",
                                    "investigator_player", "serial_killer_player",
                                    "vigilante_player"})
        return out

    def _h_one_more_day(self, scope, node, delta):
        self.current_day = _field(delta, "current_day", self.current_day + 1)
        self._targets = {}
        self._wolf_votes.clear()
        self._night_announced = False
        self._check_folds(scope, node, delta, consumed={"current_day"})
        return [self._emit(ev.PhaseChange, phase="day")]

    def _h_end_game(self, scope, node, delta):
        out = self._gm_messages(delta)
        out.append(self._emit(ev.GameOver, winner=_field(delta, "winner")))
        self._check_folds(scope, node, delta, consumed={"day_channel", "winner"})
        return out

    def _h_post_game_analysis(self, scope, node, delta):
        return []  # IGNORED on the wire (ruled); postgame memory work is not game record

    # ---- handlers: day ----------------------------------------------------------------

    def _h_discuss(self, scope, node, delta):
        out = []
        for entry in _field(delta, "day_channel", []) or []:
            day, cseq, player = _field(entry, "day"), _field(entry, "seq"), _field(entry, "player")
            if _field(entry, "passed"):
                out.append(self._emit(
                    ev.PassMarker, day=day, channel_seq=cseq, player=player,
                    pass_reason=_field(entry, "pass_reason"),
                    gated=bool(_field(entry, "gated")),
                    gated_candidate=_field(entry, "gated_candidate") or None,
                ))
            else:
                out.append(self._emit(ev.Speech, day=day, channel_seq=cseq,
                                      player=player, message=_field(entry, "message")))
            firing = _field(entry, "firing_reason")
            if firing is not None:
                out.append(self._emit(
                    ev.FiringReasonAnnotation, day=day, about_channel_seq=cseq, player=player,
                    tier=_field(firing, "tier"), owes=list(_field(firing, "owes", []) or []),
                ))
            targets = _field(entry, "addressed_targets", []) or []
            if targets:
                out.append(self._emit(
                    ev.AddressedTargetsAnnotation, day=day, about_channel_seq=cseq,
                    player=player,
                    targets=[ev.WireAddressedTarget(
                        target=_field(t, "target"),
                        addressed_form=_field(t, "addressed_form"),
                        stance=_field(t, "stance"),
                    ) for t in targets],
                ))
        out.extend(self._strategy_updates(delta))
        self._check_folds(scope, node, delta, consumed={"day_channel", "agent_strategies"})
        return out

    def _h_vote(self, scope, node, delta):
        for ballot in _field(delta, "day_votes", []) or []:
            self._day_ballots.append((_field(ballot, "voter"), _field(ballot, "votee")))
        out = self._strategy_updates(delta)
        self._check_folds(scope, node, delta, consumed={"day_votes", "agent_strategies"})
        return out

    def _h_start_voting(self, scope, node, delta):
        self._check_folds(scope, node, delta, consumed=set())
        return [self._emit(ev.PhaseChange, phase="voting")]

    def _h_collect_votes(self, scope, node, delta):
        # Content from the buffer, timing from node identity (its own delta is empty).
        out = [self._emit(ev.VoteCast, voter=voter, votee=votee)
               for voter, votee in self._day_ballots]
        self._last_day_ballots = list(self._day_ballots)
        self._day_ballots.clear()
        self._check_folds(scope, node, delta, consumed=set())
        return out

    def _h_summarize_day_discussion(self, scope, node, delta):
        out = [self._emit(ev.DaySummary, day=_field(s, "day"), summary=_field(s, "summary"))
               for s in _field(delta, "day_summaries", []) or []]
        self._check_folds(scope, node, delta, consumed={"day_summaries"})
        return out

    def _h_day_resolution(self, scope, node, delta):
        out = self._gm_messages(delta)
        tally = tally_day_vote(votee for _, votee in self._last_day_ballots)
        voted = _field(delta, "voted_player")
        if tally.lynched != voted:
            raise TranslationError(
                f"kernel/delta mismatch: tally lynched {tally.lynched!r} but the node "
                f"committed voted_player={voted!r} — inputs drifted, refusing to ship"
            )
        out.append(self._emit(
            ev.LynchResult,
            outcome=tally.outcome,
            player=voted,
            role=self.roles.get(voted) if voted else None,
            vote_counts=tally.vote_counts,
            no_lynch_streak=_field(delta, "no_lynch_streak", 0),
        ))
        out.extend(self._roster_updates(delta))
        # dead_roster: the lynch death record rides INSIDE lynch_result (player + role).
        self._check_folds(scope, node, delta,
                          consumed={"day_channel", "dead_roster",
                                    "surviving_wolves", "surviving_villagers"})
        return out

    # ---- handlers: night --------------------------------------------------------------

    def _h_healer_act(self, scope, node, delta):
        return self._night_act("healer", "healer_target", scope, node, delta)

    def _h_investigator_act(self, scope, node, delta):
        return self._night_act("investigator", "investigator_target", scope, node, delta)

    def _h_serial_killer_act(self, scope, node, delta):
        return self._night_act("serial_killer", "serial_killer_target", scope, node, delta)

    def _h_vigilante_act(self, scope, node, delta):
        return self._night_act("vigilante", "vigilante_target", scope, node, delta)

    def _night_act(self, role, target_key, scope, node, delta):
        out = []
        target = _field(delta, target_key)
        # The vigilante's no-shot sentinel: the wrapper node normalizes it to None before
        # root state (Agents/graphs/parent.py) — the subgraph part carries it raw, so the
        # translator applies the same normalization. No act -> no event, matching state.
        if target == "hold_fire":
            target = None
        if target is not None:
            self._targets[target_key] = target
            out.append(self._emit(ev.NightAction,
                                  actor=self._role_holder(role), role=role, target=target))
        strategy = _field(delta, "updated_strategy")
        if strategy:
            out.append(self._emit(ev.StrategyUpdate,
                                  player=self._role_holder(role), strategy=strategy))
        self._check_folds(scope, node, delta, consumed={target_key, "updated_strategy"})
        return out

    def _h_wolf_night_discuss(self, scope, node, delta):
        out = []
        for entry in _field(delta, "wolf_channel", []) or []:
            if _field(entry, "passed"):
                continue  # technical pass: hidden from the pack, no wire event defined
            out.append(self._emit(
                ev.WolfMessage, day=_field(entry, "day"), round=_field(entry, "round"),
                wolf=_field(entry, "wolf"), message=_field(entry, "message"),
            ))
        out.extend(self._strategy_updates(delta))
        self._check_folds(scope, node, delta, consumed={"wolf_channel", "agent_strategies"})
        return out

    def _h_wolf_night_vote(self, scope, node, delta):
        # Buffered: blind while voting, flushed with the tally (ruled R2; the spike proved
        # the runtime streams sibling votes mid-superstep, so we must hold them).
        for entry in _field(delta, "wolf_channel", []) or []:
            if _field(entry, "vote"):
                self._wolf_votes.append((_field(entry, "wolf"), _field(entry, "vote")))
        out = self._strategy_updates(delta)
        self._check_folds(scope, node, delta, consumed={"wolf_channel", "agent_strategies"})
        return out

    def _h_collect_wolf_votes(self, scope, node, delta):
        out = [self._emit(ev.WolfVote, wolf=wolf, votee=votee)
               for wolf, votee in self._wolf_votes]
        self._wolf_votes.clear()
        target = _field(delta, "wolves_kill_target")
        if target is not None:
            self._targets["wolves_kill_target"] = target
            out.append(self._emit(ev.WolfKillDecided, target=target))
        self._check_folds(scope, node, delta, consumed={"wolves_kill_target"})
        return out

    def _h_night_resolution(self, scope, node, delta):
        out = self._gm_messages(delta)

        # Derive the death atom with the SAME kernel the node used, then cross-check.
        attacks = collect_attacks(self._targets.get("wolves_kill_target"),
                                  self._targets.get("serial_killer_target"),
                                  self._targets.get("vigilante_target"))
        verdicts = resolve_attacks(attacks, self._targets.get("healer_target"),
                                   self._role_holder("serial_killer"))
        deaths = [ev.NightDeath(player=t, role=self.roles.get(t, ""),
                                attacker_types=attacks[t])
                  for t in sorted(attacks) if verdicts[t] == "killed"]
        recorded = {_field(d, "player") for d in _field(delta, "dead_roster", []) or []}
        if {d.player for d in deaths} != recorded:
            raise TranslationError(
                f"kernel/delta mismatch: derived night deaths {[d.player for d in deaths]} "
                f"but the node recorded {sorted(recorded)} — refusing to ship"
            )
        save = next((ev.NightSave(player=t, attacker_types=attacks[t])
                     for t in attacks if verdicts[t] == "saved"), None)
        out.append(self._emit(ev.NightResult, deaths=deaths, save=save))

        # Faction: the GM whiff note rides the wolf channel.
        for entry in _field(delta, "wolf_channel", []) or []:
            out.append(self._emit(
                ev.WolfMessage, day=_field(entry, "day"), round=_field(entry, "round"),
                wolf=_field(entry, "wolf"), message=_field(entry, "message"),
            ))

        # Seats: investigation (survival-gated in the node — absent delta, absent event),
        # the vigilante's private confirmation, and the bullet count.
        for result in _field(delta, "investigator_results", []) or []:
            out.append(self._emit(
                ev.InvestigationResult, day=_field(result, "day"),
                player=self._role_holder("investigator"),
                target=_field(result, "player_investigated"),
                role=_field(result, "role_revealed"),
            ))
        for _note in _field(delta, "vigilante_results", []) or []:
            out.append(self._emit(
                ev.VigilanteConfirmation, player=self._role_holder("vigilante"),
                target=self._targets.get("vigilante_target"),
            ))
        if "vigilante_bullets" in delta:
            out.append(self._emit(ev.BulletsRemaining,
                                  player=self._role_holder("vigilante"),
                                  count=_field(delta, "vigilante_bullets")))

        out.extend(self._roster_updates(delta))
        self._check_folds(scope, node, delta, consumed={
            "day_channel", "dead_roster", "wolf_channel", "investigator_results",
            "vigilante_results", "vigilante_bullets",
            "surviving_wolves", "surviving_villagers",
        })
        return out

    # ---- shared fragments -------------------------------------------------------------

    def _gm_messages(self, delta):
        return [self._emit(ev.GmMessage, day=_field(e, "day"), channel_seq=_field(e, "seq"),
                           text=_field(e, "message"))
                for e in _field(delta, "day_channel", []) or []
                if _field(e, "player") == "game_master"]

    def _strategy_updates(self, delta):
        strategies = _field(delta, "agent_strategies", {}) or {}
        return [self._emit(ev.StrategyUpdate, player=player, strategy=text)
                for player, text in strategies.items()]

    def _roster_updates(self, delta):
        wolves = _field(delta, "surviving_wolves")
        villagers = _field(delta, "surviving_villagers")
        if wolves is None and villagers is None:
            return []  # no-death resolution: rosters unchanged, no event
        if wolves is None or villagers is None:
            raise TranslationError(
                "resolution committed only one survivor bucket — the engine always commits "
                "both together; refusing to ship a partial roster"
            )
        self.wolves = list(wolves)
        # Union only: the wolf-partitioned lists merge before the public tier sees them.
        return [
            self._emit(ev.RosterUpdate, surviving_players=sorted([*villagers, *wolves])),
            self._emit(ev.PackRosterUpdate, surviving_wolves=list(wolves)),
        ]
