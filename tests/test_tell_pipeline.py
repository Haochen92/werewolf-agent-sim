"""Guards for the graduated tell pipeline's pure parts (2026-07-13): the lift arithmetic pinned to the
held-out convention, the §6.5 positive-lift-only eligibility, the role-grain book selection (owner
ruling 2026-07-14: no role-revealing exclusion), and the fold's freeze-old lifecycle (drop-or-keep
wording resolution, the probation clock, the fat-null archive with split-check). LLM judge and embedder
are stubbed — the fold's logic is deterministic around them."""

from __future__ import annotations

import json

import pytest

from evaluation.src.loop.tell_credit import (
    build_book, cast_prior, cast_prior_base, credit_eligible, lift_table, subject_lift, subject_role,
)
from evaluation.src.loop.tell_fold import (
    INDEX_ARCHIVE_RECENT, INDEX_PROBATION_RECENT, _resolve_wordings, fold, init_store,
    make_book_collapse,
)
from evaluation.src.loop.tells import _norm

CAST = {f"p{i}": r for i, r in enumerate(
    ["wolf", "wolf", "serial_killer", "villager", "villager", "villager",
     "healer", "investigator", "vigilante"])}


def _games(n):
    return {f"g{i}": CAST for i in range(n)}


def _det(game, player, tell, day=1, channel="vote", flags=()):
    return {"game_id": game, "player": player, "channel": channel, "tell_id": tell, "day": day,
            "evidence_quote": "…", "screen_flags": list(flags)}


# ── lift arithmetic (pinned to heldout_lift.py) ────────────────────────────────────────────────


def test_cast_prior_and_shrunk_lift():
    games = _games(1)
    assert cast_prior(games) == (pytest.approx(3 / 9), 9)
    # tell exhibited by one wolf + one villager: n=2, evil=1, shrunk=(1+5/3)/7, lift=shrunk-1/3
    rows = [_det("g0", "p0", "vote_1"), _det("g0", "p3", "vote_1"),
            _det("g0", "p3", "vote_1", day=2)]        # same exhibitor twice = ONE exhibitor
    t = lift_table(rows, games)[0]
    assert (t["n"], t["evil"]) == (2, 1)
    assert t["shrunk_lift"] == pytest.approx((1 + 5 / 3) / 7 - 1 / 3)


def test_screened_rows_never_count():
    rows = [_det("g0", "p0", "vote_1", flags=["quote_not_in_record"])]
    assert lift_table(rows, _games(1)) == []


def test_credit_eligible_is_positive_lift_only():
    games = _games(10)
    # evil-marker: 8 evil exhibitors; town-marker: 8 town exhibitors — both over the floor
    rows = ([_det(f"g{i}", "p0", "vote_e") for i in range(8)]
            + [_det(f"g{i}", "p3", "vote_t") for i in range(8)])
    table = lift_table(rows, games)
    elig = {t["tell_id"] for t in credit_eligible(table, support_floor=8)}
    assert elig == {"vote_e"}                        # §6.5: town-markers stay diagnostic


# ── the book ───────────────────────────────────────────────────────────────────────────────────


def test_book_is_a_role_identification_manual():
    games = _games(12)
    rows = (
        # wolf-concentrated evil-marker — book candidate under subject wolf
        [_det(f"g{i}", p, "vote_w") for i in range(10) for p in ("p0", "p1")]
        # investigator-concentrated tell — negative evil-lift, but the book carries it (ruling
        # 2026-07-14: every role's identifying tells inject, so e.g. the healer can protect a
        # likely investigator)
        + [_det(f"g{i}", "p7", "disc_inv", channel="discussion") for i in range(10)]
    )
    table = lift_table(rows, games)
    by_id = {t["tell_id"]: t for t in table}
    assert subject_role(by_id["vote_w"]) == "wolf"
    assert subject_role(by_id["disc_inv"]) == "investigator"
    assert subject_lift(by_id["disc_inv"]) > 0        # role-grain strength is positive…
    assert by_id["disc_inv"]["shrunk_lift"] < 0       # …even where the evil-lift is negative

    book = build_book(table, unrevealed_roles={"wolf", "investigator"}, support_floor=5)
    assert {t["tell_id"] for t in book} == {"vote_w", "disc_inv"}
    # the roles-alive filter still bites: both wolves revealed dead => the wolf-marker leaves
    left = build_book(table, unrevealed_roles={"investigator"}, support_floor=5)
    assert {t["tell_id"] for t in left} == {"disc_inv"}
    # book membership and credit stay independent: the investigator tell injects yet never PAYS
    # (§6.5 credits positive evil-lift only)
    elig = {t["tell_id"] for t in credit_eligible(table, support_floor=5)}
    assert "vote_w" in elig and "disc_inv" not in elig


def test_book_collapse_backfills_freed_slot_with_distinct_behavior():
    """The book seats top-3 per (subject, channel); a fragmented behavior can take two of those slots.
    make_book_collapse drops the lower-lift fragment so a DISTINCT behavior backfills. View-layer only —
    subject_lift ordering is unchanged and the collapsed tell keeps its lift-table row (credit intact)."""
    games = _games(12)
    def wolf_rows(tell, n_games):
        return [_det(f"g{i}", p, tell) for i in range(n_games) for p in ("p0", "p1")]  # pure wolf-marker
    # pure wolf-markers: more exhibitors => higher subject_lift, so w1 > w2 > w3 > w4
    rows = (wolf_rows("vote_w1", 12) + wolf_rows("vote_w2", 10)
            + wolf_rows("vote_w3", 9) + wolf_rows("vote_w4", 8))
    table = lift_table(rows, games)
    assert [t["tell_id"] for t in sorted(table, key=lambda t: -subject_lift(t))] == \
        ["vote_w1", "vote_w2", "vote_w3", "vote_w4"]
    text_of = {"vote_w1": "bandwagon vote piles on", "vote_w2": "bandwagon vote joins the pile",
               "vote_w3": "silence when accused", "vote_w4": "defends the accused"}
    judge = lambda new, canon: new.split()[0] == canon.split()[0]  # noqa: E731 — first word = behavior class

    raw = build_book(table, {"wolf"}, per_role_cap=3)                     # collapse=None -> today's behavior
    assert [t["tell_id"] for t in raw] == ["vote_w1", "vote_w2", "vote_w3"]  # dup crowds; w4 excluded

    collapse = make_book_collapse(judge=judge, embedder=_stub_embedder)
    deduped = build_book(table, {"wolf"}, per_role_cap=3, collapse=collapse, text_of=text_of)
    ids = [t["tell_id"] for t in deduped]
    assert ids == ["vote_w1", "vote_w3", "vote_w4"]   # w2 (bandwagon dup) dropped; w4 backfills -> 3 distinct
    assert "vote_w1" in ids and "vote_w2" not in ids  # GUARDRAIL: the class survivor is the HIGHER-lift one


def test_book_collapse_is_non_transitive_safe():
    """A~B and B~C but A≁C: greedy-keep compares a candidate only against already-kept SURVIVORS, so B
    (dup of kept A) is dropped and C is still kept — never wrongly folded away via the dropped B."""
    judge = lambda new, canon: {new.split()[0], canon.split()[0]} in ({"a", "b"}, {"b", "c"})  # noqa: E731
    collapse = make_book_collapse(judge=judge, embedder=_stub_embedder)
    cands = [{"tell_id": "A"}, {"tell_id": "B"}, {"tell_id": "C"}]        # lift-sorted (A highest)
    kept = [t["tell_id"] for t in collapse(cands, {"A": "a x", "B": "b x", "C": "c x"})]
    assert kept == ["A", "C"]


def test_cast_prior_base_registers_selfkeyed():
    base = cast_prior_base(_games(3))
    assert base["tell/vote"] == (pytest.approx(3 / 9), 27)
    assert set(base) == {"tell/vote", "tell/discussion"}


# ── the fold ───────────────────────────────────────────────────────────────────────────────────


SEED = {"vote": [{"tell_id": "vote_1", "text": "votes a player who had drawn no discussion"}],
        "discussion": [{"tell_id": "disc_1", "text": "goes silent when directly accused"}]}


def _mined(game, behavior, channel="vote", exhibitor="p0", day=1):
    return {"game_id": game, "channel": channel, "behavior": behavior, "exhibitor": exhibitor,
            "day": day, "evidence_quote": "…", "screen_flags": []}


def _stub_embedder(texts):
    return [[1.0, 0.0] for _ in texts]              # everything passes the prefilter; the judge decides


def test_fold_wording_resolution_freeze_old(tmp_path):
    init_store(tmp_path, SEED)
    # one wording is the seed tell rephrased (judge says same -> dies into vote_1, instances credit it);
    # one is genuinely new (judge says different -> new probation canonical)
    mined = [_mined("g0", "casts a vote for someone nobody discussed"),
             _mined("g0", "accuses the previous day's lynch leader", exhibitor="p3")]
    judge = lambda new, canon: "vote" in new and "discussed" in new  # noqa: E731
    rep = fold(tmp_path, mined, [], [], _games(1), judge=judge, embedder=_stub_embedder)
    assert rep["new_wordings"] == 2 and rep["new_canonicals"] == 1
    canon = {c["tell_id"]: c for c in json.loads((tmp_path / "canon.json").read_text())}
    assert canon["vote_1"]["text"] == SEED["vote"][0]["text"]     # freeze-old: text never rewritten
    new_id = next(t for t in canon if canon[t]["status"] == "probation")
    rows = [json.loads(l) for l in open(tmp_path / "instances.jsonl")]
    assert {r["tell_id"] for r in rows if r["source_kind"] == "MINED"} == {"vote_1", new_id}


def test_fold_probation_singleton_archives_after_window(tmp_path):
    init_store(tmp_path, SEED)
    judge = lambda a, b: False  # noqa: E731 — the new wording is its own canonical
    rep1 = fold(tmp_path, [_mined("g0", "brand new behavior nobody matches")], [], [],
                _games(1), judge=judge, embedder=_stub_embedder)
    new_id = next(c["tell_id"] for c in json.loads((tmp_path / "canon.json").read_text())
                  if c["status"] == "probation")
    # the new tell enters checklist v1; an epoch of 12 scanned games with zero detections follows
    scanned = [{"game_id": f"g{i}", "player": "p0", "channel": "vote", "prompt_version": "det_v1"}
               for i in range(12)]
    fold(tmp_path, [], [], scanned, _games(12), judge=judge, embedder=_stub_embedder)
    canon = {c["tell_id"]: c for c in json.loads((tmp_path / "canon.json").read_text())}
    assert canon[new_id]["status"] == "archive"     # still a singleton after its K-games window
    assert rep1["fold"] == 1


def test_fold_fat_null_incumbent_archives_with_split_check(tmp_path):
    init_store(tmp_path, SEED)
    games = _games(21)
    # 21 exhibitors of the seed vote tell at exactly the cast prior (7 evil, 14 town) -> |lift|~0
    det = ([_det(f"g{i}", "p0", "vote_1") for i in range(7)]
           + [_det(f"g{i}", p, "vote_1") for i in range(7) for p in ("p3", "p4")])
    rep = fold(tmp_path, [], det, [], games, judge=lambda a, b: False, embedder=_stub_embedder)
    canon = {c["tell_id"]: c for c in json.loads((tmp_path / "canon.json").read_text())}
    assert canon["vote_1"]["status"] == "archive" and canon["vote_1"]["split_check"]
    assert rep["archived_null_lift"] == 1
    # the fold registers the tell family's cast-prior base for the coherence invariant
    assert rep["credited_channels"] == {"tell/vote": "cast_prior", "tell/discussion": "cast_prior"}
    assert rep["base_rates"]["tell/vote"][1] == 21 * 9


# ── the bounded fuzzy-match index ────────────────────────────────────────────────────────────────


def _canon_entry(tid, text, status, channel="vote", born_fold=0, last_scanned_fold=0):
    return {"tell_id": tid, "channel": channel, "text": text, "status": status, "born_fold": born_fold,
            "games_scanned": 0, "last_scanned_fold": last_scanned_fold, "split_check": False}


class _RecordingEmbedder:
    """Records every batch of texts the fuzzy stage embeds, so a test can read back exactly which canon
    entries the bounded index exposed. Returns identical unit vectors -> every candidate clears the
    prefilter, isolating the index-composition rule from the cosine gate."""

    def __init__(self):
        self.seen: list[list[str]] = []

    def __call__(self, texts):
        self.seen.append(list(texts))
        return [[1.0, 0.0] for _ in texts]


def test_resolve_bounds_fuzzy_index_to_recent_slice():
    # incumbents (all kept) + 35 staggered probation + 15 staggered archive; only the recent windows show
    incumbents = [_canon_entry(f"vote_inc{i}", f"incumbent tell {i}", "incumbent") for i in range(3)]
    probation = [_canon_entry(f"vote_p{i}", f"probation tell {i}", "probation", born_fold=i)
                 for i in range(35)]
    archive = [_canon_entry(f"vote_a{i}", f"archive tell {i}", "archive", last_scanned_fold=i)
               for i in range(15)]
    canon = incumbents + probation + archive
    emb = _RecordingEmbedder()
    new = [{"channel": "vote", "text": "a genuinely novel wording"}]
    _resolve_wordings(new, canon, judge=lambda a, b: False, embedder=emb, fold_no=40)
    shown = set(emb.seen[0][len(new):])                  # canon texts the fuzzy index actually saw
    assert shown == ({f"incumbent tell {i}" for i in range(3)}
                     | {f"probation tell {i}" for i in range(35 - INDEX_PROBATION_RECENT, 35)}
                     | {f"archive tell {i}" for i in range(15 - INDEX_ARCHIVE_RECENT, 15)})


def test_resolve_retired_singleton_recurs_as_new_canonical():
    # a probation entry born_fold 0 sits outside the 30-newest window -> off the fuzzy index
    probation = [_canon_entry(f"vote_p{i}", f"probation tell {i}", "probation", born_fold=i)
                 for i in range(35)]
    old = probation[0]
    canon = list(probation)
    judge = lambda new, canon_text: canon_text == old["text"]  # noqa: E731 — fuses ONLY the retired entry
    new = [{"channel": "vote", "text": "rephrasing of the retired probation tell"}]
    resolution, created = _resolve_wordings(new, canon, judge=judge, embedder=_stub_embedder, fold_no=40)
    assert len(created) == 1                              # true match off-index -> fresh probation canonical
    assert created[0]["tell_id"] != old["tell_id"]
    assert resolution[("vote", _norm(new[0]["text"]))] == created[0]["tell_id"]


def test_resolve_exact_match_stays_global_over_full_canon():
    probation = [_canon_entry(f"vote_p{i}", f"probation tell {i}", "probation", born_fold=i)
                 for i in range(35)]
    old = probation[0]                                    # off-index for the fuzzy stage…
    canon = list(probation)
    new = [{"channel": "vote", "text": "  Probation Tell 0  "}]   # …but normalizes identically to it
    resolution, created = _resolve_wordings(new, canon, judge=lambda a, b: False,
                                            embedder=_stub_embedder, fold_no=40)
    assert created == []                                  # exact-match is global -> no duplicate identity
    assert resolution[("vote", _norm(new[0]["text"]))] == old["tell_id"]


def test_resolve_under_cap_channel_matches_whole_canon():
    canon = ([_canon_entry(f"vote_inc{i}", f"incumbent {i}", "incumbent") for i in range(2)]
             + [_canon_entry(f"vote_p{i}", f"probation {i}", "probation", born_fold=i) for i in range(3)]
             + [_canon_entry("vote_a0", "archive 0", "archive", last_scanned_fold=1)])
    expected = {c["text"] for c in canon}                 # everything fits the caps
    emb = _RecordingEmbedder()
    new = [{"channel": "vote", "text": "novel wording"}]
    _resolve_wordings(new, canon, judge=lambda a, b: False, embedder=emb, fold_no=5)
    assert set(emb.seen[0][len(new):]) == expected        # candidate list == whole channel canon


# ── the publication tripwire ─────────────────────────────────────────────────────────────────────


def _canon_map(tmp_path):
    return {c["tell_id"]: c for c in json.loads((tmp_path / "canon.json").read_text())}


_TW_KW = dict(judge=lambda a, b: False, embedder=_stub_embedder)  # noqa: E731 — no wording resolves


def test_tripwire_normal_two_folds_pass_and_carry_last_n(tmp_path):
    init_store(tmp_path, SEED)
    # fold 1: vote_1 detected by three distinct exhibitor-games -> stays incumbent, n=3
    det1 = [_det("g0", "p0", "vote_1"), _det("g1", "p3", "vote_1"), _det("g2", "p4", "vote_1")]
    rep1 = fold(tmp_path, [], det1, [], _games(3), **_TW_KW)
    assert rep1["tripwire"] == {"prior_tells": 0, "head_checked": 0, "ok": True}   # fold 1 trivial
    assert json.loads((tmp_path / "state.json").read_text())["last_n"] == {"vote_1": 3}
    # fold 2: three more distinct exhibitor-games (append-only) -> n climbs to 6, monotone holds
    det2 = [_det("g3", "p3", "vote_1"), _det("g4", "p4", "vote_1"), _det("g5", "p5", "vote_1")]
    rep2 = fold(tmp_path, [], det2, [], _games(6), **_TW_KW)
    assert rep2["tripwire"] == {"prior_tells": 1, "head_checked": 1, "ok": True}
    state2 = json.loads((tmp_path / "state.json").read_text())
    assert state2["last_n"] == {"vote_1": 6}       # matches the recomputed table's n for the head tell


def test_tripwire_monotone_violation_halts_before_persist(tmp_path):
    init_store(tmp_path, SEED)
    det1 = [_det("g0", "p0", "vote_1"), _det("g1", "p3", "vote_1"), _det("g2", "p4", "vote_1")]
    fold(tmp_path, [], det1, [], _games(3), **_TW_KW)          # last_n[vote_1] = 3
    canon_before = (tmp_path / "canon.json").read_text()
    state_before = (tmp_path / "state.json").read_text()
    # fold 2 appends one unrelated detected row, but roles_by_game silently omits g2 — the join drops
    # g2's vote_1 row so its recomputed n falls to 2 < 3
    with pytest.raises(RuntimeError, match="regressed"):
        fold(tmp_path, [], [_det("g3", "p0", "vote_x")], [],
             {"g0": CAST, "g1": CAST, "g3": CAST}, **_TW_KW)
    assert (tmp_path / "canon.json").read_text() == canon_before      # no partial persistence
    assert (tmp_path / "state.json").read_text() == state_before
    assert not (tmp_path / "checklist_v2.json").exists()
    rows = [json.loads(l) for l in open(tmp_path / "instances.jsonl")]
    assert len(rows) == 4 and any(r["tell_id"] == "vote_x" for r in rows)  # fold-2 append stays


def test_tripwire_head_null_archive_is_exempt(tmp_path):
    init_store(tmp_path, SEED)
    # fold 1: vote_1 recurs at the cast prior on 9 exhibitor-games -> incumbent, |lift|~0, n=9<20
    det1 = ([_det(f"g{i}", "p0", "vote_1") for i in range(3)]
            + [_det(f"g{i}", "p3", "vote_1") for i in range(3, 9)])
    fold(tmp_path, [], det1, [], _games(9), **_TW_KW)
    assert json.loads((tmp_path / "state.json").read_text())["last_n"] == {"vote_1": 9}
    # fold 2: twelve more at the prior -> n=21>=20, |lift|~0 -> null-lift archive THIS fold. vote_1 is
    # the channel head, but its exit is ruled by the fold, so continuity holds
    det2 = ([_det(f"g{i}", "p0", "vote_1") for i in range(9, 13)]
            + [_det(f"g{i}", "p3", "vote_1") for i in range(13, 21)])
    rep2 = fold(tmp_path, [], det2, [], _games(21), **_TW_KW)
    assert rep2["archived_null_lift"] == 1
    assert rep2["tripwire"] == {"prior_tells": 1, "head_checked": 1, "ok": True}
    assert _canon_map(tmp_path)["vote_1"]["status"] == "archive"


def test_tripwire_external_head_archive_tamper_trips(tmp_path):
    init_store(tmp_path, SEED)
    det1 = [_det("g0", "p0", "vote_1"), _det("g1", "p3", "vote_1"), _det("g2", "p4", "vote_1")]
    fold(tmp_path, [], det1, [], _games(3), **_TW_KW)          # vote_1 head incumbent, last_n = 3
    # external mutation the fold never ruled: flip the head incumbent to archive in the store
    canon = json.loads((tmp_path / "canon.json").read_text())
    for c in canon:
        if c["tell_id"] == "vote_1":
            c["status"] = "archive"
    (tmp_path / "canon.json").write_text(json.dumps(canon, indent=1))
    with pytest.raises(RuntimeError, match="head"):
        fold(tmp_path, [], [_det("g3", "p3", "vote_1")], [], _games(4), **_TW_KW)
