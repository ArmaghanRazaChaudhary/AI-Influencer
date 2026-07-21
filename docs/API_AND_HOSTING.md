# API and Hosting Notes

This project is the upstream **AI Influencer identity and content engine**. It owns persona packages, reference faces, generated images, captions, and draft handoff packages. It does **not** own social account runtime, posting schedules, link tracking, or live DM orchestration; those belong to SNS Orchestrator.

## Core Filesystem Model

Each influencer is a folder:

```text
personas/{persona_id}/
  persona.md
  voice.md
  visual.md
  memory_boundaries.md
  content_backlog.md
  handoff.json

assets/faces/{persona_id}/
  face_reference.jpg or face_reference.png
```

Sofia example:

```text
personas/sofia_reyes/
assets/faces/Sofia/
```

Batch manifest for the 100 generated personas:

```text
personas/batch_100_manifest.json
assets/faces/vecteezy_face_sources.json
```

## Function 1: Create Influencer

Creates a new character package and optional face folder.

### Signature

```python
def create_influencer(
    persona_id: str,
    display_name: str,
    age: int,
    gender: str,
    demography: str,
    home_base: str,
    niche: str,
    line: str = "N",
    contradiction: str = "",
    signature_detail: str = "",
    voice_tone: str = "",
    visual_style: str = "",
    recurring_locations: str = "",
    face_reference_path: str | None = None,
) -> dict:
    ...
```

### Required Behavior

1. Validate `persona_id` is lowercase snake case, for example `mina_park`.
2. Create `personas/{persona_id}/`.
3. Create `assets/faces/{persona_id}/`.
4. Write the six package files:
   - `persona.md`
   - `voice.md`
   - `visual.md`
   - `memory_boundaries.md`
   - `content_backlog.md`
   - `handoff.json`
5. If `face_reference_path` is provided, copy it to:

```text
assets/faces/{persona_id}/face_reference.{ext}
```

6. Optionally register the persona in SQLite with `db.state.register_persona()`.

### Return Shape

```json
{
  "persona_id": "mina_park",
  "display_name": "Mina Park",
  "package_path": "personas/mina_park",
  "face_dir": "assets/faces/mina_park",
  "handoff_path": "personas/mina_park/handoff.json",
  "status": "draft"
}
```

### Notes

- Do not create a single JSON-only persona. The markdown folder is the source of truth.
- Every persona must have one contradiction and one signature detail.
- Keep face images as references only until continuity review passes.

## Function 2: Get All or Specific Influencers

Reads influencer packages from disk and returns summary metadata.

### Signature

```python
def get_influencers(
    persona_id: str | None = None,
    include_files: bool = False,
    include_handoff: bool = True,
) -> list[dict] | dict:
    ...
```

### Behavior

If `persona_id` is provided, return one influencer. If omitted, return all influencer packages under `personas/`, excluding `_TEMPLATE`.

Read from:

```text
personas/{persona_id}/handoff.json
personas/{persona_id}/persona.md
assets/faces/{persona_id}/face_reference.*
```

### Return Shape: List

```json
[
  {
    "persona_id": "sofia_reyes",
    "display_name": "Sofia Reyes",
    "line": "N",
    "niche": "Luxury travel",
    "package_path": "personas/sofia_reyes",
    "face_reference": "assets/faces/sofia_reyes/face_reference.jpg",
    "approval_state": "draft"
  }
]
```

### Return Shape: Specific

```json
{
  "persona_id": "mina_park",
  "display_name": "Mina Park",
  "line": "N",
  "niche": "calm technology, maker culture, urban rituals",
  "package_path": "personas/mina_park",
  "files": {
    "persona": "personas/mina_park/persona.md",
    "voice": "personas/mina_park/voice.md",
    "visual": "personas/mina_park/visual.md",
    "memory_boundaries": "personas/mina_park/memory_boundaries.md",
    "content_backlog": "personas/mina_park/content_backlog.md",
    "handoff": "personas/mina_park/handoff.json"
  },
  "face_reference": "assets/faces/mina_park/face_reference.png",
  "approval_state": "draft"
}
```

### Notes

- Prefer filesystem package discovery over relying only on SQLite. SQLite can cache/search, but markdown package folders are authoritative.
- For dashboard use, read `batch_100_manifest.json` for the generated batch and `handoff.json` for individual package state.

## Function 3: Create a Post with Image and Content

Creates a draft post for one influencer. The output is an approved-style content package row, not a live publish action.

### Signature

```python
def create_post(
    persona_id: str,
    image_path: str | None = None,
    caption: str | None = None,
    scene_prompt: str | None = None,
    platform: str = "instagram",
    status: str = "draft",
    continuity: str = "pending",
) -> dict:
    ...
```

### Behavior

1. Load persona package:

```text
personas/{persona_id}/persona.md
personas/{persona_id}/voice.md
personas/{persona_id}/visual.md
personas/{persona_id}/memory_boundaries.md
```

2. If `image_path` is missing, generate or import a new image using:
   - `assets/faces/{persona_id}/face_reference.*`
   - persona visual rules from `visual.md`
   - scene direction from `scene_prompt`

3. If `caption` is missing, generate caption from:
   - `persona.md`
   - `voice.md`
   - scene/context
   - platform rules

4. Save the image under one of:

```text
assets/output/raw/{persona_id}/
assets/output/final/{persona_id}/
```

5. Append a row or block to:

```text
personas/{persona_id}/content_backlog.md
```

6. Update `handoff.json` with the draft asset if needed.
7. Optionally insert a row in SQLite `posts` table.

### Return Shape

```json
{
  "post_id": "sof-014",
  "persona_id": "sofia_reyes",
  "platform": "instagram",
  "image_path": "assets/output/final/sofia_reyes/sof-014.png",
  "caption": "Miami woke up soft today...",
  "content_backlog_path": "personas/sofia_reyes/content_backlog.md",
  "continuity": "pending",
  "status": "draft"
}
```

### Instagram Caption Rules

- Start with a specific detail.
- Include a small opinion or confession.
- End with a question or soft engagement trigger.
- Hashtags go on a separate line.
- Never mention AI.
- Keep Line N content brand-safe unless a persona is explicitly marked otherwise.

## Suggested Internal Module Layout

Create one service module for team use:

```text
services/
  influencers.py
```

Recommended exports:

```python
create_influencer(...)
get_influencers(...)
create_post(...)
```

The service can call existing lower-level modules:

```text
db/state.py
pipeline/face_gen.py
pipeline/caption_gen.py
pipeline/content_director.py
```

## Hosting Notes

### What to Host

Host only the API/service layer and required persona assets.

Good to include:

```text
personas/
assets/faces/
assets/output/final/       # optional, if previews need generated post images
config/
db/
pipeline/
services/
requirements.txt
```

Do not expose:

```text
.env
.chatgpt_profile/
.claude/
.git/
assets/output/raw/         # optional/private working files
debug scripts
local browser sessions
```

### Environment Variables

Server `.env` should be created from `.env.example`, never committed.

Required for API image generation:

```text
OPENAI_API_KEY=
IMAGE_BACKEND=api
```

Required for caption/content generation:

```text
ANTHROPIC_API_KEY=
```

Only set social platform keys on SNS Orchestrator, not this upstream service, unless the boundary changes.

### Python Runtime

Use Python 3.9+.

Install:

```bash
pip install -r requirements.txt
```

Initialize DB:

```bash
python -c "from db.state import init_db; init_db()"
```

### Recommended Server Shape

Use FastAPI for a clean internal API:

```text
GET  /influencers
GET  /influencers/{persona_id}
POST /influencers
POST /influencers/{persona_id}/posts
GET  /health
```

Keep generated assets on persistent disk or object storage. If using Docker, mount:

```text
/app/personas
/app/assets
/app/pipeline.db
```

### Deployment Checklist

1. Create a clean production branch.
2. Remove local-only generated previews unless needed.
3. Confirm `.gitignore` excludes `.env`, browser profiles, and temporary files.
4. Set server env vars in the host dashboard.
5. Run DB initialization.
6. Run a smoke test:

```bash
python -c "from pathlib import Path; print(Path('personas/sofia_reyes/persona.md').exists())"
```

7. Test:
   - create influencer
   - get all influencers
   - get one influencer
   - create post draft
8. Confirm no endpoint can reveal API keys or private local paths.

### Vercel Note

Vercel is fine for static previews like `sofia_posts_preview.html`, but not ideal for the full Python image/content engine because:

- long image generation jobs may exceed serverless timeouts
- generated assets need persistent storage
- background jobs and review workflows are easier on a VM/container

Better hosting options for the actual engine:

- Railway
- Render
- Fly.io
- DigitalOcean App Platform
- AWS Lightsail / EC2
- a small Dockerized VPS

Use Vercel only for static galleries or dashboards that consume this API.

## License and Source Notes for Imported Faces

Vecteezy source tracking is stored at:

```text
assets/faces/vecteezy_face_sources.json
```

Free Vecteezy assets may require attribution unless covered by a Pro license. Before public or commercial use, verify each source page/license or replace faces with generated/licensed assets owned by the project.
