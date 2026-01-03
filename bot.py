import ccxt
import pandas as pd
import asyncio
import time
from telegram import Bot
from config import *
from strategy import generate_signal

# ===== BYBIT (SWAP ONLY – CRITICAL FIX) =====
exchange = ccxt.bybit({
    "enableRateLimit": True,
    "options": {
        "defaultType": "swap",
        "loadAllMarkets": False   # 🔥 PREVENTS SPOT CALLS
    }
})

bot = Bot(token=TELEGRAM_TOKEN)

last_signal = {}
last_heartbeat = 0

# ===== TELEGRAM SEND =====
async def send(msg):
    await bot.send_message(
        chat_id=CHAT_ID,
        text=msg,
        parse_mode="HTML"
    )

# ===== LOAD USDT PERPETUALS ONLY =====
def get_top_symbols():
    markets = exchange.load_markets({"category": "linear"})
    symbols = []

    for symbol, m in markets.items():
        if (
            m.get("swap") is True
            and m.get("quote") == "USDT"
            and m.get("active") is True
        ):
            symbols.append(symbol)

    return symbols[:MAX_COINS]

# ===== MAIN LOOP =====
async def scan():
    global last_heartbeat

    await send("✅ <b>STARTED: BYBIT FUTURES BOT</b>\nUSDT Perpetuals Only")

    symbols = get_top_symbols()

    while True:
        now = time.time()

        # ===== HEARTBEAT =====
        if now - last_heartbeat > HEARTBEAT_INTERVAL:
            await send("💓 Bot Alive | Scanning markets")
            last_heartbeat = now

        for symbol in symbols:
            try:
                ohlcv = exchange.fetch_ohlcv(
                    symbol,
                    timeframe=TIMEFRAME,
                    limit=100
                )

                df = pd.DataFrame(
                    ohlcv,
                    columns=["t", "open", "high", "low", "close", "v"]
                )

                signal = generate_signal(df, EMA_LENGTH, RR_RATIO)

                if signal:
                    side, entry, sl, tp = signal
                    candle_time = df["t"].iloc[-1]

                    key = f"{symbol}_{side}"
                    if last_signal.get(key) == candle_time:
                        continue

                    last_signal[key] = candle_time

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
                print(symbol, e)

        await asyncio.sleep(SCAN_INTERVAL)

# ===== START BOT =====
asyncio.run(scan())
