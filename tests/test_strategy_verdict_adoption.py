"""Guard the per-SP verdict adoption: follow/override/not_relevant bump the right counters, follow
drives used_count + is returned as a followed key, and retrieved_count bumps on every surfaced point.
The full per-decision verdict record (incl. override/not_relevant) lives in the EvalCase, not here."""

from types import SimpleNamespace

from Agents.schemas.output import StrategyVerdict
from Agents.turn.adoption import process_strategy_adoption

NS = ("strategy_points", "villager", "day_vote")


class FakeStore:
    def __init__(self, keys):
        self.data = {(NS, k): {} for k in keys}

    def get(self, namespace, key):
        v = self.data.get((namespace, key))
        return SimpleNamespace(value=v) if v is not None else None

    def put(self, namespace, key, value, index=True):
        self.data[(namespace, key)] = value


def _run(verdicts, keys=("ka", "kb", "kc")):
    store = FakeStore(keys)
    index_map = {i + 1: k for i, k in enumerate(keys)}  # 1-based index -> store key
    result = {"_strategy_verdicts": verdicts}
    followed_idx, followed_keys = process_strategy_adoption(
        result, {"strategy_point_index_map": index_map}, SimpleNamespace(store=store),
        player_id="player_1", role="villager", action_phase="day_vote", day=2, round_num=0,
    )
    return store, followed_idx, followed_keys


def test_follow_bumps_follow_and_used_and_returns_key():
    store, followed_idx, followed_keys = _run(
        [StrategyVerdict(strategy_index=1, verdict="follow", why="x")]
    )
    val = store.data[(NS, "ka")]
    assert val["follow_count"] == 1 and val["used_count"] == 1
    assert followed_idx == [1] and followed_keys == ["ka"]


def test_override_and_not_relevant_bump_only_their_counters():
    store, followed_idx, followed_keys = _run([
        StrategyVerdict(strategy_index=1, verdict="override", why="better move"),
        StrategyVerdict(strategy_index=2, verdict="not_relevant", why="premise absent"),
    ])
    assert store.data[(NS, "ka")]["override_count"] == 1
    assert "used_count" not in store.data[(NS, "ka")]  # override is NOT a use
    assert store.data[(NS, "kb")]["not_relevant_count"] == 1
    assert followed_idx == [] and followed_keys == []  # neither is a follow


def test_retrieved_count_bumps_on_every_surfaced_point():
    store, *_ = _run([StrategyVerdict(strategy_index=1, verdict="follow", why="x")])
    # all three surfaced points get retrieved_count, regardless of verdict (kc had no verdict at all)
    for k in ("ka", "kb", "kc"):
        assert store.data[(NS, k)]["retrieved_count"] == 1


def test_hallucinated_index_skipped():
    store, followed_idx, followed_keys = _run(
        [StrategyVerdict(strategy_index=9, verdict="follow", why="ghost")]
    )
    assert followed_idx == [] and followed_keys == []  # index 9 not in the map → skipped


def test_dict_form_verdicts_also_work():
    # the carrier may arrive as dicts (serialized) rather than StrategyVerdict objects
    store, followed_idx, _ = _run([{"strategy_index": 1, "verdict": "follow", "why": "x"}])
    assert store.data[(NS, "ka")]["follow_count"] == 1 and followed_idx == [1]
