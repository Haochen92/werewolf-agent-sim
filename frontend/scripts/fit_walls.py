"""
One-off: the station's walls behind the site's pages (owner, 2026-10-18), from the owner's
masters in claude_artifacts/design/rasters/landing/: the landing's navy wall (behind the story,
the features and the replay), the guide's green and the ticket office's brick. (The archive's
filing room was tried and set aside: the owner preferred the drawn tile room.) Each comes
wide (a screen wider than tall) and tall (a phone), each shipped as two
pieces: the picture itself, its lamp and all, for the top of the page, and a band of its lower
wall that repeats down as far as the page runs, so the wall never ends before the content does.

The band is the run of rows whose top and bottom match best (`best_band`), its slow drift of light
evened out, then laid upright and mirrored, so each join meets its own reflection and no seam
shows. Run from frontend/: `poetry run python scripts/fit_walls.py`
"""

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MASTERS = ROOT / "claude_artifacts/design/rasters/landing"
OUT = ROOT / "src/assets/site/walls"

# name: {shape: (master, the rows the band may come from, or None: no band, the wall fades out)}
# The band stays clear of the lamp: the navy phone wall's lamp hangs low, so its band is cut
# from the panels above it. The ticket office's lower wall is panelling and floor, which would
# stack if repeated: its picture fades out instead (its page is short).
WALLS = {
    "navy": {"wide": ("desktop_bluewall.png", (744, 1020)), "tall": ("mobile_bluewall.png", (130, 860))},
    "guide": {"wide": ("guide/desktop.png", (744, 1020)), "tall": ("guide/mobile.png", (700, 1370))},
    "office": {"wide": ("play/desktop.png", None), "tall": ("play/mobile.png", None)},
}
TAPER = 120  # the picture's last rows, blended into the band: its edge is darker than its middle

# the guide's green alone (owner, 2026-10-18): its wood and brass trim cut off the sides, the
# height cut to keep the picture's shape, then scaled back to its size (x0, x1 of the master)
CROP = {("guide", "wide"): (64, 1460), ("guide", "tall"): (52, 972)}

# the navy wall's lamp as its own piece, hung by the features' heading (owner, 2026-10-18): the
# rows round it (y0, y1), fading to clear at the top and the bottom over FADE rows, so the band
# behind shows through; the wall itself is the band alone
LAMP = {"wide": (230, 630), "tall": (760, 1130)}
FADE = 110


def best_band(a: np.ndarray, lo: int, hi: int, min_h: int) -> tuple[int, int, float]:
    """The rows (y0, y1) between lo and hi whose top and bottom match best, so the band repeats."""
    best = (1e9, lo, lo + min_h)
    for y0 in range(lo, hi - min_h, 4):
        for y1 in range(y0 + min_h, hi, 4):
            d = float(np.abs(a[y0] - a[y1]).mean())
            if d < best[0]:
                best = (d, y0, y1)
    return best[1], best[2], best[0]


def level(band: np.ndarray, reach: int = 61) -> np.ndarray:
    """The band's slow drift of light top to bottom (the picture's vignette) evened out, its
    grooves kept: each row scaled by its smoothed brightness against the band's, so the repeats
    meet without a step."""
    rows = band.mean(axis=(1, 2))
    pad = np.pad(rows, reach // 2, mode="wrap")
    smooth = np.convolve(pad, np.ones(reach) / reach, mode="valid")
    return band * (rows.mean() / smooth)[:, None, None]


def save(a: np.ndarray, path: Path) -> int:
    Image.fromarray(np.clip(a, 0, 255).astype(np.uint8), "RGB").save(path, "WEBP", quality=78, method=6)
    return path.stat().st_size // 1024


def crop(im: Image.Image, x0: int, x1: int) -> Image.Image:
    """Columns x0..x1, the rows cut from the foot to keep the shape, scaled back to its size."""
    w, h = im.size
    keep = round((x1 - x0) * h / w)
    return im.crop((x0, 0, x1, keep)).resize((w, h), Image.LANCZOS)


def lamp(a: np.ndarray, shape: str) -> None:
    y0, y1 = LAMP[shape]
    piece = a[y0:y1]
    alpha = np.full(len(piece), 255.0)
    ramp = np.linspace(0, 255, FADE)
    alpha[:FADE] = ramp
    alpha[-FADE:] = ramp[::-1]
    rgba = np.dstack([piece, np.broadcast_to(alpha[:, None], piece.shape[:2])])
    path = OUT / f"navy-{shape}-lamp.webp"
    Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA").save(
        path, "WEBP", quality=80, method=6
    )
    print(f"navy-{shape}-lamp: rows {y0}-{y1}, {path.stat().st_size // 1024} KB")


def fit(name: str, shape: str, master: str, rows: tuple[int, int] | None) -> None:
    im = Image.open(MASTERS / master).convert("RGB")
    if (name, shape) in CROP:
        im = crop(im, *CROP[(name, shape)])
    a = np.asarray(im).astype(np.float32)
    h, w = a.shape[:2]
    if name == "navy":
        lamp(a, shape)
    OUT.mkdir(parents=True, exist_ok=True)
    if rows is None:
        size = save(a, OUT / f"{name}-{shape}.webp")
        print(f"{name}-{shape}: {w}x{h}, {size} KB; no band")
        return
    # at least a quarter of the picture, so the repeat is not busy
    y0, y1, seam = best_band(a, rows[0], rows[1], h // 4)
    # upright then mirrored, so every join meets its own reflection: no seam at all
    band = level(a[y0:y1])
    band = np.concatenate([band, band[::-1]])
    # the picture's foot runs into the band's foot, which the band's top repeats
    top = a.copy()
    for r in range(TAPER):
        t = (r + 1) / TAPER
        top[h - TAPER + r] = (1 - t) * a[h - TAPER + r] + t * band[len(band) - TAPER + r]
    # the navy wall is its band alone, the lamp hung over it as its own piece
    size = save(top, OUT / f"{name}-{shape}.webp") if name != "navy" else 0
    bsize = save(band, OUT / f"{name}-{shape}-band.webp")
    print(
        f"{name}-{shape}: {w}x{h}, {size} KB; band rows {y0}-{y1} ({y1 - y0} px,"
        f" seam {seam:.1f}), {bsize} KB"
    )


if __name__ == "__main__":
    for old in OUT.glob("*.webp"):
        old.unlink()
    for name, shapes in WALLS.items():
        for shape, (master, rows) in shapes.items():
            fit(name, shape, master, rows)
