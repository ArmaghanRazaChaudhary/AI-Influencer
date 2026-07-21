from __future__ import annotations

"""
Caption and hashtag generation via Anthropic API.
Generates platform-native captions tuned to the persona's voice and engagement triggers.
"""

import anthropic
from config.settings import ANTHROPIC_API_KEY, NICHE

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

_SYSTEM_PROMPT = """You are a social media strategist for AI influencer accounts.
You write short, punchy captions that feel authentic and drive engagement.
Never mention AI, never use generic phrases like "living my best life".
Write like a real person, not a brand. Use 1-3 relevant emojis max.
End with a question or strong opinion to trigger comments."""

_NICHE_CONTEXTS = {
    "anime_girl": "anime fan girl who streams, loves Japanese culture, has strong opinions on characters and arcs",
    "cosplay": "cosplayer who travels to conventions, reviews costumes, debates canon accuracy",
    "football_fangirl": "passionate football fan with a favorite player she defends aggressively",
    "goth_alt": "alt/goth aesthetic girl, dark humor, existential takes, underground music taste",
    "travel_luxury": "solo female traveler hitting high-profile events and cities, aspirational but real",
}

_PLATFORM_INSTRUCTIONS = {
    "instagram": "Max 150 words. Include 10-15 hashtags on a new line.",
    "x": "Max 240 characters including hashtags. 2-4 hashtags only.",
    "tiktok": "Max 100 words. 5-8 trending hashtags.",
}


def generate_caption_for_persona(
    persona: dict,
    context: str = "",
    platform: str = "instagram",
    include_hashtags: bool = True,
) -> str:
    """Generate a caption in the persona's own voice using their full character profile."""
    user_prompt = f"""You are writing a caption for {persona['name']}.

About her:
- Voice: {persona.get('voice', '')}
- Personality: {persona.get('personality', '')}
- Lifestyle: {persona.get('lifestyle', '')}
- Location: {persona.get('location', '')}

Post context: {context or 'A typical moment from her life.'}
Platform: {platform}
{_PLATFORM_INSTRUCTIONS.get(platform, '')}
{'Include hashtags.' if include_hashtags else 'No hashtags.'}

Write the caption in her voice. Output caption text only — no labels, no quotation marks."""

    message = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )
    return message.content[0].text.strip()


def generate_caption(
    niche: str = NICHE,
    context: str = "",
    platform: str = "instagram",
    include_hashtags: bool = True,
) -> str:
    """Generate a caption using a niche key or free-form description (legacy path)."""
    niche_desc = _NICHE_CONTEXTS.get(niche, niche)

    user_prompt = f"""
Niche: {niche_desc}
Platform: {platform}
{f'Context for this post: {context}' if context else ''}
{_PLATFORM_INSTRUCTIONS.get(platform, '')}
{'Include hashtags.' if include_hashtags else 'No hashtags.'}

Write the caption now:
""".strip()

    message = _client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=400,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    return message.content[0].text.strip()


def generate_reply(
    comment: str,
    niche: str = NICHE,
) -> str:
    """Generate a short reply to a comment to boost engagement."""
    niche_desc = _NICHE_CONTEXTS.get(niche, niche)

    message = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=80,
        system=_SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": (
                f"You are a {niche_desc}. Reply to this comment in 1-2 sentences, "
                f"stay in character, be engaging: \"{comment}\""
            ),
        }],
    )
    return message.content[0].text.strip()
