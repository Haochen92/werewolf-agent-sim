"""Tag the stored wolf night lessons with the pack's move each is about (owner, 2026-10-28).

Credit grades a lesson followed in the wolves' chat by its ``pack_move`` (kill / conceal / block;
``Agents/memory/consolidation/grading.py`` ``pack_move_grade``). Synthesis writes the tag on every new
wolf night lesson; the lessons already in the consolidation DB were written before it existed, so this
writes it onto them. The tags were read off each lesson's advice by hand (Claude, owner-reviewed); a
lesson that names two moves takes the one its advice turns on. Untagged lessons fall back to the kill.

Dry run by default (prints what would change); ``--apply`` writes ``memory_records`` (the system of
record). The served read index needs nothing: players never see the tag.

  poetry run python scripts/backfill_pack_move.py [--apply]
"""

from __future__ import annotations

import argparse
import os

import psycopg
from dotenv import load_dotenv
from psycopg.types.json import Jsonb

PACK_MOVES = {
    # chanteuse
    "0a1f2a12-c70b-44c4-8f04-931ae9ce45d4": "block",
    "2157c7e2-65e7-44fc-b496-ca7eaefb30d6": "block",
    "3b940b5e-1ba1-425b-ae57-39281de373c4": "block",
    "3d79beac-1105-41d8-88b3-d84a596160fc": "block",
    "3da7fa03-c26a-4152-87d2-172883311cdc": "block",
    "3e430e41-6d30-4a0e-8124-0bda4bac2731": "block",    # also names the kill
    "417a28d3-9a6f-4b5d-a555-b9f02232842a": "block",
    "5207eed6-78f4-4af2-8b06-7f1d592c3483": "block",
    "5869a883-49d2-4d3f-b60e-a84810f2562b": "block",
    "61ac3f53-2ab2-45e0-a3a6-a4f23b3b8a10": "block",
    "64986c2f-3dab-4270-9835-5c6f33114989": "block",
    "766c2669-48e0-473f-93a2-c4fd32e6e8d8": "kill",     # kill and block the same vigilante
    "861e8e6e-6eb8-42d5-adff-592dd2da2d8e": "block",    # also names the conceal
    "883a2e04-bed1-42d6-b657-4566476128c0": "block",
    "ac2dc81c-bdc9-4925-970d-d7f644b8f56a": "block",
    "ad54351b-e263-41b7-94cd-42228b5eb242": "block",
    "b30ce08c-6f78-4c00-8dd3-f127f061bb83": "block",
    "bb79a810-208c-4ed0-8130-355a09e8c17d": "kill",     # where the kill goes, apart from the block
    "bce88156-3b1c-4c3c-97ef-34cdfdf0c0dc": "block",
    "be54e611-a2d3-43d0-9ed4-04618cd0529c": "block",
    "c07df8b2-4199-4e8c-b3eb-6800b9ceedd3": "block",
    "c6ab98c9-06f7-42e3-909a-eed888440d18": "block",
    "c85d0b8e-242d-451b-b61e-55a7fd823a70": "block",
    "eaebc268-7a7e-4003-afe8-1cef1d95abe7": "conceal",  # agree the conceal with the illusionist
    "efa62812-b242-4b25-8c35-17b4f4c56b7a": "block",    # also names the kill
    # illusionist
    "1454b1c3-b43d-49a0-b792-ee6e6f6147e3": "kill",     # kill the healer, and conceal it
    "1cd12b76-bb40-44b2-84df-94595f8e9747": "conceal",
    "39c82553-63b7-41bf-82bb-97821d9560f1": "conceal",
    "3dc1b9d3-e19b-4c7c-9c0b-a0328286a8c0": "conceal",
    "78e2d08b-2305-442c-96e1-3ca7830ac76a": "kill",
    "84a22cb7-0cec-417c-ad6b-bb1ccc3e19f9": "kill",
    "adcf1721-64ad-4d5f-af0d-c665f0aa7ee8": "kill",     # also names the conceal
    "b177828b-9c3c-482e-a3df-f39d1af55173": "conceal",
    "b7d2b028-003e-4b92-b36a-b60323b81d25": "conceal",
    "c26b43ba-c744-4169-ba39-5d180944a021": "conceal",
    "c8cd609f-c4be-406e-8609-0a290312e706": "conceal",
    "ca5545ab-4325-4224-a4d6-ea9be3c7a40e": "kill",
    "d88e0de8-6a11-43e0-9e1c-200a9315a280": "kill",
}

WOLF_NIGHT_CELLS = ("strategy_points/chanteuse/night_action", "strategy_points/illusionist/night_action")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true", help="write the tags (default: dry run)")
    args = ap.parse_args()
    load_dotenv(".env")
    with psycopg.connect(os.environ["WW_POSTGRES_DSN"]) as conn:
        rows = conn.execute("SELECT ns, key, record FROM memory_records WHERE kind = 'strategy_points' "
                            "AND ns = ANY(%s)", (list(WOLF_NIGHT_CELLS),)).fetchall()
        untagged = [key for _ns, key, _r in rows if key not in PACK_MOVES]
        changes = []
        for ns, key, record in rows:
            move = PACK_MOVES.get(key)
            if move is None or record["value"].get("pack_move") == move:
                continue
            record["value"]["pack_move"] = move
            record["value"].setdefault("dimensions", {})["pack_move"] = move
            changes.append((ns, key, record))
        print(f"{len(rows)} wolf night lessons; {len(changes)} to tag; {len(untagged)} with no tag here: {untagged}")
        for ns, key, record in changes:
            print(f"  {ns.split('/')[1]:<12} {key[:8]} -> {record['value']['pack_move']}")
        if not args.apply:
            print("dry run: nothing written (--apply to write)")
            return
        with conn.transaction():
            for _ns, key, record in changes:
                conn.execute("UPDATE memory_records SET record = %s WHERE kind = 'strategy_points' AND key = %s",
                             (Jsonb(record), key))
        print(f"wrote {len(changes)}")


if __name__ == "__main__":
    main()
