"""Tell-ledger arithmetic — pure, no LLM, no I/O. The credit half of the tell pipeline (tells.py mines
and detects; tell_fold.py curates; this module prices).

Lift convention PINNED to the held-out table that graded the instruments
(evidence/extraction/tell_extraction/scripts/heldout_lift.py, log §14): exhibitor grain — n = distinct
(game_id, player) exhibitors from DETECTED rows only (role-blind, complete denominators; MINED rows are
discovery evidence, never lift) — evil share over n, shrunk toward the cast prior with K=5
pseudo-exhibitors:  shrunk_share = (evil + K·prior)/(n + K);  shrunk_lift = shrunk_share − prior.
The prior comes from the actual casts (3 evil of 9 on the standing role set), never hardcoded.

Two owner rulings are baked in:
- §6.5 (evidence/credit/report.md, 2026-07-13) — CREDIT-ELIGIBLE = positive-lift tells only. A negative
  evil-lift IS the same information read from town's side (faction shares are complementary): crediting
  both directions double-counts, and paying for "looking town" is farmable by a compounding loop.
  Town-markers stay diagnostic.
- Book policy (2026-07-14, supersedes the pre-reg §5 exclusion draft) — the injected book is a
  role-identification manual for EVERY unrevealed role, with NO role-revealing exclusion: inferring a
  specific role from public behavior is the tell mechanism's point, and the shared book is symmetric by
  design (the same information lets wolves hunt an investigator, the healer protect one, and the
  investigator learn to conceal the pattern). Book selection therefore runs on SUBJECT-ROLE
  concentration (subject_lift), never on credit's evil-lift — §6.5 governs what PAYS, not what injects;
  a town-power-role tell has negative evil-lift yet belongs in the book.

The cast-prior base registers under the tell channel's own key (`tell/<channel>`) so
`assert_baseline_coherence` verifies it like every other credited family.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping

from evaluation.src.loop.decision_scoring import THREAT_ROLES

SHRINK_K = 5


def cast_prior(roles_by_game: Mapping[str, Mapping[str, str]]) -> tuple[float, int]:
    """(evil share of role slots, total slots) across the window's casts — the base a tell's exhibitor
    evil-share is lifted over. Computed from the records, so a cast change reprices every tell."""
    slots = Counter(r for roles in roles_by_game.values() for r in roles.values())
    total = sum(slots.values())
    evil = sum(n for r, n in slots.items() if r in THREAT_ROLES)
    return (evil / total if total else 0.0, total)


def lift_table(detected_rows: list[dict], roles_by_game: Mapping[str, Mapping[str, str]]) -> list[dict]:
    """Per-tell lift entries from DETECTED instance rows. Rows flagged by the structural screens
    (screen_flags) never count; rows whose game/player fail the role join are dropped (a join failure
    is a wiring bug upstream, not a zero)."""
    prior, total_slots = cast_prior(roles_by_game)
    slots = Counter(r for roles in roles_by_game.values() for r in roles.values())
    role_priors = {role: cnt / total_slots for role, cnt in slots.items()} if total_slots else {}
    exhibitors: dict[str, set] = defaultdict(set)
    channel: dict[str, str] = {}
    for r in detected_rows:
        if r.get("screen_flags"):
            continue
        role = (roles_by_game.get(r.get("game_id")) or {}).get(r.get("player"))
        if role is None:
            continue
        exhibitors[r["tell_id"]].add((r["game_id"], r["player"], role))
        channel[r["tell_id"]] = r.get("channel", r["tell_id"].split("_")[0])
    table = []
    for tid, ex in exhibitors.items():
        n = len(ex)
        evil = sum(1 for *_, role in ex if role in THREAT_ROLES)
        shrunk = (evil + SHRINK_K * prior) / (n + SHRINK_K)
        roles_c = Counter(role for *_, role in ex)
        table.append({
            "tell_id": tid, "channel": channel[tid], "n": n, "evil": evil,
            "raw_share": evil / n, "shrunk_share": shrunk, "shrunk_lift": shrunk - prior,
            "roles": dict(roles_c),
            "role_rates": {role: roles_c.get(role, 0) / cnt for role, cnt in slots.items()},
            "role_priors": role_priors,
        })
    return sorted(table, key=lambda t: -abs(t["shrunk_lift"]))


def credit_eligible(table: list[dict], support_floor: int = 8) -> list[dict]:
    """The §6.5 ruling: positive-lift tells over the support floor. This set (plus the book) is what may
    charge a deceiver's concealment; town-markers (negative lift) are diagnostic only."""
    return [t for t in table if t["shrunk_lift"] > 0 and t["n"] >= support_floor]


def subject_role(entry: dict) -> str | None:
    """The role a tell points at — its dominant per-slot exhibitor rate. Drives the roles-alive filter:
    a wolf-marker is dead weight once both wolves are revealed dead."""
    rates = entry.get("role_rates") or {}
    return max(rates, key=rates.get) if rates and max(rates.values()) > 0 else None


def subject_lift(entry: dict) -> float:
    """The book's ranking stat: shrunk concentration of the tell's SUBJECT role among its exhibitors,
    over that role's cast prior (the held-out "investigator ×8.2" family scores here). Same shrinkage
    construction as the evil-lift — subject share pulled toward the prior with K pseudo-exhibitors —
    but role-grain, so it prices identification strength for town-power-role tells that evil-lift
    scores negative. 0.0 when the entry carries no exhibitors or no priors."""
    subj = subject_role(entry)
    prior = (entry.get("role_priors") or {}).get(subj)
    n = entry.get("n", 0)
    if subj is None or prior is None or not n:
        return 0.0
    count = (entry.get("roles") or {}).get(subj, 0)
    return (count + SHRINK_K * prior) / (n + SHRINK_K) - prior


def build_book(table: list[dict], unrevealed_roles: set[str], *, per_role_cap: int = 3,
               support_floor: int = 8, collapse=None, text_of: Mapping[str, str] | None = None) -> list[dict]:
    """The injected tell book — a role-identification manual for EVERY unrevealed role (owner ruling
    2026-07-14: no role-revealing exclusion; the shared book is symmetric — see the module docstring).
    Per (subject role, channel): the top per_role_cap tells by subject_lift over the support floor.
    Channel-balanced, because the book serves discussion AND vote reads and one family's higher lifts
    would otherwise crowd the other channel out (the 2026-07-13 book-screen composition artifact).
    Ranked by subject-role concentration, NOT credit's evil-lift: §6.5 decides what pays, this decides
    what informs, and the two deliberately disagree on town-subject tells. Deterministic
    filter-and-rank — no retrieval, no exploration slot (tell credit is off-policy: candidates mature
    without injection, and an unvalidated tell in the book actively misleads live reads).

    `collapse` (optional): a view-layer same-behavior de-duplicator run PER (subject role, channel) on
    the lift-sorted candidate pool BEFORE the per_role_cap cut, so a behavior that fragmented into
    several canonicals (the unwired audit's residual reaching the prompt) takes ONE slot and the freed
    slots backfill with distinct behaviors. INJECTED, never imported here (this module stays LLM-free):
    the driver passes the fold's judge+embedder cascade (`make_book_collapse`); `collapse=None` is
    today's exact behavior. It keeps the highest-lift member of each class (candidates arrive
    lift-sorted), so diversity never costs lift, and is view-layer only (canon/ledger/credit untouched —
    nothing pooled)."""
    groups: dict[tuple, list[dict]] = defaultdict(list)
    for t in sorted(table, key=lambda t: -subject_lift(t)):
        subj = subject_role(t)
        if subj is None or subj not in unrevealed_roles:
            continue
        if t["n"] < support_floor or subject_lift(t) <= 0:
            continue
        groups[(subj, t["channel"])].append(t)
    picked: list[dict] = []
    for cands in groups.values():
        if collapse is not None:
            cands = collapse(cands, text_of or {})
        picked.extend(cands[:per_role_cap])
    return picked


def render_book(book: list[dict], text_of: Mapping[str, str]) -> str:
    """The prompt block: one calibrated line per tell — the behavior plus how strongly it identified
    its subject role (subject-role exhibitor count over N), so the agent weighs strong tells above
    weak ones."""
    lines = []
    for t in sorted(book, key=lambda t: -subject_lift(t)):
        subj = subject_role(t)
        cnt = (t.get("roles") or {}).get(subj, 0)
        lines.append(f"- {text_of.get(t['tell_id'], t['tell_id'])} "
                     f"(the exhibitor was a {str(subj).replace('_', ' ')} {cnt}/{t['n']} times observed)")
    return "\n".join(lines)


def build_book_file(table: list[dict], text_of: Mapping[str, str], out_path,
                    unrevealed_roles: set[str] | None = None, *, collapse=None, **book_kwargs) -> int:
    """Emit the live-injection book artifact (Agents/memory/tell_book.py consumes it via WW_TELL_BOOK):
    the built book's entries with their text, subject role, and subject-grain calibration, so the live
    side's only per-turn logic is the roles-alive filter. Build-time selection (subject concentration,
    support floor, per-(role, channel) cap, and the optional same-behavior `collapse`) happens here, in
    build_book. `unrevealed_roles` defaults to every role in the table's rates (game start)."""
    import json

    roles = unrevealed_roles
    if roles is None:
        roles = {r for t in table for r in (t.get("role_rates") or {})}
    book = build_book(table, roles, collapse=collapse, text_of=text_of, **book_kwargs)
    entries = [{"tell_id": t["tell_id"], "channel": t["channel"],
                "text": text_of.get(t["tell_id"], t["tell_id"]),
                "subject_role": subject_role(t),
                "subject_count": (t.get("roles") or {}).get(subject_role(t), 0), "n": t["n"],
                "subject_lift": round(subject_lift(t), 4)} for t in book]
    with open(out_path, "w") as f:
        json.dump(entries, f, indent=1)
    return len(entries)


def cast_prior_base(roles_by_game: Mapping[str, Mapping[str, str]],
                    channels: tuple = ("vote", "discussion")) -> dict:
    """The tell family's baseline registration for assert_baseline_coherence: the cast prior IS the
    base a tell's share is differenced against, keyed under the tell channel's own name (self-keyed,
    like the conceal family). n = total role slots (non-degenerate iff the window has games)."""
    prior, slots = cast_prior(roles_by_game)
    return {f"tell/{ch}": (prior, slots) for ch in channels}
