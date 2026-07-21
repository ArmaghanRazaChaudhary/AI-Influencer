from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "personas" / "batch_100_manifest.json"
OUT_DIR = ROOT / "assets" / "faces" / "_batch_prompts"


def build_prompt(batch: list[dict[str, object]], batch_no: int) -> str:
    lines = [
        "Create a single 5x2 sheet containing 10 separate realistic portrait photos.",
        "Each cell contains one different fictional person from the shoulders up.",
        "Use clean spacing between cells. No text, no logos, no watermark.",
        "Make the portraits varied in face shape, age, hairstyle, clothing, skin tone, and background.",
        "Natural light, realistic skin texture, calm social profile portrait style.",
        "",
        f"Batch {batch_no} order, top row left to right, then bottom row left to right:",
    ]
    for index, persona in enumerate(batch, 1):
        lines.append(
            f"{index}. {persona['name']}: {persona['age']}, {persona['gender']}, "
            f"based in {persona['base']}, niche is {persona['niche']}."
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    personas = manifest["personas"]
    for start in range(0, len(personas), 10):
        batch_no = start // 10 + 1
        prompt = build_prompt(personas[start:start + 10], batch_no)
        path = OUT_DIR / f"face_batch_{batch_no:02d}_prompt.txt"
        path.write_text(prompt, encoding="utf-8")
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
