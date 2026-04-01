"""Tests alerts.py."""
from src.alerts import build_report_email, build_alert_html


def test_build_alert_html():
    html = build_alert_html("Test alert", [
        {"label": "r/sysadmin", "detail": "Test post"},
    ])
    assert "Test alert" in html
    assert "r/sysadmin" in html
    assert "<html>" in html


def test_build_report_email_without_pdf():
    msg = build_report_email(
        subject="Scout Report",
        summary_html="<p>Rapport du jour</p>",
        pdf_path=None,
    )
    assert msg["Subject"] == "Scout Report"
    assert len(msg.get_payload()) >= 1
