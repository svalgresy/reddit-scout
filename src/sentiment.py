"""Advanced sentiment analysis with per-subreddit scoring and evolution tracking."""

import json
from dataclasses import dataclass

from src import database as db


@dataclass
class SentimentResult:
    subreddit: str
    score: float          # -1.0 to +1.0
    label: str
    dominant_emotions: list[str]
    key_drivers: list[str]
    sample_size: int


def parse_sentiment_response(raw_json: str) -> SentimentResult | None:
    """Parse Perplexity's sentiment analysis JSON response."""
    try:
        text = raw_json.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        data = json.loads(text)
        return SentimentResult(
            subreddit=data.get("subreddit", "unknown"),
            score=float(data.get("score", 0)),
            label=data.get("label", "Neutre"),
            dominant_emotions=data.get("dominant_emotions", []),
            key_drivers=data.get("key_drivers", []),
            sample_size=int(data.get("sample_size", 0)),
        )
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        print(f"[!] Erreur parsing sentiment: {e}")
        return None


def save_and_check_shift(result: SentimentResult, run_id: str) -> dict | None:
    """Save sentiment to DB and check for significant shifts.

    Returns a dict with shift info if a major sentiment reversal is detected.
    """
    db.save_sentiment(
        run_id=run_id,
        subreddit=result.subreddit,
        score=result.score,
        label=result.label,
        dominant_emotions=", ".join(result.dominant_emotions),
        sample_size=result.sample_size,
    )

    history = db.get_sentiment_evolution(result.subreddit, limit=6)
    if len(history) < 2:
        return None

    previous_score = history[1]["score"]
    shift = result.score - previous_score

    from src.config import ALERT_SENTIMENT_SHIFT
    if abs(shift) >= ALERT_SENTIMENT_SHIFT:
        direction = "positif" if shift > 0 else "négatif"
        return {
            "subreddit": result.subreddit,
            "previous_score": previous_score,
            "current_score": result.score,
            "shift": round(shift, 2),
            "direction": direction,
            "previous_label": history[1]["label"],
            "current_label": result.label,
        }
    return None


def format_sentiment_table(results: list[SentimentResult]) -> str:
    """Format sentiment results as a Markdown table for the report."""
    lines = [
        "| Subreddit | Score | Label | Émotions dominantes |",
        "|-----------|-------|-------|---------------------|",
    ]
    for r in sorted(results, key=lambda x: x.score, reverse=True):
        bar = _score_bar(r.score)
        emotions = ", ".join(r.dominant_emotions[:3]) if r.dominant_emotions else "—"
        lines.append(f"| r/{r.subreddit} | {bar} {r.score:+.2f} | {r.label} | {emotions} |")
    return "\n".join(lines)


def format_sentiment_shifts(shifts: list[dict]) -> str:
    """Format detected sentiment shifts for alerts."""
    if not shifts:
        return ""
    lines = ["**⚠️ Retournements de sentiment détectés :**\n"]
    for s in shifts:
        lines.append(
            f"- **r/{s['subreddit']}** : {s['previous_label']} ({s['previous_score']:+.2f}) "
            f"→ {s['current_label']} ({s['current_score']:+.2f}) "
            f"| Variation : {s['shift']:+.2f} ({s['direction']})"
        )
    return "\n".join(lines)


def _score_bar(score: float) -> str:
    """Visual bar for sentiment score."""
    if score >= 0.5:
        return "🟢"
    elif score >= 0.1:
        return "🟡"
    elif score >= -0.1:
        return "⚪"
    elif score >= -0.5:
        return "🟠"
    else:
        return "🔴"
