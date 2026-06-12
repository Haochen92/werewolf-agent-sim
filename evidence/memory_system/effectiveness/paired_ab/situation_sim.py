"""Validity diagnostic (NON-BLOCKING) for the v5_0_nethorizon build.

The net-horizon change should touch ONLY the outcome field; retrieval is driven by the SITUATION
embedding. v5_0 and nethorizon are both fresh stochastic extractions (not a diff), so the question is
whether nethorizon situations land in the SAME embedding region as v5_0's — as close cross-store as
v5_0 entries are to each OTHER (the within-store density is the natural noise floor). If cross-store
nearest-neighbour similarity ~ within-store density, the outcome reframing introduced no systematic
situation drift, so a paired arm isolates framing. Reported, not gated (see nethorizon_design.md)."""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
import sys
sys.path.insert(0, str(REPO))

from Agents.memory.persistence import memory_store_paths
from Agents.memory.store import embeddings

NS = ["observations/wolf/day_discussion", "observations/wolf/day_vote",
      "observations/wolf/night_action", "observations/serial_killer/day_discussion",
      "observations/serial_killer/day_vote", "observations/serial_killer/night_action"]


def situations(store_dir):
    obs_p, _ = memory_store_paths(store_dir)
    doc = json.loads(Path(obs_p).read_text())["namespaces"]
    return {k: [e["value"]["situation"] for e in doc.get(k, [])] for k in NS}


def cosine_matrix(a, b):
    import math
    def norm(v):
        m = math.sqrt(sum(x * x for x in v)) or 1.0
        return [x / m for x in v]
    a, b = [norm(v) for v in a], [norm(v) for v in b]
    return [[sum(x * y for x, y in zip(u, w)) for w in b] for u in a]


def main():
    v5, nh = situations(REPO / "memory_stores/v5_0"), situations(REPO / "memory_stores/v5_0_nethorizon")
    # Embed everything once.
    all_text = [t for k in NS for t in v5[k]] + [t for k in NS for t in nh[k]]
    vecs = embeddings.embed_documents(all_text)
    idx, emb = 0, {}
    for tag, src in (("v5", v5), ("nh", nh)):
        for k in NS:
            emb[(tag, k)] = vecs[idx:idx + len(src[k])]
            idx += len(src[k])

    print(f"{'namespace':42} {'v5':>3} {'nh':>3} {'cross-NN':>9} {'within-v5':>9}")
    cross_all, within_all = [], []
    for k in NS:
        ve, ne = emb[("v5", k)], emb[("nh", k)]
        if not ve or not ne:
            print(f"{k:42} {len(ve):>3} {len(ne):>3}   (empty)")
            continue
        # cross: each nethorizon situation's best match in v5_0 (same namespace)
        cross = [max(row) for row in cosine_matrix(ne, ve)]
        # within-v5 floor: each v5 situation's best match among OTHER v5 situations
        m = cosine_matrix(ve, ve)
        within = [max(v for j, v in enumerate(row) if j != i) for i, row in enumerate(m)] if len(ve) > 1 else []
        cross_all += cross
        within_all += within
        wn = sum(within) / len(within) if within else float("nan")
        print(f"{k:42} {len(ve):>3} {len(ne):>3} {sum(cross)/len(cross):>9.3f} {wn:>9.3f}")
    cm = sum(cross_all) / len(cross_all)
    wm = sum(within_all) / len(within_all)
    print(f"\nOVERALL wolf+SK: cross-store NN mean = {cm:.3f} | within-v5 density floor = {wm:.3f}")
    print(f"Interpretation: cross ({cm:.3f}) {'>=' if cm >= wm else '<'} floor ({wm:.3f}) -> "
          f"{'no systematic situation drift (nethorizon as close to v5_0 as v5_0 is internally dense)' if cm >= wm - 0.02 else 'POSSIBLE drift — inspect before any framing-specific claim'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
