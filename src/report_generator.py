"""Generation du rapport Markdown + PDF."""

import os
from datetime import datetime, timezone

from jinja2 import Environment, FileSystemLoader

from src import config


def generate_report(
    run_id: str,
    top_posts: list[dict],
    interesting_posts: list[dict],
    trends: str = "",
    correlations: str = "",
    forecasts: str = "",
    executive_summary: str = "",
    weak_signals: str = "",
    sentiment_table: str = "",
    sentiment_shifts: str = "",
    web_enrichment: str = "",
    deep_dives: str = "",
    history_comparison: str = "",
    posts_scanned: int = 0,
    posts_retained: int = 0,
    perplexity_calls: int = 0,
) -> tuple[str, str | None]:
    os.makedirs(config.REPORTS_DIR, exist_ok=True)

    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d %H:%M UTC")
    base_name = f"scout_{now.strftime('%Y%m%d_%H%M')}"

    env = Environment(loader=FileSystemLoader("templates"))
    template = env.get_template("report.md.j2")

    content = template.render(
        date=date_str,
        run_id=run_id,
        top_posts=top_posts,
        interesting_posts=interesting_posts,
        trends=trends or "Aucune tendance identifiee.",
        correlations=correlations or "Aucune correlation detectee.",
        forecasts=forecasts or "Previsions non disponibles.",
        executive_summary=executive_summary or "Resume non disponible.",
        weak_signals=weak_signals or "Aucun signal faible detecte.",
        sentiment_table=sentiment_table or "Analyse de sentiment non disponible.",
        sentiment_shifts=sentiment_shifts or "",
        web_enrichment=web_enrichment or "Enrichissement web non disponible.",
        deep_dives=deep_dives or "Aucune analyse approfondie.",
        history_comparison=history_comparison,
        posts_scanned=posts_scanned,
        posts_retained=posts_retained,
        perplexity_calls=perplexity_calls,
        max_api_calls=config.MAX_API_CALLS_PER_RUN,
    )

    md_path = os.path.join(config.REPORTS_DIR, f"{base_name}.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)

    pdf_path = _convert_to_pdf(md_path, base_name)
    return md_path, pdf_path


def _convert_to_pdf(md_path: str, base_name: str) -> str | None:
    """Convert Markdown to styled PDF using weasyprint."""
    pdf_path = os.path.join(config.REPORTS_DIR, f"{base_name}.pdf")
    try:
        import markdown
        from weasyprint import HTML

        with open(md_path, "r", encoding="utf-8") as f:
            md_content = f.read()

        html_body = markdown.markdown(md_content, extensions=["tables", "fenced_code"])

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  @page {{ size: A4; margin: 2cm;
    @bottom-center {{ content: "reddit-scout v2 — BLACK PEARL RTD — Page " counter(page) " / " counter(pages); font-size: 8pt; color: #999; }}
  }}
  body {{ font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif; font-size: 11pt; line-height: 1.6; color: #1a1a1a; }}
  h1 {{ color: #1a1a2e; border-bottom: 3px solid #e94560; padding-bottom: 8px; font-size: 22pt; }}
  h2 {{ color: #16213e; border-bottom: 1px solid #ddd; padding-bottom: 5px; margin-top: 25px; font-size: 16pt; }}
  h3 {{ color: #0f3460; font-size: 13pt; }}
  table {{ width: 100%; border-collapse: collapse; margin: 15px 0; font-size: 10pt; }}
  th {{ background-color: #16213e; color: white; padding: 10px 8px; text-align: left; }}
  td {{ padding: 8px; border-bottom: 1px solid #eee; }}
  tr:nth-child(even) {{ background-color: #f8f9fa; }}
  blockquote {{ border-left: 4px solid #e94560; margin: 10px 0; padding: 8px 15px; background: #fef9f9; color: #555; font-style: italic; }}
  code {{ background: #f1f3f5; padding: 2px 6px; border-radius: 3px; font-size: 10pt; }}
  hr {{ border: none; border-top: 1px solid #ddd; margin: 20px 0; }}
  a {{ color: #e94560; text-decoration: none; }}
  strong {{ color: #16213e; }}
</style></head>
<body>{html_body}</body></html>"""

        HTML(string=html).write_pdf(pdf_path)
        print(f"[OK] PDF genere (weasyprint): {pdf_path}")
        return pdf_path
    except Exception as e:
        print(f"[!] PDF non genere: {e}")
        return None
