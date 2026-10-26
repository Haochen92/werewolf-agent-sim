"""T2 + T3 — paired decision replay: non-regression + reads soundness + the ordering A/B.

Replays frozen v2_full decisions (from the eval-case sidecars, which preserve the ORIGINAL
retrieved memories, previous_strategy, and the agent's recorded verdicts + action) under prompt/
schema arms, with zero live-code changes (templates string-patched, variant schemas defined here —
the T1b/June-13 pattern):

  arm A `old`         — dead-roster block removed (generation-era prompt).
  arm B `board`       — current template (day: roster block; night: roster INSERTED — the proposed
                        night extension, exploratory).
  arm C `reads_first` — day_vote only: script-defined schema, verdicts -> READS -> strategy -> vote.
  arm D `reads_after` — day_vote only: verdicts -> strategy -> READS -> vote (the ordering A/B).

Metrics: schema validity; verdict coverage (verdicts emitted / memories shown); follow/override/
not_relevant distribution; verdict agreement with the ORIGINAL recorded verdicts; action vs the
original action (flip rate); output tokens. Arms C/D additionally: read completeness, role-guess
accuracy vs true roles (masked + golden probes), unclear/confidence/why degeneracy.

Fidelity: memories + previous_strategy come from the sidecar (NOT cold); day transcript from the
game record; abstain allowed everywhere (noted caveat — a few original votes may be forced-day).

Run:  poetry run python evidence/generation_prompt/validation/regression_replay.py --smoke
      poetry run python evidence/generation_prompt/validation/regression_replay.py --n-vote 40 --n-night 20
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # repo root (dated study script)

from pydantic import BaseModel, Field

from Agents.llm_factory.accessors import get_llm
from Agents.prompts import day_vote as dv
from Agents.prompts import night as nt
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas import RetrievedObservation, RetrievedStrategyPoint
from Agents.schemas.game_events import DayChannel, DaySummary, DeathRecord, InvestigatorResult
from Agents.schemas.output import (
    DayVoteOutput, HealerOutput, InvestigatorOutput, MemoryVerdict, SerialKillerOutput,
    StrategyVerdict, VigilanteOutput,
)
from evaluation.src.audits.role_hallucination_screen import death_timeline
from langchain_core.prompts import ChatPromptTemplate

HERE = Path(__file__).parent
RUNS = Path("evidence/v7_final/runs/v2_full")
SIDECARS = Path("batch_results/v2_full/eval_cases")

VOTE_TPL = {"villager": dv.VILLAGER_DAY_VOTE, "healer": dv.HEALER_DAY_VOTE,
            "investigator": dv.INVESTIGATOR_DAY_VOTE, "wolf": dv.WOLF_DAY_VOTE,
            "serial_killer": dv.SERIAL_KILLER_DAY_VOTE, "vigilante": dv.VIGILANTE_DAY_VOTE}
NIGHT_TPL = {"healer": (nt.HEALER_NIGHT, HealerOutput, "healer_target"),
             "investigator": (nt.INVESTIGATOR_NIGHT, InvestigatorOutput, "investigator_target"),
             "serial_killer": (nt.SERIAL_KILLER_NIGHT, SerialKillerOutput, "serial_killer_target"),
             "vigilante": (nt.VIGILANTE_NIGHT, VigilanteOutput, "vigilante_target")}

ROLE_ENUM = Literal["unclear", "villager", "healer", "investigator", "vigilante", "wolf", "serial_killer"]


class PlayerRead(BaseModel):
    player: str = Field(description="A living player's ID (never your own).")
    why: str = Field(description="One line of evidence for this read; write 'unchanged' if your read has not moved.")
    suspected_role: ROLE_ENUM = Field(description="Your best guess of this player's role; 'unclear' if you cannot tell.")
    confidence: Literal["low", "high"] = Field(description="How sure you are.")


class VoteReadsFirst(BaseModel):  # verdicts -> READS -> strategy -> action
    strategy_verdicts: list[StrategyVerdict] = Field(default_factory=list, description="One verdict per numbered strategy point shown, in order; empty list if none shown.")
    memory_applicability: list[MemoryVerdict] = Field(default_factory=list, description="One verdict per numbered observation shown, in order; empty list if none shown.")
    reads: list[PlayerRead] = Field(description="One read per living player other than yourself.")
    updated_strategy: str
    vote_target: str


class VoteReadsAfter(BaseModel):  # verdicts -> strategy -> READS -> action
    strategy_verdicts: list[StrategyVerdict] = Field(default_factory=list, description="One verdict per numbered strategy point shown, in order; empty list if none shown.")
    memory_applicability: list[MemoryVerdict] = Field(default_factory=list, description="One verdict per numbered observation shown, in order; empty list if none shown.")
    updated_strategy: str
    reads: list[PlayerRead] = Field(description="One read per living player other than yourself.")
    vote_target: str


READS_BODY_INSTRUCTION = ("\nBefore your vote, record your current read on EVERY living player except "
                          "yourself — one entry each (best-guess role, or 'unclear').\n")
# enumerated variant (post-T2 completeness fix probe): targets injected per turn, never hard-coded
READS_ENUM_INSTRUCTION = ("\nBefore your vote, record your current read — one entry each for: "
                          "{read_targets} (best-guess role, or 'unclear').\n")


def patch(base: ChatPromptTemplate, *, drop_board: bool = False, insert_board_night: bool = False,
          add_reads_line: bool = False, enum_reads_line: bool = False) -> ChatPromptTemplate:
    msgs = []
    for m in base.messages:
        text = m.prompt.template
        role = "system" if type(m).__name__.startswith("System") else "human"
        if drop_board and "{dead_roster}" in text:
            text = re.sub(r"[^\n]*Dead so far[^\n]*\n\{dead_roster\}\n?", "", text)
            text = text.replace("{dead_roster}", "")
        if insert_board_night and "{day_summaries}" in text:
            text = text.replace("{day_summaries}",
                                "Dead so far (public): {dead_roster}\n\n{day_summaries}", 1)
        if add_reads_line and role == "human":
            text = (READS_ENUM_INSTRUCTION if enum_reads_line else READS_BODY_INSTRUCTION) + text
        msgs.append((role, text))
    return ChatPromptTemplate.from_messages(msgs)


def load_records() -> dict[tuple[str, str], dict]:
    recs = {}
    for f in sorted(RUNS.glob("gen*_o*.jsonl")):
        for line in f.read_text().splitlines():
            if line.strip():
                r = json.loads(line)
                recs[(r["game_id"], r.get("config_name", ""))] = r
    return recs


def sample_cases(n_vote: int, n_night: int) -> list[dict]:
    votes, nights = [], []
    for d in sorted(SIDECARS.glob("*_on_*")):
        for f in sorted(d.glob("*.jsonl")):
            for line in open(f):
                o = json.loads(line)
                c = (o.get("output") or {}).get("eval_case")
                if not c or not (c.get("retrieved_observations") or c.get("retrieved_strategy_points")):
                    continue
                c["_arm_dir"] = d.name
                if c["action_phase"] == "day_vote" and len(votes) < n_vote:
                    votes.append(c)
                elif c["action_phase"] == "night_action" and c["player_role"] in NIGHT_TPL \
                        and len(nights) < n_night:
                    nights.append(c)
        if len(votes) >= n_vote and len(nights) >= n_night:
            break
    return votes + nights


def build_keys(case: dict, record: dict, *, with_board: bool) -> dict:
    day, speaker = case["day"], case["player_id"]
    pc = case.get("private_context") or {}
    roles = record["roles"]
    dead_from = death_timeline(record)
    alive = [p for p in roles if dead_from.get(p, 10**9) > day]
    roster = []
    if with_board:
        for nr in record.get("night_resolutions") or []:
            if int(nr["day"]) + 1 <= day:
                for p in nr.get("deaths") or []:
                    roster.append(DeathRecord(player=p, role=roles[p], day=int(nr["day"]), phase="night"))
        for dr in record.get("day_resolutions") or []:
            vp = dr.get("voted_player")
            if vp and int(dr["day"]) + 1 <= day:
                roster.append(DeathRecord(player=vp, role=roles[vp], day=int(dr["day"]), phase="day"))
        roster.sort(key=lambda e: (e.day, 0 if e.phase == "night" else 1))
    payload = {
        "player_id": speaker, "player_role": case["player_role"], "current_day": day,
        "surviving_players": alive,
        "surviving_wolves": [p for p in alive if roles[p] == "wolf"] if case["player_role"] == "wolf" else [],
        "surviving_villagers": [p for p in alive if roles[p] != "wolf"] if case["player_role"] == "wolf" else [],
        "day_channel": [DayChannel(**m) for m in record["day_channel"] if int(m["day"]) == day],
        "day_summaries": [DaySummary(day=int(s["day"]), summary=s["summary"], structured=s.get("structured") or {})
                          for s in record.get("day_summaries") or [] if int(s["day"]) < day],
        "dead_roster": roster,
        "previous_strategy": pc.get("previous_strategy") or "",
        "retrieved_observations": [RetrievedObservation(**o) for o in case.get("retrieved_observations") or []],
        "strategy_points": [RetrievedStrategyPoint(**s) for s in case.get("retrieved_strategy_points") or []],
        "investigator_results": [InvestigatorResult(**r) for r in
                                 (pc.get("investigator_results") or []) if int(r["day"]) <= day]
        if case["player_role"] == "investigator" else [],
        "vigilante_results": pc.get("vigilante_results") or [],
        "allow_abstain": True,
    }
    keys = build_agent_prompt_input(payload)
    keys["read_targets"] = ", ".join(p for p in alive if p != speaker)
    return keys


def one_call(llm_raw, tpl, schema, keys) -> dict:
    llm = llm_raw.with_structured_output(schema, include_raw=True)
    res = llm.invoke(tpl.invoke(keys))
    parsed, raw = res.get("parsed"), res.get("raw")
    usage = (getattr(raw, "usage_metadata", None) or {})
    return {"parsed": parsed, "out_tokens": usage.get("output_tokens"),
            "err": str(res.get("parsing_error") or "") or None}


def replay_case(llm_raw, case: dict, record: dict) -> list[dict]:
    rows = []
    phase, role = case["action_phase"], case["player_role"]
    n_obs, n_sp = len(case.get("retrieved_observations") or []), len(case.get("retrieved_strategy_points") or [])
    orig_action = ((case.get("agent_vote") or {}).get("votee") if phase == "day_vote"
                   else (case.get("agent_night_action") or {}).get("target")
                   or (case.get("agent_night_action") or {}))
    if phase == "day_vote":
        base = VOTE_TPL[role]
        if case.get("_enum_only"):
            arms = [("reads_enum", patch(base, add_reads_line=True, enum_reads_line=True),
                     VoteReadsFirst)]
        else:
            arms = [("old", patch(base, drop_board=True), DayVoteOutput),
                    ("board", base, DayVoteOutput),
                    ("reads_first", patch(base, add_reads_line=True), VoteReadsFirst),
                    ("reads_after", patch(base, add_reads_line=True), VoteReadsAfter)]
    elif case.get("_enum_only"):
        return []
    else:
        base, schema, tgt = NIGHT_TPL[role]
        arms = [("old", base, schema), ("board", patch(base, insert_board_night=True), schema)]
    for arm, tpl, schema in arms:
        keys = build_keys(case, record, with_board=(arm != "old"))
        try:
            r = one_call(llm_raw, tpl, schema, keys)
        except Exception as e:  # noqa: BLE001 — study script: record and continue
            rows.append(dict(case_id=case["observation_id"], phase=phase, role=role, arm=arm,
                             valid=False, err=str(e)[:200]))
            continue
        p = r["parsed"]
        if p is None:
            rows.append(dict(case_id=case["observation_id"], phase=phase, role=role, arm=arm,
                             valid=False, err=r["err"]))
            continue
        action = getattr(p, "vote_target", None) or next(
            (getattr(p, f) for f in ("healer_target", "investigator_target",
                                     "serial_killer_target", "vigilante_target") if hasattr(p, f)), None)
        row = dict(case_id=case["observation_id"], game_id=record["game_id"], phase=phase, role=role,
                   speaker=case["player_id"], day=case["day"], arm=arm, valid=True,
                   n_obs=n_obs, n_sp=n_sp,
                   n_mem_verdicts=len(p.memory_applicability), n_sp_verdicts=len(p.strategy_verdicts),
                   sp_verdicts=[v.verdict for v in p.strategy_verdicts],
                   mem_verdicts=[v.verdict for v in p.memory_applicability],
                   orig_mem_verdicts=[v.get("verdict") for v in case.get("memory_applicability") or []],
                   action=action, orig_action=orig_action, out_tokens=r["out_tokens"])
        if hasattr(p, "reads"):
            row["reads"] = [dict(player=x.player, why=x.why, suspected_role=x.suspected_role,
                                 confidence=x.confidence) for x in p.reads]
        rows.append(row)
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-vote", type=int, default=40)
    ap.add_argument("--n-night", type=int, default=20)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--enum-only", action="store_true",
                    help="run only the reads_enum arm (completeness fix probe) on vote cases")
    args = ap.parse_args()

    records = load_records()
    cases = sample_cases(2 if args.smoke else args.n_vote, 1 if args.smoke else args.n_night)
    print(f"sampled {len(cases)} decisions "
          f"({sum(1 for c in cases if c['action_phase']=='day_vote')} vote / "
          f"{sum(1 for c in cases if c['action_phase']!='day_vote')} night)")
    llm_raw = get_llm()

    # game lookup: sidecar dir name loop_v2_full_gen3_on_g0_all_enabled -> pair_v2_full_gen3_g0
    def record_for(c):
        d = c["_arm_dir"]  # loop_v2_full_gen{N}_{on|off}_g{K}_all_{...}
        m = re.match(r"loop_v2_full_(gen\d+)_(on|off)_g(\d+)_", d)
        gid = f"pair_v2_full_{m.group(1)}_g{m.group(3)}"
        cfg = "all_enabled" if m.group(2) == "on" else "all_disabled"
        return records[(gid, cfg)]

    if args.enum_only:
        for c in cases:
            c["_enum_only"] = True
    out_path = HERE / ("t2_enum_outputs.jsonl" if args.enum_only else "t2_outputs.jsonl")
    with out_path.open("w") as fh, ThreadPoolExecutor(max_workers=6) as ex:
        for rows in ex.map(lambda c: replay_case(llm_raw, c, record_for(c)), cases):
            for row in rows:
                fh.write(json.dumps(row) + "\n")
            fh.flush()
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
