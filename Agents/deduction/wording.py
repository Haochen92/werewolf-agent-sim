"""Every sentence the engine writes, in one place, so the same fact is always worded the same way.

The modules that decide what is true call these; none of them builds a sentence itself. The rules
for the wording are in the catalogue (§0 "Form"): name players and nights, use plain verbs, end at
the conclusion, and keep any hedge on the same line.
"""

from __future__ import annotations

from Agents.schemas.role_traits import ROLE_TRAITS

ROLE_TITLES = {role: traits.title for role, traits in ROLE_TRAITS.items()}


def _immune_role_phrase(role: str) -> str:
    """How an immune role is named in a line about immunity."""
    if ROLE_TRAITS[role].night_immune == "first_nights":
        return f"{ROLE_TITLES[role]} (it cannot be killed on nights 1 and 2)"
    return ROLE_TITLES[role]


def immune_roles_phrase(roles: list[str]) -> str:
    """The immune roles, joined with "or": "the Serial Killer"."""
    return ", or ".join(_immune_role_phrase(role) for role in roles)


# --- the roleblock (A6, A7, A8) ----------------------------------------------------------------

# What the seat tried, named, since this line replaces the record's own sentence (owner, 2026-10-18).
BLOCKED_ACTION = {
    "investigate": "your check on {target}",
    "protect": "your protection of {target}",
    "shoot": "your shot at {target}",
    "watch": "your watch on {target}",
    "follow": "your follow of {target}",
    "sigil": "your sigil on {target}",
}


def what_was_blocked(action: str, target: str | None) -> str:
    """"your protection of player_5 did not happen", or the record's own words when there is no
    target to name (holding fire, a conceal)."""
    if target and action in BLOCKED_ACTION:
        return BLOCKED_ACTION[action].format(target=target) + " did not happen"
    return "your action was not carried out"


def blocked_by_living_chanteuse(blocked: str) -> str:
    return (f"You were roleblocked: {blocked}. Only the Chanteuse could roleblock that night, and a "
            "block is a visit, so the Chanteuse, a wolf, came to you that night.")


def blocked_through_chanteuse_body(blocked: str) -> str:
    return (f"You were roleblocked: {blocked}. The Chanteuse was already dead, so the Necromancer "
            "blocked you through her body; a watcher at your door would have seen the Chanteuse's "
            "name, not the Necromancer's.")


def pack_carrier_blocked_through_chanteuse_body() -> str:
    return ("The pack's carrier was roleblocked: the kill did not happen. The Chanteuse was already "
            "dead, so the Necromancer blocked the carrier through her body.")


# --- attacks that met immunity (A13–A19) ------------------------------------------------------

def target_is_the_only_immune_role(target: str, role: str) -> str:
    return (f"Only {_immune_role_phrase(role)} could survive that attack, so {target} is "
            f"{ROLE_TITLES[role]}.")


# --- an attack the fortune teller's self-bet stopped (A53, A54) -------------------------------

def saved_by_own_self_bet_so_fortune_teller(target: str) -> str:
    return f"Only the Fortune Teller's own bet saves a player like this, so {target} is the Fortune Teller."


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


# --- shared pieces ----------------------------------------------------------------------------

def _titles_with_or(roles: list[str]) -> str:
    """Roles joined with "or": "the Serial Killer or the Speculator"."""
    return " or ".join(ROLE_TITLES[role] for role in roles)


def _whose(holder: str | None) -> str:
    """"your" for the seat's own record; "player_3's" for a dead player's read-out record."""
    return "your" if holder is None else f"{holder}'s"


def _whom(holder: str | None) -> str:
    """"you" for the seat's own record; "player_3" for a dead player's read-out record."""
    return "you" if holder is None else holder


def _names_with_and(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def _none_of(names: list[str]) -> str:
    """The subject of a negative line about several players: "player_7 is not", "Neither player_7
    nor player_3 is", "None of player_7, player_3 and player_5 is"."""
    if len(names) == 1:
        return f"{names[0]} is not"
    if len(names) == 2:
        return f"Neither {names[0]} nor {names[1]} is"
    return f"None of {_names_with_and(names)} is"


# --- checks (A21–A25) -------------------------------------------------------------------------

def suspicious_only_wolves_in_this_cast(target: str) -> str:
    return f"Only a wolf reads Suspicious in this game, so {target} is a wolf."


def suspicious_on_night_one(target: str) -> str:
    return (f"The Necromancer does nothing on night 1, so only a wolf reads Suspicious that night: "
            f"{target} is a wolf.")


def suspicious_with_no_one_dead_yet(target: str) -> str:
    return ("No one had died before that night, so the Necromancer had no body to kill through and "
            f"could not read Suspicious: {target} is a wolf.")


def suspicious_with_no_killing_body(target: str) -> str:
    return ("Neither the Illusionist nor the Vigilante had been revealed dead before that night, so "
            "the Necromancer had no body to kill through and could not read Suspicious: "
            f"{target} is a wolf.")


def suspicious_and_not_the_necromancer(target: str) -> str:
    return ("Only a wolf, or the Necromancer on a night it kills through a body, reads Suspicious, "
            f"and {target} is not the Necromancer: {target} is a wolf.")


def suspicious_with_both_wolves_dead(target: str) -> str:
    return (f"Both wolves are dead and neither was {target}, so {target} is the Necromancer: it read "
            "Suspicious because it killed through a body that night.")


def suspicious_wolf_or_necromancer(target: str) -> str:
    return (f"So {target} is a wolf, or the Necromancer if it killed through a dead player's body "
            "that night.")


def suspicious_through_investigator_body(target: str) -> str:
    return f"You made no kill that night, so only a wolf could read Suspicious: {target} is a wolf."


def not_suspicious(target: str, still_possible: list[str]) -> str:
    if not still_possible:
        return f"So {target} is not a wolf."
    return f"So {target} is not a wolf, but {target} could still be {_titles_with_or(still_possible)}."


# --- watches and follows (A26, A27, A32–A35) ----------------------------------------------------

NEVER_VISITS_UNDER_OWN_NAME = {
    "under_body": "{title} visits only under a dead player's name",
    "never": "{title} never visits",
}
"""Why a role's visits never show its name, by its `visits` trait."""

BORROWED_VERB = {role: traits.borrowed_verb for role, traits in ROLE_TRAITS.items() if traits.borrowed_verb}
"""What the Necromancer does to its target through a body of each role."""


def visit_does_not_show_the_action() -> str:
    return "A visit does not show which action was taken."


def not_roles_that_never_visit_in_own_name(names: list[str], roles: list[str]) -> str:
    reasons = [NEVER_VISITS_UNDER_OWN_NAME[ROLE_TRAITS[role].visits].format(title=ROLE_TITLES[role]) for role in roles]
    return f"{_none_of(names)} {_titles_with_or(roles)}: {', and '.join(reasons)}."


def acted_through_body(body: str, body_role: str, target: str) -> str:
    return (f"{body} was already dead, so the Necromancer used {body}'s body to "
            f"{BORROWED_VERB[body_role]} {target}.")


def no_one_else_visited(target: str) -> str:
    return (f"{target} survived, so no visit to {target} was hidden: no one attacked, protected, "
            f"checked, blocked, followed or set a sigil on {target} that night. This says nothing "
            f"about what {target} did.")


def your_watch_was_a_visit(target: str) -> str:
    """A56: the Sentinel read its own "no one visited" as "I went nowhere" and denied a true follow (2b29bfe8)."""
    return (f"Your watch was itself your visit to {target}; your own result never lists you. So a follow on you "
            f"that night shows you going to {target}.")


def visited_two_so_chanteuse(target: str, destinations: list[str]) -> str:
    first, second = destinations
    return ("Only a wolf who carries the pack's kill and also blocks someone visits two players, so "
            f"{target} is the Chanteuse and carried the kill that night: one of {first} and {second} "
            "was the pack's target, the other the player she tried to block.")


def visited_no_one(target: str, not_serial_killer: bool, healer: str) -> str:
    """`healer`: "" (say nothing of the Healer), "unless_blocked" or "certain"."""
    ruled_out = []
    if not_serial_killer:
        ruled_out.append("the Serial Killer")
    if healer == "unless_blocked":
        ruled_out.append(f"the Healer unless {target} was roleblocked")
    elif healer == "certain":
        ruled_out.append("the Healer")
    return (f"No visit was made in {target}'s name that night, so {target} is not "
            f"{', and not '.join(ruled_out)}. This does not show that {target} did nothing.")


# --- sigils (A37–A39) -------------------------------------------------------------------------

def sigil_saved_so_attacker(target: str, wolf: bool, vigilante: bool, holder: str | None = None) -> str:
    if wolf and vigilante:
        who = "a wolf or the Vigilante"
    elif wolf:
        who = "a wolf"
    else:
        who = "the Vigilante"
    return f"{target} attacked someone and needed saving from {_whose(holder)} sigil, so {target} is {who}."


def sigil_no_effect_or_immune(target: str, immune_role: str) -> str:
    return (f"Either {target} attacked no one that night, or {target} is {ROLE_TITLES[immune_role]}, "
            "whom a sigil cannot harm.")


def sigil_no_effect_unless_necromancer(target: str) -> str:
    return (f"{target} did not attack anyone that night, unless {target} is the Necromancer attacking "
            "through a dead player's body.")


def sigil_no_effect(target: str) -> str:
    return f"{target} did not attack anyone that night."


# --- blocks (A40–A43) -------------------------------------------------------------------------

def your_block_took_so_town(target: str) -> str:
    return f"Your block took, so {target} is on the Town side."


def only_unblockable_roles(target: str, unblockable: list[str], possible: list[str]) -> str:
    """A41: the Chanteuse's block did not take. `possible`: the unblockable roles `target` can
    still hold, one or both."""
    reason = f"Only {_names_with_and([ROLE_TITLES[role] for role in unblockable])} cannot be blocked"
    if len(possible) == len(unblockable):
        return f"{reason}, so {target} is one of them."
    ruled_out = [role for role in unblockable if role not in possible]
    return (f"{reason}, and {target} is not {_titles_with_or(ruled_out)}, so {target} is "
            f"{ROLE_TITLES[possible[0]]}.")


def block_through_chanteuse_body_took(target: str, neutral: str) -> str:
    return f"{target} is a Town player or a wolf: a block does not take on {ROLE_TITLES[neutral]}."


def block_through_chanteuse_body_did_not_take(target: str, neutral: str) -> str:
    return (f"Only you and {ROLE_TITLES[neutral]} cannot be blocked, so {target} is "
            f"{ROLE_TITLES[neutral]}.")


# --- bets on a hidden body (A49, A50) ----------------------------------------------------------

def bet_shows_hidden_role(target: str, role: str) -> str:
    return f"{target}'s role was hidden, but your bet shows {target} was {ROLE_TITLES[role]}."


def bet_shows_hidden_role_was_not(target: str, role: str) -> str:
    return f"{target}'s role was hidden, but your bet shows {target} was not {ROLE_TITLES[role]}."


# --- Suspicious, read with the morning (A22 conditions b and c) ---------------------------------

NECROMANCER_DEED = {
    "reanimated_healer": "saved a player through the dead Healer's body",
    "reanimated_sigilist": "set a sigil through the dead Sigilist's body",
}
"""The Necromancer's announced action on a night it made no kill."""


def suspicious_when_the_necromancer_did_something_else(target: str, deed: str) -> str:
    return (f"The Necromancer acts once a night, and the morning shows it {NECROMANCER_DEED[deed]} "
            f"that night, so it made no kill and could not read Suspicious: {target} is a wolf.")


def suspicious_with_no_kill_through_a_body_announced(target: str) -> str:
    return ("No attack through a dead player's body was announced that night, and every such attack "
            "is announced, so the Necromancer made no kill and could not read Suspicious: "
            f"{target} is a wolf.")


# --- a watch read with the morning (A28–A31) ----------------------------------------------------

SEEN_DOER = {
    "wolves": "the wolf who attacked {target}",
    "serial_killer": "the Serial Killer",
    "vigilante": "the Vigilante",
    "sigilist": "the Sigilist",
    "healer": "the Healer",
}
"""Who made an announced attack (by its type) or the living Healer's save, as a line names them."""

DOER_ROLE = {
    "wolves": "a wolf",
    "serial_killer": "the Serial Killer",
    "vigilante": "the Vigilante",
    "sigilist": "the Sigilist",
    "healer": "the Healer",
}


def _names_with_or(names: list[str]) -> str:
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " or " + names[-1]


def every_attack_was_a_visit(target: str, with_healer: bool, holder: str | None = None) -> str:
    who = f"Everyone who attacked {target}" + (" and the Healer who saved them" if with_healer else "")
    return f"{who} came to {target}, and {_whose(holder)} watch saw every visitor but {_whom(holder)}."


def reanimated_conceal_hides_no_visit(target: str, holder: str | None = None) -> str:
    return (f"{target}'s role was hidden through the dead Illusionist's body, which hides no visit: "
            f"everyone who attacked {target} came to {target}, and {_whose(holder)} watch saw every "
            f"visitor but {_whom(holder)}.")


def living_conceal_hides_the_killer(target: str, holder: str | None = None) -> str:
    return (f"{target}'s role was hidden by the living Illusionist, whose conceal also hides the "
            f"visit of the wolf who made the kill: {_whose(holder)} watch could not see that wolf.")


def illusionist_made_the_kill(target: str, holder: str | None = None) -> str:
    return (f"The Illusionist's conceal is a visit to {target}, and none of the players {_whom(holder)} saw "
            "can be the Illusionist, so the Illusionist made the kill itself.")


def illusionist_made_the_kill_or_was_seen(target: str, names: list[str]) -> str:
    return (f"The Illusionist's conceal is a visit to {target}, so either the Illusionist made the "
            f"kill itself, or it is {_names_with_or(names)}.")


def other_attacks_were_seen(target: str, holder: str | None = None) -> str:
    return f"Everyone else who attacked {target} came to {target}, and {_whose(holder)} watch saw them."


def only_one_seen_can_be(doer: str, target: str, player: str, holder: str | None = None) -> str:
    return (f"Of the players {_whom(holder)} saw, only {player} can be "
            f"{SEEN_DOER[doer].format(target=target)}, so {player} is {DOER_ROLE[doer]}.")


def doer_is_one_of(doer: str, target: str, names: list[str]) -> str:
    who = SEEN_DOER[doer].format(target=target)
    return f"{who[0].upper()}{who[1:]} is {_names_with_or(names)}."


def seen_are_one_each(names: list[str], doers: list[str], holder: str | None = None) -> str:
    roles = _names_with_and([DOER_ROLE[doer] for doer in doers])
    return (f"{_names_with_and(names)} are {roles}, one each; {_whose(holder)} watch does not show which "
            "is which.")


# --- a sigil that struck down a hidden player (A36) ----------------------------------------------

def sigil_struck_a_hidden_pack_victim(target: str) -> str:
    return ("Only a wolf carrying the pack's kill or the Vigilante can be struck down by a sigil, and "
            f"{target}'s role was hidden by the living Illusionist, who hides only the pack's victim, "
            f"never a wolf: {target} is the Vigilante.")


def sigil_struck_a_hidden_player(target: str, wolf: bool, vigilante: bool) -> str:
    if wolf and vigilante:
        who = "a wolf or the Vigilante"
    elif wolf:
        who = "a wolf"
    else:
        who = "the Vigilante"
    return ("Only a wolf carrying the pack's kill or the Vigilante can be struck down by a sigil, so "
            f"{target}, whose role was hidden, is {who}.")


# --- a conceal with no body (A45) ----------------------------------------------------------------

def pack_target_saved_conceal_kept(target: str, saver: str) -> str:
    how = {
        "healer": "the Healer saved them",
        "reanimated_healer": "the Necromancer saved them through the dead Healer's body",
    }[saver]
    return f"{target}, the pack's target, survived: {how}, so your conceal was not spent."


def pack_target_self_bet_conceal_kept(target: str) -> str:
    return (f"{target}, the pack's target, survived on their own self-bet, so {target} is the Fortune "
            "Teller, and your conceal was not spent.")


def pack_target_immune_conceal_kept(target: str, role: str) -> str:
    return (f"{target}, the pack's target, survived and no save was announced, so {target} could not "
            f"be killed: {target} is {ROLE_TITLES[role]}. Your conceal was not spent.")
