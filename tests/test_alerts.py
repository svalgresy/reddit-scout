"""Tests alerts.py — Graph API email."""
from src.alerts import build_alert_html


def test_build_alert_html():
    html = build_alert_html("Test alert", [
        {"label": "r/sysadmin", "detail": "Test post"},
    ])
    assert "Test alert" in html
    assert "r/sysadmin" in html
    assert "<html>" in html


def test_build_alert_html_empty():
    html = build_alert_html("Empty", [])
    assert "Empty" in html
