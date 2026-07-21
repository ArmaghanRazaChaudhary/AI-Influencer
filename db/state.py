from __future__ import annotations

"""
Database layer — SQLite via plain sqlite3.

Tables:
  personas        — one row per AI influencer character
  social_accounts — one row per platform account, linked to a persona
  posts           — one row per pipeline run / published post

Designed so a separate developer can register social accounts and link them
to personas without touching the pipeline code.
"""

import json
import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "pipeline.db"


def _conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys = ON")
    return c


# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

def init_db() -> None:
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS personas (
                id          TEXT PRIMARY KEY,
                name        TEXT NOT NULL,
                niche       TEXT NOT NULL,
                json_path   TEXT NOT NULL,
                face_dir    TEXT,
                active      INTEGER NOT NULL DEFAULT 1,
                created_at  TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS social_accounts (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                persona_id  TEXT NOT NULL REFERENCES personas(id) ON DELETE CASCADE,
                platform    TEXT NOT NULL,
                username    TEXT NOT NULL,
                account_id  TEXT,
                status      TEXT NOT NULL DEFAULT 'active',
                notes       TEXT,
                linked_at   TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(platform, username)
            );

            CREATE TABLE IF NOT EXISTS posts (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                persona_id   TEXT REFERENCES personas(id),
                account_id   INTEGER REFERENCES social_accounts(id),
                platform     TEXT,
                scene_prompt TEXT,
                image_path   TEXT,
                video_path   TEXT,
                caption      TEXT,
                post_id      TEXT,
                status       TEXT NOT NULL DEFAULT 'pending',
                error        TEXT,
                created_at   TEXT NOT NULL DEFAULT (datetime('now')),
                posted_at    TEXT
            );

            -- Keep old jobs table alive for any existing data
            CREATE TABLE IF NOT EXISTS jobs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at  TEXT NOT NULL,
                status      TEXT NOT NULL DEFAULT 'pending',
                niche       TEXT,
                face_path   TEXT,
                ref_path    TEXT,
                raw_path    TEXT,
                final_path  TEXT,
                caption     TEXT,
                platform    TEXT,
                post_id     TEXT,
                posted_at   TEXT,
                error       TEXT,
                meta        TEXT
            );
        """)


# ---------------------------------------------------------------------------
# Personas
# ---------------------------------------------------------------------------

def register_persona(
    persona_id: str,
    name: str,
    niche: str,
    json_path: str,
    face_dir: str = "",
) -> None:
    """Insert or update a persona row. Safe to call on every startup."""
    with _conn() as c:
        c.execute("""
            INSERT INTO personas (id, name, niche, json_path, face_dir)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name      = excluded.name,
                niche     = excluded.niche,
                json_path = excluded.json_path,
                face_dir  = excluded.face_dir
        """, (persona_id, name, niche, json_path, face_dir))


def list_personas(active_only: bool = True) -> list[dict]:
    with _conn() as c:
        q = "SELECT * FROM personas"
        if active_only:
            q += " WHERE active = 1"
        q += " ORDER BY name"
        return [dict(r) for r in c.execute(q).fetchall()]


def set_persona_active(persona_id: str, active: bool) -> None:
    with _conn() as c:
        c.execute("UPDATE personas SET active = ? WHERE id = ?", (int(active), persona_id))


# ---------------------------------------------------------------------------
# Social accounts  (the other dev's main surface)
# ---------------------------------------------------------------------------

def link_account(
    persona_id: str,
    platform: str,
    username: str,
    account_id: str = "",
    notes: str = "",
) -> int:
    """
    Link a social media account to a persona.
    Returns the social_accounts.id of the new (or existing) row.

    platform: "instagram" | "tiktok" | "x"
    username: the handle, e.g. "@sofia.luxe"
    account_id: platform-native numeric/string ID (optional but useful for API posting)
    notes: anything useful — e.g. "verified", "main account", "backup"
    """
    with _conn() as c:
        cur = c.execute("""
            INSERT INTO social_accounts (persona_id, platform, username, account_id, notes)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(platform, username) DO UPDATE SET
                persona_id = excluded.persona_id,
                account_id = excluded.account_id,
                notes      = excluded.notes,
                status     = 'active'
            RETURNING id
        """, (persona_id, platform, username, account_id, notes))
        return cur.fetchone()[0]


def get_persona_accounts(persona_id: str, platform: str | None = None) -> list[dict]:
    """All active accounts linked to a persona, optionally filtered by platform."""
    with _conn() as c:
        q = "SELECT * FROM social_accounts WHERE persona_id = ? AND status = 'active'"
        params: list = [persona_id]
        if platform:
            q += " AND platform = ?"
            params.append(platform)
        q += " ORDER BY platform, username"
        return [dict(r) for r in c.execute(q, params).fetchall()]


def set_account_status(account_id: int, status: str) -> None:
    """Set account status: 'active' | 'paused' | 'banned'."""
    with _conn() as c:
        c.execute("UPDATE social_accounts SET status = ? WHERE id = ?", (status, account_id))


def list_all_accounts(platform: str | None = None) -> list[dict]:
    """List every account with its linked persona name — useful for the other dev."""
    with _conn() as c:
        q = """
            SELECT sa.*, p.name AS persona_name, p.niche
            FROM social_accounts sa
            JOIN personas p ON sa.persona_id = p.id
        """
        params: list = []
        if platform:
            q += " WHERE sa.platform = ?"
            params.append(platform)
        q += " ORDER BY sa.platform, p.name"
        return [dict(r) for r in c.execute(q, params).fetchall()]


# ---------------------------------------------------------------------------
# Posts  (pipeline writes here)
# ---------------------------------------------------------------------------

def create_post(
    persona_id: str,
    scene_prompt: str,
    account_id: int | None = None,
    platform: str | None = None,
) -> int:
    with _conn() as c:
        cur = c.execute("""
            INSERT INTO posts (persona_id, account_id, platform, scene_prompt)
            VALUES (?, ?, ?, ?)
        """, (persona_id, account_id, platform, scene_prompt))
        return cur.lastrowid


def update_post(post_id: int, **fields) -> None:
    if not fields:
        return
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [post_id]
    with _conn() as c:
        c.execute(f"UPDATE posts SET {set_clause} WHERE id = ?", values)


def get_post(post_id: int) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM posts WHERE id = ?", (post_id,)).fetchone()
        return dict(row) if row else None


def get_recent_posts(persona_id: str | None = None, limit: int = 20) -> list[dict]:
    with _conn() as c:
        q = "SELECT * FROM posts WHERE status = 'posted'"
        params: list = []
        if persona_id:
            q += " AND persona_id = ?"
            params.append(persona_id)
        q += " ORDER BY posted_at DESC LIMIT ?"
        params.append(limit)
        return [dict(r) for r in c.execute(q, params).fetchall()]


# ---------------------------------------------------------------------------
# Legacy shims — keep main.py working without changes
# ---------------------------------------------------------------------------

def create_job(niche: str, face_path: str, ref_path: str) -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO jobs (created_at, status, niche, face_path, ref_path) VALUES (?,?,?,?,?)",
            (datetime.utcnow().isoformat(), "pending", niche, face_path, ref_path),
        )
        return cur.lastrowid


def update_job(job_id: int, **fields) -> None:
    if not fields:
        return
    if "meta" in fields and isinstance(fields["meta"], dict):
        fields["meta"] = json.dumps(fields["meta"])
    set_clause = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [job_id]
    with _conn() as c:
        c.execute(f"UPDATE jobs SET {set_clause} WHERE id = ?", values)


def get_job(job_id: int) -> dict | None:
    with _conn() as c:
        row = c.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        return dict(row) if row else None
