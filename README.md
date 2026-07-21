# AI Influencer

### Persona factory + content engine for synthetic creators — identity packages, not just faces.

**AI Influencer** is an upstream **identity & content system**: each “creator” is a versioned **character package** (persona / voice / visual / memory / backlog / handoff), plus a pipeline that can draft images, short video, and captions in that persona’s voice.

Posting, scheduling, and live DMs belong to a separate orchestrator. This repo owns the durable asset and the first-draft package.

```text
Character package (markdown + handoff.json)
        │
        ▼
Content director → image (face-locked) → optional video → caption
        │
        ▼
Approved handoff package → (external) SNS Orchestrator
```

---

## What it does

| Capability | Details |
|------------|---------|
| **Character packages** | Folder-per-persona: `persona.md`, `voice.md`, `visual.md`, `memory_boundaries.md`, `content_backlog.md`, `handoff.json` |
| **Persona factory** | Template + batch tooling to scale from 1 → N fictional influencers |
| **Content director** | Decides today’s scene / mood / prompt from the package |
| **Image generation** | Face-consistent stills via OpenAI `gpt-image-1` (configurable backend) |
| **Video (optional)** | Animate stills with Higgsfield; ffmpeg post-process + metadata strip |
| **Captions** | Claude / Anthropic in the persona’s voice |
| **Dashboard UI** | Browse personas and factory output (`dashboard/`) |
| **SQLite job log** | Track generation jobs locally |

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| LLMs | **Anthropic** (captions / direction), **OpenAI** (images) |
| Video | **Higgsfield** client, **ffmpeg-python** |
| Social adapters (reference) | tweepy, instagrapi (posting largely outsourced downstream) |
| Scheduling | APScheduler |
| Optional browser route | Playwright (legacy ChatGPT web image path) |
| Config | python-dotenv |
| Frontend | Static dashboard (HTML / CSS / JS) |

---

## Privacy & what is not in this repo

| Shipped | Local only (gitignored) |
|---------|-------------------------|
| Pipeline code, dashboard, persona markdown packages | `.env` (API keys, social passwords) |
| `.env.example`, docs | `assets/faces/**` face photos |
| | `assets/output/**` generated media |
| | Spec screenshots, preview HTML |

This public fork is **detached from any company remote**. Original face libraries and campaign renders stay on your machine.

---

## Quick start

```bash
cd AI-Influencer
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# fill OPENAI_API_KEY / ANTHROPIC_API_KEY (and optional Higgsfield / social keys)
```

Add a face reference locally:

```text
assets/faces/{persona_id}/face_reference.jpg
```

Run one pipeline pass (see `main.py` CLI flags):

```bash
python main.py --help
```

Open the dashboard by serving `dashboard/` with any static file server, or open `dashboard/index.html` locally depending on your browser CORS needs.

---

## Repo map

```text
AI-Influencer/
├── main.py                 # Orchestrator CLI
├── pipeline/               # Director, face/image, video, caption, poster hooks
├── personas/               # Character packages (+ README)
├── assets/faces/           # Local face refs (binaries gitignored)
├── dashboard/              # Operator UI
├── db/                     # SQLite helpers
├── scripts/                # Factory / batch utilities
├── config/
├── docs/API_AND_HOSTING.md # Integration notes for downstream systems
├── AGENTS.md / CLAUDE.md   # Architecture context for agents
├── .env.example
└── requirements.txt
```

---

## Design notes (for engineers / hiring managers)

- **Creator = system**, not a single prompt or JPEG — packages enforce continuity and refusal rules.
- **Clear product boundary** between identity/content (this repo) and distribution/runtime (orchestrator).
- **Handoff-first API**: machine-readable `handoff.json` for approval gates and downstream queues.
- **Scale path**: G1 one persona → G2 factory (multi-persona, one operator) → G3 talking video / fleet.
- **Honest scope:** reference posting code may remain; production publishing is intentionally separate.

---

## License

MIT — see [LICENSE](LICENSE). Third-party API and model terms (OpenAI, Anthropic, Higgsfield, platform ToS) apply separately.
