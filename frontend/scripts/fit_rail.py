"""
One-off: the seat rail's pictures (owner, 2026-10-18), from the owner's masters in
claude_artifacts/design/rasters/wood/kit/: the rail's walnut frame with its brass brackets and
burgundy piping and the brass plate the rail's instruction is lettered on, both drawn as CSS
border-image 9-slices (Wing.module.css), so each is cut to the size its border shows at a
desktop's density, never the size of the box it frames: the middles stretch. The frame's hole is
not drawn (no `fill`), so what the master left inside it does not matter; the rims are
defringed. And the cream paper the seat cards are printed on, a tile (the owner's warm cream). (The cards' own walnut
frames were tried and dropped the same day: the owner wanted the cards unframed.) And the
cards' shadow on the velvet, baked, so no blur is computed when a card repaints.

The slice numbers printed are the border-image slices, in the output's pixels.

Run from frontend/: `poetry run python scripts/fit_rail.py`
"""

from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from fit_hall import defringe

ROOT = Path(__file__).resolve().parents[1]
MASTERS = ROOT / "claude_artifacts/design/rasters/wood/kit"
OUT = ROOT / "src/assets/sprites/rail"

# (master, output, the master's crop (x0, y0, x1, y1) or None, its slice in master px, output width)
PIECES = [
    # the rail's frame: the walnut is 53 px of the master's 724; a 100 px slice holds the brackets
    ("rail-frame.png", "frame.webp", None, 100, 384),
    # the plate, cropped to the brass: its rounded ends and rivets are the slice (left and right)
    ("brass-plate.png", "plate.webp", (66, 185, 2106, 515), 170, 495),
]


def fit(master: str, name: str, crop, slice_px: int, width: int) -> None:
    a = np.asarray(Image.open(MASTERS / master).convert("RGBA")).astype(np.float32)
    if crop:
        x0, y0, x1, y1 = crop
        a = a[y0:y1, x0:x1]
    a = defringe(a)
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    h = round(im.height * width / im.width)
    im = im.resize((width, h), Image.LANCZOS)
    OUT.mkdir(parents=True, exist_ok=True)
    im.save(OUT / name, "WEBP", quality=82, method=6)
    k = width / a.shape[1]
    print(
        f"{name}: {width}x{h}, {(OUT / name).stat().st_size // 1024} KB, "
        f"slice {round(slice_px * k)} px, decoded {width * h * 4 / 2**20:.2f} MB"
    )


def paper() -> None:
    # the cards' cream, a seamless tile shown 128 units across: two pixels a unit on a desktop
    im = Image.open(MASTERS / "card-paper.png").convert("RGB").resize((256, 256), Image.LANCZOS)
    im.save(OUT / "paper.webp", "WEBP", quality=82, method=6)
    print(f"paper.webp: 256x256, {(OUT / 'paper.webp').stat().st_size // 1024} KB, decoded 0.25 MB")


def shadow() -> None:
    # a 9-slice drawn round a card by border-image-outset (Wing.module.css `.tile`): a 64 px card
    # in a 128 px square, its shadow 3 px down and 2 right, blurred 8; at 2 px a unit the slice is
    # 32 px, the outset 16 units. The middle, the card itself, is never drawn.
    a = Image.new("L", (128, 128), 0)
    ImageDraw.Draw(a).rounded_rectangle((32 + 4, 32 + 6, 96 + 4, 96 + 6), radius=6, fill=150)
    a = a.filter(ImageFilter.GaussianBlur(8))
    im = Image.new("RGBA", (128, 128), (30, 15, 5, 0))
    im.putalpha(a)
    im.save(OUT / "shadow.webp", "WEBP", quality=90, method=6)
    print(f"shadow.webp: 128x128, {(OUT / 'shadow.webp').stat().st_size // 1024} KB, slice 32 px")


if __name__ == "__main__":
    for piece in PIECES:
        fit(*piece)
    paper()
    shadow()
