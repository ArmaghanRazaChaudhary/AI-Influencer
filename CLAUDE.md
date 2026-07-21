# AI Influencer — Project Context

> **Authoritative spec:** `personas/README.md` + this file.
> Last updated: 2026-06-03. This file reflects the **current** architecture; earlier
> Maya / Higgsfield / instagrapi designs are retired.

---

## 1. North Star
Replicate **"Zoe"** — a synthetic AI influencer (reported $175k in 67 days, ~1,847 paying
subscribers, ~3 hrs/week) — then make it **scale from 1 persona to N**.

> **A creator is not a face, it is a system.** Zoe = a set of markdown files that Claude
> reads before every reply. The product edge: the *system that runs N personas* — templated
> character packages + automated content factory + (later) self-hosted talking video.

**Stages:** G1 Clone one persona → G2 Factory (5 personas, 1 operator) → G3 Beyond Zoe
(talking video, voice DM, multi-platform fleet).

---

## 2. Product Role & Boundary
This repo is the **upstream content & identity engine**. It creates the fictional human as
a durable asset and produces an **approved handoff package**. A **separate** product —
**SNS Orchestrator** — consumes the package and does the downstream work.

| Layer | AI Influencer (this repo) | SNS Orchestrator (separate) |
|-------|---------------------------|------------------------------|
| Persona / voice / visual / memory | **Owns** | Drift-checks |
| Image / video / caption | **Owns first-draft package** | Publishes approved package |
| Posting queue / schedule / verify | Supplies metadata | **Owns** |
| DM / replies | Provides persona + sample replies + memory rules | **Owns runtime reply** |
| Monetization routing | Offers the intense offer + CTA | **Owns link placement + tracking** |

⇒ `pipeline/poster.py` and `pipeline/scheduler.py` are **largely out of scope** now
(posting belongs to SNS Orchestrator). Kept as reference until formally removed.

---

## 3. The Character Package (the core deliverable)
A persona is **a folder of markdown**, not a JSON. Built in a **fixed order — do not reorder.**

| File | Purpose | Build step |
|------|---------|-----------|
| `persona.md` | Durable character bible. Built FIRST. Must embed **one contradiction + one signature detail** (memorability). | 1 |
| `voice.md` | Tone, word choice, refusal style, voice-clone setup | 1 |
| `visual.md` | Face refs, body/style rules, banned drift, generation method | 2 |
| `memory_boundaries.md` | What the persona can remember / disclose / refuse / escalate | 1 |
| `content_backlog.md` | post id · asset · caption · platform fit · CTA · risk note | ongoing |
| `brain.md` | **DM brain ("the heart")** — per-subscriber memory | 3 |
| `handoff.json` | Machine-readable: id, version, assets, approval state, destinations | on handoff |

- **Reference implementation:** `personas/sofia_reyes/`
- **Factory template:** `personas/_TEMPLATE/` (copy → fill → swap settings)

---

## 4. Face / Image Generation — DECISION
**Method: OpenAI `gpt-image-1` (the current OpenAI image model, "image 2.0") via the API,
fed Sofia's reference face + the fixed descriptors from `visual.md` on every call.**

- ✅ Reliable, headless, scriptable — direct HTTP, no browser, no Cloudflare.
- ✅ Code exists: `pipeline/face_gen.py` → `create_first_frame()` uses
  `client.images.edit(model="gpt-image-1", image=<face>, prompt=<scene>)`.
- ⚠️ **Consistency caveat:** `gpt-image-1` keeps *likeness* via the reference image — it is
  **not** a trained lock like LoRA, so expect minor drift across many posts. Acceptable for
  **Line N** lifestyle content. If pixel-identical lock is ever required → revisit LoRA.

**Rejected approaches:**
- ❌ **ChatGPT web / "codex" (browser automation)** — fought Cloudflare endlessly (headless
  blocked, off-screen JS throttling, login captcha). `pipeline/chatgpt_image_gen.py` is
  **superseded** — do not revive for face gen.
- ❌ **Flux 2 + LoRA** — was the spec's method; user chose OpenAI `gpt-image-1` instead to
  avoid GPU training. (Spec text in `visual.md` still references LoRA — being migrated.)

---

## 5. Lines (publishing surface / governance)
| Line | Content | Revenue | Status |
|------|---------|---------|--------|
| **N** — Normal (SFW) | Brand-safe lifestyle | IG/TikTok/YouTube → brand deals, affiliate, own products | **Prove first.** Sofia is Line N. |
| **S** — Spicy funnel | Suggestive, within platform rules | IG/TikTok → Fanvue/Passes | Separate brand |
| **A** — Adult | Explicit (Zoe-type) | Fanvue / OnlyFans | Separate entity, ring-fenced |

Stack is shared; only the publishing surface + governance differ.

---

## 6. Evidence Rule
Progress is **not** "we made prompts." Valid evidence = **character package path + generated
asset path + continuity review result + rejected-drift examples + handoff package id +
SNS Orchestrator queue receipt.**

Face acceptance target: **post 1 and post 847 are the same person.**

---

## 7. Current Progress

### ✅ Built
- **Sofia Reyes character package** — `personas/sofia_reyes/` (Line N, luxury travel).
  All 6 markdown files + `handoff.json`. Contradiction: performs carefree luxury, privately
  a control-freak ex-analyst. Signature: crescent-moon scar, left wrist.
- **Persona Factory template** — `personas/_TEMPLATE/` + `personas/README.md`.
- **`pipeline/content_director.py`** — Claude reads a persona → decides scene/mood/caption-context.
- **`pipeline/caption_gen.py`** — `generate_caption_for_persona()` writes in the persona's voice.
- **`pipeline/face_gen.py`** — `gpt-image-1` image gen (API path is the keeper).
- **`db/state.py`** — SQLite schema: `personas`, `social_accounts`, `posts` (+ legacy `jobs`).
  Lets another dev link SNS accounts to personas via `link_account()`.
- Supporting (from old build, reusable): `postprocess.py` (ffmpeg), `metadata.py` (exiftool).

### 🟡 Superseded / out of scope (kept, not deleted)
- `pipeline/chatgpt_image_gen.py` + `scripts/chatgpt_login.py` — browser route, abandoned.
- `pipeline/poster.py`, `pipeline/scheduler.py` — posting belongs to SNS Orchestrator.
- `pipeline/video_gen.py` (Higgsfield) — video is a later stage (G3).
- `main.py` — still wired to the OLD single-JSON + posting flow; needs rework for packages.

### ❌ Not built yet
- `brain.md` for Sofia + the **DM brain loop** (cron poll → load brain.md → Claude reply →
  write facts back → brain DB). Spec build-order step 3, "the heart."
- Package-aware orchestrator (replace `main.py`: load package → generate → continuity review
  → fill content_backlog → emit handoff.json). 
- Continuity-review automation (pass/fail vs `visual.md` descriptors; keep rejected examples).
- Real `gpt-image-1` wiring to Sofia's reference + descriptors (needs a real `OPENAI_API_KEY`).
- Persona Factory automation (duplicate package + swap settings programmatically).
- Per-persona dashboard (posts / followers / DM / revenue / risk).

---

## 8. Project Structure (current)
```
AI_Influencer/
├── CLAUDE.md                       # This file
├── Specifications/                 # 1-4.PNG — authoritative product spec
├── main.py                         # OLD orchestrator (needs package rework)
├── requirements.txt
├── .env                            # API keys + config
├── personas/
│   ├── README.md                   # Character Package docs
│   ├── _TEMPLATE/                  # Persona Factory template (6 files)
│   └── sofia_reyes/                # Reference persona (Line N)
│       ├── persona.md  voice.md  visual.md
│       ├── memory_boundaries.md  content_backlog.md
│       └── handoff.json            # (brain.md still to build)
├── pipeline/
│   ├── content_director.py         # Claude → scene decision        [keep]
│   ├── caption_gen.py              # Claude → caption in voice       [keep]
│   ├── face_gen.py                 # gpt-image-1 image gen           [keep, API path]
│   ├── postprocess.py              # ffmpeg                          [keep]
│   ├── metadata.py                 # exiftool                        [keep]
│   ├── chatgpt_image_gen.py        # browser route                  [superseded]
│   ├── video_gen.py                # Higgsfield                      [later / G3]
│   ├── poster.py                   # Instagram                       [SNS Orchestrator]
│   └── scheduler.py                # APScheduler                     [SNS Orchestrator]
├── scripts/
│   ├── generate_face_variants.py   # batch image gen (browser)       [superseded]
│   └── chatgpt_login.py            # browser login                   [superseded]
├── config/settings.py              # config via .env (IMAGE_BACKEND, keys)
├── db/state.py                     # SQLite: personas / social_accounts / posts
└── assets/
    ├── faces/
    │   ├── face1.jpeg              # Sofia seed face (reference)
    │   └── Sofia/                  # variant set (inconsistent — not LoRA-grade)
    ├── lora/                       # (only if LoRA path is revived)
    ├── voice/                      # voice-clone samples (later)
    └── output/{raw,final}/
```

---

## 9. Config & Keys (`.env`)
| Key | Purpose | Needed now? |
|-----|---------|-------------|
| `OPENAI_API_KEY` | `gpt-image-1` image generation | **Yes** (currently placeholder) |
| `ANTHROPIC_API_KEY` | content_director + captions + DM brain | Yes |
| `CHATGPT_EMAIL` / `CHATGPT_PASSWORD` | browser route | No (superseded) |
| `HF_API_KEY` / `HF_API_SECRET` | Higgsfield video | Later (G3) |
| `IG_*`, `X_*` | posting | No (SNS Orchestrator) |

`config/settings.py` also has `IMAGE_BACKEND` (`api` | `chatgpt`) — keep on `api`.

**System deps (for the image/video post-processing path):** `ffmpeg`, `exiftool`.

---

## 10. Build Order (next steps, in order — do not reorder)
1. ✅ `persona.md` + full character package (Sofia) — **done**
2. **Face lock** — wire `gpt-image-1` to Sofia's reference + `visual.md` descriptors; add
   continuity review; run acceptance test. *(needs real `OPENAI_API_KEY`)*
3. **DM brain** — `brain.md` + cron loop + brain DB (per-subscriber memory).
4. **Paid funnel** — handoff to SNS Orchestrator; Line N monetization (brand deals/affiliate).
5. **Scale to N** — Persona Factory automation + dashboard.

---

## 11. Environment Notes
- Windows 10, **Python 3.9** (use `from __future__ import annotations` for `X | Y` type hints).
- PowerShell shell; console is cp1252 — avoid non-ASCII (→, ✓) in `print()` statements.
- Models: captions/direction → `claude-sonnet-4-6`; quick DM replies → `claude-haiku-4-5`.
