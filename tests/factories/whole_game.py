"""Play one whole game on the real game graph and collect what reached the wire.

Install the scripted model first (the `scripted_model` fixture) and pass a graph from the
`game_graph` fixture.
"""

from __future__ import annotations

from pydantic_core import to_jsonable_python

from Agents.config import RunConfig, build_runnable_config, normalize_run_config
from Agents.observability.case_sink import EvalCaseSink
from Agents.schemas.metrics import Metrics
from Agents.state import fresh_game_state
from server.game.pacing import BRANCH_UNITS
from server.game.translate import Translator


def play_game(graph, game: dict, seed: int, sink: EvalCaseSink | None = None) -> tuple[dict, list, set[str]]:
    """Play the game to its end. The game id is built from the lineup and the seed, and the
    game id also seeds the deal, so the same arguments play the same game.

    Args:
        graph: the compiled game graph to run.
        game: the lineup choice, `{"lone_killer": ..., "neutral": ...}`.
        seed: the scripted model's seed, which also goes into the game id.
        sink: where the game's evaluation records go, or None.

    Returns:
        The final state, the events the server's translator made from every chunk, and the
        night branches that reported (the pacing units).
    """
    game_id = f"offline-{game['lone_killer']}-{game['neutral']}-{seed}"
    run = normalize_run_config(RunConfig(game_id=game_id, game=game, memory_persistence={"dump_enabled": False}))
    config = build_runnable_config(run)
    context = {"metrics": Metrics(), "eval_sink": sink}
    translator, events, units = Translator(), [], set()
    for part in graph.stream(fresh_game_state(), config=config, context=context,
                             stream_mode=["updates", "custom"], subgraphs=True, version="v2"):
        chunk = {"type": part["type"], "ns": list(part["ns"]), "data": to_jsonable_python(part["data"])}
        events.extend(translator.translate(chunk))
        if chunk["type"] == "updates" and not chunk["ns"]:
            units |= {n for n in chunk["data"] if n in BRANCH_UNITS}
    return graph.get_state(config).values, events, units
