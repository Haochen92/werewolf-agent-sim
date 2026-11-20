"""The embedding prefilter's ceiling, drawn: the same 232 cross-game dedup cases on two embedders.

Record: evidence/dedup/embedding_prefilter/experiment_log.md (the calibration and the "topic, not
stance" finding; the 2026-10-14 addendum). For every case the prefilter's own signal is recomputed on
the current embedder exactly as the live code computes it (observations: the concatenated
situation + approach + outcome; strategy points: the action; the maximum cosine over the case's
candidates), and set beside the value the May calibration cached on gemini-embedding-001. The output
is the data the figure is drawn from, stamped with the embedder and the commit, so the figure can be
redrawn without embedding again; ``--render`` draws it.

  poetry run python evaluation/experiments/prefilter_similarity_exhibit.py            # embed + JSON
  poetry run python evaluation/experiments/prefilter_similarity_exhibit.py --render   # + the PNG
  poetry run python evaluation/experiments/prefilter_similarity_exhibit.py --render --from-json  # redraw only

Cost: ~1,400 short texts on the current embedder, cents.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CASES = ROOT / "evaluation/frozen_eval_sets/auto_dedup_v1_cross_game.jsonl"
DATA = ROOT / "evidence/dedup/embedding_prefilter/data"
LABELS = DATA / "cross_game_golden_labels.json"
OLD_CACHE = DATA / "cross_game_embedding_cache.json"
OUT_JSON = DATA / "cross_game_sims_by_embedder.json"
OUT_PNG = DATA / "cross_game_sims_by_embedder.png"

OLD_MODEL = "gemini-embedding-001"
ANNOTATED_CASE = 155  # the "topic, not stance" pair in the log: opposite advice, 0.913 alike
BATCH = 64


def _obs_text(d: dict) -> str:
    return f"{d.get('situation', '')} {d.get('approach', '')} {d.get('outcome', '')}"


def _case_texts(case: dict) -> tuple[str, list[str]]:
    if case["item_type"] == "observation":
        return _obs_text(case["new_entry"]), [_obs_text(c) for c in case["candidates"]]
    return case["new_entry"]["action"], [c["action"] for c in case["candidates"]]


def _load_cases() -> list[dict]:
    return [json.loads(line) for line in CASES.read_text().splitlines() if line.strip()]


def _labels() -> dict[int, str]:
    return {row["case_index"]: row["golden_label"] for row in json.loads(LABELS.read_text())["labels"]}


def _old_sims() -> dict[int, float]:
    out = {}
    for row in json.loads(OLD_CACHE.read_text()):
        sim = row["max_content_sim"] if row["item_type"] == "observation" else row["max_action_sim"]
        out[row["case_index"]] = sim
    return out


def _thresholds(model: str) -> dict[str, dict[str, float]]:
    from Agents.llm_factory.embeddings import SIMILARITY_THRESHOLDS

    # The May calibration was made on -001; its numbers are the ones the gemini-embedding-2 row still
    # carries (never remapped, see the log's 2026-10-14 addendum), so that row stands in for -001.
    row = SIMILARITY_THRESHOLDS["gemini-embedding-2" if model == OLD_MODEL else model]
    return {
        "observation": {"keep": row["obs_content_keep"], "discard": row["obs_content_discard"]},
        "strategy_point": {"keep": row["sp_action_keep"], "discard": row["sp_action_discard"]},
    }


def embed_current(cases: list[dict]) -> tuple[dict[int, float], str, int]:
    """The prefilter's signal for every case on the configured embedder."""
    from Agents.llm_factory.embeddings import DEFAULT_EMBEDDING_DIMS, DEFAULT_EMBEDDING_MODEL
    from Agents.memory.store import embeddings
    from Agents.memory.vectors import cosine_similarity, embed_texts

    texts: list[str] = []
    index: dict[str, int] = {}
    for case in cases:
        new, cands = _case_texts(case)
        for t in [new, *cands]:
            if t not in index:
                index[t] = len(texts)
                texts.append(t)
    vectors = []
    for start in range(0, len(texts), BATCH):
        vectors.extend(embed_texts(texts[start:start + BATCH], embeddings))
        print(f"embedded {min(start + BATCH, len(texts))}/{len(texts)}", flush=True)

    sims: dict[int, float] = {}
    for case in cases:
        new, cands = _case_texts(case)
        v = vectors[index[new]]
        sims[case["case_index"]] = max(
            (cosine_similarity(v, vectors[index[c]]) for c in cands), default=0.0
        )
    return sims, DEFAULT_EMBEDDING_MODEL, DEFAULT_EMBEDDING_DIMS


def summarise(points: list[dict], model_key: str, thresholds: dict) -> dict:
    """What the prefilter would decide at the thresholds in force, and where it would be wrong."""
    out = {}
    for kind in ("observation", "strategy_point"):
        keep, discard = thresholds[kind]["keep"], thresholds[kind]["discard"]
        rows = [p for p in points if p["item_type"] == kind and p[model_key] is not None]
        auto_keep = [p for p in rows if p[model_key] < keep]
        auto_discard = [p for p in rows if p[model_key] >= discard]
        out[kind] = {
            "n": len(rows),
            "keep_below": keep,
            "discard_at": discard,
            "auto_keep": len(auto_keep),
            "auto_discard": len(auto_discard),
            "auto_rate": round((len(auto_keep) + len(auto_discard)) / len(rows), 3) if rows else None,
            "duplicates_auto_kept": sum(1 for p in auto_keep if p["label"] == "D"),
            "keepers_auto_discarded": sum(1 for p in auto_discard if p["label"] == "K"),
        }
    return out


def build(render: bool, from_json: bool) -> dict:
    if from_json:
        record = json.loads(OUT_JSON.read_text())
    else:
        cases = _load_cases()
        labels, old = _labels(), _old_sims()
        new, model, dims = embed_current(cases)
        points = [
            {
                "case_index": c["case_index"],
                "item_type": c["item_type"],
                "label": labels[c["case_index"]],
                "sim_old": old.get(c["case_index"]),
                "sim_new": round(new[c["case_index"]], 4),
                "candidates": len(c["candidates"]),
            }
            for c in cases
        ]
        commit = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT,
                                capture_output=True, text=True).stdout.strip()
        record = {
            "what": "max prefilter similarity per cross-game dedup case, on the May embedder (cached) "
                    "and the current one (recomputed); labels from the gemini-3.5-flash labeler",
            "cases": str(CASES.relative_to(ROOT)),
            "labels": str(LABELS.relative_to(ROOT)),
            "signal": {"observation": "cosine of situation+approach+outcome, max over candidates",
                       "strategy_point": "cosine of the action, max over candidates"},
            "embedders": {
                "old": {"model": OLD_MODEL, "dims": 1536, "source": str(OLD_CACHE.relative_to(ROOT)),
                        "thresholds": _thresholds(OLD_MODEL)},
                "new": {"model": model, "dims": dims, "thresholds": _thresholds(model)},
            },
            "annotated_case": ANNOTATED_CASE,
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "git_commit": commit,
            "points": points,
        }
        record["summary"] = {
            "old": summarise(points, "sim_old", record["embedders"]["old"]["thresholds"]),
            "new": summarise(points, "sim_new", record["embedders"]["new"]["thresholds"]),
        }
        OUT_JSON.write_text(json.dumps(record, indent=1))
        print(f"wrote {OUT_JSON.relative_to(ROOT)}")
    if render:
        draw(record)
    return record


# --- the figure ------------------------------------------------------------------------------

KEEP_COLOR, DISCARD_COLOR = "#2a78d6", "#eb6834"   # categorical slots 1 and 2, validated
SURFACE, INK, INK_2, GRID = "#fcfcfb", "#1f1f1d", "#5c5b55", "#e4e3de"


def draw(record: dict) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    rng = np.random.default_rng(7)
    kinds = [("observation", "Observations: situation + approach + outcome"),
             ("strategy_point", "Strategy points: the action")]
    embedders = [("sim_old", "old"), ("sim_new", "new")]
    fig, axes = plt.subplots(2, 1, figsize=(10, 6.8), facecolor=SURFACE, sharex=True)
    fig.subplots_adjust(left=0.2, right=0.98, top=0.84, bottom=0.09, hspace=0.42)

    for ax, (kind, title) in zip(axes, kinds):
        ax.set_facecolor(SURFACE)
        for y, (key, which) in enumerate(embedders):
            model = record["embedders"][which]["model"]
            th = record["embedders"][which]["thresholds"][kind]
            rows = [p for p in record["points"] if p["item_type"] == kind and p[key] is not None]
            for label, color in (("K", KEEP_COLOR), ("D", DISCARD_COLOR)):
                xs = [p[key] for p in rows if p["label"] == label]
                ys = y + rng.uniform(-0.18, 0.18, len(xs))
                ax.scatter(xs, ys, s=26, c=color, alpha=0.75, edgecolors=SURFACE, linewidths=0.8,
                           label={"K": "labelled keep (distinct)", "D": "labelled discard (duplicate)"}[label]
                           if (kind == "observation" and y == 0) else None, zorder=3)
            ax.vlines([th["keep"], th["discard"]], y - 0.3, y + 0.3, colors=INK_2, linewidths=1.2,
                      linestyles=(0, (3, 2)), zorder=2)
            # keep label under the strip, discard label above it: the two lines sit close on Gemini
            ax.text(th["keep"], y - 0.34, f"keep < {th['keep']:.3g}", ha="right", va="top",
                    fontsize=8, color=INK_2)
            ax.text(th["discard"], y + 0.33, f"discard ≥ {th['discard']:.3g}", ha="left", va="bottom",
                    fontsize=8, color=INK_2)
            if kind == "strategy_point":
                p155 = next(p for p in rows if p["case_index"] == record["annotated_case"])
                # the cached row is the lower strip: its note goes below; the recomputed row's above
                dy = -0.62 if which == "old" else 0.5
                ax.annotate("case 155: opposite advice, labelled keep",
                            (p155[key], y), xytext=(p155[key] - 0.2, y + dy), fontsize=8, color=INK,
                            arrowprops=dict(arrowstyle="-", color=INK_2, lw=0.8))
        ax.set_yticks([0, 1])
        ax.set_yticklabels([f"{record['embedders']['old']['model']}\n(May 2026, cached)",
                            f"{record['embedders']['new']['model']}\n(recomputed)"], fontsize=9, color=INK)
        ax.set_ylim(-0.8, 1.7)
        ax.set_title(title, loc="left", fontsize=10.5, color=INK, pad=14)
        ax.grid(axis="x", color=GRID, linewidth=0.8, zorder=0)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.spines["bottom"].set_color(GRID)
        ax.tick_params(colors=INK_2, labelsize=8.5)
    axes[-1].set_xlabel("max cosine similarity to the closest stored candidate", color=INK_2, fontsize=9)
    axes[-1].set_xlim(0.6, 1.0)
    axes[0].legend(loc="lower left", frameon=False, fontsize=9, ncol=2, handletextpad=0.3,
                   columnspacing=1.6, bbox_to_anchor=(0.0, -0.02))
    fig.suptitle("Embedding similarity separates near-identical text, not stance",
                 x=0.2, ha="left", fontsize=12, color=INK, y=0.985)
    fig.text(0.2, 0.945, "The same 232 cross-game dedup cases on two embedders. Between the dashed lines "
             "the prefilter defers to the model;\nkeeps and discards interleave there on both. Thresholds "
             "are the ones in force for each model.", fontsize=8.5, color=INK_2, va="top", linespacing=1.4)
    fig.savefig(OUT_PNG, dpi=160, facecolor=SURFACE)
    print(f"wrote {OUT_PNG.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--render", action="store_true", help="also draw the PNG")
    parser.add_argument("--from-json", action="store_true", help="redraw from the saved JSON, no embedding")
    args = parser.parse_args()
    record = build(render=args.render, from_json=args.from_json)
    for which in ("old", "new"):
        print(which, record["embedders"][which]["model"], json.dumps(record["summary"][which]))


if __name__ == "__main__":
    main()
