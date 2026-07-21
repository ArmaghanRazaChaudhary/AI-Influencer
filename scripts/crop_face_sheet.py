from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "personas" / "batch_100_manifest.json"
FACES_DIR = ROOT / "assets" / "faces"


def crop_sheet(sheet_path: Path, start: int, cols: int = 5, rows: int = 2) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    personas = manifest["personas"][start:start + cols * rows]
    if not personas:
        raise ValueError(f"No personas found from start index {start}")

    image = Image.open(sheet_path).convert("RGB")
    width, height = image.size
    cell_w = width // cols
    cell_h = height // rows

    for index, persona in enumerate(personas):
        row = index // cols
        col = index % cols
        left = col * cell_w
        upper = row * cell_h
        right = width if col == cols - 1 else (col + 1) * cell_w
        lower = height if row == rows - 1 else (row + 1) * cell_h
        crop = image.crop((left, upper, right, lower))

        # Tight square crop centered inside the contact-sheet cell.
        cw, ch = crop.size
        side = min(cw, ch)
        x = (cw - side) // 2
        y = (ch - side) // 2
        crop = crop.crop((x, y, x + side, y + side)).resize((1024, 1024), Image.Resampling.LANCZOS)

        out_dir = FACES_DIR / persona["persona_id"]
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / "face_reference.png"
        crop.save(out_path, "PNG")
        print(f"{persona['persona_id']} -> {out_path.relative_to(ROOT)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sheet", type=Path)
    parser.add_argument("--start", type=int, required=True, help="Zero-based manifest start index")
    args = parser.parse_args()
    crop_sheet(args.sheet, args.start)


if __name__ == "__main__":
    main()
