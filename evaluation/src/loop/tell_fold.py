"""Tell epoch fold — the tell ledger's consolidation step (the ledger spec in the read/tactic design
record §3; owner design 2026-07-12). CURATORIAL, never generative: tells' meaning lives in their
EXTENSION (which moments count as instances), so canonical text is NEVER rewritten — a new wording
either dies into an existing canonical (its instance row credits the survivor) or becomes a new
canonical on probation. Rewriting text would break denominator continuity for every already-detected
count; wording repair is the periodic strong-model audit's prerogative, not the fold's.

The lifecycle is quantized to checklist epochs: per game, mining and detection run against the FROZEN
checklist v_k (tells.py); every fold (default N=10 games) this module (1) resolves the epoch's new
mined wordings against the canon — free normalized exact-match first, then an LLM drop-or-keep judge
on embedding-prefiltered candidates (cosine is never the judge — house dedup rule); (2) appends
instance rows (set-not-accumulate: all tallies recompute from rows); (3) advances the probation clock
(scanned games, because scanning is what produces evidence — entry can never require counts); (4) rules
verdicts — a probation singleton after K scanned games archives (evidence-volume selection,
direction-neutral); an incumbent with fat support and null lift archives with a SPLIT-CHECK flag (a
null blend can hide two directional sub-tells) — never retain-rank by lift at thin support (that
selects on noise; the probe's cleanest town tell began as a lift≈0 singleton); (5) publishes checklist
v_{k+1}: incumbents by earned discrimination with a direction-balanced quota, all live probation, and
spare slots rotated to the least-recently-scanned archive entries (every archived tell eventually
re-earns or re-fails on fresh counts).

Store layout (a directory): canon.json (the tell registry + status), instances.jsonl (every mined +
detected row, append-only), checklist_v{k}.json (the frozen per-epoch contract), state.json (fold
counter). Lift arithmetic is tell_credit's; this module never prices.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from evaluation.src.loop.tell_credit import cast_prior_base, lift_table
from evaluation.src.loop.tells import _norm

# checklist shape (detector probe's ledger-spec cap): 25 incumbents + 15 probation + 8 rotation
INCUMBENT_CAP = 25
PROBATION_CAP = 15
CHECKLIST_CAP = 48
K_PROBATION = 12          # scanned games before a probation tell must show recurrence
NULL_LIFT_EPS = 0.03      # |shrunk_lift| below this at trusted support = measured-and-uninformative
NULL_SUPPORT = 20         # ...where "trusted support" starts
PREFILTER_THRESHOLD = 0.80
PREFILTER_TOP = 3
HEAD_N = 10               # per-channel top incumbents (by last published support) the tripwire guards
# Bounded fuzzy-match index (~65/channel): the embedding+LLM stage matches a new wording against only
# incumbents (bounded by the verdict cycle) + a recent-singleton window + a rotating archive re-audit
# slice, never the canon's ever-growing singleton tail. Keeps resolution cost and nomination rot flat
# as that tail grows; owner-ruled hard cap (2026-07-14) chosen over the ledger design's unseen-based
# retirement for simplicity. Retirement is from MATCHING only — never deletion; see _resolve_wordings.
INDEX_PROBATION_RECENT = 30   # newest probation entries per channel by born_fold (recent-singleton window)
INDEX_ARCHIVE_RECENT = 10     # most-recently-scanned archive entries per channel (checklist's re-audit lane)


def _paths(store_dir: Path) -> dict:
    return {"canon": store_dir / "canon.json", "instances": store_dir / "instances.jsonl",
            "state": store_dir / "state.json"}


def init_store(store_dir: str | Path, seed_checklist: dict) -> None:
    """Seed a tell store from an existing frozen checklist ({channel: [{tell_id, text}]}) — e.g. the
    consolidated v6ab canon. Seeded tells start as incumbents (they earned the seed) with a fresh
    scan clock."""
    store_dir = Path(store_dir)
    store_dir.mkdir(parents=True, exist_ok=True)
    p = _paths(store_dir)
    canon = [{"tell_id": t["tell_id"], "channel": ch, "text": t["text"], "status": "incumbent",
              "born_fold": 0, "games_scanned": 0, "last_scanned_fold": 0, "split_check": False}
             for ch, tells in seed_checklist.items() for t in tells]
    p["canon"].write_text(json.dumps(canon, indent=1))
    p["instances"].touch()
    p["state"].write_text(json.dumps({"fold": 0}))
    publish_checklist(store_dir)


def _load(store_dir: Path) -> tuple[list[dict], dict]:
    p = _paths(store_dir)
    return json.loads(p["canon"].read_text()), json.loads(p["state"].read_text())


def _default_judge():
    """The extensional-equivalence drop-or-keep judge (flash-lite, the dedup model): two descriptions
    are the same tell iff a transcript reader would count the SAME moments as instances of both —
    strict, because the how-grain is where discrimination lives. Lazy import: pure fold logic stays
    LLM-free for tests."""
    from pydantic import BaseModel, Field

    from Agents.llm_factory import get_llm_dedup

    class SameTellVerdict(BaseModel):
        same: bool = Field(description="True only if the two descriptions denote the SAME tell — a "
                           "transcript reader would count the same moments as instances of both.")
        reason: str = Field(description="One short sentence for the call.")

    llm = get_llm_dedup().with_structured_output(SameTellVerdict)

    def judge(new_text: str, canon_text: str) -> bool:
        v = llm.invoke(
            "Two behavior descriptions from the social-deduction game Werewolf.\n"
            f"A (new): {new_text}\nB (canonical): {canon_text}\n"
            "Same tell? Judge STRICTLY by extension: same behavior, same mechanism, same trigger. "
            "A sub-type with a distinct mechanism is NOT the same.")
        return bool(v.same)

    return judge


def _default_embedder(texts: list[str]):
    from Agents.memory.vectors import embed_texts
    return embed_texts(texts)


def make_book_collapse(judge=None, embedder=None, *, prefilter_threshold: float = 0.80):
    """View-layer same-behavior collapse for the injected book (build_book's `collapse` hook). The book
    seats the top ~3 tells per (subject role, channel); the unwired merge/split audit's fragmentation
    residual (§0) can put two-plus fragments of ONE behavior into those slots, so a role's manual repeats
    itself and its effective slot count shrinks. This drops the redundant fragments so the freed slots
    backfill with DISTINCT behaviors. It reuses the fold's OWN cascade — embedding prefilter (>= threshold)
    then the extensional-equivalence judge — over the handful of book candidates, once per fold.

    GUARDRAIL (structural, not a knob): candidates arrive sorted by subject_lift, so the first member of a
    class is its highest-lift one and is kept; a later member is dropped ONLY when the judge rules it the
    SAME behavior as an already-kept survivor. Diversity therefore never costs lift — every dropped tell is
    lift-equivalent to a kept one by construction.

    SYMPTOM FIX, not the cure. View-layer only: canon, ledger, and CREDIT are untouched — a dropped fragment
    keeps its identity, stays scanned, and keeps paying credit; nothing is pooled. Pooling the fragments'
    evidence into one accurate lift is the audit's canon merge (§0); this only stops one behavior taking
    several book slots. Returns a `collapse(candidates, text_of)` callable."""
    judge = judge or _default_judge()
    embedder = embedder or _default_embedder

    def collapse(candidates: list[dict], text_of) -> list[dict]:
        if len(candidates) <= 1:
            return list(candidates)
        texts = [text_of.get(t["tell_id"], t["tell_id"]) for t in candidates]
        vecs = embedder(texts)
        kept: list[dict] = []
        kept_idx: list[int] = []
        for i, t in enumerate(candidates):   # candidates are lift-sorted: first seen of a class = survivor
            if any(_cos(vecs[i], vecs[j]) >= prefilter_threshold and judge(texts[i], texts[j])
                   for j in kept_idx):
                continue                     # same behavior as a kept higher-lift survivor -> drop from book
            kept.append(t)
            kept_idx.append(i)
        return kept
    return collapse


def _resolve_wordings(new_wordings: list[dict], canon: list[dict], judge=None, embedder=None,
                      fold_no: int = 0) -> tuple[dict, list[dict]]:
    """Resolve distinct new mined wordings against the same-channel canon: normalized exact-match
    (free) → embedding prefilter (top-PREFILTER_TOP ≥ threshold) → LLM drop-or-keep. Returns
    (norm_text -> canonical tell_id, new canon entries created). Freeze-old: the canon text is never
    touched; a match means the WORDING dies and its instances credit the canonical."""
    judge = judge or _default_judge()
    embedder = embedder or _default_embedder
    by_channel: dict[str, list[dict]] = defaultdict(list)
    for c in canon:
        by_channel[c["channel"]].append(c)
    norm_index = {(c["channel"], _norm(c["text"])): c["tell_id"] for c in canon}

    resolution: dict = {}
    created: list[dict] = []
    pending: dict[str, list[dict]] = defaultdict(list)   # channel -> unresolved wordings
    for w in new_wordings:
        key = (w["channel"], _norm(w["text"]))
        if key in norm_index:
            resolution[key] = norm_index[key]
        else:
            pending[w["channel"]].append(w)

    next_id = 1 + max((int(c["tell_id"].split("_")[-1]) for c in canon
                       if c["tell_id"].split("_")[-1].isdigit()), default=0)
    for ch, ws in pending.items():
        # The bounded fuzzy-match index (see the INDEX_* caps): the embedding+LLM stage sees only a
        # capped slice of the channel canon — all incumbents, the INDEX_PROBATION_RECENT newest
        # probation singletons, and the INDEX_ARCHIVE_RECENT most-recently-scanned archive entries —
        # never the full singleton tail. Safety argument: this can only RETIRE a stale wording from
        # MATCHING, never lose it. Nothing here deletes or restatuses a canon row; a wording whose true
        # match fell outside the window simply re-enters as a fresh probation canonical, and the
        # periodic audit can reunite the pair later. Because all tallies recompute from instance rows,
        # a temporary identity split loses no evidence. (The free normalized exact-match stage above
        # stays GLOBAL over the whole canon, so an identical wording can never mint a duplicate.)
        pool = by_channel.get(ch, [])
        cands = ([c for c in pool if c["status"] == "incumbent"]
                 + sorted((c for c in pool if c["status"] == "probation"),
                          key=lambda c: -c["born_fold"])[:INDEX_PROBATION_RECENT]
                 + sorted((c for c in pool if c["status"] == "archive"),
                          key=lambda c: -c["last_scanned_fold"])[:INDEX_ARCHIVE_RECENT])
        if cands:
            vecs = embedder([w["text"] for w in ws] + [c["text"] for c in cands])
            new_vecs, canon_vecs = vecs[:len(ws)], vecs[len(ws):]
        for i, w in enumerate(ws):
            match = None
            if cands:
                sims = sorted(((_cos(new_vecs[i], canon_vecs[j]), c) for j, c in enumerate(cands)),
                              key=lambda t: -t[0])[:PREFILTER_TOP]
                for sim, c in sims:
                    if sim >= PREFILTER_THRESHOLD and judge(w["text"], c["text"]):
                        match = c["tell_id"]
                        break
            if match:
                resolution[(ch, _norm(w["text"]))] = match
            else:
                tid = f"{ch[:4]}_{next_id}"
                next_id += 1
                entry = {"tell_id": tid, "channel": ch, "text": w["text"], "status": "probation",
                         "born_fold": fold_no, "games_scanned": 0, "last_scanned_fold": fold_no,
                         "split_check": False}
                canon.append(entry)
                by_channel[ch].append(entry)
                created.append(entry)
                resolution[(ch, _norm(w["text"]))] = tid
    return resolution, created


def _cos(a, b) -> float:
    num = sum(x * y for x, y in zip(a, b))
    da = sum(x * x for x in a) ** 0.5
    db = sum(x * x for x in b) ** 0.5
    return num / (da * db) if da and db else 0.0


def _tripwire(last_n: dict, head_by_channel: dict, canon: list[dict], table: dict,
              null_archived_ids: set) -> dict:
    """Deterministic publication gate (owner ruling 2026-07-14, consolidation walkthrough): a bad
    fold must not publish a
    corrupted checklist that the detector then trusts for a whole epoch, and a counts-only fold report
    can't catch one. Two always-on invariants, no LLM, no config knob:

    (1) Monotone detected support — the ledger is append-only and the fold never re-files old rows, so
    every previously published tell's recomputed n must be >= its last_n. A decrease means rows were
    lost in the recompute (the realistic failure: roles_by_game silently missing older games so the
    tally join drops their rows, or a corrupted instances file).

    (2) Head continuity — a top incumbent may leave the published head only via THIS fold's own
    null-lift verdict; any other exit (a step-4 bug, an external canon edit the fold never ruled) is a
    silent curation divergence. head_by_channel comes from last_n (state, not canon) so an external
    canon tamper cannot hide from it.

    Raises RuntimeError on violation (fail-loud: the loop crashes the tells step visibly). This gates
    CURATION only — the instance-row append already happened, so a halted fold loses no evidence."""
    regressed = [(tid, prior_n, table.get(tid, {}).get("n", 0)) for tid, prior_n in last_n.items()
                 if table.get(tid, {}).get("n", 0) < prior_n]
    if regressed:
        detail = ", ".join(f"{tid} {a}->{b}" for tid, a, b in sorted(regressed))
        raise RuntimeError(f"tell-fold tripwire: detected support regressed for {len(regressed)} "
                           f"tell(s) [{detail}] — an append-only ledger cannot lose rows (check "
                           "roles_by_game coverage / instances.jsonl integrity)")

    by_id = {c["tell_id"]: c for c in canon}          # canon never deletes; assert presence anyway
    dropped = []
    head_checked = 0
    for heads in head_by_channel.values():
        for tid in heads:
            head_checked += 1
            entry = by_id.get(tid)
            if entry is None:
                dropped.append((tid, "missing"))
            elif entry["status"] != "incumbent" and tid not in null_archived_ids:
                dropped.append((tid, entry["status"]))
    if dropped:
        detail = ", ".join(f"{tid} ->{st}" for tid, st in sorted(dropped))
        raise RuntimeError(f"tell-fold tripwire: {len(dropped)} head incumbent(s) left the head "
                           f"without a null-lift verdict [{detail}] — curation diverged from the "
                           "fold's own rulings")
    return {"prior_tells": len(last_n), "head_checked": head_checked, "ok": True}


def fold(store_dir: str | Path, mined_rows: list[dict], detected_rows: list[dict],
         scanned: list[dict], roles_by_game: dict, *, judge=None, embedder=None) -> dict:
    """One epoch fold. mined_rows/detected_rows/scanned = this epoch's tells.py outputs;
    roles_by_game = game_id -> role map (the deterministic join + the cast prior). Returns the fold
    report incl. the baseline registration ({'tell/<ch>': grading} + base rows) for the coherence
    invariant."""
    store_dir = Path(store_dir)
    p = _paths(store_dir)
    canon, state = _load(store_dir)
    fold_no = state["fold"] + 1
    # tripwire references, snapshotted at load BEFORE the verdict loop mutates canon: last_n = the
    # tally as of the previous publication (absent on a fresh store -> both invariants trivially pass);
    # head_by_channel = per channel the top HEAD_N previously published incumbents by that support.
    last_n = state.get("last_n", {})
    head_by_channel: dict[str, list[str]] = defaultdict(list)
    load_channel = {c["tell_id"]: c["channel"] for c in canon}
    for tid in last_n:
        if tid in load_channel:
            head_by_channel[load_channel[tid]].append(tid)
    for ch, tids in head_by_channel.items():
        head_by_channel[ch] = sorted(tids, key=lambda t: -last_n[t])[:HEAD_N]

    # (1) resolve the epoch's new wordings (screened-clean mined rows only — structural flags stay out)
    clean_mined = [r for r in mined_rows if not r.get("screen_flags")]
    distinct = {}
    for r in clean_mined:
        distinct.setdefault((r["channel"], _norm(r["behavior"])), {"channel": r["channel"],
                                                                   "text": r["behavior"]})
    resolution, created = _resolve_wordings(list(distinct.values()), canon, judge, embedder, fold_no)

    # (2) append instance rows — set-not-accumulate: tallies always recompute from rows. This is the
    # raw ledger record and is never gated; the tripwire below gates only CURATION (canon status + the
    # published card), so a fold halted there keeps its appended evidence and re-runs after the fix.
    with open(p["instances"], "a") as f:
        for r in detected_rows:
            f.write(json.dumps({**r, "source_kind": "DETECTED", "fold": fold_no}) + "\n")
        for r in clean_mined:
            tid = resolution.get((r["channel"], _norm(r["behavior"])))
            if tid:
                f.write(json.dumps({"game_id": r["game_id"], "player": r["exhibitor"],
                                    "channel": r["channel"], "tell_id": tid, "day": r["day"],
                                    "evidence_quote": r["evidence_quote"],
                                    "source_kind": "MINED", "fold": fold_no}) + "\n")

    # (3) the probation clock: scanned games per checklist tell
    from evaluation.src.loop.tells import scanned_games_by_tell
    checklist = json.loads((store_dir / f"checklist_v{state['fold']}.json").read_text())
    scans = scanned_games_by_tell(checklist, scanned)
    for c in canon:
        if c["tell_id"] in scans:
            c["games_scanned"] += scans[c["tell_id"]]
            c["last_scanned_fold"] = fold_no

    # (4) recompute tallies from DETECTED rows only (mined rows are discovery, never lift) + verdicts
    all_detected = [json.loads(l) for l in open(p["instances"]) if l.strip()]
    all_detected = [r for r in all_detected if r.get("source_kind") == "DETECTED"]
    table = {t["tell_id"]: t for t in lift_table(all_detected, roles_by_game)}
    archived_singletons = 0
    null_archived_ids: set = set()          # by explicit id, not count: the head-continuity exemption
    for c in canon:
        n = table.get(c["tell_id"], {}).get("n", 0)
        lift = table.get(c["tell_id"], {}).get("shrunk_lift", 0.0)
        if c["status"] == "probation" and c["games_scanned"] >= K_PROBATION:
            if n <= 1:
                c["status"] = "archive"          # still a singleton after its window: evidence-volume cut
                archived_singletons += 1
            else:
                c["status"] = "incumbent"        # recurred; ranking decides its checklist seat
        elif c["status"] == "incumbent" and n >= NULL_SUPPORT and abs(lift) < NULL_LIFT_EPS:
            c["status"] = "archive"              # measured-and-uninformative…
            c["split_check"] = True              # …but a null blend can hide two directional sub-tells
            null_archived_ids.add(c["tell_id"])

    # tripwire: gate persistence + publication on the two invariants. Runs after the verdict loop and
    # before ANY write, so nothing below persists on a trip (a raise here re-runnable after the fix).
    tripwire = _tripwire(last_n, head_by_channel, canon, table, null_archived_ids)

    # (5) publish v_{k+1} + persist. last_n carries forward the tally scoped to incumbents (the head
    # candidates for the next fold's continuity check); archived tells drop out so they never re-trip.
    incumbent = {c["tell_id"] for c in canon if c["status"] == "incumbent"}
    state["fold"] = fold_no
    state["last_n"] = {tid: table[tid]["n"] for tid in table if tid in incumbent}
    p["canon"].write_text(json.dumps(canon, indent=1))
    p["state"].write_text(json.dumps(state))
    published = publish_checklist(store_dir, table)
    base = cast_prior_base(roles_by_game)
    return {"fold": fold_no, "new_wordings": len(distinct), "new_canonicals": len(created),
            "archived_singletons": archived_singletons, "archived_null_lift": len(null_archived_ids),
            "checklist": {ch: len(ts) for ch, ts in published.items()},
            "credited_channels": {k: "cast_prior" for k in base},
            "base_rates": {k: list(v) for k, v in base.items()}, "tripwire": tripwire}


def publish_checklist(store_dir: str | Path, table: dict | None = None) -> dict:
    """Compose and write checklist v_{fold}: per channel, incumbents by |shrunk_lift| under a
    direction-balanced quota (evil-leaning and town-leaning both surface — every role's book needs
    candidates), all live probation (newest first, capped), spare slots rotated to the
    least-recently-scanned archive entries (zero-marginal-cost re-audit)."""
    store_dir = Path(store_dir)
    canon, state = _load(store_dir)
    table = table or {}
    out: dict = {}
    for ch in sorted({c["channel"] for c in canon}):
        pool = [c for c in canon if c["channel"] == ch]
        inc = [c for c in pool if c["status"] == "incumbent"]
        inc.sort(key=lambda c: -abs(table.get(c["tell_id"], {}).get("shrunk_lift", 0.0)))
        pos = [c for c in inc if table.get(c["tell_id"], {}).get("shrunk_lift", 0.0) >= 0]
        neg = [c for c in inc if table.get(c["tell_id"], {}).get("shrunk_lift", 0.0) < 0]
        half = INCUMBENT_CAP // 2
        picked = pos[:INCUMBENT_CAP - min(len(neg), half)] + neg[:half]
        picked = picked[:INCUMBENT_CAP]
        prob = sorted((c for c in pool if c["status"] == "probation"),
                      key=lambda c: -c["born_fold"])[:PROBATION_CAP]
        spare = CHECKLIST_CAP - len(picked) - len(prob)
        rot = sorted((c for c in pool if c["status"] == "archive"),
                     key=lambda c: c["last_scanned_fold"])[:max(0, spare)]
        out[ch] = [{"tell_id": c["tell_id"], "text": c["text"]} for c in picked + prob + rot]
    (store_dir / f"checklist_v{state['fold']}.json").write_text(json.dumps(out, indent=1))
    return out
