"""Every sentence of the claim comparisons (slice 11: catalogue Table E, F3's claim status, F7's note
for an evil seat), in one place, so the same comparison is always worded the same way.

The rules are the catalogue's (§0 "Form", Table E "What a comparison can say"): a line names the
players and the night; two claims that disagree "cannot both be true", never which one is false; a
claim is called false only against an engine source (the seat's own record, a will, the morning,
the roster) or what the seat knows for certain; a false claim is never said to prove a role; a line
that rests on a claim opens with it ("If …").
"""

from __future__ import annotations

from Agents.deduction.joins.wording import DEED
from Agents.deduction.wording import ROLE_TITLES

DOES = {"investigate": "checks", "protect": "protects", "watch": "watches", "follow": "follows",
        "shoot": "shoots at", "sigil": "sets a sigil on"}
"""What a role's one action a night does, in the present (a player who does it visits no one else)."""


def _joined(names: list[str], last: str) -> str:
    if len(names) == 1:
        return names[0]
    return f"{', '.join(names[:-1])} {last} {names[-1]}"


def title(role: str) -> str:
    return ROLE_TITLES[role]


class Names:
    """Players as the seat reads them: itself as "you"."""

    def __init__(self, seat: str):
        self.seat = seat

    def __call__(self, player: str) -> str:
        return "you" if player == self.seat else player


def when(night: int, first: bool) -> str:
    """"on night 2" the first time a line names the night, "that night" after."""
    if night <= 0:
        return ""
    return f"on night {night}" if first else "that night"


def _at(text: str, night_words: str) -> str:
    return f"{text} {night_words}".rstrip()


# --- a claim, as a clause -----------------------------------------------------------------------

def sighting(n: Names, claimant: str, how: str, visitor: str, target: str, night_words: str) -> str:
    """A claimed watch or follow that saw a visit: "player_2 says player_7 came to player_5 on night 1"."""
    verb = "came to" if how == "watch" else "went to"
    return _at(f"{claimant} says {n(visitor)} {verb} {n(target)}", night_words)


def own_visit(n: Names, claimant: str, action: str, target: str, night_words: str) -> str:
    """A claimant's own action: "player_7 says it protected player_5 on night 1"."""
    return _at(f"{claimant} says it {DEED[action]} {n(target)}", night_words)


def roleblocked(claimant: str, night_words: str) -> str:
    return _at(f"{claimant} says it was roleblocked", night_words)


def saw_no_one_come(n: Names, claimant: str, target: str, night_words: str) -> str:
    """A claimed watch that saw no one (AC4, line 5)."""
    return _at(f"{claimant} says no one came to {n(target)}", night_words)


def saw_visit_no_one(n: Names, claimant: str, followed: str, night_words: str) -> str:
    """A claimed follow that saw the followed player visit no one."""
    return _at(f"{claimant} says {n(followed)} visited no one", night_words)


def visited_no_one(claimant: str, night_words: str) -> str:
    """A player's own denial (AC3, line 3): "player_6 says it visited no one on night 2"."""
    return _at(f"{claimant} says it visited no one", night_words)


def did_not_go_to(n: Names, claimant: str, target: str, night_words: str) -> str:
    return _at(f"{claimant} says it did not go to {n(target)}", night_words)


# --- an engine source, as the evidence of a line --------------------------------------------------

def _holder_shows(holder: str | None) -> str:
    return "" if holder is None else f"{holder}'s will shows "


def you_did(n: Names, holder: str | None, action: str, target: str) -> str:
    """The seat's (or a will's holder's) own action that went ahead: "you checked player_3 that night"."""
    who = "you" if holder is None else holder
    return f"{_holder_shows(holder)}{who} {DEED[action]} {n(target)} that night"


def you_saw(n: Names, holder: str | None, how: str, visitor: str, target: str) -> str:
    """A visit the seat's (or a will's) watch or follow saw: "your watch saw player_7 come to player_3
    that night"."""
    whose = "your" if holder is None else f"{holder}'s"
    verb = "come to" if how == "watch" else "go to"
    return f"{_holder_shows(holder)}{whose} {how} saw {n(visitor)} {verb} {n(target)} that night"


def you_were_blocked(holder: str | None) -> str:
    """A roleblock is a visit to the blocked player (catalogue L3)."""
    if holder is None:
        return "you were roleblocked that night, and a block is a visit to you"
    return f"{holder}'s will shows {holder} was roleblocked that night, and a block is a visit to {holder}"


def watch_saw_everyone(n: Names, holder: str | None, target: str, missing: str) -> str:
    """An engine watch's whole list (catalogue L12: every visitor but the watcher's own)."""
    whose = "your" if holder is None else f"{holder}'s"
    watcher = "you" if holder is None else holder
    return (f"{_holder_shows(holder)}{whose} watch on {n(target)} saw everyone who came to {n(target)} that night "
            f"but {watcher}, and {missing}")


def follow_saw_everywhere(n: Names, holder: str | None, followed: str, missing: str) -> str:
    """An engine follow's whole list: every place the followed player went that night."""
    whose = "your" if holder is None else f"{holder}'s"
    return (f"{_holder_shows(holder)}{whose} follow of {n(followed)} saw everywhere {n(followed)} went that night, "
            f"and {missing}")


def not_among(n: Names, player: str) -> str:
    return f"{n(player)} was not among them"


def no_blocker_among() -> str:
    return "no one among them could have made a roleblock"


def you_did_not_go(n: Names, target: str) -> str:
    """The seat's own movements: it knows every visit it made."""
    return f"you did not go to {n(target)} that night"



# --- the conclusions -----------------------------------------------------------------------------

def is_false(claim: str, evidence: str, kind: str = "report") -> str:
    """An engine source against a claim: "…, but your watch …: that report is false."."""
    return f"{claim}, but {evidence}: that {kind} is false."


def cannot_both(first: str, second: str, reason: str | None = None) -> str:
    """Two claims that disagree: never which one is false."""
    return f"{first}, and {second}. {reason + ' ' if reason else ''}The two cannot both be true."


def blocked_goes_nowhere() -> str:
    return "A roleblocked player's action does not go ahead."


def one_visit_a_night(action: str) -> str:
    """E2a for a role that makes one visit a night."""
    return f"A player who {DOES[action]} a player goes nowhere else that night."


def only_if_chanteuse(visitor: str) -> str:
    """E2a (catalogue wording): two places in one night."""
    return (f"These can both be true only if {visitor} visited two players that night, which only the Chanteuse "
            f"does when she carries the pack's kill.")


def not_the_chanteuse(visitor: str) -> str:
    return f"Only the Chanteuse visits two players in one night, and {visitor} cannot be the Chanteuse."


def two_places_false(evidence: str, claim: str, reason: str) -> str:
    """E2a against an engine sighting: the claimant's own action elsewhere that night is false."""
    return f"{evidence}, and {claim}. {reason} So that claim is false."


def agree(first: str, second: str, visitor: str, bare: bool) -> str:
    """E1: a sighting and the visitor's own word agree; neither shows the action."""
    hedge = (f"neither shows which action {visitor} took" if bare
             else f"the sighting does not show which action {visitor} took")
    return f"{first}, and {second}. These agree; {hedge}."


def directions(outgoing: str, player: str, incoming_source: str) -> str:
    """E17 (AC3, line 3): where a player went and who came to it are different questions."""
    return (f"{outgoing}. That is about where {player} went. {incoming_source} is about who came to {player}. "
            f"The two do not conflict.")


def no_one_came_is_not_inaction(claim: str, target: str) -> str:
    """E17 (AC4, line 5)."""
    return f"{claim}. That is about who came to {target}, not about whether {target} acted."


def incoming_source(n: Names, claimant: str | None, holder: str | None) -> str:
    """Whose watch: "player_9's watch", "Your watch", "player_4's watch"."""
    if claimant is not None:
        return f"{claimant}'s watch"
    if holder is None:
        return "Your watch"
    return f"{holder}'s watch"


def only_blocker(n: Names, player: str) -> str:
    """The suffix when one name alone could have made a roleblock (the known Chanteuse, or her body)."""
    return f", and only {n(player)} could have made a roleblock that night"


def only_blocker_sentence(n: Names, player: str) -> str:
    name = n(player)
    return f"Only {name} could have made a roleblock that night." if name != "you" else "Only you could have made a roleblock that night."


# --- claims against the record (E4, E7, E8, E9, E11, E14, E6) -------------------------------------

def protection_went_ahead_but_died(claimant: str, target: str, night: int) -> str:
    """E4b."""
    return (f"{claimant} says its protection of {target} went ahead on night {night}, but {target} died that "
            f"night, and a protection that goes ahead stops every attack: that claim is false.")


def reading_word(suspicious: bool) -> str:
    return "Suspicious" if suspicious else "Not suspicious"


def check_reading_false(n: Names, claimant: str, target: str, night: int, suspicious: bool, reason: str) -> str:
    """E7."""
    return (f"{claimant} says {n(target)} read {reading_word(suspicious)} on night {night}, but {reason}: that "
            f"claim is false.")


def revealed_reads(target: str, role: str, suspicious: bool) -> str:
    return f"{target} was revealed as {title(role)}, who reads {reading_word(suspicious)}"


def you_read(role: str, suspicious: bool) -> str:
    return f"you are {title(role)}, who reads {reading_word(suspicious)}"


def packmate_reads(target: str, role: str) -> str:
    return f"your packmate {target} is {title(role)}, a wolf, who reads Suspicious"


def can_only_be_reads(target: str, roles: list[str], suspicious: bool) -> str:
    named = _joined([title(role) for role in roles], "or")
    return f"{target} can only be {named}, and none of them read {reading_word(suspicious)} that night"


def no_shot_announced(target: str) -> str:
    return f"no shot at {target} was announced that night"


def shot_went_ahead_false(claimant: str, target: str, night: int, killed: bool, silent: list[str] = ()) -> str:
    """E8b with no role left to the target that a shot fails on in silence (`silent`: those roles in
    this cast that night), or a claimed kill with no shot announced."""
    said = f"its shot killed {target}" if killed else f"its shot at {target} went ahead"
    if killed:
        extra = ""
    elif silent:
        named = _joined([title(role) for role in silent], "or")
        extra = f", and {target} cannot be {named}, the only role a shot fails on without an announcement"
    else:
        extra = ", and every shot that went ahead that night was announced"
    return f"{claimant} says {said} on night {night}, but {no_shot_announced(target)}{extra}: that claim is false."


def sigil_struck_false(claimant: str, target: str, night: int) -> str:
    """E9."""
    return (f"{claimant} says its sigil struck {target} down on night {night}, but no sigil killed {target} that "
            f"night: that claim is false.")


def too_many_uses(claimant: str, action: str, nights: list[int], role: str, uses: int) -> str:
    """E11."""
    noun = {"investigate": "checks", "watch": "watches", "sigil": "sigils"}[action]
    did = {"investigate": "checked a player", "watch": "watched a player", "sigil": "set a sigil"}[action]
    listed = _joined([str(night) for night in nights], "and")
    return (f"{claimant} says it {did} on nights {listed}, but {title(role)} has {uses} {noun} for the whole "
            f"game: {claimant} cannot have made them all as {title(role)}.")


def death_words(phase: str, day: int) -> str:
    return f"killed on night {day}" if phase == "night" else f"voted out on day {day}"


def target_already_dead(claim: str, target: str, how: str) -> str:
    """E14: no action goes to the dead."""
    return f"{claim}, but {target} was already dead by then ({how}): that claim is false."


def visitor_already_dead(claim: str, visitor: str, how: str, necromancer: bool) -> str:
    """E14: a dead name visits only as the Necromancer's body, and that body could not be used (or the
    cast has no Necromancer)."""
    why = (f"the Necromancer could not act through {visitor}'s body that night" if necromancer
           else "no one visits in a dead player's name in this game")
    return f"{claim}, but {visitor} was already dead by then ({how}), and {why}: that report is false."


def no_blocker_left(claim: str, chanteuse: str, how: str) -> str:
    """E14: the Chanteuse dead, in a cast with no Necromancer to block through her body."""
    return (f"{claim}, but the Chanteuse, {chanteuse}, was already dead by then ({how}), and no one else can "
            f"roleblock in this game: that claim is false.")


def self_protection(claimant: str, night: int) -> str:
    """E14."""
    return f"{claimant} says it protected itself on night {night}, but the Healer cannot protect itself: that claim is false."


def unblockable(claimant: str, role: str, night: int) -> str:
    """E6."""
    when_ = f" on night {night}" if night > 0 else ""
    return (f"{claimant} claims {title(role)} and says it was roleblocked{when_}, but {title(role)} cannot be "
            f"roleblocked: the two claims cannot both be true.")


# --- claim status (E15, F3's other half) and role claims ------------------------------------------

def no_one_else_claims(roles: list[str]) -> str:
    """AC4, line 3: "No one else claims the Sentinel."."""
    return f"No one else claims {_joined([title(role) for role in roles], 'or')}."


def counter_claim(n: Names, players: list[str], role: str) -> str:
    """E15: "player_3 and player_8 both claim the Healer; at most one holds it."."""
    ordered = sorted(players, key=lambda p: p != n.seat)
    names = [n(p) for p in ordered]
    names[0] = names[0][0].upper() + names[0][1:] if names[0] == "you" else names[0]
    both = "both" if len(players) == 2 else "all"
    return f"{_joined(names, 'and')} {both} claim {title(role)}; at most one holds it."


def withdrew(player: str, role: str, claimed_day: int, withdrawn_day: int) -> str:
    """E15: "player_8 claimed the Healer on day 2 and withdrew it on day 3."."""
    return f"{player} claimed {title(role)} on day {claimed_day} and withdrew it on day {withdrawn_day}."


_KEPT_DEED = {"held_fire": "held fire", "kept_check": "kept a check", "kept_watch": "kept a watch",
              "kept_sigil": "kept a sigil"}


def implied_claim(n: Names, claimant: str, actions: list[tuple[str, str, str, int]], role: str) -> str:
    """An implied role claim: "player_7 names no role, but says it held fire on nights 1 and 2, which
    is the Vigilante's action: this reads as a claim to be the Vigilante." ``actions`` are (action,
    result, target, night), in night order."""
    deeds: dict[str, list[int]] = {}
    for action, result, target, night in actions:
        deed = _KEPT_DEED[result] if action == "no_action" else f"{DEED[action]} {n(target)}".rstrip()
        deeds.setdefault(deed, [])
        if night > 0 and night not in deeds[deed]:
            deeds[deed].append(night)
    said = []
    for deed, nights in deeds.items():
        if not nights:
            said.append(deed)
        elif len(nights) == 1:
            said.append(f"{deed} on night {nights[0]}")
        else:
            said.append(f"{deed} on nights {_joined([str(night) for night in nights], 'and')}")
    whose = "action" if len(deeds) == 1 else "actions"
    return (f"{claimant} names no role, but says it {_joined(said, 'and')}, which is {title(role)}'s {whose}: "
            f"this reads as a claim to be {title(role)}.")


def no_role_claim(players: list[str]) -> str:
    verb = "has" if len(players) == 1 else "have"
    return f"{_joined(players, 'and')} {verb} made no role claim."


def role_claim_false(player: str, role: str, reason: str, implied: bool = False) -> str:
    if implied:  # the player named no role: its claimed actions did
        return f"{player}'s claimed night actions are {title(role)}'s, but {reason}: that claim is false."
    return f"{player} claims {title(role)}, but {reason}: that claim is false."


def not_in_cast(role: str) -> str:
    return f"{title(role)} is not in this game"


def revealed_as(players: list[str], role: str) -> str:
    verb = "was" if len(players) == 1 else "were"
    return f"{_joined(players, 'and')} {verb} revealed as {title(role)}"


def you_are(role: str) -> str:
    return f"you are {title(role)}"


def packmate_is(player: str, role: str) -> str:
    return f"your packmate {player} is {title(role)}"


def can_only_be(player: str, roles: list[str]) -> str:
    if len(roles) == 1:
        return f"{player} can only be {title(roles[0])}"
    return f"{player} can only be {_joined([title(role) for role in roles], 'or')}"


_HELD = {"held_fire": "held fire", "kept_check": "kept your check", "kept_watch": "kept your watch",
         "kept_sigil": "kept your sigil"}


def _story(deeds: list[tuple[int, str, str, str]]) -> str:
    """A cover's nights: "you checked player_10 on night 1 and kept your check on night 2"."""
    nights: dict[tuple[str, str], list[int]] = {}  # the same deed on two nights is said once
    for night, action, target, result in deeds:
        if action == "no_action":
            deed, after = _HELD[result], ""
        else:
            deed = f"{DEED[action]} {target}"
            after = {"saved_from_attack": " and saved them", "suspicious": ", who read Suspicious",
                     "not_suspicious": ", who read Not suspicious"}.get(result, "")
        nights.setdefault((deed, after), []).append(night)
    parts = [f"{deed} on {'night' if len(on) == 1 else 'nights'} {_joined([str(x) for x in on], 'and')}{after}"
             for (deed, after), on in nights.items()]
    return "you " + _joined(parts, "and")


def covers(n: Names, fitting: list[tuple[str, list]], countered: list[tuple[str, list, list[str], list[str]]],
           reported: dict[int, list[str]], others_fail: bool = False) -> str:
    """Slice 14 (R11): "player_3 says it saw your visit on night 1. Stories that fit your nights and
    every claim so far: as the Investigator, you checked player_10 on night 1 and kept your check on
    night 2. A Trailseer story fits too (you followed player_10 on night 1), but player_3 claims the
    Trailseer: claiming it starts a counter-claim."."""
    sentences = [f"{_joined(players, 'and')} {'says it' if len(players) == 1 else 'say they'} saw your visit on night {night}."
                 for night, players in sorted(reported.items())]
    if fitting:
        told = "; ".join(f"as {title(role)}, {_story(deeds)}" for role, deeds in fitting)
        sentences.append(f"Stories that fit your nights and every claim so far: {told}.")
    for role, deeds, claimants, packmates in countered:
        who = " and ".join(f"your packmate {player}" if player in packmates else player for player in claimants)
        verb = "claims" if len(claimants) == 1 else "claim"
        story = title(role).removeprefix("the ")
        sentences.append(f"A {story} story fits too ({_story(deeds)}), but {who} {verb} {title(role)}: claiming it "
                         f"starts a counter-claim.")
    if others_fail:
        sentences.append("No other town role you can claim has a story that fits these nights.")
    return " ".join(sentences)


def claimable(roles: list[str], unclaimed: list[str]) -> str:
    """F7's note for an evil seat (owner, 2026-10-16): the town and neutral roles the public record
    still allows it, and which of them no living player claims now (coordinator, 2026-10-17)."""
    if not roles:
        return "The public record already rules out every town and neutral role for you."
    text = f"You can claim {_joined([title(role) for role in roles], 'or')} without contradicting the public record"
    if len(unclaimed) == len(roles):
        return text + ("; no one has claimed it yet." if len(roles) == 1 else "; no one has claimed any of them yet.")
    if not unclaimed:
        return text + ("; it is already claimed." if len(roles) == 1 else "; every one of them is already claimed.")
    return text + f"; no one has claimed {_joined([title(role) for role in unclaimed], 'or')} yet."


# --- an evil seat's own nights (owner, 2026-10-17: certain facts about what a claim would meet) ---

def hidden_role_claim(body: str, role: str, source: str) -> str:
    """A body's role hidden from the public, from the seat's own record: no living player holds it.
    Not "only you know it": a Fortune Teller's bet that named the role, or a seat's own deductions,
    can show it too."""
    return (f"{body}'s hidden role was {title(role)}: {source} shows it, and the public record does not. No living "
            f"player holds {title(role)}, so if you claim it, no one can counter-claim you truthfully.")


def pack_kill_record(night: int) -> str:
    return f"your pack's kill record of night {night}"


def own_record(night: int) -> str:
    return f"your record of night {night}"


def own_protection_false(target: str, night: int) -> str:
    """E4b, on a protection the seat could claim at a door its own visit went to."""
    return (f"On night {night} you went to {target}, and {target} died that night: a claim that you protected "
            f"{target} then would be false, since a protection that goes ahead stops every attack.")


def own_dead_targets(dead: list[tuple[str, str]], night: int) -> str:
    """E14, on an action the seat could claim on a player already dead when the night began; `dead`
    is each player with how it died ("voted out on day 2")."""
    if len(dead) == 1:
        player, how = dead[0]
        return (f"{player} was already dead when night {night} began ({how}): a claim that you checked, watched, "
                f"followed or protected {player} on night {night} would be false.")
    names = _joined([player for player, _ in dead], "and")
    hows = ", ".join(f"{player} {how}" for player, how in dead)
    which = "either" if len(dead) == 2 else "any"
    return (f"{names} were already dead when night {night} began ({hows}): a claim that you checked, watched, "
            f"followed or protected {which} of them on night {night} would be false.")


def own_two_visits(first: str, second: str, night: int) -> str:
    """E2a's rule on the Chanteuse's own night: the pack's kill and a block elsewhere (L4)."""
    return (f"On night {night} you went to {first} and {second}, and neither visit was hidden: a follow of you that "
            f"night, or a watch on each of them, shows two visits, and only the Chanteuse visits two players in a "
            f"night.")
