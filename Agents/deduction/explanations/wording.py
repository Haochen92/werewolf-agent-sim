"""Every sentence of level 7 (slice 12: catalogue F8, F9), in one place, so the same explanation is
always worded the same way. The rules are the catalogue's (§0 grade 3, "Form"): a list of
explanations names the claim, then what the record shows, then every branch, the claim being false
last ("either …, or …, or player_4's claim is false"); a claim with no other branch left is false,
said plainly with the reasons the other branches are shut.
"""

from __future__ import annotations

from Agents.deduction.wording import ROLE_TITLES


def _title(role: str) -> str:
    return ROLE_TITLES[role]


def _joined(parts: list[str], last: str) -> str:
    if len(parts) == 1:
        return parts[0]
    return f"{', '.join(parts[:-1])} {last} {parts[-1]}"


# --- F8: a claim and the record -----------------------------------------------------------------

def explained(claim: str, observation: str, branches: list[str], claimant: str, kind: str) -> str:
    """The list (catalogue §0 example): "player_4 says it shot at player_9 on night 1, but no shot at
    player_9 was announced that night: either player_4 was roleblocked, or player_9 is the Serial
    Killer, or player_4's claim is false."."""
    listed = ", or ".join([*branches, f"{claimant}'s {kind} is false"])
    return f"{claim}, but {observation}: either {listed}."


def is_false(claim: str, observation: str, reasons: list[str], kind: str) -> str:
    """No branch but the claim being false: "…, but no shot at player_5 was announced that night. No
    one could roleblock that night, and …, so that claim is false."; with nothing to add to what the
    morning shows: "…, but …: that report is false."."""
    if not reasons:
        return f"{claim}, but {observation}: that {kind} is false."
    shut = reasons[0] if len(reasons) == 1 else f"{', '.join(reasons[:-1])}, and {reasons[-1]}"
    return f"{claim}, but {observation}. {shut[0].upper()}{shut[1:]}, so that {kind} is false."


def no_shot_announced(target: str) -> str:
    return f"no shot at {target} was announced that night"


def died_despite_protection(target: str) -> str:
    return f"{target} died that night, and a protection that goes ahead stops every attack"


def roleblocked(player: str) -> str:
    return f"{player} was roleblocked"


def immune_holder(target: str, roles: list[str]) -> str:
    return f"{target} is {_joined([_title(role) for role in roles], 'or')}"


def no_blocker() -> str:
    return "no one could roleblock that night"


DOES = {"shoot": "shoots", "protect": "protects", "watch": "watches"}


def cannot_be(player: str, role: str, action: str, yours: bool) -> str:
    """The claimant cannot hold the one role whose action it claims (`yours`: the seat holds it)."""
    why = f"you are {_title(role)}" if yours else f"{player} cannot be {_title(role)}"
    return f"only {_title(role)} {DOES[action]}, and {why}"


def not_immune(target: str, silent: list[str]) -> str:
    """The silent immune roles of the cast that night (catalogue L1 since R10), none left to `target`."""
    if not silent:
        return "every shot that went ahead that night was announced"
    return (f"{target} cannot be {_joined([_title(role) for role in silent], 'or')}, the only "
            f"{'role' if len(silent) == 1 else 'roles'} a shot fails on without an announcement")


VISITOR = {
    "wolves": "a wolf attacked",
    "serial_killer": "the Serial Killer attacked",
    "vigilante": "the Vigilante shot at",
    "sigilist": "the Sigilist set a sigil on",
    "healer": "the Healer protected",
}
"""What was done to the attacked or saved player under the doer's own name, a visit (catalogue B1,
B3–B5, B11)."""


def came_and_shows(deed: str, target: str) -> str:
    """A visit the morning shows went to the watched player: "the Serial Killer attacked player_5 that
    night, and a watch shows that visit"."""
    return f"{deed} {target} that night, and a watch shows that visit"


def came_through_body(body: str, target: str) -> str:
    """The Necromancer's visit through a body shows the body's name (catalogue L4)."""
    return f"the Necromancer went to {target} that night under {body}'s name, and a watch shows that visit"


def conceal_visit(target: str) -> str:
    """The living Illusionist's conceal is a visit to the pack's victim, hidden only when it carried the
    kill itself (catalogue L4, R5)."""
    return (f"the living Illusionist went to {target} that night to hide their role, a visit a watch shows "
            f"unless the Illusionist made the kill itself")


def illusionist_carried() -> str:
    return "the Illusionist carried the pack's kill"


# --- F9: what the public counts fix across nights ----------------------------------------------

def self_bets_used_up(player: str, times: int, savers: list[str]) -> str:
    """Catalogue F9 (C17, R10): "player_5's self-bet has saved it twice, so it has none left: an attack
    on player_5 from now on kills it unless the Healer saves it."."""
    count = {2: "twice"}.get(times, f"{times} times")
    then = f"an attack on {player} from now on kills it"
    if len(savers) == 1:
        then += f" unless {savers[0]} saves it"
    elif savers:
        then += f" unless {', or '.join(savers)}, saves it"
    return f"{player}'s self-bet has saved it {count}, so it has none left: {then}."


def conceals_used_up(hidden: list[tuple[str, int]]) -> str:
    """Catalogue F9 (C20, L8): every conceal hides exactly one death, from one pool of two."""
    named = _joined([f"{player}'s on night {night}" for player, night in hidden], "and")
    count = {2: "Two"}.get(len(hidden), str(len(hidden)))
    return (f"{count} deaths have been hidden ({named}), so the Illusionist's conceals are used up: no death "
            f"will be hidden again.")


HEALER_SAVES = "the Healer"
REANIMATED_SAVES = "the Necromancer through the Healer's body"
