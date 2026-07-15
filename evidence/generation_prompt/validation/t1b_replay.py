"""T1b — counterfactual decision replay of the 4 confirmed hallucination cases (dated study code).

Replays each confirmed case's exact discussion turn under three prompt arms, WITHOUT touching live
code: the live role template is imported and its message text string-patched at runtime (the same
direct-chain-call pattern as the 2026-06-13 reorder probes). Arms:

  A baseline    — live template with the `== Dead so far ==` block REMOVED (the generation-era
                  prompt: v2_full predates the dead-roster block that now sits in the template).
  B board       — live template as-is (structured dead roster, `format_dead_roster`).
  C full_board  — board + an attacker-typed roster line + the derived `Roles still in play` line
                  (the alive-roles design under evaluation; attacker type targets case 4).

Fidelity notes (recorded, not hidden): memory context and previous_strategy are COLD in all arms
(store state at the original turn is not reproducible; symmetric across arms), and generation runs
at live temp 1.0, so per-sample variance is expected — each case×arm is sampled K times and graded
for RECURRENCE of its error class, not for reproducing the original wording.

Grading: composition cases via the standing audit's count regexes vs the true alive-wolf count;
case 4 (attacker misattribution) via an attacker-verb regex near the victim id; all raw outputs
persisted to t1b_outputs.jsonl for the confirming read.

Run:  poetry run python evidence/generation_prompt/validation/t1b_replay.py --smoke   (1 call)
      poetry run python evidence/generation_prompt/validation/t1b_replay.py --k 6     (full)
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # repo root (dated study script)

from Agents.llm_factory.accessors import get_llm
from Agents.prompts.day_discuss import INVESTIGATOR_DAY_DISCUSS, VILLAGER_DAY_DISCUSS
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas.game_events import DayChannel, DaySummary, DeathRecord, InvestigatorResult
from Agents.schemas.output import DayDiscussOutput
from evaluation.src.audits.role_hallucination_screen import COUNT_CLAIM, _NUM, death_timeline
from langchain_core.prompts import ChatPromptTemplate

HERE = Path(__file__).parent
RUNS = Path("evidence/v7_final/runs/v2_full")

CASES = [
    dict(case=1, game_id="pair_v2_full_gen1_g3", speaker="player_6", day=3, seq=2,
         kind="composition", note="'only two wolves left' — 1 alive"),
    dict(case=2, game_id="pair_v2_full_gen4_g3", speaker="player_7", day=5, seq=0,
         kind="composition", note="'the remaining wolf' — 0 remain"),
    dict(case=3, game_id="pair_v2_full_gen5_g3", speaker="player_6", day=4, seq=11,
         kind="composition", note="'two wolves ... remaining' — 0 remain"),
    dict(case=4, game_id="pair_v2_full_gen6_g2", speaker="player_8", day=3, seq=2,
         kind="attacker", victim="player_2", true_attacker="wolves",
         note="'the serial killer hit player_2' — wolves killed p2"),
]

TEMPLATES = {"villager": VILLAGER_DAY_DISCUSS, "investigator": INVESTIGATOR_DAY_DISCUSS}
DEAD_BLOCK = "== Dead so far (public) ==\n{dead_roster}\n"
ALIVE_BLOCK = ("== Dead so far (public) ==\n{dead_roster}\n\n"
               "== Roles still in play (fixed cast minus revealed deaths) ==\n{alive_roles}\n")


def load_record(game_id: str, arm_hint: str) -> dict:
    for f in sorted(RUNS.glob("gen*_o*.jsonl")):
        for line in f.read_text().splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r["game_id"] == game_id and r.get("config_name", "") == arm_hint:
                return r
    raise SystemExit(f"record not found: {game_id} ({arm_hint})")


def patched_template(base: ChatPromptTemplate, arm: str) -> ChatPromptTemplate:
    msgs = []
    for m in base.messages:
        text = m.prompt.template
        role = "system" if type(m).__name__.startswith("System") else "human"
        if arm == "baseline":
            text = text.replace(DEAD_BLOCK, "")
        elif arm == "full_board":
            text = text.replace(DEAD_BLOCK, ALIVE_BLOCK)
        msgs.append((role, text))
    return ChatPromptTemplate.from_messages(msgs)


def roster_records(record: dict, day: int, *, attacker_typed: bool) -> tuple[list[DeathRecord], str]:
    """DeathRecords known by `day` + (for full_board) attacker-typed line overrides via role text."""
    roles, entries = record["roles"], []
    for nr in record.get("night_resolutions") or []:
        d = int(nr["day"])
        if d + 1 > day:
            continue
        for p in nr.get("deaths") or []:
            attacker = ("wolves" if nr.get("wolves_target") == p and nr.get("kill_successful")
                        else "the serial killer" if nr.get("serial_killer_target") == p
                        else "the vigilante" if nr.get("vigilante_target") == p else "unknown")
            role = roles[p] + (f", killed by {attacker}" if attacker_typed else "")
            entries.append(DeathRecord(player=p, role=role, day=d, phase="night"))
    for dr in record.get("day_resolutions") or []:
        d, vp = int(dr["day"]), dr.get("voted_player")
        if vp and d + 1 <= day:
            entries.append(DeathRecord(player=vp, role=roles[vp], day=d, phase="day"))
    entries.sort(key=lambda e: (e.day, 0 if e.phase == "night" else 1))
    alive = [p for p in roles if p not in {e.player for e in entries}]
    counts: dict[str, int] = {}
    for p in alive:
        counts[roles[p]] = counts.get(roles[p], 0) + 1
    order = ["wolf", "serial_killer", "healer", "investigator", "vigilante", "villager"]
    alive_line = ", ".join(f"{counts[r]} {r.replace('_', ' ')}{'s' if counts[r] > 1 and r == 'villager' else ''}"
                           for r in order if counts.get(r)) or "none"
    return entries, alive_line


def build_payload(record: dict, case: dict, arm: str) -> dict:
    day, seq, speaker = case["day"], case["seq"], case["speaker"]
    roles = record["roles"]
    dead_from = death_timeline(record)
    alive = [p for p in roles if dead_from.get(p, 10**9) > day]
    channel = [DayChannel(**m) for m in record["day_channel"]
               if int(m["day"]) == day and int(m["seq"]) < seq]
    summaries = [DaySummary(day=int(s["day"]), summary=s["summary"], structured=s.get("structured") or {})
                 for s in record.get("day_summaries") or [] if int(s["day"]) < day]
    roster, alive_line = roster_records(record, day, attacker_typed=(arm == "full_board"))
    original = next(m for m in record["day_channel"]
                    if int(m["day"]) == day and int(m["seq"]) == seq)
    payload = {
        "player_id": speaker, "player_role": roles[speaker], "current_day": day,
        "surviving_players": alive, "day_channel": channel, "day_summaries": summaries,
        "dead_roster": roster if arm != "baseline" else [],
        "firing_reason": original.get("firing_reason"),
        "investigator_results": [InvestigatorResult(**r) for r in record.get("investigator_results") or []
                                 if int(r["day"]) < day] if roles[speaker] == "investigator" else [],
    }
    keys = build_agent_prompt_input(payload)
    keys["alive_roles"] = alive_line
    return keys


def grade(case: dict, record: dict, message: str) -> list[str]:
    hits = []
    if case["kind"] == "composition":
        dead_from = death_timeline(record)
        alive_wolves = sum(1 for p, r in record["roles"].items()
                           if r == "wolf" and dead_from.get(p, 10**9) > case["day"])
        for m in COUNT_CLAIM.finditer(message):
            n = _NUM.get(m.group(1).lower())
            if n is not None and n != alive_wolves:
                hits.append(f"count_claim:{m.group(0)}(alive={alive_wolves})")
        if re.search(r"\bremaining wol(f|ves)\b|\bwol(f|ves)\s+(?:still\s+)?(left|remain)", message, re.I) \
                and alive_wolves == 0:
            hits.append("remaining_wolf_when_zero")
    else:
        v = case["victim"]
        for m in re.finditer(re.escape(v), message):
            window = message[max(0, m.start() - 90): m.end() + 90]
            if re.search(r"serial[ _-]?killer", window, re.I) and \
                    re.search(r"\b(hit|kill\w*|took|murder\w*|claim\w* the life)\b", window, re.I):
                hits.append(f"sk_attribution_near_{v}")
    return hits


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--k", type=int, default=6, help="samples per case per arm")
    ap.add_argument("--smoke", action="store_true", help="one call only")
    args = ap.parse_args()

    llm = get_llm().with_structured_output(DayDiscussOutput)
    out_path = HERE / "t1b_outputs.jsonl"
    results = []
    with out_path.open("a") as fh:
        for case in CASES:
            arm_hint = "all_enabled"  # all four cases came from ON-arm records
            record = load_record(case["game_id"], arm_hint)
            tpl_base = TEMPLATES[record["roles"][case["speaker"]]]
            for arm in ("baseline", "board", "full_board"):
                tpl = patched_template(tpl_base, arm)
                keys = build_payload(record, case, arm)
                n = 1 if args.smoke else args.k
                for i in range(n):
                    out = llm.invoke(tpl.invoke(keys))
                    msg = out.message or ""
                    hits = grade(case, record, msg)
                    row = dict(case=case["case"], arm=arm, sample=i, pass_turn=out.pass_turn,
                               hits=hits, message=msg)
                    fh.write(json.dumps(row) + "\n")
                    results.append(row)
                    print(f"case{case['case']} {arm} #{i}: pass={out.pass_turn} "
                          f"hits={hits or 'clean'}")
                if args.smoke:
                    return
    # summary
    print("\n=== recurrence by case x arm ===")
    for case in CASES:
        for arm in ("baseline", "board", "full_board"):
            rows = [r for r in results if r["case"] == case["case"] and r["arm"] == arm]
            bad = sum(1 for r in rows if r["hits"])
            print(f"case{case['case']} {arm:10s} {bad}/{len(rows)} error-recurrence "
                  f"(pass_turn {sum(r['pass_turn'] for r in rows)}/{len(rows)})")


if __name__ == "__main__":
    main()
