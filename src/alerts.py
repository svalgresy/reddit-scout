"""Alertes email O365 SMTP avec support PDF en piece jointe."""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

from src import config


def send_email(subject: str, body_html: str, pdf_path: str | None = None) -> bool:
    if not all([config.SMTP_USER, config.SMTP_PASSWORD, config.ALERT_EMAIL_TO]):
        print("[!] Email non configure — alerte ignoree.")
        return False

    msg = build_report_email(subject, body_html, pdf_path)

    try:
        with smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.SMTP_USER, config.SMTP_PASSWORD)
            server.sendmail(config.SMTP_USER, config.ALERT_EMAIL_TO.split(","), msg.as_string())
        print(f"[OK] Email envoye a {config.ALERT_EMAIL_TO}")
        return True
    except Exception as e:
        print(f"[!] Erreur envoi email: {e}")
        return False


def build_report_email(subject: str, summary_html: str, pdf_path: str | None = None) -> MIMEMultipart:
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"] = config.SMTP_USER or ""
    msg["To"] = config.ALERT_EMAIL_TO

    msg.attach(MIMEText(summary_html, "html", "utf-8"))

    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_part = MIMEApplication(f.read(), _subtype="pdf")
            pdf_part.add_header(
                "Content-Disposition", "attachment",
                filename=os.path.basename(pdf_path),
            )
            msg.attach(pdf_part)

    return msg


def build_alert_html(title: str, items: list[dict]) -> str:
    rows = ""
    for item in items:
        rows += f"""
        <tr>
            <td style="padding:8px;border-bottom:1px solid #eee"><strong>{item.get('label', '')}</strong></td>
            <td style="padding:8px;border-bottom:1px solid #eee">{item.get('detail', '')}</td>
        </tr>"""

    return f"""
    <html>
    <body style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto">
        <h2 style="color:#e74c3c">{title}</h2>
        <table style="width:100%;border-collapse:collapse">{rows}</table>
        <p style="color:#999;font-size:12px;margin-top:20px">reddit-scout v2 — BLACK PEARL RTD</p>
    </body>
    </html>
    """


def send_report(summary_html: str, pdf_path: str | None = None) -> bool:
    return send_email(
        subject="reddit-scout — Rapport de veille",
        body_html=summary_html,
        pdf_path=pdf_path,
    )


def alert_explosive_posts(posts: list[dict]):
    explosive = [p for p in posts if p.get("score", 0) >= config.ALERT_SCORE_THRESHOLD]
    if not explosive:
        return
    items = [{"label": f"r/{p['subreddit']} — {p['score']}+",
              "detail": p["title"][:100]} for p in explosive[:5]]
    send_email(
        f"ALERTE: {len(explosive)} post(s) explosif(s)",
        build_alert_html(f"{len(explosive)} post(s) explosif(s)", items),
    )


def alert_sentiment_shifts(shifts: list[dict]):
    if not shifts:
        return
    items = [{"label": f"r/{s['subreddit']}",
              "detail": f"{s['previous_label']} -> {s['current_label']} (delta {s['shift']:+.2f})"}
             for s in shifts]
    send_email(
        f"ALERTE: {len(shifts)} retournement(s) de sentiment",
        build_alert_html(f"{len(shifts)} retournement(s) de sentiment", items),
    )


def alert_new_trends(trends: list[str]):
    if not trends:
        return
    items = [{"label": "Nouvelle tendance", "detail": t} for t in trends[:5]]
    send_email(
        f"ALERTE: {len(trends)} nouvelle(s) tendance(s)",
        build_alert_html(f"{len(trends)} nouvelle(s) tendance(s)", items),
    )
