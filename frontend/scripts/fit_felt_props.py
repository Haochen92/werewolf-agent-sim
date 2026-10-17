"""One-off: fit the owner's felt prop set (2026-10-17, ChatGPT masters) to the stage's props.

Reads the cleaned masters in claude_artifacts/design/rasters/felt/ and writes the WebP files the
build ships to src/assets/sprites/props/, under the names the old set had, so the manifest is
unchanged. Each picture is sized so its pixel count is at or under the file it replaces (a phone
holds the same decoded memory), and prints the measured lines the code needs (stage_architecture
§4 "The felt set"). The glass pair are cut from shots on black (`glass()`): alpha from brightness,
colour a warm white, so they read as lamp-lit glass over anything.

Run from frontend/: `poetry run python scripts/fit_felt_props.py`; then
`node scripts/small-sprites.mjs` for the phone copies.
"""

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
MASTERS = ROOT / 'claude_artifacts/design/rasters/felt'
OUT = ROOT / 'src/assets/sprites/props'
LUMA = np.array([0.2126, 0.7152, 0.0722])
WARM = np.array([1.0, 0.92, 0.80])
# the set it replaces (git has the files): size, and mean brightness where it was judged in place
OLD = {
    'stand-front.webp': ((1525, 429), 32.9),
    'vote-table.webp': ((1536, 295), 140.1),
    'shutter.webp': ((1640, 615), 31.6),
}


def resize(im: Image.Image, w: int, h: int) -> Image.Image:
    """Premultiplied resize, so no colour bleeds in from under transparent pixels."""
    return im.convert('RGBa').resize((w, h), Image.LANCZOS).convert('RGBA')


def area_cap(w: float, h: float, old: str) -> float:
    """The scale that keeps w×h at or under the old file's pixel count (1 if already under)."""
    ow, oh = OLD[old][0]
    return min(1.0, (ow * oh / (w * h)) ** 0.5)


def mean_luma(im: Image.Image) -> float:
    a = np.asarray(im.convert('RGBA')).astype(float)
    solid = a[..., 3] > 200
    return float((a[..., :3][solid] @ LUMA).mean())


def match_luma(im: Image.Image, old: str) -> Image.Image:
    """Darken (never brighten) to the old picture's mean, which was judged in place."""
    k = min(1.0, OLD[old][1] / mean_luma(im))
    a = np.asarray(im).astype(float)
    a[..., :3] *= k
    print(f'  {old}: darkened ×{k:.3f}')
    return Image.fromarray(a.round().astype(np.uint8), 'RGBA')


# the felt fronts compress poorly (fibre noise); at 75 only the fibres soften (bench 2026-10-17)
QUALITY = {'stand-front.webp': 75, 'shutter.webp': 75}


def save(im: Image.Image, name: str) -> None:
    im.save(OUT / name, 'WEBP', quality=QUALITY.get(name, 85), alpha_quality=100, method=6)
    print(f'  {name}: {im.size[0]}×{im.size[1]}, {(OUT / name).stat().st_size / 1024:.0f} KB')


def stand() -> None:
    """The podium front: the body (the stiles' outer edges) is 605u, as the old one's was."""
    im = Image.open(MASTERS / 'stand-front.png')
    body = (60, 2051)  # the stiles' outer edges, master px
    lines = {'top': 240, 'bottom': 420, 'left': 300, 'right': 1810, 'rail': 5, 'foot': 616}
    s = 0.7454 * area_cap(im.width * 0.7454, im.height * 0.7454, 'stand-front.webp')
    w, h = round(im.width * s), round(im.height * s)
    out = match_luma(resize(im, w, h), 'stand-front.webp')
    save(out, 'stand-front.webp')
    u = 605 / ((body[1] - body[0]) * s)  # puppet units a pixel
    px = {k: round(v * s) for k, v in lines.items()}
    print(f'  u/px {u:.6f}; slices top {px["top"]} right {w - px["right"]} bottom {h - px["bottom"]} '
          f'left {px["left"]}; box offsets left {body[0] * s * u:.3f}u right {(im.width - body[1]) * s * u:.3f}u '
          f'top {px["rail"] * u:.3f}u bottom {(h - px["foot"]) * u:.3f}u')


def table() -> None:
    im = Image.open(MASTERS / 'vote-table.png')
    lines = {'back': 8, 'front': 70, 'left': 13, 'right': 2050, 'drop': 260}
    s = (1536 / im.width) * area_cap(1536, im.height * 1536 / im.width, 'vote-table.webp')
    w, h = round(im.width * s), round(im.height * s)
    save(resize(im, w, h), 'vote-table.webp')
    print('  TABLE_PX', {'W': w, 'H': h, **{k: round(v * s, 1) for k, v in lines.items()}})


def plate() -> None:
    save(resize(Image.open(MASTERS / 'plate.png'), 900, 270), 'plate.webp')


def glass(src: str, name: str, floor: float = 0.035, gain: float = 1.15, pad: int = 6) -> None:
    c = np.asarray(Image.open(MASTERS / src).convert('RGB')).astype(float) / 255
    a = np.clip(((c / WARM).max(axis=2) - floor) / (1 - floor) * gain, 0, 1)
    ys, xs = np.nonzero(a > 0.06)
    y0, y1, x0, x1 = ys.min() - pad, ys.max() + pad + 1, xs.min() - pad, xs.max() + pad + 1
    rgb = np.broadcast_to(WARM * 255, c.shape)
    out = Image.fromarray(np.dstack([rgb, a * 255]).round().astype(np.uint8)[y0:y1, x0:x1], 'RGBA')
    save(out, name)


def shutter() -> None:
    """The roller blind: cloth stretched to the frame's shape, the hem rod and ring kept true."""
    im = Image.open(MASTERS / 'shutter.png')
    a = np.asarray(im)
    cloth = (55, 1988)  # the cloth's edges, master px
    top, seam, hem, ring = 6, 556, 598, 734  # cloth top, cloth/rod seam, rod centre, ring foot
    rod_ends = (5, 2038)
    # the rod's ends pulled in to 15 px past the cloth (the pelmet overhangs the frame by as much)
    band = Image.fromarray(a[seam:ring], 'RGBA')
    want = (cloth[0] - 15, cloth[1] + 15)
    k = (want[1] - want[0]) / (rod_ends[1] - rod_ends[0])
    squeezed = resize(band, round(band.width * k), band.height)
    band = Image.new('RGBA', (im.width, band.height))
    band.alpha_composite(squeezed, (round(want[0] - rod_ends[0] * k), 0))
    # the frame is about 818 × 316u: the cloth's top to the rod's centre spans its height
    kx = 1640 / (cloth[1] - cloth[0])
    cloth_h = round(316 / 818 * 1640 - (hem - seam) * kx)
    body = resize(Image.fromarray(a[top:seam], 'RGBA'), round(im.width * kx), cloth_h)
    rod = resize(band, round(im.width * kx), round(band.height * kx))
    full = Image.new('RGBA', (body.width, body.height + rod.height))
    full.alpha_composite(body, (0, 0))
    full.alpha_composite(rod, (0, body.height))
    x0 = round((cloth[0] - 15) * kx) - 2
    full = full.crop((x0, 0, round((cloth[1] + 15) * kx) + 2, full.height))
    s = area_cap(full.width, full.height, 'shutter.webp')
    w, h = round(full.width * s), round(full.height * s)
    save(resize(full, w, h), 'shutter.webp')
    m = lambda v: round(v * s, 1)  # noqa: E731
    print('  PAINTED_SHUTTER', {
        'w': w, 'h': h,
        'cloth': (m(cloth[0] * kx - x0), m(cloth[1] * kx - x0)),
        'hem': m(cloth_h + (hem - seam) * kx),
        'rod': (m(cloth_h), m(cloth_h + (645 - seam) * kx)),
    })


def carriage_frame(master: str, hole: tuple[int, int, int, int], name: str) -> None:
    """A carriage picture for the landing (owner 2026-10-17: cream and walnut felt, gold stitching,
    a quilted snowy roof), drawn as a 9-slice round the game's window (Carriage.module.css
    `.paint`). The window is cut clean: inside the rim's inner edge (`hole`: x0, y0, x1, y1, master
    px, a few px inside the measured edge so the stage overlaps the rim) nothing is left, so no
    fringe shows round the game; the stage covers the hole."""
    im = np.asarray(Image.open(MASTERS / master).convert('RGBA')).astype(float)
    im[hole[1] : hole[3], hole[0] : hole[2], 3] = 0
    a = im[..., 3]
    im[..., 3] = np.where(a < 96, 0, np.where(a > 200, 255, a))
    im[im[..., 3] == 0, :3] = 0
    out = Image.fromarray(im.round().astype(np.uint8), 'RGBA')
    dest = ROOT / f'src/assets/sprites/carriage/{name}'
    out.save(dest, 'WEBP', quality=75, alpha_quality=100, method=6)
    print(f'  carriage/{name}: {out.width}×{out.height}, {dest.stat().st_size / 1024:.0f} KB; '
          f'slices {hole[1]} {out.width - hole[2]} {out.height - hole[3]} {hole[0]}')


if __name__ == '__main__':
    print('stand'); stand()
    print('table'); table()
    print('plate'); plate()
    print('glass'); glass('jar-glass-on-black.png', 'jar-glass.webp'); glass('jar-lid-on-black.png', 'jar-lid.webp')
    print('shutter'); shutter()
    print('carriage')
    # the desktop's carriage, and the phone's own (thin posts, the window near the screen's width)
    carriage_frame('carriage.png', (226, 262, 1312, 674), 'frame-felt.webp')
    carriage_frame('carriage-phone.png', (130, 264, 1406, 692), 'frame-felt-phone.webp')
