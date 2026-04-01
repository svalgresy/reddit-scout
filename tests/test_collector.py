"""Tests collector.py."""
from src.collector import (
    RedditPost, parse_listing, is_weak_signal,
    matches_keywords, filter_posts, build_url,
)


def test_build_url():
    url = build_url("sysadmin", limit=25, time_filter="day")
    assert "sysadmin" in url
    assert "limit=25" in url
    assert "t=day" in url


def test_parse_listing_valid():
    raw = {
        "data": {
            "children": [
                {
                    "kind": "t3",
                    "data": {
                        "id": "abc123", "title": "Test post",
                        "subreddit": "sysadmin", "score": 42,
                        "num_comments": 15, "url": "https://example.com",
                        "permalink": "/r/sysadmin/comments/abc123/test/",
                        "selftext": "Hello world", "created_utc": 1700000000,
                        "stickied": False, "link_flair_text": None,
                        "removed_by_category": None,
                    },
                }
            ]
        }
    }
    posts = parse_listing(raw, "sysadmin")
    assert len(posts) == 1
    assert posts[0].id == "abc123"
    assert posts[0].score == 42


def test_parse_listing_filters_stickied():
    raw = {
        "data": {
            "children": [
                {
                    "kind": "t3",
                    "data": {
                        "id": "s1", "title": "Stickied",
                        "subreddit": "test", "score": 100,
                        "num_comments": 50, "url": "", "permalink": "/r/test/s1/",
                        "selftext": "", "created_utc": 0,
                        "stickied": True, "link_flair_text": None,
                        "removed_by_category": None,
                    },
                }
            ]
        }
    }
    posts = parse_listing(raw, "test")
    assert len(posts) == 0


def test_is_weak_signal():
    assert is_weak_signal(score=50, num_comments=30) is True
    assert is_weak_signal(score=200, num_comments=30) is False
    assert is_weak_signal(score=50, num_comments=5) is False


def test_matches_keywords():
    assert "VMware" in matches_keywords("New CVE in VMware ESXi")
    assert "ESXi" in matches_keywords("New CVE in VMware ESXi")
    assert "CVE" in matches_keywords("New CVE in VMware ESXi")
    assert matches_keywords("Hello world") == []


def test_filter_posts_dedup():
    p1 = RedditPost(id="a", title="A", subreddit="s", score=20,
                     num_comments=5, url="", permalink="/a/", selftext="",
                     created_utc=0)
    p2 = RedditPost(id="a", title="A dup", subreddit="s", score=20,
                     num_comments=5, url="", permalink="/a/", selftext="",
                     created_utc=0)
    p3 = RedditPost(id="b", title="B", subreddit="s", score=30,
                     num_comments=10, url="", permalink="/b/", selftext="",
                     created_utc=0)
    result = filter_posts([p1, p2, p3], seen_ids=set())
    assert len(result) == 2
