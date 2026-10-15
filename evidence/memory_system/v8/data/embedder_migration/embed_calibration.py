"""Calibration vectors for the Gemini -> Qwen3-Embedding-8B threshold remap.

Texts (from memory_stores/v8_seed_synth_sonnet2): observation situations, observation content
(situation + approach + outcome, as the dedup prefilter builds it), strategy-point situations and
actions. Gemini situation vectors come from the store's indexed cache (document vectors, 1536);
Gemini content/action vectors and every Qwen vector are embedded here. Output: one .npz per model.
"""
import json, os, pickle, sys, time
from pathlib import Path
import numpy as np
from dotenv import load_dotenv; load_dotenv(".env")

OUT = Path(sys.argv[1]); STORE = Path("memory_stores/v8_seed_synth_sonnet2")
obs = json.loads((STORE / "observations.json").read_text())["namespaces"]
sps = json.loads((STORE / "strategy_points.json").read_text())["namespaces"]
rows = []  # (population, namespace, key, text)
for ns, recs in obs.items():
    for r in recs:
        v = r["value"]
        rows.append(("obs_situation", ns, r["key"], v.get("situation", "")))
        rows.append(("obs_content", ns, r["key"], f"{v.get('situation','')} {v.get('approach','')} {v.get('outcome','')}"))
for ns, recs in sps.items():
    for r in recs:
        v = r["value"]
        rows.append(("sp_situation", ns, r["key"], v.get("situation", "")))
        rows.append(("sp_action", ns, r["key"], v.get("action", "")))
(OUT / "rows.json").write_text(json.dumps(rows))
print(len(rows), "texts", flush=True)

which = sys.argv[2]
if which == "qwen":
    from openai import OpenAI
    c = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ["OPENROUTER_API_KEY"])
    vecs = []
    for i in range(0, len(rows), 64):
        batch = [t for _p, _n, _k, t in rows[i:i + 64]]
        for attempt in range(5):
            try:
                r = c.embeddings.create(model="qwen/qwen3-embedding-8b", input=batch, dimensions=1536,
                                        extra_body={"provider": {"order": ["Nebius", "DeepInfra"], "allow_fallbacks": False}})
                break
            except Exception as e:  # noqa: BLE001
                print("retry", attempt, e, flush=True); time.sleep(5 * (attempt + 1))
        vecs += [d.embedding for d in r.data]
        print(i, flush=True)
    np.savez(OUT / "qwen.npz", v=np.array(vecs, dtype=np.float32))
else:
    cache = pickle.load(open(STORE / "indexed_cache.pkl", "rb"))
    cached = {(tuple(ns), k): p for ns, items in cache["vectors"].items() for k, p in items.items()}
    from Agents.llm_factory import create_embeddings, DEFAULT_EMBEDDING_MODEL, DEFAULT_EMBEDDING_DIMS
    emb = create_embeddings(DEFAULT_EMBEDDING_MODEL, output_dimensionality=DEFAULT_EMBEDDING_DIMS)
    vecs = []
    for n, (pop, ns, key, text) in enumerate(rows):
        hit = cached.get((tuple(ns.split("/")), key))
        if pop.endswith("situation") and hit is not None and "situation" in hit:
            vecs.append(hit["situation"])
        else:
            vecs.append(emb.embed_documents([text])[0])
        if n % 50 == 0: print(n, flush=True)
    np.savez(OUT / "gemini.npz", v=np.array(vecs, dtype=np.float32))
print("done", flush=True)
