"""Perplexity AI client — analyse de tendances, sentiment, recherche web."""

import json
from openai import OpenAI

from src import config
from src import prompts


def build_client() -> OpenAI:
    return OpenAI(
        api_key=config.PERPLEXITY_API_KEY,
        base_url=config.PERPLEXITY_BASE_URL,
    )


_call_count = 0


def _chat(client: OpenAI, user_prompt: str, temperature: float = 0.3) -> str:
    """Send a chat completion request to Perplexity with budget tracking."""
    global _call_count
    if _call_count >= config.MAX_API_CALLS_PER_RUN:
        return '{"error": "Budget API atteint pour cette exécution."}'
    _call_count += 1

    response = client.chat.completions.create(
        model=config.PERPLEXITY_MODEL,
        messages=[
            {"role": "system", "content": prompts.SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
    )
    return response.choices[0].message.content


def reset_call_count():
    global _call_count
    _call_count = 0


def get_call_count() -> int:
    return _call_count


# ── Trend Identification ──────────────────────────────────────────────

def identify_trends(client: OpenAI, posts_json: str, n: int = 5) -> str:
    prompt = prompts.TREND_IDENTIFICATION_PROMPT.format(posts_json=posts_json, n=n)
    return _chat(client, prompt)


# ── Deep Dive ─────────────────────────────────────────────────────────

def deep_dive(client: OpenAI, post: dict) -> str:
    comments_text = "\n".join(
        f"- {c}" for c in post.get("top_comments", [])
    ) or "Aucun commentaire disponible."
    prompt = prompts.DEEP_DIVE_PROMPT.format(
        title=post["title"],
        subreddit=post["subreddit"],
        score=post["score"],
        num_comments=post["num_comments"],
        selftext=post.get("selftext", "N/A"),
        comments=comments_text,
    )
    return _chat(client, prompt, temperature=0.4)


# ── Forecasts ─────────────────────────────────────────────────────────

def forecast_trends(client: OpenAI, trends_summary: str) -> str:
    prompt = prompts.FORECAST_PROMPT.format(trends_summary=trends_summary)
    return _chat(client, prompt, temperature=0.5)


# ── Executive Summary ─────────────────────────────────────────────────

def executive_summary(client: OpenAI, full_analysis: str) -> str:
    prompt = prompts.EXECUTIVE_SUMMARY_PROMPT.format(full_analysis=full_analysis)
    return _chat(client, prompt, temperature=0.2)


# ── Correlations ──────────────────────────────────────────────────────

def find_correlations(client: OpenAI, posts_json: str) -> str:
    prompt = prompts.CORRELATION_PROMPT.format(posts_json=posts_json)
    return _chat(client, prompt)


# ── Sentiment Analysis ────────────────────────────────────────────────

def analyze_sentiment(client: OpenAI, subreddit: str, posts_data: str) -> str:
    prompt = prompts.SENTIMENT_ANALYSIS_PROMPT.format(
        subreddit=subreddit,
        posts_data=posts_data,
    )
    return _chat(client, prompt, temperature=0.2)


# ── Weak Signals ──────────────────────────────────────────────────────

def analyze_weak_signals(client: OpenAI, weak_signals_json: str) -> str:
    prompt = prompts.WEAK_SIGNALS_PROMPT.format(weak_signals_json=weak_signals_json)
    return _chat(client, prompt, temperature=0.4)


# ── Web Enrichment ────────────────────────────────────────────────────

def enrich_trend_with_web(client: OpenAI, topic: str, summary: str, evidence: str) -> str:
    prompt = prompts.WEB_ENRICHMENT_PROMPT.format(
        topic=topic,
        summary=summary,
        evidence=evidence,
    )
    return _chat(client, prompt, temperature=0.3)


# ── History Comparison ────────────────────────────────────────────────

def compare_with_history(
    client: OpenAI,
    current_trends: str,
    previous_trends: str,
    previous_date: str,
    new_trends: str,
    disappeared_trends: str,
    persistent_trends: str,
) -> str:
    prompt = prompts.HISTORY_COMPARISON_PROMPT.format(
        current_trends=current_trends,
        previous_trends=previous_trends,
        previous_date=previous_date,
        new_trends=new_trends,
        disappeared_trends=disappeared_trends,
        persistent_trends=persistent_trends,
    )
    return _chat(client, prompt, temperature=0.3)
