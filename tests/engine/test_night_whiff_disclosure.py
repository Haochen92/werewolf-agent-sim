"""Wolf-side whiff disclosure (change E): a pack kill on a night-immune player tells the wolves,
privately, that the attack failed on immunity.

Mirrors the vigilante's immune-shot record. The public GM transcript stays SILENT on an immune
whiff (announcing it would out the immune player); a HEALED target gives the result "saved" (a
public save), never "immune" — so there is no false positive. The ten-seat engine writes the
whiff into the pack's own night record (actor "wolves", which every wolf's payload carries via
own_night_actions) instead of a game-master note in the wolf channel; and the record says only
that the target was immune tonight, not who they are, since the serial killer is immune every
night and the necromancer on night 1. The Send-builder gating + leak_test.check_night_record_isolation
fence it to wolf prompts.
"""
from __future__ import annotations

from tests.factories.builders import night_runtime as _runtime

from Agents.nodes.night.resolution import night_resolution
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.rules.night_record import own_night_actions
from Agents.schemas.night import NightChoice
from Agents.schemas.roles import lineup
from tests.leak_test import check_night_record_isolation

# --- fixtures ---------------------------------------------------------------

ROLES = {
    "w0": "chanteuse",
    "w1": "illusionist",
    "sk": "serial_killer",
    "h": "healer",
    "t0": "sentinel",
}

WHIFF = "sk was unharmed: immune to night kills tonight. The public was told nothing about this attack."


def _state(kill=None, protect=None, roles=ROLES, day=1) -> dict:
    """A live-game state for one night: the pack's kill (carried by w0) and the healer's protection."""
    choices = []
    if kill:
        choices.append(NightChoice("w0", roles["w0"], "kill", kill))
    if protect:
        choices.append(NightChoice("h", "healer", "protect", protect))
    return {
        "current_day": day,
        "roles": roles,
        "lineup": lineup("serial_killer", "speculator"),
        "surviving_wolves": ["w0", "w1"],
        "surviving_villagers": [p for p in roles if p not in ("w0", "w1")],
        "day_channel": [],
        "night_choices": choices,
    }


def _pack_record(update: dict):
    records = [r for r in update.get("night_actions", []) if r.actor == "wolves"]
    assert len(records) <= 1
    return records[0] if records else None


def _public_message(update: dict) -> str:
    return update["day_channel"][0].message


# --- (a) wolves hit the SK -> private record, silent public line ---------------

def test_wolf_kill_on_sk_writes_private_note():
    update = night_resolution(_state(kill="sk"), _runtime())

    record = _pack_record(update)
    assert (record.action, record.target, record.result) == ("kill", "sk", "immune")
    assert record.outcome == WHIFF
    assert "wolf_channel" not in update  # no game-master note rides the channel any more


def test_wolf_kill_on_sk_public_transcript_stays_silent():
    update = night_resolution(_state(kill="sk"), _runtime())

    message = _public_message(update)
    # The immune whiff is never announced (announcing it would out the SK): the public
    # line reads as a quiet night, and the SK's name / the confirmation never surface.
    assert "No one died last night." in message
    assert "sk" not in message
    assert "immune" not in message
    assert "serial killer" not in message


def test_the_necromancer_is_immune_on_night_one_only():
    roles = {**ROLES, "sk": "necromancer"}
    night_one = _pack_record(night_resolution(_state(kill="sk", roles=roles), _runtime()))
    assert night_one.result == "immune"
    night_two = _pack_record(night_resolution(_state(kill="sk", roles=roles, day=2), _runtime()))
    assert night_two.result == "killed"


# --- (b) wolves' target is healed -> NO whiff, public save announced -----------

def test_healed_wolf_target_writes_no_note():
    # Wolves hit t0, healer protects t0: result "saved", not "immune".
    update = night_resolution(_state(kill="t0", protect="t0"), _runtime())
    record = _pack_record(update)
    assert record.result == "saved"
    assert "immune" not in record.outcome

    message = _public_message(update)
    assert "was saved by the healer" in message


def test_healed_sk_would_still_be_immune_only_note_gates_on_immune():
    # Defensive: even if the healer covers the SK, the verdict is "immune" (immunity precedes
    # the heal), so the whiff is recorded — the gate is the verdict, not "unhealed".
    update = night_resolution(_state(kill="sk", protect="sk"), _runtime())
    assert _pack_record(update).result == "immune"


# --- (c) an ordinary landed kill -> no whiff ------------------------------------

def test_normal_kill_writes_no_note():
    update = night_resolution(_state(kill="t0"), _runtime())
    record = _pack_record(update)
    assert record.result == "killed"
    assert "immune" not in record.outcome

    message = _public_message(update)
    assert "t0 was killed by the wolves" in message


def test_no_wolf_target_writes_no_note():
    update = night_resolution(_state(), _runtime())
    assert _pack_record(update) is None


# --- (d) leak boundary: the whiff never reaches a town payload / public line ----

def _entry(player_id: str, role: str, output_key: str, records) -> dict:
    return {
        "player_id": player_id,
        "player_role": role,
        "output_key": output_key,
        "prompt_input": build_agent_prompt_input(
            {"player_role": role, "night_actions": own_night_actions(records, player_id, role)}
        ),
    }


def test_whiff_note_is_isolated_to_wolf_prompts():
    """The whiff rides the pack's night record: it must reach every wolf's prompt and NO town
    prompt / public transcript. Build the real prompt_input each role would receive from the
    payload builders' own filter and run the standing night-record leak check over them."""
    update = night_resolution(_state(kill="sk"), _runtime())
    records = update["night_actions"]

    wolf_entries = [_entry("w0", "chanteuse", "kill_target", records),
                    _entry("w1", "illusionist", "conceal", records)]
    town_entry = _entry("t0", "sentinel", "day_votes", records)

    # Each wolf really does see the whiff...
    for entry in wolf_entries:
        assert WHIFF in entry["prompt_input"]["night_actions"]
    # ...the town player's whole prompt_input never mentions it...
    assert WHIFF not in repr(town_entry["prompt_input"])
    # ...and it is absent from the public GM transcript emitted this night.
    assert WHIFF not in _public_message(update)

    # The standing night-record isolation check passes for these entries.
    assert check_night_record_isolation([*wolf_entries, town_entry], records, ROLES) == []


def test_leak_check_would_catch_the_note_in_a_town_payload():
    """Negative control: if the whiff ever leaked into a non-wolf payload, the standing check
    must flag it — proving the guard above is live, not vacuous."""
    records = night_resolution(_state(kill="sk"), _runtime())["night_actions"]
    leaked_town_entry = {
        "player_id": "t0",
        "player_role": "sentinel",
        "output_key": "day_votes",
        "prompt_input": build_agent_prompt_input({"player_role": "sentinel", "night_actions": records}),
    }
    assert check_night_record_isolation([leaked_town_entry], records, ROLES) != []
