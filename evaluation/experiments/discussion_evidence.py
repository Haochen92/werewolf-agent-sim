"""What does the day discussion rest on? Two reads of finished games, for the discussion-evidence work.

Record: evidence/game_play_enhancement/discussion_evidence.md (§2 = the census, §4 = the judge).

  census — free. Counts the evidence label the in-game day summary already attaches to every
           accusation (voting record / behaviour / communication style / concrete claim), plus the
           structural counts no model is needed for: who passed by choice vs was skipped by the
           novelty gate, and how long messages run.
  judge  — an independent model reads every day-discussion message and records what it rests on,
           whom it accuses, and any role the speaker claims for themselves. The judge never sees true
           roles (knowing who is evil would colour the labels); code joins them in afterwards to score
           accusation accuracy by evidence type and to spot fake claims. Writes a review sheet so a
           human can check the judge's labels message by message.

  poetry run python evaluation/experiments/discussion_evidence.py census \\
      --records 'batch_results/wolf_sk_mining_p*/games/*.jsonl'
  poetry run python evaluation/experiments/discussion_evidence.py judge \\
      --records 'batch_results/<batch>/games/*.jsonl' --label v2 --games 3

Website games are read from the public replay endpoint instead (`--replays <game_id> ...`, or
`--latest N`); human seats stay in the transcript the judge reads but are not themselves judged.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
import urllib.request
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluation.src.core.settings import REPO_ROOT  # noqa: E402
from evaluation.src.data.sources.batch_records import load_batch_records  # noqa: E402
from evaluation.src.judges.config import DEFAULT_JUDGE_MODEL, get_judge_llm  # noqa: E402
from evaluation.src.judges.role_fact_read import build_fact_sheet  # noqa: E402

EVIL = {"wolf", "serial_killer"}
DEFAULT_OUT = "evidence/game_play_enhancement/data"

Basis = Literal[
    "own_night_result", "role_claim", "night_events", "voting_record",
    "speech_content", "manner", "turn_taking", "reveal_timing", "none",
]
ClaimedRole = Literal[
    "none", "villager", "healer", "investigator", "vigilante", "wolf", "serial_killer",
]


class EvidenceRead(BaseModel):
    quote: str = Field(description="the phrase that carries the message's main point, copied verbatim; empty string if none")
    reason: str = Field(description="one sentence: what the message rests on and why the labels below fit")
    bases: list[Basis] = Field(description="every kind of evidence the message relies on, per the definitions; ['none'] if it relies on nothing")
    accuses: list[str] = Field(description="player ids the message accuses or casts suspicion on; empty list if none")
    self_claim: ClaimedRole = Field(description="the role the speaker claims for themselves in this message, or 'none'")


SYSTEM = """You read one message from the day discussion of a Werewolf (social-deduction) game and record what it rests on. You are not judging whether the message is true or good play, only what kind of evidence it uses.

The game: nine players. Town side: villagers, a healer, an investigator (learns one player's exact role each night), a vigilante (may shoot at night). Evil: two wolves, and a serial killer who plays alone. Each day players talk one at a time, then vote someone out. A moderator decides who speaks next. Deaths and the dead player's role are announced publicly; votes are public.

Evidence kinds (a message may use several):
- own_night_result — the speaker shares or relies on something they learned at night themselves ("I investigated player_4: wolf", "I protected player_2 last night").
- role_claim — reasoning about a role claim or a claimed result made by someone (supporting it, doubting it, pointing out a contradiction between claims).
- night_events — public night outcomes: who died and to which attacker, a healer save, who survived an attack, the revealed role of a dead player.
- voting_record — how players voted or abstained on earlier days, or who pushed which lynch through their votes.
- speech_content — something specific a player SAID in discussion: a contradiction, a changed story, pushing hard for a lynch, defending someone, dodging a direct question.
- manner — tone or attitude without pointing at anything specific said or done ("seems nervous", "too eager", "overly defensive", "acting suspicious").
- turn_taking — how often or in what order someone has spoken: being quiet or silent, passing, not having spoken yet, speaking first, early or late, talking a lot or very little. (The moderator decides who speaks when, so this is about the turn order itself, not about anything the player chose to say.)
- reveal_timing — WHEN a player chose to share something: claiming a role or a result "suddenly", "right away", "only now", "too late", or holding information back.
- none — no evidence at all: procedure, general advice ("we should be careful"), agreement without a new reason, greetings.

Rules:
- Label only what THIS message relies on. Mentioning a vote in passing to propose a plan is not voting_record evidence unless the message reasons from it.
- "accuses" lists only players this message casts suspicion on (including "I suspect" or "I'm voting X because..."). Defending someone is not an accusation.
- "self_claim" is a role the speaker states as their OWN ("I'm the healer"). Hinting is not claiming. Claiming to be "just a villager" counts as villager.

Copy the main phrase, give one sentence of reasoning, then the labels."""

USER_TEMPLATE = """== Public facts at the start of day {day} ==
Deaths so far (role revealed publicly at death; "died night N" = killed the night after day N):
{deaths}
Alive players: {alive}
Votes on earlier days:
{votes}

== Today's discussion so far ==
{transcript}

== The message to read ==
{speaker}: {message}"""


# --- loading -----------------------------------------------------------------

def _load(records_glob: str, games: int | None) -> list[dict]:
    records = load_batch_records(records_glob)
    if not records:
        sys.exit(f"no successful game records match {records_glob!r} (relative to {REPO_ROOT})")
    return records[:games] if games else records


def _get_json(url: str):
    # Cloudflare in front of the site refuses urllib's default user agent.
    req = urllib.request.Request(url, headers={"User-Agent": "werewolf-eval/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.load(resp)


_ATTACKER_FIELDS = {"wolves": ("wolves_target", "kill_successful"),
                    "serial_killer": ("serial_killer_target", "serial_killer_kill_landed"),
                    "vigilante": ("vigilante_target", "vigilante_kill_landed")}


def record_from_replay(replay: dict) -> dict:
    """A finished website game, rebuilt from its replay events into the run_batch record shape the
    readers above take. Human seats (any seat the game asked for input) are listed in `humans`."""
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


def load_replays(server: str, game_ids: list[str], latest: int | None) -> list[dict]:
    if latest:
        game_ids = [g["game_id"] for g in _get_json(f"{server}/replays?limit={latest}")] + game_ids
    if not game_ids:
        sys.exit("name games with --replays, or take the newest with --latest N")
    return [record_from_replay(_get_json(f"{server}/replays/{g}")) for g in game_ids]


def _real_messages(record: dict) -> list[dict]:
    return [e for e in record["day_channel"]
            if e["player"] != "game_master" and not e.get("passed") and e.get("message", "").strip()]


def _agent_messages(record: dict) -> list[dict]:
    """What the judge scores: the agents' messages. A human seat's lines stay in the transcript
    the judge reads, but they are the player under test, not the agents."""
    humans = set(record.get("humans") or [])
    return [e for e in _real_messages(record) if e["player"] not in humans]


def _words(text: str) -> int:
    return len(text.split())


def structural(records: list[dict]) -> dict:
    """Counts that need no model: passes by kind, messages per day, message length."""
    passes: Counter = Counter()
    lengths: list[int] = []
    days = 0
    for r in records:
        for e in r["day_channel"]:
            if e["player"] == "game_master" or e["player"] in (r.get("humans") or []):
                continue
            if e.get("passed"):
                passes[e.get("pass_reason") or "unlabelled"] += 1
        msgs = _agent_messages(r)
        lengths += [_words(e["message"]) for e in msgs]
        days += len({e["day"] for e in _real_messages(r)})
    lengths.sort()
    return {
        "games": len(records),
        "human_seats": sum(len(r.get("humans") or []) for r in records),
        "agent_messages": len(lengths),
        "messages_per_day": round(len(lengths) / days, 1) if days else 0,
        "passes": dict(passes),
        "words_mean": round(statistics.mean(lengths), 1) if lengths else 0,
        "words_median": statistics.median(lengths) if lengths else 0,
        "words_p90": lengths[int(0.9 * (len(lengths) - 1))] if lengths else 0,
        "town_wins": sum(r.get("winner") == "villagers" for r in records),
    }


# --- census: the in-game summary's own labels --------------------------------

def census(records: list[dict]) -> dict:
    labels: Counter = Counter()
    town_hits: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    evil_claims = summaries = quiet_named = 0
    for r in records:
        roles = r["roles"]
        for s in r["day_summaries"]:
            st = s.get("structured") or {}
            if "accusations" not in st:
                continue
            summaries += 1
            for a in st["accusations"]:
                label = re.sub(r"[^a-z_]", "", a.get("evidence_type", "").lower()) or "blank"
                labels[label] += 1
                accusers = {roles.get(p) for p in a.get("accusers", [])}
                if accusers and not accusers & EVIL:
                    town_hits[label][1] += 1
                    town_hits[label][0] += roles.get(a.get("target")) in EVIL
            evil_claims += sum(roles.get(c.get("player")) in EVIL for c in st.get("role_claims", []))
            drivers = st.get("village_dynamics", {}).get("drivers", "")
            # day-1 summaries say "no players are staying quiet yet": a keyword hit, not a name
            quiet_named += bool(re.search(r"quiet|silent", drivers, re.I)
                                and not re.match(r"\s*no (specific )?players", drivers, re.I))
    return {
        "accusation_labels": dict(labels.most_common()),
        "town_accusations_on_evil": {k: f"{h}/{n}" for k, (h, n) in town_hits.items()},
        "evil_role_claims": evil_claims,
        "summaries_naming_quiet_players": f"{quiet_named}/{summaries}",
    }


# --- judge: an independent read of every message -----------------------------

def _units(records: list[dict]) -> list[dict]:
    units = []
    for r in records:
        by_day: dict[int, list[dict]] = defaultdict(list)
        for e in _real_messages(r):
            by_day[e["day"]].append(e)
        for day, msgs in by_day.items():
            humans = set(r.get("humans") or [])
            for i, e in enumerate(msgs):
                if e["player"] in humans:
                    continue
                units.append({"game_id": r["game_id"], "day": day, "seq": e["seq"],
                              "speaker": e["player"], "message": e["message"],
                              "earlier": [f"{m['player']}: {m['message']}" for m in msgs[:i]]})
    return units


def _prompt(record: dict, unit: dict) -> str:
    facts = build_fact_sheet(record, {"day": unit["day"], "speaker": unit["speaker"],
                                      "unit": "message", "text": unit["message"], "anchors": []})
    return USER_TEMPLATE.format(
        day=unit["day"], deaths=facts["deaths"], alive=facts["alive"], votes=facts["votes"],
        transcript="\n".join(unit["earlier"]) or "(nobody has spoken yet)",
        speaker=unit["speaker"], message=unit["message"])


def read_messages(records: list[dict], model: str, workers: int) -> list[dict]:
    by_game = {r["game_id"]: r for r in records}
    units = _units(records)
    llm = get_judge_llm(model, temperature=0.0).with_structured_output(EvidenceRead)

    def one(i: int) -> tuple[int, dict]:
        unit = units[i]
        prompt = _prompt(by_game[unit["game_id"]], unit)
        last_err = None
        for attempt in range(4):
            try:
                read = llm.invoke([("system", SYSTEM), ("human", prompt)])
                return i, {**unit, "read": read.model_dump()}
            except Exception as e:  # transport/429/parse — the standard retry layer
                last_err = e
                time.sleep(2 ** attempt)
        return i, {**unit, "read": None, "read_error": str(last_err)}

    out: list[dict | None] = [None] * len(units)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        for done, f in enumerate(as_completed([ex.submit(one, i) for i in range(len(units))]), 1):
            i, row = f.result()
            out[i] = row
            if done % 50 == 0:
                print(f"  {done}/{len(units)} read")
    for row in out:
        row.pop("earlier", None)
        row["speaker_role"] = by_game[row["game_id"]]["roles"].get(row["speaker"])
    return out  # type: ignore[return-value]


def score(rows: list[dict], records: list[dict]) -> dict:
    roles_by_game = {r["game_id"]: r["roles"] for r in records}
    read = [r for r in rows if r.get("read")]
    basis_share: Counter = Counter()
    accusing_basis: Counter = Counter()
    town_hits: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    claims: list[dict] = []
    for r in read:
        roles = roles_by_game[r["game_id"]]
        bases = set(r["read"]["bases"]) or {"none"}
        basis_share.update(bases)
        accused = [p for p in r["read"]["accuses"] if p in roles]
        if accused:
            accusing_basis.update(bases)
            if r["speaker_role"] not in EVIL:
                for b in bases:
                    town_hits[b][1] += len(accused)
                    town_hits[b][0] += sum(roles[p] in EVIL for p in accused)
        claim = r["read"]["self_claim"]
        if claim != "none":
            claims.append({"game_id": r["game_id"], "day": r["day"], "speaker": r["speaker"],
                           "claimed": claim, "actual": r["speaker_role"]})
    n = len(read)
    n_acc = sum(1 for r in read if any(p in roles_by_game[r["game_id"]] for p in r["read"]["accuses"]))
    first_claims = {}
    for c in claims:  # one claim per speaker per game: the first
        first_claims.setdefault((c["game_id"], c["speaker"]), c)
    return {
        "messages_read": n, "read_errors": len(rows) - n,
        "share_of_messages_using": {b: f"{k}/{n} ({k / n:.0%})" for b, k in basis_share.most_common()},
        "accusing_messages": n_acc,
        "share_of_accusing_messages_using": {b: f"{k}/{n_acc} ({k / n_acc:.0%})"
                                             for b, k in accusing_basis.most_common()} if n_acc else {},
        "town_accusations_on_evil_by_basis": {b: f"{h}/{t}" for b, (h, t) in town_hits.items()},
        "self_claims": list(first_claims.values()),
        "fake_claims_by_evil": sum(c["actual"] in EVIL and c["claimed"] != c["actual"]
                                   for c in first_claims.values()),
    }


def review_sheet(rows: list[dict]) -> str:
    """One line per message for a human to check the judge against: agree, or write the fix."""
    out = ["# Judge review sheet", "",
           "Mark each row: ✓ if the labels are right, or write what they should be.", ""]
    game = day = None
    for r in sorted(rows, key=lambda r: (r["game_id"], r["day"], r["seq"])):
        if r["game_id"] != game:
            game, day = r["game_id"], None
            out += [f"## {game}", ""]
        if r["day"] != day:
            day = r["day"]
            out += [f"### Day {day}", ""]
        read = r.get("read") or {}
        out += [f"- **{r['speaker']}** ({r['speaker_role']}): {r['message']}",
                f"  - bases: `{', '.join(read.get('bases', ['ERROR']))}` · accuses: "
                f"`{', '.join(read.get('accuses', [])) or '—'}` · claims: `{read.get('self_claim', '—')}`",
                f"  - judge: {read.get('reason', r.get('read_error', ''))}",
                "  - check: ", ""]
    return "\n".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("mode", choices=["census", "judge"])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--records", help="repo-relative glob of run_batch game-record .jsonl files")
    src.add_argument("--replays", nargs="+", help="finished website games, by game id")
    src.add_argument("--latest", type=int, help="the N most recently finished website games")
    ap.add_argument("--server", default="https://wolf.liuhaochen.com/api", help="where --replays/--latest read from")
    ap.add_argument("--games", type=int, default=None, help="read only the first N games")
    ap.add_argument("--label", default="run", help="output folder name under --out")
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--model", default=DEFAULT_JUDGE_MODEL)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    if args.records:
        records, source = _load(args.records, args.games), args.records
    else:
        records = load_replays(args.server, args.replays or [], args.latest)
        source = {"server": args.server, "game_ids": [r["game_id"] for r in records]}
    result = {"source": source, "structural": structural(records)}
    if args.mode == "census":
        result["census"] = census(records)
        print(json.dumps(result, indent=2))
        return

    out_dir = REPO_ROOT / args.out / args.label
    out_dir.mkdir(parents=True, exist_ok=True)
    print(f"reading {sum(len(_agent_messages(r)) for r in records)} messages from {len(records)} games with {args.model}")
    rows = read_messages(records, args.model, args.workers)
    result |= {"model": args.model, "judge": score(rows, records)}
    with open(out_dir / "reads.jsonl", "w") as f:
        f.writelines(json.dumps(r) + "\n" for r in rows)
    (out_dir / "summary.json").write_text(json.dumps(result, indent=2))
    (out_dir / "review.md").write_text(review_sheet(rows))
    print(json.dumps(result, indent=2))
    print(f"wrote {out_dir}/{{reads.jsonl,summary.json,review.md}}")


if __name__ == "__main__":
    main()
