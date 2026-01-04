import os, sys

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    print("❌ TELEGRAM_TOKEN or CHAT_ID missing")
    sys.exit(1)

EMA_LENGTH = 34
STOP_LOSS_PCT = 1.2

TP_LEVELS = [1, 2, 3, 4, 5]  # percent

TIMEFRAMES = {
    "5m": "5m",
    "15m": "15m",
    "1H": "1H",
    "4H": "4H",
    "1D": "1D",
    "1W": "1W"
}

SCAN_INTERVAL = 60
HEARTBEAT_INTERVAL = 900
