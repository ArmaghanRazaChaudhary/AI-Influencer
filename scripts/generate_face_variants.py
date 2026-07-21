from __future__ import annotations

"""
Generate a library of Sofia Reyes reference photos in different locations and poses.
Uses the active IMAGE_BACKEND (chatgpt web or api) — same as the main pipeline.

Output: assets/faces/Sofia/<slug>.png

Run:
    python scripts/generate_face_variants.py
    python scripts/generate_face_variants.py --only santorini paris    # specific scenes
    python scripts/generate_face_variants.py --skip-existing           # resume if interrupted
"""

import argparse
import sys
import time
from pathlib import Path

# Make project root importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.chatgpt_image_gen import generate_images_batch
from config.settings import BASE_DIR

SOFIA_FACE = BASE_DIR / "assets/faces/face1.jpeg"
SOFIA_DIR = BASE_DIR / "assets/faces/Sofia"

# 8 scenes — each becomes one reference photo
SCENES: list[dict] = [
    {
        "slug": "paris_cafe_morning",
        "prompt": (
            "Sitting at a classic Parisian sidewalk café at golden-hour morning light. "
            "Wearing a camel Celine trench coat, tortoiseshell sunglasses pushed up on her head. "
            "A café au lait and croissant on the marble table. "
            "Cobblestone street and iron bistro chairs behind her. Relaxed, off-guard expression."
        ),
    },
    {
        "slug": "santorini_infinity_pool",
        "prompt": (
            "Standing at the edge of a cliffside infinity pool in Santorini at golden hour. "
            "White bikini top, a sheer Bottega Veneta sarong knotted at the hip. "
            "Holding a glass of champagne. Iconic white-washed buildings and blue domes visible behind her. "
            "The Aegean Sea stretches to the horizon. Warm, cinematic light."
        ),
    },
    {
        "slug": "mykonos_yacht_deck",
        "prompt": (
            "On the sun deck of a private yacht anchored off Mykonos in the early afternoon. "
            "White wide-leg linen trousers, strapless cream top, oversized Chanel sunglasses. "
            "Windblown hair. Turquoise Aegean water all around. "
            "Leaning casually against the railing, looking toward the horizon."
        ),
    },
    {
        "slug": "amalfi_terrace_sunset",
        "prompt": (
            "Standing on a flower-draped terrace on the Amalfi Coast at late afternoon. "
            "Wearing a floral midi sundress, strappy tan sandals. "
            "Colourful hillside houses cascading down behind her to the sea. "
            "Holding a limoncello glass, laughing softly at something off camera."
        ),
    },
    {
        "slug": "dubai_hotel_lobby",
        "prompt": (
            "Walking through the grand atrium lobby of a five-star Dubai hotel. "
            "The Row black wide-leg trousers, silk ivory blouse, Bottega Veneta Andiamo bag. "
            "Gold light fixtures and towering palms in the background. "
            "Confident mid-stride, looking slightly off to the side."
        ),
    },
    {
        "slug": "monaco_marina_evening",
        "prompt": (
            "Standing on the Quai des États-Unis in Monaco harbour at dusk. "
            "A simple black slip dress, strappy heels, minimal gold jewellery. "
            "Mega-yachts and the glittering harbour lights behind her. "
            "One hand holding a small clutch. Soft evening light, effortlessly elegant."
        ),
    },
    {
        "slug": "positano_village_steps",
        "prompt": (
            "On the colourful ceramic-tiled steps winding through Positano village, mid-morning. "
            "Breezy white linen co-ord set, Gucci horsebit slides, oversized straw tote. "
            "Pastel-painted buildings stacked behind her leading down to the blue sea. "
            "Holding a lemon gelato. Sunlit, relaxed, candid."
        ),
    },
    {
        "slug": "tulum_cenote",
        "prompt": (
            "Floating on her back in a crystal-clear cenote in Tulum. "
            "White one-piece swimsuit. Lush jungle canopy overhead, "
            "dappled sunlight filtering through the trees and hitting the water. "
            "Eyes closed, completely relaxed — serene and quietly beautiful."
        ),
    },
]


def generate_variants(slugs: list[str] | None = None, skip_existing: bool = False) -> None:
    SOFIA_DIR.mkdir(parents=True, exist_ok=True)

    scenes = SCENES
    if slugs:
        scenes = [s for s in SCENES if s["slug"] in slugs]
        if not scenes:
            print(f"No matching scenes for: {slugs}")
            return

    # Filter out already-done scenes
    tasks = []
    for scene in scenes:
        out_path = SOFIA_DIR / f"{scene['slug']}.png"
        if skip_existing and out_path.exists():
            print(f"SKIP  {scene['slug']} (already exists)")
            continue
        tasks.append((scene["prompt"], SOFIA_FACE, out_path))

    if not tasks:
        print("Nothing to generate.")
        return

    print(f"\nGenerating {len(tasks)} Sofia photo(s) in ONE session -> {SOFIA_DIR}\n")

    # Single browser session — login once, generate all
    results = generate_images_batch(tasks)

    print(f"\nDone. {len(results)}/{len(tasks)} images saved to: {SOFIA_DIR}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate Sofia face variant photos")
    parser.add_argument(
        "--only", nargs="+", metavar="SLUG",
        help="Generate only these scene slugs",
    )
    parser.add_argument(
        "--skip-existing", action="store_true",
        help="Skip scenes that already have an output file",
    )
    parser.add_argument(
        "--list", action="store_true",
        help="List available scene slugs and exit",
    )
    args = parser.parse_args()

    if args.list:
        for s in SCENES:
            print(f"  {s['slug']}")
        sys.exit(0)

    generate_variants(slugs=args.only, skip_existing=args.skip_existing)
