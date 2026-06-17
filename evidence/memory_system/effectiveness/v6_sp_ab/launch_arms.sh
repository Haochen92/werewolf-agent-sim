#!/usr/bin/env bash
# v6 SP A/B — 5 arms, N=30, raw retrieval, same-epoch (concurrent), held-out fresh game_ids.
#
# Each arm is its own run_batch process so the five advance in lockstep (one game per index
# at a time across all arms = same-epoch interleave) and pair via the shared --game-ids-file
# (run_index i -> game_ids[i-1], identical role draws across arms). All seed READ-ONLY from
# the UNDEDUPED v6_1 store with --no-memory-dump (no extraction write-back mid-experiment).
#
# Retrieval pinned RAW (rerank_disabled + filter_disabled, the run_batch defaults): the live
# reranker is an LLM pass with no trained weights (no v5 model to be stale), and the prior
# paired A/B showed rerank~=raw, so ranking is held constant and out of the way.
#
# Deceptive arm = the SERIAL KILLER, not the wolf: the registry threat-brief fix (commit bbc7c5b)
# changed wolf behavior, so wolf memory mined under the old prompt is stale. The SK was always
# self-aware, so its v6_1 memory stays valid. (Wolf ablation is a later, separate run off the new
# baseline games.)
#
# Arms:
#   baseline   all_disabled         (no memory)
#   town-obs   town_only            observations_only
#   sk-obs     serial_killer_only   observations_only
#   sk-sp      serial_killer_only   strategy_points_only
#   sk-both    serial_killer_only   both
set -euo pipefail
cd "$(dirname "$0")/../../../.."   # repo root

IDS=evidence/memory_system/effectiveness/v6_sp_ab/game_ids.json
STORE=memory_stores/v6_1
COMMON=(--game-ids-file "$IDS" --seed-store-dir "$STORE" --no-memory-dump)

run() {  # name configs retrieval-types
  local name=$1 configs=$2 rt=$3
  poetry run python scripts/run_batch.py \
    --configs $configs --retrieval-types "$rt" "${COMMON[@]}" \
    --session-prefix "v6ab_${name}" \
    --output "batch_results/v6ab_${name}.jsonl" \
    > "batch_results/v6ab_${name}.log" 2>&1 &
  echo "launched $name (pid $!)"
}

run baseline  all_disabled        both
run townobs   town_only           observations_only
run skobs     serial_killer_only  observations_only
run sksp      serial_killer_only  strategy_points_only
run skboth    serial_killer_only  both

echo "all 5 arms launched; waiting..."
wait
echo "all arms complete"
