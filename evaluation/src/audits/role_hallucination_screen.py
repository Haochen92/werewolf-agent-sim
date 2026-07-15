"""Deterministic candidate screen for role-fact hallucinations — stages 1+2 of the detection
pipeline (ZERO LLM).

The pipeline splits the work by what each layer can do *reliably*:

1. **Anchor (this module).** Flag every agent text unit that touches an entity or count the
   structured game record can contradict: a dead ``player_N``, a role word whose holders are all
   dead, a numeric/grammatical count claim about a role, or a role-claim attribution. Anchoring on
   entities (a closed, exhaustively-matchable set) instead of error phrasings makes recall provable
   by construction for anything that NAMES a dead entity or states a count — the screen never has
   to anticipate how an error might be worded.
2. **Safe filters (this module).** Drop only what is provably legitimate: game_master messages
   (rendered from state, cannot hallucinate) and count claims that match the true alive count.
   Nothing position- or phrasing-based is trusted (an "early turns just recap the GM" filter would
   drop wrong recaps — the attacker-misattribution class is exactly a wrong early recap).
3. **Read (``evaluation.src.judges.role_fact_read``).** An LLM judges each surviving candidate
   against a deterministic fact sheet (deaths, revealed roles, alive counts, the speaker's own
   knowledge). Whether a mention *treats a dead entity as alive* is a semantic question; it is
   never decided here.

Scanned units: public ``day_channel`` messages AND each turn's private ``updated_strategy`` (from
the eval-case sidecar at ``record["eval_cases_path"]`` — a hallucinated private belief drives votes
and night targets directly). Two structural checks are deterministic *verdicts*, not candidates:
a vote for a dead player, and a question/response addressed to one.

Known out-of-scope (stated, not hidden): anchor-less fabrications — pronoun/description references
("the guy we lynched"), misquotes, invented vote history — carry no id or role word to anchor on.

Console: ``eval-role-hallucination``. Record home: ``evidence/generation_prompt/validation/``.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from evaluation.src.core.settings import REPO_ROOT
from evaluation.src.data.sources.batch_records import load_batch_records

DEFAULT_RECORDS_GLOB = "evidence/v7_final/runs/v2_full/gen*_o*.jsonl"
DEFAULT_OUT = "evidence/generation_prompt/validation/hallucination_candidates.jsonl"

# alias regex -> canonical role
ROLE_ALIASES: list[tuple[re.Pattern, str]] = [
    (re.compile(r"\bwere?wol(?:f|ves)\b|\bwol(?:f|ves)\b", re.I), "wolf"),
    (re.compile(r"\bserial[ _-]?killers?\b", re.I), "serial_killer"),
    (re.compile(r"\bvillagers?\b", re.I), "villager"),
    (re.compile(r"\bhealers?\b", re.I), "healer"),
    (re.compile(r"\binvestigators?\b", re.I), "investigator"),
    (re.compile(r"\bvigilantes?\b", re.I), "vigilante"),
]
_ROLE_FRAG = (r"(?:were?wol(?:f|ves)|wol(?:f|ves)|serial[ _-]?killers?|villagers?|healers?"
              r"|investigators?|vigilantes?)")

PLAYER_ID = re.compile(r"\bplayer_\d+\b")
CLAIM_WORD = re.compile(r"\bclaim(?:ed|s|ing)?\b", re.I)

# Count claims. Three grammatical forms assert a count; spelled and digit numerals share one
# dictionary. "no more wolves" rides the optional middle word; the definite-singular form
# ("the remaining wolf") asserts exactly one — grammar is a quantifier too.
_NUM = {"one": 1, "two": 2, "three": 3, "four": 4, "both": 2, "no": 0, "zero": 0,
        "1": 1, "2": 2, "3": 3, "4": 4}
NUM_ROLE = re.compile(
    rf"\b(one|two|three|four|both|no|zero|1|2|3|4)\s+(?:\w+[- ])?({_ROLE_FRAG})\b", re.I)
DEF_SINGULAR = re.compile(
    rf"\b(?:the|that|this)\s+(?:remaining|last|final|other|hidden)\s+({_ROLE_FRAG})\b", re.I)
VAGUE_PLURAL = re.compile(
    rf"\b(?:several|many|a few|a couple(?: of)?)\s+(?:\w+[- ])?({_ROLE_FRAG})\b", re.I)

# Legacy export — the frozen T1b study script grades with this wolf-only pattern; the live screen
# uses the generalized NUM_ROLE above.
COUNT_CLAIM = re.compile(
    r"\b(both|one|two|three|no|zero|1|2|3)\s+(?:remaining\s+)?(were?wol(?:f|ves)|wol(?:f|ves))\b",
    re.I,
)

WINDOW = 70  # chars of context kept around a match in the anchor detail


def death_timeline(record: dict) -> dict[str, int]:
    """player -> first day the table KNOWS them dead (reveal day). Night/lynch of day d -> d+1."""
    dead_from: dict[str, int] = {}
    for nr in record.get("night_resolutions") or []:
        for p in nr.get("deaths") or []:
            dead_from.setdefault(p, int(nr["day"]) + 1)
    for dr in record.get("day_resolutions") or []:
        vp = dr.get("voted_player")
        if vp:
            dead_from.setdefault(vp, int(dr["day"]) + 1)
    return dead_from


def claims_through(record: dict, day: int) -> set[tuple[str, str]]:
    """(player, claimed_role) pairs persisted for any day <= day (same-day inclusive: a summary is
    written post-day, but the claim it records was made in that day's channel, possibly before the
    message under test — same-day exclusion would over-flag; the read resolves residue)."""
    pairs: set[tuple[str, str]] = set()
    for ds in record.get("day_summaries") or []:
        if int(ds.get("day", 0)) > day:
            continue
        for rc in (ds.get("structured") or {}).get("role_claims") or []:
            if rc.get("player") and rc.get("claimed_role"):
                pairs.add((rc["player"], str(rc["claimed_role"]).strip().lower()))
    return pairs


def _canon_role(fragment: str) -> str | None:
    for pat, canon in ROLE_ALIASES:
        if pat.search(fragment):
            return canon
    return None


def _alive_counts(roles: dict[str, str], dead_from: dict[str, int], day: int) -> dict[str, int]:
    counts: dict[str, int] = {}
    for p, r in roles.items():
        if dead_from.get(p, 10**9) > day:
            counts[r] = counts.get(r, 0) + 1
    return counts


def _window(text: str, start: int, end: int) -> str:
    return text[max(0, start - WINDOW): end + WINDOW]


def anchors_for_text(text: str, *, roles: dict[str, str], dead_from: dict[str, int],
                     day: int, speaker: str, claims: set[tuple[str, str]]) -> list[dict]:
    """All anchors in one text unit. Each anchor records why it fired and the contradicting or
    checkable fact; it is a CANDIDATE for the read, never a verdict."""
    anchors: list[dict] = []
    alive = _alive_counts(roles, dead_from, day)

    # A — mention of a dead player id (self-mentions skipped; a dead speaker trips the
    # timeline self-check in screen_game instead).
    for m in PLAYER_ID.finditer(text):
        p = m.group(0)
        if p not in roles or p == speaker:
            continue
        if dead_from.get(p, 10**9) <= day:
            anchors.append({"kind": "dead_id", "entity": p,
                            "fact": f"{p} dead since day {dead_from[p]} (revealed {roles[p]})",
                            "span": _window(text, m.start(), m.end())})

    # B — role word whose holders are ALL dead by this day.
    for pat, canon in ROLE_ALIASES:
        m = pat.search(text)
        if m and alive.get(canon, 0) == 0 and any(r == canon for r in roles.values()):
            anchors.append({"kind": "dead_role_word", "entity": canon,
                            "fact": f"no {canon} alive on day {day}",
                            "span": _window(text, m.start(), m.end())})

    # C — count claims vs the true alive count. Matching counts are provably consistent and
    # not flagged (the one safe drop); mismatches may still be legitimate cumulative-kill talk
    # ("we cleared two wolves") — surface-identical to the error, so the read decides.
    for m in NUM_ROLE.finditer(text):
        # a bounded quantifier ("at least one wolf") is not an exact-count claim
        lead = text[max(0, m.start() - 14): m.start()].lower()
        if any(b in lead for b in ("at least", "more than", "over ", "at most", "up to",
                                   "no more than")):
            continue
        n, canon = _NUM[m.group(1).lower()], _canon_role(m.group(2))
        if canon and n != alive.get(canon, 0):
            anchors.append({"kind": "count_mismatch", "entity": canon,
                            "fact": f"{alive.get(canon, 0)} {canon} alive on day {day}, claim says {n}",
                            "span": _window(text, m.start(), m.end())})
    for m in DEF_SINGULAR.finditer(text):
        canon = _canon_role(m.group(1))
        if canon and alive.get(canon, 0) != 1:
            anchors.append({"kind": "count_mismatch", "entity": canon,
                            "fact": f"{alive.get(canon, 0)} {canon} alive on day {day}, "
                                    f"phrase implies exactly 1",
                            "span": _window(text, m.start(), m.end())})
    for m in VAGUE_PLURAL.finditer(text):
        canon = _canon_role(m.group(1))
        if canon and alive.get(canon, 0) < 2:  # "several X" is impossible below 2
            anchors.append({"kind": "count_mismatch", "entity": canon,
                            "fact": f"{alive.get(canon, 0)} {canon} alive on day {day}, "
                                    f"phrase implies several",
                            "span": _window(text, m.start(), m.end())})

    # D — role-claim attribution vs the persisted claim log.
    for m in PLAYER_ID.finditer(text):
        p = m.group(0)
        if p not in roles:
            continue
        window = _window(text, m.start(), m.end())
        if CLAIM_WORD.search(window):
            for pat, canon in ROLE_ALIASES:
                if pat.search(window) and (p, canon) not in claims:
                    anchors.append({"kind": "claim_attrib", "entity": p,
                                    "fact": f"no logged claim {p}->{canon}; logged: "
                                            f"{sorted(r for q, r in claims if q == p) or 'none'}",
                                    "span": window})
    return anchors


def load_strategy_units(record: dict) -> list[dict]:
    """Per-turn private ``updated_strategy`` units from the eval-case sidecar (absent sidecar →
    empty list; the screen still covers public messages)."""
    path = REPO_ROOT / (record.get("eval_cases_path") or "__missing__")
    if not path.exists():
        return []
    units: list[dict] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if row.get("kind") != "agent_action_eval":
            continue
        ec = (row.get("output") or {}).get("eval_case") or {}
        text = ec.get("updated_strategy") or ""
        if not text.strip():
            continue
        units.append({"unit": "updated_strategy", "day": int(ec.get("day", 0)),
                      "phase": ec.get("action_phase"), "speaker": ec.get("player_id"),
                      "seq": (ec.get("agent_message") or {}).get("seq"), "text": text})
    return units


def screen_game(record: dict, strategy_units: list[dict] | None = None
                ) -> tuple[list[dict], Counter, int]:
    """Candidates + deterministic verdicts + counts for one game.

    Returns (rows, counts, scanned_units). Rows carry ``row_type``: "candidate" (needs the read)
    or "verdict" (deterministically wrong — dead vote / question-response to a dead player).
    ``strategy_units`` is injectable for tests; None loads the record's sidecar.
    """
    roles: dict[str, str] = record["roles"]
    dead_from = death_timeline(record)
    rows: list[dict] = []
    counts: Counter = Counter()
    scanned = 0

    def is_dead(p: str, day: int) -> bool:
        return dead_from.get(p, 10**9) <= day

    def base(day, seq, speaker, unit, phase=None):
        return {"game_id": record["game_id"], "arm": record.get("config_name", ""),
                "day": day, "seq": seq, "phase": phase, "speaker": speaker,
                "speaker_role": roles.get(speaker, ""), "unit": unit}

    units: list[dict] = []
    for msg in record.get("day_channel") or []:
        speaker, day = msg.get("player"), int(msg.get("day", 0))
        text = msg.get("message") or ""
        if msg.get("passed") or not text.strip():
            continue
        if speaker == "game_master":  # safe filter: rendered from state, cannot hallucinate
            continue
        if is_dead(speaker, day):  # timeline self-check: a dead speaker falsifies the convention
            counts["dead_speaker_violations"] += 1
        units.append({"unit": "message", "day": day, "seq": msg.get("seq"), "phase": "day",
                      "speaker": speaker, "text": text, "_msg": msg})
    units.extend(load_strategy_units(record) if strategy_units is None else strategy_units)

    for u in units:
        scanned += 1
        anchors = anchors_for_text(u["text"], roles=roles, dead_from=dead_from, day=u["day"],
                                   speaker=u["speaker"], claims=claims_through(record, u["day"]))
        # structural: a question/response addressed AT a dead player is a candidate too
        # (mention-form is ordinary retrospection and is already covered by the dead_id anchor)
        for at in (u.get("_msg") or {}).get("addressed_targets") or []:
            tgt = at.get("target")
            if tgt in roles and is_dead(tgt, u["day"]) and \
                    at.get("addressed_form") in ("question", "response"):
                anchors.append({"kind": "addressed_dead", "entity": tgt,
                                "fact": f"{tgt} dead since day {dead_from[tgt]}, "
                                        f"addressed as {at.get('addressed_form')}",
                                "span": u["text"][:2 * WINDOW]})
        if anchors:
            row = base(u["day"], u.get("seq"), u["speaker"], u["unit"], u.get("phase"))
            row.update({"row_type": "candidate", "text": u["text"], "anchors": anchors})
            rows.append(row)
            counts["candidates"] += 1
            for a in anchors:
                counts[f"anchor_{a['kind']}"] += 1

    # deterministic verdict: a recorded vote for a dead player needs no read
    for dr in record.get("day_resolutions") or []:
        for v in dr.get("votes") or []:
            votee = v.get("votee")
            if votee in roles and is_dead(votee, int(dr["day"])):
                row = base(int(dr["day"]), None, v.get("voter"), "vote")
                row.update({"row_type": "verdict", "kind": "dead_vote", "entity": votee,
                            "fact": f"{votee} dead since day {dead_from[votee]}"})
                rows.append(row)
                counts["verdict_dead_vote"] += 1

    return rows, counts, scanned


def run(records_glob: str = DEFAULT_RECORDS_GLOB, out: str = DEFAULT_OUT,
        include_strategy: bool = True) -> dict:
    records = load_batch_records(records_glob)
    all_rows: list[dict] = []
    totals: Counter = Counter()
    scanned_total = 0
    for rec in records:
        rows, counts, scanned = screen_game(
            rec, strategy_units=None if include_strategy else [])
        all_rows.extend(rows)
        totals.update(counts)
        scanned_total += scanned
    out_path = REPO_ROOT / out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as fh:
        for r in all_rows:
            fh.write(json.dumps(r) + "\n")
    summary = {
        "records_glob": records_glob,
        "games": len(records),
        "units_scanned": scanned_total,
        "candidates": totals.get("candidates", 0),
        "by_count": {k: v for k, v in sorted(totals.items())},
        "out": str(out_path.relative_to(REPO_ROOT)),
    }
    print(json.dumps(summary, indent=2))
    return summary


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--records", default=DEFAULT_RECORDS_GLOB,
                    help="repo-root-relative glob of game-record JSONLs")
    ap.add_argument("--out", default=DEFAULT_OUT, help="repo-root-relative candidates JSONL path")
    ap.add_argument("--no-strategy", action="store_true",
                    help="skip updated_strategy units (public messages only)")
    args = ap.parse_args()
    run(args.records, args.out, include_strategy=not args.no_strategy)


if __name__ == "__main__":
    main()
