#!/usr/bin/env python3
"""reddit-scout v2 — orchestrateur principal."""

import argparse
import json
import sys
import uuid
from collections import defaultdict
from dataclasses import asdict

from src import config
from src import collector
from src import scorer
from src import perplexity_client as pplx
from src import sentiment
from src import database as db
from src import alerts
from src import report_generator


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="reddit-scout v2")
    parser.add_argument("--no-email", action="store_true")
    parser.add_argument("--no-web", action="store_true")
    parser.add_argument("--deep-dive", type=int, default=3)
    parser.add_argument("--trends", type=int, default=5)
    return parser.parse_args()


def run(args: argparse.Namespace) -> None:
    run_id = str(uuid.uuid4())[:8]
    print(f"=== reddit-scout v2 — run {run_id} ===\n")

    db.init_db()
    db.save_run(run_id)
    pplx.reset_call_count()
    seen_ids = db.get_seen_ids()

    # ETAPE 1 : Collecte Reddit
    print("[1/9] Collecte Reddit...")
    raw_posts = collector.collect_all()
    print(f"  Total brut: {len(raw_posts)} posts\n")

    if not raw_posts:
        print("[!] Aucun post collecte. Fin.")
        sys.exit(1)

    # ETAPE 2 : Pre-filtrage + dedup
    print("[2/9] Filtrage + dedup...")
    filtered = collector.filter_posts(raw_posts, seen_ids)
    print(f"  Apres filtrage: {len(filtered)} posts\n")

    # ETAPE 3 : Enrichissement commentaires
    print("[3/9] Enrichissement commentaires...")
    for p in filtered[:30]:
        p.top_comments = collector.fetch_comments(p.permalink)
    posts_dicts = [asdict(p) for p in filtered]

    # ETAPE 4 : Scoring Claude
    print("[4/9] Scoring Claude sonnet...")
    claude_client = scorer.build_client()
    scored = scorer.score_posts(claude_client, posts_dicts)
    top_posts = [p for p in scored if p["ai_category"] == "TOP"]
    interesting = [p for p in scored if p["ai_category"] == "INTERESSANT"]
    print(f"  TOP: {len(top_posts)} | INTERESSANT: {len(interesting)}\n")

    db.save_posts(posts_dicts, run_id)

    posts_json = json.dumps(
        [{"title": p["title"], "subreddit": p["subreddit"], "score": p["score"],
          "num_comments": p["num_comments"], "selftext": p.get("selftext", "")[:200]}
         for p in scored],
        indent=2, ensure_ascii=False,
    )

    weak_signals = [p for p in posts_dicts if p.get("is_weak_signal")]

    # ETAPE 5 : Analyses Perplexity
    pplx_client = pplx.build_client()

    print("[5/9] Analyses Perplexity...")
    print("  - Tendances...")
    raw_trends = pplx.identify_trends(pplx_client, posts_json, n=args.trends)
    trends_list = _parse_trends_json(raw_trends)  # Parse for DB
    db.save_trends(trends_list, run_id)
    trends_raw = _clean_perplexity_output(raw_trends)  # Clean for report

    print("  - Correlations...")
    correlations = _clean_perplexity_output(pplx.find_correlations(pplx_client, posts_json))

    weak_analysis = ""
    if weak_signals:
        print(f"  - Signaux faibles ({len(weak_signals)})...")
        weak_json = json.dumps(
            [{"title": p["title"], "subreddit": p["subreddit"],
              "score": p["score"], "num_comments": p["num_comments"],
              "comment_score_ratio": p.get("comment_score_ratio", 0)}
             for p in weak_signals[:10]],
            indent=2, ensure_ascii=False,
        )
        weak_analysis = _clean_perplexity_output(pplx.analyze_weak_signals(pplx_client, weak_json))

    print("  - Sentiment...")
    sentiment_results, sentiment_shifts = _analyze_sentiments(
        pplx_client, posts_dicts, run_id
    )
    sentiment_table = sentiment.format_sentiment_table(sentiment_results)
    shifts_text = sentiment.format_sentiment_shifts(sentiment_shifts)

    web_enrichment = ""
    if not args.no_web and trends_list:
        print("  - Enrichissement web...")
        web_parts = []
        for t in trends_list[:3]:
            enriched = _clean_perplexity_output(pplx.enrich_trend_with_web(
                pplx_client,
                topic=t.get("topic", ""),
                summary=t.get("summary", ""),
                evidence=json.dumps(t.get("evidence", []), ensure_ascii=False),
            ))
            web_parts.append(f"### {t.get('topic', 'Tendance')}\n\n{enriched}")
        web_enrichment = "\n\n---\n\n".join(web_parts)

    print("  - Previsions...")
    forecasts = _clean_perplexity_output(pplx.forecast_trends(pplx_client, trends_raw))

    print(f"  - Deep-dive (top {args.deep_dive})...")
    deep_parts = []
    for p in top_posts[:args.deep_dive]:
        analysis = _clean_perplexity_output(pplx.deep_dive(pplx_client, p))
        deep_parts.append(f"### {p['title']}\n\n{analysis}")
    deep_dives = "\n\n---\n\n".join(deep_parts)
    print()

    # ETAPE 6 : Comparaison historique
    print("[6/9] Comparaison historique...")
    history_comparison = ""
    history = db.get_history_comparison()
    if history:
        prev_trends = db.get_previous_trends()
        history_comparison = _clean_perplexity_output(pplx.compare_with_history(
            pplx_client,
            current_trends=trends_raw,
            previous_trends=json.dumps(prev_trends, ensure_ascii=False),
            previous_date=history.get("previous_run", "N/A"),
            new_trends=", ".join(history.get("new_trends", [])) or "Aucune",
            disappeared_trends=", ".join(history.get("disappeared", [])) or "Aucune",
            persistent_trends=", ".join(history.get("persistent", [])) or "Aucune",
        ))

    # ETAPE 7 : Resume executif
    print("[7/9] Resume executif...")
    full_analysis = (
        f"## Tendances\n{trends_raw}\n\n"
        f"## Correlations\n{correlations}\n\n"
        f"## Previsions\n{forecasts}\n\n"
        f"## Sentiment\n{sentiment_table}\n\n"
        f"## Signaux Faibles\n{weak_analysis}\n\n"
        f"## Analyses Approfondies\n{deep_dives}"
    )
    executive_summary = _clean_perplexity_output(pplx.executive_summary(pplx_client, full_analysis))

    # ETAPE 8 : Rapport
    print("[8/9] Generation rapport...")
    md_path, pdf_path = report_generator.generate_report(
        run_id=run_id,
        top_posts=top_posts,
        interesting_posts=interesting,
        trends=trends_raw,
        correlations=correlations,
        forecasts=forecasts,
        executive_summary=executive_summary,
        weak_signals=weak_analysis,
        sentiment_table=sentiment_table,
        sentiment_shifts=shifts_text,
        web_enrichment=web_enrichment,
        deep_dives=deep_dives,
        history_comparison=history_comparison,
        posts_scanned=len(raw_posts),
        posts_retained=len(scored),
        perplexity_calls=pplx.get_call_count(),
    )

    db.complete_run(
        run_id, posts_scanned=len(raw_posts), posts_retained=len(scored),
        trends_count=len(trends_list), perplexity_calls=pplx.get_call_count(),
        report_path=md_path,
    )

    # ETAPE 9 : Email
    if not args.no_email:
        print("[9/9] Envoi email...")

        # Identify actions relevant to BP
        bp_keywords = ["axios", "npm", "node", "go ", "golang", "docker", "shopify", "odoo",
                       "sage", "x3", "pimcore", "sophos", "vmware", "esxi", "vsphere",
                       "claude", "anthropic", "mcp", "cve", "zero-day", "supply chain",
                       "exchange", "office 365", "microsoft 365"]

        actions = []
        all_text = f"{trends_raw} {correlations} {weak_analysis} {forecasts}".lower()
        for kw in bp_keywords:
            if kw in all_text:
                # Find the context around the keyword
                idx = all_text.find(kw)
                start = max(0, idx - 80)
                end = min(len(all_text), idx + 80)
                snippet = all_text[start:end].replace("\n", " ").strip()
                actions.append(f"<b>{kw.upper()}</b> mentionné : ...{snippet}...")

        actions_html = ""
        if actions:
            actions_items = "".join(f"<li>{a}</li>" for a in actions[:10])
            actions_html = f"""
            <div style="background:#fff0f0;border-left:4px solid #e00;padding:12px;margin:15px 0">
                <h3 style="color:#c00;margin:0 0 8px">&#9888; Actions à prévoir pour BLACK PEARL</h3>
                <ul style="color:#900;margin:0">{actions_items}</ul>
            </div>
            """

        summary_html = f"""
        <html><body style="font-family:Arial,sans-serif;max-width:700px;margin:0 auto">
        <h2 style="color:#16213e">reddit-scout — Rapport de veille</h2>
        <p><strong>Run {run_id}</strong> — {len(top_posts)} TOP, {len(interesting)} INTERESSANT sur {len(raw_posts)} posts scannés</p>
        {actions_html}
        <h3>Résumé exécutif</h3>
        <div>{executive_summary.replace(chr(10), '<br>')}</div>
        <hr>
        <p style="color:#999;font-size:11px">Rapport PDF en pièce jointe. Appels Perplexity : {pplx.get_call_count()}/{config.MAX_API_CALLS_PER_RUN} |
        <a href="https://github.com/svalgresy/reddit-scout">GitHub</a></p>
        </body></html>
        """
        alerts.send_report(summary_html, pdf_path)
        alerts.alert_explosive_posts(posts_dicts)
        alerts.alert_sentiment_shifts(sentiment_shifts)
        if history:
            alerts.alert_new_trends(history.get("new_trends", []))

    db.purge_old_posts()

    print(f"\n=== Termine ===")
    print(f"  Rapport MD : {md_path}")
    print(f"  Rapport PDF: {pdf_path or 'non disponible'}")
    print(f"  Perplexity  : {pplx.get_call_count()}/{config.MAX_API_CALLS_PER_RUN} appels")
    print(f"  Run ID      : {run_id}")


def _clean_perplexity_output(raw: str) -> str:
    """Convert raw JSON from Perplexity into readable Markdown."""
    import json as _json
    text = raw.strip()

    # Try to detect and parse JSON
    json_text = text
    if "```json" in text:
        json_text = text.split("```json")[1].split("```")[0]
    elif "```" in text:
        json_text = text.split("```")[1].split("```")[0]
    elif not text.startswith(("[", "{")):
        return text  # Already Markdown, return as-is

    try:
        data = _json.loads(json_text)
    except (_json.JSONDecodeError, IndexError):
        return text  # Not JSON, return as-is

    # Convert JSON to Markdown
    if isinstance(data, list):
        parts = []
        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                title = item.get("topic") or item.get("title") or item.get("theme") or f"Element {i}"
                lines = [f"### {i}. {title}"]
                for k, v in item.items():
                    if k in ("topic", "title", "theme"):
                        continue
                    if isinstance(v, list):
                        lines.append(f"- **{k.replace('_', ' ').title()}** :")
                        for elem in v:
                            lines.append(f"  - {elem}")
                    else:
                        lines.append(f"- **{k.replace('_', ' ').title()}** : {v}")
                parts.append("\n".join(lines))
            else:
                parts.append(f"- {item}")
        return "\n\n".join(parts)
    elif isinstance(data, dict):
        lines = []
        for k, v in data.items():
            if isinstance(v, list):
                lines.append(f"**{k.replace('_', ' ').title()}** :")
                for elem in v:
                    lines.append(f"- {elem}")
            else:
                lines.append(f"**{k.replace('_', ' ').title()}** : {v}")
        return "\n".join(lines)

    return text


def _parse_trends_json(raw: str) -> list[dict]:
    try:
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return json.loads(text)
    except (json.JSONDecodeError, IndexError):
        return []


def _analyze_sentiments(
    client, posts_dicts: list[dict], run_id: str,
) -> tuple[list[sentiment.SentimentResult], list[dict]]:
    by_sub = defaultdict(list)
    for p in posts_dicts:
        by_sub[p["subreddit"]].append(p)

    results = []
    shifts = []
    top_subs = sorted(by_sub.items(), key=lambda x: len(x[1]), reverse=True)[:8]

    for sub_name, sub_posts in top_subs:
        posts_data = json.dumps(
            [{"title": p["title"], "score": p["score"],
              "top_comments": p.get("top_comments", [])[:3]}
             for p in sub_posts[:5]],
            indent=2, ensure_ascii=False,
        )
        raw = pplx.analyze_sentiment(client, sub_name, posts_data)
        result = sentiment.parse_sentiment_response(raw)
        if result:
            result.subreddit = sub_name
            results.append(result)
            shift = sentiment.save_and_check_shift(result, run_id)
            if shift:
                shifts.append(shift)

    return results, shifts


def main():
    args = parse_args()
    run(args)


if __name__ == "__main__":
    main()
