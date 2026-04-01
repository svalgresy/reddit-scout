"""Scoring IA via Claude sonnet — 5 criteres ponderes BLACK PEARL."""

import json
import anthropic

from src import config

SCORING_PROMPT = """\
Tu es un analyste de veille technologique pour BLACK PEARL RTD (La Reunion).
Contexte : sysadmin, integrateur, e-commerce (Shopify/Odoo), SAGE X3, Pimcore PIM, \
infra VMware/Sophos, dev Go, crypto/DeFi, securite reseau.

Evalue ce post Reddit selon 5 criteres ponderes :
1. **Pertinence BLACK PEARL** (30%) — alignement avec nos domaines metier
2. **Actionnable** (25%) — contient un outil, tuto, repo, solution concrete
3. **Engagement Reddit** (15%) — score et commentaires significatifs
4. **Nouveaute** (15%) — information nouvelle, pas du recycle
5. **Urgence/Impact** (15%) — CVE, incident, changement majeur

Post :
- Titre : {title}
- Subreddit : r/{subreddit}
- Score : {score} | Commentaires : {num_comments}
- Texte : {selftext}
- Top commentaires : {comments}

Reponds UNIQUEMENT en JSON :
{{"score": <0-100>, "justification": "<1 phrase>"}}
"""


def build_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)


def score_post(client: anthropic.Anthropic, post: dict) -> tuple[int, str]:
    comments_text = "\n".join(
        f"- {c[:200]}" for c in post.get("top_comments", [])[:3]
    ) or "Aucun"

    prompt = SCORING_PROMPT.format(
        title=post["title"],
        subreddit=post["subreddit"],
        score=post["score"],
        num_comments=post["num_comments"],
        selftext=post.get("selftext", "")[:300],
        comments=comments_text,
    )

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        return parse_score_response(response.content[0].text)
    except Exception as e:
        print(f"  [!] Scoring error: {e}")
        return 0, ""


def parse_score_response(raw: str) -> tuple[int, str]:
    try:
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        data = json.loads(text)
        return int(data.get("score", 0)), data.get("justification", "")
    except (json.JSONDecodeError, ValueError, IndexError):
        return 0, ""


def categorize(score: int) -> str:
    if score >= config.SCORE_TOP:
        return "TOP"
    elif score >= config.SCORE_INTERESTING:
        return "INTERESSANT"
    return "IGNORE"


def score_posts(client: anthropic.Anthropic, posts: list[dict]) -> list[dict]:
    scored = []
    for p in posts:
        ai_score, justification = score_post(client, p)
        p["ai_score"] = ai_score
        p["ai_category"] = categorize(ai_score)
        p["ai_justification"] = justification
        category = p["ai_category"]
        if category != "IGNORE":
            print(f"  [{category}] {ai_score}/100 — {p['title'][:60]}")
        scored.append(p)

    scored.sort(key=lambda p: p["ai_score"], reverse=True)
    retained = [p for p in scored if p["ai_category"] != "IGNORE"]
    return retained[:config.MAX_RETAINED_POSTS]
