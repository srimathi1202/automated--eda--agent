"""
config/settings.py
------------------
Centralised configuration loader.
All secrets come from environment variables (never hardcoded).
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
load_dotenv(Path(__file__).parent.parent / ".env")


# ── Anthropic ──────────────────────────────────────────────────────────
ANTHROPIC_API_KEY: str = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL: str      = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS: int = 4096

# ── Email (Gmail SMTP) ─────────────────────────────────────────────────
EMAIL_SENDER:    str = os.environ.get("EMAIL_SENDER", "")
EMAIL_PASSWORD:  str = os.environ.get("EMAIL_PASSWORD", "")
EMAIL_RECIPIENT: str = os.environ.get("EMAIL_RECIPIENT", "")
SMTP_HOST:       str = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT:       int = int(os.environ.get("SMTP_PORT", 587))

# ── SendGrid (optional alternative) ───────────────────────────────────
SENDGRID_API_KEY: str = os.environ.get("SENDGRID_API_KEY", "")

# ── Paths ──────────────────────────────────────────────────────────────
BASE_DIR:      Path = Path(__file__).parent.parent
OUTPUTS_DIR:   Path = BASE_DIR / "outputs"
TEMPLATES_DIR: Path = BASE_DIR / "templates"
DATA_DIR:      Path = BASE_DIR / "data"

OUTPUTS_DIR.mkdir(exist_ok=True)

# ── Chart settings ─────────────────────────────────────────────────────
MAX_CATEGORIES_BAR:    int   = 20
OUTLIER_IQR_FACTOR:    float = 1.5
CORRELATION_THRESHOLD: float = 0.7


def validate_config() -> list[str]:
    """Return a list of missing required settings."""
    missing = []
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if not EMAIL_SENDER:
        missing.append("EMAIL_SENDER")
    if not EMAIL_PASSWORD:
        missing.append("EMAIL_PASSWORD")
    return missing
