"""Collecte Reddit via API publique .json (endpoint local)."""

import json
import time
import urllib.request
from dataclasses import dataclass, field

from src import config


@dataclass
class RedditPost:
    id: str
    title: str
    subreddit: str
    score: int
    num_comments: int
    url: str
    permalink: str
    selftext: str
    created_utc: float
    top_comments: list[str] = field(default_factory=list)
    matched_keywords: list[str] = field(default_factory=list)
    is_weak_signal: bool = False
    comment_score_ratio: float = 0.0
    ai_score: int = 0
    ai_category: str = ""


EXCLUDED_FLAIRS = {"hiring", "job", "career", "recrutement", "megathread"}


def build_url(subreddit: str, limit: int = 25, time_filter: str = "day") -> str:
    return f"https://www.reddit.com/r/{subreddit}/top.json?limit={limit}&t={time_filter}"


def _fetch_json(url: str) -> dict:
    """Fetch JSON from Reddit public API with rate limiting."""
    req = urllib.request.Request(url, headers={"User-Agent": config.USER_AGENT})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def parse_listing(data: dict, subreddit: str) -> list[RedditPost]:
    posts = []
    for child in data.get("data", {}).get("children", []):
        if child.get("kind") != "t3":
            continue
        d = child["data"]
        if d.get("stickied"):
            continue
        if d.get("removed_by_category"):
            continue
        flair = (d.get("link_flair_text") or "").lower()
        if flair in EXCLUDED_FLAIRS:
            continue

        score = d.get("score", 0)
        num_comments = d.get("num_comments", 0)
        weak = is_weak_signal(score, num_comments)
        ratio = round(num_comments / max(score, 1), 2)
        kw = matches_keywords(f"{d.get('title', '')} {d.get('selftext', '')}")

        posts.append(RedditPost(
            id=d["id"],
            title=d.get("title", ""),
            subreddit=subreddit,
            score=score,
            num_comments=num_comments,
            url=d.get("url", ""),
            permalink=d.get("permalink", ""),
            selftext=(d.get("selftext") or "")[:500],
            created_utc=d.get("created_utc", 0),
            matched_keywords=kw,
            is_weak_signal=weak,
            comment_score_ratio=ratio,
        ))
    return posts


def is_weak_signal(score: int, num_comments: int) -> bool:
    if score > config.WEAK_SIGNAL_MAX_SCORE:
        return False
    if num_comments < config.WEAK_SIGNAL_MIN_COMMENTS:
        return False
    return (num_comments / max(score, 1)) >= config.WEAK_SIGNAL_COMMENT_RATIO


def matches_keywords(text: str) -> list[str]:
    text_lower = text.lower()
    return [kw for kw in config.TRACKED_KEYWORDS if kw.lower() in text_lower]


def fetch_comments(permalink: str, limit: int = 3) -> list[str]:
    try:
        url = f"https://www.reddit.com{permalink}.json?limit={limit}&sort=top"
        data = _fetch_json(url)
        comments = []
        if len(data) > 1:
            for child in data[1].get("data", {}).get("children", [])[:limit]:
                if child.get("kind") == "t1":
                    body = child["data"].get("body", "")
                    if body and len(body) > 10:
                        comments.append(body[:300])
        time.sleep(config.RATE_LIMIT_SECONDS)
        return comments
    except Exception:
        return []


def filter_posts(posts: list[RedditPost], seen_ids: set[str]) -> list[RedditPost]:
    unique = {}
    for p in posts:
        if p.id in seen_ids or p.id in unique:
            continue
        if p.score < config.MIN_SCORE and not p.is_weak_signal:
            continue
        unique[p.id] = p
    return sorted(unique.values(), key=lambda p: p.score, reverse=True)


def collect_all(subreddits: list[str] | None = None, time_filter: str = "day") -> list[RedditPost]:
    subreddits = subreddits or config.DEFAULT_SUBREDDITS
    all_posts = []
    for sub in subreddits:
        try:
            url = build_url(sub, limit=config.POSTS_PER_SUB, time_filter=time_filter)
            data = _fetch_json(url)
            posts = parse_listing(data, sub)
            all_posts.extend(posts)
            print(f"  r/{sub}: {len(posts)} posts")
            time.sleep(config.RATE_LIMIT_SECONDS)
        except Exception as e:
            print(f"  [!] r/{sub}: erreur — {e}")
    return all_posts
