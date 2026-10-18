"""One-off: the station's train, joined from the owner's pieces: felt (2026-10-17), then a wooden
toy, walnut and cream with brass (2026-10-18, `SET`; the felt set's numbers are kept beside it).

Reads claude_artifacts/design/rasters/<SET>/station/ (train_back = a car's left end, train_front its
right end, train_center a window bay, train_connector the bellows, train_wheel) and writes the
master `train.png` beside them, plus the WebP files the build ships (src/assets/sprites/station/
train.webp at about 1.5 px a unit and train@1x.webp at 1), and prints the geometry station.ts
needs (`TRAIN_PX`).

The bay is drawn taller than the ends, so it is first warped row by row onto the ends' bands (the
snow, the top rail, the cream panel, the brown panel, the bottom rail, the chassis). The dining
car is five bays, each window narrowed along its straight middle so the five span the room's
places as the painted train's five did; each side car keeps one bay as it was drawn. Through the windows
the felt night country (the dining car's own window pictures), baked into the picture.

Run from frontend/: `poetry run python scripts/fit_felt_station.py`
"""

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
SET = 'wood'
SRC = ROOT / f'claude_artifacts/design/rasters/{SET}/station'
FELT = ROOT / 'claude_artifacts/design/rasters/felt/station'
OUT = ROOT / 'src/assets/sprites/station'

# Each set's measurements, in its pieces' own pixels:
# - rows: the bands' tops down a plain column (the snow's top, the roof, the top rail, the cream
#   panel, the brown panel, the bottom rail, the chassis, and the foot); the bay's, and the ends'
#   it is warped onto
# - hole: the bay's window hole, and straight: the straight run of its frame (columns)
# - keep: what is kept of each piece across: the bay without most of its outer cream (the corner
#   ornaments too), the ends without the plain panel on their inner side (the door, the post and
#   the buffer kept)
# - wheel: the wheel's crop (rows, columns), so the rim comes out the same size
# - lines: more rows of the bay held to the ends' (bay row, end row), so a gold line meets its own
# - under: a strip of an end's own chassis (rows, columns) laid under the bay, when the bay's
#   chassis is one tier and the ends' two: the bay's tier is then held to the upper one, unstretched
#   (its brass bolts stay round), the foot in `rows` being where the bay's chassis stops
GEOMETRY = {
    'felt': dict(
        bay_rows=[84, 144, 324, 378, 960, 1140, 1224, 1320],
        end_rows=[42, 102, 300, 360, 864, 1020, 1110, 1302],
        hole=(258, 865), straight=(430, 690),
        bay_keep=(150, 975), back_keep=(100, 600), front_keep=(520, 1050),
        wheel=((60, 1200), (120, 1135)),
        lines=[],
        under=None,
    ),
    'wood': dict(
        bay_rows=[131, 190, 309, 376, 970, 1140, 1226, 1318],
        end_rows=[97, 138, 260, 356, 862, 1026, 1106, 1198],
        hole=(257, 866), straight=(430, 690),
        bay_keep=(150, 975), back_keep=(100, 584), front_keep=(552, 1050),
        wheel=((60, 1200), (130, 1123)),
        lines=[(338, 311)],  # the top rail's gold line
        under=((1194, 1302), (620, 980)),
    ),
}
_g = GEOMETRY[SET]
BAY_ROWS, END_ROWS = _g['bay_rows'], _g['end_rows']
HOLE, STRAIGHT = _g['hole'], _g['straight']
BAY_KEEP, BACK_KEEP, FRONT_KEEP = _g['bay_keep'], _g['back_keep'], _g['front_keep']
WHEEL_ROWS, WHEEL_COLS = _g['wheel']
LINES, UNDER = _g['lines'], _g['under']
H = 1402
# the dining car's windows: how many, each one's width, and the cream either side of each
DINING_WINDOWS = 5
DINING_HOLE_W = 480
DINING_PANEL = 100
# the car's lamps, a warm cast over the country seen through its windows
LIT_TOP = np.array([226, 158, 88])


def rgba(name: str) -> np.ndarray:
    return np.asarray(Image.open(SRC / f'{name}.png').convert('RGBA')).astype(float)


def premul(a: np.ndarray) -> np.ndarray:
    out = a.copy()
    out[..., :3] *= a[..., 3:] / 255
    return out


def unpremul(a: np.ndarray) -> np.ndarray:
    out = a.copy()
    al = np.maximum(a[..., 3:], 1e-3)
    out[..., :3] = np.where(a[..., 3:] > 0, a[..., :3] * 255 / al, 0)
    return out


def warp_rows(a: np.ndarray, src: list[int], dst: list[int], height: int) -> np.ndarray:
    """Each output row takes the input row the piecewise-linear map sends it to."""
    ys = np.arange(height)
    take = np.interp(ys, dst, src)
    lo = np.clip(np.floor(take).astype(int), 0, a.shape[0] - 1)
    hi = np.clip(lo + 1, 0, a.shape[0] - 1)
    t = (take - np.floor(take))[:, None, None]
    p = premul(a)
    out = p[lo] * (1 - t) + p[hi] * t
    out[(ys < dst[0]) | (ys > dst[-1] + 20)] = 0
    return unpremul(out)


def stretch_cols(a: np.ndarray, x0: int, x1: int, width: int) -> np.ndarray:
    """Columns x0..x1 laid again and again to `width` columns, every other copy mirrored so the
    copies meet without a seam, the rest kept: the window's straight run, its stitches still
    stitches and the roof's quilting still quilted (a stretch drew them out into lines)."""
    piece, run, flip = a[:, x0:x1], [], False
    while sum(p.shape[1] for p in run) < width:
        run.append(piece[:, ::-1] if flip else piece)
        flip = not flip
    mid = np.concatenate(run, 1)[:, :width]
    return np.concatenate([a[:, :x0], mid, a[:, x1:]], 1)


def country(w: int, h: int, offset: int) -> np.ndarray:
    """The felt night country (the dining car's own window pictures, sprites/window/night-*),
    the far hills and the near row of pines, scaled to the window's height and laid along it."""
    far = Image.open(ROOT / 'src/assets/sprites/window/night-far.webp').convert('RGBA')
    near = Image.open(ROOT / 'src/assets/sprites/window/night-near.webp').convert('RGBA')
    sc = h / far.height
    fw = round(far.width * sc)
    far = far.resize((fw, h), Image.LANCZOS)
    near = near.resize((fw, round(near.height * sc)), Image.LANCZOS)
    row = Image.new('RGBA', (fw, h))
    row.alpha_composite(far)
    row.alpha_composite(near, (0, h - near.height))
    strip = Image.new('RGBA', (w + fw, h))
    for x in range(0, w + fw, fw):
        strip.alpha_composite(row, (x, 0))
    return np.asarray(strip).astype(float)[:, offset % fw : offset % fw + w, :3]


def light_hole(a: np.ndarray, x0: int, x1: int, rows: tuple[int, int], offset: int = 0) -> np.ndarray:
    """The window's transparent hole filled with the country seen through the car, under the
    frame, a little warmed by the car's own lamps."""
    out = a.copy()
    y0, y1 = rows
    fill = country(x1 - x0, y1 - y0, offset)
    fill = fill * 0.85 + LIT_TOP * 0.08
    region = out[y0:y1, x0:x1]
    al = region[..., 3:] / 255
    region[..., :3] = region[..., :3] * al + fill * (1 - al)
    region[..., 3] = 255
    return out


def light_portholes(a: np.ndarray) -> np.ndarray:
    """Every see-through hole inside a piece (a door's porthole) filled as a window is, so the
    sky never shows through the car."""
    from scipy import ndimage

    clear = a[..., 3] < 128
    lab, n = ndimage.label(clear)
    edge = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]])))
    out = a
    for i, box in enumerate(ndimage.find_objects(lab), 1):
        if i in edge:
            continue
        ys, xs = box
        out = light_hole(out, xs.start - 3, xs.stop + 3, (ys.start - 3, ys.stop + 3), 300 * i)
    return out


def with_under(middle: np.ndarray) -> np.ndarray:
    """The bay over the ends' lower chassis tier, mirror-tiled to its width (`UNDER`)."""
    if not UNDER:
        return middle
    (y0, y1), (x0, x1) = UNDER
    tier = rgba('train_back')[y0:y1, x0:x1]
    strip = stretch_cols(tier, 0, tier.shape[1], middle.shape[1])[:, : middle.shape[1]]
    out = np.zeros_like(middle)
    place(out, strip, 0, y0)
    place(out, middle, 0)
    return out


def hole_rows(a: np.ndarray, x: int) -> tuple[int, int]:
    col = a[:, x, 3]
    ys = np.nonzero(col[300:1100] < 128)[0] + 300
    return int(ys.min()) - 6, int(ys.max()) + 7


def place(canvas: np.ndarray, piece: np.ndarray, x: int, y: int = 0) -> None:
    """Over-composite `piece` at (x, y), premultiplied."""
    h, w = piece.shape[:2]
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, canvas.shape[1]), min(y + h, canvas.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    src = premul(piece[y0 - y : y1 - y, x0 - x : x1 - x])
    dst = premul(canvas[y0:y1, x0:x1])
    sa = src[..., 3:] / 255
    canvas[y0:y1, x0:x1] = unpremul(src + dst * (1 - sa))


def scaled(a: np.ndarray, k: float) -> np.ndarray:
    im = Image.fromarray(premul(a).round().astype(np.uint8), 'RGBA')
    im = im.resize((round(a.shape[1] * k), round(a.shape[0] * k)), Image.LANCZOS)
    return unpremul(np.asarray(im).astype(float))


def main() -> None:
    knots = sorted([*zip(BAY_ROWS, END_ROWS), *LINES])
    bay = warp_rows(rgba('train_center'), [b for b, _ in knots], [e for _, e in knots], H)
    rows = hole_rows(bay, (HOLE[0] + HOLE[1]) // 2)
    back = light_portholes(rgba('train_back')[:, BACK_KEEP[0] : BACK_KEEP[1]])
    front = light_portholes(rgba('train_front')[:, FRONT_KEEP[0] : FRONT_KEEP[1]])
    short = light_hole(bay, HOLE[0], HOLE[1], rows, 900)[:, BAY_KEEP[0] : BAY_KEEP[1]]
    # the dining car: five of the bay side by side, each window narrowed along its straight run
    # and the cream between them trimmed, so the five span about the room's places (owner,
    # 2026-10-17: five windows, as the painted train had)
    cut = (HOLE[1] - HOLE[0]) - DINING_HOLE_W
    nbay = stretch_cols(bay, STRAIGHT[0], STRAIGHT[1], (STRAIGHT[1] - STRAIGHT[0]) - cut)
    nhole = (HOLE[0], HOLE[1] - cut)
    bays = [
        light_hole(nbay, nhole[0], nhole[1], rows, 700 * i)[
            :, nhole[0] - DINING_PANEL : nhole[1] + DINING_PANEL
        ]
        for i in range(DINING_WINDOWS)
    ]
    longbay = np.concatenate(bays, 1)

    def car(middle: np.ndarray) -> np.ndarray:
        # the ends overlap the bay by a few px, so no seam of light shows between them
        w = back.shape[1] + middle.shape[1] + front.shape[1] - 12
        c = np.zeros((H, w, 4))
        place(c, middle, back.shape[1] - 6)
        place(c, back, 0)
        place(c, front, w - front.shape[1])
        return c

    side, dining = car(with_under(short)), car(with_under(longbay))
    # the bellows between cars: their snow at the roof's snow, their foot on the bottom rail
    conn = rgba('train_connector')
    cs = (END_ROWS[6] - END_ROWS[1] - 60) / (1455 - 55)
    conn = scaled(conn[55:1456, 76:950], cs)
    gap = 150  # buffer to buffer; the bellows behind, between the cars' ends
    wheel = rgba('train_wheel')[WHEEL_ROWS[0] : WHEEL_ROWS[1], WHEEL_COLS[0] : WHEEL_COLS[1]]
    wheel = scaled(wheel, 300 / wheel.shape[1])

    cars = [side, dining, side]
    width = sum(c.shape[1] for c in cars) + 2 * gap
    train = np.zeros((H + 120, width, 4))
    x, starts = 0, []
    for i, c in enumerate(cars):
        if i:
            place(train, conn, x - gap // 2 - conn.shape[1] // 2, END_ROWS[1] + 40)
        starts.append(x)
        x += c.shape[1] + gap
    for c, x0 in zip(cars, starts):
        # two wheels under each end of a car's body, behind its chassis line
        w = c.shape[1]
        for fx in (0.17, 0.33, 0.67, 0.83) if w > 3000 else (0.25, 0.75):
            place(train, wheel, round(x0 + fx * w - wheel.shape[1] / 2), END_ROWS[6] - 30)
        place(train, c, x0)
    a = train[..., 3]
    ys = np.nonzero(a.max(1) > 10)[0]
    # the empty rows above the snow and below the wheels are cut (no pixels drawn for nothing)
    top = max(int(ys.min()) - 4, 0)
    train = train[top : ys.max() + 4]
    # the glass the places sit in: the first window's left edge to the last one's right
    win_x0 = starts[1] + back.shape[1] - 6 + DINING_PANEL
    win_x1 = starts[1] + back.shape[1] - 6 + longbay.shape[1] - DINING_PANEL
    master = Image.fromarray(train.clip(0, 255).round().astype(np.uint8), 'RGBA')
    master.save(SRC / 'train.png')
    snow = END_ROWS[1] - top
    bottom = int(ys.max()) - top
    print('master', master.size)
    print('TRAIN_PX', dict(w=master.width, h=master.height, wx0=win_x0, wx1=win_x1,
                           wy0=rows[0] + 6 - top, wy1=rows[1] - 7 - top, snow=snow, bottom=bottom))
    # the shipped copies: units a master px is CAR_H (432) over the snow-to-foot height
    k = 432 / (bottom - snow)
    for name, density in (('train.webp', 1.5), ('train@1x.webp', 1.0)):
        w, h = round(master.width * k * density), round(master.height * k * density)
        out = master.convert('RGBa').resize((w, h), Image.LANCZOS).convert('RGBA')
        out.save(OUT / name, 'WEBP', quality=80, alpha_quality=100, method=6)
        print(f'  {name}: {w}×{h}, {(OUT / name).stat().st_size / 1024:.0f} KB')


def beam() -> None:
    """The beam along the top and the ledge along the foot: the owner's walnut felt, a tile that
    meets itself on every side (its edges cross-faded into the opposite ones), 512 px square."""
    a = np.asarray(Image.open(FELT / 'wood_felt.png').convert('RGB')).astype(float)
    n, b = a.shape[0], 96
    k = np.linspace(0, 1, b)
    a = a.copy()
    a[:, :b] = k[None, :, None] * a[:, :b] + (1 - k[None, :, None]) * a[:, n - b :]
    a = a[:, : n - b]
    a[:b] = k[:, None, None] * a[:b] + (1 - k[:, None, None]) * a[n - b :]
    a = a[: n - b]
    tile = Image.fromarray(a.round().astype(np.uint8)).resize((512, 512), Image.LANCZOS)
    tile.save(OUT / 'beam.webp', 'WEBP', quality=75, method=6)
    print(f'  beam.webp: 512×512, {(OUT / "beam.webp").stat().st_size / 1024:.0f} KB')


def floor() -> None:
    """The platform's paving, kept (the owner, 2026-10-17: reuse it) but brought towards the felt:
    its contrast softened, its cold grey warmed to a brown grey, the same tile at the same size."""
    src = ROOT / 'claude_artifacts/design/sprites/station/floor.png'
    a = np.asarray(Image.open(src).convert('RGB')).astype(float)
    mean = a.mean(axis=(0, 1))
    a = mean + (a - mean) * 0.7  # softer: the cracks and joints less sharp
    lum = (a @ np.array([0.2126, 0.7152, 0.0722]))[..., None]
    warm = lum * np.array([1.08, 0.98, 0.86])  # a warm grey of the same light
    a = a * 0.45 + warm * 0.55
    out = Image.fromarray(a.clip(0, 255).round().astype(np.uint8)).resize((768, 768), Image.LANCZOS)
    out.save(OUT / 'floor.webp', 'WEBP', quality=85, method=6)
    print(f'  floor.webp: 768×768, {(OUT / "floor.webp").stat().st_size / 1024:.0f} KB')


if __name__ == '__main__':
    main()
    # the beam and the floor are as the felt set made them (2026-10-17); call beam() and floor() to
    # remake them
