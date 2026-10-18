"""AC2 current/before_note re-sampled with the closing call in today's wording (no accuser list).

Record: evidence/reasoning_failures/data/deduction_ac2_closing_fixed/ (README there). Generation only.
A sibling of deduction_ac2_2x2.py: one arm of that 2x2 (block "current", placement "before_note"),
rendered fresh from the tree, where the replay bench now rewrites the old closing call to today's
("Before the vote: player_8 gets a last word."). Before any call the render is checked to differ from
the 2x2's saved prompt in that line only. The 2x2 runner's ``run`` / ``count`` are reused unchanged,
pointed at this folder with one arm, n=25 and a 30-call cap.

  poetry run python evaluation/experiments/deduction_ac2_closing_fixed.py --render-only
  LANGFUSE_TRACING_ENABLED=false GOOGLE_GENAI_MODEL=anthropic/claude-haiku-5-5 GOOGLE_GENAI_THINKING_LEVEL=low \
    GAME_LLM_ATTEMPTS=1 GAME_LLM_TIMEOUT_S=180 poetry run python evaluation/experiments/deduction_ac2_closing_fixed.py --run
  poetry run python evaluation/experiments/deduction_ac2_closing_fixed.py --count
"""

from __future__ import annotations

import argparse
import difflib
import json

from evaluation.experiments import deduction_ac2_2x2 as x2
from evaluation.experiments import deduction_placement_screen as screen

OUT = screen.DATA / "deduction_ac2_closing_fixed"
X2_PROMPTS = x2.OUT / "prompts"
OLD_LINE = ("game_master: Before the vote: player_8 has been accused by player_2, player_5 and player_4. "
            "player_8 gets a last word.")
NEW_LINE = "game_master: Before the vote: player_8 gets a last word."

# the 2x2 runner, pointed at this run: one arm, n=25, cap 30 (module globals its functions read)
x2.OUT, x2.BLOCKS, x2.ARMS, x2.N, x2.MAX_CALLS = OUT, {"current": ()}, [("current", "before_note")], 25, 30


def render() -> dict:
    name, source, case_id, fields, _ = next(c for c in screen.CASES if c[0] == "AC2")
    t = screen._turn(name, source, case_id, fields, "before_note")
    old_human = (X2_PROMPTS / "AC2_current_before_note.txt").read_text()
    old_system = (X2_PROMPTS / "system.txt").read_text()
    diff = list(difflib.unified_diff(old_human.splitlines(), t["human"].splitlines(),
                                     "deduction_ac2_2x2/prompts/AC2_current_before_note.txt",
                                     "rendered", lineterm="", n=0))
    changed = [d for d in diff if d[:1] in "+-" and not d.startswith(("+++", "---"))]
    check = {
        "new_call_present": t["human"].count("Before the vote: player_8 gets a last word.") == 1,
        "no_accused_by": "has been accused by" not in t["human"],
        "system_equals_2x2": t["system"] == old_system,
        "only_closing_line_differs": changed == [f"-{OLD_LINE}", f"+{NEW_LINE}"],
        "human_equals_2x2_with_line_swapped": t["human"] == old_human.replace(OLD_LINE, NEW_LINE, 1),
        "diff_vs_2x2": diff,
        "human_chars": len(t["human"]), "human_sha256": x2._sha(t["human"]),
        "system_chars": len(t["system"]), "system_sha256": x2._sha(t["system"]),
    }
    check["all_ok"] = all(v for k, v in check.items() if k in (
        "new_call_present", "no_accused_by", "system_equals_2x2", "only_closing_line_differs",
        "human_equals_2x2_with_line_swapped"))
    print(json.dumps(check, indent=1))
    if not check["all_ok"]:
        raise SystemExit("verification failed: prompt differs from the 2x2's beyond the closing line; "
                         "nothing saved, no model call made")
    (OUT / "prompts").mkdir(parents=True, exist_ok=True)
    (OUT / "prompts" / "system.txt").write_text(t["system"])
    (OUT / "prompts" / "AC2_current_before_note.txt").write_text(t["human"])
    (OUT / "prompt_check.json").write_text(json.dumps(check, indent=1) + "\n")
    return {"turn": t, "case_id": case_id}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--render-only", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--count", action="store_true")
    args = parser.parse_args()
    if args.count:
        x2.count()
        return
    rendered = render()
    if args.run:
        if (OUT / "samples.jsonl").exists():
            raise SystemExit("samples.jsonl exists: this runner makes one run only")
        x2.run(rendered)


if __name__ == "__main__":
    main()
