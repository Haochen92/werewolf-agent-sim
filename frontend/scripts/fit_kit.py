"""
One-off: the material kit's pieces for the landing's "What makes it different" board and the
replay's exhibit, "At the end of the line" (owner, 2026-10-18), from the owner's masters in claude_artifacts/design/rasters/wood/kit/ and
.../landing/ (the worn ink).

- walnut: the board's wood, a tile (it repeats cleanly); shipped at half size, the grain is soft.
- card-paper: one card's paper, laid once per card and never repeated (the master's light falls
  off to its corners, and a repeat would show its seam).
- cream: the lighter slips on the cards (the lesson, the notes), likewise laid once.
- brass-plate: the name plate, cut to its plate and shipped for a 9-slice (its screwed ends
  kept, its middle stretched to the name).
- paperclip: the clip on the lesson slip, cut to the clip.
- kraft, folder-tab, brass-disc: "At the end of the line" (the replay's exhibit): the folder's
  kraft (laid once), its top edge (a 9-slice: the shoulders kept, the raised middle stretched),
  the head of the brass pin that joins its cards.
- ink: the worn-ink mask for the stamps: the master's grey speckle as alpha (white = ink, the
  black flecks = where the ink did not take), a small tile.

Run from frontend/: `poetry run python scripts/fit_kit.py`
"""

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
KIT = ROOT / "claude_artifacts/design/rasters/wood/kit"
LANDING = ROOT / "claude_artifacts/design/rasters/landing"
OUT = ROOT / "src/assets/site/kit"


def opaque_box(im: Image.Image, t: int = 20) -> tuple[int, int, int, int]:
    a = np.array(im.getchannel("A"))
    ys, xs = np.where(a > t)
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def save(im: Image.Image, name: str, quality: int = 82) -> None:
    path = OUT / f"{name}.webp"
    im.save(path, "WEBP", quality=quality, method=6)
    print(f"{name}: {im.size[0]}x{im.size[1]}, {path.stat().st_size // 1024} KB")


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)

    walnut = Image.open(KIT / "walnut-tile.png").convert("RGB")
    save(walnut.resize((627, 627), Image.LANCZOS), "walnut", 80)

    paper = Image.open(KIT / "card-paper.png").convert("RGB")
    save(paper.resize((900, 900), Image.LANCZOS), "card-paper", 78)

    cream = Image.open(KIT / "cream-tile.png").convert("RGB")
    save(cream.resize((627, 627), Image.LANCZOS), "cream", 78)

    plate = Image.open(KIT / "brass-plate.png").convert("RGBA")
    plate = plate.crop(opaque_box(plate))
    h = 120  # three times the plate's height on screen (40px)
    save(plate.resize((round(plate.width * h / plate.height), h), Image.LANCZOS), "brass-plate", 86)

    clip = Image.open(KIT / "paperclip.png").convert("RGBA")
    clip = clip.crop(opaque_box(clip))
    w = 66  # three times its width on screen (20px)
    save(clip.resize((w, round(clip.height * w / clip.width)), Image.LANCZOS), "paperclip", 86)

    # "At the end of the line" (the replay's exhibit): the kraft folder, its top edge, the brass pin
    kraft = Image.open(KIT / "kraft-tile.png").convert("RGB")
    save(kraft.resize((900, 900), Image.LANCZOS), "kraft", 78)

    tab = Image.open(KIT / "folder-tab.png").convert("RGBA")
    tab = tab.crop(opaque_box(tab, 128))
    h = 120  # its height for a 9-slice: the shoulders kept, the raised middle stretched
    save(tab.resize((round(tab.width * h / tab.height), h), Image.LANCZOS), "folder-tab", 82)

    disc = Image.open(KIT / "brass-disc.png").convert("RGBA")
    disc = disc.crop(opaque_box(disc, 128))
    save(disc.resize((48, 48), Image.LANCZOS), "brass-disc", 86)

    ink = Image.open(LANDING / "ink.png").convert("L").resize((256, 256), Image.LANCZOS)
    mask = Image.new("RGBA", ink.size, (0, 0, 0, 0))
    mask.putalpha(ink)
    path = OUT / "ink.webp"
    mask.save(path, "WEBP", quality=60, alpha_quality=60, method=6)
    print(f"ink: {mask.size[0]}x{mask.size[1]}, {path.stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
