import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# API keys
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
# Higgsfield uses two keys: HF_API_KEY + HF_API_SECRET
# The higgsfield_client SDK reads these automatically from env — no manual wiring needed
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]

# ChatGPT web credentials (used for auto-login when IMAGE_BACKEND=chatgpt)
# Optional — if not set, the browser opens for manual login on first run
CHATGPT_EMAIL = os.getenv("CHATGPT_EMAIL", "")
CHATGPT_PASSWORD = os.getenv("CHATGPT_PASSWORD", "")

X_API_KEY = os.environ["X_API_KEY"]
X_API_SECRET = os.environ["X_API_SECRET"]
X_ACCESS_TOKEN = os.environ["X_ACCESS_TOKEN"]
X_ACCESS_TOKEN_SECRET = os.environ["X_ACCESS_TOKEN_SECRET"]
X_BEARER_TOKEN = os.environ["X_BEARER_TOKEN"]

IG_USERNAME = os.environ["IG_USERNAME"]
IG_PASSWORD = os.environ["IG_PASSWORD"]

# Paths
OUTPUT_DIR = BASE_DIR / os.getenv("OUTPUT_DIR", "assets/output")
RAW_DIR = OUTPUT_DIR / "raw"
FINAL_DIR = OUTPUT_DIR / "final"
FACES_DIR = BASE_DIR / os.getenv("FACES_DIR", "assets/faces")
REFERENCES_DIR = BASE_DIR / os.getenv("REFERENCES_DIR", "assets/references")

for d in [OUTPUT_DIR, RAW_DIR, FINAL_DIR, FACES_DIR, REFERENCES_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Pipeline behaviour
NICHE = os.getenv("NICHE", "anime_girl")
POSTS_PER_DAY = int(os.getenv("POSTS_PER_DAY", 3))
# Image generation backend: "api" (OpenAI gpt-image-1), "chatgpt" (web UI via
# Playwright), or "livepair" (LivePair i2i — keeps the persona face across scenes)
IMAGE_BACKEND = os.getenv("IMAGE_BACKEND", "api")

# LivePair (livepairai.com) — prepaid per-result image/video generation.
# Create a key at https://livepairai.com/settings (billed per result, no sub).
LIVEPAIR_API_KEY = os.getenv("LP_KEY", "")
LIVEPAIR_BASE_URL = os.getenv("LIVEPAIR_BASE_URL", "https://livepairai.com").rstrip("/")
LIVEPAIR_IMAGE_MODEL = os.getenv("LIVEPAIR_IMAGE_MODEL", "qwen-image-3-edit")
LIVEPAIR_VIDEO_MODEL = os.getenv("LIVEPAIR_VIDEO_MODEL", "wan-3.0-i2v")

# Video generation backend: "higgsfield" (default) or "livepair"
VIDEO_BACKEND = os.getenv("VIDEO_BACKEND", "higgsfield")

# Post-processing defaults (from the guide)
POSTPROCESS = {
    "grain": 40,
    "sharpness": 20,
    "brightness": -7,
    "vignette": 12,
}

# Higgsfield — dop-turbo (fastest), dop-preview (balanced), dop-lite
HIGGSFIELD_MODEL = os.getenv("HIGGSFIELD_MODEL", "dop-preview")
# Motion style UUID — get full list from cloud.higgsfield.ai/motion-ids
HIGGSFIELD_MOTION_ID = os.getenv("HIGGSFIELD_MOTION_ID", "c5881721-05b1-47d9-94d6-0203863114e1")
HIGGSFIELD_MOTION_STRENGTH = float(os.getenv("HIGGSFIELD_MOTION_STRENGTH", "0.8"))
