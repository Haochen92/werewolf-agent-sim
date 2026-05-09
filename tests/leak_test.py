from __future__ import annotations

from collections.abc import Iterable
from typing import Any

NO_WOLF_MESSAGES = "No messages yet."
NO_INVESTIGATIONS = "No investigations yet."


def _record_leak(leaks: list[str], message: str) -> None:
    leaks.append(message)
    print(message)


def test_wolf_identity_isolation(
    prompt_log: list[dict[str, Any]], roles: dict[str, str]
) -> list[str]:
    """Wolf names should only appear in wolf agents' private prompt fields."""
    leaks: list[str] = []
    wolf_names = [player for player, role in roles.items() if role == "wolf"]

    for entry in prompt_log:
        if entry["player_role"] == "wolf":
            continue

        prompt_input = entry["prompt_input"]
        if prompt_input["surviving_wolves"]:
            _record_leak(
                leaks,
                f"LEAK: {entry['player_id']} ({entry['player_role']}) "
                f"received surviving_wolves: {prompt_input['surviving_wolves']}",
            )

        leaked_names = [
            wolf_name for wolf_name in wolf_names if wolf_name in prompt_input["surviving_wolves"]
        ]
        if leaked_names:
            _record_leak(
                leaks,
                f"LEAK: {entry['player_id']} ({entry['player_role']}) "
                f"received wolf identities: {', '.join(leaked_names)}",
            )

    return leaks


def test_wolf_channel_isolation(prompt_log: list[dict[str, Any]]) -> list[str]:
    """Wolf channel should only appear in wolf night prompts."""
    leaks: list[str] = []
    for entry in prompt_log:
        if entry["output_key"] == "wolf_channel":
            continue

        wolf_channel = entry["prompt_input"]["wolf_channel"]
        if wolf_channel and wolf_channel != NO_WOLF_MESSAGES:
            _record_leak(
                leaks,
                f"LEAK: {entry['player_id']} ({entry['player_role']}) "
                f"received wolf_channel in {entry['output_key']} phase",
            )

    return leaks


def test_investigator_results_isolation(prompt_log: list[dict[str, Any]]) -> list[str]:
    """Investigation results should only appear in investigator prompts."""
    leaks: list[str] = []
    for entry in prompt_log:
        if entry["player_role"] == "investigator":
            continue

        results = entry["prompt_input"]["investigator_results"]
        if results and results != NO_INVESTIGATIONS:
            _record_leak(
                leaks,
                f"LEAK: {entry['player_id']} ({entry['player_role']}) "
                "received investigator_results",
            )

    return leaks


def test_healer_target_absent(prompt_log: list[dict[str, Any]]) -> list[str]:
    """Healer target should never be included in prompt input."""
    leaks: list[str] = []
    for entry in prompt_log:
        prompt_input = entry["prompt_input"]
        if "healer_target" in prompt_input and prompt_input["healer_target"]:
            _record_leak(
                leaks,
                f"LEAK: {entry['player_id']} ({entry['player_role']}) "
                "received healer_target",
            )
    return leaks


def test_eliminated_players_excluded(
    prompt_log: list[dict[str, Any]], eliminated_players: Iterable[str]
) -> list[str]:
    """Eliminated players should receive no prompts after their elimination day."""
    leaks: list[str] = []
    elimination_day_by_player: dict[str, int] = {}

    for player in eliminated_players:
        for entry in prompt_log:
            day_channel = entry["prompt_input"]["day_channel"]
            if f"Player {player} has been voted out" in day_channel or (
                f"{player} was killed by the wolves last night" in day_channel
            ):
                elimination_day_by_player[player] = entry["day"]
                break

    for entry in prompt_log:
        player = entry["player_id"]
        elimination_day = elimination_day_by_player.get(player)
        if elimination_day is not None and entry["day"] > elimination_day:
            _record_leak(
                leaks,
                f"LEAK: eliminated player {player} received prompt on day {entry['day']}",
            )

    return leaks


def run_leak_tests(
    prompt_log: list[dict[str, Any]],
    roles: dict[str, str],
    eliminated_players: Iterable[str] = (),
) -> list[str]:
    print("=== Running Leak Tests ===")
    leaks = [
        *test_wolf_identity_isolation(prompt_log, roles),
        *test_wolf_channel_isolation(prompt_log),
        *test_investigator_results_isolation(prompt_log),
        *test_healer_target_absent(prompt_log),
        *test_eliminated_players_excluded(prompt_log, eliminated_players),
    ]
    print("=== Leak Tests Complete ===")
    return leaks
