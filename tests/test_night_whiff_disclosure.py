"""Wolf-side whiff disclosure (change E): a wolf kill on the night-immune SK drops a
private game-master note into the wolf channel confirming the target is the serial killer.

Mirrors the vigilante's immune-shot confirmation. The public GM transcript stays SILENT on
an immune whiff (announcing it would out the SK); a HEALED target gives outcome "saved" (a
public save), never the private note — so there is no false positive. The note rides
wolf_channel, the established wolf-private field, so the existing Send-builder gating +
leak_test.check_wolf_channel_isolation already fence it to wolf prompts.
"""
from __future__ import annotations

from types import SimpleNamespace

from Agents.nodes.night.resolution import night_kill_resolution
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas.metrics import Metrics
from tests.leak_test import check_wolf_channel_isolation

# --- fixtures ---------------------------------------------------------------

ROLES = {
    "w0": "wolf",
    "w1": "wolf",
    "sk": "serial_killer",
    "h": "healer",
    "t0": "villager",
}


def _runtime() -> SimpleNamespace:
    return SimpleNamespace(context={"metrics": Metrics()})


def _state(**targets) -> dict:
    """A live-game state for one night. `targets` overrides the tonight-chosen targets."""
    s = {
        "current_day": 1,
        "roles": ROLES,
        "surviving_wolves": ["w0", "w1"],
        "surviving_villagers": ["sk", "h", "t0"],
        "serial_killer_player": "sk",
        "healer_player": "h",
        "investigator_player": None,
        "vigilante_player": None,
        "day_channel": [],
        "wolves_kill_target": None,
        "healer_target": None,
        "serial_killer_target": None,
        "vigilante_target": None,
    }
    s.update(targets)
    return s


def _note_text(target: str) -> str:
    return (
        f"Night of day 1: your kill on {target} failed — {target} was unharmed, "
        f"immune to night kills, which confirms {target} is the serial killer."
    )


def _public_message(update: dict) -> str:
    return update["day_channel"][0].message


# --- (a) wolves hit the SK -> private note, silent public line --------------

def test_wolf_kill_on_sk_writes_private_note():
    update = night_kill_resolution(_state(wolves_kill_target="sk"), _runtime())

    notes = update.get("wolf_channel", [])
    assert len(notes) == 1
    note = notes[0]
    assert note.wolf == "game_master"
    assert note.message == _note_text("sk")
    # vote="" keeps the GM note out of the wolf kill-vote tally (which reads .vote).
    assert note.vote == ""


def test_wolf_kill_on_sk_public_transcript_stays_silent():
    update = night_kill_resolution(_state(wolves_kill_target="sk"), _runtime())

    message = _public_message(update)
    # The immune whiff is never announced (announcing it would out the SK): the public
    # line reads as a quiet night, and the SK's name / the confirmation never surface.
    assert "No one died last night." in message
    assert "sk" not in message
    assert "immune" not in message
    assert "serial killer" not in message


# --- (b) wolves' target is healed -> NO note, public save announced ----------

def test_healed_wolf_target_writes_no_note():
    # Wolves hit t0, healer protects t0: outcome "saved", not "immune".
    update = night_kill_resolution(
        _state(wolves_kill_target="t0", healer_target="t0"), _runtime()
    )
    assert "wolf_channel" not in update

    message = _public_message(update)
    assert "was saved by the healer" in message


def test_healed_sk_would_still_be_immune_only_note_gates_on_immune():
    # Defensive: even if the healer covers the SK, outcome is "immune" (SK check precedes
    # heal), so the note fires — the gate is `outcomes == "immune"`, not "unhealed".
    update = night_kill_resolution(
        _state(wolves_kill_target="sk", healer_target="sk"), _runtime()
    )
    assert len(update.get("wolf_channel", [])) == 1


# --- (c) an ordinary landed kill -> no note ---------------------------------

def test_normal_kill_writes_no_note():
    update = night_kill_resolution(_state(wolves_kill_target="t0"), _runtime())
    assert "wolf_channel" not in update

    message = _public_message(update)
    assert "t0 was killed by the wolves" in message


def test_no_wolf_target_writes_no_note():
    update = night_kill_resolution(_state(wolves_kill_target=None), _runtime())
    assert "wolf_channel" not in update


# --- (d) leak boundary: the note never reaches a town payload / public line --

def test_whiff_note_is_isolated_to_wolf_prompts():
    """The note rides wolf_channel: it must reach wolf prompts and NO town prompt / public
    transcript. Build the real prompt_input both roles would receive and run the standing
    wolf_channel leak check over them."""
    update = night_kill_resolution(_state(wolves_kill_target="sk"), _runtime())
    note = update["wolf_channel"][0]
    note_text = _note_text("sk")

    # A wolf on the following night sees the accumulated wolf_channel (incl. the note);
    # a town player's payload carries no wolf_channel at all (single-actor night nodes and
    # day turns never seed it), so it formats to the empty sentinel.
    wolf_entry = {
        "player_id": "w0",
        "player_role": "wolf",
        "output_key": "wolf_channel",
        "prompt_input": build_agent_prompt_input(
            {"player_role": "wolf", "wolf_channel": [note]}
        ),
    }
    town_entry = {
        "player_id": "t0",
        "player_role": "villager",
        "output_key": "day_votes",
        "prompt_input": build_agent_prompt_input({"player_role": "villager"}),
    }

    # The wolf really does see the confirmation...
    assert note_text in wolf_entry["prompt_input"]["wolf_channel"]
    # ...the town player's whole prompt_input never mentions it...
    assert note_text not in repr(town_entry["prompt_input"])
    # ...and it is absent from the public GM transcript emitted this night.
    assert note_text not in _public_message(update)

    # The standing wolf_channel isolation check passes for this pair (town carries none).
    assert check_wolf_channel_isolation([wolf_entry, town_entry]) == []


def test_leak_check_would_catch_the_note_in_a_town_payload():
    """Negative control: if the note ever leaked into a non-wolf payload, the standing check
    must flag it — proving the guard above is live, not vacuous."""
    note = night_kill_resolution(_state(wolves_kill_target="sk"), _runtime())["wolf_channel"][0]
    leaked_town_entry = {
        "player_id": "t0",
        "player_role": "villager",
        "output_key": "day_votes",
        "prompt_input": build_agent_prompt_input(
            {"player_role": "villager", "wolf_channel": [note]}
        ),
    }
    assert check_wolf_channel_isolation([leaked_town_entry]) != []
