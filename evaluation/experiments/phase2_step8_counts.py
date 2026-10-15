"""Phase 2 step 8: counts per game and per day for the comparison games, and the judge pass.

Record: evidence/game_play_enhancement/data/phase2_step8_games/ (README.md, report.md). The
questions are discussion_evidence.md §7.3's. Everything structural is counted from the records
with no model; the judge is discussion_evidence.py's evidence judge, reused as it is (read_messages
and score), run only with --judge and cached in the output folder.

Sources, newest design first (each count is reported only where the record has the field it
needs; a missing field is "n/a", never approximated):
  step8 game1..3   this step's games: record + chunk stream with arrival times + model-call log
  4c-catalogue     the step 6 recapture (notebooks/fixtures/chunk_catalogue_phase2.jsonl): the
                   sequential sweep under the gate's first prompt, before the held-not-re-asked ruling
  4c-rerun         two days replayed on the 4c-catalogue board after the rulings (days only)
  4b-smoke         the parallel proactive round's smoke game (transcript only, no votes)
  v2-832404e9      the June-scheduler v2 website game §7.3 names (replay endpoint; one human seat)

  poetry run python evaluation/experiments/phase2_step8_counts.py            # counts only
  poetry run python evaluation/experiments/phase2_step8_counts.py --judge    # + the judge pass
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluation.experiments.discussion_evidence import read_messages, review_sheet, score  # noqa: E402
from evaluation.src.core.settings import REPO_ROOT  # noqa: E402
from evaluation.src.data.sources.replay_api import LIVE_SERVER, get_json, record_from_replay  # noqa: E402
from evaluation.src.judges.config import DEFAULT_JUDGE_MODEL  # noqa: E402

DATA = REPO_ROOT / "evidence/game_play_enhancement/data"
OUT = DATA / "phase2_step8_games"
STEP8_LABELS = ["game1", "game2", "game3", "game4"]
BASELINE_V2 = "832404e9-a5f2-434e-8484-5bb953718a8f"
CATALOGUE = REPO_ROOT / "notebooks/fixtures/chunk_catalogue_phase2.jsonl"
EVIL = {"wolf", "serial_killer"}
CLOSING_PREFIX = "Before the vote:"


# --- loading: every source becomes {game_id, label, roles, day_channel, day_resolutions, ...} ----

def day_channel_from_chunks(chunks: list[dict]) -> list[dict]:
    """Every transcript entry the day graph committed (discuss, COLLECT_ROUND, START_CLOSING), once
    each, in (day, seq) order. These are the engine's own entries, so day_round, firing_reason and
    pass_reason are all there."""
    seen: dict[tuple[int, int], dict] = {}
    for chunk in chunks:
        if chunk["type"] != "updates" or not chunk["ns"] or not chunk["ns"][0].startswith("DAY_PHASE"):
            continue
        for node_name, delta in chunk["data"].items():
            if node_name.startswith("__") or not isinstance(delta, dict):
                continue
            for entry in delta.get("day_channel") or []:
                seen[(entry["day"], entry["seq"])] = entry
    ordered = []
    for key in sorted(seen):
        ordered.append(seen[key])
    return ordered


def closing_players_from_chunks(chunks: list[dict]) -> dict[int, list[str]]:
    """day -> the players START_CLOSING called, as the engine listed them (round_players). Read from
    the chunk rather than the transcript, because a closing turn that failed every attempt is
    recorded without its round (the technical pass drops day_round)."""
    called: dict[int, list[str]] = {}
    for chunk in chunks:
        if chunk["type"] != "updates":
            continue
        delta = chunk["data"].get("START_CLOSING")
        if not isinstance(delta, dict):
            continue
        day = delta["day_channel"][0]["day"]
        called[day] = list(delta.get("round_players") or [])
    return called


def day_windows(chunks: list[dict]) -> dict[int, dict]:
    """Per day: start/end times of the whole day (opening to the vote) and of its opening and closing
    rounds, from the chunks' arrival times. A day starts at the root chunk just before its first
    DAY_PHASE chunk and ends at the root DAY_PHASE chunk."""
    windows: dict[int, dict] = {}
    day = 0
    last_root_time = None
    current: dict | None = None
    for chunk in chunks:
        if chunk["type"] != "updates":
            continue
        if not chunk["ns"]:
            if "DAY_PHASE" in chunk["data"] and current is not None:
                current["end"] = chunk["t"]
                windows[day] = current
                current = None
            last_root_time = chunk["t"]
            continue
        if not chunk["ns"][0].startswith("DAY_PHASE"):
            continue
        if current is None:
            day += 1
            current = {"start": last_root_time, "rounds": []}
        for node_name in chunk["data"]:
            if node_name in ("START_OPENING", "START_CLOSING"):
                current["rounds"].append({"round": node_name, "start": chunk["t"]})
            if node_name == "COLLECT_ROUND" and current["rounds"]:
                current["rounds"][-1]["end"] = chunk["t"]
    return windows


def load_step8(label: str) -> dict:
    record = json.loads((OUT / f"{label}.record.json").read_text())
    manifest = json.loads((OUT / f"{label}.manifest.json").read_text())
    calls = json.loads((OUT / f"{label}.calls.json").read_text())
    chunks = []
    with (OUT / f"{label}.chunks.jsonl").open() as f:
        for line in f:
            chunks.append(json.loads(line))
    record["label"] = f"step8 {label}"
    record["design"] = "Phase 2 (HEAD): opening, sweep + echo gate, closing"
    record["windows"] = day_windows(chunks)
    record["closing_players"] = closing_players_from_chunks(chunks)
    record["calls"] = calls
    record["cost_usd"] = manifest.get("cost_usd")
    record["model"] = manifest.get("model")
    return record


def load_catalogue() -> dict:
    """The step 6 capture: translated to wire events (as the website stores a game) for the votes
    and roles, with the transcript taken straight from the chunks for the fields events drop."""
    from server.game.translate import Translator

    chunks = []
    with CATALOGUE.open() as f:
        header = json.loads(f.readline())["_header"]
        for line in f:
            chunks.append(json.loads(line))
    translator = Translator()
    events = []
    for chunk in chunks:
        for event in translator.translate(chunk):
            events.append(event.model_dump(mode="json"))
    winner = None
    for event in events:
        if event["type"] == "game_over":
            winner = event["winner"]
    record = record_from_replay({"game_id": "phase2-chunk-catalogue", "winner": winner, "events": events})
    record["day_channel"] = day_channel_from_chunks(chunks)
    record["closing_players"] = closing_players_from_chunks(chunks)
    record["label"] = "4c-catalogue"
    record["design"] = f"Phase 2 step 4c, first gate prompt (capture at {header['git'][:8]})"
    return record


def load_v2_baseline() -> dict:
    """The v2 website game, from the replay endpoint (cached beside the results). Its transcript
    has no rounds; the scheduler's tier is joined back from the firing_reason annotations."""
    cache = OUT / "baselines" / f"replay_{BASELINE_V2[:8]}.json"
    if cache.exists():
        replay = json.loads(cache.read_text())
    else:
        replay = get_json(f"{LIVE_SERVER}/replays/{BASELINE_V2}")
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(replay, indent=1))
    record = record_from_replay(replay)
    tiers: dict[tuple[int, int], str] = {}
    for event in replay["events"]:
        if event["type"] == "firing_reason":
            tiers[(event["day"], event["about_channel_seq"])] = event["tier"]
    for entry in record["day_channel"]:
        tier = tiers.get((entry["day"], entry["seq"]))
        if tier is not None:
            entry["firing_reason"] = {"tier": tier}
    record["label"] = "v2-832404e9"
    record["design"] = "v2 prompts, June scheduler (no rounds); one human seat"
    record["model"] = replay.get("model")
    return record


def load_4b_smoke() -> dict:
    raw = json.loads((DATA / "phase2_step4b_smoke_game_2026-10-07.json").read_text())
    return {"game_id": "phase2-step4b-smoke", "label": "4b-smoke",
            "design": "Phase 2 step 4b: parallel proactive rounds, no filters yet",
            "winner": raw["winner"], "roles": raw["roles"], "day_channel": raw["day_channel"],
            "duration_seconds": raw["seconds"], "humans": []}


def load_4c_rerun() -> dict:
    days = json.loads((DATA / "phase2_step4c_day_rerun_2026-10-07.json").read_text())
    channel = []
    seconds = {}
    survivors = {}
    for day in days:
        channel.extend(day["day_channel"])
        seconds[day["day"]] = day["seconds"]
        survivors[day["day"]] = len(day["survivors"])
    return {"game_id": "phase2-step4c-rerun", "label": "4c-rerun",
            "design": "Phase 2 step 4c after the rulings: two days replayed on the catalogue board",
            "roles": days[0]["roles"], "day_channel": channel, "humans": [],
            "rerun_seconds": seconds, "rerun_survivors": survivors}


# --- counting -------------------------------------------------------------------------------

def survivors_by_day(record: dict) -> dict[int, int]:
    """Living players at the start of each day, from the deaths the record holds; empty when it
    holds none (the transcript-only records)."""
    if record.get("rerun_survivors"):
        return dict(record["rerun_survivors"])
    if not record.get("day_resolutions") and not record.get("night_resolutions"):
        return {}
    days = set()
    for entry in record["day_channel"]:
        days.add(entry["day"])
    alive_at: dict[int, int] = {}
    for day in sorted(days):
        dead = set()
        for night in record.get("night_resolutions") or []:
            if night["day"] < day:
                for player in night.get("deaths") or []:
                    dead.add(player)
        for lynch in record.get("day_resolutions") or []:
            if lynch["day"] < day and lynch.get("voted_player"):
                dead.add(lynch["voted_player"])
        alive_at[day] = len(record["roles"]) - len(dead)
    return alive_at


def tier_of(entry: dict) -> str | None:
    """reactive / proactive. The 4b game's parallel proactive rounds stamped no firing reason;
    their lines carry day_round "proactive", which is read as the proactive tier."""
    firing = entry.get("firing_reason")
    if firing:
        return firing.get("tier")
    if entry.get("day_round") == "proactive":
        return "proactive"
    return None


def answers_someone_who_named_me(entry: dict, earlier: list[dict]) -> bool:
    """resolve.py's exemption, re-read from the record: the line is tagged as a response to a
    player whose earlier spoken line today named the speaker."""
    named_me = set()
    for other in earlier:
        if other.get("passed") or other["player"] == "game_master":
            continue
        for tag in other.get("addressed_targets") or []:
            if tag["target"] == entry["player"]:
                named_me.add(other["player"])
    for tag in entry.get("addressed_targets") or []:
        if tag["addressed_form"] == "response" and tag["target"] in named_me:
            return True
    return False


def count_day(record: dict, day: int, alive: int | None) -> dict:
    entries = []
    for entry in record["day_channel"]:
        if entry["day"] == day:
            entries.append(entry)
    humans = set(record.get("humans") or [])
    has_rounds = False
    for entry in entries:
        if entry.get("day_round", "discussion") != "discussion":
            has_rounds = True

    row: dict = {"day": day, "alive": alive}
    opening = []
    closing = []
    discussion = []
    moderator = []
    for entry in entries:
        if entry["player"] == "game_master":
            moderator.append(entry)
        elif entry.get("day_round") == "opening":
            opening.append(entry)
        elif entry.get("day_round") == "closing":
            closing.append(entry)
        else:
            discussion.append(entry)

    if has_rounds:
        spoken_openings = []
        held_openings = 0
        kinds: Counter = Counter()
        for entry in opening:
            if not entry.get("passed"):
                spoken_openings.append(entry["player"])
            if entry.get("pass_reason") == "opening_filtered":
                held_openings += 1
            if entry.get("opening_kind"):
                kinds[entry["opening_kind"]] += 1
        row["opening_turns"] = len(opening)
        row["opening_spoken"] = len(spoken_openings)
        row["opening_speakers"] = spoken_openings
        row["opening_held_by_filter"] = held_openings
        row["opening_kinds"] = dict(kinds)
    else:
        row["opening_turns"] = "n/a"

    spoken = 0
    reactive = 0
    sweep_lines = 0
    sweep_turns = 0
    held_echo = 0
    voluntary = 0
    failed = 0
    gate_calls = 0
    earlier: list[dict] = []
    for entry in opening + discussion:
        earlier_before = list(earlier)
        earlier.append(entry)
        if entry in opening:
            if not entry.get("passed"):
                spoken += 1
            continue
        tier = tier_of(entry)
        if entry.get("pass_reason") == "voluntary":
            voluntary += 1
        if entry.get("pass_reason") == "generation_failed":
            failed += 1
        if entry.get("pass_reason") == "novelty_gated":
            held_echo += 1
        if tier == "proactive":
            sweep_turns += 1
        if not entry.get("passed"):
            spoken += 1
            if tier == "reactive":
                reactive += 1
            elif tier == "proactive":
                sweep_lines += 1
        # the gate's calls, re-read: an agent's sweep turn with a line, after someone spoke today
        has_line = (not entry.get("passed")) or entry.get("pass_reason") == "novelty_gated"
        anyone_spoke = False
        for other in earlier_before:
            if not other.get("passed") and other["player"] != "game_master":
                anyone_spoke = True
        if (has_rounds and tier == "proactive" and has_line and entry["player"] not in humans
                and anyone_spoke and not answers_someone_who_named_me(entry, earlier_before)):
            gate_calls += 1

    row["discussion_turns"] = len(discussion)
    row["lines_before_closing"] = spoken
    row["reactive_lines"] = reactive
    row["sweep_turns"] = sweep_turns
    row["sweep_lines"] = sweep_lines
    row["held_by_echo_gate"] = held_echo
    row["voluntary_passes_in_discussion"] = voluntary
    row["generation_failed"] = failed
    row["gate_calls_derived"] = gate_calls if has_rounds else "n/a"

    if alive:
        cap = max(6, math.ceil(3.0 * alive))
        row["cap"] = cap
        row["cap_reached"] = spoken >= cap
    else:
        row["cap"] = "n/a"
        row["cap_reached"] = "n/a"

    closing_called = []
    for entry in moderator:
        if entry["message"].startswith(CLOSING_PREFIX):
            closing_called.append(entry["message"])
    defended = []
    called = (record.get("closing_players") or {}).get(day)
    if called is not None:
        defended = list(called)
    else:
        for entry in closing:
            defended.append(entry["player"])
    closing_spoken = 0
    for entry in closing:
        if not entry.get("passed"):
            closing_spoken += 1
    if has_rounds:
        row["closing_ran"] = bool(closing_called)
        row["closing_line"] = closing_called[0] if closing_called else ""
        row["defended"] = defended
        row["closing_spoken"] = closing_spoken
    else:
        row["closing_ran"] = "n/a"

    lynched = "n/a"
    for lynch in record.get("day_resolutions") or []:
        if lynch["day"] == day:
            lynched = lynch.get("voted_player") or "nobody"
    row["lynched"] = lynched
    if has_rounds and defended and lynched != "n/a":
        row["defended_lynched"] = lynched in defended
    row["lynched_role"] = record["roles"].get(lynched, "") if lynched not in ("n/a", "nobody") else ""

    windows = record.get("windows") or {}
    window = windows.get(day) or windows.get(str(day))
    if window:
        row["day_seconds"] = round(window["end"] - window["start"], 1)
        for one_round in window["rounds"]:
            name = "opening_seconds" if one_round["round"] == "START_OPENING" else "closing_seconds"
            if "end" in one_round:
                row[name] = round(one_round["end"] - one_round["start"], 1)
        calls_by_node: Counter = Counter()
        for call in record.get("calls") or []:
            in_day = (call.get("checkpoint_ns") or "").startswith("DAY_PHASE")
            if in_day and window["start"] <= call["started"] <= window["end"]:
                calls_by_node[call["node"]] += 1
        row["llm_calls"] = sum(calls_by_node.values())
        row["llm_calls_by_node"] = dict(calls_by_node)
    elif record.get("rerun_seconds"):
        row["day_seconds"] = record["rerun_seconds"].get(day, "n/a")
        row["llm_calls"] = "n/a"
    else:
        row["day_seconds"] = "n/a"
        row["llm_calls"] = "n/a"
    return row


def count_game(record: dict) -> dict:
    alive = survivors_by_day(record)
    days = set()
    for entry in record["day_channel"]:
        days.add(entry["day"])
    rows = []
    for day in sorted(days):
        rows.append(count_day(record, day, alive.get(day)))
    night_calls = 0
    for call in record.get("calls") or []:
        if not (call.get("checkpoint_ns") or "").startswith("DAY_PHASE"):
            night_calls += 1
    return {
        "game_id": record["game_id"],
        "label": record["label"],
        "design": record["design"],
        "model": record.get("model", ""),
        "winner": record.get("winner"),
        "days": len(rows),
        "seconds": record.get("duration_seconds", "n/a"),
        "cost_usd": record.get("cost_usd", "n/a"),
        "llm_calls_total": len(record["calls"]) if record.get("calls") else "n/a",
        "llm_calls_outside_day": night_calls if record.get("calls") else "n/a",
        "per_day": rows,
    }


# --- the judge: claims and labels -------------------------------------------------------------

def claims_from_reads(rows: list[dict], record: dict) -> dict:
    """Role claims the judge saw: who claimed what, which were evil, which were counterclaims (a
    role two different players claimed, villager aside), and which were made in an opening."""
    opening_seqs = set()
    for entry in record["day_channel"]:
        if entry.get("day_round") == "opening":
            opening_seqs.add((entry["day"], entry["seq"]))
    claimants: dict[str, list[str]] = defaultdict(list)
    claims = []
    for row in sorted(rows, key=lambda r: (r["day"], r["seq"])):
        read = row.get("read") or {}
        claimed = read.get("self_claim", "none")
        if claimed == "none":
            continue
        in_opening = (row["day"], row["seq"]) in opening_seqs
        claims.append({"day": row["day"], "speaker": row["speaker"], "claimed": claimed,
                       "actual": row["speaker_role"], "in_opening": in_opening})
        if row["speaker"] not in claimants[claimed]:
            claimants[claimed].append(row["speaker"])
    first_by_speaker = {}
    for claim in claims:
        first_by_speaker.setdefault((claim["speaker"], claim["claimed"]), claim)
    counterclaimed = []
    for role, players in claimants.items():
        if role != "villager" and len(players) >= 2:
            counterclaimed.append({"role": role, "players": players})
    evil_claims = []
    for claim in first_by_speaker.values():
        if claim["actual"] in EVIL:
            evil_claims.append(claim)
    return {"claims": list(first_by_speaker.values()), "evil_claims": evil_claims,
            "evil_claims_in_opening": [c for c in evil_claims if c["in_opening"]],
            "counterclaims": counterclaimed}


def run_judge(records: list[dict], model: str, workers: int) -> None:
    for record in records:
        folder = OUT / "judge" / record["label"].replace(" ", "_")
        if (folder / "reads.jsonl").exists():
            print(f"judge: {record['label']} already read, skipping (delete {folder} to re-read)")
            continue
        folder.mkdir(parents=True, exist_ok=True)
        rows = read_messages([record], model, workers)
        with (folder / "reads.jsonl").open("w") as f:
            for row in rows:
                f.write(json.dumps(row) + "\n")
        (folder / "summary.json").write_text(json.dumps({"model": model, "judge": score(rows, [record])}, indent=2))
        (folder / "review.md").write_text(review_sheet(rows))
        print(f"judge: {record['label']}: {len(rows)} messages read")


def judge_results(record: dict) -> dict | None:
    folder = OUT / "judge" / record["label"].replace(" ", "_")
    if not (folder / "reads.jsonl").exists():
        return None
    rows = []
    with (folder / "reads.jsonl").open() as f:
        for line in f:
            rows.append(json.loads(line))
    summary = json.loads((folder / "summary.json").read_text())["judge"]
    read_ok = [r for r in rows if r.get("read")]
    turn_taking = 0
    reveal_timing = 0
    for row in read_ok:
        if "turn_taking" in row["read"]["bases"]:
            turn_taking += 1
        if "reveal_timing" in row["read"]["bases"]:
            reveal_timing += 1
    return {
        "messages_read": len(read_ok),
        "turn_taking": f"{turn_taking}/{len(read_ok)}",
        "reveal_timing": f"{reveal_timing}/{len(read_ok)}",
        "share_of_messages_using": summary["share_of_messages_using"],
        **claims_from_reads(rows, record),
    }


# --- output ---------------------------------------------------------------------------------

def markdown(results: list[dict]) -> str:
    out = ["# Phase 2 step 8 counts", "",
           "Written by evaluation/experiments/phase2_step8_counts.py; n/a = the record lacks the field.", ""]
    for game in results:
        out += [f"## {game['label']} ({game['design']})", "",
                f"winner {game['winner']}, {game['days']} days, {game['seconds']} s, model calls "
                f"{game['llm_calls_total']} (outside the day {game['llm_calls_outside_day']}), "
                f"cost ${game['cost_usd']}", "",
                "| day | alive | openings spoken/turns | held by filter | lines before closing | "
                "reactive | sweep lines/turns | held by gate | voluntary passes | cap | closing: defended "
                "| lynched | day s | opening s | LLM calls |",
                "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
        for d in game["per_day"]:
            openings = "n/a" if d["opening_turns"] == "n/a" else f"{d['opening_spoken']}/{d['opening_turns']}"
            held = d.get("opening_held_by_filter", "n/a")
            if d["closing_ran"] == "n/a":
                closing = "n/a"
            elif d["closing_ran"]:
                closing = ", ".join(d["defended"])
                if "defended_lynched" in d:
                    closing += " (lynched)" if d["defended_lynched"] else " (survived)"
            else:
                closing = "none"
            cap = d["cap"] if d["cap"] == "n/a" else f"{d['lines_before_closing']}/{d['cap']}"
            lynched = d["lynched"]
            if d.get("lynched_role"):
                lynched += f" ({d['lynched_role']})"
            out.append(f"| {d['day']} | {d['alive'] or 'n/a'} | {openings} | {held} | "
                       f"{d['lines_before_closing']} | {d['reactive_lines']} | "
                       f"{d['sweep_lines']}/{d['sweep_turns']} | {d['held_by_echo_gate']} | "
                       f"{d['voluntary_passes_in_discussion']} | {cap} | {closing} | {lynched} | "
                       f"{d['day_seconds']} | {d.get('opening_seconds', 'n/a')} | {d['llm_calls']} |")
        if game.get("judge"):
            j = game["judge"]
            out += ["", f"Judge ({j['messages_read']} agent messages): turn_taking {j['turn_taking']}, "
                        f"reveal_timing {j['reveal_timing']}; evil claims {len(j['evil_claims'])} "
                        f"(in an opening {len(j['evil_claims_in_opening'])}); counterclaims "
                        f"{j['counterclaims'] or 'none'}"]
        out.append("")
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--judge", action="store_true", help="run the evidence judge where not cached")
    ap.add_argument("--model", default=DEFAULT_JUDGE_MODEL)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    records = []
    for label in STEP8_LABELS:
        if (OUT / f"{label}.record.json").exists():
            records.append(load_step8(label))
    records.append(load_catalogue())
    records.append(load_4c_rerun())
    records.append(load_4b_smoke())
    records.append(load_v2_baseline())

    if args.judge:
        judged = []
        for record in records:
            if record["label"].startswith("step8") or record["label"] == "v2-832404e9":
                judged.append(record)
        run_judge(judged, args.model, args.workers)

    results = []
    for record in records:
        game = count_game(record)
        game["judge"] = judge_results(record)
        results.append(game)
    (OUT / "counts.json").write_text(json.dumps(results, indent=1))
    (OUT / "counts.md").write_text(markdown(results))
    print(markdown(results))


if __name__ == "__main__":
    main()
