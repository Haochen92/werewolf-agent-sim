"""Canonical discussion-tagger VALIDATION runner (graduated from three frozen evidence scripts).

The end-of-day discussion tagger (``evaluation.src.loop.discussion_tagger.tag_game``) is the
deceiver-side measurement instrument: an omniscient per-day flash-lite pass that grades each player's
discussion (framing / credibility / role-reveal → one holistic de-luck verdict) and night read. This
runner is its validation apparatus — one config-driven entry, three modes, each reproducing what used
to be a separate one-off script under ``evidence/v7_final/``:

  mode=accuracy — are the per-FIELD tags CORRECT? role_reveal is cross-tabbed against a deterministic
                  self-claim detector on the raw day_channel (the one ground-truthable axis) + the
                  in-game 'Role claims:' summary; framing/credibility distributions are read by faction
                  (deceivers should skew 'manipulative'). Graduated from ``tagger_accuracy.py``.
  mode=skill    — is the game-level deceiver signal REAL SKILL, not leak or verbosity? Per faction over
                  the games: partial r(disc_verdict, won | deluck) blinded (outcome withheld) and again
                  with verbosity partialled out. Graduated from ``v2_full/tagger_skill_retest.py``.
  mode=deleak   — a 2x2 (outcome in/out × all/speakers) ablation that SEPARATES the outcome-leak from
                  the mechanical silent-player effect, so each coupling number is diagnostic instead of
                  confounded. Graduated from ``v2_full/tagger_deleak_ablation.py``.

CURRENT VALIDATION STATE (honest, as of graduation 2026-07-02): on the v2 ON games the game-level
signal is partial r(disc_verdict, won | deluck, verbosity) ≈ +0.56 (wolf) / +0.60 (SK) at N=24,
single-epoch flash-lite, and the measured discussion-verdict outcome-leak is negligible (day-local
coupling moved +0.07 town / ~0 wolf-SK when the outcome was withheld). These are the numbers the tagger
keeps ``show_outcome=True`` on. A LARGER-N revalidation is a queued paid item — this runner is what
runs it. Full write-up + the frozen originals: ``evidence/evaluation/discussion_tagger/`` (hub) and
``evidence/v7_final/`` (originals, kept as the frozen record of the numbers above).

  poetry run eval-tagger --config evaluation/config/template/tagger_eval_example.json

COST: the runner TAGS (paid flash-lite) on a cache miss; pin the model via ``pro_model`` (default
flash-lite) and set ``tags_cache_dir`` so a re-run is free. Tests stub ``tag_game`` → $0.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any, Callable

from evaluation.src.core import manifest
from evaluation.src.core.config_schema import TaggerEvalConfig
from evaluation.src.core.settings import REPO_ROOT
from evaluation.src.core.stats import partial_correlation, pearson
from evaluation.src.data.sources.batch_records import read_records_file
from evaluation.src.loop.credit_backfill import (
    VERDICT_VALUE,
    TOWN_VOTE_ROLES,
    _decision_credit,
    _majority_vote,
)
from evaluation.src.loop.discussion_tagger import _provenance_slug, tag_game

# Verdict/credibility → numeric, shared across modes (the disc verdict scale is VERDICT_VALUE, reused
# rather than redefined so the tagger's outcome scale and the credit ledger's stay one thing).
TOWN = TOWN_VOTE_ROLES
CRED = {"low": 0, "medium": 1, "high": 2}
WINNER_FACTION = {"villagers": "town", "wolves": "wolf", "serial_killer": "serial_killer"}
FACTIONS = ("town", "wolf", "serial_killer")

ROLE_WORDS = r"investigator|healer|vigilante|villager|wolf|serial[\s_]?killer|seer|cop|doctor|detective|sheriff"
# explicit FIRST-PERSON role claim in a discussion message (the deterministic ground-truth axis)
CLAIM_PAT = re.compile(
    rf"\b(i\s*'?\s*m|i\s+am)\s+(the\s+|a\s+|your\s+)?({ROLE_WORDS})\b"
    rf"|\bmy\s+role\s+is\b"
    rf"|\bas\s+(the\s+|your\s+)?({ROLE_WORDS})\b"
    rf"|\bi\s+investigated\b|\bi\s+(healed|saved|protected)\b|\bi\s+(am|was)\s+the\s+one\s+who\b",
    re.IGNORECASE,
)


def _faction(role: str | None) -> str:
    return "town" if role in TOWN else (role or "?")


# ---------------------------------------------------------------------------
# Shared setup: record loading + provenance-slugged tag cache
# ---------------------------------------------------------------------------


def _expand(glob_spec: str) -> list[Path]:
    """Repo-root glob(s), whitespace-joined (like the credit loop's rolling window), sorted."""
    return sorted({p for pat in glob_spec.split() for p in REPO_ROOT.glob(pat)})


def _has_cases(record: dict) -> bool:
    path = record.get("eval_cases_path")
    return bool(record.get("roles")) and bool(path) and os.path.exists(path)


def load_records(cfg: TaggerEvalConfig) -> tuple[list[dict], list[Path]]:
    """Records + the source files that produced them (for the lineage manifest).

    accuracy — first ``max_games_per_source`` (default 4) of EACH matched file, no eval-case
      requirement (the tagger reads roles/day_channel/day_summaries straight off the record).
    skill    — every record that carries roles + an existing eval_cases sidecar (deluck needs it).
    deleak   — same eval-case filter, then stride-subsampled to ``n_games`` (default 6).
    """
    files = _expand(cfg.batch_glob or "")
    if cfg.mode == "accuracy":
        cap = cfg.max_games_per_source if cfg.max_games_per_source is not None else 4
        records: list[dict] = []
        for path in files:
            recs = [r for r in read_records_file(path, require_success=False) if r.get("roles")]
            records.extend(recs[:cap])
        return records, files
    records = [r for f in files for r in read_records_file(f, require_success=False) if _has_cases(r)]
    if cfg.mode == "deleak":
        n = cfg.n_games if cfg.n_games is not None else 6
        records.sort(key=lambda g: g.get("game_id", ""))
        step = max(1, len(records) // n) if n else 1
        records = records[::step][:n]
    return records, files


def _pack(mapping: dict) -> dict:
    return {f"{d}|{p}": v for (d, p), v in mapping.items()}


def _unpack(mapping: dict) -> dict:
    return {(int(k.split("|", 1)[0]), k.split("|", 1)[1]): v for k, v in mapping.items()}


def tagged(
    record: dict,
    cfg: TaggerEvalConfig,
    *,
    show_outcome: bool,
    speakers_only: bool,
) -> tuple[dict, dict]:
    """``tag_game`` with an optional provenance-slugged cache (keyed by game_id/slug/outcome/
    speakers/version). A played game's tags are immutable, so the cache lets a paid re-run over
    the same dumps cost nothing; ``tags_cache_dir=None`` tags fresh every time."""
    cache_dir = cfg.tags_cache_dir
    gid = record.get("game_id")
    path: Path | None = None
    if cache_dir and gid:
        slug = _provenance_slug(record)
        oc, sp = ("in" if show_outcome else "out"), ("spk" if speakers_only else "all")
        stem = f"{gid}.{slug}.{oc}.{sp}.{cfg.tagger_version}" if slug else f"{gid}.{oc}.{sp}.{cfg.tagger_version}"
        path = Path(cache_dir) / f"{stem}.json"
        if path.exists():
            data = json.load(open(path))
            return _unpack(data["disc"]), _unpack(data.get("night", {}))
    disc, night = tag_game(
        record, show_outcome=show_outcome, speakers_only=speakers_only, strict=cfg.strict
    )
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"disc": _pack(disc), "night": _pack(night)}))
    return disc, night


# ---------------------------------------------------------------------------
# mode=accuracy  (from evidence/v7_final/tagger_accuracy.py)
# ---------------------------------------------------------------------------


def _detector_claims(record: dict) -> dict:
    """(day, player) -> the message, for every EXPLICIT first-person role-claim in the raw day_channel."""
    claims: dict = {}
    for m in record.get("day_channel", []):
        msg = m.get("message") or ""
        if msg and CLAIM_PAT.search(msg):
            claims[(m.get("day"), m.get("player"))] = msg
    return claims


def _summary_claim_days(record: dict) -> set:
    """Days whose in-game summary 'Role claims:' prose line is non-empty (the persisted reference)."""
    days = set()
    for s in record.get("day_summaries", []):
        for line in (s.get("summary") or "").splitlines():
            ls = line.strip().lower()
            if ls.startswith("role claims:") and "none" not in ls.split(":", 1)[1]:
                days.add(s.get("day"))
    return days


def run_accuracy(records: list[dict], cfg: TaggerEvalConfig) -> dict[str, Any]:
    rr_counts: Counter = Counter()
    confirmed = missed_by_tagger = tagger_only = 0
    tagger_only_examples: list = []
    missed_examples: list = []
    summary_day_agree: Counter = Counter()
    framing: dict[str, Counter] = defaultdict(Counter)
    credibility: dict[str, Counter] = defaultdict(Counter)

    for g in records:
        roles = g.get("roles", {})
        det = _detector_claims(g)
        det_keys = set(det)
        summ_days = _summary_claim_days(g)
        disc, _ = tagged(g, cfg, show_outcome=True, speakers_only=True)

        tagger_reveal_days: set = set()
        for (day, player), t in disc.items():
            role = roles.get(player, "?")
            fac = _faction(role)
            rr = t["role_reveal"]
            rr_counts[rr] += 1
            framing[fac][t["framing"]] += 1
            credibility[fac][t["credibility"]] += 1
            if rr != "none":
                tagger_reveal_days.add(day)
            if rr == "own_role_claim":
                if (day, player) in det_keys:
                    confirmed += 1
                else:
                    tagger_only += 1
                    if len(tagger_only_examples) < 6:
                        msgs = [m["message"] for m in g["day_channel"]
                                if m.get("day") == day and m.get("player") == player and m.get("message")]
                        tagger_only_examples.append(
                            {"player": player, "role": role, "day": day, "msg": " | ".join(msgs)[:200]})
        flagged = {(d, p) for (d, p), t in disc.items() if t["role_reveal"] == "own_role_claim"}
        for k in det_keys - flagged:
            missed_by_tagger += 1
            if len(missed_examples) < 6:
                d, p = k
                missed_examples.append(
                    {"player": p, "role": roles.get(p, "?"), "day": d, "msg": det[k][:200]})
        for day in {s.get("day") for s in g.get("day_summaries", [])}:
            summary_day_agree[(day in tagger_reveal_days, day in summ_days)] += 1

    det_total = confirmed + missed_by_tagger
    return {
        "n_games": len(records),
        "role_reveal": {
            "distribution": dict(rr_counts),
            "detector_explicit_claims": det_total,
            "confirmed": confirmed,
            "missed_by_tagger": missed_by_tagger,
            "recall": (confirmed / det_total) if det_total else None,
            "tagger_only": tagger_only,
            "tagger_only_examples": tagger_only_examples,
            "missed_examples": missed_examples,
        },
        "summary_day_agreement": {f"tagger={k[0]}|summary={k[1]}": v for k, v in summary_day_agree.items()},
        "framing_by_faction": {f: dict(framing[f]) for f in FACTIONS},
        "credibility_by_faction": {f: dict(credibility[f]) for f in FACTIONS},
    }


# ---------------------------------------------------------------------------
# mode=skill  (from evidence/v7_final/v2_full/tagger_skill_retest.py)
# ---------------------------------------------------------------------------


def _deluck_by_faction(record: dict) -> dict[str, list[float]]:
    """Per-faction de-lucked decision-credit values over the game's eval cases (the SKILL proxy the
    tagger is measured against). Deterministic — ``_decision_credit`` is a pure roles lookup."""
    roles = record["roles"]
    blend = {dr.get("day"): _majority_vote(dr) for dr in record.get("day_resolutions", [])}
    dl: dict[str, list[float]] = defaultdict(list)
    path = record.get("eval_cases_path")
    if not path or not os.path.exists(path):
        return dl
    for line in open(path):
        if not line.strip():
            continue
        ec = (json.loads(line).get("output") or {}).get("eval_case") or {}
        v = _decision_credit(ec, roles, blend)
        if v is not None:
            dl[_faction(ec.get("player_role"))].append(VERDICT_VALUE[v])
    return dl


def _verbosity_by_faction(record: dict) -> dict[str, int]:
    roles = record["roles"]
    verb: dict[str, int] = defaultdict(int)
    for m in record.get("day_channel") or []:
        if not m.get("passed") and (m.get("message") or "").strip():
            verb[_faction(roles.get(m.get("player"), "?"))] += 1
    return verb


def run_skill(records: list[dict], cfg: TaggerEvalConfig) -> dict[str, Any]:
    cols: dict[str, dict[str, list[float]]] = {f: defaultdict(list) for f in FACTIONS}
    for g in records:
        roles = g["roles"]
        winf = WINNER_FACTION.get(g.get("winner"))
        disc_in, _ = tagged(g, cfg, show_outcome=True, speakers_only=False)    # A: outcome-IN
        disc_out, _ = tagged(g, cfg, show_outcome=False, speakers_only=False)  # B/C: blinded
        deluck = _deluck_by_faction(g)
        verb = _verbosity_by_faction(g)
        for f in FACTIONS:
            players = {p for p, r in roles.items() if _faction(r) == f}
            din = [VERDICT_VALUE[t["verdict"]] for (d, p), t in disc_in.items() if p in players]
            dout = [VERDICT_VALUE[t["verdict"]] for (d, p), t in disc_out.items() if p in players]
            if not din or not dout or not deluck[f]:
                continue
            cols[f]["din"].append(mean(din))
            cols[f]["dout"].append(mean(dout))
            cols[f]["deluck"].append(mean(deluck[f]))
            cols[f]["verb"].append(float(verb[f]))
            cols[f]["won"].append(1.0 if winf == f else 0.0)

    def _pr(x, y, controls):
        r, p, n = partial_correlation(x, y, controls)
        return {"r": r, "p": p, "n": n}

    factions: dict[str, Any] = {}
    for f in FACTIONS:
        c = cols[f]
        factions[f] = {
            "n": len(c["won"]),
            "A_in_given_deluck": _pr(c["din"], c["won"], [c["deluck"]]),
            "B_out_given_deluck": _pr(c["dout"], c["won"], [c["deluck"]]),
            "C_out_given_deluck_verbosity": _pr(c["dout"], c["won"], [c["deluck"], c["verb"]]),
            "columns": {k: list(v) for k, v in c.items()},
        }
    return {
        "n_games": len(records),
        "legend": {
            "A": "partial r(disc_in, won | deluck)  — sanity reproduction (outcome-IN tags)",
            "B": "partial r(disc_out[blinded], won | deluck)  — survives => not outcome-leak",
            "C": "partial r(disc_out[blinded], won | deluck, verbosity)  — survives => real skill",
        },
        "factions": factions,
    }


# ---------------------------------------------------------------------------
# mode=deleak  (from evidence/v7_final/v2_full/tagger_deleak_ablation.py)
# ---------------------------------------------------------------------------


def _favor(faction: str, lynch_role: str | None) -> int:
    """Day-lynch favorability for a faction (computed analysis-side, independent of what the tagger saw)."""
    if not lynch_role:
        return 0
    if faction == "town":
        return 1 if lynch_role in ("wolf", "serial_killer") else -1
    if faction == "wolf":
        return 1 if lynch_role != "wolf" else -1
    if faction == "serial_killer":
        return 1 if lynch_role != "serial_killer" else -1
    return 0


def _cell_rows(records: list[dict], cfg: TaggerEvalConfig, show_outcome: bool) -> dict[str, list]:
    """All disc tags for one outcome pass joined to (verdict, credibility, favorability, spoke?)."""
    rows: dict[str, list] = defaultdict(list)
    for g in records:
        roles = g["roles"]
        lynch_role = {dr.get("day"): dr.get("voted_player_role") for dr in g.get("day_resolutions", [])}
        spoke: dict = defaultdict(set)
        for m in g.get("day_channel") or []:
            if not m.get("passed") and (m.get("message") or "").strip():
                spoke[m.get("day")].add(m.get("player"))
        disc, _ = tagged(g, cfg, show_outcome=show_outcome, speakers_only=False)  # all players; filter here
        for (day, p), t in disc.items():
            f = _faction(roles.get(p, "?"))
            rows[f].append((VERDICT_VALUE[t["verdict"]], CRED.get(t.get("credibility"), 1),
                            _favor(f, lynch_role.get(day)), p in spoke[day]))
    return rows


def _coupling(rows: dict[str, list], speakers_only: bool) -> dict[str, dict]:
    """Pearson(disc_verdict | credibility, favorability) per faction, optionally speakers-restricted."""
    out: dict[str, dict] = {}
    for f, rs in rows.items():
        rs2 = [r for r in rs if r[3]] if speakers_only else rs
        n = len(rs2)
        rv, _ = pearson([r[0] for r in rs2], [r[2] for r in rs2])
        rc, _ = pearson([r[1] for r in rs2], [r[2] for r in rs2])
        out[f] = {"disc_verdict": rv, "credibility": rc, "n": n}
    return out


def run_deleak(records: list[dict], cfg: TaggerEvalConfig) -> dict[str, Any]:
    rows_in = _cell_rows(records, cfg, show_outcome=True)
    rows_out = _cell_rows(records, cfg, show_outcome=False)
    cells = {
        "in/all": _coupling(rows_in, False), "in/speakers": _coupling(rows_in, True),
        "out/all": _coupling(rows_out, False), "out/speakers": _coupling(rows_out, True),
    }

    def _get(cell: str, f: str) -> float | None:
        return cells[cell].get(f, {}).get("disc_verdict")

    contrasts = {}
    for f in FACTIONS:
        ia, ip, oa = _get("in/all", f), _get("in/speakers", f), _get("out/all", f)
        contrasts[f] = {
            "mechanical_silent_player_effect": (ia - ip) if _num(ia) and _num(ip) else None,
            "outcome_leak_all_players": (ia - oa) if _num(ia) and _num(oa) else None,
        }
    return {
        "n_games": len(records),
        "game_ids": [g.get("game_id") for g in records],
        "metric": "Pearson(disc_verdict|credibility, day-lynch-favorability)",
        "coupling": {f: {cell: cells[cell].get(f, {"disc_verdict": None, "credibility": None, "n": 0})
                         for cell in cells} for f in FACTIONS},
        "contrasts": contrasts,
    }


def _num(x: Any) -> bool:
    return isinstance(x, (int, float)) and not (isinstance(x, float) and math.isnan(x))


# ---------------------------------------------------------------------------
# entry
# ---------------------------------------------------------------------------

RUNNERS: dict[str, Callable[[list[dict], TaggerEvalConfig], dict]] = {
    "accuracy": run_accuracy,
    "skill": run_skill,
    "deleak": run_deleak,
}


def _clean(obj: Any) -> Any:
    """Recursively replace NaN with None so the artifact is valid JSON (partial_correlation/pearson
    return nan on degenerate/low-N inputs, which json would emit as the non-standard token `NaN`)."""
    if isinstance(obj, float):
        return None if math.isnan(obj) else obj
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    return obj


def output_path(requested: Path | None, mode: str) -> Path:
    if requested:
        return requested
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return REPO_ROOT / "evaluation" / "eval_results" / f"tagger_eval_{mode}_{ts}.json"


def read_config(path: Path) -> TaggerEvalConfig:
    return TaggerEvalConfig.model_validate_json(Path(path).read_text(encoding="utf-8"))


def run(cfg: TaggerEvalConfig) -> tuple[dict[str, Any], list[Path]]:
    """Load records, tag (cache-aware), aggregate for ``cfg.mode``. The single testable seam.
    Returns (result, source_files)."""
    if cfg.pro_model:  # cost guard: pin the paid slot before any tag_game call
        os.environ["GOOGLE_GENAI_PRO_MODEL"] = cfg.pro_model
        os.environ["GOOGLE_GENAI_PRO_BACKUP_MODEL"] = cfg.pro_model
    records, sources = load_records(cfg)
    if not records:
        raise SystemExit(f"tagger_eval: no records matched {cfg.batch_glob!r} for mode={cfg.mode}")
    result = RUNNERS[cfg.mode](records, cfg)
    result["mode"] = cfg.mode
    result["_sources"] = [str(p.relative_to(REPO_ROOT)) if p.is_absolute() else str(p) for p in sources]
    return result, sources


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate the end-of-day discussion tagger (accuracy | skill | deleak).")
    parser.add_argument("--config", type=Path, required=True)
    args = parser.parse_args()

    cfg = read_config(args.config)
    result, sources = run(cfg)
    out = output_path(cfg.output, cfg.mode)
    out.parent.mkdir(parents=True, exist_ok=True)
    manifest.embed(result, artifact=out, config=cfg, inputs=sources)
    out.write_text(json.dumps(_clean(result), indent=2) + "\n", encoding="utf-8")

    _print_summary(result)
    print(f"\nWrote {cfg.mode} results -> {out}", flush=True)


def _print_summary(result: dict) -> None:
    mode = result.get("mode")
    print(f"\n=== tagger_eval mode={mode} · {result.get('n_games')} games ===", flush=True)
    if mode == "accuracy":
        rr = result["role_reveal"]
        print(f"  role_reveal distribution: {rr['distribution']}")
        print(f"  detector explicit self-claims: {rr['detector_explicit_claims']} | "
              f"confirmed {rr['confirmed']} | missed {rr['missed_by_tagger']} | "
              f"recall {rr['recall']} | tagger-only {rr['tagger_only']}")
        for axis in ("framing_by_faction", "credibility_by_faction"):
            print(f"  {axis}:")
            for f in FACTIONS:
                print(f"    {f:14s} {result[axis][f]}")
    elif mode == "skill":
        print(f"  {'faction':14s} {'N':>3}   (A) in|dl   (B) OUT|dl   (C) OUT|dl,verb")
        for f in FACTIONS:
            fr = result["factions"][f]
            fmt = lambda d: (f"{d['r']:+.2f}" if _num(d.get('r')) else "  -  ")
            print(f"  {f:14s} {fr['n']:>3}   {fmt(fr['A_in_given_deluck']):>8}   "
                  f"{fmt(fr['B_out_given_deluck']):>9}   {fmt(fr['C_out_given_deluck_verbosity']):>9}")
    elif mode == "deleak":
        for f in FACTIONS:
            print(f"  === {f} ===")
            for cell, c in result["coupling"][f].items():
                fmt = lambda x: (f"{x:+.2f}" if _num(x) else "  -  ")
                print(f"    {cell:12s} disc={fmt(c['disc_verdict'])} cred={fmt(c['credibility'])} (N={c['n']})")
            con = result["contrasts"][f]
            print(f"    -> mechanical silent-player = "
                  f"{con['mechanical_silent_player_effect']}, outcome-leak = {con['outcome_leak_all_players']}")


if __name__ == "__main__":
    main()
