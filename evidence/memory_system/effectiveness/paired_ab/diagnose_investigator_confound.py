"""Town power-role probe follow-up (2026-06-12): is the investigator's apparent find-rate
DROP under town memory (wolf-find 0.43 -> 0.33 in the per-role probe) a real skill
regression, or a survival artifact?

The confound: town memory doubles investigator survival (13% -> 23%), so memory-investigators
check deeper into games where the wolf pool is already depleted — per-check hit rate falls
mechanically even at identical skill. Fix: luck-adjust each check against the random-check
expectation that night (wolves_before / (alive - 1)) and report LIFT = actual - expected.

Findings on first run (2026-06-12):
- Random expectation confirms the depletion: 0.250 baseline -> 0.208-0.228 in memory arms.
- Wolf-find LIFT is flat-to-up: +0.110 off vs +0.094 raw / +0.243 rr / +0.160 all-on.
- Threat-find (wolf OR SK) is stronger still: per-check raw rate is flat-to-up even WITHOUT
  adjustment (0.500 -> 0.508/0.597/0.554 — the probe's 0.56->0.46 was a per-game rate diluted
  by exposure), and LIFT rises in every memory arm (+0.123 off vs +0.163/+0.253/+0.209).
- Check VOLUME rises (1.67 -> ~2.0-2.2 checks/game); distinct wolves identified per game rises
  (0.60 -> 0.63 raw / 0.90 rr / 0.83 all-on) and distinct threats 0.83 -> 0.97/1.20/1.20 —
  total information delivered to town is UP.
- Verdict: the probe's "core job got worse" was the denominator artifact (same trap family as
  the kill-timing and conditioned-blending metrics). No town analog of the wolf/SK harm.
- Caveat: ~50-65 checks per arm -> binomial SE on lift ~±0.06-0.08; this refutes the
  regression claim, it does not establish an rr improvement.

    poetry run python evidence/memory_system/effectiveness/paired_ab/diagnose_investigator_confound.py
"""
from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]


def load(name):
    out = []
    for line in (REPO_ROOT / "batch_results" / f"{name}.jsonl").read_text().splitlines():
        if line.strip():
            r = json.loads(line)
            if r.get("status") == "success":
                out.append(r)
    return out


def main() -> None:
    arms = {
        "mem-OFF (baseline)": load("ab_baseline") + load("ab_baseline_recovered"),
        "town-mem (raw)": load("ab_arms_town"),
        "town-mem (rr)": load("ab_rr_town"),
        "all-on": load("ab_allon"),
    }
    seen: set = set()
    arms["mem-OFF (baseline)"] = [r for r in arms["mem-OFF (baseline)"]
                                  if not (r["game_id"] in seen or seen.add(r["game_id"]))]

    print(f"{'arm':20s} {'checks/g':>8s} | {'wolf-find':>9s} {'rand':>6s} {'LIFT':>7s} | "
          f"{'threat-find':>11s} {'rand':>6s} {'LIFT':>7s} | distinct wolf/g  threat/g")
    for label, recs in arms.items():
        checks = whits = thits = 0
        wexp = texp = 0.0
        dwolf = dthreat = 0
        for r in recs:
            fw: set = set()
            ft: set = set()
            for nr in r["night_resolutions"]:
                tgt = nr.get("investigator_target")
                if tgt is None:
                    continue
                role = nr.get("investigator_target_role")
                alive = nr["town_before"] + nr["wolves_before"] + nr["sk_before"]
                cand = max(alive - 1, 1)  # excludes self
                checks += 1
                wh = role == "wolf"
                th = role in ("wolf", "serial_killer")
                whits += wh
                thits += th
                wexp += nr["wolves_before"] / cand
                texp += (nr["wolves_before"] + nr["sk_before"]) / cand
                if wh:
                    fw.add(tgt)
                if th:
                    ft.add(tgt)
            dwolf += len(fw)
            dthreat += len(ft)
        n = len(recs)
        print(f"{label:20s} {checks/n:8.2f} | {whits/checks:9.3f} {wexp/checks:6.3f} "
              f"{whits/checks - wexp/checks:+7.3f} | {thits/checks:11.3f} {texp/checks:6.3f} "
              f"{thits/checks - texp/checks:+7.3f} | {dwolf/n:8.2f} {dthreat/n:9.2f}")


if __name__ == "__main__":
    main()
