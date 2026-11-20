"""Real day subgraph, ten seats, day 1 (opening round only): every model turn stubbed by a 0.5 s
sleep. Compares the old child config (patch_config, no max_concurrency) with child_runnable_config."""
import threading, time, uuid
from types import SimpleNamespace
from langchain_core.runnables.config import patch_config

from Agents.config.langgraph import child_runnable_config, discussion_recursion_limit
from Agents.game_config import GameConfig
from Agents.graphs.day import build_day_graph
from Agents.nodes.day import actors, flow
from Agents.schemas.roles import FIXED_SEATS, lineup
from Agents.tracing import Metrics
from Agents.turn import resolve

NO_REASONING = {"strategy": None, "strategy_verdicts": [], "memory_verdicts": [], "reads": []}
LINEUP = lineup("serial_killer", "speculator")
SEATS = [f"player_{i}" for i in range(1, 11)]
ROLES = dict(zip(SEATS, LINEUP))
starts = []

def turn(payload, config, runtime, phase, prompt, schema, output_key):
    starts.append((time.perf_counter(), threading.current_thread().name, config.get("max_concurrency")))
    time.sleep(0.5)
    d = SimpleNamespace(pass_turn=True, message="", addressed_targets=[])
    return resolve.resolve_decision(d, NO_REASONING, "day_channel", payload, [])

actors.run_memory_informed_action = turn
flow.run_day_summary_agent = lambda current_day, messages, max_retries=1, **kw: ("brief", "fake", {})
flow.filter_openings = lambda entries: entries
resolve.line_echo_of = lambda message, player, earlier: ""

gc = GameConfig()
wolves = [p for p, r in ROLES.items() if r in ("chanteuse", "illusionist")]
graph = build_day_graph().compile()

def run(label, make_cfg):
    starts.clear()
    gid = f"probe-{uuid.uuid4()}"
    state = {"current_day": 1, "day_channel": [], "day_summaries": [], "dead_roster": [], "wolf_channel": [],
             "roles": ROLES, "lineup": LINEUP, "human_players": [], "night_actions": [], "uses_left": {"illusionist": 2},
             "surviving_villagers": [p for p in SEATS if p not in wolves], "surviving_wolves": wolves,
             "no_lynch_streak": 0, "agent_strategies": {}, "day_votes": [], "game_id": gid}
    parent = {"configurable": {"game_config": gc.model_dump(), "game_id": gid}, "recursion_limit": 100}
    cfg = make_cfg(parent)
    t0 = time.perf_counter()
    graph.invoke(state, config=cfg, context={"metrics": Metrics()})
    total = time.perf_counter() - t0
    first = min(s[0] for s in starts)
    offsets = sorted(round(s[0] - first, 2) for s in starts)
    print(f"{label}: max_concurrency={cfg.get('max_concurrency')} turns={len(starts)} "
          f"opening round span={max(offsets) + 0.5:.2f}s total day={total:.2f}s "
          f"threads={len({s[1] for s in starts})} start offsets={offsets}")

limit = discussion_recursion_limit(gc, 10)
run("before (patch_config only)", lambda p: patch_config(p, recursion_limit=limit))
run("after  (child_runnable_config)", lambda p: child_runnable_config(p, recursion_limit=limit))
