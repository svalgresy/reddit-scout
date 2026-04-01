"""Alertes email via Microsoft Graph API — bot@blackpearl.re"""

import json
import os
import base64
import urllib.request
import urllib.parse

from src import config

_access_token: str | None = None
_token_expires: float = 0


def _get_graph_token() -> str | None:
    """Get OAuth2 token for Microsoft Graph API using client_credentials."""
    import time
    global _access_token, _token_expires

    if _access_token and time.time() < _token_expires:
        return _access_token

    if not all([config.GRAPH_TENANT_ID, config.GRAPH_CLIENT_ID, config.GRAPH_CLIENT_SECRET]):
        print("[!] Graph API non configure — email ignore.")
        return None

    token_url = f"https://login.microsoftonline.com/{config.GRAPH_TENANT_ID}/oauth2/v2.0/token"
    data = urllib.parse.urlencode({
        "client_id": config.GRAPH_CLIENT_ID,
        "client_secret": config.GRAPH_CLIENT_SECRET,
        "scope": "https://graph.microsoft.com/.default",
        "grant_type": "client_credentials",
    }).encode()

    req = urllib.request.Request(token_url, data=data, headers={
        "Content-Type": "application/x-www-form-urlencoded",
    })

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
            _access_token = result["access_token"]
            _token_expires = time.time() + result.get("expires_in", 3600) - 60
            return _access_token
    except Exception as e:
        print(f"[!] Graph token error: {e}")
        return None


def send_email(subject: str, body_html: str, pdf_path: str | None = None) -> bool:
    """Send email via Microsoft Graph API with optional PDF attachment."""
    if not config.ALERT_EMAIL_TO:
        print("[!] ALERT_EMAIL_TO non configure.")
        return False

    token = _get_graph_token()
    if not token:
        return False

    # Build message
    message = {
        "message": {
            "subject": subject,
            "body": {
                "contentType": "HTML",
                "content": body_html,
            },
            "toRecipients": [
                {"emailAddress": {"address": addr.strip()}}
                for addr in config.ALERT_EMAIL_TO.split(",")
            ],
        },
        "saveToSentItems": "false",
    }

    # Add PDF attachment if exists
    if pdf_path and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as f:
            pdf_bytes = f.read()
        message["message"]["attachments"] = [{
            "@odata.type": "#microsoft.graph.fileAttachment",
            "name": os.path.basename(pdf_path),
            "contentType": "application/pdf",
            "contentBytes": base64.b64encode(pdf_bytes).decode(),
        }]

    # Send via Graph API
    url = f"https://graph.microsoft.com/v1.0/users/{config.GRAPH_SENDER}/sendMail"
    payload = json.dumps(message).encode()

    req = urllib.request.Request(url, data=payload, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            print(f"[OK] Email envoye via Graph API a {config.ALERT_EMAIL_TO}")
            return True
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"[!] Graph API error {e.code}: {error_body[:200]}")
        return False
    except Exception as e:
        print(f"[!] Email error: {e}")
        return False


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
