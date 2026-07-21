from __future__ import annotations

"""
Social media posting: X (Twitter) and Instagram.
X via tweepy v4, Instagram via instagrapi.
"""

import random
import time
from pathlib import Path

import tweepy
from instagrapi import Client as IGClient

from config.settings import (
    X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET, X_BEARER_TOKEN,
    IG_USERNAME, IG_PASSWORD,
)


# ---------------------------------------------------------------------------
# X / Twitter
# ---------------------------------------------------------------------------

def _x_client() -> tweepy.Client:
    return tweepy.Client(
        bearer_token=X_BEARER_TOKEN,
        consumer_key=X_API_KEY,
        consumer_secret=X_API_SECRET,
        access_token=X_ACCESS_TOKEN,
        access_token_secret=X_ACCESS_TOKEN_SECRET,
    )


def _x_v1_api() -> tweepy.API:
    auth = tweepy.OAuth1UserHandler(
        X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_TOKEN_SECRET
    )
    return tweepy.API(auth)


def post_to_x(
    caption: str,
    media_path: str | Path | None = None,
) -> str:
    """Post a tweet with optional media. Returns the tweet ID."""
    client = _x_client()
    media_id = None

    if media_path:
        api_v1 = _x_v1_api()
        media = api_v1.media_upload(filename=str(media_path))
        media_id = media.media_id

    if media_id:
        response = client.create_tweet(text=caption, media_ids=[media_id])
    else:
        response = client.create_tweet(text=caption)

    return str(response.data["id"])


# ---------------------------------------------------------------------------
# Instagram
# ---------------------------------------------------------------------------

_ig_client: IGClient | None = None


def _get_ig_client() -> IGClient:
    global _ig_client
    if _ig_client is None:
        _ig_client = IGClient()
        _ig_client.login(IG_USERNAME, IG_PASSWORD)
    return _ig_client


def post_to_instagram(
    caption: str,
    media_path: str | Path,
) -> str:
    """
    Post a photo or video to Instagram. Returns the media ID.
    Automatically detects image vs. video by extension.
    """
    media_path = Path(media_path)
    cl = _get_ig_client()

    # Human-like delay before posting
    time.sleep(random.uniform(3, 8))

    suffix = media_path.suffix.lower()
    if suffix in (".mp4", ".mov", ".avi"):
        media = cl.video_upload(media_path, caption=caption)
    else:
        media = cl.photo_upload(media_path, caption=caption)

    return str(media.id)


# ---------------------------------------------------------------------------
# Multi-platform dispatcher
# ---------------------------------------------------------------------------

def post(
    caption: str,
    media_path: str | Path | None = None,
    platforms: list[str] | None = None,
) -> dict[str, str]:
    """
    Post to one or more platforms.

    Args:
        caption: The caption/text to post.
        media_path: Path to image or video file.
        platforms: List of 'x', 'instagram'. Defaults to both.

    Returns:
        Dict mapping platform name → post ID.
    """
    if platforms is None:
        platforms = ["x", "instagram"]

    results = {}

    if "x" in platforms:
        x_caption = caption[:280]  # X hard limit
        post_id = post_to_x(x_caption, media_path)
        results["x"] = post_id

    if "instagram" in platforms and media_path:
        # Add human-like jitter between platform posts
        time.sleep(random.uniform(10, 30))
        post_id = post_to_instagram(caption, media_path)
        results["instagram"] = post_id

    return results
