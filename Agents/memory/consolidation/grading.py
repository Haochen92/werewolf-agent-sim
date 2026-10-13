"""Ten-seat decision grades: one verdict per decision, read from the game record.

Each role's turn is graded by the outcome that is ideal for it ("positive"), neutral, or
undesirable ("negative": a wasted turn, a limited use spent for nothing, a foreseeable failure,
exposure). The table is plan §9.6 item 10 (evidence/memory_system/v8/plan.md); why it is so is
decisions §12. ``None`` means unscored: the Necromancer's nights, the Fortune Teller's votes, the
Speculator's votes before its pick.

Everything is read from the record a ten-seat night keeps (each choice, each actor's result, the
attacks, visits and conceals) and the day resolutions; sides come from the role registry.
"""

from __future__ import annotations

from types import SimpleNamespace

from Agents.rules.night_record import PACK_ACTOR
from Agents.schemas.roles import LONE_KILLER, NEUTRAL, ROLE_SPECS, TOWN, WOLVES
from Agents.ten_seat_metrics import would_have_hurt_the_pack

EVIL = (WOLVES, LONE_KILLER)
SELF = "self"
"""The Speculator's lens after picking itself: it wins only as the last one standing."""
PICKED_LENS = {"town": TOWN, "wolves": WOLVES, "lone_killer": LONE_KILLER, "self": SELF}


def side(role: str | None) -> str | None:
    spec = ROLE_SPECS.get(role or "")
    return spec.side if spec is not None else None


def majority_vote(day_res: dict) -> str | None:
    """The room's plurality vote that day (abstain included): the pack's blend reference. None if
    no vote happened. Read from vote_counts, so an abstain plurality still counts."""
    vc = day_res.get("vote_counts") or {}
    return max(vc, key=vc.get) if vc else None


def town_abstain_grade(day_res: dict | None) -> str:
    """A town abstain is graded by the day it fed: a no-lynch day is negative (a deadlock with a
    threat still votable), a day whose lynch landed is neutral; a missing row is neutral."""
    if day_res is None:
        return "neutral"
    if day_res.get("no_vote") or not day_res.get("voted_player"):
        return "negative"
    return "neutral"


def night_scope(ec: dict) -> str:
    """The pack's chat and its act (the kill and the skill) are separate lookups; every other night
    turn is one act."""
    return "chat" if (ec.get("agent_night_action") or {}).get("kind") == "chat" else "act"


def night_channel(ec: dict) -> str:
    """The base-rate channel of a night decision: a wolf's chat, kill and skill are different turn
    kinds sharing one lesson namespace, so each has its own memory-off baseline."""
    role = ec.get("player_role")
    cell = f"{role}/night_action"
    if side(role) != WOLVES:
        return cell
    kind = (ec.get("agent_night_action") or {}).get("kind")
    return f"{cell}/{kind if kind in ('chat', 'kill') else 'skill'}"


class GameView:
    """One game record, indexed for grading its decisions."""

    def __init__(self, g: dict):
        self.roles: dict[str, str] = g.get("roles") or {}
        self.side = {p: side(r) for p, r in self.roles.items()}
        self.nights = {n.get("day"): n for n in g.get("night_resolutions") or []}
        self.days = {d.get("day"): d for d in g.get("day_resolutions") or []}
        self.neutral_won = str(g.get("neutral_result") or "").startswith("won")
        self.died_night: dict[str, int] = {}
        for night in sorted(self.nights):
            for p in self.nights[night].get("deaths") or []:
                self.died_night.setdefault(p, night)
        self.lynched_day = {d["voted_player"]: day for day, d in self.days.items() if d.get("voted_player")}
        self.accused: dict[tuple[str, int], set[str]] = {}
        """(player, day) -> the players it accused that day (stance-tagged), from the day channel."""
        for m in g.get("day_channel") or []:
            for t in m.get("addressed_targets") or []:
                if t.get("stance") == "accusation" and t.get("target"):
                    self.accused.setdefault((m.get("player"), m.get("day")), set()).add(t["target"])
        self.pick: tuple[int, str] | None = None
        for night in sorted(self.nights):
            for r in self.nights[night].get("records") or []:
                if r.get("action") == "pick" and r.get("result") == "picked" and self.pick is None:
                    self.pick = (night, r.get("target"))

    # --- shared reads ---

    def _records(self, night: int) -> list[dict]:
        return (self.nights.get(night) or {}).get("records") or []

    def _own_record(self, night: int, player: str, action: str) -> dict | None:
        return next((r for r in self._records(night) if r.get("actor") == player and r.get("action") == action),
                    None)

    def _dead_entering(self, night: int) -> set[str]:
        """Dead before this night's actions: killed on an earlier night or lynched on the day before."""
        return ({p for p, n in self.died_night.items() if n < night}
                | {p for p, d in self.lynched_day.items() if d <= night})

    def _sighted(self, night: int, killer: str | None, victim: str | None) -> bool:
        """The kill was seen: a Sentinel watching the victim saw the killer at the door, or a
        Trailseer following the killer saw it go to the victim. A conceal hides the carrier's visit
        to its victim, and the record already leaves it out."""
        if killer is None or victim is None:
            return False
        for r in self._records(night):
            if r.get("result") == "roleblocked":
                continue
            role, seen = self.roles.get(r.get("actor")), r.get("seen") or []
            if role == "sentinel" and r.get("action") == "watch" and r.get("target") == victim and killer in seen:
                return True
            if role == "trailseer" and r.get("action") == "follow" and r.get("target") == killer and victim in seen:
                return True
        return False

    def _has_record_before(self, player: str, night: int) -> bool:
        return any(r.get("actor") == player for n in self.nights if n < night for r in self._records(n))

    def _will_names_a_wolf(self, player: str, night: int) -> bool:
        """Whether the player's record from earlier nights (read out at its death) points at a wolf:
        a Suspicious read, a wolf seen at a watched door or followed to a visit, a sigil or a shot on
        a wolf."""
        for n in self.nights:
            if n >= night:
                continue
            for r in self._records(n):
                if r.get("actor") != player or r.get("result") == "roleblocked":
                    continue
                action, target, seen = r.get("action"), r.get("target"), r.get("seen") or []
                if action == "investigate" and r.get("result") == "suspicious" and self.side.get(target) == WOLVES:
                    return True
                if action == "watch" and any(self.side.get(p) == WOLVES for p in seen):
                    return True
                if action in ("follow", "sigil", "shoot") and self.side.get(target) == WOLVES and (
                        action != "follow" or seen):
                    return True
        return False

    def lens(self, player: str, role: str, day: int) -> str | None:
        """The side a player's day play is graded as: its own, the Speculator's picked side once it
        has picked (a night before this day), None before then and always for the Fortune Teller."""
        s = side(role)
        if s != NEUTRAL:
            return s
        if role == "speculator" and self.pick is not None and self.pick[0] < day:
            return PICKED_LENS.get(self.pick[1])
        return None

    # --- night ---

    def pack_kill_grade(self, night: int) -> str | None:
        rec = self._own_record(night, PACK_ACTOR, "kill")
        if rec is None:
            return None
        if rec.get("result") == "roleblocked":
            return "neutral"  # a borrowed Chanteuse body blocked the carrier: not the pack's choice
        n = self.nights[night]
        carrier = next((c.get("actor") for c in n.get("choices") or []
                        if c.get("kind") == "kill" and self.side.get(c.get("actor")) == WOLVES), None)
        victim = rec.get("target")
        if self._sighted(night, carrier, victim) or rec.get("result") in ("saved", "immune"):
            return "negative"
        if rec.get("result") != "killed":
            return None
        victim_side = self.side.get(victim)
        if victim_side in (TOWN, LONE_KILLER):  # the lone killer is the rival the pack must remove
            return "positive"
        return "neutral" if victim_side == NEUTRAL else "negative"

    def night_grade(self, ec: dict) -> str | None:
        act = ec.get("agent_night_action") or {}
        kind, night, player, role = act.get("kind"), ec.get("day"), ec.get("player_id"), ec.get("player_role")
        if role == "necromancer" or night not in self.nights:
            return None
        if side(role) == WOLVES and kind in ("chat", "kill"):
            return self.pack_kill_grade(night)  # a chat lesson is graded by that night's kill (ruled)
        if kind in ("declined", "hold_fire"):
            return self._declined_grade(role, player, night)
        action = {"vigilante": "shoot"}.get(role, ROLE_SPECS[role].night_action if role in ROLE_SPECS else None)
        rec = self._own_record(night, player, action) if action else None
        if rec is None:
            return None
        if rec.get("result") == "unknown":
            return None  # a record rebuilt for a player who died that night, its result not public
        if rec.get("result") == "roleblocked":
            return "neutral"  # a blocked action spends nothing and was not the actor's choice
        grade = getattr(self, f"_grade_{role}", None)
        return grade(rec, night, player) if grade else None

    def _declined_grade(self, role: str, player: str, night: int) -> str:
        if role == "illusionist":
            rec = self._own_record(night, PACK_ACTOR, "kill")
            victim = rec.get("target") if rec else None
            landed = rec is not None and rec.get("result") == "killed"
            if landed and self.side.get(victim) == TOWN and self._will_names_a_wolf(victim, night):
                return "negative"  # the will read out a wolf the conceal could have hidden
            return "neutral"
        if role == "speculator":
            return "negative" if self._last_night_unpicked(player, night) else "neutral"
        return "neutral"

    def _last_night_unpicked(self, player: str, night: int) -> bool:
        """The Speculator never picked and this was its last night alive."""
        if self.pick is not None:
            return False
        if player in self.died_night:
            return self.died_night[player] == night
        if player in self.lynched_day:
            return self.lynched_day[player] - 1 == night
        return False

    def _grade_serial_killer(self, rec: dict, night: int, player: str) -> str | None:
        victim = rec.get("target")
        if self._sighted(night, player, victim) or rec.get("result") in ("saved", "immune"):
            return "negative"
        if rec.get("result") != "killed":
            return None
        return "neutral" if self.side.get(victim) == NEUTRAL else "positive"

    def _grade_chanteuse(self, rec: dict, night: int, player: str) -> str:
        if rec.get("result") != "blocked":
            return "neutral"  # did not take: the target is the lone killer or the neutral, and it learns so
        n = self.nights[night]
        target = rec.get("target")
        blocked = next((c for c in n.get("choices") or [] if c.get("actor") == target), None)
        if blocked is None or blocked.get("kind") == "hold_fire" or self.side.get(target) != TOWN:
            return "negative"  # nothing to cancel
        pack = self._own_record(night, PACK_ACTOR, "kill")
        night_ns = SimpleNamespace(choices=n.get("choices") or [], outcome=n.get("outcome") or {})
        critical = would_have_hurt_the_pack(blocked, night_ns, self.side, pack.get("target") if pack else None)
        return "positive" if critical else "neutral"

    def _grade_illusionist(self, rec: dict, night: int, player: str) -> str:
        if rec.get("result") != "concealed":
            return "neutral"  # the victim survived: the conceal is kept
        concealed = ((self.nights[night].get("outcome") or {}).get("concealed") or [])
        victim = concealed[0] if concealed else None
        if victim and self.side.get(victim) == TOWN and self._has_record_before(victim, night):
            return "positive"
        return "negative"  # a conceal spent on a body whose will had nothing to read out

    def _grade_investigator(self, rec: dict, night: int, player: str) -> str:
        if self.roles.get(rec.get("target")) == "serial_killer":
            return "negative"  # a false clear, and a check spent
        return "positive" if rec.get("result") == "suspicious" else "neutral"

    def _grade_sentinel(self, rec: dict, night: int, player: str) -> str:
        seen = rec.get("seen") or []
        if not seen:
            return "negative"  # a watch spent on a door no one came to
        borrowed = self._dead_entering(night)  # a dead name at the door is the Necromancer's body
        return "positive" if any(self.side.get(p) in EVIL or p in borrowed for p in seen) else "neutral"

    def _grade_trailseer(self, rec: dict, night: int, player: str) -> str:
        if not rec.get("seen"):
            return "negative"  # followed someone who went nowhere
        return "positive" if self.side.get(rec.get("target")) in EVIL else "neutral"

    def _grade_healer(self, rec: dict, night: int, player: str) -> str:
        if rec.get("result") != "saved":
            return "neutral"
        target_side = self.side.get(rec.get("target"))
        if target_side == TOWN:
            return "positive"
        return "negative" if target_side in EVIL else "neutral"

    def _grade_vigilante(self, rec: dict, night: int, player: str) -> str:
        target_side = self.side.get(rec.get("target"))
        if target_side in EVIL:
            return "positive"  # saved or immune included: the choice was right
        return "negative" if target_side == TOWN else "neutral"

    def _grade_sigilist(self, rec: dict, night: int, player: str) -> str:
        attackers = (self.nights[night].get("outcome") or {}).get("attackers") or []
        target = rec.get("target")
        if target not in attackers:
            return "negative"  # a sigil spent on someone who did not attack
        return "positive" if self.side.get(target) in EVIL else "negative"  # the Vigilante struck down

    def _grade_speculator(self, rec: dict, night: int, player: str) -> str:
        return "positive" if self.neutral_won else "negative"

    def _grade_fortune_teller(self, rec: dict, night: int, player: str) -> str:
        result = rec.get("result")
        if result == "self_bet":
            attacked = player in ((self.nights[night].get("outcome") or {}).get("attacks_on") or {})
            return "positive" if attacked else "negative"
        return "positive" if result in ("scored_1", "scored_2") else "negative"

    # --- day ---

    def vote_grade(self, player: str, role: str, day: int, votee: str | None,
                   majority: str | None = None, day_res: dict | None = None) -> str | None:
        """A vote (or the day's lynch, for discussion) graded under the player's lens."""
        lens = self.lens(player, role, day)
        if lens is None:
            return None
        abstain = not votee or votee == "abstain"
        if lens == TOWN:
            if abstain:
                return town_abstain_grade(day_res)
            return "positive" if self.side.get(votee) in EVIL else "negative"
        if lens == WOLVES:
            if majority is not None:
                return "positive" if votee == majority else "negative"  # blend with the room
            if abstain:
                return "neutral"
            return "negative" if self.side.get(votee) == WOLVES else "positive"
        if abstain:
            return "neutral"
        # the lone killer, and a Speculator betting on it or on itself: any lynch but its own side's
        own = {player} if lens == SELF or side(role) == LONE_KILLER else \
            {p for p, s in self.side.items() if s == LONE_KILLER}
        return "negative" if votee in own else "positive"

    def day_vote_grade(self, ec: dict) -> str | None:
        day = ec.get("day")
        day_res = self.days.get(day)
        return self.vote_grade(ec.get("player_id"), ec.get("player_role"), day,
                               (ec.get("agent_vote") or {}).get("votee"),
                               majority=majority_vote(day_res) if day_res else None, day_res=day_res)

    def discussion_grade(self, player: str, role: str, day: int, accused: set[str]) -> str | None:
        """A day's discussion, for a lesson followed on at least one spoken turn: its own lynch is
        negative; an accusation of the lynched player (on a followed turn) is graded on the target;
        otherwise the day's lynch is graded as if it were the player's vote."""
        lens = self.lens(player, role, day)
        if lens is None:
            return None
        lynched = (self.days.get(day) or {}).get("voted_player")
        if lynched and lynched == player:
            return "negative"
        if lynched and lynched in accused:
            if lens != TOWN:
                return "positive"  # a landed push advances an evil or a betting player
            return "positive" if self.side.get(lynched) in EVIL else "read_excluded"
        return self.vote_grade(player, role, day, lynched)

    def observation_grade(self, role: str, phase: str, day: int, pack_turn: str = "none") -> str | None:
        """The grade of the decision an extracted observation names (its role, phase, and
        ``decision_day``/``pack_turn``; decisions §13). None when the observation names no single
        decision (day 0, untagged -1, a wolf's "several") or the record holds no such decision."""
        holder = next((p for p, r in self.roles.items() if r == role), None)
        if holder is None or day is None or day <= 0:
            return None
        if phase == "day_vote":
            day_res = self.days.get(day) or {}
            votee = next((v.get("votee") for v in day_res.get("votes") or [] if v.get("voter") == holder), None)
            if votee is None:
                return None
            return self.vote_grade(holder, role, day, votee, majority=majority_vote(day_res), day_res=day_res)
        if phase == "day_discussion":
            grade = self.discussion_grade(holder, role, day, self.accused.get((holder, day), set()))
            return None if grade == "read_excluded" else grade  # credit's exclusion, not a grade
        if phase != "night_action" or day not in self.nights:
            return None
        if side(role) == WOLVES:
            if pack_turn in ("chat", "kill"):
                kind = pack_turn
            elif pack_turn == "skill":
                kind = ROLE_SPECS[role].night_action if self._own_record(
                    day, holder, ROLE_SPECS[role].night_action) else "declined"
            else:
                return None
        else:
            own = next((r for r in self._records(day) if r.get("actor") == holder), None)
            kind = "declined" if own is None else ("hold_fire" if own.get("action") == "hold_fire" else
                                                   ROLE_SPECS[role].night_action)
        return self.night_grade({"player_id": holder, "player_role": role, "day": day,
                                 "agent_night_action": {"kind": kind}})

    def decision_grade(self, ec: dict) -> str | None:
        """The grade of one vote or night decision; None = not graded."""
        phase = ec.get("action_phase")
        if phase == "day_vote" and ec.get("agent_vote"):
            return self.day_vote_grade(ec)
        if phase == "night_action" and ec.get("agent_night_action"):
            return self.night_grade(ec)
        return None
