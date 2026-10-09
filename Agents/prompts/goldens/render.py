"""Write the rendered rules block into this folder, for two lineups that between them deal every
role once.

Run on purpose after editing a role's words: ``poetry run python -m Agents.prompts.goldens.render``.
The test ``tests/engine/test_game_rules_render.py`` fails when the composed text and the rendered
file differ, so a wording change always shows up as a diff in English.
"""

from __future__ import annotations

from pathlib import Path

from Agents.prompts.compose import rules_block
from Agents.schemas.roles import lineup

RENDERED_DIR = Path(__file__).parent

CASTS = {
    "rules_serial_killer_speculator.txt": lineup("serial_killer", "speculator"),
    "rules_necromancer_fortune_teller.txt": lineup("necromancer", "fortune_teller"),
}


def main() -> None:
    for filename, cast in CASTS.items():
        path = RENDERED_DIR / filename
        path.write_text(rules_block(cast) + "\n")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
