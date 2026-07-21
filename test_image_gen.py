"""
Quick test: generate a posed scene image from a face photo.
Run: python test_image_gen.py
Output saved to assets/output/raw/
"""

import sys
from pathlib import Path

from dotenv import load_dotenv
load_dotenv()

from config.settings import FACES_DIR, RAW_DIR
from pipeline.face_gen import create_first_frame

def main():
    # Find face images
    faces = list(FACES_DIR.glob("*.jpg")) + list(FACES_DIR.glob("*.jpeg")) + list(FACES_DIR.glob("*.png"))

    if not faces:
        print(f"No face images found in {FACES_DIR}")
        print("Add a JPG or PNG face photo to assets/faces/ and try again.")
        sys.exit(1)

    face = faces[0]
    print(f"Using face: {face.name}")
    print("Generating scene image via gpt-image-1...")

    output = create_first_frame(face)

    print(f"\nDone! Image saved to:\n  {output}")
    print("\nOpen it and check the quality before we add video generation.")

if __name__ == "__main__":
    main()
