"""The reads of the 40-game store (2026-10-13): its points screened for rule errors and duplicates, and
the gate's lookups replayed against it read for fit.

Record: evidence/memory_system/v8/experiment_log.md. Writes the readers' inputs to
``data/reextract/``: ``rules.md`` (the whole role pool's rules block, as synthesis saw it),
``points/part_N.md`` (every point, grouped by cell, for a rule-and-duplicate screen) and
``fit/part_N.md`` (the replay's unread lessons by lookup, from
``data/gate/stage_filter_40games/to_read.md``).

  poetry run python evaluation/experiments/v8_reextract_reads.py
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from Agents.prompts.compose import pool_rules_block

MAIN = Path(__file__).resolve().parents[2]
STORE = MAIN / "memory_stores/v8_reextract_synth"
GATE = MAIN / "evidence/memory_system/v8/data/gate"
OUT = MAIN / "evidence/memory_system/v8/data/reextract"
PARTS = 4


def _deal(blocks: list[tuple[int, str]], parts: int) -> list[list[str]]:
    """Blocks dealt into ``parts`` of about equal size (by their weight), keeping each block whole."""
    out: list[list[str]] = [[] for _ in range(parts)]
    load = [0] * parts
    for weight, text in sorted(blocks, key=lambda b: -b[0]):
        i = load.index(min(load))
        out[i].append(text)
        load[i] += weight
    return out


def main() -> None:
    (OUT / "points").mkdir(parents=True, exist_ok=True)
    (OUT / "fit").mkdir(parents=True, exist_ok=True)
    (OUT / "rules.md").write_text(pool_rules_block() + "\n")

    namespaces = json.loads((STORE / "strategy_points.json").read_text())["namespaces"]
    cells = []
    for ns, items in sorted(namespaces.items()):
        lines = [f"## Cell {ns.split('/', 1)[1]} ({len(items)} points)", ""]
        for it in items:
            p = it["value"]
            lines += [f"- key {it['key']}", f"  *When:* {p['situation']}", f"  *Do:* {p['action']}"]
        cells.append((len(items), "\n".join(lines) + "\n"))
    for i, part in enumerate(_deal(cells, PARTS), 1):
        (OUT / "points" / f"part_{i}.md").write_text("\n".join(part))

    text = (GATE / "stage_filter_40games" / "to_read.md").read_text()
    lookups = [b for b in re.split(r"(?m)^(?=## Lookup )", text) if b.strip()]
    for i, part in enumerate(_deal([(b.count("\n- key"), b) for b in lookups], PARTS), 1):
        (OUT / "fit" / f"part_{i}.md").write_text("".join(part))
    print(f"{sum(n for n, _ in cells)} points in {len(cells)} cells, {len(lookups)} lookups -> {OUT}")


if __name__ == "__main__":
    main()
