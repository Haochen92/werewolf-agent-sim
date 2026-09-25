# Werewolf Playhouse: design bundle for the codebase

Start with `HANDOFF.md`. It is the specification; everything else here is the evidence behind it.

The benches in `benches/` are self-contained HTML pages: no build step, no network beyond Google Fonts. Open one in a browser, or from Claude Code render it headless to compare a beat against what you have built:

```bash
pip install playwright && python -m playwright install chromium
python - <<'PY'
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={'width': 1400, 'height': 900})
    pg.goto('file:///ABSOLUTE/PATH/benches/rev-73-game-over.html'); pg.wait_for_timeout(1500)
    # every bench exposes its state as `st` and redraws with drawMain(animate)
    pg.evaluate("st.viewer='xray'; st.beat=5; st.motion='0'; drawMain(false);"); pg.wait_for_timeout(400)
    pg.locator('#main').screenshot(path='rev-73-beat-5.png'); b.close()
PY
```

Each bench has controls at the top (viewer, fixture, frame, motion), a stepper for its beats, a caption under the stage that names the wire event driving the beat and who sees what, and a "How we got here" section at the foot with the decisions made on it. Bench pages carry the kits inline; the same kits are standalone in `kits/`.

Sprites are decoded in `sprites/`; `sprites/manifest.json` gives each file's size and, for the day figures, the `body` measure (`top` and `body` as fractions of the image height) the cast module scales from. The `castForGame(gameId)` mapping of seats to characters is in `kits/puppet-kit.js`.

The game fixture used throughout is game 9369a5c1 (memory on), available in the project's replay store as `replay_memory_on_2026-09-17_9369a5c1.json`; bench 74 carries its public and observer transcript as data.
