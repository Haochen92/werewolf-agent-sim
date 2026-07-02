"""Graduated 2026-07-02 → evaluation/src/experiments/tagger_eval.py (mode=accuracy); this file is the frozen original apparatus.

v7 (d) — TAG ACCURACY check (not effectiveness): are the tagger's per-field tags CORRECT?

Settles the pre-run question: the credit loop weighs role_reveal / framing / credibility, but those fields
were never validated against ground truth (only the holistic verdict's de-halo/redundancy were). Here:

  role_reveal  -> cross-tab vs a DETERMINISTIC self-claim detector on the raw day_channel messages (the
                  one ground-truthable axis) AND vs the in-game day-summary "Role claims:" prose line.
  framing      -> distribution BY FACTION (deceivers should skew 'manipulative'; town should not).
  credibility  -> distribution (sanity: not degenerate).

Deterministic detector catches EXPLICIT own-claims ("I am the investigator", "I investigated ..."); it
misses implicit/challenge claims, so: regex-found-but-tagger-missed = likely tagger FALSE NEGATIVE
(concerning); tagger-flagged-but-regex-missed = either implicit catch (good) or hallucination (read the
dumped examples). Per [[feedback-semantic-eval-not-string-parse]] the residual semantic cases need a read.

  GOOGLE_GENAI_PRO_MODEL=gemini-3.1-flash-lite GOOGLE_GENAI_PRO_BACKUP_MODEL=gemini-3.1-flash-lite \
    poetry run python evidence/v7_final/tagger_accuracy.py
"""

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from evaluation.src.loop.discussion_tagger import tag_game  # noqa: E402

SOURCES = ["batch_results/v6ab_baseline.jsonl", "batch_results/v6ab_skboth.jsonl"]
N_PER_SOURCE = 4
ROLE_WORDS = r"investigator|healer|vigilante|villager|wolf|serial[\s_]?killer|seer|cop|doctor|detective|sheriff"
# explicit FIRST-PERSON role claim in a discussion message
CLAIM_PAT = re.compile(
    rf"\b(i\s*'?\s*m|i\s+am)\s+(the\s+|a\s+|your\s+)?({ROLE_WORDS})\b"
    rf"|\bmy\s+role\s+is\b"
    rf"|\bas\s+(the\s+|your\s+)?({ROLE_WORDS})\b"
    rf"|\bi\s+investigated\b|\bi\s+(healed|saved|protected)\b|\bi\s+(am|was)\s+the\s+one\s+who\b",
    re.IGNORECASE,
)


def _faction(role: str) -> str:
    return role if role in ("wolf", "serial_killer") else "town"


def _detector_claims(record: dict) -> dict:
    """(day, player) -> True if the player made an explicit self role-claim in raw day_channel."""
    claims: dict = {}
    for m in record.get("day_channel", []):
        msg = m.get("message") or ""
        if msg and CLAIM_PAT.search(msg):
            claims[(m.get("day"), m.get("player"))] = msg
    return claims


def _summary_claim_days(record: dict) -> set:
    """Days whose in-game summary 'Role claims:' line is non-empty (the persisted-prose reference; the
    structured RoleClaim list is computed in-game but discarded, only this prose line survives)."""
    days = set()
    for s in record.get("day_summaries", []):
        for line in (s.get("summary") or "").splitlines():
            ls = line.strip().lower()
            if ls.startswith("role claims:") and "none" not in ls.split(":", 1)[1]:
                days.add(s.get("day"))
    return days


def main() -> int:
    games = []
    for src in SOURCES:
        if not Path(src).exists():
            continue
        for line in list(open(src))[:N_PER_SOURCE]:
            if line.strip():
                games.append(json.loads(line))
    print(f"tagging {len(games)} games for ACCURACY ...", flush=True)

    # role_reveal vs deterministic detector
    rr_counts = Counter()                 # tagger role_reveal distribution
    confirmed = missed_by_tagger = tagger_only = 0
    tagger_only_examples, missed_examples = [], []
    summary_day_agree = Counter()         # (tagger_any_reveal_on_day, summary_claim_on_day)
    # framing / credibility by faction
    framing = defaultdict(Counter)
    credibility = defaultdict(Counter)

    for g in games:
        roles = g.get("roles", {})
        det = _detector_claims(g)
        det_keys = set(det)
        summ_days = _summary_claim_days(g)
        disc, _ = tag_game(g)

        tagger_reveal_days = set()
        for (day, player), t in disc.items():
            role = roles.get(player, "?")
            fac = _faction(role)
            rr = t["role_reveal"]
            rr_counts[rr] += 1
            framing[fac][t["framing"]] += 1
            credibility[fac][t["credibility"]] += 1
            if rr != "none":
                tagger_reveal_days.add(day)
            if rr == "own_role_claim":
                if (day, player) in det_keys:
                    confirmed += 1
                else:
                    tagger_only += 1
                    if len(tagger_only_examples) < 6:
                        msgs = [m["message"] for m in g["day_channel"]
                                if m.get("day") == day and m.get("player") == player and m.get("message")]
                        tagger_only_examples.append((player, role, day, " | ".join(msgs)[:200]))
        # detector claims the tagger did NOT flag as own_role_claim
        flagged = {(d, p) for (d, p), t in disc.items() if t["role_reveal"] == "own_role_claim"}
        for k in det_keys - flagged:
            missed_by_tagger += 1
            if len(missed_examples) < 6:
                d, p = k
                missed_examples.append((p, roles.get(p, "?"), d, det[k][:200]))
        for day in set([s.get("day") for s in g.get("day_summaries", [])]):
            summary_day_agree[(day in tagger_reveal_days, day in summ_days)] += 1

    det_total = confirmed + missed_by_tagger
    print("\n=== role_reveal vs DETERMINISTIC self-claim detector (raw day_channel) ===")
    print(f"  tagger role_reveal distribution: {dict(rr_counts)}")
    print(f"  detector found {det_total} explicit self-claims")
    print(f"  CONFIRMED (tagger own_role_claim & detector agree): {confirmed}")
    print(f"  detector-found but tagger MISSED (likely false neg): {missed_by_tagger}"
          f"  -> recall {confirmed/det_total:.2f}" if det_total else "  (no detector claims)")
    print(f"  tagger own_role_claim w/o explicit detector match: {tagger_only}"
          f"  (implicit catch OR hallucination -> read below)")
    print("\n  -- tagger own_role_claim WITHOUT a regex match (eyeball these) --")
    for p, role, day, msg in tagger_only_examples:
        print(f"    d{day} {p}({role}): {msg!r}")
    print("\n  -- detector claims the tagger MISSED (eyeball these) --")
    for p, role, day, msg in missed_examples:
        print(f"    d{day} {p}({role}): {msg!r}")

    print("\n=== role_reveal vs in-game day-summary 'Role claims:' line (per day) ===")
    print("  (tagger_reveal, summary_claim): count")
    for k in sorted(summary_day_agree, reverse=True):
        print(f"    tagger={k[0]!s:5} summary={k[1]!s:5}: {summary_day_agree[k]}")

    print("\n=== framing BY FACTION (deceivers should skew 'manipulative') ===")
    for fac in ("town", "wolf", "serial_killer"):
        c = framing[fac]
        tot = sum(c.values()) or 1
        print(f"  {fac:14} n={tot:3}  " + "  ".join(f"{k}={c[k]}({c[k]/tot:.0%})"
              for k in ("none", "legitimate", "manipulative")))

    print("\n=== credibility distribution (sanity: not degenerate) ===")
    for fac in ("town", "wolf", "serial_killer"):
        c = credibility[fac]
        tot = sum(c.values()) or 1
        print(f"  {fac:14} n={tot:3}  " + "  ".join(f"{k}={c[k]}({c[k]/tot:.0%})"
              for k in ("low", "medium", "high")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
