"""Why did the investigator invent a result? Resample its exact turn under prompt variants.

Record: evidence/game_play_enhancement/discussion_evidence.md §6.2. In live game 832404e9 (day 4,
channel entry 8) the investigator said "I investigated player_9 last night, and they are the
remaining wolf" — it never checked player_9 (its checks: player_1 wolf, player_4 villager, player_5
healer). This rebuilds that turn's payload from the game's LangGraph checkpoint (read-only), with the
engine's own payload builder, and samples the same template and model many times per variant:

  A  as played
  B  results reworded: "Night 3 (last night): you investigated player_5 — healer"
  C  the previous strategy note removed
  D  B and C together

Each sampled message is screened for a claimed investigation of someone the investigator never
checked; the screen flags candidates and every flagged line is written out to be read by hand.

  WW_DISCUSSION_PROMPT=v2 poetry run python evaluation/experiments/investigator_claim_replay.py --n 20
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

GAME = "832404e9-a5f2-434e-8484-5bb953718a8f"
DAY, SPEAKER, CHANNEL_SEQ = 4, "player_7", 8
MODEL = "gemini-3.5-flash-lite"  # the live game's seat model; temperature/thinking stay at defaults
OUT = Path("evidence/game_play_enhancement/data/investigator_replay")


def load_state() -> dict:
    """The day-4 discussion state just before the investigator's turn: today's channel ends at
    entry CHANNEL_SEQ - 1."""
    import psycopg
    from dotenv import dotenv_values
    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg.rows import dict_row

    from Agents.memory.checkpointer import durable_serde

    dsn = dotenv_values(".env")["WW_POSTGRES_DSN"]
    with psycopg.connect(dsn, autocommit=True, row_factory=dict_row,
                         options="-c default_transaction_read_only=on") as conn:
        saver = PostgresSaver(conn, serde=durable_serde())
        namespaces = [r["checkpoint_ns"] for r in conn.execute(
            "select distinct checkpoint_ns from checkpoints where thread_id=%s "
            "and checkpoint_ns like 'DAY_PHASE:%%'", (GAME,)).fetchall()]
        for ns in namespaces:
            for t in saver.list({"configurable": {"thread_id": GAME, "checkpoint_ns": ns}}):
                v = t.checkpoint["channel_values"]
                today = [m.seq for m in v.get("day_channel", []) if m.day == DAY]
                if v.get("current_day") == DAY and today and max(today) == CHANNEL_SEQ - 1:
                    return v
    sys.exit("no checkpoint found just before the turn")


def as_played_results(results, current_day=None) -> str:
    """The wording the live game used (the engine's formatter before the fix it led to)."""
    if not results:
        return "No investigations yet."
    return "\n".join(f"Day {r.day}: {r.player_investigated} was revealed as {r.role_revealed}"
                     for r in results)


def build(state: dict, variant: str):
    from Agents.nodes.day.actors import DISCUSS_PROMPTS
    from Agents.nodes.day.flow import build_speaker_send
    from Agents.prompts import prompt_inputs
    from Agents.prompts.prompt_formatters import format_investigator_results
    from Agents.schemas.game_events import FiringReason

    payload = dict(build_speaker_send(state, SPEAKER, "investigator",
                                      FiringReason(tier="proactive", owes=[])).arg)
    if variant in ("C", "D"):
        payload["previous_strategy"] = ""
    # B/D: the engine's current formatter (the reworded lines, adopted after this replay)
    prompt_inputs.format_investigator_results = (
        format_investigator_results if variant in ("B", "D") else as_played_results)
    prompt_input = prompt_inputs.build_agent_prompt_input(payload)
    prompt_inputs.format_investigator_results = format_investigator_results
    return payload, prompt_input, DISCUSS_PROMPTS["investigator"]


def sample(payload: dict, prompt_input: dict, template) -> dict:
    from Agents.llm_factory import get_llm
    from Agents.schemas import DayDiscussOutput
    from Agents.turn.action_space import output_schema_with_legal_targets, valid_targets_for_action

    schema = output_schema_with_legal_targets(
        DayDiscussOutput, "day_channel", valid_targets_for_action(payload, "day_channel"))
    out = (template | get_llm().with_structured_output(schema)).invoke(prompt_input)
    p9 = next((r for r in out.reads if r.player == "player_9"), None)
    return {"message": out.message, "pass_turn": out.pass_turn, "note": out.updated_strategy,
            "read_p9": f"{p9.suspected_role}/{p9.confidence}" if p9 else ""}


def invented(message: str, checked: set[str]) -> list[str]:
    """Candidate screen: players the message says were investigated/checked but never were."""
    hits = re.findall(r"(?:investigat\w*|check\w*)\s+(?:on\s+)?(player_\d)", message, re.I)
    return sorted({p for p in hits if p not in checked})


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=20, help="samples per variant")
    ap.add_argument("--variants", default="ABCD")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()
    if os.environ.get("WW_DISCUSSION_PROMPT") != "v2":
        sys.exit("the live game ran WW_DISCUSSION_PROMPT=v2; set it to replay faithfully")
    os.environ["GOOGLE_GENAI_MODEL"] = MODEL

    state = load_state()
    checked = {r.player_investigated for r in state["investigator_results"]}
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {"game": GAME, "day": DAY, "speaker": SPEAKER, "channel_seq": CHANNEL_SEQ,
               "model": MODEL, "checked": sorted(checked), "n": args.n, "variants": {}}
    for variant in args.variants:
        payload, prompt_input, template = build(state, variant)
        (OUT / f"prompt_{variant}.txt").write_text(
            "\n\n".join(m.content for m in template.format_messages(**prompt_input)))
        with ThreadPoolExecutor(max_workers=args.workers) as ex:
            rows = list(ex.map(lambda _: sample(payload, prompt_input, template), range(args.n)))
        for r in rows:
            r["invented"] = invented(r["message"], checked)
        with open(OUT / f"samples_{variant}.jsonl", "w") as f:
            f.writelines(json.dumps(r) + "\n" for r in rows)
        spoke = [r for r in rows if not r["pass_turn"]]
        summary["variants"][variant] = {
            "spoke": len(spoke), "passed": len(rows) - len(spoke),
            "flagged_invented_claim": sum(bool(r["invented"]) for r in rows),
            "mentions_player_9": sum("player_9" in r["message"] for r in spoke),
        }
        print(variant, summary["variants"][variant])
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
