"""Replays test_a_human_vigilantes_shot_is_spent_once_across_the_pause_and_resume and dumps what
happened to the vigilante's shot. argv: on|off [seed] [unique-suffix]"""
import sys
import pytest
import Agents.config.langgraph as lg
mode = sys.argv[1]; seed = int(sys.argv[2]) if len(sys.argv) > 2 else 5
suffix = sys.argv[3] if len(sys.argv) > 3 else ""
if mode == "off":
    lg.subgraph_max_concurrency = lambda game: None
sys.path.insert(0, ".")  # run from the repository root
from tests.engine import test_ten_seat_game as T
from langgraph.types import Command

mp = pytest.MonkeyPatch()
T._script_the_model(mp, seed=seed)
game = {"lone_killer": "serial_killer", "neutral": "speculator"}
run = T.normalize_run_config(T.RunConfig(game_id=f"offline-human-vigilante-{seed}{suffix}", game=game, human_player=1,
                             human_role="vigilante", memory_persistence={"dump_enabled": False}))
config = T.build_runnable_config(run)
context = {"metrics": T.Metrics()}
g = T.parent_graph_compiled
result = g.invoke(T.fresh_game_state(), config=config, context=context)
log = []
while "__interrupt__" in result:
    req = result["__interrupt__"][0].value
    state = g.get_state(config).values
    if req["phase"] != "vigilante_target":
        ans = {"delegate": True}
    elif T._shots_fired(state, req["player_id"]) == 0:
        ans = {"target": next(t for t in req["valid_targets"] if t.startswith("player_"))}
        log.append(f"day{state['current_day']} SHOOT {ans['target']}")
    else:
        ans = {"target": "hold_fire"}; log.append(f"day{state['current_day']} hold_fire")
    result = g.invoke(Command(resume=ans), config=config, context=context)
final = g.get_state(config).values
v = final["human_players"][0]
recs = [(r.day if hasattr(r, "day") else "?", r.action, getattr(r, "target", None), r.result)
        for r in final.get("night_actions", []) if r.actor == v]
blocks = [(getattr(r, "day", "?"), r.actor, final["roles"].get(r.actor, r.actor), r.action, getattr(r, "target", None), r.result)
          for r in final.get("night_actions", []) if getattr(r, "target", None) == v]
dead = [d for d in final.get("dead_roster", [])]
print(f"mode={mode} seed={seed} vig={v} human_turns={log} vig_records={recs} "
      f"uses_left={final['uses_left'].get('vigilante')} fired={T._shots_fired(final, v)} "
      f"targeted_vig={blocks} vig_dead={any(v in str(d) for d in dead)} days={final['current_day']} winner={final.get('winner')}")
