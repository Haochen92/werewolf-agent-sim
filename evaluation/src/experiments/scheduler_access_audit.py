"""Scheduler access audit — does the role-blind sequential scheduler starve specific role behaviors?

Workstream 2, diagnostics A/B/C (all $0, deterministic, over existing batch records). The
role-blind scheduler is defensible by design, but role-blind *access* is not the same as
role-neutral *opportunity*; this module measures, from the persisted `day_channel`, whether the
starvation the design never checked for actually shows up. See
`evidence/metrics/metrics_audit/scheduler_bias_log.md` for the motivation, pre-registered
definitions, and the reading discipline (these are DESCRIPTIVE audits — access, not win cost;
diagnostic D, not in this module, is what speaks to outcomes).

Subcommands:
  floor-access    (A) per role x day: turns, reactive/proactive share, spoke-zero rate, passes;
                      + investigator-with-pending-find and wolf-before-bandwagon joins.
  gate-silencing  (B) can novelty-gated passes be told apart from voluntary passes / never-offered?
  reveal-withhold (C) the four-way decomposition of confirmed finds that never converted to a lynch.
  all             run all three, write every artifact.

    poetry run python -m evaluation.src.experiments.scheduler_access_audit all

Artifacts land in evidence/metrics/metrics_audit/data/. Timeline convention and all three matched
definitions are pinned in the log's §3 pre-registration block.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve()
REPO_ROOT = HERE.parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

DATA_DIR = REPO_ROOT / "evidence" / "metrics" / "metrics_audit" / "data"

# Same 50-game validation set as evidence/metrics/proxy_win_monotonicity.py (kept in lockstep so the
# access audits and the proxy-trust work describe the same epoch).
OFF_FILES = ["v5_seed_b1", "v5_seed_b2", "v5_seed_b3", "v5_seed_b4", "v5_baseline_pad"]
ON_FILES = ["v5_1_b1", "v5_1_b2", "v5_1_b3", "v5_1_b4"]

THREAT_ROLES = {"wolf", "serial_killer"}

# Reveal matcher tokens (pre-registered §3c; reused from investigator_transmission.py's convention).
_ROLE_CLAIM_TOKENS = (
    "i am the investigator",
    "i'm the investigator",
    "as the investigator",
    "my role as investigator",
    "my investigation",
    "my findings",
)
_BASIS_TOKENS = ("investigat", "i checked", "i identified", "confirmed", "my result", "scan")
_THREAT_TOKENS = ("wolf", "serial killer", "sk")


# --------------------------------------------------------------------------- loading


def load_records(names: list[str]) -> list[dict]:
    """Successful game records from the named batch_results JSONL files."""
    records = []
    for name in names:
        path = REPO_ROOT / "batch_results" / f"{name}.jsonl"
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            record = json.loads(line)
            if record.get("status") == "success":
                records.append(record)
    return records


# --------------------------------------------------------------------------- timeline


def lynched_by_day(record: dict) -> dict[int, str]:
    """{day: lynched_player} from day_resolutions (voted_player only, ignoring no-vote days)."""
    out: dict[int, str] = {}
    for d in record.get("day_resolutions", []) or []:
        if d.get("voted_player"):
            out[d["day"]] = d["voted_player"]
    return out


def night_deaths_by_day(record: dict) -> dict[int, set[str]]:
    """{night_day: set(dead)} — deaths on night N, announced day N+1."""
    out: dict[int, set[str]] = {}
    for nr in record.get("night_resolutions", []) or []:
        out[nr["day"]] = set(nr.get("deaths", []) or [])
    return out


def alive_at_start_of_day(record: dict, day: int) -> set[str]:
    """Cast roster minus everyone lynched on an earlier day or killed on an earlier night.

    Night N (result day=N) is announced day N+1, so a night-N death is gone by the start of
    day N+1: it counts against day D iff N <= D-1. Lynches on day k are resolved at the end of
    day k, so they count against day D iff k < D.
    """
    dead: set[str] = set()
    for k, player in lynched_by_day(record).items():
        if k < day:
            dead.add(player)
    for n, deaths in night_deaths_by_day(record).items():
        if n <= day - 1:
            dead |= deaths
    return set(record.get("roles", {})) - dead


def death_day_of(record: dict, player: str) -> int | None:
    """The day at the START of which `player` is first absent (lynched day k -> k+1; night n -> n+1).
    None if the player survived to game end."""
    days = []
    for k, p in lynched_by_day(record).items():
        if p == player:
            days.append(k + 1)
    for n, deaths in night_deaths_by_day(record).items():
        if player in deaths:
            days.append(n + 1)
    return min(days) if days else None


def day_messages(record: dict, day: int) -> list[dict]:
    """This day's non-game_master day_channel entries (passes included), seq order."""
    return sorted(
        (m for m in record.get("day_channel", []) or []
         if m.get("day") == day and m.get("player") != "game_master"),
        key=lambda m: m.get("seq", 0),
    )


def all_days(record: dict) -> list[int]:
    return sorted({m.get("day") for m in record.get("day_channel", []) or []
                   if m.get("player") != "game_master"})


# --------------------------------------------------------------------------- (a) bandwagon


def bandwagon_seq(record: dict, day: int) -> int | None:
    """The first seq on `day` at which a single target holds >=2 distinct accusers (pre-reg §3a).
    None if no bandwagon forms that day."""
    accusers: dict[str, set[str]] = defaultdict(set)
    for m in day_messages(record, day):
        if m.get("passed"):
            continue
        speaker = m.get("player")
        for at in m.get("addressed_targets", []) or []:
            if at.get("stance") == "accusation" and at.get("target") and at["target"] != speaker:
                accusers[at["target"]].add(speaker)
                if len(accusers[at["target"]]) >= 2:
                    return m.get("seq")
    return None


# --------------------------------------------------------------------------- (c) reveal matcher


def _mention_forms(player_id: str) -> list[str]:
    n = player_id.split("_")[-1]
    return [player_id.lower(), f"player {n}", f"player{n}"]


def is_find_disclosure(message: str, target: str) -> bool:
    """Pre-reg §3c: names target AND an investigation-basis token AND a threat-role token."""
    text = (message or "").lower()
    if not any(f in text for f in _mention_forms(target)):
        return False
    if not any(b in text for b in _BASIS_TOKENS):
        return False
    return any(t in text for t in _THREAT_TOKENS)


def is_role_claim(message: str) -> bool:
    text = (message or "").lower()
    return any(tok in text for tok in _ROLE_CLAIM_TOKENS)


# --------------------------------------------------------------------------- A. floor access


def floor_access(records: list[dict]) -> dict:
    """Per role x day floor-access table + the investigator-pending and wolf-bandwagon joins."""
    # role -> aggregate counters
    turns = defaultdict(int)          # real (non-passed) utterances
    reactive = defaultdict(int)       # real utterances fired reactive
    proactive_real = defaultdict(int) # real utterances fired proactive
    passes = defaultdict(int)         # proactive pass markers
    alive_days = defaultdict(int)     # (role, player, day) cells where player was alive
    spoke_zero = defaultdict(int)     # of those cells, how many had zero real utterances

    for record in records:
        roles = record.get("roles", {})
        for day in all_days(record):
            alive = alive_at_start_of_day(record, day)
            msgs = day_messages(record, day)
            real_by_player = Counter()
            for m in msgs:
                role = roles.get(m.get("player"))
                if role is None:
                    continue
                fr = m.get("firing_reason") or {}
                tier = fr.get("tier")
                if m.get("passed"):
                    passes[role] += 1
                    continue
                turns[role] += 1
                real_by_player[m["player"]] += 1
                if tier == "reactive":
                    reactive[role] += 1
                else:
                    proactive_real[role] += 1
            for player in alive:
                role = roles.get(player)
                if role is None:
                    continue
                alive_days[role] += 1
                if real_by_player[player] == 0:
                    spoke_zero[role] += 1

    per_role = {}
    for role in sorted(alive_days):
        t = turns[role]
        per_role[role] = {
            "real_utterances": t,
            "reactive_share": round(reactive[role] / t, 3) if t else None,
            "proactive_share": round(proactive_real[role] / t, 3) if t else None,
            "passes": passes[role],
            "pass_rate_of_offers": round(passes[role] / (proactive_real[role] + passes[role]), 3)
            if (proactive_real[role] + passes[role]) else None,
            "alive_player_days": alive_days[role],
            "spoke_zero_days": spoke_zero[role],
            "spoke_zero_rate": round(spoke_zero[role] / alive_days[role], 3) if alive_days[role] else None,
            "turns_per_alive_day": round(t / alive_days[role], 3) if alive_days[role] else None,
        }

    inv_join = _investigator_pending_join(records)
    wolf_join = _wolf_bandwagon_join(records)
    return {"per_role": per_role, "investigator_pending_join": inv_join, "wolf_bandwagon_join": wolf_join}


def _investigator_pending_join(records: list[dict]) -> dict:
    """Join (i): investigator holding a pending threat find at the start of a day -> did they take a
    non-pass turn that day (i.e. before the blind vote)? (All discussion precedes the vote.)"""
    cells = 0
    spoke = 0
    per_game = []
    for record in records:
        roles = record.get("roles", {})
        inv = next((p for p, r in roles.items() if r == "investigator"), None)
        if inv is None:
            continue
        results = record.get("investigator_results", []) or []
        for day in all_days(record):
            if inv not in alive_at_start_of_day(record, day):
                continue
            lynched_before = {p for k, p in lynched_by_day(record).items() if k < day}
            alive_now = alive_at_start_of_day(record, day)
            pending = [
                r for r in results
                if r.get("role_revealed") in THREAT_ROLES
                and r.get("day", 99) <= day - 1
                and r.get("player_investigated") in alive_now
                and r.get("player_investigated") not in lynched_before
            ]
            if not pending:
                continue
            cells += 1
            spoke_today = any(
                (not m.get("passed")) and m.get("player") == inv for m in day_messages(record, day)
            )
            if spoke_today:
                spoke += 1
            per_game.append({
                "run_id": record.get("run_id"),
                "day": day,
                "pending_targets": [r["player_investigated"] for r in pending],
                "investigator_spoke": spoke_today,
            })
    return {
        "pending_find_days": cells,
        "spoke_before_vote": spoke,
        "spoke_rate": round(spoke / cells, 3) if cells else None,
        "detail": per_game,
    }


def _wolf_bandwagon_join(records: list[dict]) -> dict:
    """Join (ii): on days a bandwagon formed, did any wolf get a PROACTIVE non-pass turn BEFORE it
    formed (a chance to shape/start the pile-on)? And was that wolf among the target's accusers?"""
    bandwagon_days = 0
    wolf_proactive_before = 0
    wolf_accuser_before = 0
    detail = []
    for record in records:
        roles = record.get("roles", {})
        wolves = {p for p, r in roles.items() if r == "wolf"}
        for day in all_days(record):
            bseq = bandwagon_seq(record, day)
            if bseq is None:
                continue
            live_wolves = wolves & alive_at_start_of_day(record, day)
            if not live_wolves:
                continue
            bandwagon_days += 1
            proactive_before = False
            accuser_before = False
            for m in day_messages(record, day):
                if m.get("seq", 0) >= bseq:
                    break
                if m.get("player") not in live_wolves or m.get("passed"):
                    continue
                fr = m.get("firing_reason") or {}
                if fr.get("tier") == "proactive":
                    proactive_before = True
                if any(at.get("stance") == "accusation" for at in m.get("addressed_targets", []) or []):
                    accuser_before = True
            if proactive_before:
                wolf_proactive_before += 1
            if accuser_before:
                wolf_accuser_before += 1
            detail.append({
                "run_id": record.get("run_id"),
                "day": day,
                "bandwagon_seq": bseq,
                "wolf_proactive_before": proactive_before,
                "wolf_accuser_before": accuser_before,
            })
    return {
        "bandwagon_days_with_live_wolf": bandwagon_days,
        "wolf_proactive_turn_before_formation": wolf_proactive_before,
        "wolf_proactive_before_rate": round(wolf_proactive_before / bandwagon_days, 3)
        if bandwagon_days else None,
        "wolf_already_accusing_before_formation": wolf_accuser_before,
        "wolf_accuser_before_rate": round(wolf_accuser_before / bandwagon_days, 3)
        if bandwagon_days else None,
        "detail": detail,
    }


# --------------------------------------------------------------------------- B. gate silencing


def gate_silencing(records: list[dict]) -> dict:
    """Establish what pass persistence supports. In this epoch a novelty-gated pass and a voluntary
    pass_turn are written by the SAME code path to an IDENTICAL DayChannel(passed=True, message="",
    firing_reason=<proactive>) — the gated candidate text is discarded. So the two are
    indistinguishable from records, and the gate's selectivity is unmeasurable. We report the
    distinguishability finding + the raw pass census (all we CAN count)."""
    pass_tiers = Counter()
    passes_by_role = Counter()
    passes_with_message = 0            # would signal gated-text persistence if >0
    passes_with_addressed = 0
    real_by_role = Counter()
    proactive_real_by_role = Counter()
    for record in records:
        roles = record.get("roles", {})
        for m in record.get("day_channel", []) or []:
            if m.get("player") == "game_master":
                continue
            role = roles.get(m.get("player"))
            fr = m.get("firing_reason") or {}
            if m.get("passed"):
                pass_tiers[fr.get("tier")] += 1
                passes_by_role[role] += 1
                if (m.get("message") or "").strip():
                    passes_with_message += 1
                if m.get("addressed_targets"):
                    passes_with_addressed += 1
            else:
                real_by_role[role] += 1
                if fr.get("tier") == "proactive":
                    proactive_real_by_role[role] += 1
    per_role = {}
    for role in sorted(set(passes_by_role) | set(proactive_real_by_role)):
        offers = passes_by_role[role] + proactive_real_by_role[role]
        per_role[role] = {
            "proactive_passes": passes_by_role[role],
            "proactive_reals": proactive_real_by_role[role],
            "pass_share_of_proactive_offers": round(passes_by_role[role] / offers, 3) if offers else None,
        }
    return {
        "distinguishable": passes_with_message > 0,
        "gated_text_persisted": passes_with_message > 0,
        "pass_tier_distribution": dict(pass_tiers),
        "passes_with_nonempty_message": passes_with_message,
        "passes_with_addressed_targets": passes_with_addressed,
        "per_role": per_role,
        "note": (
            "Novelty-gated pass and voluntary pass_turn share one write path (Agents/turn/agent.py) "
            "producing an identical passed=True/empty-message/proactive marker; the attempted-but-gated "
            "message is never persisted. Gate selectivity by role/stance is UNMEASURABLE from records. "
            "Fix is a small instrumentation change (persist a gate flag + the gated candidate on the "
            "pass marker), to PROPOSE not build."
        ),
    }


# --------------------------------------------------------------------------- C. reveal / withhold


def reveal_withhold(records: list[dict]) -> dict:
    """Four-way decomposition of confirmed threat finds that never converted to a lynch of the find.

    For each (game, investigator, find on threat T):
      converted        -> T was lynched on a day >= find-available (excluded from the 4-way split)
      NO_FLOOR         -> investigator never took a non-pass turn while the find was pending
      LATE_FLOOR       -> investigator's only non-pass turns came after T died / game decided
      WITHHELD         -> had >=1 non-pass turn with the find pending but never disclosed it (§3c)
      REVEALED_IGNORED -> disclosed the find (§3c) while pending, town still didn't convert
    """
    classes = Counter()
    by_found_role = defaultdict(lambda: Counter())  # found_role -> {converted, unconverted}
    role_claim_coverage = {"finds": 0, "any_role_claim_by_inv": 0}
    detail = []
    for record in records:
        roles = record.get("roles", {})
        inv = next((p for p, r in roles.items() if r == "investigator"), None)
        if inv is None:
            continue
        lynched = lynched_by_day(record)
        game_last_day = max(all_days(record), default=0)
        # Dedup by target (a re-investigated wolf yields two rows) — keep the earliest find night.
        finds: dict[str, dict] = {}
        for r in record.get("investigator_results", []) or []:
            if r.get("role_revealed") not in THREAT_ROLES:
                continue
            t = r.get("player_investigated")
            if t not in finds or r.get("day", 99) < finds[t].get("day", 99):
                finds[t] = r
        for r in finds.values():
            target = r.get("player_investigated")
            avail_day = r.get("day", 0) + 1
            # Converted iff T lynched on/after the find became usable.
            lynch_day = next((k for k, p in lynched.items() if p == target), None)
            if lynch_day is not None and lynch_day >= avail_day:
                classes["CONVERTED"] += 1
                by_found_role[r.get("role_revealed")]["converted"] += 1
                continue
            by_found_role[r.get("role_revealed")]["unconverted"] += 1

            role_claim_coverage["finds"] += 1
            t_death = death_day_of(record, target)      # day T first absent (any cause)
            # Days the find is pending: from avail_day up to the last day T is still alive & unlynched.
            pending_end = game_last_day
            if t_death is not None:
                pending_end = min(pending_end, t_death - 1)

            spoke_days = []          # days inv took a non-pass turn (any)
            disclosed_pending = False
            spoke_pending = False
            for day in all_days(record):
                if inv not in alive_at_start_of_day(record, day):
                    continue
                inv_msgs = [m for m in day_messages(record, day)
                            if m.get("player") == inv and not m.get("passed")]
                if inv_msgs:
                    spoke_days.append(day)
                if avail_day <= day <= pending_end:
                    if inv_msgs:
                        spoke_pending = True
                    if any(is_find_disclosure(m.get("message", ""), target) for m in inv_msgs):
                        disclosed_pending = True

            if any(is_role_claim(m.get("message", ""))
                   for m in record.get("day_channel", []) or [] if m.get("player") == inv):
                role_claim_coverage["any_role_claim_by_inv"] += 1

            if disclosed_pending:
                cls = "REVEALED_IGNORED"
            elif spoke_pending:
                cls = "WITHHELD"
            elif not spoke_days:
                cls = "NO_FLOOR"
            else:
                # spoke, but never while the find was pending -> only after T died / decided.
                cls = "LATE_FLOOR"
            classes[cls] += 1
            detail.append({
                "run_id": record.get("run_id"),
                "investigator": inv,
                "target": target,
                "found_role": r.get("role_revealed"),
                "find_night": r.get("day"),
                "available_day": avail_day,
                "pending_end_day": pending_end,
                "target_death_day": t_death,
                "class": cls,
            })

    unconverted = sum(v for k, v in classes.items() if k != "CONVERTED")
    dist = {k: classes[k] for k in
            ("NO_FLOOR", "LATE_FLOOR", "WITHHELD", "REVEALED_IGNORED") if classes.get(k)}
    return {
        "total_threat_finds": sum(classes.values()),
        "converted_to_lynch": classes["CONVERTED"],
        "unconverted": unconverted,
        "conversion_rate": round(classes["CONVERTED"] / sum(classes.values()), 3)
        if sum(classes.values()) else None,
        "by_found_role": {
            role: {
                "converted": c["converted"],
                "unconverted": c["unconverted"],
                "conversion_rate": round(c["converted"] / (c["converted"] + c["unconverted"]), 3)
                if (c["converted"] + c["unconverted"]) else None,
            }
            for role, c in by_found_role.items()
        },
        "unconverted_breakdown": dist,
        "unconverted_breakdown_pct": {
            k: round(v / unconverted, 3) for k, v in dist.items()
        } if unconverted else {},
        "role_claim_coverage": role_claim_coverage,
        "detail": detail,
    }


# --------------------------------------------------------------------------- cli


def _write(name: str, payload: dict) -> Path:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / name
    path.write_text(json.dumps(payload, indent=2, sort_keys=False))
    return path


def _run(which: str) -> None:
    records = load_records(OFF_FILES + ON_FILES)
    meta = {"n_games": len(records), "files": OFF_FILES + ON_FILES}
    if which in ("floor-access", "all"):
        out = {"meta": meta, **floor_access(records)}
        p = _write("floor_access.json", out)
        print(f"[A] floor-access -> {p}")
        print(json.dumps({r: v for r, v in out["per_role"].items()}, indent=2))
        print("investigator_pending_join:", json.dumps(
            {k: v for k, v in out["investigator_pending_join"].items() if k != "detail"}))
        print("wolf_bandwagon_join:", json.dumps(
            {k: v for k, v in out["wolf_bandwagon_join"].items() if k != "detail"}))
    if which in ("gate-silencing", "all"):
        out = {"meta": meta, **gate_silencing(records)}
        p = _write("gate_silencing.json", out)
        print(f"[B] gate-silencing -> {p}")
        print(json.dumps({k: v for k, v in out.items() if k not in ("meta", "detail")}, indent=2))
    if which in ("reveal-withhold", "all"):
        out = {"meta": meta, **reveal_withhold(records)}
        p = _write("reveal_withhold.json", out)
        print(f"[C] reveal-withhold -> {p}")
        print(json.dumps({k: v for k, v in out.items() if k != "detail"}, indent=2))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("cmd", choices=["floor-access", "gate-silencing", "reveal-withhold", "all"])
    args = ap.parse_args()
    _run(args.cmd)


if __name__ == "__main__":
    main()
