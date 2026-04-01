"""Tests scorer.py."""
from src.scorer import parse_score_response, categorize, SCORING_PROMPT


def test_parse_score_response_valid():
    raw = '{"score": 85, "justification": "Tres pertinent pour BP"}'
    score, justification = parse_score_response(raw)
    assert score == 85
    assert "pertinent" in justification.lower()


def test_parse_score_response_json_in_markdown():
    raw = '```json\n{"score": 72, "justification": "Bon article"}\n```'
    score, justification = parse_score_response(raw)
    assert score == 72


def test_parse_score_response_invalid():
    score, justification = parse_score_response("pas du json")
    assert score == 0
    assert justification == ""


def test_categorize():
    assert categorize(90) == "TOP"
    assert categorize(80) == "TOP"
    assert categorize(70) == "INTERESSANT"
    assert categorize(65) == "INTERESSANT"
    assert categorize(50) == "IGNORE"


def test_scoring_prompt_contains_criteria():
    assert "Pertinence BLACK PEARL" in SCORING_PROMPT
    assert "Actionnable" in SCORING_PROMPT
    assert "30%" in SCORING_PROMPT
