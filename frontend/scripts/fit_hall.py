"""
One-off: the departures hall's pictures (owner, 2026-10-18), from the owner's masters in
claude_artifacts/design/rasters/wood/rooms/: the night platform's bench (a wide one for a screen
wider than tall, a tall one for a phone), the same wall with nobody on it (a landscape screen too
narrow for the bench beside the board, which puts the bench after it) and the departures board, cut in three so it grows with
the rooms: the head (the brass plate, the clock, the plaque), a middle that repeats down, the foot.
(board-middle.png, the owner's middle piece, is not used: its outer rim is ragged.)

The board's masters were cut out of a background, and their edges carry a fringe of it (a red
halo, ~1,000 px on the head): every part-transparent pixel takes the colour of the solid frame
beside it. Each board's middle is a band of its own head's sides, so the two meet without a
step; a foot's rims are a few px thinner, so its top tapers into them. A phone's board has its own head,
whose rims are thinner, and its foot is the desktop's, scaled to the phone's rims and its middle
taken out.

The text on the plate and the plaque is live: the boxes it sits in are printed in percent of the
head, for Departures.module.css.

Run from frontend/: `poetry run python scripts/fit_hall.py`
"""

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MASTERS = ROOT / "claude_artifacts/design/rasters/wood/rooms"
OUT = ROOT / "src/assets/site"

# the desktop board: one column range for all three pieces, the head cut where its sides run
# straight, the foot where its inner corners begin to turn
DESK_X = (24, 2148)
HEAD_Y = (40, 380)
FOOT_Y = (440, 620)
DESK_BAND = (390, 672)  # the head's straight sides under its cut, the band the middle repeats
DESK_W = 1600  # shown ~1000 css px wide

# the phone's board: its head, and the band of its sides the middle repeats from
PHONE_X = (20, 1428)
PHONE_HEAD_Y = (55, 380)
PHONE_BAND = (450, 1000)
PHONE_W = 1080  # shown 340-400 css px wide, at a phone's 3x

# the live text's boxes in the masters (x0, y0, x1, y1)
DESK_BOXES = {"plate": (134, 204, 876, 291), "plaque": (1627, 201, 2037, 292)}
PHONE_BOXES = {"plate": (107, 196, 600, 281), "plaque": (962, 194, 1340, 283)}


def rgba(name: str) -> np.ndarray:
    return np.asarray(Image.open(MASTERS / name).convert("RGBA")).astype(np.float32)


def box(x: np.ndarray, axis: int, r: int = 6) -> np.ndarray:
    """A (2r+1)-wide box sum along one axis, the edges padded with zero."""
    c = np.cumsum(np.pad(x, [(r + 1, r) if i == axis else (0, 0) for i in range(2)]), axis)
    n = x.shape[axis]
    return np.take(c, range(2 * r + 1, 2 * r + 1 + n), axis) - np.take(c, range(n), axis)


def defringe(a: np.ndarray) -> np.ndarray:
    """Every part-transparent pixel takes the colour of the solid pixels round it."""
    solid = (a[..., 3] >= 250).astype(np.float32)
    rgb = a[..., :3] * solid[..., None]
    blur = lambda x: box(box(x, 0), 1)  # noqa: E731
    wsum = blur(solid)
    fill = np.stack([blur(rgb[..., c]) for c in range(3)], -1) / np.maximum(wsum, 1e-3)[..., None]
    edge = (a[..., 3] < 250) & (wsum > 1e-3)
    out = a.copy()
    out[..., :3][edge] = fill[edge]
    # a speck with no solid frame near it is background left behind
    out[..., 3][(a[..., 3] < 250) & (wsum <= 1e-3)] = 0
    return out


def best_band(a: np.ndarray, lo: int, hi: int, min_h: int) -> tuple[int, int]:
    """The rows (y0, y1) between lo and hi whose top and bottom match best, so the band repeats."""
    best = (1e9, lo, lo + min_h)
    for y0 in range(lo, hi - min_h, 4):
        for y1 in range(y0 + min_h, hi, 4):
            d = np.abs(a[y0] - a[y1])[..., :3].mean()
            if d < best[0]:
                best = (d, y0, y1)
    print(f"  band {best[1]}-{best[2]}, seam {best[0]:.2f}")
    return best[1], best[2]


def taper(foot: np.ndarray, band: np.ndarray, rows: int = 40) -> np.ndarray:
    """The foot's top rows blended from the middle's sides into its own: its rims are a few px
    thinner, and a step where the middle stops would show."""
    out = foot.copy()
    for r in range(rows):
        t = r / rows
        out[r] = (1 - t) * band[r % band.shape[0]] + t * foot[r]
    return out


def save(a: np.ndarray, name: str, width: int) -> None:
    im = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGBA")
    h = round(im.height * width / im.width)
    im = im.resize((width, h), Image.LANCZOS)
    path = OUT / name
    im.save(path, "WEBP", quality=82, method=6)
    print(f"{name}: {width}x{h}, {path.stat().st_size // 1024} KB")


def boxes(boxes: dict, x0: int, y0: int, w: int, h: int) -> None:
    for name, (bx0, by0, bx1, by1) in boxes.items():
        print(
            f"  {name}: left {100 * (bx0 - x0) / w:.2f}% top {100 * (by0 - y0) / h:.2f}%"
            f" width {100 * (bx1 - bx0) / w:.2f}% height {100 * (by1 - by0) / h:.2f}%"
        )


def desktop() -> None:
    (x0, x1), w = DESK_X, DESK_X[1] - DESK_X[0]
    master = defringe(rgba("board-head.png"))
    save(master[HEAD_Y[0] : HEAD_Y[1], x0:x1], "board-head.webp", DESK_W)
    boxes(DESK_BOXES, x0, HEAD_Y[0], w, HEAD_Y[1] - HEAD_Y[0])
    # the middle master's outer rim is ragged from its cut-out: the head's own sides run straight
    # below its cut, so the middle repeats a band of those, the same wood and gold as the head
    y0, y1 = best_band(master, *DESK_BAND, 200)
    save(master[y0:y1, x0:x1], "board-middle.webp", DESK_W)
    foot = defringe(rgba("board-foot.png"))[FOOT_Y[0] : FOOT_Y[1], x0:x1]
    save(taper(foot, master[y0:y1, x0:x1]), "board-foot.webp", DESK_W)


def phone() -> None:
    (x0, x1), w = PHONE_X, PHONE_X[1] - PHONE_X[0]
    master = defringe(rgba("board-phone-head.png"))
    save(master[PHONE_HEAD_Y[0] : PHONE_HEAD_Y[1], x0:x1], "board-phone-head.webp", PHONE_W)
    boxes(PHONE_BOXES, x0, PHONE_HEAD_Y[0], w, PHONE_HEAD_Y[1] - PHONE_HEAD_Y[0])
    y0, y1 = best_band(master, *PHONE_BAND, 240)
    save(master[y0:y1, x0:x1], "board-phone-middle.webp", PHONE_W)

    # the desktop foot at 0.8, each half moved onto the phone's rims: its inner gold line at
    # x 106 / 2066 to the phone's 78 / 1365.5, its outer edge landing within 2 px of the phone's
    s = 0.8
    foot = defringe(rgba("board-foot.png"))[FOOT_Y[0] : FOOT_Y[1]]
    fh = round(foot.shape[0] * s)
    small = Image.fromarray(np.clip(foot, 0, 255).astype(np.uint8), "RGBA").resize(
        (round(foot.shape[1] * s), fh), Image.LANCZOS
    )
    out = Image.new("RGBA", (master.shape[1], fh), (0, 0, 0, 0))
    half = master.shape[1] // 2
    left = small.crop((0, 0, half + 7, fh))
    out.paste(left, (-7, 0))
    right_from = round(half + 287.3)
    out.paste(small.crop((right_from, 0, small.width, fh)), (half, 0))
    foot = np.asarray(out).astype(np.float32)[:, x0:x1]
    save(taper(foot, master[y0:y1, x0:x1]), "board-phone-foot.webp", PHONE_W)


def scenes() -> None:
    for src, name in (
        ("hall-wide.png", "hall-wide.webp"),
        ("hall-tall.png", "hall-tall.webp"),
        ("wall-empty-wide.png", "hall-wall.webp"),
    ):
        im = Image.open(MASTERS / src).convert("RGB")
        im.save(OUT / name, "WEBP", quality=80, method=6)
        print(f"{name}: {im.width}x{im.height}, {(OUT / name).stat().st_size // 1024} KB")


if __name__ == "__main__":
    scenes()
    desktop()
    phone()
