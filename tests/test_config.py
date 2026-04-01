"""Tests config.py."""
def test_subreddits_count():
    import src.config as cfg
    all_subs = (cfg.SUBS_INFRA + cfg.SUBS_ERP + cfg.SUBS_DEV
                + cfg.SUBS_IA + cfg.SUBS_CRYPTO + cfg.SUBS_SECU)
    assert len(all_subs) == 21

def test_default_subreddits():
    import src.config as cfg
    assert "sysadmin" in cfg.DEFAULT_SUBREDDITS
    assert "shopify" in cfg.DEFAULT_SUBREDDITS
    assert "ClaudeAI" in cfg.DEFAULT_SUBREDDITS

def test_graph_defaults():
    import src.config as cfg
    assert cfg.GRAPH_SENDER == "bot@blackpearl.re"

def test_perplexity_budget():
    import src.config as cfg
    assert cfg.MAX_API_CALLS_PER_RUN == 50

def test_scoring_thresholds():
    import src.config as cfg
    assert cfg.SCORE_TOP >= 80
    assert cfg.SCORE_INTERESTING >= 65
    assert cfg.SCORE_INTERESTING < cfg.SCORE_TOP
