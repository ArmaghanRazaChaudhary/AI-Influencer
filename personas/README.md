# Personas — Character Packages

Per the product spec, **a creator is not a face, it is a system.** Each influencer ships
as a **Character Package** (a folder), not a single JSON. This is the durable asset the
AI Influencer product produces and hands off downstream.

## Package contents (build order — do NOT reorder)

| File | Purpose | Build step |
|------|---------|-----------|
| `persona.md` | Durable character bible. Built FIRST, before any face work. Must embed **one contradiction + one signature detail**. | 1 |
| `voice.md` | Tone, word choice, refusal style, voice-clone setup | 1 |
| `visual.md` | Face refs, body/style rules, banned drift, seed/LoRA/reference method. Face is locked by **Flux 2 + LoRA** (not gpt-image-1, not ChatGPT). | 2 |
| `memory_boundaries.md` | What the persona can remember, disclose, refuse, escalate | 1 |
| `content_backlog.md` | post id · asset · caption · platform fit · CTA · risk note | ongoing |
| `brain.md` | DM brain — per-subscriber memory, the "heart". Cron polls inbox → loads brain.md → the LLM replies → writes facts back. | 3 |
| `handoff.json` | Machine-readable: persona id, version, assets, approval state, destinations | on handoff |

## Acceptance gate (spec §7 — evidence, not "we made prompts")
A package is real only with: character package path · generated asset path ·
continuity review result · rejected-drift examples · handoff package id ·
SNS Orchestrator queue receipt.

Face acceptance: **post 1 and post 847 are the same person** (LoRA-locked).

## Product boundary
**AI Influencer** (this repo) = upstream identity & content engine. Owns persona/voice/
visual/memory + first-draft image/video/caption package + intense offer/CTA.
**SNS Orchestrator** (separate product) = downstream. Owns posting queue/schedule/verify,
DM runtime reply, link placement + tracking. It consumes our approved `handoff.json`.

## Lines
- **N** — Normal / SFW (brand-safe). Prove the method here first.
- **S** — Spicy funnel (SFW → paid), under a separate brand.
- **A** — Adult (Zoe-type), fully ring-fenced separate entity.

## Scale to N (Persona Factory)
New character = copy `_TEMPLATE/`, fill the files, swap settings, retrain LoRA.
`brain.md` is one shared mechanism → many personas × many subscribers in a brain DB.

## Current personas
- `sofia_reyes/` — Line N, luxury travel. **Reference implementation.** Status: persona package built; LoRA not yet trained.
