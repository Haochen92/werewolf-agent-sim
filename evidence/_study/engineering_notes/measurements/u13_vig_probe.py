"""Replays test_a_human_vigilantes_shot_is_spent_once_across_the_pause_and_resume and prints one
line about what happened to the Vigilante's shot. 2026-11-17.

argv: threads=default|serial [spare]. Without "spare", the game the test played at commit a543c724;
with it, the repaired test's game, in which no scripted player targets the Vigilante. (The
"spare" option and the times_targeted field were added after the first 70 runs in
u13_vig_probe_runs.txt.) Run with PYTHONHASHSEED set or unset to separate the two sources of
run-to-run variation. "serial" gives every thread pool one worker, so the seats' turns draw from
the shared random generator in a fixed order.

Printed fields:
  test_would=     what the test's own assertions give on this game (pass/fail)
  state_shots=    shots that went ahead, counted from the state's night records (the test's count)
  metric_shots=   the same count from the night metric, which keeps the record of a seat that died
  uses_left=      bullets left at the end (the Vigilante starts with 2)
  shot_night_death= whether the Vigilante died on a night it fired
  times_targeted= how many night choices named the Vigilante as their target
  game=           a short hash of every night's choices, to tell whether two runs played one game
"""
import hashlib
import json
import sys

import pytest
from langgraph.types import Command

sys.path.insert(0, ".")  # run from the repository root
import Agents.config.langgraph as lg  # noqa: E402

if sys.argv[1] == "threads=serial":
    lg.subgraph_max_concurrency = lambda game: 1

from tests.engine import test_ten_seat_game as T  # noqa: E402

mp = pytest.MonkeyPatch()
game = {"lone_killer": "serial_killer", "neutral": "speculator"}
run = T.normalize_run_config(T.RunConfig(game_id="offline-human-vigilante-5", game=game, human_player=1,
                                         human_role="vigilante", memory_persistence={"dump_enabled": False}))
config = T.build_runnable_config(run)
spare = frozenset(T.initialize_game({}, config)["human_players"]) if "spare" in sys.argv[2:] else frozenset()
T._script_the_model(mp, seed=5, **({"spare": spare} if spare else {}))
if sys.argv[1] == "threads=serial":
    config["max_concurrency"] = 1
metrics = T.Metrics()
context = {"metrics": metrics}
g = T.parent_graph_compiled
result = g.invoke(T.fresh_game_state(), config=config, context=context)
shot_turns = 0
while "__interrupt__" in result:
    req = result["__interrupt__"][0].value
    state = g.get_state(config).values
    if req["phase"] != "vigilante_target":
        ans = {"delegate": True}
    elif T._shots_fired(state, req["player_id"]) == 0:
        ans = {"target": next(t for t in req["valid_targets"] if t.startswith("player_"))}
        shot_turns += 1
    else:
        ans = {"target": "hold_fire"}
    result = g.invoke(Command(resume=ans), config=config, context=context)

final = g.get_state(config).values
v = final["human_players"][0]
state_shots = T._shots_fired(final, v)
metric_records = [(m.day, r) for m in metrics.night_resolutions for r in m.records if r["actor"] == v]
metric_shots = sum(1 for _, r in metric_records if r["action"] == "shoot" and r["result"] != "roleblocked")
shot_nights = {d for d, r in metric_records if r["action"] == "shoot" and r["result"] != "roleblocked"}
targeted = sum(1 for m in metrics.night_resolutions for c in m.choices if c.get("target") == v)
death_nights = {d.day for d in final.get("dead_roster", []) if d.player == v and d.phase == "night"}
test_would = "pass" if (shot_turns >= 1 and state_shots == 1 and final["uses_left"]["vigilante"] == 1) else "fail"
fingerprint = hashlib.sha1(json.dumps([m.choices for m in metrics.night_resolutions], default=str,
                                      sort_keys=True).encode()).hexdigest()[:8]
print(f"test_would={test_would} state_shots={state_shots} metric_shots={metric_shots} "
      f"uses_left={final['uses_left'].get('vigilante')} shot_night_death={bool(shot_nights & death_nights)} "
      f"times_targeted={targeted} resolutions={len(metrics.night_resolutions)} days={final['current_day']} game={fingerprint}")
