"""Whiff-conversion audit — does an attacker convert a silent SK-whiff into action?

The §1 SK-wolf information-design gap of `scheduler_bias_log.md`, measured directly. When an
attacker (wolf night-kill / vigilante shot) hits the night-immune serial killer, the attack SILENTLY
whiffs (`Agents/nodes/night/resolution.py:92-100,149`): the immune target is excluded from `deaths`,
no death line is announced, and if it was the only attack the GM prints "No one died last night".
This module asks, over the persisted records, whether the attacker converts that private event into
action, and if not, which layer failed:

  Layer 1 VISIBILITY  — what the attacker sees the morning after (a code/payload fact, documented as
                        constants below with file:line, not computed from records).
  Layer 2 BEHAVIOR    — a deterministic join: did the attacker accuse / vote / re-target the target?
  Layer 3 FLOOR       — did the attacker have the discussion floor to convert (reuse WS2 machinery).
  + reasoning scan    — keyword co-occurrence over the attacker's post-whiff strategy notes (v6ab
                        sidecars only); separates "never noticed" from "noticed, didn't convert".

Sibling to `scheduler_access_audit.py` (imports its record-loading + timeline helpers). Kept
separate because it runs on BOTH validation sets (not the 50-game access set) and its concern —
attacker conversion — is orthogonal to floor access. All definitions are pinned in the log's ③.E
pre-registration block. Zero LLM calls.

    poetry run python -m evaluation.src.experiments.whiff_conversion_audit run
"""

from __future__ import annotations

import argparse
import glob
import json
from collections import defaultdict
from pathlib import Path

from evaluation.src.experiments.scheduler_access_audit import (
    DATA_DIR,
    ON_FILES,
    OFF_FILES,
    REPO_ROOT,
    alive_at_start_of_day,
    all_days,
    day_messages,
    load_records,
)

# --------------------------------------------------------------------------- validation sets
# v5 = the same 50-game access-audit set (no sidecars). v6ab = the 180-game proxy set (6 memory
# arms x 30 seeds; siblings share game_id so events are correlated across arms). Kept separate.
V5_FILES = OFF_FILES + ON_FILES
V6AB_FILES = sorted(Path(p).stem for p in glob.glob(str(REPO_ROOT / "batch_results" / "v6ab_*.jsonl")))

ATTACKERS = ("wolf", "vigilante")

# Reasoning-scan tokens (pre-reg ③.E side-read). Conservative whole-field co-occurrence with a
# target-name form; documented as a heuristic, never a judge.
_INFER_TOKENS = (
    "survive", "immune", "failed", "fail to", "heal", "didn't die", "did not die",
    "unharmed", "still alive", "no one died", "nobody died", "no death", "didn't work",
    "did not work", "couldn't kill", "could not kill", "wasn't killed", "was not killed",
    "blocked", "protected", "night-immune", "night immune", "escaped",
)


# --------------------------------------------------------------------------- Layer 1 (static facts)
# What the attacker actually sees the morning after a whiff — a code/payload read, not a record
# computation. Documented as constants (file:line) so the artifact is self-contained.
LAYER1_VISIBILITY = {
    "wolf": {
        "own_kill_target_visible": True,
        "how": "persisted in wolf_channel, which accumulates all game (orchestrator.one_more_day "
               "clears wolves_kill_target but NOT wolf_channel; init sets it [] once) and is replayed "
               "into every wolf-night payload (state/night/wolf.py:47, prompts/night.py:176).",
        "explicit_kill_failed_signal": False,
        "how_not": "resolution.py:92-100 marks the SK-immune outcome and resolution.py:149 `continue` "
                   "DROPS it from the GM announcement (silent whiff); if it was the only attack the GM "
                   "prints 'No one died last night' (resolution.py:164). No wolf-side field says the "
                   "kill failed.",
        "only_inferable_absence": True,
        "note": "The wolf must JOIN {my target = T, from wolf_channel} x {no death announced for T} to "
                "infer heal-or-immune, and CANNOT distinguish heal from immune from public info.",
    },
    "vigilante": {
        "own_kill_target_visible": True,
        "explicit_kill_failed_signal": True,
        "how": "resolution.py:139-143 writes an EXPLICIT private note to vigilante_results on an immune "
               "outcome: 'you shot T, but they were unharmed - immune to night kills, which confirms T "
               "is the serial killer.' Fed into the next VIGILANTE_NIGHT prompt (prompts/night.py:124). "
               "A heal does NOT trigger it (resolution.py:138) so there is no false positive.",
        "only_inferable_absence": False,
        "bullet_consumed_on_whiff": True,
        "bullet_note": "resolution.py:133-134 spends a bullet on any shot, including a whiff.",
        "note": "The vigilante is handed the SK identity outright and pre-disambiguated from a heal. "
                "Change E (whiff disclosure) is a WOLF-side change; the vigilante already has it.",
    },
}


# --------------------------------------------------------------------------- record helpers


def _roles(record: dict) -> dict:
    return record.get("roles", {}) or {}


def _players_with_role(record: dict, role: str) -> set[str]:
    return {p for p, r in _roles(record).items() if r == role}


def _votes_by_day(record: dict) -> dict[int, list[dict]]:
    out: dict[int, list[dict]] = {}
    for d in record.get("day_resolutions", []) or []:
        out[d.get("day")] = d.get("votes", []) or []
    return out


def _wolf_targets_by_night(record: dict) -> dict[int, str | None]:
    return {nr.get("day"): nr.get("wolves_target") for nr in record.get("night_resolutions", []) or []}


def _vig_targets_by_night(record: dict) -> dict[int, str | None]:
    return {nr.get("day"): nr.get("vigilante_target") for nr in record.get("night_resolutions", []) or []}


# --------------------------------------------------------------------------- event detection


def target_survived_events(record: dict) -> list[dict]:
    """Per-night target-survived events for both attackers (pre-reg ③.E-a/b).

    A target-survived event = the attacker's target is set but absent from `deaths`. Per
    resolution.py it survives for exactly two reasons: immune (SK-whiff) or healed. The SK check is
    first, mirroring `_resolved`.
    """
    events: list[dict] = []
    for nr in record.get("night_resolutions", []) or []:
        night = nr.get("day")
        deaths = set(nr.get("deaths") or [])
        healer_target = nr.get("healer_target")

        wt = nr.get("wolves_target")
        if wt and wt not in deaths:
            if nr.get("wolf_target_role") == "serial_killer":
                gt = "sk_whiff"
            elif nr.get("healer_saved") or wt == healer_target:
                gt = "healed"
            else:
                gt = "other"  # should not occur per _resolved; kept to catch anomalies
            events.append({"attacker": "wolf", "night": night, "target": wt, "ground_truth": gt,
                           "target_role": nr.get("wolf_target_role")})

        vt = nr.get("vigilante_target")
        if vt and not nr.get("vigilante_kill_landed"):
            if nr.get("vigilante_target_role") == "serial_killer":
                gt = "sk_whiff"
            elif vt == healer_target:
                gt = "healed"
            else:
                gt = "other"
            events.append({"attacker": "vigilante", "night": night, "target": vt, "ground_truth": gt,
                           "target_role": nr.get("vigilante_target_role")})
    return events


def dedup_events(events: list[dict]) -> list[dict]:
    """Keep the earliest whiff night per (attacker, target) — the point the info first exists."""
    first: dict[tuple, dict] = {}
    for ev in events:
        key = (ev["attacker"], ev["target"])
        if key not in first or ev["night"] < first[key]["night"]:
            first[key] = ev
    return sorted(first.values(), key=lambda e: (e["attacker"], e["night"]))


# --------------------------------------------------------------------------- Layer 2 (behavior)


def _attacker_players(record: dict, attacker: str) -> set[str]:
    return _players_with_role(record, "wolf" if attacker == "wolf" else "vigilante")


def _accused_voted(record: dict, attackers: set[str], target: str, days: list[int],
                   votes_by_day: dict[int, list[dict]]) -> tuple[bool, bool]:
    """Did any attacker accuse (addressed_target) or vote (day_resolutions) the target on `days`?"""
    accused = voted = False
    for day in days:
        live = attackers & alive_at_start_of_day(record, day)
        if not live:
            continue
        for m in day_messages(record, day):
            if m.get("passed") or m.get("player") not in live:
                continue
            for at in m.get("addressed_targets", []) or []:
                if at.get("target") == target and at.get("stance") == "accusation":
                    accused = True
        for v in votes_by_day.get(day, []):
            if v.get("voter") in live and v.get("votee") == target:
                voted = True
    return accused, voted


def _accused_voted_any_other(record: dict, attackers: set[str], target: str, days: list[int],
                             votes_by_day: dict[int, list[dict]]) -> bool:
    """General propensity: did any attacker accuse/vote SOME non-target player on `days`?"""
    for day in days:
        live = attackers & alive_at_start_of_day(record, day)
        if not live:
            continue
        for m in day_messages(record, day):
            if m.get("passed") or m.get("player") not in live:
                continue
            for at in m.get("addressed_targets", []) or []:
                t = at.get("target")
                if t and t != target and t not in attackers and at.get("stance") == "accusation":
                    return True
        for v in votes_by_day.get(day, []):
            votee = v.get("votee")
            if v.get("voter") in live and votee not in (None, "abstain", target) and votee not in attackers:
                return True
    return False


def conversion_for_event(record: dict, ev: dict, votes_by_day: dict[int, list[dict]]) -> dict:
    """Layer-2 join for a single deduped event (pre-reg ③.E-c/d)."""
    attackers = _attacker_players(record, ev["attacker"])
    target, night = ev["target"], ev["night"]
    days = all_days(record)
    post_days = [d for d in days if d >= night + 1]
    pre_days = [d for d in days if d <= night]

    post_acc, post_vote = _accused_voted(record, attackers, target, post_days, votes_by_day)
    pre_acc, pre_vote = _accused_voted(record, attackers, target, pre_days, votes_by_day)
    post_other = _accused_voted_any_other(record, attackers, target, post_days, votes_by_day)

    # Night re-target (reported separately; futile against the immune SK).
    retarget = False
    tgt_by_night = (_wolf_targets_by_night if ev["attacker"] == "wolf" else _vig_targets_by_night)(record)
    for n, t in tgt_by_night.items():
        if n is not None and n > night and t == target:
            retarget = True

    # "What instead": did the attacker keep killing OTHER players on later nights?
    kept_killing_others = any(
        n is not None and n > night and t and t != target
        for n, t in tgt_by_night.items()
    )

    converted = post_acc or post_vote
    return {
        "converted": converted,
        "post_accused": post_acc,
        "post_voted": post_vote,
        "pre_target_directed": pre_acc or pre_vote,
        "post_accused_other": post_other,
        "night_retarget": retarget,
        "kept_killing_others": kept_killing_others,
    }


# --------------------------------------------------------------------------- Layer 3 (floor)


def floor_for_event(record: dict, ev: dict) -> dict:
    """Non-pass turns + declined offers (pass markers) for the attacker over the conversion window."""
    attackers = _attacker_players(record, ev["attacker"])
    nonpass = passes = 0
    for day in [d for d in all_days(record) if d >= ev["night"] + 1]:
        live = attackers & alive_at_start_of_day(record, day)
        if not live:
            continue
        for m in day_messages(record, day):
            if m.get("player") not in live:
                continue
            if m.get("passed"):
                passes += 1
            else:
                nonpass += 1
    return {"nonpass_turns": nonpass, "passes": passes, "had_floor": nonpass > 0}


# --------------------------------------------------------------------------- reasoning scan (sidecar)


def _mention_forms(player_id: str) -> list[str]:
    n = player_id.split("_")[-1]
    return [player_id.lower(), f"player {n}", f"player{n}"]


def _field_matches(text: str, target: str) -> bool:
    low = (text or "").lower()
    if not any(f in low for f in _mention_forms(target)):
        return False
    return any(tok in low for tok in _INFER_TOKENS)


def _load_sidecar_cases(record: dict) -> list[dict]:
    """Attacker-relevant eval cases from the record's local sidecar (v6ab only; [] if none)."""
    pointer = record.get("eval_cases_path")
    if not pointer:
        return []
    path = REPO_ROOT / pointer
    if not path.exists():
        return []
    cases = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        span = json.loads(line)
        ec = (span.get("output") or {}).get("eval_case") if isinstance(span.get("output"), dict) else None
        if ec:
            cases.append(ec)
    return cases


def reasoning_scan_for_event(cases: list[dict], record: dict, ev: dict, converted: bool) -> dict:
    """Keyword co-occurrence over the attacker's POST-whiff strategy notes (pre-reg ③.E side-read)."""
    role = "wolf" if ev["attacker"] == "wolf" else "vigilante"
    target, night = ev["target"], ev["night"]
    samples: list[str] = []
    mentioned = False
    for c in cases:
        if c.get("player_role") != role or (c.get("day") or 0) < night + 1:
            continue
        for field in (c.get("updated_strategy"), (c.get("private_context") or {}).get("previous_strategy")):
            if field and _field_matches(field, target):
                mentioned = True
                if field not in samples:
                    samples.append(field)
    if not mentioned:
        cls = "never_mentions"
    elif converted:
        cls = "mentions_and_acts"
    else:
        cls = "mentions_no_act"
    return {"class": cls, "mentioned": mentioned, "samples": samples[:2]}


# --------------------------------------------------------------------------- aggregation


def _blank_agg() -> dict:
    return {
        "n_events_raw": 0, "n_events_dedup": 0,
        "converted": 0, "post_accused": 0, "post_voted": 0,
        "pre_target_directed": 0, "post_accused_other": 0,
        "night_retarget": 0, "kept_killing_others": 0,
        "floor_had": 0, "floor_nonpass_total": 0, "floor_passes_total": 0,
    }


def _rate(num: int, den: int) -> float | None:
    return round(num / den, 3) if den else None


def audit_set(records: list[dict], with_sidecars: bool) -> dict:
    # agg[attacker][ground_truth]
    agg: dict[str, dict[str, dict]] = {a: {"sk_whiff": _blank_agg(), "healed": _blank_agg()}
                                       for a in ATTACKERS}
    raw_counts: dict[str, dict[str, int]] = {a: defaultdict(int) for a in ATTACKERS}
    scan = {"sidecar_games": 0, "total_games": len(records),
            "classes": {a: defaultdict(int) for a in ATTACKERS},
            "samples": []}
    detail: list[dict] = []
    votes_cache: dict[int, dict] = {}

    for record in records:
        events = target_survived_events(record)
        for ev in events:
            gt = ev["ground_truth"]
            if gt in ("sk_whiff", "healed"):
                raw_counts[ev["attacker"]][gt] += 1

        cases = _load_sidecar_cases(record) if with_sidecars else []
        has_sidecar = bool(cases)
        if has_sidecar:
            scan["sidecar_games"] += 1
        vbd = _votes_by_day(record)

        for ev in dedup_events(events):
            gt = ev["ground_truth"]
            if gt not in ("sk_whiff", "healed"):
                continue
            a = agg[ev["attacker"]][gt]
            a["n_events_dedup"] += 1
            conv = conversion_for_event(record, ev, vbd)
            a["converted"] += conv["converted"]
            a["post_accused"] += conv["post_accused"]
            a["post_voted"] += conv["post_voted"]
            a["pre_target_directed"] += conv["pre_target_directed"]
            a["post_accused_other"] += conv["post_accused_other"]
            a["night_retarget"] += conv["night_retarget"]
            a["kept_killing_others"] += conv["kept_killing_others"]
            fl = floor_for_event(record, ev)
            a["floor_had"] += fl["had_floor"]
            a["floor_nonpass_total"] += fl["nonpass_turns"]
            a["floor_passes_total"] += fl["passes"]

            row = {"run_id": record.get("run_id"), "game_id": record.get("game_id"),
                   "attacker": ev["attacker"], "night": ev["night"], "target": ev["target"],
                   "ground_truth": gt, **conv, **{f"floor_{k}": v for k, v in fl.items()}}
            if has_sidecar:
                rs = reasoning_scan_for_event(cases, record, ev, conv["converted"])
                row["reasoning_class"] = rs["class"]
                scan["classes"][ev["attacker"]][rs["class"]] += 1
                for s in rs["samples"]:
                    if len(scan["samples"]) < 12:
                        scan["samples"].append({"attacker": ev["attacker"], "target": ev["target"],
                                                "ground_truth": gt, "class": rs["class"], "line": s})
            detail.append(row)

    # finalize raw counts + rates
    for a in ATTACKERS:
        for gt in ("sk_whiff", "healed"):
            agg[a][gt]["n_events_raw"] = raw_counts[a][gt]
            g = agg[a][gt]
            n = g["n_events_dedup"]
            g["rates"] = {
                "converted": _rate(g["converted"], n),
                "post_accused": _rate(g["post_accused"], n),
                "post_voted": _rate(g["post_voted"], n),
                "pre_target_directed": _rate(g["pre_target_directed"], n),
                "post_accused_other": _rate(g["post_accused_other"], n),
                "night_retarget": _rate(g["night_retarget"], n),
                "kept_killing_others": _rate(g["kept_killing_others"], n),
                "floor_had": _rate(g["floor_had"], n),
            }
        scan["classes"][a] = dict(scan["classes"][a])
    return {"aggregate": agg, "reasoning_scan": scan, "detail": detail}


# --------------------------------------------------------------------------- cli


def run() -> dict:
    v5 = load_records(V5_FILES)
    v6 = load_records(V6AB_FILES)
    payload = {
        "meta": {
            "v5_files": V5_FILES, "v5_games": len(v5),
            "v6ab_files": V6AB_FILES, "v6ab_games": len(v6),
            "definitions": "evidence/metrics/metrics_audit/scheduler_bias_log.md §3 ③.E pre-registration",
        },
        "layer1_visibility": LAYER1_VISIBILITY,
        "v5": audit_set(v5, with_sidecars=False),   # v5 has no sidecars
        "v6ab": audit_set(v6, with_sidecars=True),
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    out = DATA_DIR / "whiff_conversion.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=False))
    print(f"whiff-conversion -> {out}")
    for label in ("v5", "v6ab"):
        print(f"\n=== {label} ===")
        for a in ATTACKERS:
            for gt in ("sk_whiff", "healed"):
                g = payload[label]["aggregate"][a][gt]
                print(f"{a:9s} {gt:8s} N(raw/dedup)={g['n_events_raw']}/{g['n_events_dedup']} "
                      f"conv={g['rates']['converted']} acc={g['rates']['post_accused']} "
                      f"vote={g['rates']['post_voted']} pre={g['rates']['pre_target_directed']} "
                      f"other={g['rates']['post_accused_other']} retgt={g['rates']['night_retarget']} "
                      f"floor={g['rates']['floor_had']}")
        rs = payload[label]["reasoning_scan"]
        print(f"reasoning: sidecar_games={rs['sidecar_games']}/{rs['total_games']} classes={rs['classes']}")
    return payload


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=["run"], nargs="?", default="run")
    ap.parse_args()
    run()


if __name__ == "__main__":
    main()
