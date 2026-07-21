from __future__ import annotations

"""
Content Director — the LLM brain of the pipeline.
Reads a persona JSON and decides what this influencer should post today.
Returns a structured ContentDecision consumed by face_gen and caption_gen.
"""

import json
import random
from dataclasses import dataclass
from pathlib import Path

import anthropic

from config.settings import ANTHROPIC_API_KEY

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)


@dataclass
class ContentDecision:
    scene_prompt: str    # fed to gpt-image-1 (full image generation instruction)
    caption_context: str # fed to caption_gen (notes for the caption writer)
    location: str        # e.g. "Santorini, Greece"
    mood: str            # e.g. "golden hour, relaxed, aspirational"


_SYSTEM_PROMPT = """You are the creative director for a social media influencer.
You are given a persona — a complete character profile. Your job is to decide what this person
would authentically post today on Instagram.

Output valid JSON only, with these exact fields:
{
  "scene_prompt": "Detailed image generation prompt. Describe: exact location, outfit with specific brands if they match the persona, body position, lighting, time of day, mood, background details. End with: photorealistic lifestyle photo, shot on iPhone, natural lighting, social media quality. Written for gpt-image-1 to generate a photorealistic scene featuring this person.",
  "caption_context": "2-3 sentences of context for this post — what happened, how she felt, what she wants followers to take away. Written as notes for the caption writer, not the caption itself.",
  "location": "City, Country where the scene takes place",
  "mood": "2-4 adjectives describing the mood (e.g. golden hour, laid-back, aspirational)"
}

Rules:
- Vary the type of content — not every post is a pool or a view
- Stay true to the persona's lifestyle, things they own, and recurring locations
- Make it feel like a real moment from her actual day — candid, lived-in
- Use specific real locations, hotels, or landmarks when possible
- Never mention AI, never use generic phrases like 'living my best life'"""

_VARIETY_NUDGES = [
    "Focus on a quiet morning moment — hotel room light, coffee, getting ready.",
    "Focus on travel — in transit, arriving somewhere, airport, train, or yacht.",
    "Focus on a social scene — dinner, event, bar, table of friends.",
    "Focus on a private, introspective moment — a view, journaling, reading by water.",
    "Focus on fashion — outfit detail, a boutique, a mirror selfie with context.",
    "Focus on food and drink — an exceptional meal, a cocktail, a rooftop bar.",
    "Focus on a luxury experience — spa, yacht deck, private villa pool, penthouse balcony.",
    "Focus on exploring a city on foot — street, market, alley, local hidden spot.",
]


def decide(persona_path: str | Path) -> ContentDecision:
    """Read a persona and return today's content decision."""
    persona = json.loads(Path(persona_path).read_text(encoding="utf-8"))
    nudge = random.choice(_VARIETY_NUDGES)

    user_prompt = f"""Persona:
{json.dumps(persona, indent=2)}

Today's creative direction: {nudge}

Decide what {persona['name']} posts today. Output JSON only — no markdown fences."""

    response = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=700,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if the model includes them anyway
    if raw.startswith("```"):
        raw = raw[raw.index("{"):]
        raw = raw[: raw.rindex("}") + 1]

    data = json.loads(raw)
    return ContentDecision(
        scene_prompt=data["scene_prompt"],
        caption_context=data["caption_context"],
        location=data["location"],
        mood=data["mood"],
    )
