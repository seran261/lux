import os
import sys

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN:
    print("❌ TELEGRAM_TOKEN missing in environment variables")
    sys.exit(1)

if not CHAT_ID:
    print("❌ CHAT_ID missing in environment variables")
    sys.exit(1)

TIMEFRAME = "5m"
EMA_LENGTH = 34
RR_RATIO = 2.0

SCAN_INTERVAL = 60
HEARTBEAT_INTERVAL = 900
MAX_COINS = 50
