"""Batch-consolidation prep — PROBE SCAFFOLDING (see experiment_log.md; follows §3.8).

Local step only: loads the ledger-sim store snapshot, embeds each canonical with the
production store embedder, and writes per-channel input files for the Claude-side
clustering pass — each tell with its support, status, and rank-based top-k embedding
neighbours (absolute thresholds are dead on the compressed scale; §3.6).

  PYTHONPATH=. poetry run python evidence/extraction/tell_extraction/consolidation_prep.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import numpy as np

from Agents.memory.store import embeddings as _embedding_model
from Agents.memory.vectors import embed_texts

PROBE_DIR = Path(__file__).resolve().parent.parent
TOPK = 8

snap = json.load(open(PROBE_DIR / "outputs" / "ledger_sim_store.json"))
for ch in ("vote", "discussion"):
    tells = [t for t in snap if t["channel"] == ch]
    vecs = np.array(embed_texts([t["canonical"] for t in tells], _embedding_model))
    vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
    sims = vecs @ vecs.T
    np.fill_diagonal(sims, -1)
    out = []
    for i, t in enumerate(tells):
        top = np.argsort(-sims[i])[:TOPK]
        out.append({
            "tid": t["tid"], "support": t["support"], "status": t["status"],
            "canonical": t["canonical"],
            "neighbors": [tells[j]["tid"] for j in top],
        })
    path = PROBE_DIR / "outputs" / f"consolidation_input_{ch}.json"
    path.write_text(json.dumps(out, indent=1))
    print(f"{ch}: {len(out)} tells -> {path.name}")
