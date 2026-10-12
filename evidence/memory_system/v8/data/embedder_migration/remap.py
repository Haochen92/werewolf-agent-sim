"""Percentile remap of the cosine thresholds, gemini-embedding-2 -> qwen3-embedding-8b, over
within-cell pairs of each text population (v8_seed_synth_sonnet2)."""
import json, sys
from collections import defaultdict
import numpy as np
D = sys.argv[1]
rows = json.load(open(f"{D}/rows.json"))
G = np.load(f"{D}/gemini.npz")["v"]; Q = np.load(f"{D}/qwen.npz")["v"]
def norm(m): return m / np.linalg.norm(m, axis=1, keepdims=True)
G, Q = norm(G), norm(Q)
def pairs(pops):
    by = defaultdict(list)
    for i, (pop, ns, _k, _t) in enumerate(rows):
        if pop in pops:
            by[ns.split("/", 1)[1]].append(i)   # cell = role/phase, obs and SPs together
    g, q = [], []
    for idx in by.values():
        idx = np.array(idx)
        if len(idx) < 2: continue
        sg, sq = G[idx] @ G[idx].T, Q[idx] @ Q[idx].T
        iu = np.triu_indices(len(idx), 1)
        g.append(sg[iu]); q.append(sq[iu])
    return np.concatenate(g), np.concatenate(q)
def remap(name, t, pops):
    g, q = pairs(pops)
    pct = (g < t).mean()
    tq = float(np.quantile(q, pct))
    rho = np.corrcoef(np.argsort(np.argsort(g)), np.argsort(np.argsort(q)))[0, 1]
    print(f"{name:22} gemini {t:.3f} = p{pct*100:5.1f} of {len(g)} pairs -> qwen {tq:.3f}   (rank corr {rho:.2f}; gemini median {np.median(g):.3f}, qwen median {np.median(q):.3f})")
SIT = {"obs_situation", "sp_situation"}
remap("dedup_candidate", 0.55, SIT)
remap("batch_cluster", 0.70, {"obs_situation"})
remap("synth_cluster", 0.65, {"obs_situation"})
remap("retrieval_dedup_gate", 0.87, SIT)
remap("obs_content_keep", 0.935, {"obs_content"})
remap("obs_content_discard", 0.96, {"obs_content"})
remap("sp_action_keep", 0.81, {"sp_action"})
remap("sp_action_discard", 0.93, {"sp_action"})
