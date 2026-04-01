"""Configuration reddit-scout v2 — BLACK PEARL."""

import os
from dotenv import load_dotenv

load_dotenv()

# ── API Keys
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
PERPLEXITY_MODEL = "sonar-pro"
PERPLEXITY_BASE_URL = "https://api.perplexity.ai"

# ── Email O365
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.office365.com")
SMTP_PORT = int(os.getenv("SMTP_PORT") or "587")
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO", "")

# ── Subreddits BLACK PEARL (20)
SUBS_INFRA = ["sysadmin", "homelab", "selfhosted", "docker", "devops"]
SUBS_ERP = ["shopify", "odoo", "ecommerce"]
SUBS_DEV = ["golang", "nextjs", "programming"]
SUBS_IA = ["LocalLLaMA", "MachineLearning", "ClaudeAI", "ChatGPT"]
SUBS_CRYPTO = ["CryptoCurrency", "algotrading", "defi"]
SUBS_SECU = ["netsec", "cybersecurity"]

DEFAULT_SUBREDDITS = (
    SUBS_INFRA + SUBS_ERP + SUBS_DEV + SUBS_IA + SUBS_CRYPTO + SUBS_SECU
)

# ── Mots-cles bonus
TRACKED_KEYWORDS = [
    "VMware", "ESXi", "vSphere", "Sophos", "SAGE", "X3",
    "Pimcore", "PIM", "MCP", "Claude", "agents", "RAG",
    "Go", "API", "webhook", "trading bot", "DeFi", "yield",
    "CVE", "pentest", "zero-day",
]

# ── Collecte
POSTS_PER_SUB = 25
MIN_SCORE = 10
RATE_LIMIT_SECONDS = 2
USER_AGENT = "reddit-scout/2.0 (by u/blackpearl-rtd)"

# ── Signaux faibles
WEAK_SIGNAL_MAX_SCORE = 100
WEAK_SIGNAL_MIN_COMMENTS = 20
WEAK_SIGNAL_COMMENT_RATIO = 0.5

# ── Scoring IA
SCORE_TOP = 80
SCORE_INTERESTING = 65
MAX_RETAINED_POSTS = 20

# ── Alertes
ALERT_SCORE_THRESHOLD = 5000
ALERT_SENTIMENT_SHIFT = 0.4

# ── Database
DB_PATH = os.getenv("DB_PATH", "data/scout.db")
DEDUP_TTL_DAYS = 30

# ── Output
REPORTS_DIR = "reports"
MAX_API_CALLS_PER_RUN = 50
