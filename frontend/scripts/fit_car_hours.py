"""
One-off: the owner's dining car at its four hours (2026-10-19), from the
masters in claude_artifacts/design/rasters/live_ugrade/.

The four hours are one room relit (they line up to the pixel), so each is fitted the same way
onto the 1600×900 picture the car is placed by (dining-car.ts `CAR_PICTURE.fit`: the puppet's
centre line at 800, the rail at 639): scaled so the floor meets the wall on the stage's floor
line (`carLines().floorY`, 580.5) with the picture still reaching the frame's foot, the glass
centred on the puppet. The country is painted in the glass, so nothing is cut out. The lines
code needs (`CAR_PICTURE`) are printed in the fitted picture's pixels.

Run from frontend/: `poetry run python scripts/fit_car_hours.py`
"""

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MASTERS = ROOT / "claude_artifacts/design/rasters/live_ugrade"
OUT = ROOT / "src/assets/sprites"

# the masters, measured: the floor's line at the wall's foot, the glass, the table lamps' shades
# and the picture light over the right-hand painting
CAR = {
    "wall_foot": 628,
    "glass": (485, 135, 1190, 440),
    "table_lamps": ((68, 275), (1610, 275)),
    "picture_light": (1338, 148),
}
FLOOR_Y, FIT_CX, W, H = 580.5, 800, 1600, 900
SCALE = 1.021  # the least that keeps the picture's foot at the frame's (313 px under the wall's foot)


def car() -> None:
    x0, y0, x1, y1 = CAR["glass"]
    ox = FIT_CX - (x0 + x1) / 2 * SCALE
    oy = FLOOR_Y - CAR["wall_foot"] * SCALE
    for hour in ("day", "dusk", "night", "dawn"):
        im = Image.open(MASTERS / f"car-{hour}.png").convert("RGB")
        im = im.resize((round(im.width * SCALE), round(im.height * SCALE)), Image.LANCZOS)
        out = im.crop((round(-ox), round(-oy), round(-ox) + W, round(-oy) + H))
        out.save(OUT / "car" / f"{hour}.webp", "WEBP", quality=82, method=6)
        print(f"car/{hour}.webp: {out.size}, {(OUT / 'car' / f'{hour}.webp').stat().st_size // 1024} KB")
    at = lambda x, y: (round(x * SCALE + ox, 1), round(y * SCALE + oy, 1))  # noqa: E731
    print("glass", at(x0, y0), at(x1, y1))
    print("table lamps", [at(*p) for p in CAR["table_lamps"]], "picture light", at(*CAR["picture_light"]))


if __name__ == "__main__":
    car()
