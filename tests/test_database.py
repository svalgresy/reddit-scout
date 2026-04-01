"""Tests database.py."""
import os
import tempfile
from unittest.mock import patch
from src.database import init_db, save_run, complete_run, save_posts, get_db, is_post_seen, purge_old_posts


def test_init_and_save_run(tmp_path):
    db_path = str(tmp_path / "test.db")
    with patch("src.config.DB_PATH", db_path):
        init_db()
        save_run("run-001")
        with get_db() as conn:
            row = conn.execute("SELECT id FROM runs WHERE id='run-001'").fetchone()
            assert row is not None


def test_save_and_query_posts(tmp_path):
    db_path = str(tmp_path / "test.db")
    with patch("src.config.DB_PATH", db_path):
        init_db()
        save_run("run-002")
        posts = [
            {"id": "abc", "title": "Test", "subreddit": "sysadmin",
             "score": 100, "num_comments": 20, "url": "", "permalink": "/r/sysadmin/abc/",
             "selftext": "", "created_utc": 1700000000, "is_weak_signal": False,
             "ai_score": 85, "ai_category": "TOP"},
        ]
        save_posts(posts, "run-002")
        assert is_post_seen("abc")
        assert not is_post_seen("xyz")


def test_purge_old_posts(tmp_path):
    db_path = str(tmp_path / "test.db")
    with patch("src.config.DB_PATH", db_path):
        init_db()
        save_run("run-003")
        with get_db() as conn:
            conn.execute(
                "INSERT INTO posts (reddit_id, title, subreddit, score, num_comments, fetched_at, ai_score, ai_category) VALUES (?,?,?,?,?,?,?,?)",
                ("old1", "Old post", "test", 10, 5, "2025-01-01T00:00:00+00:00", 0, "IGNORE"),
            )
        purge_old_posts()
        assert not is_post_seen("old1")
