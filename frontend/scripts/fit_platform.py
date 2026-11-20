"""
One-off: the platform is the owner's one picture (2026-10-19), from
claude_artifacts/design/rasters/live_ugrade/platform.png: the roof's beam, two stone pillars with
their lanterns, the low stone ledge and the paving, the night country through the arches.

The train stands in the arches, behind the pillars, the beam and the ledge, as it stood behind
the old lamp posts. So the picture ships twice at the same size:
- `platform.webp`, whole: the back.
- `platform-front.webp`, the beam, the pillars and the ledge with the paving, the rest clear: drawn
  over the train. The beam is the rows above `BEAM`, the ledge and paving the rows below `LEDGE`;
  between them the snow line is kept where it is not the night (`EDGE`). The pillars are the warm
  pixels in their boxes (the night is near black blue, its red under 25), only the largest piece
  in each box, so a lantern's halo on the sky or a far cabin's lit window does not come along.

Run from frontend/: `poetry run python scripts/fit_platform.py`
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter
from scipy import ndimage

ROOT = Path(__file__).resolve().parents[1]
MASTER = ROOT / "claude_artifacts/design/rasters/live_ugrade/platform.png"
OUT = ROOT / "src/assets/sprites/station"

# rows, in the master's pixels: the beam's foot, the snow line on the ledge, the ledge's top
BEAM, EDGE, LEDGE = 138, 550, 590
# the pillars' boxes (x0, x1), from the beam's brackets down to the ledge
PILLARS = ((175, 405), (1265, 1505))
PILLAR_Y = (60, 600)


def main() -> None:
    im = Image.open(MASTER).convert("RGB")
    a = np.asarray(im).astype(float)
    h, w = a.shape[:2]
    r, b = a[..., 0], a[..., 2]
    lum = a.mean(axis=2)
    warm = ((r > 25) & (r > 0.8 * b)) | ((lum > 150) & (r > 150))

    keep = np.zeros((h, w), bool)
    keep[:BEAM] = True
    keep[LEDGE:] = True
    keep[EDGE:LEDGE] |= ((r > 110) | ((r > 25) & (r > 0.6 * b)))[EDGE:LEDGE]
    for x0, x1 in PILLARS:
        box = np.zeros((h, w), bool)
        box[PILLAR_Y[0] : PILLAR_Y[1], x0:x1] = True
        # opened first: a far cabin touching a pillar by a thread of lantern glow comes apart
        parts, n = ndimage.label(ndimage.binary_opening(box & warm, iterations=3))
        if n:
            sizes = ndimage.sum(np.ones_like(parts), parts, range(1, n + 1))
            # the pillar whole: the dark seams in its stone are its own, not the night
            keep |= ndimage.binary_fill_holes(parts == 1 + int(np.argmax(sizes)))

    alpha = Image.fromarray((keep * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
    front = im.convert("RGBA")
    front.putalpha(alpha)
    im.save(OUT / "platform.webp", "WEBP", quality=80, method=6)
    front.save(OUT / "platform-front.webp", "WEBP", quality=80, alpha_quality=90, method=6)
    for f in ("platform.webp", "platform-front.webp"):
        print(f"{f}: {w}x{h}, {(OUT / f).stat().st_size // 1024} KB, decoded {w * h * 4 / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
