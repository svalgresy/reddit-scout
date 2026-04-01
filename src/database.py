"""SQLite persistence — posts, trends, sentiment, runs."""

import json
import os
import sqlite3
from datetime import datetime, timezone, timedelta
from contextlib import contextmanager

from src import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reddit_id TEXT UNIQUE,
    title TEXT NOT NULL,
    subreddit TEXT NOT NULL,
    score INTEGER,
    num_comments INTEGER,
    url TEXT,
    permalink TEXT,
    selftext TEXT,
    created_utc REAL,
    fetched_at TEXT NOT NULL,
    is_weak_signal INTEGER DEFAULT 0,
    ai_score INTEGER DEFAULT 0,
    ai_category TEXT DEFAULT 'IGNORE',
    run_id TEXT
);

CREATE TABLE IF NOT EXISTS trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL,
    topic TEXT NOT NULL,
    summary TEXT,
    sentiment TEXT,
    momentum TEXT,
    importance_score INTEGER DEFAULT 0,
    evidence TEXT,
    detected_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS sentiment_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT,
    subreddit TEXT NOT NULL,
    score REAL NOT NULL,
    label TEXT NOT NULL,
    dominant_emotions TEXT,
    sample_size INTEGER,
    measured_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    posts_scanned INTEGER,
    posts_retained INTEGER,
    trends_count INTEGER,
    perplexity_calls INTEGER DEFAULT 0,
    report_path TEXT
);

CREATE INDEX IF NOT EXISTS idx_posts_reddit_id ON posts(reddit_id);
CREATE INDEX IF NOT EXISTS idx_posts_subreddit ON posts(subreddit);
CREATE INDEX IF NOT EXISTS idx_posts_fetched ON posts(fetched_at);
CREATE INDEX IF NOT EXISTS idx_trends_run ON trends(run_id);
CREATE INDEX IF NOT EXISTS idx_sentiment_sub ON sentiment_history(subreddit, measured_at);
"""


@contextmanager
def get_db():
    os.makedirs(os.path.dirname(config.DB_PATH) or ".", exist_ok=True)
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript(SCHEMA)


def save_run(run_id: str):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO runs (id, started_at) VALUES (?, ?)",
            (run_id, datetime.now(timezone.utc).isoformat()),
        )


def complete_run(run_id: str, posts_scanned: int, posts_retained: int,
                 trends_count: int, perplexity_calls: int, report_path: str):
    with get_db() as conn:
        conn.execute(
            """UPDATE runs SET completed_at=?, posts_scanned=?, posts_retained=?,
               trends_count=?, perplexity_calls=?, report_path=? WHERE id=?""",
            (datetime.now(timezone.utc).isoformat(), posts_scanned, posts_retained,
             trends_count, perplexity_calls, report_path, run_id),
        )


def save_posts(posts: list[dict], run_id: str):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        for p in posts:
            try:
                conn.execute(
                    """INSERT OR IGNORE INTO posts
                       (reddit_id, title, subreddit, score, num_comments, url, permalink,
                        selftext, created_utc, fetched_at, is_weak_signal, ai_score, ai_category, run_id)
                       VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (p["id"], p["title"], p["subreddit"], p["score"], p["num_comments"],
                     p.get("url", ""), p.get("permalink", ""), p.get("selftext", "")[:1000],
                     p.get("created_utc", 0), now,
                     1 if p.get("is_weak_signal") else 0,
                     p.get("ai_score", 0), p.get("ai_category", "IGNORE"), run_id),
                )
            except sqlite3.IntegrityError:
                pass


def is_post_seen(reddit_id: str) -> bool:
    with get_db() as conn:
        row = conn.execute("SELECT 1 FROM posts WHERE reddit_id=?", (reddit_id,)).fetchone()
        return row is not None


def get_seen_ids() -> set[str]:
    with get_db() as conn:
        rows = conn.execute("SELECT reddit_id FROM posts").fetchall()
        return {r["reddit_id"] for r in rows}


def save_trends(trends: list[dict], run_id: str):
    now = datetime.now(timezone.utc).isoformat()
    with get_db() as conn:
        for t in trends:
            conn.execute(
                """INSERT INTO trends (run_id, topic, summary, sentiment, momentum,
                   importance_score, evidence, detected_at) VALUES (?,?,?,?,?,?,?,?)""",
                (run_id, t.get("topic", ""), t.get("summary", ""),
                 t.get("sentiment", ""), t.get("momentum", ""),
                 t.get("score", 0),
                 json.dumps(t.get("evidence", []), ensure_ascii=False), now),
            )


def save_sentiment(run_id: str, subreddit: str, score: float, label: str,
                   dominant_emotions: str, sample_size: int):
    with get_db() as conn:
        conn.execute(
            """INSERT INTO sentiment_history
               (run_id, subreddit, score, label, dominant_emotions, sample_size, measured_at)
               VALUES (?,?,?,?,?,?,?)""",
            (run_id, subreddit, score, label, dominant_emotions, sample_size,
             datetime.now(timezone.utc).isoformat()),
        )


def get_sentiment_evolution(subreddit: str, limit: int = 6) -> list[dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT score, label, measured_at FROM sentiment_history WHERE subreddit=? ORDER BY measured_at DESC LIMIT ?",
            (subreddit, limit),
        ).fetchall()
        return [dict(r) for r in rows]


def get_previous_trends() -> list[dict]:
    with get_db() as conn:
        last_run = conn.execute(
            "SELECT id FROM runs WHERE completed_at IS NOT NULL ORDER BY completed_at DESC LIMIT 1 OFFSET 1"
        ).fetchone()
        if not last_run:
            return []
        rows = conn.execute(
            "SELECT topic, summary, sentiment, momentum FROM trends WHERE run_id=?",
            (last_run["id"],),
        ).fetchall()
        return [dict(r) for r in rows]


def get_history_comparison() -> dict:
    with get_db() as conn:
        runs = conn.execute(
            "SELECT id, completed_at FROM runs WHERE completed_at IS NOT NULL ORDER BY completed_at DESC LIMIT 2"
        ).fetchall()
        if len(runs) < 2:
            return {}
        current = {r["topic"] for r in conn.execute(
            "SELECT topic FROM trends WHERE run_id=?", (runs[0]["id"],)).fetchall()}
        previous = {r["topic"] for r in conn.execute(
            "SELECT topic FROM trends WHERE run_id=?", (runs[1]["id"],)).fetchall()}
        return {
            "new_trends": list(current - previous),
            "disappeared": list(previous - current),
            "persistent": list(current & previous),
            "previous_run": runs[1]["completed_at"],
        }


def purge_old_posts():
    cutoff = (datetime.now(timezone.utc) - timedelta(days=config.DEDUP_TTL_DAYS)).isoformat()
    with get_db() as conn:
        conn.execute("DELETE FROM posts WHERE fetched_at < ?", (cutoff,))
