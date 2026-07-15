"""LLM reader for role-fact hallucination candidates — stage 3 of the detection pipeline.

The deterministic screen (``evaluation.src.audits.role_hallucination_screen``) proves *which* text
units touch a checkable fact; this reader decides the semantic question the screen never can:
does the text merely mention the fact (retrospection, kill-counting — legitimate) or does it
contradict it (treat a dead player as alive, misstate a revealed role, miscount the living)?

Design choices that keep the read cheap and grounded:

- **Fact sheet, not transcript.** Each candidate is judged against a small deterministic fact
  sheet built from the structured game record — deaths (with revealed role, day, and attacker),
  the alive set with per-role counts, the logged public role-claims, and the speaker's own
  first-hand knowledge. No transcript context is sent; the judgment is "text vs facts."
- **Speaker knowledge distinguishes lying from hallucinating.** A wolf misstating its dead
  packmate's role *knows* the truth — that is deception, not hallucination, and only the verdicts
  the speaker could not know better about count toward the hallucination rate.
- **Reasoning before verdict** in the output schema (quote → reason → verdict), the same
  commitment ordering the game schemas use; all fields required (the weak-model rule).

Golden calibration (``--golden``) scores the reader against the manually confirmed cases before
any census run is trusted. Console: ``eval-role-hallucination-read``.
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from evaluation.src.core.settings import REPO_ROOT
from evaluation.src.data.sources.batch_records import load_batch_records
from evaluation.src.judges.config import get_judge_llm

DEFAULT_READ_MODEL = "gemini-3.1-flash-lite"  # narrow grounded task; --golden gates fitness
DEFAULT_CANDIDATES = "evidence/generation_prompt/validation/hallucination_candidates.jsonl"
DEFAULT_OUT = "evidence/generation_prompt/validation/hallucination_verdicts.jsonl"
DEFAULT_RECORDS_GLOB = "evidence/v7_final/runs/v2_full/gen*_o*.jsonl"


class RoleFactVerdict(BaseModel):
    quote: str = Field(description="the decisive phrase copied verbatim from the statement, or an empty string if none")
    reason: str = Field(description="one or two sentences: what the phrase asserts vs what the facts say")
    verdict: Literal["consistent", "hallucination", "deliberate_deception", "ambiguous"] = Field(
        description="the classification, per the definitions in the instructions")
    error_class: Literal["dead_role", "dead_as_alive", "composition", "claim_attrib", "other", "none"] = Field(
        description="which fact was contradicted; 'none' when the verdict is consistent")


SYSTEM = """You audit statements from a Werewolf (social-deduction) game for factual errors about deaths and roles. In this game, every death is publicly announced and the dead player's true role is revealed to all players at death — so the facts below are known to every living player at the time of the statement.

You get (a) the verified facts as of that game day, and (b) ONE statement by a living player — either a public chat message or that player's private strategy note. Judge the statement ONLY against the given facts.

Verdicts:
- consistent — nothing in the statement contradicts the facts. Discussing past events is consistent: analysing votes that were cast for or against a now-dead player ("who voted for the investigator", "who pushed hardest against the investigator" — those votes happened while they were alive), reasoning about who USED to be aligned with a now-dead player ("where the wolf pack might have been hiding" is about past behavior), or counting kills made so far ("we cleared two wolves" is a kill count, not a claim that two wolves are alive). Judge the time reference carefully: past-tense references to dead players and dead roles are consistent AS LONG AS the described event matches the facts; only treating them as alive NOW (or as a live future threat) contradicts. Past tense does NOT excuse a false claim about the past — misstating who killed whom, what role a dead player was revealed as, or who claimed what is a contradiction whatever the tense. Uncertainty about things the facts leave open is consistent.
- hallucination — the statement asserts, or actively reasons as if, something the facts rule out, and the speaker has no first-hand knowledge of the matter (see speaker knowledge). Examples: treating a dead player as a live suspect or threat; misstating a dead player's revealed role; hunting "the remaining wolf" when the facts show no wolf can be alive; giving a wrong count of a role still alive; attributing a role-claim the player never made. Hedged or conditional phrasing still counts when the reasoning treats the ruled-out possibility as live.
- deliberate_deception — the statement contradicts a fact in the speaker's PRIVATE first-hand knowledge (their own role, their own night actions, a wolf's pack roster — the "speaker knowledge" section), e.g. a wolf misstating its own dead packmate's role. Reserve this verdict for private knowledge only: misstating a PUBLICLY known fact (deaths, reveals, votes) is hallucination even when the speaker "should know better" — genuinely forgetting public facts is exactly the failure being measured, and strategic lying about them cannot be distinguished from it. This verdict applies ONLY to public chat messages: a private strategy note has no audience, so it cannot deceive — a factual error in a private note is a hallucination (the player genuinely believes it), and a note PLANNING deception ("keep claiming villager") is consistent.
- ambiguous — genuinely undecidable from the statement (e.g. wording that could equally be past-tense analysis or a present-tense claim).

Scope rules:
- Judge ONLY claims the facts below can settle: deaths, revealed roles, who killed whom, alive counts, the recorded votes, and the logged role-claims. What players merely SAID in chat is not in the facts (except logged claims) — do not guess about it; if a claim is about unrecorded chat content, it is out of scope: judge it consistent.
- Role-claims made earlier TODAY may be missing from the claims log (the log is compiled at each day's end). Never flag a claim-attribution about something said today; only flag one that contradicts a listed claim or a revealed role.
- Timing convention: "died night N" means killed in the night AFTER day N's discussion and vote — the player was alive and could act, speak, and vote throughout day N. "lynched day N" means voted out at the END of day N — they participated in that day, including its vote. Deaths become known to everyone the next morning.
- A bare plural is not a count claim: "find the remaining wolves", "the wolves are hiding" is idiomatic even when one wolf is alive — read it as "at least one". Only explicit quantities assert counts ("two wolves", "both wolves", "the last wolf"). With ZERO of the role alive, any "remaining/still out there" reference does contradict the facts.

Copy the decisive phrase verbatim, explain briefly, then give the verdict and the error class."""

USER_TEMPLATE = """== Verified facts, game day {day} ==
Deaths so far (role revealed publicly at death):
{deaths}
Alive players ({n_alive}): {alive}
Roles still alive: {alive_counts}
Public role-claims logged so far: {claims}
Recorded votes on previous days (public):
{votes}

== Speaker ==
{speaker} — true role: {speaker_role}
First-hand knowledge: {knowledge}

== Statement under audit ({unit}, day {day}) ==
\"\"\"{text}\"\"\"

== Why it was flagged (deterministic screen anchors) ==
{anchors}"""


def _attacker(nr: dict, victim: str) -> str:
    if nr.get("wolves_target") == victim and nr.get("kill_successful"):
        return "the wolves"
    if nr.get("serial_killer_target") == victim and nr.get("serial_killer_kill_landed", True):
        return "the serial killer"
    if nr.get("vigilante_target") == victim and nr.get("vigilante_kill_landed", True):
        return "the vigilante"
    return "unknown"


def build_fact_sheet(record: dict, cand: dict) -> dict:
    """Deterministic prompt inputs for one candidate, from the structured record only."""
    roles, day = record["roles"], int(cand["day"])
    dead: list[str] = []
    dead_set: set[str] = set()
    for nr in record.get("night_resolutions") or []:
        if int(nr["day"]) + 1 > day:
            continue
        for p in nr.get("deaths") or []:
            dead.append(f"- {p} — {roles[p]} — died night {nr['day']}, killed by {_attacker(nr, p)}")
            dead_set.add(p)
    for dr in record.get("day_resolutions") or []:
        vp = dr.get("voted_player")
        if vp and int(dr["day"]) + 1 <= day:
            dead.append(f"- {vp} — {roles[vp]} — lynched by vote, day {dr['day']}")
            dead_set.add(vp)
    alive = [p for p in roles if p not in dead_set]
    counts: dict[str, int] = {}
    for p in alive:
        counts[roles[p]] = counts.get(roles[p], 0) + 1
    alive_counts = ", ".join(f"{v} {k.replace('_', ' ')}" for k, v in sorted(counts.items()))
    for role in ("wolf", "serial_killer", "healer", "investigator", "vigilante"):
        if role not in counts:
            alive_counts += f", 0 {role.replace('_', ' ')}"

    votes: list[str] = []
    for dr in record.get("day_resolutions") or []:
        if int(dr["day"]) >= day:
            continue  # the unit's own day is still in progress when it is written
        pairs = ", ".join(f"{v['voter']}→{v['votee']}" for v in dr.get("votes") or [])
        outcome = f"{dr['voted_player']} lynched" if dr.get("voted_player") else "no lynch"
        votes.append(f"- day {dr['day']}: {pairs or 'no votes'} ({outcome})")

    claims = sorted({f"{p} claimed {r}" for ds in record.get("day_summaries") or []
                     if int(ds.get("day", 0)) <= day
                     for rc in (ds.get("structured") or {}).get("role_claims") or []
                     for p, r in [(rc.get("player"), rc.get("claimed_role"))] if p and r})

    speaker, speaker_role = cand["speaker"], roles.get(cand["speaker"], "unknown")
    knowledge = ["knows every publicly revealed fact above (all players do)"]
    if speaker_role == "wolf":
        pack = [p for p, r in roles.items() if r == "wolf"]
        knowledge.append(f"is a wolf and knows the full wolf roster first-hand: {', '.join(pack)}")
    if speaker_role == "investigator":
        checks = [f"{r['player_investigated']} is {r['role_revealed']} (night {r['day']})"
                  for r in record.get("investigator_results") or [] if int(r["day"]) < day]
        if checks:
            knowledge.append("has private investigation results: " + "; ".join(checks))
    # the speaker's OWN night actions — without these, a true first-person claim
    # ("I targeted X") can misread as deception when someone else landed the kill
    own: list[str] = []
    for nr in record.get("night_resolutions") or []:
        n = int(nr["day"])
        if n + 1 > day:
            continue
        if speaker_role == "wolf" and nr.get("wolves_target"):
            own.append(f"night {n}: the wolves attacked {nr['wolves_target']} "
                       f"({'kill succeeded' if nr.get('kill_successful') else 'kill failed'})")
        if speaker_role == "healer" and nr.get("healer_target"):
            own.append(f"night {n}: protected {nr['healer_target']}"
                       f"{' (save mattered)' if nr.get('healer_saved') else ''}")
        if speaker_role == "vigilante" and nr.get("vigilante_target"):
            own.append(f"night {n}: targeted {nr['vigilante_target']} "
                       f"({'shot landed' if nr.get('vigilante_kill_landed') else 'shot failed'})")
        if speaker_role == "serial_killer" and nr.get("serial_killer_target"):
            own.append(f"night {n}: attacked {nr['serial_killer_target']} "
                       f"({'kill landed' if nr.get('serial_killer_kill_landed') else 'kill failed'})")
    if own:
        knowledge.append("own night actions so far — " + "; ".join(own))

    return {
        "day": day,
        "deaths": "\n".join(dead) or "- none yet",
        "n_alive": len(alive), "alive": ", ".join(alive),
        "alive_counts": alive_counts,
        "claims": "; ".join(claims) or "none",
        "votes": "\n".join(votes) or "- none yet",
        "speaker": speaker, "speaker_role": speaker_role.replace("_", " "),
        "knowledge": "; ".join(knowledge),
        "unit": "private strategy note" if cand["unit"] == "updated_strategy"
                else "public chat message",
        "text": cand["text"],
        "anchors": "\n".join(f"- {a['kind']}: {a['fact']}" for a in cand["anchors"]),
    }


def read_candidates(candidates: list[dict], records_by_key: dict, model: str,
                    workers: int = 12) -> list[dict]:
    llm = get_judge_llm(model, temperature=0.0).with_structured_output(RoleFactVerdict)

    def one(idx_cand):
        idx, cand = idx_cand
        record = records_by_key[(cand["game_id"], cand["arm"])]
        prompt = USER_TEMPLATE.format(**build_fact_sheet(record, cand))
        last_err = None
        for attempt in range(4):
            try:
                v = llm.invoke([("system", SYSTEM), ("human", prompt)])
                return idx, {**cand, "read": v.model_dump(), "read_model": model}
            except Exception as e:  # transport/429/parse — the standard retry layer
                last_err = e
                time.sleep(2 ** attempt)
        return idx, {**cand, "read": None, "read_error": str(last_err), "read_model": model}

    out: list[dict | None] = [None] * len(candidates)
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = [ex.submit(one, (i, c)) for i, c in enumerate(candidates)]
        done = 0
        for f in as_completed(futures):
            i, row = f.result()
            out[i] = row
            done += 1
            if done % 200 == 0:
                print(f"  {done}/{len(candidates)} read")
    return [r for r in out if r is not None]


# --- Golden calibration -------------------------------------------------------
# Manually confirmed cases (T1 read + the 2026-07-08 recall probes). `expect` is the acceptable
# verdict set; `frag` disambiguates the row (game ids repeat across paired arms).

GOLDEN = [
    # confirmed hallucinations (T1 read, re-verified per-arm 2026-07-08)
    dict(g="pair_v2_full_gen1_g3", arm="all_enabled", d=3, s=2, frag="two wolves left",
         expect={"hallucination"}),
    dict(g="pair_v2_full_gen4_g3", arm="all_enabled", d=5, s=0, frag="remaining wolf",
         expect={"hallucination"}),
    dict(g="pair_v2_full_gen5_g3", arm="all_enabled", d=4, s=11, frag="two wolves and a serial",
         expect={"hallucination"}),
    # T1's "case 4" REFUTED during this calibration: the record for its own arm shows the serial
    # killer really did kill player_2 (the original read's "wolves killed p2" note described the
    # OTHER arm's night) — the statement is true, and the reader must say so.
    dict(g="pair_v2_full_gen6_g2", arm="all_disabled", d=3, s=2, frag="serial killer hit",
         expect={"consistent"}),
    # deliberate lie (T1's deception catch): wolf about its dead packmate
    dict(g="pair_v2_full_gen5_g3", arm="all_enabled", d=3, s=0, frag="player_7 was the serial",
         expect={"deliberate_deception"}),
    # probe-found composition misses (plain assertions)
    dict(g="pair_v2_full_gen4_g0", arm="all_disabled", d=4, s=0, frag="final wolf",
         expect={"hallucination", "ambiguous"}),
    dict(g="pair_v2_full_gen4_g0", arm="all_enabled", d=5, s=4, frag="remaining wolf",
         expect={"hallucination"}),
    dict(g="pair_v2_full_gen4_g0", arm="all_enabled", d=5, s=6, frag="remaining wolf",
         expect={"hallucination"}),
    dict(g="pair_v2_full_gen5_g0", arm="all_enabled", d=4, s=6, frag="remaining wolf",
         expect={"hallucination"}),
    dict(g="pair_v2_full_gen5_g2", arm="all_enabled", d=5, s=1, frag="remaining wolf",
         expect={"hallucination"}),
    # probe-found conditionals (lenient: rhetorical "if you're the last wolf")
    dict(g="pair_v2_full_gen4_g3", arm="all_disabled", d=5, s=2, frag="last wolf",
         expect={"hallucination", "ambiguous"}),
    dict(g="pair_v2_full_gen4_g3", arm="all_disabled", d=5, s=4, frag="last wolf",
         expect={"hallucination", "ambiguous"}),
    # confirmed-legitimate windows (the manual read's false-positive taxonomy)
    dict(g="pair_v2_full_gen1_g3", arm="all_enabled", d=4, s=12, frag="pushing the investigator",
         expect={"consistent"}),
    dict(g="pair_v2_full_gen2_g1", arm="all_disabled", d=4, s=9, frag="voted for the investigator",
         expect={"consistent"}),
    dict(g="pair_v2_full_gen2_g1", arm="all_disabled", d=4, s=12, frag="eliminating the serial killer",
         expect={"consistent"}),
    dict(g="pair_v2_full_gen3_g1", arm="all_enabled", d=3, s=9, frag="vote for the investigator",
         expect={"consistent"}),
    dict(g="pair_v2_full_gen3_g2", arm="all_enabled", d=5, s=10, frag="converging on the serial killer",
         expect={"consistent"}),
    # true first-person action claim by the vigilante — exercises the own-night-actions knowledge
    dict(g="pair_v2_full_gen4_g3", arm="all_disabled", d=4, s=4, frag="against the investigator",
         expect={"consistent"}),
    dict(g="pair_v2_full_gen4_g2", arm="all_enabled", d=3, s=7, frag="the healer dead",
         expect={"consistent"}),
    # vote-history claims, record-verified 2026-07-08 (exercise the vote lines in the fact sheet):
    # player_4 really did vote abstain on day 4 — a TRUE claim the vote-blind reader misflagged
    dict(g="pair_v2_full_gen6_g0", arm="all_enabled", d=5, s=3, frag="player_4 abstained",
         expect={"consistent"}),
    # player_4 actually voted FOR player_5 — the "opposed the push" claim is false. Votes are
    # public, so per the private-knowledge rule this is hallucination, not deception.
    dict(g="pair_v2_full_gen6_g0", arm="all_disabled", d=5, s=12, frag="opposed the push",
         expect={"hallucination"}),
    # retrospective discussion of a past lynch — tense rule at scale
    dict(g="pair_v2_full_gen1_g2", arm="all_enabled", d=6, s=6, frag="pushing for the vigilante",
         expect={"consistent"}),
    # private-note composition error ("both wolves eliminated", one alive): hallucination, and
    # NEVER deception — a private note has no audience
    dict(g="pair_v2_full_gen1_g0", arm="all_enabled", d=4, s=None, unit="updated_strategy",
         frag="both wolves eliminated", expect={"hallucination"}),
]


def _match_golden(candidates: list[dict]) -> list[tuple[dict, dict]]:
    pairs = []
    for g in GOLDEN:
        unit = g.get("unit", "message")
        hits = [c for c in candidates
                if c["game_id"] == g["g"] and c["arm"] == g["arm"] and c["day"] == g["d"]
                and (g["s"] is None or c.get("seq") == g["s"]) and c["unit"] == unit
                and g["frag"].lower() in c["text"].lower()]
        if hits:
            pairs.append((g, hits[0]))
        else:
            print(f"  GOLDEN NOT ANCHORED (screen recall gap!): {g}")
    return pairs


def run_golden(candidates: list[dict], records_by_key: dict, model: str) -> bool:
    pairs = _match_golden(candidates)
    rows = read_candidates([c for _, c in pairs], records_by_key, model)
    ok = 0
    for (g, _), row in zip(pairs, rows):
        got = (row.get("read") or {}).get("verdict", "READ_ERROR")
        mark = "PASS" if got in g["expect"] else "FAIL"
        ok += mark == "PASS"
        print(f"[{mark}] {g['g']} d{g['d']} s{g['s']} ({g['frag']!r}): "
              f"expected {sorted(g['expect'])}, got {got}")
    print(f"golden: {ok}/{len(pairs)} within expectation")
    # gate: every confirmed hallucination caught (not judged consistent), <=1 legit misread
    miss_h = sum(1 for (g, _), row in zip(pairs, rows)
                 if g["expect"] == {"hallucination"}
                 and (row.get("read") or {}).get("verdict") == "consistent")
    miss_l = sum(1 for (g, _), row in zip(pairs, rows)
                 if g["expect"] == {"consistent"}
                 and (row.get("read") or {}).get("verdict") != "consistent")
    print(f"gate: confirmed-hallucinations judged consistent = {miss_h} (must be 0); "
          f"legit windows misread = {miss_l} (must be <=1)")
    return miss_h == 0 and miss_l <= 1


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--candidates", default=DEFAULT_CANDIDATES)
    ap.add_argument("--records", default=DEFAULT_RECORDS_GLOB)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--model", default=DEFAULT_READ_MODEL)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--limit", type=int, default=0, help="read only the first N candidates")
    ap.add_argument("--golden", action="store_true", help="calibrate on the confirmed cases only")
    ap.add_argument("--stage2-from", default="",
                    help="cascade mode: re-read only the hallucination/deception positives of a "
                         "prior verdicts file (stage-1 read kept as read_stage1)")
    args = ap.parse_args()

    if args.stage2_from:
        prior = [json.loads(l) for l in (REPO_ROOT / args.stage2_from).read_text().splitlines()
                 if l.strip()]
        candidates = [{**{k: v for k, v in r.items() if k not in ("read", "read_model")},
                       "read_stage1": r.get("read"), "read_stage1_model": r.get("read_model")}
                      for r in prior
                      if (r.get("read") or {}).get("verdict") in
                      ("hallucination", "deliberate_deception")]
    else:
        candidates = [json.loads(l) for l in (REPO_ROOT / args.candidates).read_text().splitlines()
                      if l.strip()]
        candidates = [c for c in candidates if c.get("row_type") == "candidate"]
    records_by_key = {(r["game_id"], r.get("config_name", "")): r
                      for r in load_batch_records(args.records)}

    if args.golden:
        passed = run_golden(candidates, records_by_key, args.model)
        raise SystemExit(0 if passed else 1)

    if args.limit:
        candidates = candidates[: args.limit]
    rows = read_candidates(candidates, records_by_key, args.model, workers=args.workers)
    out_path = REPO_ROOT / args.out
    with out_path.open("w") as fh:
        for r in rows:
            fh.write(json.dumps(r) + "\n")
    from collections import Counter
    verdicts = Counter((r.get("read") or {}).get("verdict", "READ_ERROR") for r in rows)
    print(json.dumps({"read": len(rows), "model": args.model,
                      "verdicts": dict(verdicts), "out": str(out_path.relative_to(REPO_ROOT))},
                     indent=2))


if __name__ == "__main__":
    main()
