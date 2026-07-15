"""First-link diagnostic — momentum-adjusted read-deltas for targeted day pushes. DIAGNOSTIC ONLY
(pre-registered, evidence/credit/report.md §5): it never feeds prune, protect, or synthesis. Its job is
the endpoint's known blind spot — driver vs rider: did THIS push move THIS addressee's read, or did the
speaker just join a pile the room was already building? Graduation to a credited channel goes through
the ablation replay, not through this instrument.

Mechanics (v1, approximations named):
- A PUSH is an accusation-stance addressed target on a real utterance (day_channel order = seq).
- Its LINKS are the utterance's other addressed players (design record §3: an addressee's next speaking
  turn, or failing that its vote-time read list, supplies the post-read; the target itself has no
  self-read and is skipped).
- Read value on the target: threat-read = 1.0, town-read = 0.0, 'unclear' = 0.5, shrunk toward 0.5 by
  half for low confidence. delta = after − before; an accusation intends +.
- MOMENTUM adjustment (the herding guard): subtract the addressee's own pre-push trajectory on that
  target, per prior push — a bandwagon join scores ~0, a trend-starter keeps its delta. This is the v1
  approximation of "the shift predicted by prior accusations": per-addressee linear drift, not a fitted
  room model. The residual it cannot remove — "persuaded the room" vs "read the room about to turn and
  spoke first" — is accepted and named in the design record.
- Each row carries the speaker's followed SP keys, so the pre-registered per-tactic instance-density
  census is a groupby away.

Two known undercounts, quarantined here by design: the read-list filler rate (~40% of "unchanged"
entries are cold filler — deltas undercount) and the coarse read lattice. Empty on pre-2026-07-09
dumps (no reads field).

  poetry run python evaluation/src/loop/first_link.py --dumps "batch_results/<run>*.jsonl"
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict

from evaluation.src.loop.credit_backfill import _expand_dumps
from evaluation.src.loop.decision_scoring import THREAT_ROLES

VOTE_SEQ = 10 ** 9  # vote-time reads order after every utterance of the day


def _read_value(read: dict) -> float:
    """Scalar 'how evil does this read say the target is': 1.0 threat / 0.0 town / 0.5 unclear,
    low confidence shrunk halfway toward 0.5 (a hesitant read moves the meter half as far)."""
    role = read.get("suspected_role")
    if role == "unclear":
        return 0.5
    raw = 1.0 if role in THREAT_ROLES else 0.0
    w = 1.0 if read.get("confidence") == "high" else 0.5
    return 0.5 + (raw - 0.5) * w


def _read_timeline(eval_cases: list[dict]) -> dict:
    """(day, player) -> sorted [(seq, {target: value})]: each stated read list, ordered within the day
    by the utterance seq it rode (vote-time reads order last). Cases without reads contribute nothing."""
    tl: dict = defaultdict(list)
    for ec in eval_cases:
        reads = ec.get("reads") or []
        if not reads:
            continue
        if ec.get("action_phase") == "day_vote":
            seq = VOTE_SEQ
        elif ec.get("action_phase") == "day_discussion" and ec.get("agent_message"):
            seq = ec["agent_message"].get("seq", 0)
        else:
            continue  # night reads have no in-day order relative to pushes
        tl[(ec.get("day"), ec.get("player_id"))].append(
            (seq, {r.get("player"): _read_value(r) for r in reads}))
    for k in tl:
        tl[k].sort(key=lambda t: t[0])
    return tl


def _value_at(timeline: list, target: str, before_seq: int | None = None,
              after_seq: int | None = None) -> tuple[float | None, int | None]:
    """The addressee's read value on `target` — latest strictly before `before_seq`, or first strictly
    after `after_seq`. (value, seq); (None, None) when no stated read qualifies."""
    if before_seq is not None:
        for seq, reads in reversed(timeline):
            if seq < before_seq and target in reads:
                return reads[target], seq
    if after_seq is not None:
        for seq, reads in timeline:
            if seq > after_seq and target in reads:
                return reads[target], seq
    return None, None


def compute_first_link(dumps_glob: str) -> dict:
    rows: list[dict] = []
    for dump in _expand_dumps(dumps_glob):
        for line in open(dump):
            if not line.strip():
                continue
            g = json.loads(line)
            roles, path = g.get("roles"), g.get("eval_cases_path")
            if not roles or not path or not os.path.exists(path):
                continue
            cases = []
            for cl in open(path):
                if not cl.strip():
                    continue
                ec = (json.loads(cl).get("output") or {}).get("eval_case")
                if ec:
                    cases.append(ec)
            timeline = _read_timeline(cases)
            followed_by_turn = {}
            for ec in cases:
                if ec.get("action_phase") == "day_discussion" and ec.get("agent_message"):
                    idx = ec.get("strategy_index_to_key") or {}
                    followed_by_turn[(ec.get("day"), ec["agent_message"].get("seq"))] = [
                        idx.get(str(sv.get("strategy_index")))
                        for sv in ec.get("strategy_verdicts") or [] if sv.get("verdict") == "follow"]

            pushes_on: dict = defaultdict(list)   # (day, target) -> [seq, ...] for the momentum count
            utterances = [m for m in g.get("day_channel", [])
                          if not m.get("passed") and m.get("player") != "game_master"]
            for m in utterances:
                for t in m.get("addressed_targets") or []:
                    if t.get("stance") == "accusation" and t.get("target"):
                        pushes_on[(m.get("day"), t["target"])].append(m.get("seq", 0))

            for m in utterances:
                day, seq, speaker = m.get("day"), m.get("seq", 0), m.get("player")
                targets = {t.get("target") for t in m.get("addressed_targets") or []
                           if t.get("stance") == "accusation" and t.get("target")}
                addressed = {t.get("target") for t in m.get("addressed_targets") or [] if t.get("target")}
                for target in targets:
                    prior_pushes = sum(1 for s in pushes_on[(day, target)] if s < seq)
                    for addressee in addressed - {speaker, target}:
                        tl = timeline.get((day, addressee), [])
                        before, before_seq = _value_at(tl, target, before_seq=seq)
                        after, _ = _value_at(tl, target, after_seq=seq)
                        if after is None:
                            continue  # no post-push stated read that day -> no link
                        b = before if before is not None else 0.5
                        delta = after - b
                        # per-addressee pre-push drift on this target, per prior push (the v1 momentum)
                        if prior_pushes and before is not None:
                            start, _ = _value_at(tl, target, before_seq=(tl[0][0] + 1) if tl else 0)
                            drift = ((before - start) / prior_pushes) if start is not None else 0.0
                        else:
                            drift = 0.0
                        rows.append({
                            "game_id": g.get("game_id"), "day": day, "seq": seq,
                            "speaker": speaker, "speaker_role": roles.get(speaker),
                            "target": target, "target_role": roles.get(target),
                            "addressee": addressee,
                            "before": None if before is None else round(b, 3),
                            "after": round(after, 3), "delta": round(delta, 3),
                            "momentum": round(drift, 3), "adjusted": round(delta - drift, 3),
                            "prior_pushes": prior_pushes,
                            "followed_sp_keys": followed_by_turn.get((day, seq), []),
                        })

    n = len(rows)
    by_faction: dict = defaultdict(list)
    for r in rows:
        fac = "deceiver" if r["speaker_role"] in THREAT_ROLES else "town"
        by_faction[fac].append(r["adjusted"])
    summary = {"n_links": n,
               "mean_delta": round(sum(r["delta"] for r in rows) / n, 4) if n else None,
               "mean_adjusted": round(sum(r["adjusted"] for r in rows) / n, 4) if n else None,
               "by_faction": {f: {"n": len(v), "mean_adjusted": round(sum(v) / len(v), 4)}
                              for f, v in by_faction.items()}}
    return {"summary": summary, "rows": rows}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dumps", required=True)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    res = compute_first_link(args.dumps)
    print(json.dumps(res["summary"], indent=1))
    if args.out:
        with open(args.out, "w") as f:
            json.dump(res, f, indent=1)
        print(f"wrote {args.out} ({len(res['rows'])} link rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
