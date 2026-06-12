"""Build the `v5_0_nethorizon` store — full offline re-extraction of the frozen v5_0 source games
with the net-horizon outcome framing (impact_on_final_game_outcome first), then the SAME downstream
dedup, into a fresh store. The config-flag variant for the wolf/SK myopic-framing A/B.

Mirrors how v5_0 itself was seeded — a fresh empty store accumulated game-by-game through the live
dedup — but full-role (all six), not the namespace-scoped augment pass. The ONLY difference from v5_0
is the extraction prompt (already changed, commits e7494fe/8ac5adc), so a paired arm isolates the
framing. See evidence/memory_system/effectiveness/paired_ab/nethorizon_design.md.

  poetry run python scripts/build_nethorizon_store.py \
      --output-store-dir memory_stores/v5_0_nethorizon --cache-prefix
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from Agents.memory.deduplication import (
    run_downstream_observation_dedup,
    run_downstream_strategy_dedup,
)
from Agents.memory.extraction import (
    build_role_extraction_prefix,
    extraction_inputs_from_frozen_case,
)
from Agents.memory.extraction.extraction_agent import extract_postgame_per_role
from Agents.memory.persistence import (
    dump_memory_to_json_files,
    memory_store_paths,
    seed_memory_from_json_files_cached,
)
from Agents.memory.store import store

DEFAULT_SOURCE = "evaluation/frozen_eval_sets/extraction/extraction_v5_0.jsonl"

# Role -> winning-faction label (matches determine_winner outputs).
_FACTION = {
    "wolf": "wolves",
    "serial_killer": "serial_killer",
    "villager": "villagers", "healer": "villagers",
    "investigator": "villagers", "vigilante": "villagers",
}


def load_cases(path: Path) -> list[dict]:
    if not path.exists():
        raise SystemExit(f"Source extraction set not found: {path}")
    cases = []
    for line in path.read_text().splitlines():
        if line.strip():
            rec = json.loads(line)
            cases.append(rec.get("extraction_case", rec))
    return cases


def namespace_count(kind: str) -> int:
    """Total items across every (role, phase) namespace of a kind."""
    from Agents.schemas.roles import ACTION_PHASES, VALID_ACTION_PHASES_BY_ROLE, roles
    total = 0
    for role in roles:
        for phase in VALID_ACTION_PHASES_BY_ROLE.get(role, ACTION_PHASES):
            ns, offset = (kind, role, phase), 0
            while True:
                page = store.search(ns, query=None, limit=100, offset=offset)
                if not page:
                    break
                total += len(page)
                offset += 100
    return total


def stamp_source_game_winner(store_dir: Path, winner_by_game: dict[str, str]) -> int:
    """Objective game_id -> winner join, written into each stored entry's metadata (soft-signal
    only, never a filter). Navigates the dumped JSON; role parsed from the namespace key."""
    stamped = 0
    obs_path, _ = memory_store_paths(store_dir)
    doc = json.loads(obs_path.read_text())
    for key, entries in doc.get("namespaces", {}).items():
        role = key.split("/")[1] if key.count("/") >= 2 else None
        faction = _FACTION.get(role)
        for entry in entries:
            val = entry.get("value", {})
            winner = winner_by_game.get(val.get("game_id"))
            if winner is None:
                continue
            val["source_game_winner"] = winner
            val["role_faction_won"] = (faction == winner) if faction else None
            stamped += 1
    obs_path.write_text(json.dumps(doc, indent=2))
    return stamped


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", default=DEFAULT_SOURCE)
    ap.add_argument("--output-store-dir", default="memory_stores/v5_0_nethorizon")
    ap.add_argument("--cache-prefix", action="store_true",
                    help="Vertex-cache each game's prefix (the role fan-out shares it)")
    ap.add_argument("--roles", nargs="+", default=["wolf", "serial_killer"],
                    help="roles to re-extract (default: the two arms' roles only — the other "
                         "roles' entries would never be retrieved by the wolf/SK arms)")
    ap.add_argument("--max-games", type=int, default=None)
    ap.add_argument("--seed-from", default=None,
                    help="seed the store from this existing nethorizon dir BEFORE extracting --roles "
                         "(to ADD roles to an existing store; --output-store-dir may be the same dir). "
                         "Role namespaces are independent, so existing roles are preserved untouched.")
    args = ap.parse_args()

    out_dir = Path(args.output_store_dir)
    if not args.seed_from and out_dir.exists() and any(out_dir.iterdir()):
        raise SystemExit(f"{out_dir} exists and is non-empty — refusing to overwrite. Remove it first.")

    if args.seed_from:
        sfrom = Path(args.seed_from)
        sobs, ssp = memory_store_paths(sfrom)
        print(f"Seeding store from {sfrom} (preserving its existing role namespaces)...")
        seed_memory_from_json_files_cached(observations_path=sobs, strategy_points_path=ssp,
                                           target_store=store, cache_dir=sfrom)

    cases = load_cases(Path(args.source))
    if args.max_games:
        cases = cases[: args.max_games]
    winner_by_game = {c.get("game_id"): c.get("game_outcome") for c in cases if c.get("game_id")}
    print(f"Re-extracting {len(cases)} games (net-horizon framing), roles={args.roles}...")

    for i, case in enumerate(cases, 1):
        gid = case.get("game_id") or f"nethorizon_{i}"
        inputs = extraction_inputs_from_frozen_case(case)
        prefix = build_role_extraction_prefix(inputs)
        result = extract_postgame_per_role(
            prefix, roles=tuple(args.roles), cache_prefix=args.cache_prefix
        )
        if result is None:
            print(f"  game {i}/{len(cases)} {gid[:8]} -> EXTRACTION FAILED (all roles)", flush=True)
            continue
        out = result.output
        obs_stats = run_downstream_observation_dedup(store, out.observations, gid)
        sp_stats = run_downstream_strategy_dedup(store, out.strategy_points, gid)
        print(f"  game {i}/{len(cases)} {gid[:8]} winner={case.get('game_outcome')} -> "
              f"{len(out.observations)} obs ({obs_stats.kept}k/{obs_stats.discarded}d) "
              f"{len(out.strategy_points)} sp ({sp_stats.kept}k/{sp_stats.discarded}d) "
              f"[{result.model_used}]", flush=True)

    obs_path, sp_path = memory_store_paths(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    counts = dump_memory_to_json_files(observations_path=obs_path, strategy_points_path=sp_path, target_store=store)
    stamped = stamp_source_game_winner(out_dir, winner_by_game)
    print(f"\nDumped to {out_dir}: {counts} | stamped source_game_winner on {stamped} obs entries")
    print(f"Store totals: observations={namespace_count('observations')} strategy_points={namespace_count('strategy_points')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
