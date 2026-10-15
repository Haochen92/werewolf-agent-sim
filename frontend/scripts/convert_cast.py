"""Convert one cast character's masters into the stage's day sprites (stage_architecture §4 "The cast").

The eleven were converted with a one-off Pillow pass that was never kept; this reproduces its
recipe so a new character comes out on the same terms:

- Cleaning: the masters' body alpha is 253, so alpha is scaled by 255/253; alpha under 3 is
  cleared and RGB under alpha 0 zeroed.
- Registration: each pose is fitted to the base by the overlap of their alpha below the crown
  (a scale about the base's feet, then a shift), so switching states never jumps.
- One canvas for the four poses: the union of their alpha boxes, 6 px of air on top and on the
  wider side, the feet on the bottom edge, symmetric about the face's centre line. Scaled so the
  body (crown to toe) is 1000 px. Premultiplied Lanczos, WebP quality 82, method 6.
- The head portrait at 384 px, same cleaning and encoder.

The crown (the skull's top under any hat) and the face's centre line are read by eye off the
base, so they live in MEASURES, in master px. Prints the canvas, BODY and REACH to paste into
manifest.ts. Shadows and the phone's copies are made from the output afterwards (see §4).

Run from frontend/: `poetry run python scripts/convert_cast.py <id> [--out DIR]`
"""

import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

ROOT = Path(__file__).resolve().parent.parent
MASTERS = ROOT / 'claude_artifacts/design/rasters/cast'
SPRITES = ROOT / 'src/assets/sprites/day'
POSES = ('base', 'talking', 'thinking', 'out')
BODY_PX = 1000
AIR = 6
HEAD_PX = 384
PAD = 256  # transparent margin so a resize box may run past the master's edge

# id -> (crown y, face centre x), master px on the base. face_x is the eyes' midpoint.
MEASURES = {
    # the check against the shipped eleven (backed out of its canvas): 886x1162 against 885x1162
    'whale': (279, 533.5),
    'kitsune': (300, 511),  # the dome between the ears; the hairpin rises above
    'mushroom': (330, 515),  # under the cap, read as a hat: eyes to crown ~400 px, as the whale's
    'lionCub': (365, 511),  # the face's circle under the forelock; mane, ears and cap rise above
    'automaton': (260, 540),  # the dome's arc under the cap
}


def load_clean(path: Path) -> np.ndarray:
    """A master as float RGBA, alpha rescaled from 253 and its faint fringe cleared."""
    m = np.asarray(Image.open(path).convert('RGBA')).astype(np.float32)
    a = np.clip(m[..., 3] * 255 / 253, 0, 255)
    a[a < 3] = 0
    m[..., 3] = a
    m[a == 0, :3] = 0
    return m


def to_image(m: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(np.rint(m), 0, 255).astype(np.uint8), 'RGBA')


def warp_mask(mask: np.ndarray, k: float, dx: float, dy: float, feet: tuple[float, float]):
    """The pose's mask placed on the base: scaled by k about the feet, then shifted."""
    fx, fy = feet
    # output (y, x) samples input at feet + (out - feet - shift) / k
    return ndimage.affine_transform(
        mask.astype(np.float32),
        [1 / k, 1 / k],
        offset=[fy - (fy + dy) / k, fx - (fx + dx) / k],
        order=1,
    ) > 0.5


def overlap(a: np.ndarray, b: np.ndarray) -> float:
    return (a & b).sum() / max((a | b).sum(), 1)


def shifted(mask: np.ndarray, dx: int, dy: int) -> np.ndarray:
    out = np.zeros_like(mask)
    h, w = mask.shape
    out[max(dy, 0):h + min(dy, 0), max(dx, 0):w + min(dx, 0)] = \
        mask[max(-dy, 0):h - max(dy, 0), max(-dx, 0):w - max(dx, 0)]
    return out


def search(target, src, below, feet, scales, shifts):
    """Best (IoU, k, dx, dy) over the grid: one warp per scale, the shifts by slicing."""
    best = (-1.0, 1.0, 0, 0)
    for k in scales:
        w = warp_mask(src, k, 0, 0, feet)
        for dx in shifts[0]:
            for dy in shifts[1]:
                score = overlap(target, shifted(w, dx, dy) & below)
                if score > best[0]:
                    best = (score, float(k), dx, dy)
    return best


def register(base_a, pose_a, crown: float, feet: tuple[float, float]):
    """Best (IoU, k, dx, dy) by alpha overlap below the crown: coarse at quarter size, then fine."""
    q = 4
    below = np.zeros(base_a.shape, dtype=bool)
    below[int(crown):] = True
    target = (base_a >= 128) & below
    src = pose_a >= 128
    _, k0, dx0, dy0 = search(
        target[::q, ::q], src[::q, ::q], below[::q, ::q], (feet[0] / q, feet[1] / q),
        np.arange(0.92, 1.0801, 0.01), (range(-12, 13), range(-12, 13)),
    )
    return search(
        target, src, below, feet, np.arange(k0 - 0.008, k0 + 0.0081, 0.002),
        (range(dx0 * q - 5, dx0 * q + 6), range(dy0 * q - 5, dy0 * q + 6)),
    )


def box(alpha: np.ndarray, threshold: int = 3):
    ys, xs = np.nonzero(alpha >= threshold)
    return xs.min(), ys.min(), xs.max() + 1, ys.max() + 1


def render(m: np.ndarray, size: tuple[int, int], region: tuple[float, ...]) -> np.ndarray:
    """Premultiplied Lanczos resample of `region` (master px) to `size`, cleaned again."""
    padded = Image.new('RGBA', (m.shape[1] + 2 * PAD, m.shape[0] + 2 * PAD))
    padded.paste(to_image(m), (PAD, PAD))
    x0, y0, x1, y1 = region
    out = padded.convert('RGBa').resize(
        size, Image.Resampling.LANCZOS, box=(x0 + PAD, y0 + PAD, x1 + PAD, y1 + PAD)
    ).convert('RGBA')
    o = np.asarray(out).copy()
    o[o[..., 3] < 3] = 0
    return o


def convert(cid: str, out_dir: Path) -> None:
    crown, face_x = MEASURES[cid]
    masters = {p: load_clean(MASTERS / cid / f'{p}.png') for p in POSES}
    base_a = masters['base'][..., 3]
    anchor_y = box(base_a)[3]  # the base's feet, which the fits scale about
    feet = (face_x, float(anchor_y))

    # Registration: identity unless the fit moves the pose by 2 px or 0.5% or more.
    fits = {'base': (1.0, 0.0, 0.0)}
    for p in POSES[1:]:
        score0 = overlap((base_a >= 128)[int(crown):], (masters[p][..., 3] >= 128)[int(crown):])
        score, k, dx, dy = register(base_a, masters[p][..., 3], crown, feet)
        moved = abs(k - 1) >= 0.005 or max(abs(dx), abs(dy)) >= 2
        fits[p] = (k, dx, dy) if moved else (1.0, 0.0, 0.0)
        print(f'  {p:8s} IoU {score0:.3f} -> {score:.3f}  k={k:.3f} dx={dx} dy={dy}'
              f'{"" if moved else "  (kept as is)"}')

    # The union of the registered poses' boxes, in base px.
    boxes = []
    for p in POSES:
        k, dx, dy = fits[p]
        x0, y0, x1, y1 = box(masters[p][..., 3])
        boxes.append((face_x + k * (x0 - face_x) + dx, anchor_y + k * (y0 - anchor_y) + dy,
                      face_x + k * (x1 - face_x) + dx, anchor_y + k * (y1 - anchor_y) + dy))
    left = min(b[0] for b in boxes)
    top = min(b[1] for b in boxes)
    right = max(b[2] for b in boxes)
    foot = max(b[3] for b in boxes)  # the canvas's bottom edge: the lowest foot of any pose

    scale = BODY_PX / (foot - crown)
    half = max(face_x - left, right - face_x) + AIR / scale
    width = round(2 * half * scale)
    height = round((foot - top) * scale + AIR)
    # the canvas in base px, rebuilt from the rounded size so the scale holds exactly
    cx0 = face_x - width / scale / 2
    cy0 = foot - height / scale

    dest = out_dir / cid
    dest.mkdir(parents=True, exist_ok=True)
    reach_l = reach_r = 0.0
    for p in POSES:
        k, dx, dy = fits[p]
        # the canvas's corners in this pose's own px (the fit inverted)
        region = (face_x + (cx0 - dx - face_x) / k, anchor_y + (cy0 - dy - anchor_y) / k,
                  face_x + (cx0 + width / scale - dx - face_x) / k,
                  anchor_y + (foot - dy - anchor_y) / k)
        o = render(masters[p], (width, height), region)
        Image.fromarray(o, 'RGBA').save(dest / f'{p}.webp', quality=82, method=6)
        xs = np.nonzero((o[..., 3] >= 128).any(0))[0]
        reach_l = max(reach_l, width / 2 - xs.min())
        reach_r = max(reach_r, xs.max() + 1 - width / 2)

    head = load_clean(MASTERS / cid / 'head.png')
    h = render(head, (HEAD_PX, HEAD_PX), (0, 0, head.shape[1], head.shape[0]))
    Image.fromarray(h, 'RGBA').save(dest / 'head.webp', quality=82, method=6)

    top_frac = (height - BODY_PX) / height
    print(f'  canvas {width}x{height}  scale {scale:.4f}')
    print(f'  BODY  {cid}: {{ top: {top_frac:.3f}, body: {1 - top_frac:.3f} }},')
    print(f'  REACH {cid}: {{ left: {reach_l / BODY_PX:.3f}, right: {reach_r / BODY_PX:.3f} }},')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('ids', nargs='+', choices=sorted(MEASURES))
    parser.add_argument('--out', type=Path, default=SPRITES)
    args = parser.parse_args()
    if 'whale' in args.ids and args.out.resolve() == SPRITES.resolve():
        parser.error('whale is a check: pass --out elsewhere, never over its shipped sprites')
    for cid in args.ids:
        print(cid)
        convert(cid, args.out)


if __name__ == '__main__':
    main()
