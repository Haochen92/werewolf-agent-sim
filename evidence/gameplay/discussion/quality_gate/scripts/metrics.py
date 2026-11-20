"""Deterministic discussion-quality metrics for the concurrent-vs-sequential gate.

Auditable counts over transcripts (no LLM): redundancy/echo, turn-fairness, volume.
Handles both schemas: concurrent {day,round,player,message}, sequential
{day,seq,player,message,addressed_targets,passed,firing_reason}.
"""
from __future__ import annotations
import json, re, glob
from difflib import SequenceMatcher
from statistics import mean

SIM = 0.60  # near-duplicate threshold on normalized text


def norm(t: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", (t or "").lower()).strip()


def dc_of(rec):
    r = rec.get("result")
    d = r.get("day_channel") if isinstance(r, dict) else None
    return d or rec.get("day_channel") or []


def real_msgs(dc):
    return [m for m in dc if not m.get("passed")]


def by_day(dc):
    days = {}
    for m in dc:
        days.setdefault(m["day"], []).append(m)
    return days


def day_metrics(msgs):
    """msgs: real (non-pass) messages for one day, in order."""
    n = len(msgs)
    if n == 0:
        return None
    # turn-fairness
    counts = {}
    for m in msgs:
        counts[m["player"]] = counts.get(m["player"], 0) + 1
    distinct = len(counts)
    max_share = max(counts.values()) / n
    # max consecutive same speaker
    maxc = cur = 1
    for i in range(1, n):
        cur = cur + 1 if msgs[i]["player"] == msgs[i-1]["player"] else 1
        maxc = max(maxc, cur)
    # redundancy: each msg vs all prior msgs same day; echo if max sim >= SIM
    texts = [norm(m["message"]) for m in msgs]
    echoes = 0
    same_round_echoes = 0
    for i in range(1, n):
        best = 0.0; best_j = -1
        for j in range(i):
            if not texts[i] or not texts[j]:
                continue
            s = SequenceMatcher(None, texts[i], texts[j]).ratio()
            if s > best:
                best, best_j = s, j
        if best >= SIM:
            echoes += 1
            if best_j >= 0 and msgs[i].get("round") is not None \
               and msgs[i].get("round") == msgs[best_j].get("round"):
                same_round_echoes += 1
    return dict(n=n, distinct=distinct, max_share=round(max_share, 2),
                max_consec=maxc, echoes=echoes, echo_rate=round(echoes / n, 2),
                same_round_echoes=same_round_echoes)


def game_summary(dc):
    rms = real_msgs(dc)
    days = by_day(rms)
    rows = []
    for d in sorted(days):
        dm = day_metrics(days[d])
        if dm:
            rows.append((d, dm))
    return rows


def load_games(path, predicate=None, limit=None):
    out = []
    for line in open(path):
        rec = json.loads(line)
        if rec.get("status") == "error":
            continue
        dc = dc_of(rec)
        if not dc:
            continue
        if predicate and not predicate(rec):
            continue
        out.append((rec, dc))
        if limit and len(out) >= limit:
            break
    return out


def report(label, games):
    print(f"\n{'='*72}\n{label}  ({len(games)} games)\n{'='*72}")
    all_days = []
    for gi, (rec, dc) in enumerate(games, 1):
        rows = game_summary(dc)
        winner = rec.get("winner")
        print(f"  game {gi} (winner={winner}):")
        for d, m in rows:
            extra = f" same_round_echo={m['same_round_echoes']}" if m['same_round_echoes'] else ""
            print(f"    day {d}: n={m['n']:2d} distinct={m['distinct']} "
                  f"max_share={m['max_share']} max_consec={m['max_consec']} "
                  f"echoes={m['echoes']} echo_rate={m['echo_rate']}{extra}")
            all_days.append(m)
    if all_days:
        print(f"  -- AGGREGATE over {len(all_days)} game-days --")
        print(f"     mean utterances/day : {mean(m['n'] for m in all_days):.1f}")
        print(f"     mean distinct/day   : {mean(m['distinct'] for m in all_days):.1f}")
        print(f"     mean max_share      : {mean(m['max_share'] for m in all_days):.2f}")
        print(f"     mean max_consec     : {mean(m['max_consec'] for m in all_days):.2f}")
        print(f"     mean echo_rate      : {mean(m['echo_rate'] for m in all_days):.2f}")
        print(f"     total same_round_echoes: {sum(m['same_round_echoes'] for m in all_days)}")
    return all_days


if __name__ == "__main__":
    G = "evidence/sequential_discussion/quality_gate/data"
    seq = load_games(f"{G}/gate_sequential.jsonl")
    seq_off = [(r, d) for r, d in seq if r.get("config_name") == "all_disabled"]
    seq_on  = [(r, d) for r, d in seq if r.get("config_name") == "all_enabled"]
    # fold in retry if present
    try:
        seq_on += load_games(f"{G}/gate_sequential_memon_retry.jsonl")
    except FileNotFoundError:
        pass

    conc_off = load_games("batch_results/werewolf_flashlite_3_v1.jsonl", limit=4)
    conc_on  = load_games("batch_results/werewolf_flashlite_3_v1_deduped.jsonl", limit=4)

    print("\n" + "#"*72 + "\n# DISCUSSION-QUALITY GATE — deterministic metrics\n" + "#"*72)
    print("# echo_rate = frac of day's msgs >=0.60 similar to an earlier msg that day")
    print("# max_share = largest single speaker's share of a day; max_consec = longest same-speaker run")
    a = report("SEQUENTIAL  mem-OFF", seq_off)
    b = report("CONCURRENT  mem-OFF", conc_off)
    c = report("SEQUENTIAL  mem-ON",  seq_on)
    e = report("CONCURRENT  mem-ON",  conc_on)
