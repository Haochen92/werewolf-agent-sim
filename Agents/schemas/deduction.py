"""What the deduction engine tells a seat: lines computed by code from what the seat knows, never
from hidden state. Specification: evidence/reasoning_failures/deduction_catalogue.md (Table A is
level 1: a seat's own night result and what it implies)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from Agents.schemas.game_events import (
    AnnouncedDeath,
    AnnouncedSave,
    DeathRecord,
    NightActionRecord,
    NightAnnouncement,
    ReadOutWill,
    WillClause,
)

DeductionMode = Literal["off", "record", "public", "full"]
"""How much of the engine a game's AI seats get, set once per game (RunConfig.deduction_mode, and per
side RunConfig.deduction_by_side), by difficulty level (owner, 2026-10-18):
- "off": nothing (an A/B arm; a human seat always gets nothing);
- "record", level 1: the lines beside the seat's own night records;
- "public", level 2: those, the public block (Agents/deduction/render.py) and the seat's census and
  candidate roles: what the record alone works out;
- "full", level 3: those plus the claims against the record and each other, the conditionals, the
  explanations and an evil seat's covers."""

DeductionPlacement = Literal["before_note", "after_note"]
"""Where a seat's own deduction block sits in its prompt, relative to its carried-forward strategy
note (catalogue OQ21), set once per game (RunConfig.deduction_placement) so a screen can compare
the two. The public block never moves: it is in the shared public record, before the cache
boundary."""

Grade = Literal["certain", "follows_if_claims", "possible"]
"""The three grades of catalogue §0 (R9): holds in every legal game that agrees with what the seat
knows; holds if the named claims are true (the item's premises); or a complete list of
explanations ("either … or …")."""


@dataclass(frozen=True)
class SeatView:
    """Everything one seat knows, as the engine reads it: built from the seat's own payload and
    nothing else, so no line can rest on what the seat was not told (the leak boundary)."""

    player_id: str
    role: str
    """The seat's own role."""
    cast_role_counts: dict[str, int]
    """The public cast census: how many of each role were dealt."""
    dead_roster: list[DeathRecord]
    """The public dead roster, in death order."""
    night_records: list[NightActionRecord]
    """The seat's own night records (and, for a wolf, the pack's kill records)."""
    pack_roles: dict[str, str] = field(default_factory=dict)
    """For a wolf, its living pack and each one's role; empty for every other seat."""
    announcements: list[NightAnnouncement] = field(default_factory=list)
    """The public morning announcements as data, one per night resolved so far (empty on a
    payload from before they were kept: the rows that need them then say nothing)."""
    wills: list[ReadOutWill] = field(default_factory=list)
    """The read-out town records as data, one per revealed town death so far, each from the
    moment it was read out (catalogue L11)."""
    living: list[str] = field(default_factory=list)
    """Every living player, the seat included, in seat order; empty when the payload does not list
    them (the census then names no one)."""
    claims: list[PlayerClaimView] = field(default_factory=list)
    """Every player's public claims so far, today's included (Agents/deduction/claim_view.py)."""


@dataclass(frozen=True)
class PublicRecord:
    """What every seat knows alike: the part of a SeatView that is public. The public rows
    (level 5, Agents/deduction/public/) read only this, so their items cannot depend on whose
    payload they came from (they are cached in the prompt's shared prefix)."""

    cast_role_counts: dict[str, int]
    """The public cast census: how many of each role were dealt."""
    dead_roster: list[DeathRecord]
    """The public dead roster, in death order."""
    announcements: list[NightAnnouncement]
    """The morning announcements as data, one per night resolved so far."""
    wills: list[ReadOutWill]
    """The read-out town records as data, one per revealed town death so far."""
    living: list[str] = field(default_factory=list)
    """Every living player, in seat order (public: the game names the survivors)."""
    claims: list[PlayerClaimView] = field(default_factory=list)
    """Every player's public claims so far, today's included: anyone could hear them. Unlike the
    rest of the record they change with each message of the day, so a row that reads them does not
    belong in the cached public block (the joins, slice 9b, go in the seat block)."""


@dataclass(frozen=True)
class RoleClaim:
    """One change in a player's role claim, as the claim ledger keeps it."""

    day: int
    """The day it was said."""
    role: str
    withdrawn: bool
    """True: the player withdrew this role that day. A withdrawal stays in the history and
    reserves no role."""
    implied_by: tuple[ActionClaim, ...] = ()
    """Set when the player named no role but claimed actions only this role takes ("I held fire":
    the Vigilante): those claims. The engine reads it as a role claim; its wording says why."""


@dataclass(frozen=True)
class ActionClaim:
    """One night action a player claimed, as the claim ledger keeps it (Agents/rules/claim_ledger.py):
    the claimant's word, true or not (catalogue Table E's typed claim)."""

    claimant: str
    day: int
    """The day it was said."""
    night: int
    """The night it names; 0 = not said (also a night that had not happened by that day)."""
    action: str
    """The summary's action words (investigate, protect, shoot, kill, watch, follow, sigil, block,
    conceal, bet, pick), visit (went to the target, action not said), or no_action for a denial."""
    target: str
    """The player it was on; for no_action, the one not visited, or ""."""
    result: str
    """A result word ("not_said" when unstated); from an old summary possibly a role."""
    seen: tuple[str, ...]
    """A watch or follow: the players the claimant says they saw."""
    latest: bool
    """The claimant's current version for that night and action; False for a version they later
    changed (Table E compares the latest)."""
    blocked: bool
    """Says it was roleblocked: chosen, not carried out (L13)."""
    completed: bool
    """Says it went ahead: it states an outcome, or it is a claimed visit (L13: otherwise, read it
    as only tried)."""
    seen_complete: bool
    """The sighting is the whole list: only a stated "no one" (L12: a named list is partial)."""
    source: Literal["speaker", "summary"]
    """The speaker's own field (DayChannel.claimed_night_actions) or the day summariser's
    transcription (a human's line, a game from before the field)."""
    history: tuple[ActionClaim, ...] = ()
    """On the latest version: the versions it replaced, oldest first (each with latest False)."""


@dataclass(frozen=True)
class PlayerClaimView:
    """One player's public claims: role claims and withdrawals, and claimed night actions."""

    player: str
    roles: tuple[RoleClaim, ...]
    """Each change of role claim, in order; a repeated claim adds nothing."""
    current_role: str | None
    """The role claimed now; None if never claimed or withdrawn."""
    withdrawn_roles: tuple[str, ...]
    """Roles the player withdrew, in order."""
    actions: tuple[ActionClaim, ...]
    """Every claimed night action, each replaced version included (latest False), in night order
    (not-said nights last). Two targets named for the same night and action on the same day (one
    message, or one summary) are both latest."""


@dataclass(frozen=True)
class ReadRecord:
    """One of the seat's own night records, split into separate fields before any row reads it
    (catalogue L14). A record's `seen` list mixes kinds of names: a necromancer's record puts the
    body first, a check puts its target there, the pack's concealed kill the hidden role. Read raw,
    an empty watch through a body would show the body as a visitor."""

    night: int
    actor: str
    """The acting player, or "wolves" for the pack's kill."""
    action: str
    target: str | None
    result: str
    body: str | None
    """The dead player the necromancer acted through; None on every other seat's record."""
    observed: tuple[str, ...]
    """What a watch or a follow saw: the visitors (never the watcher, never the body), or the
    players the followed player went to. Empty for every other action."""
    hidden_role: str | None
    """The role of the pack's victim that the living illusionist hid, on the pack's kill record; the
    role of the necromancer's victim it hid through the illusionist's body, on its own kill record."""
    bet_role: str | None
    """The role a fortune teller's scored bet named (scored_1 with a role, scored_2)."""


@dataclass(frozen=True)
class RoleIn:
    """A machine-checkable fact: `player`'s role is one of `roles`. The tests check every emitted
    fact against the true roles of randomly generated nights (the soundness oracle)."""

    player: str
    roles: frozenset[str]


@dataclass(frozen=True)
class BlockedBy:
    """A machine-checkable fact: `player`'s action that night was cancelled by the living
    Chanteuse's block (`through_body` False) or by the Necromancer's block through her body."""

    player: str
    through_body: bool


@dataclass(frozen=True)
class AttackOutcome:
    """A machine-checkable fact about the attacks on `player` that night: either no attack went
    ahead on it, or every attack on it failed because it was immune for one of `immune_as` (a role
    name, or "self_bet" for a fortune teller betting on itself). An empty `immune_as` means no
    attack went ahead."""

    player: str
    immune_as: frozenset[str]


@dataclass(frozen=True)
class ProtectedBy:
    """A machine-checkable fact: a protection went ahead on `player` that night, made by the
    living Healer (`through_body` False) or by the Necromancer through the Healer's body."""

    player: str
    through_body: bool


@dataclass(frozen=True)
class WentTo:
    """A machine-checkable fact: an action under `visitor`'s own name went ahead on `target` that
    night (a visit)."""

    visitor: str
    target: str


@dataclass(frozen=True)
class ActedThroughBody:
    """A machine-checkable fact: the Necromancer acted on `target` through `body`'s body that
    night, and the action went ahead."""

    body: str
    target: str


@dataclass(frozen=True)
class NoVisitTo:
    """A machine-checkable fact: no action that went ahead visited `target` that night, hidden
    visits included, apart from the one shown under `except_name` (the watcher's own)."""

    target: str
    except_name: str


@dataclass(frozen=True)
class NotRoleUnlessBlocked:
    """A machine-checkable fact: `player` is not `role`, or `player` was roleblocked that night."""

    player: str
    role: str


@dataclass(frozen=True)
class CarriedPackKill:
    """A machine-checkable fact: `player` made the pack's kill that night, and it went ahead."""

    player: str


@dataclass(frozen=True)
class NoAttackUnless:
    """A machine-checkable fact: `player` made no attack that went ahead that night, under its own
    name or through a body, unless its role is one of `unless_roles`."""

    player: str
    unless_roles: frozenset[str]


@dataclass(frozen=True)
class KilledThroughBody:
    """A machine-checkable fact: `player` attacked through a dead player's body that night."""

    player: str


@dataclass(frozen=True)
class MadeBy:
    """A machine-checkable fact: the announced `action` on `target` that night was made, under its
    own name, by one of `players`. `action` is an attack type ("wolves", "serial_killer",
    "vigilante", "sigilist") or "healer" for the living Healer's protection."""

    target: str
    action: str
    players: tuple[str, ...]


@dataclass(frozen=True)
class VisitorsAmong:
    """A machine-checkable fact: every action that went ahead on `target` that night, hidden visits
    included, was a visit under one of `players`' names."""

    target: str
    players: tuple[str, ...]


@dataclass(frozen=True)
class CarriedOrAmong:
    """A machine-checkable fact: the holder of `role` carried the pack's kill that night, or is
    one of `players`."""

    role: str
    players: tuple[str, ...]


@dataclass(frozen=True)
class NotProtected:
    """A machine-checkable fact: no protection went ahead on `player` that night."""

    player: str


@dataclass(frozen=True)
class Visited:
    """A machine-checkable fact: a player holding one of `roles` went to `target` that night under
    its own name, with an action that went ahead. `shown`: that visit was among those a watch or a
    follow reports (False: it was hidden, as the living Illusionist hides the killer's; None: either)."""

    roles: frozenset[str]
    target: str
    shown: bool | None = True


@dataclass(frozen=True)
class NoHiddenVisitTo:
    """A machine-checkable fact: every visit to `target` that night that went ahead was shown to
    a watch or a follow."""

    target: str


@dataclass(frozen=True)
class AttackedInOwnName:
    """A machine-checkable fact: `player` made an attack under its own name that night, and it
    went ahead (the pack's kill, a shot or the Serial Killer's stab)."""

    player: str


@dataclass(frozen=True)
class SilentAttack:
    """A machine-checkable fact: an attack announced as `attacker_type` would have been made that
    night, went ahead, and failed in silence on a player holding one of `immune_roles` (an attack a
    fortune teller's self-bet stopped is announced, so it is not one)."""

    attacker_type: str
    immune_roles: frozenset[str]


@dataclass(frozen=True)
class AttacksOnlyOn:
    """A machine-checkable fact: every attack that went ahead that night was on a player holding
    one of `roles`; none went ahead when `roles` is empty."""

    roles: frozenset[str]


@dataclass(frozen=True)
class NoKillThroughBody:
    """A machine-checkable fact: no kill through a dead player's body went ahead that night, so the
    Necromancer read Not suspicious (catalogue L7, L10)."""


@dataclass(frozen=True)
class NoConcealsLeft:
    """A machine-checkable fact: the Illusionist's conceals (one pool for it and its body) were used
    up when that night began."""


@dataclass(frozen=True)
class MadeNoChoice:
    """A machine-checkable fact: `player` made no night choice that night: no action, no attempt,
    no hold_fire (catalogue L11, a night missing from a complete will)."""

    player: str


@dataclass(frozen=True)
class PickMade:
    """A machine-checkable fact: the Speculator picked `side` that night."""

    side: str


@dataclass(frozen=True)
class NeverPicked:
    """A machine-checkable fact over the whole game: `player`, the Speculator, never picked."""

    player: str


@dataclass(frozen=True)
class BodyUsable:
    """A machine-checkable fact: on that night the Necromancer could act through `player`'s body
    (revealed dead before it, with an ability to give)."""

    player: str


@dataclass(frozen=True)
class HeldBy:
    """A machine-checkable fact over the whole game: every holder of `role` is one of `players`
    (a census line: "the Serial Killer is one of …"; a dead holder is named by its body)."""

    role: str
    players: tuple[str, ...]


@dataclass(frozen=True)
class VisitAsClaimed:
    """A machine-checkable fact: the visit `claimant` claimed happened that night. An action under
    `visitor`'s name (a body's name, for the Necromancer) went ahead on `target`, and, when `shown`
    (the claim is a sighting), it was among the visits a watch or a follow reports. `claimant` only
    names whose report a line confirms (catalogue F1: two reports of one visit are two lines); what
    must hold does not depend on it."""

    claimant: str
    visitor: str
    target: str
    shown: bool


@dataclass(frozen=True)
class AnyOf:
    """A machine-checkable fact: at least one of `branches` holds, each branch facts that hold
    together. A complete list of explanations (catalogue §0, grade 3): the true branch is one of them."""

    branches: tuple[tuple[Fact, ...], ...]


@dataclass(frozen=True)
class NotAllTrue:
    """A machine-checkable fact: at least one of `facts` does not hold. Two claims that cannot both
    be true (catalogue Table E: never which of them), or one claim an engine source shows is false."""

    facts: tuple[Fact, ...]


@dataclass(frozen=True)
class NoVisitBy:
    """A machine-checkable fact: no action under `player`'s own name went ahead on anyone that night,
    a hidden visit included ("I visited no one": only that no visit was made in its name)."""

    player: str


@dataclass(frozen=True)
class NoShownVisitTo:
    """A machine-checkable fact: every visit to `target` that night that a watch or a follow could
    report was under `except_name`'s name (a claimed watch that saw no one: the watcher's own visit
    is never on its list)."""

    target: str
    except_name: str


@dataclass(frozen=True)
class NoShownVisitBy:
    """A machine-checkable fact: no visit under `player`'s name that night was one a watch or a
    follow could report (a claimed follow that saw the player visit no one)."""

    player: str


@dataclass(frozen=True)
class ChoseAction:
    """A machine-checkable fact: `player` chose `action` (a claim's action word: "protect",
    "shoot", …) on `target` that night, under its own name (not through a body); `went_ahead`:
    and no block cancelled it (catalogue L13: chosen, against carried out)."""

    player: str
    action: str
    target: str
    went_ahead: bool = False


@dataclass(frozen=True)
class CheckRead:
    """A machine-checkable fact: `player`'s check on `target` went ahead that night, under its own
    name, and read Suspicious (`suspicious` True) or Not suspicious."""

    player: str
    target: str
    suspicious: bool


@dataclass(frozen=True)
class DiedBy:
    """A machine-checkable fact: `player` died that night, and an attack of `attacker_type` was among
    those on it (the morning names every attack type on a death)."""

    player: str
    attacker_type: str


@dataclass(frozen=True)
class OnNight:
    """A machine-checkable fact: `fact` holds on night `night` (claims about several nights, read
    together: catalogue E11)."""

    night: int
    fact: Fact


@dataclass(frozen=True)
class Compatible:
    """Two claims that can both be true (catalogue E1, E17): each side is the facts one claim states.
    It holds in every game; the oracle counts the games where both sides held."""

    first: tuple[Fact, ...]
    second: tuple[Fact, ...]


@dataclass(frozen=True)
class OpenRoles:
    """A fact over the whole game: for each of `roles`, some legal game that agrees with the public
    record gives it to `player`, so claiming it contradicts no public fact (catalogue F7, for an evil
    seat). Checked by the brute-force oracle, not against one game."""

    player: str
    roles: frozenset[str]


@dataclass(frozen=True)
class NoUsesLeft:
    """A machine-checkable fact: when that night ended, the holder of `role` had no use of its
    limited ability left, so it has none on any later night (catalogue C17, C20, F9: the Fortune
    Teller's self-bets; the Illusionist's conceals, one pool for it and its body)."""

    role: str


Fact = (RoleIn | BlockedBy | AttackOutcome | ProtectedBy | WentTo | ActedThroughBody | NoVisitTo
        | NotRoleUnlessBlocked | CarriedPackKill | NoAttackUnless | KilledThroughBody | MadeBy
        | VisitorsAmong | CarriedOrAmong | NotProtected | Visited | NoHiddenVisitTo | AttackedInOwnName
        | SilentAttack | AttacksOnlyOn | NoKillThroughBody | NoConcealsLeft | MadeNoChoice | PickMade
        | NeverPicked | BodyUsable | HeldBy | VisitAsClaimed | AnyOf | NotAllTrue | NoVisitBy | NoShownVisitTo
        | NoShownVisitBy | ChoseAction | CheckRead | DiedBy | OnNight | Compatible | OpenRoles | NoUsesLeft)


@dataclass(frozen=True)
class OwnResultLine:
    """What a seat's own night record implies, shown next to that record."""

    text: str
    """The line the seat reads, in plain words naming players and nights."""
    row: str
    """The catalogue row it implements (e.g. "A6"), for tracing a live line back to its rule;
    rows joined with "+" when one line carries several (a watch read with the morning: "A26+A28")."""
    grade: Grade = "certain"
    """"possible" for a complete list of explanations ("either … or …")."""
    replaces_outcome: bool = False
    """True when the record's own prose is replaced rather than followed (the roleblock record)."""
    facts: tuple[Fact, ...] = field(default_factory=tuple)
    """The line's content as checkable facts; every one must hold in the real game."""


SourceKind = Literal["announcement", "will", "dead_roster", "own_record", "claim"]
"""Where an item's premises come from (catalogue §0, "Where knowledge comes from"): the engine's
certified sources (a morning, a read-out will, the dead roster, the seat's own record) and, for a
conditional item, a player's claim."""

SourceEvent = (AnnouncedDeath | AnnouncedSave | NightAnnouncement | WillClause | ReadOutWill | DeathRecord
               | NightActionRecord | ActionClaim)
"""A source event as the engine holds it: a death or a save the morning announced, a whole morning
(an absence, a pick), a will's night or the whole will, an entry of the dead roster, a record, a
player's claimed night action (a join with a claim, slice 9b)."""


@dataclass(frozen=True)
class Source:
    """One source an item rests on."""

    kind: SourceKind
    night: int
    """The night the source is about: the announcement's night, the will clause's night, or for
    the dead roster the day of the death."""
    player: str | None = None
    """The player the source names: the dead or saved player, the will's holder, the claimant."""


@dataclass(frozen=True)
class DeductionItem:
    """One conclusion the engine draws (catalogue, "Rendering: Items, then text"): the shape every
    level from 5 on emits. The renderer (slice 8) turns items into the block the seat reads; the
    derivation is logged with it but never shown, so a live line can be traced to why it was made."""

    row: str
    """The catalogue row(s) it implements, joined with "+" (a will's clause: "B18+A21")."""
    subject: str | None
    """The player the item is about, for one entry per player; None for a line about a night as a
    whole ("No one died", an absent attack)."""
    night: int
    """The night the conclusion is about; every fact in `conclusion` is about that night (a role is
    the same on every night)."""
    conclusion: tuple[Fact, ...]
    """The proposition as checkable facts: every one must hold in the real game (the soundness
    oracle, tests/factories/random_nights.py)."""
    text: str
    """The exact sentence (Agents/deduction/wording.py, public/wording.py), naming players and nights."""
    grade: Grade = "certain"
    premises: tuple[Fact, ...] = ()
    """What a "follows_if_claims" item assumes, as facts (a claim taken as true is the facts it
    states); empty for the other grades."""
    sources: tuple[Source, ...] = ()
    derivation: tuple[SourceEvent, ...] = ()
    """The source events the conclusion was drawn from, as the engine holds them."""
    receiver: str | None = None
    """The seat the item is for; None for a public item, the same for every seat (level 5)."""
    vote_form: bool = False
    """F6 only: the contrapositive worded about the evil roles the premise takes from the player
    ("player_8 can be the Serial Killer only if player_2's watch is false"), the form a vote turn
    shows (fold rule 3); False for the plain F6 and every other item."""


# --- the candidate roles (level 3: catalogue Table C, F3, F7) ------------------------------------

@dataclass(frozen=True)
class OnlyRoles:
    """A constraint the candidate roles read: `player`'s role is one of `roles`."""

    player: str
    roles: frozenset[str]
    rule: str
    """The catalogue row(s) it comes from ("C1", "L8", or the row of the item whose fact it is)."""
    sources: tuple[Source, ...] = ()
    derivation: tuple[SourceEvent, ...] = ()


@dataclass(frozen=True)
class AliveAtNight:
    """A constraint: the holder of `role` was alive at the start of night `night`, so it is not a
    body that died before then (catalogue F, "a role whose holder must be alive")."""

    role: str
    night: int
    deed: str
    """What the holder did that night, for the census line's reason: "killed_through_body",
    "acted_through_body", "roleblocked", "roleblocked_the_carrier", "protected", "went_to",
    "attacked" or "picked"."""
    target: str | None = None
    """The player the deed was on, when there is one."""
    rule: str = ""
    sources: tuple[Source, ...] = ()
    derivation: tuple[SourceEvent, ...] = ()


@dataclass(frozen=True)
class HolderAmong:
    """A constraint: some player among `players` holds one of `roles` (an announced attack or save
    made by one of the players a watch saw: catalogue A28, A29, C6)."""

    players: tuple[str, ...]
    roles: frozenset[str]
    rule: str
    sources: tuple[Source, ...] = ()
    derivation: tuple[SourceEvent, ...] = ()


RoleConstraint = OnlyRoles | AliveAtNight | HolderAmong
"""What the candidate roles are built from: every certain fact the engine states, read as one of
these, and the census rules (catalogue C1, L8)."""


@dataclass(frozen=True)
class Removal:
    """Why a role is no longer a candidate for a player: the rule that removed it and what that rule
    rested on (for the item's sources and derivation)."""

    role: str
    rule: str
    sources: tuple[Source, ...] = ()
    derivation: tuple[SourceEvent, ...] = ()


@dataclass(frozen=True)
class Candidates:
    """The roles each player, living or a hidden body, can still hold, as far as one view knows:
    the public's (identical for every seat) or one seat's (catalogue Table F, "Candidate roles per
    player"). Sound, not complete: a role is removed only when no legal game that agrees with the
    view gives it to that player."""

    living: tuple[str, ...]
    """The living players, in seat order."""
    hidden_bodies: tuple[str, ...]
    """The players who died with their role hidden, in death order."""
    roles: dict[str, frozenset[str]]
    """Every player's candidate roles, the dead included; one role for a player whose role is known."""
    census: frozenset[str]
    """What the census leaves everyone: the dealt roles not revealed at a death, not the receiver's
    and not its pack's. F7 speaks only of a player whose candidates are fewer."""
    known: frozenset[str]
    """The players whose role the view knows outright: the revealed dead, the receiver and its pack."""
    removals: dict[str, tuple[Removal, ...]]
    """Per player, why each role it lost is gone."""
    alive_reasons: dict[str, AliveAtNight]
    """Per role, the latest-night constraint that took the role off a hidden body: the census line's
    reason that its holder is alive."""
    receiver: str | None = None
    """The seat whose view this is; None for the public's."""


# --- the rendered blocks (slice 8: catalogue "Rendering") --------------------------------------

@dataclass(frozen=True)
class RenderedBlock:
    """One deduction block as the seat reads it, with the items it shows. The items' derivations
    go to the turn's log (Agents/deduction/render.py `deduction_log`), never into the text."""

    text: str
    """The block, heading included; "" when it has no line."""
    shown: tuple[DeductionItem, ...] = ()
    """The items whose sentences are in `text`, in the order shown."""


@dataclass(frozen=True)
class DeductionBlocks:
    """One turn's two blocks, split by where they sit in the prompt (Agents/prompts/layout.py)."""

    public: RenderedBlock
    """The same for every seat of a game at that moment: in the shared public record, before the
    cache boundary. It changes only at a morning, a reveal or a vote."""
    seat: RenderedBlock
    """This seat's own lines and today's raised events: after the boundary, before or after its
    strategy note (DeductionPlacement)."""


# --- the joins with claims (slice 9b: catalogue Table F, F1 and F2) ---------------------------------

@dataclass(frozen=True)
class KnownVisit:
    """A visit an engine source shows went ahead: the seat's own action, or a visitor its own watch
    or follow saw, or the same in a read-out will (catalogue F1). A claim that states the same visit
    is confirmed on that point only."""

    night: int
    visitor: str
    """The visitor's name as shown: the seat (or the will's holder) for its own action."""
    target: str
    how: Literal["own_action", "watch", "follow"]
    holder: str | None
    """None for the seat's own record; the dead holder of a read-out will."""
    action: str
    """The record's action ("investigate", "protect", …): what the seat or the holder did, for
    "own_action"; the sighting's for a watch or a follow."""
    record: NightActionRecord
    """The record (or the will's night, as its record) it was read from."""


@dataclass(frozen=True)
class VisitClaim:
    """A visit a claim states: `visitor` went to `target` on `night`. From a sighting (the claimant's
    watch on the target, or its follow of the visitor) or from the visitor's own claimed action."""

    night: int
    visitor: str
    target: str
    claim: ActionClaim
    sighting: bool
    """True: the claimant says it saw the visit (a watch or a follow); False: the claimant is the
    visitor, claiming its own action."""
    went_ahead: bool
    """The claim says the visit happened: a sighting, or an own action stated as carried out (L13:
    an action claimed with no outcome is only "tried")."""


# --- the conditionals (slice 10: catalogue Table F, F4 to F6) ---------------------------------------

PremiseKind = Literal["role_claims", "role_claim", "action"]
"""What a conditional line assumes (catalogue §0, grade 2): the current role claims together (F4),
one player's role claim (F5, "player_9's claim"), or one claimed night action with its claimant's
role (F5, "player_2's watch")."""


@dataclass(frozen=True)
class Premise:
    """The claims a conditional line assumes true, as the propagation adds them (catalogue Table F,
    "How the engine derives them"): each assumed role, and each visit the claim states, taken as
    verified for that run only."""

    kind: PremiseKind
    claimant: str | None
    """The player whose claim it is; None for the current role claims."""
    roles: tuple[tuple[str, str], ...]
    """(player, role) pairs assumed: the claimant's role, or every claimant's for the role claims."""
    claim: ActionClaim | None = None
    """The claimed night action, for an action premise."""
    visits: tuple[VisitClaim, ...] = ()
    """The visits the claimed action states went ahead: the claimant's own, and those it saw."""
    facts: tuple[Fact, ...] = ()
    """The premise as checkable facts (the item's `premises`): when they all hold in the real game,
    every conclusion drawn under it must hold too (the truth oracle)."""
    night: int = 0
    """The night the claimed action is about; 0 for a role premise (a role holds on every night)."""
    unchecked_only: bool = False
    """The role claims only: some role claim the seat can check (its own, its pack's, a revealed
    player's) is false, so the line assumes every role claim it cannot check instead."""


# --- the comparisons of claims (slice 11: catalogue Table E, F3's claim status) ---------------------

StatementSource = Literal["own_record", "will", "claim"]
"""Where a statement about a visit comes from: the seat's own record, a read-out will (both engine
sources: certain), or a player's claim (its word, true or not)."""


@dataclass(frozen=True)
class VisitStatement:
    """Something that says a visit went ahead on `night`: one of `visitors` went to `target`. One
    name, or for a roleblock the names that could have made the block (the Chanteuse's possible
    holders, or her body's name)."""

    night: int
    visitors: tuple[str, ...]
    target: str
    shown: bool
    """A watch or a follow could have reported it (False: it may be a visit the living Illusionist's
    conceal hid)."""
    source: StatementSource
    claim: ActionClaim | None = None
    """The claim it comes from (a sighting, the visitor's own action, a roleblock); None for an
    engine source."""
    known: KnownVisit | None = None
    """The engine source's visit (the seat's own action, or a watch or follow it or a will saw)."""
    block: bool = False
    """The statement is a roleblock: the Chanteuse (or her body) came to `target`."""
    facts: tuple[Fact, ...] = ()
    """What the statement says, as checkable facts (for a claim: what holds if it is true)."""


VisitListKind = Literal["to", "by", "none_by", "not_to"]
"""What an exhaustive account covers: every visitor to a player but its watcher ("to"); every place a
player went that a watch or a follow could see ("by"); that a player went nowhere ("none_by"); that a
player did not go to one player ("not_to")."""


@dataclass(frozen=True)
class VisitList:
    """An account that rules visits out (catalogue L12: only a whole list does): an engine watch or
    follow, a claimed sighting of "no one", a player's own denial, or the seat's own movements."""

    night: int
    kind: VisitListKind
    subject: str
    """The watched player ("to"), or the player whose movements it covers."""
    names: tuple[str, ...]
    """"to": the visitors seen; "by": the places seen; empty for "none_by"; for "not_to", the one
    player not visited."""
    watcher: str | None
    """"to": the watcher, whose own visit is never on its list."""
    source: StatementSource
    claim: ActionClaim | None = None
    record: NightActionRecord | None = None
    """The engine record it was read from (the seat's own, or a will's night)."""
    holder: str | None = None
    """The dead holder of a read-out will; None for the seat's own record or a claim."""
    facts: tuple[Fact, ...] = ()
    """What the account says, as checkable facts."""


# --- the possible explanations (slice 12: catalogue Table F, F8) ------------------------------------

@dataclass(frozen=True)
class Branch:
    """One way a claimed action can have ended that the record leaves open (catalogue F8, §0 grade 3):
    one branch of a complete list of explanations. The claim being false is a branch of every list,
    added by the line itself."""

    text: str
    """The branch as the line words it: "player_4 was roleblocked", "player_9 is the Serial Killer"."""
    facts: tuple[Fact, ...]
    """What holds on this branch, as checkable facts (they hold together)."""
