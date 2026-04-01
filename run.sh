#!/bin/bash
# reddit-scout v2 — local runner
# Called by launchd or manually

set -euo pipefail

SCOUT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCOUT_DIR"

# Load env
if [ -f .env ]; then
    set -a
    source .env
    set +a
fi

LOG_FILE="$SCOUT_DIR/logs/scout-$(date +%Y%m%d_%H%M).log"
mkdir -p "$SCOUT_DIR/logs"

echo "=== reddit-scout v2 — $(date) ===" | tee "$LOG_FILE"

# Run the agent
python3 -m src.agent 2>&1 | tee -a "$LOG_FILE"

# Push reports + DB to GitHub (optional, non-blocking)
git add data/scout.db 2>/dev/null || true
git add reports/*.md 2>/dev/null || true
git diff --cached --quiet || {
    git commit -m "scout: rapport $(date -u +%Y-%m-%d_%H%M)"
    git push origin main 2>/dev/null || echo "[!] Push failed — will retry next run"
}

# macOS notification
osascript -e 'display notification "Scan termine" with title "reddit-scout v2"' 2>/dev/null || true

echo "=== Done ===" | tee -a "$LOG_FILE"
