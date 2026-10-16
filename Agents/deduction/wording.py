"""Every sentence the engine writes, in one place, so the same fact is always worded the same way.

The modules that decide what is true call these; none of them builds a sentence itself. The rules
for the wording are in the catalogue (§0 "Form"): name players and nights, use plain verbs, end at
the conclusion, and keep any hedge on the same line.
"""

from __future__ import annotations

ROLE_TITLES = {
    "serial_killer": "the Serial Killer",
    "necromancer": "the Necromancer",
    "fortune_teller": "the Fortune Teller",
    "vigilante": "the Vigilante",
    "healer": "the Healer",
    "chanteuse": "the Chanteuse",
}


def _immune_role_phrase(role: str) -> str:
    """How an immune role is named in a line about immunity."""
    if role == "fortune_teller":
        return "the Fortune Teller betting on itself that night"
    if role == "necromancer":
        return "the Necromancer (it cannot be killed on night 1)"
    return ROLE_TITLES[role]


def immune_roles_phrase(roles: list[str]) -> str:
    """"the Serial Killer, or the Fortune Teller betting on itself that night"."""
    return ", or ".join(_immune_role_phrase(role) for role in roles)


# --- the roleblock (A6, A7, A8) ----------------------------------------------------------------

def blocked_by_living_chanteuse() -> str:
    return ("You were roleblocked: your action was not carried out. Only the Chanteuse could "
            "roleblock that night, and a block is a visit, so the Chanteuse, a wolf, came to you "
            "that night.")


def blocked_through_chanteuse_body() -> str:
    return ("You were roleblocked: your action was not carried out. The Chanteuse was already dead, "
            "so the Necromancer blocked you through her body; a watcher at your door would have seen "
            "the Chanteuse's name, not the Necromancer's.")


def pack_carrier_blocked_through_chanteuse_body() -> str:
    return ("The pack's carrier was roleblocked: the kill did not happen. The Chanteuse was already "
            "dead, so the Necromancer blocked the carrier through her body.")


# --- attacks that met immunity (A13–A19) ------------------------------------------------------

def target_is_the_only_immune_role(target: str, role: str) -> str:
    if role == "fortune_teller":
        return (f"Only the Fortune Teller betting on itself could survive that attack, so {target} is "
                f"the Fortune Teller and bet on itself that night.")
    return (f"Only {_immune_role_phrase(role)} could survive that attack, so {target} is "
            f"{ROLE_TITLES[role]}.")


def target_is_one_of_the_immune_roles(target: str, roles: list[str]) -> str:
    return f"{target} could not be killed that night: {target} is {immune_roles_phrase(roles)}."


# --- saves (A1, A11, A12) ---------------------------------------------------------------------

def saved_target_can_be_killed(target: str, roles_ruled_out: list[str]) -> str:
    titles = " or ".join(ROLE_TITLES[role] for role in roles_ruled_out)
    return f"{target} can be killed at night, so {target} is not {titles}."


def saved_by_necromancer_through_healer_body(target: str) -> str:
    return ("A reanimated healer is the Necromancer acting through the dead Healer's body: the "
            f"Necromancer protected {target} that night.")


def attacked_by_wolves_so_not_a_wolf(target: str) -> str:
    return f"The wolves attacked {target}, so {target} is not a wolf."


def struck_by_sigil_so_attacked_in_own_name(target: str) -> str:
    return ("A sigil strikes back only at a player who attacked someone in their own name that "
            f"night, so {target} is a wolf or the Vigilante.")


def attacked_by_wolves_and_sigil_so_vigilante(target: str) -> str:
    return (f"The wolves attacked {target} and a sigil struck back at {target}, so {target} attacked "
            f"someone in their own name that night and is not a wolf: {target} is the Vigilante.")


# --- no attack on the protected player (A2–A5, A48) -------------------------------------------

def no_attack_reached(target: str) -> str:
    return f"No attack reached {target} that night."


def no_attack_reached_or_immune(target: str, roles: list[str]) -> str:
    return (f"Either no attack reached {target} that night, or {target} could not be killed: "
            f"{target} would then be {immune_roles_phrase(roles)}.")
