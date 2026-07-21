"""The graduated memory-consolidation pipeline (go-live 2026-07-21).

The production form of the v7 compounding loop's memory machinery: fixed-rule credit
(``credit_rules``/``credit`` — deadlock-negative town abstains, no rule switches), the conversion
channel (``conversion`` — always applied), the consolidation store-ops (``store_ops``), Postgres
persistence (``db``), and the batch tick entry (``tick``). The knobbed eval-era ancestors stay in
``evaluation/src/loop/`` for frozen-run reproduction; ``decision_scoring`` and ``obs_fold`` moved
here wholesale (eval imports them back through shims).
"""

from Agents.memory.consolidation.config import TickConfig  # noqa: F401
from Agents.memory.consolidation.conversion import conversion_apply, conversion_lift  # noqa: F401
from Agents.memory.consolidation.credit import (  # noqa: F401
    base_for,
    credit_apply,
    credit_distribution,
    sp_lift,
)
from Agents.memory.consolidation.credit_rules import build_ledger, compute_base_rates  # noqa: F401
from Agents.memory.consolidation.store_ops import consolidate, prune_and_evict  # noqa: F401

# db / tick are imported explicitly (Agents.memory.consolidation.tick) — they pull psycopg, and
# this package init must stay light: the eval shims (decision_scoring, obs_fold) route through it.
