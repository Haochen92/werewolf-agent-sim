"""Where each solo night role's night 1 choice lands (discussion_evidence.md §7.5).

Over the June games every night 1 action fell on seat 1: with nothing to go on, the model takes
the lowest-numbered seat, whatever order the list comes in (the first run of this check, two arms,
seat order against a seeded shuffle: 94 and 95 of 96 calls). This replays night 1 for the
investigator, the healer and the serial killer on the recorded boards (the roles of the 28 June
games and the four step 8 games), through the real prompts and ``run_agent``, under one or more
arms: ``plain`` (no lot: ``night_lot`` rendered empty) and ``lot`` (as built: the night 1 default
drawn by lot, ``prompt_inputs.night_one_lot``). One row per call; a summary at the end.

    poetry run python -m evaluation.experiments.night1_target_bias_check [--boards N] [--arms plain,lot]
"""
from __future__ import annotations

import argparse
import collections
import glob
import json
import time
from pathlib import Path

from Agents.prompts import HEALER_NIGHT, INVESTIGATOR_NIGHT, SERIAL_KILLER_NIGHT
from Agents.prompts import prompt_inputs
from Agents.rules.seats import seat_order
from Agents.schemas import HealerOutput, InvestigatorOutput, SerialKillerOutput
from Agents.schemas.game_events import DaySummary
from Agents.turn.agent_player import run_agent

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "evidence" / "game_play_enhancement" / "data" / "night1_target_bias"

ROLES = {
    "investigator": (INVESTIGATOR_NIGHT, InvestigatorOutput, "investigator_target"),
    "healer": (HEALER_NIGHT, HealerOutput, "healer_target"),
    "serial_killer": (SERIAL_KILLER_NIGHT, SerialKillerOutput, "serial_killer_target"),
}

# What every agent knows on night 1 of a day with rounds: nobody spoke, nobody voted.
DAY_ONE_SUMMARIES = [
    DaySummary(day=1, summary="Key accusations and defenses: None.\nRole claims: None.",
               source="discussion", structured={"accusations": [], "role_claims": []}),
    DaySummary(day=1, summary="\nThere is no vote on day 1, so no one voted and no one is eliminated.",
               source="game_master", structured={}),
]


def load_boards() -> list[tuple[str, dict[str, str]]]:
    """(board id, roles) for every recorded game: the June batch and the step 8 games."""
    boards = []
    june_files = sorted(glob.glob(str(REPO_ROOT / "batch_results" / "wolf_sk_mining_p*" / "games" / "*.jsonl")))
    for path in june_files:
        for line in open(path):
            if not line.strip():
                continue
            record = json.loads(line)
            boards.append((str(record.get("game_id", ""))[:8], record["roles"]))
    step8_files = sorted(glob.glob(str(REPO_ROOT / "evidence" / "game_play_enhancement" / "data"
                                       / "phase2_step8_games" / "game*.record.json")))
    for path in step8_files:
        record = json.load(open(path))
        boards.append((str(record.get("game_id", ""))[-8:], record["roles"]))
    return boards


def night_one_payload(board_id: str, roles: dict[str, str], role: str) -> dict:
    """The payload a solo night role's node receives on night 1: everyone alive, no results yet."""
    actor = None
    for player, player_role in roles.items():
        if player_role == role:
            actor = player
    if actor is None:
        raise LookupError(f"no {role} on board {board_id}")
    everyone = seat_order(list(roles))
    wolves = [p for p in everyone if roles[p] == "wolf"]
    others = [p for p in everyone if roles[p] != "wolf"]
    cast_role_counts = dict(collections.Counter(roles.values()))
    return {
        "player_id": actor,
        "player_role": role,
        "current_day": 1,
        "current_round": 0,
        "game_id": f"night1-bias-{board_id}",
        "surviving_players": everyone,
        "surviving_wolves": wolves,
        "surviving_villagers": others,
        "day_channel": [],
        "day_summaries": list(DAY_ONE_SUMMARIES),
        "dead_roster": [],
        "cast_role_counts": cast_role_counts,
        "investigator_results": [],
        "vigilante_results": [],
        "vigilante_bullets": 2,
        "previous_strategy": "",
        "agent_strategies": {},
        "human_players": [],
    }


def no_lot(payload):
    """The plain arm: the night 1 prompt without the drawn default."""
    return ""


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--boards", type=int, default=0, help="only the first N boards (0 = all)")
    parser.add_argument("--arms", default="plain,lot")
    parser.add_argument("--roles", default="investigator,healer,serial_killer")
    parser.add_argument("--out", default=str(OUT_DIR))
    args = parser.parse_args()
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    boards = load_boards()
    if args.boards:
        boards = boards[: args.boards]
    arms = args.arms.split(",")
    roles = args.roles.split(",")
    real_lot = prompt_inputs.night_one_lot

    rows = []
    results_path = out_dir / "results.jsonl"
    with results_path.open("w") as out:
        for arm in arms:
            if arm == "plain":
                prompt_inputs.night_one_lot = no_lot
            else:
                prompt_inputs.night_one_lot = real_lot
            for board_id, board_roles in boards:
                for role in roles:
                    template, output_schema, output_key = ROLES[role]
                    payload = night_one_payload(board_id, board_roles, role)
                    lot_line = prompt_inputs.night_one_lot(payload)
                    lot = None
                    if lot_line:
                        lot = lot_line.split(": ")[-1].split(".")[0]
                    started = time.time()
                    turn = run_agent(payload, template, output_schema, output_key)
                    target = turn.entry if turn is not None else None
                    read_players = []
                    if turn is not None:
                        for read in turn.effects.reads:
                            read_players.append(read.player)
                    row = {
                        "arm": arm,
                        "board": board_id,
                        "role": role,
                        "actor": payload["player_id"],
                        "lot": lot,
                        "target": target,
                        "target_is_lot": lot is not None and target == lot,
                        "target_seat_1": target == "player_1",
                        "reads_players": read_players,
                        "placeholder_copied": any("<" in p or "exact" in p for p in read_players),
                        "seconds": round(time.time() - started, 2),
                    }
                    rows.append(row)
                    out.write(json.dumps(row) + "\n")
                    out.flush()
                    print(f"{arm:<9} {board_id} {role:<14} {payload['player_id']:<9} -> {target}  "
                          f"(lot {lot})", flush=True)
    prompt_inputs.night_one_lot = real_lot

    lines = ["# Night 1 target choice, with and without the drawn default", "",
             f"{len(boards)} boards, roles {', '.join(roles)}; one call per board per role per arm.", ""]
    for arm in arms:
        arm_rows = [r for r in rows if r["arm"] == arm]
        lines.append(f"## {arm}")
        lines.append("")
        lines.append("| role | calls | target = seat 1 | target = the lot | distinct targets | placeholder copied |")
        lines.append("|---|---|---|---|---|---|")
        for role in roles:
            role_rows = [r for r in arm_rows if r["role"] == role]
            targets = collections.Counter(r["target"] for r in role_rows)
            lines.append("| {} | {} | {} | {} | {} | {} |".format(
                role, len(role_rows),
                sum(1 for r in role_rows if r["target_seat_1"]),
                sum(1 for r in role_rows if r["target_is_lot"]),
                len(targets),
                sum(1 for r in role_rows if r["placeholder_copied"]),
            ))
        lines.append("")
        all_targets = collections.Counter(r["target"] for r in arm_rows)
        lines.append("Targets, all roles: " + ", ".join(f"{k} {v}" for k, v in sorted(all_targets.items(), key=lambda kv: str(kv[0]))))
        lines.append("")
    (out_dir / "summary.md").write_text("\n".join(lines))
    print("\n".join(lines))


if __name__ == "__main__":
    main()
