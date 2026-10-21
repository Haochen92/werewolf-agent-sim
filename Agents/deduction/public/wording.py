"""Every sentence of the public rows (level 5, catalogue Table B), in one place, so the same fact
is always worded the same way. The rules for the wording are in the catalogue (§0 "Form"): name
players and nights, use plain verbs, end at the conclusion, and keep any hedge on the same line.
A will's clause reuses the level-1 sentence (Agents/deduction/wording.py), worded with the dead
holder's name; only its opening and the roleblock are here.
"""

from __future__ import annotations

from Agents.deduction.wording import BORROWED_VERB, ROLE_TITLES, immune_roles_phrase

# --- who went to an attacked player (B1–B5, B11, B33) -------------------------------------------

VISITOR = {
    "wolves": ("A wolf", "attack"),
    "serial_killer": ("The Serial Killer", "attack"),
    "vigilante": ("The Vigilante", "shoot"),
    "sigilist": ("The Sigilist", "set a sigil on"),
}
"""Who made an announced attack under their own name, and what they did."""


def went_there_and_was_shown(doer: str, target: str, night: int) -> str:
    who, verb = VISITOR[doer]
    return (f"{who} went to {target} on night {night} to {verb} them, and a watch on {target} that night "
            "would have shown that visit.")


def healer_went_there(target: str, night: int) -> str:
    return (f"The living Healer protected {target} on night {night}: it was alive and not roleblocked that "
            f"night, and a watch on {target} would have shown its visit.")


def killer_went_there_unseen(target: str, night: int) -> str:
    return (f"The wolf who killed {target} on night {night} went to {target} unseen: the living "
            "Illusionist's conceal hides that visit from every watch and follow.")


def illusionist_was_alive(target: str, night: int) -> str:
    return (f"{target}'s role was hidden by the living Illusionist, so the Illusionist was alive at the start "
            f"of night {night} and went to {target} that night.")


def no_protection(target: str, night: int) -> str:
    return f"No protection went ahead on {target} on night {night}: one would have saved {target}."


# --- the Necromancer's one action through a body (B6–B9, B12) -----------------------------------

def necromancer_attacked_through_body(target: str, night: int, body: str, body_role: str) -> str:
    return (f"The Necromancer attacked {target} on night {night} through {body}'s body "
            f"({ROLE_TITLES[body_role]}): it was alive that night, and a kill through a body makes it read "
            "Suspicious that night. It acts once a night, so it did nothing else.")


def necromancer_sigil_through_body(target: str, night: int, body: str) -> str:
    return (f"The Necromancer set a sigil on {target} on night {night} through {body}'s body (the Sigilist): "
            "it acts once a night, so it made no kill and read Not suspicious that night.")


def necromancer_protected_through_body(target: str, night: int, body: str) -> str:
    return (f"The Necromancer protected {target} on night {night} through {body}'s body (the Healer): it "
            "acts once a night, so it made no kill and read Not suspicious that night.")


def conceals_used_up(target: str) -> str:
    # Only after a kill through the dead Illusionist's body, which hides the role while a conceal is left.
    return (f"{target} was killed through the dead Illusionist's body and their role was not hidden, so the "
            "Illusionist's conceals are used up: no death will be hidden again.")


def reanimated_conceal_hides_no_visit(target: str, night: int) -> str:
    return (f"{target}'s role was hidden through the dead Illusionist's body, which hides no visit: every "
            f"visit to {target} on night {night} would have shown on a watch or a follow.")


# --- what an attacked player can be (B2, B7, B9–B12, B33) ---------------------------------------

def killed_so_not_immune(target: str, roles: list[str]) -> str:
    return f"{target} was killed at night, so {target} is not {immune_roles_phrase(roles)}."


def saved_so_not_immune(target: str, roles: list[str]) -> str:
    return (f"A protection saved {target}, so {target} could be killed that night: {target} is not "
            f"{immune_roles_phrase(roles)}.")


def healer_cannot_protect_itself(target: str) -> str:
    return f"The Healer cannot protect itself, so {target} is not the Healer."


def attacked_by_wolves_so_not_a_wolf(target: str) -> str:
    return f"The wolves attacked {target}, so {target} is not a wolf."


def shot_by_vigilante_so_not_vigilante(target: str) -> str:
    return f"The Vigilante shot at {target}, so {target} is not the Vigilante."


def acted_on_through_body_so_not_necromancer(target: str) -> str:
    return (f"The Necromancer acted on {target} through a body, and it cannot act on itself, so {target} is "
            "not the Necromancer.")


def struck_by_sigil_so_attacker(target: str, wolf: bool, vigilante: bool, dead: str = "") -> str:
    """`dead`: "" or the reason a candidate is gone ("the Vigilante is dead")."""
    if wolf and vigilante:
        who = "a wolf or the Vigilante"
    elif wolf:
        who = "a wolf"
    else:
        who = "the Vigilante"
    reason = f", since {dead}" if dead else ""
    return ("A sigil strikes back only at a player who attacked someone in their own name that night, so "
            f"{target} is {who}{reason}.")


def survived_on_own_self_bet(target: str, night: int) -> str:
    return (f"{target} survived on their own self-bet, so {target} is the Fortune Teller and bet on "
            f"themselves on night {night}.")


# --- the attacker a sigil struck (B5, B10) --------------------------------------------------------

def wolf_struck_by_sigil_carried(target: str, night: int) -> str:
    return (f"A wolf is struck by a sigil only when it carries the pack's kill, so {target} carried the "
            f"pack's kill on night {night}.")


def vigilante_struck_by_sigil_shot(target: str, night: int) -> str:
    return (f"The Vigilante is struck by a sigil only when it shoots, so {target} shot someone on night "
            f"{night}.")


SILENT_ATTACKER = {"wolves": ("attack by the wolves", "the pack's target"),
                   "vigilante": ("shot by the Vigilante", "the Vigilante's target")}


def attack_made_but_not_announced(attacker_type: str, night: int, roles: list[str]) -> str:
    attack, target = SILENT_ATTACKER[attacker_type]
    return (f"No {attack} was announced on night {night}, so {target} could not be killed: it was "
            f"{immune_roles_phrase(roles)}.")


# --- absences (B13, B14) --------------------------------------------------------------------------

def pack_attack_silent(night: int, roles: list[str]) -> str:
    return (f"A wolf was alive at the start of night {night}, and the wolves must attack every night, but no "
            f"attack by the wolves was announced: their target could not be killed, so it was "
            f"{immune_roles_phrase(roles)}.")


def pack_carrier_blocked_through_body(night: int) -> str:
    return (f"A wolf was alive at the start of night {night}, and the wolves must attack every night, but no "
            "attack by the wolves was announced: the Chanteuse was already dead, so the Necromancer blocked "
            "the wolf carrying the kill through her body.")


def pack_attack_silent_or_blocked(night: int, roles: list[str]) -> str:
    return (f"A wolf was alive at the start of night {night}, and the wolves must attack every night, but no "
            f"attack by the wolves was announced: either their target could not be killed, so it was "
            f"{immune_roles_phrase(roles)}, or the Necromancer blocked the wolf carrying the kill through "
            "the dead Chanteuse's body.")


def no_one_died(night: int, roles: list[str]) -> str:
    if not roles:
        return f"No one died and no one was saved on night {night}, so no attack went ahead that night."
    return (f"No one died and no one was saved on night {night}, so every attack that night, if any, was on a "
            f"player who could not be killed: {immune_roles_phrase(roles)}.")


# --- the roster and the pick (B25–B27) ------------------------------------------------------------

SIDE_WORDS = {"town": "Town", "wolves": "the Wolves", "lone_killer": "the lone killer", "self": "itself"}


def body_usable_from(player: str, day: int, role: str) -> str:
    return (f"{player} was voted out on day {day} as {ROLE_TITLES[role]}, so from night {day} on the "
            f"Necromancer can use {player}'s body to {BORROWED_VERB[role]} someone.")


def speculator_picked(side: str, night: int) -> str:
    return (f"The Speculator picked {SIDE_WORDS.get(side, side)} on night {night}, so it was alive at the "
            "start of that night, and it will not pick again.")


def speculator_never_picked(player: str) -> str:
    return f"{player} was the Speculator and never picked a side, so it has lost."


# --- the read-out wills (B15–B24, B32) ------------------------------------------------------------

def will_shows(holder: str, night: int, deed: str) -> str:
    return f"{holder}'s will shows that on night {night} {holder} {deed}."


def holder_blocked_by_living_chanteuse(holder: str) -> str:
    return (f"Only the Chanteuse could roleblock that night, and a block is a visit, so the Chanteuse, a wolf, "
            f"came to {holder} that night.")


def holder_blocked_through_chanteuse_body(holder: str) -> str:
    return (f"The Chanteuse was already dead, so the Necromancer blocked {holder} through her body; a watch on "
            f"{holder} would have shown the Chanteuse's name, not the Necromancer's.")


def holder_held_fire(holder: str) -> str:
    return f"So {holder} shot no one that night."


def will_has_nothing_for(holder: str, night: int) -> str:
    return (f"{holder}'s will has nothing for night {night}, so {holder} made no choice that night: it used "
            "no ability and went to no one.")


def revealed_with_nothing_on_record(holder: str, role: str, night: int) -> str:
    return (f"{holder} was revealed as {ROLE_TITLES[role]} with nothing on record, so {holder} made no choice "
            f"on night {night}: it used no ability and went to no one.")
