"""Guard the soft selective dimension-gating reweight (v7 retrieval-precision lever): alignment is
+1 match / -1 mismatch / 0 when nothing comparable, EXCLUDES dist_parity (screened flat), and the
reweight is a soft tilt that can reorder a dim-matched item above a higher-similarity mismatch — while
being a strict no-op when the query has no structured dims (soft-retrieval guarantee)."""

from types import SimpleNamespace

from Agents.memory.retrieval.dimension_gating import alignment, reweight


def _item(score, sit, dims):
    return SimpleNamespace(score=score, matched_situation=sit, _dims=dims)


def test_alignment_full_match_mismatch_and_missing():
    q = {"exposure_class": "safe", "info_landscape_class": "info_rich",
         "players_alive": 8, "is_swing": False}
    assert alignment(q, q) == 1.0
    opp = {"exposure_class": "exposed", "info_landscape_class": "info_starved",
           "players_alive": 4, "is_swing": True}
    assert alignment(q, opp) == -1.0
    assert alignment(q, {}) == 0.0  # nothing comparable → neutral


def test_alignment_excludes_dist_parity():
    # distance_to_parity is NOT a gate dim (screened flat) — differing values must not move alignment
    assert alignment({"distance_to_parity": 1}, {"distance_to_parity": 5}) == 0.0


def test_alignment_alive_bucketed_not_exact():
    # 8 and 9 share the 'early' bucket → match; 8 (early) vs 5 (mid) → mismatch
    assert alignment({"players_alive": 8}, {"players_alive": 9}) == 1.0
    assert alignment({"players_alive": 8}, {"players_alive": 5}) == -1.0


def test_reweight_reorders_matched_above_higher_similarity_mismatch():
    q = {"exposure_class": "safe", "info_landscape_class": "info_rich"}
    matched = _item(0.80, "sit", {"exposure_class": "safe", "info_landscape_class": "info_rich"})
    mism = _item(0.82, "sit", {"exposure_class": "exposed", "info_landscape_class": "info_starved"})
    out = reweight([mism, matched], {"sit": q}, lambda it: it._dims)
    assert out[0] is matched  # 0.80*1.3=1.04 > 0.82*0.7=0.574


def test_reweight_is_noop_without_query_dims():
    a = _item(0.9, "sit", {"exposure_class": "safe"})
    b = _item(0.8, "sit", {"exposure_class": "safe"})
    out = reweight([a, b], {}, lambda it: it._dims)  # no query dims → soft-retrieval no-op
    assert out == [a, b]
    assert a.score == 0.9 and b.score == 0.8
