"""Entry point for one game: seed memory, invoke the compiled parent graph, return the outcome.

``run_game`` runs a single werewolf game end-to-end under one Langfuse trace; ``main`` is the CLI
wrapper that runs one game and prints the result.
"""
from __future__ import annotations

import warnings
from typing import Any

from dotenv import load_dotenv

from langgraph.types import Command

from Agents.graphs.parent import parent_graph_compiled

from Agents.turn import prompt_log, reads_log
from Agents.compute_metrics import compute_game_metrics, push_scores_to_langfuse
from Agents.config import RunConfig, build_runnable_config, normalize_run_config
from Agents.memory import store
from Agents.memory.persistence import seed_memory_from_config
from Agents.observability import EvalCaseSink
from Agents.run_fingerprint import runtime_fingerprint
from Agents.schemas.metrics import GameOutcome
from Agents.schemas.human_player import HumanTurnRequest, HumanTurnResponse
from Agents.driver.hitl_loop import collect_human_response
from Agents.tracing import (
    Metrics,
    create_langfuse_handler,
    flush,
    langfuse,
)


INITIAL_STATE = {
    "day_channel": [],
    "day_summaries": [],
    "wolf_channel": [],
    "investigator_results": [],
    "day_votes": [],
}

_LEGACY_RUN_GAME_OPTION_MAP = {
    "memory_config": "memory_config",
    "session_id": "session_id",
    "game_config": "game",
    "memory_persistence_config": "memory_persistence",
    "reranking_config": "reranking_config",
    "filtering_config": "filtering_config",
    "retrieval_types_config": "retrieval_types_config",
    "game_id": "game_id",
}
_LEGACY_MEMORY_ROLE_KEYS = frozenset(
    {"wolf", "villager", "healer", "investigator", "serial_killer", "vigilante"}
)


def run_game(
    run_config: RunConfig | dict[str, Any] | None = None,
    **legacy_options: Any,
):
    """Run one game from its canonical application configuration.

    ``RunConfig`` describes what to run. This entry point owns how it runs: memory seeding,
    LangGraph ``RunnableConfig`` construction, observability, invocation, and scoring.

    The former loose keyword interface remains as a deprecation shim so existing external scripts do
    not fail immediately. New callers should pass one ``RunConfig`` (or a dict in its field shape).
    """
    # The old function's first positional argument was memory_config. Preserve that form when the
    # dict is unambiguously role flags; a canonical RunConfig dict uses fields such as ``game`` or
    # ``memory_config`` instead.
    if (
        isinstance(run_config, dict)
        and run_config
        and set(run_config) <= _LEGACY_MEMORY_ROLE_KEYS
    ):
        if "memory_config" in legacy_options:
            raise TypeError("memory_config was supplied both positionally and by keyword")
        legacy_options = {"memory_config": run_config, **legacy_options}
        run_config = None

    if legacy_options:
        if run_config is not None:
            raise TypeError("run_config cannot be combined with legacy run_game keyword options")
        unknown = sorted(set(legacy_options) - set(_LEGACY_RUN_GAME_OPTION_MAP))
        if unknown:
            names = ", ".join(unknown)
            raise TypeError(f"run_game() got unexpected keyword argument(s): {names}")
        warnings.warn(
            "Passing individual options to run_game() is deprecated; pass RunConfig(...) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        run_config = {
            _LEGACY_RUN_GAME_OPTION_MAP[key]: value
            for key, value in legacy_options.items()
        }

    run = normalize_run_config(run_config)
    seed_memory_from_config(run.memory_persistence, target_store=store)
    # Adapt the validated application settings to a RunnableConfig, injecting observability and the
    # runtime fingerprint here so the config layer remains framework/tracing-free.
    config = build_runnable_config(
        run,
        callbacks=[create_langfuse_handler()],
        metadata={"runtime_fingerprint": runtime_fingerprint()},
    )
    game_id = config["configurable"]["game_id"]
    normalized_game_config = config["configurable"]["game_config"]
    normalized_memory_persistence_config = config["configurable"][
        "memory_persistence_config"
    ]
    metrics = Metrics()
    eval_sink = EvalCaseSink()
    initial_state = {key: value.copy() for key, value in INITIAL_STATE.items()}

    prompt_log.clear()
    reads_log.clear()

    with langfuse.start_as_current_observation(
        as_type="span",
        name="werewolf-game",
        input=initial_state,
    ) as root:
        root.update_trace(
            name="werewolf_game",
            session_id=run.session_id,
            input=initial_state,
            output={"status": "running"},
            metadata={
                "game_id": game_id,
                "memory_config": config["configurable"]["memory_config"],
                "reranking_config": config["configurable"]["reranking_config"],
                "filtering_config": config["configurable"]["filtering_config"],
                "retrieval_types_config": config["configurable"]["retrieval_types_config"],
                "game_config": normalized_game_config,
                "memory_persistence_config": normalized_memory_persistence_config,
            },
        )
        flush()

        try:
            result = parent_graph_compiled.invoke(
                initial_state,
                config=config,
                context={"metrics": metrics, "eval_sink": eval_sink},
            )
            
            while "__interrupt__" in result:
                request = HumanTurnRequest.model_validate(result["__interrupt__"][0].value)
                human_action: HumanTurnResponse = collect_human_response(request)
                
                result = parent_graph_compiled.invoke(Command(resume=human_action.model_dump()), config=config, context={"metrics": metrics, "eval_sink": eval_sink})
        except Exception as exc:
            error_output = {
                "status": "error",
                "error": repr(exc),
            }
            root.update(output=error_output, level="ERROR", status_message=str(exc))
            root.update_trace(output=error_output)
            flush()
            raise

        final_output = {
            "status": "success",
            "result": result,
            "raw_metrics": metrics.model_dump(mode="json"),
        }
        root.update(output=final_output)
        root.update_trace(output=final_output)

        game_metrics = compute_game_metrics(result, metrics)
        push_scores_to_langfuse(game_metrics, root.trace_id, run.session_id)

    flush()
    return GameOutcome(
        result=result,
        game_metrics=game_metrics,
        raw_metrics=metrics.model_dump(mode="json"),
        game_id=game_id,
        trace_id=root.trace_id,
        eval_records=eval_sink.records,
    )


def main():
    load_dotenv()
    # dump_enabled=False: belt-and-braces with the in-graph poisoning guard — a human game is
    # never mined into the store, and skipping the dump also skips the redundant store re-write.
    outcome = run_game(
        RunConfig(human_player=True, human_role='vigilante', memory_persistence={"dump_enabled": False})
    )
    result = outcome.result

    print(f"Winner: {result['winner']}")
    print(f"Game lasted {result['current_day']} days")
    print(f"Surviving wolves: {result['surviving_wolves']}")
    print(f"Surviving villagers: {result['surviving_villagers']}")

    for msg in result["day_channel"]:
        print(f"[Day {msg.day} · #{msg.seq}] {msg.player}: {msg.message}")


if __name__ == "__main__":
    main()
