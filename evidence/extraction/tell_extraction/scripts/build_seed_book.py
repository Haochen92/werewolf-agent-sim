"""FROZEN RECORD — builds the v2 launch seed book (2026-07-14) from the held-out lift table.

v2 = the role-grain book (owner ruling 2026-07-14: NO role-revealing exclusion; the book is a
role-identification manual for EVERY unrevealed role — selection by subject-role concentration via
tell_credit.subject_lift, not credit's evil-lift). Supersedes the 2026-07-13 12-entry balanced book
(`tell_book_v1_seed.json`, wolf+SK subjects only — kept in place: the recorded book-screen results
ran on it). The held-out table predates the `role_priors` field on lift_table entries, so this
script reconstructs per-role slot counts from each entry's (roles, role_rates) pairs — rate =
count/slots, so slots = count/rate — cross-checked for consensus across all entries before use.

Run:  poetry run python evidence/extraction/tell_extraction/scripts/build_seed_book.py
"""

from __future__ import annotations

import json
from pathlib import Path

from evaluation.src.loop.tell_credit import build_book, subject_lift, subject_role

HERE = Path(__file__).resolve().parent
TABLE = HERE.parent / "outputs" / "heldout" / "provisional_lift_table.json"
OUT = Path("evaluation/frozen_eval_sets/tell_book_v2_seed.json")


def main() -> None:
    doc = json.loads(TABLE.read_text())
    tells = doc["tells"]

    # reconstruct per-role slot counts (consensus across entries; a disagreement = corrupt table)
    slots: dict[str, int] = {}
    for t in tells:
        for role, cnt in (t.get("roles") or {}).items():
            rate = (t.get("role_rates") or {}).get(role)
            if cnt and rate:
                s = round(cnt / rate)
                assert slots.setdefault(role, s) == s, f"inconsistent slot count for {role}"
    total = sum(slots.values())
    assert total == doc["provenance"]["games"] * 9, f"slot total {total} != games x 9"
    priors = {r: s / total for r, s in slots.items()}
    for t in tells:
        t["role_priors"] = priors   # channel strings stay as the table wrote them ("disc"/"vote")

    book = build_book(tells, unrevealed_roles=set(priors), per_role_cap=3, support_floor=8)
    entries = [{"tell_id": t["tell_id"], "channel": t["channel"], "text": t["text"],
                "subject_role": subject_role(t),
                "subject_count": (t.get("roles") or {}).get(subject_role(t), 0), "n": t["n"],
                "subject_lift": round(subject_lift(t), 4)} for t in book]
    entries.sort(key=lambda e: -e["subject_lift"])
    OUT.write_text(json.dumps(entries, indent=1))
    by_role: dict[str, int] = {}
    for e in entries:
        by_role[e["subject_role"]] = by_role.get(e["subject_role"], 0) + 1
    print(f"{len(entries)} entries -> {OUT}")
    print("by subject role:", by_role)


if __name__ == "__main__":
    main()
