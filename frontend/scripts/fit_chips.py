"""
One-off: the ballot chips as pictures (owner, 2026-10-18), from the owner's masters in
claude_artifacts/design/rasters/live_ugrade/. So far the hidden chip: navy wood, a cream stitch
round its face, back up in the jar (VoteChip.tsx `FlatChip` without a face). A chip face up keeps
its vector drawing.

The master is seen a little higher than the table (its face's height is 0.46 of its width, the
table's chips 0.42), so it is squashed to 0.42 here and code places it by its face's centre and
radius. Its edge comes out at 0.21 of the radius, the jar's own chips' 0.20.

Two copies, each the largest it is drawn: the jar's chip is 43.8 units in radius and the camera
never pushes in on the jar (at the count it stands aside at 0.6), so ~175 px across on a
1600 px desktop stage at density 2 (192), ~125 on a phone (128).

Run from frontend/: `poetry run python scripts/fit_chips.py`
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MASTERS = ROOT / "claude_artifacts/design/rasters/live_ugrade"
OUT = ROOT / "src/assets/sprites/props"

# the hidden chip's master, measured: its bounding box, and its face's top and near rim on the
# centre column (where the face's light gives way to the side's shade)
HIDDEN = {"file": "hidden-chip-navy.png", "box": (384, 233, 1331, 775), "face": (233, 666)}
TILT = 0.42
SIZES = {"chip-hidden.webp": 192, "chip-hidden@small.webp": 128}


def hidden() -> None:
    x0, y0, x1, y1 = HIDDEN["box"]
    im = Image.open(MASTERS / HIDDEN["file"]).convert("RGBA").crop((x0 - 2, y0 - 2, x1 + 2, y1 + 2))
    rx = (x1 - x0) / 2
    face_top, face_bot = HIDDEN["face"]
    squash = TILT * rx / ((face_bot - face_top) / 2)
    im = im.resize((im.width, round(im.height * squash)), Image.LANCZOS)
    # where the face's centre falls, and the picture's height, both in radii from its top-left
    cy = ((face_top + face_bot) / 2 - (y0 - 2)) * squash / rx
    print(f"squash {squash:.3f}: width {im.width / rx:.4f} r, height {im.height / rx:.4f} r, "
          f"face centre {(im.width / 2) / rx:.4f} r across, {cy:.4f} r down")
    for name, width in SIZES.items():
        out = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        out.save(OUT / name, "WEBP", quality=85, method=6)
        print(f"{name}: {out.width}x{out.height}, {(OUT / name).stat().st_size // 1024} KB")


if __name__ == "__main__":
    hidden()
