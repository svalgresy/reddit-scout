"""Generation du rapport Markdown + PDF."""

import os
import subprocess
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
    pdf_path = os.path.join(config.REPORTS_DIR, f"{base_name}.pdf")
    try:
        subprocess.run(
            ["pandoc", md_path, "-o", pdf_path, "--pdf-engine=xelatex",
             "-V", "geometry:margin=2cm", "-V", "mainfont:DejaVu Sans",
             "-V", "fontsize=11pt"],
            check=True, capture_output=True, timeout=120,
        )
        print(f"[OK] PDF genere: {pdf_path}")
        return pdf_path
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"[!] PDF non genere: {e}")
        return None
