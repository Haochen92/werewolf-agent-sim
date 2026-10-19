"""
One-off: the input HUDs' and the transcript's materials (owner, 2026-10-19), from the masters in
claude_artifacts/design/rasters/live_ugrade/: the riveted bronze frame round a panel, the dark and
the light brushed bronze, and the cream paper.

- The frame (`frame-bronze.png`, transparent in and out) is cut to its box, its four riveted
  corners kept and each side shortened to a strip (a border image stretches the sides anyway), at
  half the master's pixels: a 9-slice of `SLICE` px a corner.
- The bronzes are brushed across, so their tiles meet badly side to side: the last `BLEND` columns
  are faded into the first before the cut, and the tile repeats without a seam. Top to bottom they
  already do.
- The paper repeats as it is.

Run from frontend/: `poetry run python scripts/fit_hud_kit.py [out_dir]`
"""

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MASTERS = ROOT / "claude_artifacts/design/rasters/live_ugrade"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "src/assets/sprites/hud"

# the frame, measured: its opaque box, and a corner's size (the rivet's block and the bar's mitre)
FRAME = {"box": (29, 42, 1094, 1358), "corner": 100, "side": 60}
SLICE = FRAME["corner"] // 2
TILE, BLEND = 512, 96


def frame() -> None:
    x0, y0, x1, y1 = FRAME["box"]
    im = Image.open(MASTERS / "frame-bronze.png").convert("RGBA").crop((x0, y0, x1, y1))
    w, h = im.size
    c, s = FRAME["corner"], FRAME["side"]
    # the corners, and a strip from the middle of each side
    out = Image.new("RGBA", (2 * c + s, 2 * c + s))
    mx, my = (w - s) // 2, (h - s) // 2
    for ox, sx in ((0, 0), (c, mx), (c + s, w - c)):
        for oy, sy in ((0, 0), (c, my), (c + s, h - c)):
            pw = s if ox == c else c
            ph = s if oy == c else c
            out.paste(im.crop((sx, sy, sx + pw, sy + ph)), (ox, oy))
    out = out.resize((out.width // 2, out.height // 2), Image.LANCZOS)
    out.save(OUT / "frame.webp", "WEBP", quality=88, alpha_quality=100, method=6)
    print(f"frame.webp: {out.size}, slice {SLICE}, {(OUT / 'frame.webp').stat().st_size // 1024} KB")


def tile(src: str, name: str, seamless: bool) -> None:
    a = np.asarray(Image.open(MASTERS / src).convert("RGB")).astype(float)
    if seamless:
        w = a.shape[1] - BLEND
        t = np.linspace(0, 1, BLEND)[None, :, None]
        head = a[:, :BLEND] * t + a[:, w:] * (1 - t)
        a = np.concatenate([head, a[:, BLEND:w]], axis=1)
    im = Image.fromarray(a.round().clip(0, 255).astype(np.uint8)).resize((TILE, TILE), Image.LANCZOS)
    im.save(OUT / name, "WEBP", quality=82, method=6)
    g = np.asarray(im.convert("L")).astype(float)
    print(f"{name}: {im.size}, {(OUT / name).stat().st_size // 1024} KB, seam {abs(g[:, 0] - g[:, -1]).mean():.2f} "
          f"(neighbours {abs(g[:, 0] - g[:, 1]).mean():.2f})")


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    frame()
    tile("bronze-dark.png", "bronze-dark.webp", True)
    tile("bronze-light.png", "bronze-light.webp", True)
    tile("paper-cream.png", "paper.webp", False)
