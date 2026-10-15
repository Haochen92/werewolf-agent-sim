"""Website-game source: finished games from the live server's public replay endpoint.

A game played on the website leaves no ``run_batch`` record; its durable trace is the replay (every
event the server stored: speeches, passes, votes, night results, summaries, roles). This module
fetches a replay and rebuilds the same record shape ``batch_records`` yields, so readers written for
batch games (the role-fact screen and reader, the discussion-evidence judge, the hallucination bench)
take website games unchanged. Human seats are listed in ``humans``: readers keep their lines as
context and leave them out of what they measure.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from collections import defaultdict

LIVE_SERVER = "https://wolf.liuhaochen.com/api"

# night_result attacker types → the batch record's per-attacker target / landed fields
_ATTACKER_FIELDS = {"wolves": ("wolves_target", "kill_successful"),
                    "serial_killer": ("serial_killer_target", "serial_killer_kill_landed"),
                    "vigilante": ("vigilante_target", "vigilante_kill_landed")}


def get_json(url: str):
    # Cloudflare in front of the site refuses urllib's default user agent.
    req = urllib.request.Request(url, headers={"User-Agent": "werewolf-eval/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


def record_from_replay(replay: dict) -> dict:
    """One replay (the endpoint's JSON) → a batch-shaped game record."""
    record: dict = {"game_id": replay["game_id"], "winner": replay["winner"], "roles": {},
                    "day_channel": [], "day_summaries": [], "day_resolutions": [],
                    "night_resolutions": [], "investigator_results": [], "humans": set(),
                    "model": replay.get("model"), "memory": replay.get("memory")}
    votes: dict[int, list[dict]] = defaultdict(list)
    for e in replay["events"]:
        t, day = e["type"], e["day"]
        if t == "roles_assigned":
            record["roles"] = e["roles"]
        elif t == "input_request":
            record["humans"].add(e["player"])
        elif t == "speech":
            record["day_channel"].append({"day": day, "seq": e["channel_seq"], "player": e["player"],
                                          "message": e["message"], "passed": False})
        elif t == "pass_marker":
            record["day_channel"].append({"day": day, "seq": e["channel_seq"], "player": e["player"],
                                          "message": "", "passed": True,
                                          "pass_reason": e.get("pass_reason")})
        elif t == "day_summary_structured":
            record["day_summaries"].append({"day": day, "structured": e["data"]})
        elif t == "vote_cast":
            votes[day].append({"voter": e["voter"], "votee": e["votee"]})
        elif t == "lynch_result":
            record["day_resolutions"].append({
                "day": day, "votes": votes.pop(day, []), "vote_counts": e["vote_counts"],
                "voted_player": e["player"] if e["outcome"] == "lynched" else None})
        elif t == "night_result":  # day N = the night after day N, as in the batch records
            night: dict = {"day": day, "deaths": [d["player"] for d in e["deaths"]]}
            for d in e["deaths"]:
                for attacker in d["attacker_types"][:1]:
                    target, landed = _ATTACKER_FIELDS[attacker]
                    night[target], night[landed] = d["player"], True
            record["night_resolutions"].append(night)
        elif t == "investigation_result":
            record["investigator_results"].append(
                {"day": day, "player_investigated": e["target"], "role_revealed": e["role"]})
    record["humans"] = sorted(record["humans"])
    return record


def load_replays(game_ids: list[str], *, latest: int | None = None,
                 server: str = LIVE_SERVER) -> list[dict]:
    """Records for the named games, plus the ``latest`` N most recently finished ones."""
    if latest:
        listing = get_json(f"{server}/replays?" + urllib.parse.urlencode({"limit": latest}))
        game_ids = [g["game_id"] for g in listing] + list(game_ids)
    return [record_from_replay(get_json(f"{server}/replays/{g}")) for g in game_ids]
