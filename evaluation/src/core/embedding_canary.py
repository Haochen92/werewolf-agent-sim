"""Embedding-alias drift canary — turn a silent, undetectable failure into a crash.

The vector store keys on an embedding MODEL ALIAS (``gemini-embedding-001``). If the
model behind that alias silently changes, every stored vector and every live retrieval
query shifts in a way nothing else notices: retrieval still returns *something*, scores
still look plausible, and a whole run's memory signal is quietly corrupted. There is no
other guard for this surface.

The canary is a fixed set of text pairs with their pairwise cosine similarities PINNED
once (``--pin``) and stored next to this module. ``check_embedding_canary`` re-embeds the
same texts and asserts every pair's similarity is within ``epsilon`` of its pin — a drift
in the alias moves the geometry and trips the assert loudly at batch start, before a run
spends anything on corrupted retrieval.

Bootstrap (one command, needs embedding creds — cheap, NOT generation spend):
    poetry run python -m evaluation.src.core.embedding_canary --pin
Verify:
    poetry run python -m evaluation.src.core.embedding_canary --check
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from Agents.llm_factory.embeddings import (
    DEFAULT_EMBEDDING_DIMS,
    DEFAULT_EMBEDDING_MODEL,
    create_embeddings,
)
from Agents.memory.vectors import cosine_similarity, embed_texts

# Fixed probe pairs — a spread from near-paraphrase (high sim) through topically related
# to unrelated (low sim), so drift that flattens OR sharpens the space shows up. The texts
# are game-domain so they exercise the same vocabulary the store embeds. NEVER edit these
# after pinning without re-pinning; the pins below are only valid for this exact list.
CANARY_PAIRS: list[tuple[str, str]] = [
    ("The investigator publicly claimed their role on day two.",
     "On the second day, the seer revealed they were the investigator."),
    ("A wolf voted to lynch a townsperson to build trust.",
     "The werewolf cast a vote against a villager to appear helpful."),
    ("The healer protected the same player two nights running.",
     "The doctor guarded one target on consecutive nights."),
    ("The serial killer struck alone at night, immune to the wolves.",
     "The lone night-killer, unaffected by the pack, made a solo kill."),
    ("With four players left, one mislynch hands the game to evil.",
     "At the final four, a single wrong vote loses town the game."),
    ("The vigilante held their last bullet for the endgame.",
     "The vigilante saved a shot, banking the bullet for later."),
    ("Everyone piled their votes onto the quiet player.",
     "The consensus swung hard toward the silent suspect."),
    ("The investigator publicly claimed their role on day two.",
     "The vigilante held their last bullet for the endgame."),
    ("A wolf voted to lynch a townsperson to build trust.",
     "The healer protected the same player two nights running."),
    ("With four players left, one mislynch hands the game to evil.",
     "Everyone piled their votes onto the quiet player."),
    ("The serial killer struck alone at night, immune to the wolves.",
     "The investigator publicly claimed their role on day two."),
    ("The doctor guarded one target on consecutive nights.",
     "The consensus swung hard toward the silent suspect."),
]

PINS_PATH = Path(__file__).with_name("embedding_canary_pins.json")
DEFAULT_EPSILON = 0.02


def _embedder():
    """The SAME embedder the store indexes with (model + dims), so the canary tracks the
    exact geometry live retrieval uses."""
    return create_embeddings(
        DEFAULT_EMBEDDING_MODEL, output_dimensionality=DEFAULT_EMBEDDING_DIMS
    )


def _pair_similarities() -> list[float]:
    """Cosine similarity for each canary pair, embedding every distinct text once."""
    texts: list[str] = []
    index: dict[str, int] = {}
    for a, b in CANARY_PAIRS:
        for t in (a, b):
            if t not in index:
                index[t] = len(texts)
                texts.append(t)
    vectors = embed_texts(texts, _embedder())
    return [
        cosine_similarity(vectors[index[a]], vectors[index[b]]) for a, b in CANARY_PAIRS
    ]


def pin(path: Path = PINS_PATH, epsilon: float = DEFAULT_EPSILON) -> dict:
    """Compute + persist the pinned similarities. Run once (or when intentionally
    changing the embedding model/dims — that is the only legitimate reason to re-pin)."""
    sims = _pair_similarities()
    payload = {
        "model": DEFAULT_EMBEDDING_MODEL,
        "dims": DEFAULT_EMBEDDING_DIMS,
        "epsilon": epsilon,
        "pairs": [
            {"a": a, "b": b, "sim": round(sim, 6)}
            for (a, b), sim in zip(CANARY_PAIRS, sims)
        ],
    }
    path.write_text(json.dumps(payload, indent=2))
    return payload


class EmbeddingCanaryDrift(RuntimeError):
    """Raised when a re-embedded canary pair drifts beyond epsilon from its pin."""


def check_embedding_canary(
    path: Path = PINS_PATH, raise_on_missing: bool = False
) -> bool:
    """Re-embed the canary pairs and assert each similarity is within the pinned epsilon.
    Returns True on pass. Raises EmbeddingCanaryDrift on drift. A missing pin file is a
    setup gap, not drift: by default returns False with printed instructions (so a batch
    is not blocked by an un-bootstrapped canary); pass raise_on_missing=True to hard-fail."""
    if not path.exists():
        msg = (
            f"Embedding canary not pinned ({path.name} missing). Bootstrap once with:\n"
            "  poetry run python -m evaluation.src.core.embedding_canary --pin"
        )
        if raise_on_missing:
            raise FileNotFoundError(msg)
        print(f"WARNING: {msg}", flush=True)
        return False

    pinned = json.loads(path.read_text())
    epsilon = float(pinned.get("epsilon", DEFAULT_EPSILON))
    expected = [p["sim"] for p in pinned["pairs"]]
    if len(expected) != len(CANARY_PAIRS):
        raise EmbeddingCanaryDrift(
            f"Canary pin count {len(expected)} != {len(CANARY_PAIRS)} probe pairs — "
            "the pair list changed without re-pinning; re-run --pin."
        )
    actual = _pair_similarities()
    drifts = [
        (i, exp, act)
        for i, (exp, act) in enumerate(zip(expected, actual))
        if abs(exp - act) > epsilon
    ]
    if drifts:
        detail = "; ".join(
            f"pair[{i}] pinned={exp:.4f} now={act:.4f} (Δ={abs(exp - act):.4f})"
            for i, exp, act in drifts
        )
        raise EmbeddingCanaryDrift(
            f"Embedding-alias DRIFT: {len(drifts)}/{len(expected)} canary pairs moved "
            f">epsilon={epsilon} for model={pinned.get('model')} dims={pinned.get('dims')}. "
            f"The store's embedding geometry changed under the alias — retrieval this run "
            f"would be corrupted. {detail}. If the model change is intentional, rebuild the "
            f"stores and re-pin (--pin)."
        )
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Embedding-alias drift canary.")
    group = ap.add_mutually_exclusive_group(required=True)
    group.add_argument("--pin", action="store_true", help="compute + write the pins")
    group.add_argument("--check", action="store_true", help="assert no drift vs the pins")
    args = ap.parse_args()
    if args.pin:
        payload = pin()
        print(f"Pinned {len(payload['pairs'])} canary pairs to {PINS_PATH}")
        for p in payload["pairs"]:
            print(f"  sim={p['sim']:.4f}  {p['a'][:40]!r} :: {p['b'][:40]!r}")
    else:
        check_embedding_canary(raise_on_missing=True)
        print("Embedding canary OK: no drift.")


if __name__ == "__main__":
    main()
