"""Shared loading + split for the metrics-audit Workstream-1 rescue/discovery runners.

The three runners (`proxy_rescue`, `accusation_metrics`, `claim_conversion`) all validate on the
same N=180 v6ab set (the 3-faction epoch on which sk_lynched +0.455 and the wolf-night null were
measured) and use the same pre-registered 50/50 split. Kept in one place so the split is identical
across ideas and can't silently drift. Deterministic; recompute-only; ZERO LLM.

The 180 games are 30 role-seeds x 6 memory-arms — `game_id` is pinned across arms — so the split is
on `game_id` (SHA1 parity): arm-siblings of a seed stay on the same side, no near-duplicate leaks
across the discover/confirm halves.
"""

from __future__ import annotations

import glob
import hashlib
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
V6AB_GLOB = "batch_results/v6ab_*.jsonl"

TOWN_ROLES = {"villager", "healer", "investigator", "vigilante"}
THREAT_ROLES = {"wolf", "serial_killer"}


def load_v6ab() -> list[dict]:
    """All status==success v6ab games (N=180)."""
    games: list[dict] = []
    for f in sorted(glob.glob(str(REPO_ROOT / V6AB_GLOB))):
        for line in Path(f).read_text().splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("status") == "success":
                games.append(rec)
    return games


def split_half(game_id: str) -> int:
    """0 = discover half, 1 = confirm half. Deterministic SHA1 parity on the seed's game_id."""
    return int(hashlib.sha1((game_id or "").encode()).hexdigest(), 16) % 2


def won(record: dict, faction: str) -> int:
    return int(record.get("winner") == faction)
