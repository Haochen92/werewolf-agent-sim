"""Tell-dedup v0 — PROBE SCAFFOLDING (see experiment_log.md §3.6).

Collapses a mined tell corpus into canonical tells, previewing how the store consolidates
before any bigger sweep is paid for. Three stages, mirroring the house dedup architecture
in miniature:

1. exact-match collapse (free — the wording-convergence rows);
2. TF-IDF cosine prefilter over distinct wordings (structural only; production would use
   the store embedding model, this probe stays offline/$0);
3. flash-lite EXTENSIONAL-EQUIVALENCE judge (`get_llm_dedup`) on candidate pairs: two
   descriptions are the same tell iff a transcript reader would count the SAME moments as
   instances of both. Judged strictly — a sub-type with distinct mechanism stays separate,
   because the how-grain is where discrimination lives (log §3.6).

Scope rules from the design discussion: GLOBAL within channel (never partitioned by
exhibitor role — the lift denominator needs all-role tallies), channel is a hard partition
(a vote tell references cast votes by construction). Merges are index-level only: the
instance rows are never rewritten, so a wrong-grain merge is reversible (split trigger =
fat support + null lift).

  PYTHONPATH=. poetry run python evidence/extraction/tell_extraction/dedup_v0.py \
      --in outputs/mining_v4_flashlite_split.jsonl
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

import numpy as np
from pydantic import BaseModel, Field

from Agents.llm_factory import get_llm_dedup
from Agents.memory.store import embeddings as _embedding_model
from Agents.memory.vectors import embed_texts

PROBE_DIR = Path(__file__).resolve().parent.parent
# v0 used TF-IDF at 0.35: only 10 candidate pairs on 202 wordings — lexical cosine cannot
# see paraphrase at tell length (log §3.6). v0.1 uses the PRODUCTION store embedding model
# (same prefilter the SP/obs dedup runs on); threshold picked from the printed distribution.
PREFILTER_THRESHOLD = 0.80
MAX_JUDGED_PAIRS = 400

EVIL_ROLES = {"wolf", "serial_killer"}
CAST_EVIL_PRIOR = 3 / 9  # 2 wolves + 1 SK of 9 — the cast base-rate for the toy lift preview
SHRINK_K = 5


class SameTellVerdict(BaseModel):
    same: bool = Field(description="True only if the two descriptions denote the SAME tell.")
    reason: str = Field(description="One short sentence for the call.")


JUDGE_PROMPT = """You are deduplicating behavior patterns ("tells") mined from Werewolf game
transcripts. Two descriptions are THE SAME TELL only if a reader scanning a transcript would
count the SAME moments as instances of both — same behavior, same mechanism, same trigger.
Judge strictly: if one describes a narrower sub-type, a different tactic or mechanism, a
different trigger, or a different relation to the target, they are DIFFERENT tells. Phrasing
differences with identical meaning are the SAME tell.

A: {a}
B: {b}
"""


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip().lower().rstrip(".")


def load_corpus(path: Path) -> list[dict]:
    return [json.loads(l) for l in open(path)]


def judge_pairs(pairs: list[tuple[str, str]]) -> dict[tuple[str, str], SameTellVerdict]:
    llm = get_llm_dedup().with_structured_output(SameTellVerdict)
    out: dict[tuple[str, str], SameTellVerdict] = {}
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(llm.invoke, JUDGE_PROMPT.format(a=a, b=b)): (a, b) for a, b in pairs}
        for fut in as_completed(futures):
            key = futures[fut]
            try:
                out[key] = fut.result()
            except Exception as e:  # noqa: BLE001 — probe: skip, never crash
                print(f"  judge FAIL {key[0][:40]}...: {e}", flush=True)
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default=str(PROBE_DIR / "outputs" / "mining_v4_flashlite_split.jsonl"))
    ap.add_argument("--out", default=str(PROBE_DIR / "outputs" / "dedup_v0_clusters.json"))
    args = ap.parse_args()

    rows = load_corpus(Path(args.inp))
    print(f"{len(rows)} instance rows")

    # Stage 1 — exact-match collapse, per channel. Wordings keep first-seen order (freeze-old:
    # the earliest wording is the canonical candidate).
    by_channel: dict[str, dict[str, list[dict]]] = defaultdict(dict)
    for r in rows:
        by_channel[r["channel"]].setdefault(_norm(r["behavior"]), []).append(r)

    all_clusters: dict[str, list[list[str]]] = {}
    judged_total = same_total = 0
    for channel, wordings in by_channel.items():
        keys = list(wordings)  # first-seen order
        print(f"\n[{channel}] {sum(len(v) for v in wordings.values())} rows -> {len(keys)} distinct wordings")

        # Stage 2 — semantic prefilter with the PRODUCTION store embedding model.
        vecs = np.array(embed_texts(keys, _embedding_model))
        vecs = vecs / np.linalg.norm(vecs, axis=1, keepdims=True)
        sim = vecs @ vecs.T
        upper = [sim[i, j] for i in range(len(keys)) for j in range(i + 1, len(keys))]
        qs = np.quantile(upper, [0.5, 0.9, 0.99])
        print(f"  sim distribution: p50={qs[0]:.2f} p90={qs[1]:.2f} p99={qs[2]:.2f}")
        cand = [(keys[i], keys[j], sim[i, j])
                for i in range(len(keys)) for j in range(i + 1, len(keys))
                if sim[i, j] >= PREFILTER_THRESHOLD]
        cand.sort(key=lambda t: -t[2])
        if len(cand) > MAX_JUDGED_PAIRS:
            print(f"  prefilter: {len(cand)} pairs, judging top {MAX_JUDGED_PAIRS} (cap) — rest assumed different")
            cand = cand[:MAX_JUDGED_PAIRS]
        else:
            print(f"  prefilter: {len(cand)} candidate pairs >= {PREFILTER_THRESHOLD}")

        # Stage 3 — extensional-equivalence judge.
        verdicts = judge_pairs([(a, b) for a, b, _ in cand])
        judged_total += len(verdicts)

        # Union-find; canonical = earliest wording in each set.
        parent = {k: k for k in keys}

        def find(x: str) -> str:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        order = {k: i for i, k in enumerate(keys)}
        for (a, b), v in verdicts.items():
            if v.same:
                same_total += 1
                ra, rb = find(a), find(b)
                if ra != rb:
                    old, new = (ra, rb) if order[ra] <= order[rb] else (rb, ra)
                    parent[new] = old  # freeze-old: merge newer INTO older

        clusters: dict[str, list[str]] = defaultdict(list)
        for k in keys:
            clusters[find(k)].append(k)
        all_clusters[channel] = [[c] + [m for m in ms if m != c] for c, ms in clusters.items()]

        sizes = Counter(len(ms) for ms in clusters.values())
        n_rows = sum(len(v) for v in wordings.values())
        print(f"  {len(keys)} wordings -> {len(clusters)} canonical tells "
              f"(cluster sizes: {dict(sorted(sizes.items()))})")

        # Toy lift preview on the biggest clusters (IN-SAMPLE + 5 games — direction only, never a claim).
        def tally(members: list[str]) -> tuple[int, int]:
            inst = [r for m in members for r in wordings[m]]
            return sum(1 for r in inst if r["exhibitor_role"] in EVIL_ROLES), len(inst)

        big = sorted(clusters.values(), key=lambda ms: -sum(len(wordings[m]) for m in ms))[:5]
        print("  top clusters (evil/total exhibitors -> shrunk toy lift; IN-SAMPLE PREVIEW ONLY):")
        for ms in big:
            evil, tot = tally(ms)
            lift = (evil / tot - CAST_EVIL_PRIOR) * (tot / (tot + SHRINK_K))
            canon = min(ms, key=lambda m: order[m])
            print(f"    n={tot} evil={evil} lift={lift:+.2f} | {canon[:95]}")

    Path(args.out).write_text(json.dumps(all_clusters, indent=1))
    print(f"\njudged {judged_total} pairs, {same_total} merges -> {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
