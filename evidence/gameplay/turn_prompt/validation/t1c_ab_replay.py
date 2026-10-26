"""T1c — pre-ship A/B decision replay at census scale (dated study code).

Regenerates census-confirmed hallucination turns (plus anchored-but-consistent controls) from
their frozen inputs under two arms, and judges every output with the standing census reader:

  arm `old`         — generation-era prompt: dead-roster block removed, standard schemas.
  arm `new_bundle`  — dead roster + alive-roles line + reads_first schema (verdicts -> reads ->
                      strategy -> action) with enumerated read targets — the ship candidate.

Method notes (pre-registered in ../validation_plan.md T1c): inputs come from the eval-case
sidecars (original memories + previous_strategy, NOT cold; read feedback is still cold — biases
against the reads arm, so a reduction is conservative evidence). The metric is the arm-vs-arm
PAIRED hallucination rate over regenerated outputs — never flip-vs-original (T2: noise-dominated).
Judging: each output's message/updated_strategy is anchored deterministically; anchored units go
through the flash-lite recall read, its positives through the 3.5-flash precision read (the census
cascade). A case is "bad" in an arm if any of its regenerated units draws a final hallucination
verdict (deception excluded, as in the census).

Run:  poetry run python evidence/generation_prompt/validation/t1c_ab_replay.py --smoke
      poetry run python evidence/generation_prompt/validation/t1c_ab_replay.py --n-pos 60 --n-ctl 20
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Literal

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))  # repo root (dated study script)

from pydantic import BaseModel, Field, create_model

from Agents.llm_factory.accessors import get_llm
from Agents.prompts import day_discuss as dd
from Agents.prompts import day_vote as dv
from Agents.prompts import night as nt
from Agents.prompts.prompt_inputs import build_agent_prompt_input
from Agents.schemas import RetrievedObservation, RetrievedStrategyPoint
from Agents.schemas.game_events import DayChannel, DaySummary, DeathRecord, InvestigatorResult
from Agents.schemas.output import (
    AddressedTarget, DayDiscussOutput, DayVoteOutput, HealerOutput, InvestigatorOutput,
    MemoryVerdict, SerialKillerOutput, StrategyVerdict, VigilanteOutput,
)
from evaluation.src.audits.role_hallucination_screen import (
    anchors_for_text, claims_through, death_timeline,
)
from evaluation.src.judges.role_fact_read import read_candidates
from langchain_core.prompts import ChatPromptTemplate

HERE = Path(__file__).parent
RUNS = Path("evidence/v7_final/runs/v2_full")
SIDECARS = Path("batch_results/v2_full/eval_cases")
STAGE1 = HERE / "hallucination_verdicts.jsonl"
STAGE2 = HERE / "hallucination_verdicts_stage2.jsonl"

DISCUSS_TPL = {r: getattr(dd, f"{r.upper()}_DAY_DISCUSS")
               for r in ("villager", "healer", "investigator", "wolf", "serial_killer", "vigilante")}
VOTE_TPL = {r: getattr(dv, f"{r.upper()}_DAY_VOTE")
            for r in ("villager", "healer", "investigator", "wolf", "serial_killer", "vigilante")}
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


_READS_FIELDS = dict(
    strategy_verdicts=(list[StrategyVerdict], Field(default_factory=list, description="One verdict per numbered strategy point shown, in order; empty list if none shown.")),
    memory_applicability=(list[MemoryVerdict], Field(default_factory=list, description="One verdict per numbered observation shown, in order; empty list if none shown.")),
    reads=(list[PlayerRead], Field(description="One read per living player other than yourself.")),
    updated_strategy=(str, ...),
)
DiscussReadsFirst = create_model("DiscussReadsFirst", **_READS_FIELDS,
                                 pass_turn=(bool, ...), message=(str, ...),
                                 addressed_targets=(list[AddressedTarget], Field(default_factory=list)))
VoteReadsFirst = create_model("VoteReadsFirst", **_READS_FIELDS, vote_target=(str, ...))
NIGHT_READS = {role: create_model(f"NightReadsFirst_{role}", **_READS_FIELDS, **{tgt: (str, ...)})
               for role, (_, _, tgt) in NIGHT_TPL.items()}

READS_ENUM_INSTRUCTION = ("\nBefore your decision, record your current read — one entry each for: "
                          "{read_targets} (best-guess role, or 'unclear').\n")
ALIVE_BLOCK = ("== Dead so far (public) ==\n{dead_roster}\n\n"
               "== Roles still in play (fixed cast minus revealed deaths) ==\n{alive_roles}\n")
DEAD_BLOCK_RE = re.compile(r"[^\n]*Dead so far[^\n]*\n\{dead_roster\}\n?")


def patch(base: ChatPromptTemplate, arm: str, phase: str) -> ChatPromptTemplate:
    msgs = []
    for m in base.messages:
        text = m.prompt.template
        role = "system" if type(m).__name__.startswith("System") else "human"
        if arm == "old":
            text = DEAD_BLOCK_RE.sub("", text).replace("{dead_roster}", "")
        else:  # new_bundle: board + alive-roles + reads instruction
            if "{dead_roster}" in text:
                text = DEAD_BLOCK_RE.sub(ALIVE_BLOCK, text)
            elif phase == "night_action" and "{day_summaries}" in text:
                text = text.replace("{day_summaries}", ALIVE_BLOCK + "\n{day_summaries}", 1)
            if role == "human":
                text = READS_ENUM_INSTRUCTION + text
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


def sidecar_index(records: dict) -> dict[tuple, dict]:
    """(game_id, arm, phase, day, speaker, seq_or_None) -> eval_case, from every sidecar."""
    idx: dict[tuple, dict] = {}
    for d in sorted(SIDECARS.glob("*")):
        m = re.match(r"loop_v2_full_(gen\d+)_(on|off)_g(\d+)_", d.name)
        if not m:
            continue
        gid = f"pair_v2_full_{m.group(1)}_g{m.group(3)}"
        cfg = "all_enabled" if m.group(2) == "on" else "all_disabled"
        for f in sorted(d.glob("*.jsonl")):
            for line in open(f):
                o = json.loads(line)
                c = (o.get("output") or {}).get("eval_case")
                if not c or o.get("kind") != "agent_action_eval":
                    continue
                seq = (c.get("agent_message") or {}).get("seq") \
                    if c["action_phase"] == "day_discussion" else None
                idx[(gid, cfg, c["action_phase"], int(c["day"]), c["player_id"], seq)] = c
    return idx


def case_key(v: dict) -> tuple:
    phase = "day_discussion" if v["unit"] == "message" else v["phase"]
    seq = v.get("seq") if phase == "day_discussion" else None
    return (v["game_id"], v["arm"], phase, int(v["day"]), v["speaker"], seq)


def sample_cases(n_pos: int, n_ctl: int, sidecars: dict,
                 exclude_ids: set[str] | None = None) -> tuple[list[dict], list[dict]]:
    """Composition positives from stage 2 + anchored-but-consistent controls from stage 1,
    keeping only turns whose sidecar eval_case exists (needed to rebuild the frozen input).
    Wolf night turns are excluded (2-round channel, no single-decision template).
    ``exclude_ids`` (observation_ids from a prior run's outputs) enforces the escalation rule's
    fresh-cases-only requirement."""
    rng = random.Random(11)
    exclude_ids = exclude_ids or set()

    def usable(v):
        k = case_key(v)
        if k not in sidecars:
            return False
        if sidecars[k]["observation_id"] in exclude_ids:
            return False
        if k[2] == "night_action" and sidecars[k]["player_role"] not in NIGHT_TPL:
            return False
        return True

    pos_all = [json.loads(l) for l in STAGE2.read_text().splitlines() if l.strip()]
    pos = [v for v in pos_all if v["read"]["verdict"] == "hallucination"
           and v["read"]["error_class"] == "composition" and usable(v)]
    ctl_all = [json.loads(l) for l in STAGE1.read_text().splitlines() if l.strip()]
    ctl = [v for v in ctl_all if v["read"]["verdict"] == "consistent" and usable(v)
           and any(a["kind"] in ("count_mismatch", "dead_role_word") for a in v["anchors"])]

    def stratified(rows, n):
        rng.shuffle(rows)
        by_phase: dict[str, list] = {}
        for r in rows:
            by_phase.setdefault(case_key(r)[2], []).append(r)
        out, i = [], 0
        while len(out) < n and any(by_phase.values()):
            for ph in list(by_phase):
                if by_phase[ph] and len(out) < n:
                    out.append(by_phase[ph].pop())
            i += 1
        return out

    seen: set[tuple] = set()
    pos_u = [v for v in pos if not (case_key(v) in seen or seen.add(case_key(v)))]
    ctl_u = [v for v in ctl if case_key(v) not in seen
             and not (case_key(v) in seen or seen.add(case_key(v)))]
    return stratified(pos_u, n_pos), stratified(ctl_u, n_ctl)


def build_keys(v: dict, case: dict, record: dict, arm: str) -> dict:
    phase = case["action_phase"]
    day, speaker = int(case["day"]), case["player_id"]
    pc = case.get("private_context") or {}
    roles = record["roles"]
    dead_from = death_timeline(record)
    alive = [p for p in roles if dead_from.get(p, 10**9) > day]
    roster: list[DeathRecord] = []
    for nr in record.get("night_resolutions") or []:
        if int(nr["day"]) + 1 <= day:
            for p in nr.get("deaths") or []:
                roster.append(DeathRecord(player=p, role=roles[p], day=int(nr["day"]), phase="night"))
    for dr in record.get("day_resolutions") or []:
        vp = dr.get("voted_player")
        if vp and int(dr["day"]) + 1 <= day:
            roster.append(DeathRecord(player=vp, role=roles[vp], day=int(dr["day"]), phase="day"))
    roster.sort(key=lambda e: (e.day, 0 if e.phase == "night" else 1))
    counts: dict[str, int] = {}
    for p in alive:
        counts[roles[p]] = counts.get(roles[p], 0) + 1
    order = ["wolf", "serial_killer", "healer", "investigator", "vigilante", "villager"]
    alive_line = ", ".join(f"{counts[r]} {r.replace('_', ' ')}" for r in order if counts.get(r)) or "none"

    channel = [DayChannel(**m) for m in record["day_channel"] if int(m["day"]) == day]
    if phase == "day_discussion":  # the turn sees only what preceded it
        seq = (case.get("agent_message") or {}).get("seq") or 0
        channel = [m for m in channel if m.seq < seq]

    payload = {
        "player_id": speaker, "player_role": case["player_role"], "current_day": day,
        "surviving_players": alive,
        "surviving_wolves": [p for p in alive if roles[p] == "wolf"] if case["player_role"] == "wolf" else [],
        "surviving_villagers": [p for p in alive if roles[p] != "wolf"] if case["player_role"] == "wolf" else [],
        "day_channel": channel,
        "day_summaries": [DaySummary(day=int(s["day"]), summary=s["summary"], structured=s.get("structured") or {})
                          for s in record.get("day_summaries") or [] if int(s["day"]) < day],
        "dead_roster": roster if arm != "old" else [],
        "previous_strategy": pc.get("previous_strategy") or "",
        "retrieved_observations": [RetrievedObservation(**o) for o in case.get("retrieved_observations") or []],
        "strategy_points": [RetrievedStrategyPoint(**s) for s in case.get("retrieved_strategy_points") or []],
        "investigator_results": [InvestigatorResult(**r) for r in (pc.get("investigator_results") or [])
                                 if int(r["day"]) <= day] if case["player_role"] == "investigator" else [],
        "vigilante_results": pc.get("vigilante_results") or [],
        "allow_abstain": True,
    }
    if phase == "day_discussion":
        payload["firing_reason"] = (case.get("agent_message") or {}).get("firing_reason")
    keys = build_agent_prompt_input(payload)
    keys["alive_roles"] = alive_line
    keys["read_targets"] = ", ".join(p for p in alive if p != speaker)
    return keys


def arm_setup(case: dict, arm: str):
    phase, role = case["action_phase"], case["player_role"]
    if phase == "day_discussion":
        return patch(DISCUSS_TPL[role], arm, phase), (DayDiscussOutput if arm == "old" else DiscussReadsFirst)
    if phase == "day_vote":
        return patch(VOTE_TPL[role], arm, phase), (DayVoteOutput if arm == "old" else VoteReadsFirst)
    base, schema, _ = NIGHT_TPL[role]
    return patch(base, arm, phase), (schema if arm == "old" else NIGHT_READS[role])


def generate(llm_raw, v: dict, case: dict, record: dict) -> list[dict]:
    rows = []
    for arm in ("old", "new_bundle"):
        tpl, schema = arm_setup(case, arm)
        keys = build_keys(v, case, record, arm)
        try:
            out = llm_raw.with_structured_output(schema).invoke(tpl.invoke(keys))
            units = []
            if hasattr(out, "message") and (out.message or "").strip() and not getattr(out, "pass_turn", False):
                units.append(("message", out.message))
            if (getattr(out, "updated_strategy", "") or "").strip():
                units.append(("updated_strategy", out.updated_strategy))
            rows.append(dict(case_id=case["observation_id"], kind=v["_kind"], arm_generated=arm,
                             game_id=record["game_id"], game_arm=record.get("config_name", ""),
                             phase=case["action_phase"], day=int(case["day"]),
                             speaker=case["player_id"], speaker_role=case["player_role"],
                             valid=True, units=[{"unit": u, "text": t} for u, t in units]))
        except Exception as e:  # noqa: BLE001 — study script: record and continue
            rows.append(dict(case_id=case["observation_id"], kind=v["_kind"], arm_generated=arm,
                             game_id=record["game_id"], game_arm=record.get("config_name", ""),
                             phase=case["action_phase"], day=int(case["day"]),
                             speaker=case["player_id"], speaker_role=case["player_role"],
                             valid=False, err=str(e)[:200], units=[]))
    return rows


def judge(gen_rows: list[dict], records: dict) -> None:
    """Anchor every generated unit; cascade-read the anchored ones; mark each row bad/clean."""
    cands = []
    for i, row in enumerate(gen_rows):
        rec = records[(row["game_id"], row["game_arm"])]
        roles, dead_from = rec["roles"], death_timeline(rec)
        for j, u in enumerate(row["units"]):
            anchors = anchors_for_text(u["text"], roles=roles, dead_from=dead_from,
                                       day=row["day"], speaker=row["speaker"],
                                       claims=claims_through(rec, row["day"]))
            if anchors:
                cands.append({"game_id": row["game_id"], "arm": row["game_arm"],
                              "day": row["day"], "seq": None, "phase": row["phase"],
                              "speaker": row["speaker"], "speaker_role": row["speaker_role"],
                              "unit": u["unit"], "text": u["text"], "anchors": anchors,
                              "_row": i, "_unit": j})
    print(f"judging {len(cands)} anchored units of {sum(len(r['units']) for r in gen_rows)} generated")
    lite = read_candidates(cands, records, "gemini-3.1-flash-lite")
    pos = [c for c in lite if (c.get("read") or {}).get("verdict") in ("hallucination", "deliberate_deception")]
    flash = read_candidates(pos, records, "gemini-3.5-flash") if pos else []
    verdicts: dict[tuple, str] = {}
    for c in lite:
        verdicts[(c["_row"], c["_unit"])] = (c.get("read") or {}).get("verdict", "read_error")
    for c in flash:  # precision pass overrides
        verdicts[(c["_row"], c["_unit"])] = (c.get("read") or {}).get("verdict", "read_error")
    for i, row in enumerate(gen_rows):
        vs = [verdicts.get((i, j), "no_anchor") for j in range(len(row["units"]))]
        row["unit_verdicts"] = vs
        row["bad"] = any(v == "hallucination" for v in vs)  # deception excluded, as in the census


def summarize(gen_rows: list[dict]) -> None:
    from collections import Counter
    from math import comb
    for kind in ("positive", "control", "POOLED"):
        kinds = ("positive", "control") if kind == "POOLED" else (kind,)
        pairs: dict[str, dict[str, bool]] = {}
        for r in gen_rows:
            if r["kind"] in kinds and r["valid"]:
                pairs.setdefault(r["case_id"], {})[r["arm_generated"]] = r["bad"]
        both = {k: v for k, v in pairs.items() if len(v) == 2}
        old_bad = sum(v["old"] for v in both.values())
        new_bad = sum(v["new_bundle"] for v in both.values())
        b = sum(1 for v in both.values() if v["old"] and not v["new_bundle"])
        c = sum(1 for v in both.values() if v["new_bundle"] and not v["old"])
        n = len(both)
        pval = (sum(comb(b + c, k) for k in range(b, b + c + 1)) / 2 ** (b + c)) if (b + c) else 1.0
        print(f"\n[{kind}] n={n} paired cases: old bad {old_bad}/{n} ({old_bad/max(n,1):.0%})  "
              f"new_bundle bad {new_bad}/{n} ({new_bad/max(n,1):.0%})")
        print(f"  discordant pairs: old-only-bad={b}  new-only-bad={c}  "
              f"one-sided sign p={pval:.4f}")
    invalid = Counter((r["kind"], r["arm_generated"]) for r in gen_rows if not r["valid"])
    if invalid:
        print("invalid generations:", dict(invalid))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n-pos", type=int, default=60)
    ap.add_argument("--n-ctl", type=int, default=20)
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--exclude", default="", help="prior run's outputs jsonl — its case_ids are "
                                                  "excluded (escalation: fresh cases only)")
    ap.add_argument("--out", default="t1c_outputs.jsonl", help="output filename (in validation/)")
    args = ap.parse_args()

    records = load_records()
    sidecars = sidecar_index(records)
    exclude_ids: set[str] = set()
    if args.exclude:
        exclude_ids = {json.loads(l)["case_id"] for l in (HERE / args.exclude).read_text().splitlines()
                       if l.strip()}
        print(f"excluding {len(exclude_ids)} case_ids from {args.exclude}")
    n_pos, n_ctl = (2, 1) if args.smoke else (args.n_pos, args.n_ctl)
    pos, ctl = sample_cases(n_pos, n_ctl, sidecars, exclude_ids)
    for v in pos:
        v["_kind"] = "positive"
    for v in ctl:
        v["_kind"] = "control"
    cases = pos + ctl
    print(f"sampled {len(pos)} positives + {len(ctl)} controls "
          f"(phases: {sorted({case_key(v)[2] for v in cases})})")

    llm_raw = get_llm()
    gen_rows: list[dict] = []
    with ThreadPoolExecutor(max_workers=6) as ex:
        for rows in ex.map(lambda v: generate(llm_raw, v, sidecars[case_key(v)],
                                              records[(v["game_id"], v["arm"])]), cases):
            gen_rows.extend(rows)
    judge(gen_rows, records)
    out_path = HERE / args.out
    with out_path.open("w") as fh:
        for r in gen_rows:
            fh.write(json.dumps(r) + "\n")
    print(f"wrote {out_path}")
    summarize(gen_rows)


if __name__ == "__main__":
    main()
