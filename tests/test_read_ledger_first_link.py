"""Guards for the two v1 read-side instruments (2026-07-13): the read ledger (Brier meter on agent
read skill — knowledge-masked, 'unclear' makes no claim) and the first-link diagnostic (momentum-
adjusted read-deltas — a bandwagon join scores ~0, a trend-starter keeps its delta). Synthetic
fixtures: both instruments are empty on pre-reads dumps, so real-data smoke can't exercise them."""

from __future__ import annotations

import json

import pytest

from evaluation.src.loop.first_link import compute_first_link
from evaluation.src.loop.read_ledger import compute_read_ledger


def _game(tmp, name, cases, *, roles, day_channel=None, extra=None):
    ecp = tmp / f"{name}_cases.jsonl"
    ecp.write_text("\n".join(
        json.dumps({"kind": "agent_action_eval", "output": {"eval_case": c}}) for c in cases))
    rec = {"roles": roles, "eval_cases_path": str(ecp), "game_id": f"gid_{name}"}
    if day_channel is not None:
        rec["day_channel"] = day_channel
    if extra:
        rec.update(extra)
    gp = tmp / f"{name}.jsonl"
    gp.write_text(json.dumps(rec))
    return str(gp)


def _read(player, role, conf="high"):
    return {"player": player, "why": "…", "suspected_role": role, "confidence": conf}


# ── read ledger ────────────────────────────────────────────────────────────────────────────────


def test_brier_scored_against_revealed_roles(tmp_path):
    roles = {"v1": "villager", "w1": "wolf", "v2": "villager"}
    cases = [{"action_phase": "day_vote", "player_role": "villager", "player_id": "v1", "day": 1,
              "memory_enabled": True,
              "reads": [_read("w1", "wolf", "high"), _read("v2", "wolf", "high")]}]
    win = _game(tmp_path, "b", cases, roles=roles)
    led = compute_read_ledger(win)
    ch = led["channels"]["villager/day_vote/on"]
    assert ch["n_claims"] == 2 and ch["role_acc"] == 0.5 and ch["faction_acc"] == 0.5
    # correct high-conf claim: (0.85-1)^2; wrong: (0.85-0)^2 — mean asserted exactly
    assert ch["brier"] == pytest.approx(((0.85 - 1) ** 2 + 0.85 ** 2) / 2, abs=1e-4)


def test_knowledge_mask_and_unclear(tmp_path):
    roles = {"w1": "wolf", "w2": "wolf", "v1": "villager", "v2": "villager"}
    cases = [
        # wolf reading its packmate = known, masked; its read on v1 counts
        {"action_phase": "day_vote", "player_role": "wolf", "player_id": "w1", "day": 1,
         "memory_enabled": True, "reads": [_read("w2", "wolf"), _read("v1", "villager")]},
        # investigator already checked v2 -> masked; 'unclear' recorded but makes no Brier claim
        {"action_phase": "day_vote", "player_role": "investigator", "player_id": "v1", "day": 2,
         "memory_enabled": True,
         "private_context": {"investigator_results": [
             {"day": 1, "player_investigated": "v2", "role_revealed": "villager"}]},
         "reads": [_read("v2", "villager"), _read("w1", "unclear")]},
    ]
    win = _game(tmp_path, "m", cases, roles=roles)
    led = compute_read_ledger(win)
    wolf = led["channels"]["wolf/day_vote/on"]
    assert wolf["n"] == 1                       # the packmate read never entered
    inv = led["channels"]["investigator/day_vote/on"]
    assert inv["n"] == 1 and inv["n_claims"] == 0 and inv["unclear_rate"] == 1.0


def test_empty_on_reads_free_dumps(tmp_path):
    roles = {"v1": "villager"}
    cases = [{"action_phase": "day_vote", "player_role": "villager", "player_id": "v1", "day": 1,
              "memory_enabled": True}]
    led = compute_read_ledger(_game(tmp_path, "e", cases, roles=roles))
    assert led["rows"] == [] and led["channels"] == {}


# ── first link ─────────────────────────────────────────────────────────────────────────────────


def _speech(day, seq, player, accuse=None, address=()):
    tags = [{"target": t, "addressed_form": "mention", "stance": "accusation"} for t in (accuse or [])]
    tags += [{"target": t, "addressed_form": "question", "stance": "neutral"} for t in address]
    return {"day": day, "seq": seq, "player": player, "message": "…", "passed": False,
            "addressed_targets": tags}


def _disc(player, role, day, seq, reads):
    return {"action_phase": "day_discussion", "player_role": role, "player_id": player, "day": day,
            "memory_enabled": True, "reads": reads,
            "agent_message": {"day": day, "seq": seq, "player": player, "message": "…",
                              "addressed_targets": []}}


def test_first_link_delta_on_addressee(tmp_path):
    roles = {"p1": "villager", "p2": "villager", "w1": "wolf"}
    # p1 accuses w1 at seq 2, addressing p2. p2's read on w1: 0.25 before (town, low), 1.0 after.
    channel = [_speech(1, 1, "p2"), _speech(1, 2, "p1", accuse=["w1"], address=["p2"]),
               _speech(1, 3, "p2")]
    cases = [_disc("p2", "villager", 1, 1, [_read("w1", "villager", "low")]),
             _disc("p2", "villager", 1, 3, [_read("w1", "wolf", "high")])]
    res = compute_first_link(_game(tmp_path, "fl", cases, roles=roles, day_channel=channel))
    assert res["summary"]["n_links"] == 1
    row = res["rows"][0]
    assert (row["addressee"], row["target"]) == ("p2", "w1")
    assert row["before"] == 0.25 and row["after"] == 1.0
    assert row["delta"] == pytest.approx(0.75) and row["momentum"] == 0.0


def test_bandwagon_push_is_momentum_flattened(tmp_path):
    roles = {"p1": "villager", "p2": "villager", "p3": "villager", "w1": "wolf"}
    # w1 is already trending: p3 pushed at seq 2 and p2's read drifted 0.5 -> 0.75 before p1's
    # late push at seq 4. p2's post-read is 1.0: raw delta +0.25, momentum +0.25 -> adjusted ~0.
    channel = [_speech(1, 1, "p2"), _speech(1, 2, "p3", accuse=["w1"], address=["p2"]),
               _speech(1, 3, "p2"), _speech(1, 4, "p1", accuse=["w1"], address=["p2"]),
               _speech(1, 5, "p2")]
    cases = [_disc("p2", "villager", 1, 1, [_read("w1", "unclear")]),
             _disc("p2", "villager", 1, 3, [_read("w1", "wolf", "low")]),
             _disc("p2", "villager", 1, 5, [_read("w1", "wolf", "high")])]
    res = compute_first_link(_game(tmp_path, "bw", cases, roles=roles, day_channel=channel))
    late = [r for r in res["rows"] if r["seq"] == 4]
    assert len(late) == 1
    assert late[0]["delta"] == pytest.approx(0.25)
    assert late[0]["adjusted"] == pytest.approx(0.0)


def test_no_post_read_means_no_link(tmp_path):
    roles = {"p1": "villager", "p2": "villager", "w1": "wolf"}
    channel = [_speech(1, 1, "p1", accuse=["w1"], address=["p2"])]
    cases = [_disc("p2", "villager", 1, 0, [_read("w1", "villager", "low")])]  # before only
    res = compute_first_link(_game(tmp_path, "np", cases, roles=roles, day_channel=channel))
    assert res["summary"]["n_links"] == 0
