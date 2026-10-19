"""
One-off: the ballot chips as pictures (owner, 2026-10-18), from the owner's masters in
claude_artifacts/design/rasters/live_ugrade/: the hidden chip, navy wood, a cream stitch round its
face, back up in the jar (VoteChip.tsx `FlatChip` without a face); and the counted chip's body, a
maple ring the voter's face is inlaid in, on the plates' towers (2026-10-19). A chip face up in the
jar keeps its vector drawing.

The master is seen a little higher than the table (its face's height is 0.46 of its width, the
table's chips 0.42), so it is squashed to 0.42 here and code places it by its face's centre and
radius. Its edge comes out at 0.21 of the radius, the jar's own chips' 0.20.

Two copies, each the largest it is drawn: the jar's chip is 43.8 units in radius and the camera
never pushes in on the jar (at the count it stands aside at 0.6), so ~175 px across on a
1600 px desktop stage at density 2 (192), ~125 on a phone (128).

The ring is seen lower than the table (its top's height 0.295 of its width, its edge 0.30 of its
radius), so it is stretched to 0.42, which brings its edge to 0.42, the towers' step. A tower's
chip is at most 54.8 units in radius, and the count's camera comes in to 1.32: ~290 px across at
density 2 (288), 192 on a phone.

The plate the towers stand on is pewter (2026-10-19, for the white cloth and the maple chips), in
the cream plate's file: its outer rim fills the box, squashed to the table's 0.3, so the code is
unchanged; then `node scripts/small-sprites.mjs props/plate` for the phone's copy.

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
# the ring's master, measured: its bounding box, and on the centre column its top's near rim (where
# the top's light gives way to the side's shade) and the hole's near rim
RING = {"file": "chip-ring-maple.png", "box": (77, 96, 1694, 816), "top_near": 574, "hole_near": 504}
RING_SIZES = {"chip-ring.webp": 288, "chip-ring@small.webp": 192}
# the plate's master and its bounding box; written at the cream plate's size
PLATE = {"file": "chip-plate-pewter.png", "box": (0, 0, 2172, 700), "size": (900, 270)}


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


def ring() -> None:
    x0, y0, x1, y1 = RING["box"]
    im = Image.open(MASTERS / RING["file"]).convert("RGBA").crop((x0 - 2, y0 - 2, x1 + 3, y1 + 3))
    rx = (x1 - x0 + 1) / 2
    top_cy = (y0 + RING["top_near"]) / 2
    stretch = TILT * rx / (RING["top_near"] - top_cy)
    # the hole: across, the clear run round the centre on the top's centre row; down, its near rim
    a = Image.open(MASTERS / RING["file"]).getchannel("A")
    row, mid = round(top_cy), (x0 + x1) // 2
    left = next(x for x in range(mid, x0, -1) if a.getpixel((x, row)) > 128)
    right = next(x for x in range(mid, x1) if a.getpixel((x, row)) > 128)
    hole_rx, hole_ry = (right - left) / 2, RING["hole_near"] - top_cy
    im = im.resize((im.width, round(im.height * stretch)), Image.LANCZOS)
    cy = (top_cy - (y0 - 2)) * stretch / rx
    print(f"stretch {stretch:.3f}: width {im.width / rx:.4f} r, height {im.height / rx:.4f} r, "
          f"top centre {(mid - (x0 - 2)) / rx:.4f} r across, {cy:.4f} r down; edge "
          f"{(y1 - RING['top_near']) * stretch / rx:.3f} r; hole {hole_rx / rx:.4f} r "
          f"(its depth {hole_ry * stretch / hole_rx:.3f} of its width)")
    for name, width in RING_SIZES.items():
        out = im.resize((width, round(im.height * width / im.width)), Image.LANCZOS)
        out.save(OUT / name, "WEBP", quality=85, method=6)
        print(f"{name}: {out.width}x{out.height}, {(OUT / name).stat().st_size // 1024} KB")


def plate() -> None:
    im = Image.open(MASTERS / PLATE["file"]).convert("RGBA").crop(PLATE["box"])
    im.resize(PLATE["size"], Image.LANCZOS).save(OUT / "plate.webp", "WEBP", quality=85, alpha_quality=100, method=6)
    print(f"plate.webp: {PLATE['size']}, {(OUT / 'plate.webp').stat().st_size // 1024} KB")


if __name__ == "__main__":
    hidden()
    ring()
    plate()
