"""Live tell-book injection — the second memory channel of the v1 two-channel design (tells + SPs;
observations are synthesis substrate, never injected — read/tactic design record §4).

The book is a small, deterministic prompt block: a role-identification manual for every unrevealed
role — top validated behavior→role tells with their observed subject-role rates — rendered immediately
above the reads instruction (evidence before belief — the book is the how-to-read manual and the read
list is the output it should improve). Deliberately symmetric (owner ruling 2026-07-14, no
role-revealing exclusion): the same shared book lets wolves hunt an investigator, the healer protect
one, and the investigator conceal the pattern. No retrieval, no exploration slot: selection happened
at build time (evaluation/src/loop/tell_credit.build_book — subject-role concentration, support floor,
~3 per (subject role, channel)); the only per-turn logic here is the roles-alive filter (a wolf-marker
is dead weight once both wolves are revealed dead — a free lookup on the public dead roster).

Arm gating is by environment: WW_TELL_BOOK=<path to book.json> (the run harness sets it for the loop
arm only; absent => empty block everywhere, which IS the baseline/memory-off behavior). The book is
PUBLIC information (behavior statistics from past games' revealed roles), so it needs no role gating
and no leak check — every seat may read it.
"""

from __future__ import annotations

import json
import os
from functools import lru_cache

TELL_BOOK_ENV = "WW_TELL_BOOK"

_HEADER = ("== Behavior tells from past games (public study notes: how a behavior correlated with "
           "hidden roles) ==\n")
_FOOTER = ("Use these as priors when forming your reads: a matching behavior shifts suspicion by the "
           "strength shown, it never proves a role.\n")


@lru_cache(maxsize=4)
def _load(path: str) -> tuple:
    return tuple(json.load(open(path)))


def _role_of(death) -> str | None:
    return death.get("role") if isinstance(death, dict) else getattr(death, "role", None)


def tell_book_block(dead_roster: list, cast_role_counts: dict) -> str:
    """The per-turn book block, or "" (no book configured / every entry's subject role revealed dead /
    no census on the payload — legacy replay paths render nothing rather than an unfiltered book)."""
    path = os.environ.get(TELL_BOOK_ENV)
    if not path:
        return ""
    if not cast_role_counts:
        return ""
    dead: dict = {}
    for d in dead_roster or []:
        r = _role_of(d)
        if r:
            dead[r] = dead.get(r, 0) + 1
    unrevealed = {r for r, n in cast_role_counts.items() if n - dead.get(r, 0) > 0}
    entries = [e for e in _load(path) if e.get("subject_role") in unrevealed]
    if not entries:
        return ""
    lines = [f"- {e['text']} (the exhibitor was a {e['subject_role'].replace('_', ' ')} "
             f"{e['subject_count']}/{e['n']} times observed)"
             for e in sorted(entries, key=lambda e: -e.get("subject_lift", 0.0))]
    return _HEADER + "\n".join(lines) + "\n" + _FOOTER
