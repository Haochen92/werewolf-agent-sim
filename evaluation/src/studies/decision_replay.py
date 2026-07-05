"""Decision-replay study CLI — the concluded memory-framing campaign that runs on
the standing screen engine (``evaluation.src.replay.decision_screen``).

The reusable engine (case/game-index loading, off-policy vote/night regeneration,
day-stratified cohort selection, mechanical outcome-blind scoring, paired McNemar,
the two lenses, and every ``run_*`` screen) now lives in ``replay/decision_screen``.
This module is the thin CLI over it plus the RETIRED lexical-echo proxy — kept here,
deprecated, only so ``run_echo_judge_validation`` can reproduce its own invalidation
(rho=0.14 vs the adherence judge, p=0.38); do NOT resurrect it in new screens.

Run: ``poetry run python evaluation/src/studies/decision_replay.py \
        --batch batch_results/ab_nh_town.jsonl``
"""

from __future__ import annotations

import argparse
import json
import re
import warnings
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from Agents.schemas import DayVote
from Agents.schemas.evaluation import EvalCase
from evaluation.src.loop.decision_scoring import (
    REPLAYABLE_TOWN_ROLES,
    allow_abstain_for,
)
from evaluation.src.loop.memory_adherence import (
    DEFAULT_ADHERENCE_JUDGE_MODEL,
    judge_decision_adherence,
)
from evaluation.src.replay.turn_action import application_case_for_judge
from evaluation.src.replay.decision_screen import (
    DayVoteOutputMemoryLinked,
    DayVoteOutputReasonFirst,
    _mem_text,
    _replay_vote,
    _select_diverse,
    run_adherence_scan,
    run_adherence_smoke,
    run_applicability_probe,
    run_causal,
    run_coherence_test,
    run_discussion_causal,
    run_framing_rewrite_screen,
    run_night_causal,
    run_observational,
    run_reorder_adoption,
    run_reorder_test,
)


# Judge-FREE engagement read (reuses the paired_ab echo logic): how much of the
# agent's post-retrieval reasoning is drawn from the words of the memory it was
# given. Every prior "did it engage the memory" number came from the adherence
# judge (which reads STATED reasoning and may agree with the agent); this is the
# first measure that needs no LLM to score.
_ECHO_STOP = set(
    """the a an and or but if then else of to in on at by for with from as is are was were be been
    being this that these those it its their they them he she his her you your we our i my me will would can
    could should may might must do does did not no yes so very more most much many few both all any each
    other some such than too then once here there when where which who whom what how why into out up down off
    over under again further about against between through during before after above below their them having
    have has had your yours ourselves a's able about above according""".split()
)


def _echo_toks(s: str | None) -> set[str]:
    if not s:
        return set()
    return {w for w in re.findall(r"[a-z]{4,}", s.lower()) if w not in _ECHO_STOP}


def _echo(reasoning: str | None, mem_text: str) -> float | None:
    """DEPRECATED — the lexical echo proxy is RETIRED as an engagement measure.
    Fraction of the reasoning's distinctive (>=4-char, non-stopword) tokens that also
    appear in the memory text; None if the reasoning has no scorable tokens. Validated
    against the adherence judge at Spearman rho=0.14 (p=0.38) — it does NOT track whether
    the memory was applied, so it must not be read as an engagement signal. Kept only so
    ``run_echo_judge_validation`` can reproduce the invalidation; do not use it in new
    screens (use the adherence judge)."""
    s, m = _echo_toks(reasoning), _echo_toks(mem_text)
    return (len(s & m) / len(s)) if s else None


def run_echo_consideration(
    batch_path: Path,
    n: int = 150,
    min_day: int = 3,
    roles: frozenset[str] = REPLAYABLE_TOWN_ROLES,
    max_workers: int = 6,
) -> dict[str, Any]:
    """Judge-FREE engagement screen. Replay the STORED arm under each of the three
    schemas {vote-first, reason-first, memory-linked} and measure how much of the
    regenerated reasoning is drawn from the retrieved memory (echo), ABOVE a
    shuffled-memory floor (the same reasoning scored against a foreign decision's
    memory). The floor is taken per-schema and per-decision, so it cancels verbosity:
    a longer memory-flavored note overlaps ANY memory, and only echo-above-floor
    isolates genuine drawing-on. Paired by decision -> does the memory-LINKED wording
    make the reasoning engage the memory more than plain vote-first, with no judge?

    DEPRECATED / RETIRED: the echo proxy this screen is built on does not track memory
    application (rho=0.14 vs the adherence judge, p=0.38 — see run_echo_judge_validation
    and evidence/.../decision_replay/experiment_log.md). Its numbers are not a valid
    engagement signal; use the adherence judge instead. Retained for reproducibility."""
    warnings.warn(
        "run_echo_consideration uses the retired lexical echo proxy (rho=0.14 vs the "
        "adherence judge); its engagement numbers are invalid — use the adherence judge.",
        DeprecationWarning,
        stacklevel=2,
    )
    cases = _select_diverse(batch_path, n, min_day, 999, roles, phase="day_vote")
    schemas = {
        "vote_first": None,
        "reason_first": DayVoteOutputReasonFirst,
        "memory_linked": DayVoteOutputMemoryLinked,
    }

    def one(case: EvalCase, game: dict[str, Any]):
        allow = allow_abstain_for(case.day, game["day_resolutions"])
        reasonings = {}
        for sname, sch in schemas.items():
            _, updated = _replay_vote(
                case, case.retrieved_observations, allow, schema_override=sch
            )
            reasonings[sname] = updated
        return {"mem": _mem_text(case), "reasonings": reasonings}

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        results = [f.result() for f in [ex.submit(one, c, g) for c, g in cases]]

    # Per decision i, per schema s: own-memory echo and the foreign-memory floor
    # (same reasoning vs decision (i+k)'s memory). per_dec[s][i] = own - floor keeps
    # it paired so the schema-vs-schema deltas align on the same decisions.
    mems = [r["mem"] for r in results]
    k = len(results) // 3 or 1
    own_by: dict[str, list[float]] = {s: [] for s in schemas}
    floor_by: dict[str, list[float]] = {s: [] for s in schemas}
    per_dec: dict[str, dict[int, float]] = {s: {} for s in schemas}
    for i, r in enumerate(results):
        foreign = mems[(i + k) % len(mems)] if mems else ""
        for s in schemas:
            own = _echo(r["reasonings"][s], r["mem"])
            flo = _echo(r["reasonings"][s], foreign)
            if own is not None:
                own_by[s].append(own)
            if flo is not None:
                floor_by[s].append(flo)
            if own is not None and flo is not None:
                per_dec[s][i] = own - flo

    avg = lambda xs: round(sum(xs) / len(xs), 4) if xs else None  # noqa: E731
    by_schema = {
        s: {
            "n": len(per_dec[s]),
            "echo": avg(own_by[s]),
            "shuffle_floor": avg(floor_by[s]),
            "echo_above_floor": avg(list(per_dec[s].values())),
        }
        for s in schemas
    }
    vf = per_dec["vote_first"]
    vs_vote_first = {}
    for s in schemas:
        if s == "vote_first":
            continue
        paired = [per_dec[s][i] - vf[i] for i in per_dec[s] if i in vf]
        vs_vote_first[s] = {
            "n_paired": len(paired),
            "delta_echo_above_floor": avg(paired),
        }
    return {
        "batch": batch_path.name,
        "n_decisions": len(cases),
        "by_schema": by_schema,
        "engagement_vs_vote_first": vs_vote_first,
    }


def run_echo_judge_validation(
    batch_path: Path,
    n: int = 40,
    min_day: int = 3,
    roles: frozenset[str] = REPLAYABLE_TOWN_ROLES,
    judge_model: str = DEFAULT_ADHERENCE_JUDGE_MODEL,
    max_workers: int = 6,
) -> dict[str, Any]:
    """Does the judge-free echo agree with the adherence JUDGE? Replay each decision
    once (production vote-first schema), then score the SAME regenerated action two
    ways: echo (lexical draw-on) and the judge's per-memory applied/overrode/ignored.
    If they agree, judge-engaged decisions carry higher echo than judge-ignored ones.
    Each row also keeps the memory + reasoning + the judge's per-memory evidence, so
    the JUDGE'S OWN accuracy can be read by hand (echo can't validate the judge — only
    a human can say whether 'applied' was the right call on a given reasoning)."""
    cases = _select_diverse(batch_path, n, min_day, 999, roles)

    def one(case: EvalCase, game: dict[str, Any]):
        allow = allow_abstain_for(case.day, game["day_resolutions"])
        votee, updated = _replay_vote(case, case.retrieved_observations, allow)
        mem = _mem_text(case)
        echo_own = _echo(updated, mem)
        jcase = application_case_for_judge(
            case,
            agent_message=None,
            agent_vote=DayVote(voter=case.player_id, votee=votee or "abstain"),
            updated_strategy=updated,
        )
        adh = judge_decision_adherence(jcase, model=judge_model)
        labels = [
            {
                "application": r.application,
                "action_followed": r.action_followed,
                "implied_direction": r.implied_direction,
                "evidence": r.evidence,
            }
            for r in (adh.per_memory if adh else [])
        ]
        nmem = len(labels)
        applied = sum(la["application"] == "applied" for la in labels)
        overrode = sum(la["application"] == "overrode_with_reason" for la in labels)
        ignored = sum(la["application"] == "ignored" for la in labels)
        return {
            "game": str(game["game_id"])[:8],
            "role": case.player_role,
            "day": case.day,
            "echo": round(echo_own, 4) if echo_own is not None else None,
            "n_mem": nmem,
            "frac_applied": round(applied / nmem, 3) if nmem else None,
            "frac_engaged": round((applied + overrode) / nmem, 3) if nmem else None,
            "frac_ignored": round(ignored / nmem, 3) if nmem else None,
            "vote": votee,
            "mem_text": mem[:500],
            "reasoning": (updated or "")[:500],
            "labels": labels,
        }

    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        rows = [f.result() for f in [ex.submit(one, c, g) for c, g in cases]]

    scored = [r for r in rows if r["echo"] is not None and r["frac_engaged"] is not None]
    engaged = [r["echo"] for r in scored if r["frac_engaged"] >= 0.5]
    ign = [r["echo"] for r in scored if r["frac_ignored"] is not None and r["frac_ignored"] > 0.5]
    mean = lambda xs: round(sum(xs) / len(xs), 4) if xs else None  # noqa: E731
    rho = pval = None
    try:  # rank correlation of echo vs judge engagement, if scipy is present
        from scipy.stats import spearmanr

        es = [r["echo"] for r in scored]
        fs = [r["frac_engaged"] for r in scored]
        if len(es) >= 5:
            rs = spearmanr(es, fs)
            rho, pval = round(float(rs.statistic), 3), round(float(rs.pvalue), 4)
    except Exception:  # noqa: BLE001 - correlation is a nice-to-have
        pass
    return {
        "batch": batch_path.name,
        "n_decisions": len(rows),
        "n_scored": len(scored),
        "echo_when_judge_engaged": {"n": len(engaged), "mean_echo": mean(engaged)},
        "echo_when_judge_ignored": {"n": len(ign), "mean_echo": mean(ign)},
        "spearman_echo_vs_frac_engaged": {"rho": rho, "p": pval},
        "rows": rows,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Decision-replay screen.")
    ap.add_argument(
        "--batch", required=True, type=Path, help="batch_results/<arm>.jsonl"
    )
    ap.add_argument(
        "--adherence-smoke",
        type=int,
        default=0,
        help="judge N recorded decisions with the adherence judge (LLM) instead "
        "of the no-LLM observational outcome pass",
    )
    ap.add_argument(
        "--causal",
        type=int,
        default=0,
        help="causal day-vote replay on N decisions: memory off vs as-stored, paired",
    )
    ap.add_argument(
        "--night",
        type=int,
        default=0,
        help="causal night-action replay on N decisions (power-targeting metric); "
        "use with --roles wolf or --roles serial_killer",
    )
    ap.add_argument(
        "--discussion",
        type=int,
        default=0,
        help="causal day_discussion replay on N town turns (passivity / threat-naming)",
    )
    ap.add_argument(
        "--adherence-scan",
        type=int,
        default=0,
        help="judge adherence on N RECORDED decisions and aggregate (did the "
        "agent follow the memory?) — no replay",
    )
    ap.add_argument(
        "--reorder",
        type=int,
        default=0,
        help="judge-free 2x2: replay N decisions under vote-first vs reason-first "
        "schema x memory off vs stored (tests the reason-before-act fix)",
    )
    ap.add_argument(
        "--reorder-adoption",
        type=int,
        default=0,
        help="judge adoption under vote-first vs reason-first (did reorder raise "
        "memory consideration?)",
    )
    ap.add_argument(
        "--echo",
        type=int,
        default=0,
        help="judge-FREE engagement: replay N decisions under vote-first vs "
        "reason-first vs memory-linked, measure how much each schema's reasoning "
        "draws on the retrieved memory (echo above a shuffled-memory floor)",
    )
    ap.add_argument(
        "--echo-validate",
        type=int,
        default=0,
        help="validate echo against the adherence judge on N replayed decisions: "
        "does echo agree with applied/ignored, and is the judge itself accurate "
        "(rows keep memory+reasoning+judge evidence to read by hand)",
    )
    ap.add_argument(
        "--coherence",
        type=int,
        default=0,
        help="does reordering SYNC vote with reasoning? Replay N decisions under "
        "vote-first/reason-first/memory-linked; judge reads the reasoning blind and "
        "its concluded choice is compared to the real vote (synced/desync/unclear)",
    )
    ap.add_argument(
        "--applicability",
        type=int,
        default=0,
        help="CAPABILITY probe: inject a clearly-mismatched ENDGAME memory into N "
        "mid-game decisions under the situation-match schema; does the agent reason "
        "it out as not-applicable (rejection rate + reasoning to read by hand)?",
    )
    ap.add_argument(
        "--framing",
        type=int,
        default=0,
        help="framing fact-check: hold the retrieved entries fixed, rewrite each "
        "outcome net->immediate, replay N town day-votes off/net/immediate, paired "
        "(net-value + abstain decomposition)",
    )
    ap.add_argument(
        "--judge",
        action="store_true",
        help="with --causal, also label adherence on the stored arm",
    )
    ap.add_argument("--min-day", type=int, default=3)
    ap.add_argument("--max-day", type=int, default=999)
    ap.add_argument(
        "--roles",
        default="villager,healer,investigator",
        help="comma-separated player roles to replay (default town; e.g. 'wolf')",
    )
    ap.add_argument(
        "--lens",
        choices=["town", "wolf"],
        default="town",
        help="scoring lens for --causal: town (correct = votes a threat) or wolf "
        "(deceiver: correct = induces a town mislynch). Use with --roles wolf,serial_killer",
    )
    ap.add_argument("--model", default=DEFAULT_ADHERENCE_JUDGE_MODEL)
    args = ap.parse_args()
    roles = frozenset(r.strip() for r in args.roles.split(",") if r.strip())
    if args.adherence_smoke:
        run_adherence_smoke(
            args.batch, n=args.adherence_smoke, min_day=args.min_day, model=args.model
        )
    elif args.causal:
        report = run_causal(
            args.batch,
            n=args.causal,
            min_day=args.min_day,
            max_day=args.max_day,
            do_judge=args.judge,
            judge_model=args.model,
            roles=roles,
            lens=args.lens,
        )
        print(json.dumps(report, indent=2))
    elif args.night:
        print(json.dumps(run_night_causal(args.batch, n=args.night, roles=roles), indent=2))
    elif args.discussion:
        print(json.dumps(run_discussion_causal(args.batch, n=args.discussion, roles=roles), indent=2))
    elif args.adherence_scan:
        print(json.dumps(run_adherence_scan(args.batch, n=args.adherence_scan, min_day=args.min_day, roles=roles), indent=2))
    elif args.reorder:
        print(json.dumps(run_reorder_test(args.batch, n=args.reorder, min_day=args.min_day, roles=roles), indent=2))
    elif args.reorder_adoption:
        print(json.dumps(run_reorder_adoption(args.batch, n=args.reorder_adoption, min_day=args.min_day, roles=roles), indent=2))
    elif args.echo:
        print(json.dumps(run_echo_consideration(args.batch, n=args.echo, min_day=args.min_day, roles=roles), indent=2))
    elif args.echo_validate:
        print(json.dumps(run_echo_judge_validation(args.batch, n=args.echo_validate, min_day=args.min_day, roles=roles, judge_model=args.model), indent=2))
    elif args.coherence:
        print(json.dumps(run_coherence_test(args.batch, n=args.coherence, min_day=args.min_day, roles=roles), indent=2))
    elif args.applicability:
        print(json.dumps(run_applicability_probe(args.batch, n=args.applicability, day=args.min_day), indent=2))
    elif args.framing:
        print(json.dumps(run_framing_rewrite_screen(
            args.batch, n=args.framing, min_day=args.min_day, max_day=args.max_day, roles=roles,
            audit_path=Path(
                f"evidence/memory_system/effectiveness/decision_replay/content_pilot/immediate_rewrites_d{args.min_day}-{args.max_day}.json"
            ),
        ), indent=2))
    else:
        print(json.dumps(run_observational(args.batch), indent=2))


if __name__ == "__main__":
    main()
