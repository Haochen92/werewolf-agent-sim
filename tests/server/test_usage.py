"""A game's tokens and call times are counted per model and hour, saved on its row as it goes,
carried over a restart, and priced when its replay is read (server/game/usage.py)."""
from uuid import uuid4

from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, LLMResult

from server.database_models.game import GameRow
from server.game.usage import UsageMeter, average_call_seconds, game_cost
from server.storage.replay_service import _summary
from tests.fixtures.server import FakeGraph


def _call(meter, model, input=1000, cached=0, output=200, reasoning=0, fail=False):
    run = uuid4()
    meter.on_chat_model_start({}, [], run_id=run, metadata={"ls_model_name": model})
    if fail:
        meter.on_llm_error(RuntimeError("429"), run_id=run)
        return
    usage = {"input_tokens": input, "output_tokens": output, "total_tokens": input + output,
             "input_token_details": {"cache_read": cached}, "output_token_details": {"reasoning": reasoning}}
    meter.on_llm_end(LLMResult(generations=[[ChatGeneration(message=AIMessage("ok", usage_metadata=usage))]]),
                     run_id=run)


def test_calls_are_counted_per_model_and_a_failed_call_adds_no_tokens():
    meter = UsageMeter()
    _call(meter, "deepseek-v4-pro", cached=600, reasoning=50)
    _call(meter, "deepseek-v4-pro")
    _call(meter, "gemini-3.1-flash-lite")
    _call(meter, "deepseek-v4-pro", fail=True)
    buckets = {b["model"]: b for b in meter.snapshot()["buckets"]}
    pro = buckets["deepseek-v4-pro"]
    assert (pro["calls"], pro["failed"], pro["input"], pro["cached"], pro["output"], pro["reasoning"]) == (
        2, 1, 2000, 600, 400, 50)
    assert buckets["gemini-3.1-flash-lite"]["calls"] == 1
    assert not meter.changed  # a snapshot is what gets saved


def test_a_restarted_game_carries_on_from_its_saved_counts():
    first = UsageMeter()
    _call(first, "deepseek-v4-pro")
    resumed = UsageMeter(first.snapshot())
    _call(resumed, "deepseek-v4-pro")
    assert sum(b["calls"] for b in resumed.snapshot()["buckets"]) == 2


def test_cost_and_call_time_come_from_the_counts_and_unknown_shows_nothing():
    usage = {"buckets": [
        {"model": "deepseek-v4-pro", "hour": "2026-10-04T12:00:00+00:00", "calls": 4, "failed": 0,
         "input": 1_000_000, "cached": 400_000, "output": 100_000, "reasoning": 0, "seconds": 20.0},
        {"model": "gemini-3.1-flash-lite", "hour": "2026-10-04T12:00:00+00:00", "calls": 1, "failed": 0,
         "input": 0, "cached": 0, "output": 0, "reasoning": 0, "seconds": 9.0},
    ]}
    assert game_cost(usage) == round(0.396 + 0.0088 + 0.198, 4)
    assert average_call_seconds(usage, "deepseek/deepseek-v4-pro") == 5.0
    assert average_call_seconds(usage) == 5.0  # the model with the most calls
    assert game_cost(None) is None and average_call_seconds(None) is None
    usage["buckets"][1]["model"] = "unpriced-model"
    assert game_cost(usage) is None


def test_the_replay_summary_carries_cost_and_call_time_but_not_the_raw_counts():
    row = GameRow(game_id="g", status="completed", winner="villagers", days=3, n_events=10, n_humans=0,
                  cast_role_counts={}, model="deepseek/deepseek-v4-pro", usage={"buckets": [
                      {"model": "deepseek-v4-pro", "hour": "2026-10-04T12:00:00+00:00", "calls": 2,
                       "failed": 0, "input": 1000, "cached": 0, "output": 100, "reasoning": 0, "seconds": 8.0}]})
    summary = _summary(row)
    assert summary.cost_usd is not None and summary.avg_call_seconds == 4.0
    assert "usage" not in summary.model_dump()


class _Repo:
    def __init__(self):
        self.updates = []

    async def record_events(self, game_id, events):
        return True

    async def update_game(self, game_id, **fields):
        self.updates.append(fields)
        return True

    async def record_cast(self, game_id, cast):
        return True


async def test_usage_is_saved_at_most_every_30_seconds_and_always_at_the_end(quiet_session):
    repo = _Repo()
    session = quiet_session(FakeGraph([]), repository=repo)
    _call(session.usage_meter, "gemini-3.5-flash-lite")
    await session._persist_tail()
    _call(session.usage_meter, "gemini-3.5-flash-lite")
    await session._persist_tail()  # too soon: held back
    assert [list(u) for u in repo.updates] == [["usage"]]
    session.game_over = True
    await session._persist_tail()  # the end always saves
    assert repo.updates[-1]["usage"]["buckets"][0]["calls"] == 2


def test_the_model_menu_averages_only_games_that_can_be_priced_memory_off_and_on_apart():
    from server.storage.replay_service import average_costs

    usage = lambda calls: {"buckets": [
        {"model": "deepseek-v4-pro", "hour": "2026-10-04T12:00:00+00:00", "calls": calls, "failed": 0,
         "input": 1_000_000 * calls, "cached": 0, "output": 0, "reasoning": 0, "seconds": 1.0}]}
    unpriced = {"buckets": [{**usage(1)["buckets"][0], "model": "unpriced-model"}]}
    rows = [("deepseek/deepseek-v4-pro", False, usage(1)), ("deepseek/deepseek-v4-pro", False, usage(3)),
            ("deepseek/deepseek-v4-pro", False, None), ("deepseek/deepseek-v4-pro", False, unpriced),
            ("deepseek/deepseek-v4-pro", True, usage(5))]  # memory on: its own mean
    assert average_costs(rows) == {("deepseek/deepseek-v4-pro", False): (round((0.66 + 1.98) / 2, 4), 2),
                                   ("deepseek/deepseek-v4-pro", True): (3.3, 1)}
