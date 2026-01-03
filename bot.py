import ccxt
import pandas as pd
import asyncio
import time
from telegram import Bot
from config import *
from strategy import generate_signal

# ===== BYBIT EXCHANGE =====
exchange = ccxt.bybit({
    "enableRateLimit": True,
    "options": {
        "defaultType": "swap"  # USDT Perpetuals
    }
})

bot = Bot(token=TELEGRAM_TOKEN)

last_signal = {}
last_heartbeat = 0

# ===== TELEGRAM SEND =====
async def send(msg):
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML")

# ===== GET TOP COINS =====
def get_top_symbols():
    markets = exchange.load_markets()
    symbols = []

    for sym, m in markets.items():
        if (
            m.get("quote") == "USDT"
            and m.get("swap")
            and m.get("active")
        ):
            symbols.append(sym)

    return symbols[:MAX_COINS]

# ===== MAIN LOOP =====
async def scan():
    global last_heartbeat

    symbols = get_top_symbols()
    await send("🤖 <b>Bybit EMA Bot Started</b>\nScanning Top 50 USDT Perpetuals")

    while True:
        now = time.time()

        # HEARTBEAT
        if now - last_heartbeat > HEARTBEAT_INTERVAL:
            await send("💓 Bot Alive | Scanning markets...")
            last_heartbeat = now

        for symbol in symbols:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=100)
                df = pd.DataFrame(
                    ohlcv,
                    columns=["t", "open", "high", "low", "close", "v"]
                )

                signal = generate_signal(df, EMA_LENGTH, RR_RATIO)

                if signal:
                    side, entry, sl, tp = signal
                    key = f"{symbol}_{side}"

                    if last_signal.get(key) == df["t"].iloc[-1]:
                        continue

                    last_signal[key] = df["t"].iloc[-1]

                    msg = f"""
<b>{side} SIGNAL</b>
📊 <b>{symbol}</b>
⏱ TF: {TIMEFRAME}

🔑 Entry: {entry:.4f}
🛑 SL: {sl:.4f}
🎯 TP: {tp:.4f}

📐 RR: 1:{RR_RATIO}
"""
                    await send(msg)
                    await asyncio.sleep(1)

            except Exception as e:
                print(f"{symbol} error:", e)

        await asyncio.sleep(SCAN_INTERVAL)

# ===== START =====
asyncio.run(scan())
