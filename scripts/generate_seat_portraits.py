"""One-off op: generate candidate seat portraits for the frontend, and post-process the picks.

NOT part of any pipeline — this is an ops script run by hand, twice, with a human decision
in between (build brief, asset task):

    poetry run python scripts/generate_seat_portraits.py generate
        → ~30 candidates into frontend/docs/portrait_candidates/ for the OWNER to curate.
          The script deliberately does not choose; picking faces is a taste call.

    poetry run python scripts/generate_seat_portraits.py finalize a3 b1 c4 ...
        → the named picks, post-processed to 512px square WebP into
          frontend/src/assets/portraits/, plus the manifest snippet to paste.

Consistency is enforced at GENERATION time, not in code (ux_baseline §1): ONE style prompt,
ONE palette clause, ONE canvas ratio, and only the persona descriptor varies. That is why
the template below is a single constant with one interpolation slot — editing it per-persona
is exactly the mistake that produces twelve portraits from twelve different worlds.

Candidates are written outside src/ on purpose: only curated finals belong in the bundle,
and src/assets/manifest.ts stays the sole import site.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CANDIDATE_DIR = REPO_ROOT / "frontend" / "docs" / "portrait_candidates"
FINAL_DIR = REPO_ROOT / "frontend" / "src" / "assets" / "portraits"

MODEL = "imagen-4.0-generate-001"
CANDIDATES_PER_PERSONA = 2
FINAL_SIZE = 512

# The ONE style template. Everything outside `{persona}` is fixed so the set coheres.
STYLE_TEMPLATE = (
    "hi-bit pixel art portrait of {persona}, "
    "Coffee Talk / VA-11 Hall-A register, chunky visible pixels, limited palette, "
    "dark ink and charcoal ground, single warm amber key light from one side, "
    "deep shadow, moody tavern interior, bust framing facing the viewer, "
    "muted desaturated colours, no text, no watermark, no border, no UI"
)

NEGATIVE = "text, letters, watermark, signature, frame, border, glossy 3d render, photorealistic, bright saturated colours, anime cel shading"

# Only this varies. Twelve personas, deliberately mixed in age, build and bearing so a
# nine-seat table never looks like one family — but all in the same world.
PERSONAS: dict[str, str] = {
    "a": "a weathered innkeeper with a heavy jaw and tired eyes",
    "b": "a young woman with cropped dark hair and a sharp, watchful expression",
    "c": "an elderly herbalist in a hooded shawl, deep-set eyes",
    "d": "a broad-shouldered blacksmith with a soot-marked face and a short beard",
    "e": "a thin scholarly man with round spectacles and a nervous mouth",
    "f": "a middle-aged woman with grey-streaked braids and a hard, level stare",
    "g": "a lean traveller with a scarf pulled to the chin and shadowed eyes",
    "h": "a round-faced baker with flour-dusted forearms and an uneasy smile",
    "i": "a stern constable with a scarred brow and close-cropped hair",
    "j": "a quiet girl with long pale hair holding a lantern, half in shadow",
    "k": "a wiry old fisherman with a crooked nose and a pipe",
    "l": "a hooded figure whose face is mostly darkness, one eye catching the light",
}


def _client():
    """Vertex-backed genai client, using the project's existing ADC — no new credentials."""
    from google import genai

    project = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project:
        # .env is the project's convention; read it rather than demanding an export.
        for line in (REPO_ROOT / ".env").read_text().splitlines():
            if line.startswith("GOOGLE_CLOUD_PROJECT="):
                project = line.split("=", 1)[1].strip()
                break
    if not project:
        raise SystemExit("GOOGLE_CLOUD_PROJECT is not set (env or .env)")

    location = os.environ.get("GOOGLE_CLOUD_LOCATION", "us-central1")
    return genai.Client(vertexai=True, project=project, location=location)


def generate() -> None:
    from google.genai import types

    client = _client()
    CANDIDATE_DIR.mkdir(parents=True, exist_ok=True)

    total = 0
    for key, persona in PERSONAS.items():
        prompt = STYLE_TEMPLATE.format(persona=persona)
        try:
            response = client.models.generate_images(
                model=MODEL,
                prompt=prompt,
                config=types.GenerateImagesConfig(
                    number_of_images=CANDIDATES_PER_PERSONA,
                    aspect_ratio="1:1",
                    negative_prompt=NEGATIVE,
                    # Portraits of invented people: person generation must be permitted, and
                    # adults only — these are tavern regulars, not children.
                    person_generation="allow_adult",
                ),
            )
        except Exception as exc:  # noqa: BLE001 — an ops script reports and continues
            print(f"  {key}: FAILED — {type(exc).__name__}: {exc}")
            continue

        for index, image in enumerate(response.generated_images, start=1):
            path = CANDIDATE_DIR / f"{key}{index}.png"
            path.write_bytes(image.image.image_bytes)
            total += 1
            print(f"  wrote {path.relative_to(REPO_ROOT)}")

    print(f"\n{total} candidates in {CANDIDATE_DIR.relative_to(REPO_ROOT)}")
    print("Review them, then: poetry run python scripts/generate_seat_portraits.py finalize <ids…>")


def finalize(picks: list[str]) -> None:
    """Crop-to-square, downscale to 512px, encode WebP, and print the manifest snippet.

    Raw generation output is multi-megabyte PNG; portraits render at chip and card scale, so
    ~2× display size is the honest ceiling (build_plan §3).
    """
    from PIL import Image

    FINAL_DIR.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    for order, pick in enumerate(picks, start=1):
        source = CANDIDATE_DIR / f"{pick}.png"
        if not source.exists():
            raise SystemExit(f"no such candidate: {source}")

        image = Image.open(source).convert("RGB")
        side = min(image.size)
        left = (image.width - side) // 2
        top = (image.height - side) // 2
        image = image.crop((left, top, left + side, top + side))
        # NEAREST, not LANCZOS: smooth resampling turns pixel art into mush.
        image = image.resize((FINAL_SIZE, FINAL_SIZE), Image.Resampling.NEAREST)

        name = f"{order:02d}.webp"
        image.save(FINAL_DIR / name, "WEBP", quality=88, method=6)
        written.append(name)
        print(f"  wrote {(FINAL_DIR / name).relative_to(REPO_ROOT)}")

    print("\nPaste into frontend/src/assets/manifest.ts:\n")
    for name in written:
        stem = name.split(".")[0]
        print(f"import p{stem} from './portraits/{name}';")
    print()
    print("export const PORTRAITS: StaticImageData[] = [")
    print("  " + ", ".join(f"p{n.split('.')[0]}" for n in written) + ",")
    print("];")


if __name__ == "__main__":
    command = sys.argv[1] if len(sys.argv) > 1 else ""
    if command == "generate":
        generate()
    elif command == "finalize":
        if len(sys.argv) < 3:
            raise SystemExit("finalize needs candidate ids, e.g. `finalize a1 c2 d1`")
        finalize(sys.argv[2:])
    else:
        raise SystemExit(__doc__)
