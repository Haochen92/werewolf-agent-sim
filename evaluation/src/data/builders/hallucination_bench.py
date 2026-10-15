"""Freeze the hallucination bench's case set: turns where agents misstated game facts, plus controls.

Each case is one agent turn frozen as the game STATE the engine held when the agent spoke (JSON),
plus the facts a judge checks against. Replay (``replay/hallucination_bench.py``) rebuilds the
turn's payload from that state with the engine's own builders, so one frozen set can be replayed
under any later prompt version or model. A case is self-contained: no batch file, sidecar or
database is read after the build.

Two sources:

- census: the July role-fact census (evidence/generation_prompt/validation/), whose stage-2 reader
  confirmed hallucinations on 50 batch games. Positives are confirmed turns; controls are turns the
  same screen anchored (they touch a checkable fact) but the reader judged consistent. A turn's
  state comes from its game record plus the per-turn sidecar (what the agent was shown privately).
  The dead roster is rebuilt from the record: those games predate it, today's prompt shows it.
- checkpoint: named turns from website games, read from the game's LangGraph checkpoint
  (read-only) just before the turn, with the facts from the public replay. A checkpoint case may
  carry a hand-written ``golden`` expectation for the golden judge.

Old census cases come from June prompts, and many no longer go wrong on today's prompt. So the
intended flow is: build a wide candidate set, run one bench arm of the current prompts over it, then
``curate`` (a config with a ``curate`` block): keep the positives that still go wrong at least
``min_bad_rate`` of the time, an unfiltered random slice of positives, and every control.

Day discussion and day vote turns only (the bench's replay scope). Console:
``eval-build-hallucination-bench --config evaluation/config/template/hallucination_bench_build_example.json``
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic_core import to_jsonable_python

from evaluation.src.audits.role_hallucination_screen import death_timeline
from evaluation.src.core.settings import REPO_ROOT
from evaluation.src.data.sources.replay_api import LIVE_SERVER, get_json, record_from_replay

STATE_KEYS = ("roles", "current_day", "current_round", "surviving_villagers", "surviving_wolves",
              "human_players", "day_channel", "day_summaries", "dead_roster", "agent_strategies",
              "investigator_results", "vigilante_results", "vigilante_bullets", "wolf_channel",
              "night_actions")
FACT_KEYS = ("roles", "night_resolutions", "day_resolutions", "investigator_results")


def _case_id(*parts: Any) -> str:
    return hashlib.sha1("|".join(map(str, parts)).encode()).hexdigest()[:16]


def _facts(record: dict) -> dict:
    """What the judges check against: roles, deaths, votes, results, and the logged role claims."""
    facts = {k: record.get(k) or ([] if k != "roles" else {}) for k in FACT_KEYS}
    facts["day_summaries"] = [{"day": s["day"], "structured": s.get("structured") or {}}
                              for s in record.get("day_summaries") or []]
    return facts


# --- census -------------------------------------------------------------------

def _census_key(v: dict) -> tuple:
    phase = "day_vote" if v["phase"] == "day_vote" else "day_discussion"
    return (v["game_id"], v["arm"], phase, int(v["day"]), v["speaker"],
            v.get("seq") if phase == "day_discussion" else None)


def _sidecar_index(sidecars: Path) -> dict[tuple, dict]:
    """(game_id, arm, phase, day, speaker, seq|None) → the turn's eval case."""
    idx: dict[tuple, dict] = {}
    for d in sorted(sidecars.glob("*")):
        m = re.match(r"loop_v2_full_(gen\d+)_(on|off)_g(\d+)_", d.name)
        if not m:
            continue
        gid = f"pair_v2_full_{m.group(1)}_g{m.group(3)}"
        arm = "all_enabled" if m.group(2) == "on" else "all_disabled"
        for f in sorted(d.glob("*.jsonl")):
            for line in open(f):
                o = json.loads(line)
                c = (o.get("output") or {}).get("eval_case")
                if not c or o.get("kind") != "agent_action_eval" or c["action_phase"] not in (
                        "day_discussion", "day_vote"):
                    continue
                seq = (c.get("agent_message") or {}).get("seq") \
                    if c["action_phase"] == "day_discussion" else None
                idx[(gid, arm, c["action_phase"], int(c["day"]), c["player_id"], seq)] = c
    return idx


def _dead_roster(record: dict, day: int) -> list[dict]:
    roles, roster = record["roles"], []
    for nr in record.get("night_resolutions") or []:
        if int(nr["day"]) + 1 <= day:
            roster += [{"player": p, "role": roles[p], "day": int(nr["day"]), "phase": "night"}
                       for p in nr.get("deaths") or []]
    for dr in record.get("day_resolutions") or []:
        if dr.get("voted_player") and int(dr["day"]) + 1 <= day:
            roster.append({"player": dr["voted_player"], "role": roles[dr["voted_player"]],
                           "day": int(dr["day"]), "phase": "day"})
    return sorted(roster, key=lambda e: (e["day"], 0 if e["phase"] == "night" else 1))


def _census_state(record: dict, case: dict) -> dict:
    """The engine state at this turn, rebuilt from the record and the turn's private context."""
    day, speaker = int(case["day"]), case["player_id"]
    roles, dead_from = record["roles"], death_timeline(record)
    alive = [p for p in roles if dead_from.get(p, 10**9) > day]
    channel = [m for m in record["day_channel"] if int(m["day"]) < day]
    # The moderator's same-day lines are mostly posted after the votes (the vote result, then the
    # night's deaths); the record files them under the day, but no day turn can have seen them. The
    # one the day's turns did see is the closing announcement, which the engine marks with its round.
    today = [m for m in record["day_channel"] if int(m["day"]) == day
             and (m["player"] != "game_master" or m.get("day_round") == "closing")]
    if case["action_phase"] == "day_discussion":  # the turn sees only what preceded it
        seq = (case.get("agent_message") or {}).get("seq") or 0
        today = [m for m in today if m["seq"] < seq]
    pc = case.get("private_context") or {}
    return {
        "roles": roles, "current_day": day, "current_round": 0,
        "surviving_villagers": [p for p in alive if roles[p] != "wolf"],
        "surviving_wolves": [p for p in alive if roles[p] == "wolf"],
        "human_players": [],
        "day_channel": channel + today,
        "day_summaries": [{"day": s["day"], "summary": s.get("summary", ""),
                           "structured": s.get("structured") or {}}
                          for s in record.get("day_summaries") or []],
        "dead_roster": _dead_roster(record, day),
        "agent_strategies": {speaker: pc.get("previous_strategy") or ""},
        "investigator_results": pc.get("investigator_results") or [],
        "vigilante_results": pc.get("vigilante_results") or [],
        "vigilante_bullets": 0,
        "wolf_channel": pc.get("wolf_channel") or [],
    }


def census_cases(cfg: dict) -> list[dict]:
    records = {}
    for f in sorted(REPO_ROOT.glob(cfg["runs_glob"])):
        for line in f.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                records[(r["game_id"], r.get("config_name", ""))] = r
    sidecars = _sidecar_index(REPO_ROOT / cfg["sidecars"])

    def rows(path, verdict):
        out = [json.loads(line) for line in (REPO_ROOT / path).read_text().splitlines() if line.strip()]
        return [v for v in out if (v.get("read") or {}).get("verdict") == verdict
                and v["phase"] != "night_action" and _census_key(v) in sidecars]

    positives = rows(cfg["stage2"], "hallucination")
    controls = [v for v in rows(cfg["stage1"], "consistent") if v.get("anchors")]

    # one case per turn: a turn's message and note can both carry verdicts
    by_turn: dict[tuple, list[dict]] = defaultdict(list)
    for v in positives:
        by_turn[_census_key(v)].append(v)
    control_turns = {_census_key(v): v for v in controls if _census_key(v) not in by_turn}

    rng = random.Random(cfg.get("seed", 11))

    def pick(keys: list[tuple], n: int | None) -> list[tuple]:
        """Stratified by phase, then role, so no one kind of turn dominates the set (None = all)."""
        rng.shuffle(keys)
        if n is None:
            return keys
        groups: dict[tuple, list] = defaultdict(list)
        for k in keys:
            groups[(k[2], records[k[:2]]["roles"][k[4]])].append(k)
        out: list[tuple] = []
        while len(out) < n and any(groups.values()):
            for g in sorted(groups):
                if groups[g] and len(out) < n:
                    out.append(groups[g].pop())
        return out

    cases = []
    for kind, keys, verdicts in (
            ("positive", pick(list(by_turn), cfg.get("n_positive")), by_turn),
            ("control", pick(list(control_turns), cfg.get("n_control")),
             {k: [v] for k, v in control_turns.items()})):
        for k in keys:
            record, case = records[k[:2]], sidecars[k]
            cases.append({
                "case_id": _case_id("census", *k), "source": "census", "kind": kind,
                "game_id": k[0], "game_arm": k[1], "phase": k[2], "day": k[3], "speaker": k[4],
                "role": case["player_role"],
                "state": _census_state(record, case),
                "firing_reason": (case.get("agent_message") or {}).get("firing_reason"),
                "memory": {"observations": case.get("retrieved_observations") or [],
                           "strategy_points": case.get("retrieved_strategy_points") or []},
                "facts": _facts(record),
                "golden": "",
                "original": [{"unit": v["unit"], "text": v["text"],
                              "error_class": v["read"].get("error_class")} for v in verdicts[k]],
            })
    return cases


# --- checkpoint (website games) -------------------------------------------------

def _checkpoint_state(game_id: str, day: int, channel_seq: int | None) -> dict:
    """The day-phase checkpoint just before the turn: today's channel ends at channel_seq - 1
    (a vote turn: the last checkpoint of that day's discussion)."""
    import psycopg
    from dotenv import dotenv_values
    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg.rows import dict_row

    from Agents.memory.checkpointer import durable_serde

    dsn = dotenv_values(REPO_ROOT / ".env")["WW_POSTGRES_DSN"]
    with psycopg.connect(dsn, autocommit=True, row_factory=dict_row,
                         options="-c default_transaction_read_only=on") as conn:
        saver = PostgresSaver(conn, serde=durable_serde())
        namespaces = [r["checkpoint_ns"] for r in conn.execute(
            "select distinct checkpoint_ns from checkpoints where thread_id=%s "
            "and checkpoint_ns like 'DAY_PHASE:%%'", (game_id,)).fetchall()]
        for ns in namespaces:
            for t in saver.list({"configurable": {"thread_id": game_id, "checkpoint_ns": ns}}):
                v = t.checkpoint["channel_values"]
                if v.get("current_day") != day:
                    break
                today = [m.seq for m in v.get("day_channel", []) if m.day == day]
                # the day's first message (channel_seq 0) follows a checkpoint with no entries yet
                if channel_seq is None or (today and max(today) == channel_seq - 1) \
                        or (channel_seq == 0 and not today):
                    return {k: to_jsonable_python(v.get(k)) for k in STATE_KEYS if k in v}
    raise LookupError(f"{game_id}: no day-{day} checkpoint before channel entry {channel_seq}")


def _night_targets(replay: dict) -> list[dict]:
    """Each night's targets from a replay's night events, in the shape the bench's night-record
    rebuild reads (games from before the engine kept the record)."""
    nights: dict[int, dict] = defaultdict(dict)
    field = {"healer": "healer_target", "serial_killer": "serial_killer_target", "vigilante": "vigilante_target"}
    for e in replay["events"]:
        if e["type"] == "night_action" and e.get("role") in field:
            nights[e["day"]][field[e["role"]]] = e.get("target")
        elif e["type"] == "wolf_kill_decided":
            nights[e["day"]]["wolves_target"] = e.get("target")
        elif e["type"] == "night_result":
            nights[e["day"]]["deaths"] = [d["player"] for d in e["deaths"]]
    return [{"day": d, **v} for d, v in sorted(nights.items())]


def checkpoint_cases(specs: list[dict], server: str = LIVE_SERVER) -> list[dict]:
    from evaluation.src.replay.hallucination_bench import night_actions_from_resolutions

    cases = []
    for s in specs:
        replay = get_json(f"{server}/replays/{s['game_id']}")
        record = record_from_replay(replay)
        seq = s.get("channel_seq")
        state = _checkpoint_state(s["game_id"], s["day"], seq)
        if "night_actions" not in state:
            state["night_actions"] = to_jsonable_python(night_actions_from_resolutions(
                _night_targets(replay), record["roles"], s["day"], record["day_resolutions"]))
        cases.append({
            "case_id": _case_id("checkpoint", s["game_id"], s["phase"], s["day"], s["speaker"], seq),
            "source": "checkpoint", "kind": s.get("kind", "positive"),
            "game_id": s["game_id"], "game_arm": "live", "phase": s["phase"], "day": s["day"],
            "speaker": s["speaker"], "role": record["roles"][s["speaker"]],
            "state": state,
            "firing_reason": s.get("firing_reason") or {"tier": "proactive", "owes": []},
            "memory": {"observations": [], "strategy_points": []},
            "facts": _facts(record),
            "golden": s.get("golden", ""),
            "original": s.get("original", []),
        })
    return cases


# --- curate: keep only the cases the current prompts still get wrong ---------------

def curate(cases: list[dict], judged: list[dict], min_bad_rate: float,
           random_slice: int = 0, seed: int = 11) -> list[dict]:
    """The bench's three slices, each case tagged ``slice``:

    - ``curated``: positives whose bad rate in a screen run (one arm of today's prompts) reaches
      ``min_bad_rate``. An old case today's prompt no longer gets wrong measures nothing for a prompt
      change. But the screen model chose these, so they lean toward its failure modes.
    - ``random``: ``random_slice`` positives drawn from the whole pool regardless of the screen,
      for comparing models without that lean (taken first, so the slices never overlap).
    - ``control``: every control (turns the census reader judged consistent).
    - ``pinned``: every hand-picked case with a written golden, kept whatever the screen says: it
      guards a known failure (a fix that passes today must keep passing).
    """
    per_case: dict[str, list[bool]] = defaultdict(list)
    for s in judged:
        if s["valid"]:
            per_case[s["case_id"]].append(s["bad"])
    positives = [c for c in cases if c["kind"] == "positive" and not c.get("golden")]
    rng = random.Random(seed)
    random_ids = {c["case_id"] for c in rng.sample(positives, min(random_slice, len(positives)))}
    kept = []
    for c in cases:
        runs = per_case.get(c["case_id"]) or []
        rate = sum(runs) / len(runs) if runs else 0.0
        tag = {"screen": {"bad": sum(runs), "samples": len(runs)}}
        if c.get("golden"):
            kept.append({**c, **tag, "slice": "pinned"})
        elif c["kind"] == "control":
            kept.append({**c, **tag, "slice": "control"})
        elif c["case_id"] in random_ids:
            kept.append({**c, **tag, "slice": "random"})
        elif runs and rate >= min_bad_rate:
            kept.append({**c, **tag, "slice": "curated"})
    return kept


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", required=True)
    args = ap.parse_args()
    cfg = json.loads(Path(args.config).read_text())
    out = REPO_ROOT / cfg["output"]
    if cfg.get("extend"):  # a new version of a frozen set: its cases plus newly built ones
        ext = cfg["extend"]
        if out.exists() and not cfg.get("overwrite"):
            raise SystemExit(f"{out} exists; set overwrite: true to replace it")
        read = lambda path: [json.loads(line) for line in (REPO_ROOT / path).read_text().splitlines() if line.strip()]  # noqa: E731
        cases = read(ext["from_dataset"]) + [{**c, "slice": ext["slice"]} for c in read(ext["add"])]
        with open(out, "w") as f:
            f.writelines(json.dumps(c) + "\n" for c in cases)
        manifest = {"eval_set_id": cfg["eval_set_id"], "scope": cfg.get("scope", "shared"),
                    "built_at": datetime.now(timezone.utc).isoformat(), "config": cfg, "n_cases": len(cases),
                    "slices": {k: sum(c.get("slice") == k for c in cases) for k in ("curated", "random", "control", "pinned")}}
        out.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))
        print(json.dumps({k: manifest[k] for k in ("n_cases", "slices")}))
        return
    if cfg.get("curate"):
        cur = cfg["curate"]
        if out.exists() and not cfg.get("overwrite"):
            raise SystemExit(f"{out} exists; set overwrite: true to replace it")
        source = [json.loads(line) for line in (REPO_ROOT / cur["from_dataset"]).read_text().splitlines() if line.strip()]
        judged = [json.loads(line) for line in (REPO_ROOT / cur["judged"]).read_text().splitlines() if line.strip()]
        cases = curate(source, judged, cur["min_bad_rate"], cur.get("random_slice", 0), cur.get("seed", 11))
        with open(out, "w") as f:
            f.writelines(json.dumps(c) + "\n" for c in cases)
        manifest = {"eval_set_id": cfg["eval_set_id"], "scope": cfg.get("scope", "shared"),
                    "built_at": datetime.now(timezone.utc).isoformat(), "config": cfg, "n_cases": len(cases),
                    "slices": {k: sum(c["slice"] == k for c in cases) for k in ("curated", "random", "control", "pinned")},
                    "of_positive": sum(c["kind"] == "positive" for c in source)}
        out.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))
        print(json.dumps({k: manifest[k] for k in ("n_cases", "slices", "of_positive")}))
        return
    if out.exists() and not cfg.get("overwrite"):
        raise SystemExit(f"{out} exists; set overwrite: true to replace it")

    cases = (census_cases(cfg["census"]) if cfg.get("census") else []) \
        + checkpoint_cases(cfg.get("checkpoint_cases") or [])
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w") as f:
        f.writelines(json.dumps(c) + "\n" for c in cases)
    counts: dict[str, int] = defaultdict(int)
    for c in cases:
        counts[f"{c['source']}/{c['kind']}/{c['phase']}/{c['role']}"] += 1
    manifest = {"eval_set_id": cfg["eval_set_id"], "scope": cfg.get("scope", "shared"),
                "built_at": datetime.now(timezone.utc).isoformat(),
                "config": cfg, "n_cases": len(cases), "counts": dict(sorted(counts.items()))}
    out.with_suffix(".manifest.json").write_text(json.dumps(manifest, indent=2))
    print(json.dumps({"wrote": str(out.relative_to(REPO_ROOT)), "n_cases": len(cases),
                      "counts": manifest["counts"]}, indent=2))


if __name__ == "__main__":
    main()
