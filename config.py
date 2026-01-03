import os, sys

# ===== TELEGRAM =====
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    print("❌ TELEGRAM_TOKEN or CHAT_ID missing")
    sys.exit(1)

# ===== STRATEGY =====
TIMEFRAME = "5m"     # OKX format: 1m, 5m, 15m, 1H
EMA_LENGTH = 34
RR_RATIO = 2.0

# ===== BOT =====
SCAN_INTERVAL = 60
HEARTBEAT_INTERVAL = 900
