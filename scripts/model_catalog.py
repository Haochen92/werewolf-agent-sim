"""Read and edit the model catalogue: the menu, each model's settings, and its prices.

The catalogue is rows in the database (tables ``models`` and ``model_prices``,
``Agents/llm_factory/catalog.py``). A running server re-reads them every ten seconds, so a change
made here reaches the menu and new turns without a deploy or a restart. Every change is checked
before it is written: the factory must know the provider, levels and modes must be real ones, a
rescue must be in the catalogue, and a model goes on the menu only with a price in force.

    poetry run python scripts/model_catalog.py list
    poetry run python scripts/model_catalog.py show anthropic/claude-haiku-5-5
    poetry run python scripts/model_catalog.py set anthropic/claude-sonnet-5-5 --turn-thinking low
    poetry run python scripts/model_catalog.py price gemini-3.6-flash --since 2026-10-12 \\
        --input 0.75 --cached 0.075 --output 3.75 --source "Gemini API pricing page, promo to 2026-12-31"
    poetry run python scripts/model_catalog.py set gemini-3.6-flash --listed
    poetry run python scripts/model_catalog.py sync-langfuse

A price change is also written to Langfuse's model definitions, so traces are priced at the
catalogue's rates; ``sync-langfuse`` does it on its own (after editing the table directly).

A new model needs ``--name``, starts off the menu, and is listed with ``--listed`` once it has a
price. ``none`` clears a rescue; ``default`` clears a level or a mode.
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from dotenv import load_dotenv  # noqa: E402

from Agents.llm_factory.accessors import VALID_THINKING_LEVELS  # noqa: E402
from Agents.llm_factory.backends import OPENROUTER_PROVIDER, STRUCTURED_MODES  # noqa: E402
from Agents.llm_factory.catalog import _sync_dsn, billed_name  # noqa: E402

# The factory's prefixes (backends._build_chat_model); a bare id is a Gemini model.
PREFIXES = ("anthropic/", "openai/", "deepseek/", "openrouter/", "xai/", "nim/")
COLUMNS = ("model", "display_name", "listed", "menu_order", "house_funded", "rescue_model",
           "turn_thinking", "summary_thinking", "structured_mode", "notes")


def fail(message: str) -> None:
    raise SystemExit(f"refused: {message}")


def check_provider(model: str) -> None:
    if model.startswith(PREFIXES):
        if model.startswith("openrouter/") and not any(
                model.removeprefix("openrouter/").startswith(k) for k in OPENROUTER_PROVIDER):
            fail(f"{model}: OpenRouter is pinned per model family and has none for this one "
                 f"(backends.OPENROUTER_PROVIDER); that needs code")
        return
    if not model.startswith("gemini-"):
        fail(f"{model}: the factory has no branch for this provider ({', '.join(PREFIXES)} or a "
             f"bare gemini- id); a new provider needs code once")


def price_in_force(conn, model: str) -> tuple | None:
    return conn.execute(
        "SELECT since, input, cached, output, peak FROM model_prices "
        "WHERE model = %s AND since <= %s ORDER BY since DESC LIMIT 1",
        (billed_name(model), date.today())).fetchone()


def cmd_list(conn, args) -> None:
    rows = conn.execute("SELECT " + ", ".join(COLUMNS) + " FROM models "
                        "ORDER BY menu_order, model").fetchall()
    print(f"{'#':>3}  {'model':34} {'menu':5} {'pays':6} {'turn':8} {'summary':8} {'mode':12} "
          f"{'rescue':28} price now (in / cached / out per 1M)")
    for r in rows:
        row = dict(zip(COLUMNS, r))
        p = price_in_force(conn, row["model"])
        price = f"${p[1]:g} / ${p[2]:g} / ${p[3]:g}{' peak' if p[4] else ''}" if p else "NO PRICE"
        print(f"{row['menu_order']:>3}  {row['model']:34} {'yes' if row['listed'] else '-':5} "
              f"{'house' if row['house_funded'] else 'key':6} {row['turn_thinking'] or '-':8} "
              f"{row['summary_thinking'] or '-':8} {row['structured_mode'] or '-':12} "
              f"{row['rescue_model'] or '-':28} {price}")


def cmd_show(conn, args) -> None:
    r = conn.execute("SELECT " + ", ".join(COLUMNS) + " FROM models WHERE model = %s",
                     (args.model,)).fetchone()
    if r is None:
        fail(f"{args.model} is not in the catalogue")
    for k, v in zip(COLUMNS, r):
        print(f"{k:17} {v}")
    print(f"prices for {billed_name(args.model)}:")
    for since, i, c, o, peak, source in conn.execute(
            "SELECT since, input, cached, output, peak, source FROM model_prices WHERE model = %s "
            "ORDER BY since", (billed_name(args.model),)):
        print(f"  from {since}: ${i:g} in, ${c:g} cached, ${o:g} out{' (peak x2)' if peak else ''}"
              f"  [{source}]")


def cmd_set(conn, args) -> None:
    check_provider(args.model)
    existing = conn.execute("SELECT " + ", ".join(COLUMNS) + " FROM models WHERE model = %s",
                            (args.model,)).fetchone()
    row = dict(zip(COLUMNS, existing)) if existing else None
    if row is None:
        if not args.name:
            fail(f"{args.model} is new: give it a --name")
        row = {"model": args.model, "display_name": args.name, "listed": False, "menu_order": 100,
               "house_funded": False, "rescue_model": None, "turn_thinking": None,
               "summary_thinking": None, "structured_mode": None, "notes": ""}
    changes = {
        "display_name": args.name, "listed": args.listed, "menu_order": args.order,
        "house_funded": args.house, "notes": args.notes,
        "rescue_model": None if args.rescue == "none" else args.rescue,
        "turn_thinking": None if args.turn_thinking == "default" else args.turn_thinking,
        "summary_thinking": None if args.summary_thinking == "default" else args.summary_thinking,
        "structured_mode": None if args.mode == "default" else args.mode,
    }
    given = {"rescue_model": args.rescue, "turn_thinking": args.turn_thinking,
             "summary_thinking": args.summary_thinking, "structured_mode": args.mode}
    for key, value in changes.items():
        if value is not None or given.get(key) in ("none", "default"):
            row[key] = value
    for key in ("turn_thinking", "summary_thinking"):
        if row[key] is not None and row[key] not in VALID_THINKING_LEVELS:
            fail(f"{key} must be one of {sorted(VALID_THINKING_LEVELS)} or default")
    if row["structured_mode"] is not None:
        if row["structured_mode"] not in STRUCTURED_MODES:
            fail(f"mode must be one of {STRUCTURED_MODES} or default")
        if not args.model.startswith(PREFIXES):
            fail("a Gemini model has its own structured output and takes no mode")
    if row["rescue_model"] is not None:
        if row["rescue_model"] == args.model:
            fail("a model cannot be its own rescue")
        if conn.execute("SELECT 1 FROM models WHERE model = %s", (row["rescue_model"],)).fetchone() is None:
            fail(f"rescue {row['rescue_model']} is not in the catalogue")
    if row["listed"] and price_in_force(conn, args.model) is None:
        fail(f"{args.model} has no price in force for {billed_name(args.model)}; add one with "
             f"`price` first, or its games would show no cost")
    conn.execute(
        "INSERT INTO models (" + ", ".join(COLUMNS) + ", updated_at) VALUES ("
        + ", ".join(["%s"] * len(COLUMNS)) + ", now()) ON CONFLICT (model) DO UPDATE SET "
        + ", ".join(f"{c} = EXCLUDED.{c}" for c in COLUMNS[1:]) + ", updated_at = now()",
        tuple(row[c] for c in COLUMNS))
    print(f"{'updated' if existing else 'added'} {args.model}")


def cmd_price(conn, args) -> None:
    name = billed_name(args.model)
    if min(args.input, args.cached, args.output) < 0:
        fail("prices cannot be negative")
    if not args.source:
        fail("say where the price comes from: --source")
    conn.execute(
        "INSERT INTO model_prices (model, since, input, cached, output, peak, source) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (model, since) DO UPDATE SET "
        "input = EXCLUDED.input, cached = EXCLUDED.cached, output = EXCLUDED.output, "
        "peak = EXCLUDED.peak, source = EXCLUDED.source",
        (name, args.since, args.input, args.cached, args.output, args.peak, args.source))
    print(f"{name}: ${args.input:g} in, ${args.cached:g} cached, ${args.output:g} out from {args.since}"
          " (every game on or after that date is now priced at it)")


def cmd_sync_langfuse(conn, args) -> None:
    """Write the catalogue's prices into Langfuse's model definitions (Agents/observability/
    langfuse_prices.py). Runs after every price change; run it by hand after editing the table directly."""
    from Agents.llm_factory.catalog import load_from_database
    from Agents.observability.langfuse_prices import sync
    from Agents.tracing import langfuse

    counts = sync(langfuse.api, load_from_database(args.dsn).prices)
    print(f"Langfuse: {counts['definitions']} prices, {counts['created']} written, "
          f"{counts['removed']} stale removed, {counts['unchanged']} already right.")


def main() -> None:
    load_dotenv(REPO_ROOT / ".env")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dsn", default=os.getenv("WW_POSTGRES_DSN", ""))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="every model, its settings and its price now")
    show = sub.add_parser("show", help="one model's row, notes and every price")
    show.add_argument("model")
    s = sub.add_parser("set", help="add a model or change its row")
    s.add_argument("model")
    s.add_argument("--name", help="what the menu shows (required for a new model)")
    s.add_argument("--listed", dest="listed", action="store_true", default=None, help="put it on the menu")
    s.add_argument("--unlisted", dest="listed", action="store_false", help="take it off the menu")
    s.add_argument("--house", dest="house", action="store_true", default=None, help="the server pays")
    s.add_argument("--player-key", dest="house", action="store_false", help="players bring a key")
    s.add_argument("--rescue", help="the fallback model id, or none")
    s.add_argument("--turn-thinking", help="minimal / low / medium / high, or default")
    s.add_argument("--summary-thinking", help="minimal / low / medium / high, or default")
    s.add_argument("--mode", help=f"{' / '.join(STRUCTURED_MODES)}, or default")
    s.add_argument("--order", type=int, help="menu position, ascending")
    s.add_argument("--notes", help="why the row is what it is (replaces the notes)")
    p = sub.add_parser("price", help="add a price from a date (or correct that date's price)")
    p.add_argument("model", help="the factory id or the billed name")
    p.add_argument("--since", required=True, type=date.fromisoformat)
    p.add_argument("--input", required=True, type=float, help="USD per 1M input tokens")
    p.add_argument("--cached", required=True, type=float, help="USD per 1M cached input tokens")
    p.add_argument("--output", required=True, type=float, help="USD per 1M output tokens, reasoning included")
    p.add_argument("--peak", action="store_true", help="DeepSeek-style peak hours bill double")
    p.add_argument("--source", default="", help="where the price comes from")
    sub.add_parser("sync-langfuse", help="write the catalogue's prices into Langfuse's model definitions")
    args = parser.parse_args()
    if not args.dsn:
        raise SystemExit("WW_POSTGRES_DSN is not set")

    import psycopg

    with psycopg.connect(_sync_dsn(args.dsn)) as conn:
        {"list": cmd_list, "show": cmd_show, "set": cmd_set, "price": cmd_price,
         "sync-langfuse": cmd_sync_langfuse}[args.command](conn, args)
        if args.command in ("set", "price"):
            conn.commit()
            print("A running server picks this up within about ten seconds.")
        if args.command == "price":
            # Langfuse prices traces from its own model definitions; keep them the catalogue's.
            try:
                cmd_sync_langfuse(conn, args)
            except Exception as e:  # noqa: BLE001 — the price is saved; the sync can be rerun
                print(f"Langfuse not updated ({e}); run: scripts/model_catalog.py sync-langfuse")


if __name__ == "__main__":
    main()
