import ccxt
import pandas as pd
import asyncio
import time
from telegram import Bot
from config import *
from strategy import generate_signal

exchange = ccxt.bybit({
    "enableRateLimit": True,
    "options": {
        "defaultType": "swap",
        "loadAllMarkets": False
    }
})

bot = Bot(token=TELEGRAM_TOKEN)

last_signal = {}
last_heartbeat = 0

async def send(msg):
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML")

def get_top_symbols():
    markets = exchange.load_markets({"category": "linear"})
    return [
        s for s, m in markets.items()
        if m.get("swap") and m.get("quote") == "USDT" and m.get("active")
    ][:MAX_COINS]

async def scan():
    global last_heartbeat

    await send("✅ <b>BYBIT FUTURES BOT STARTED</b>\nUSDT Perpetuals Only")

    symbols = get_top_symbols()

    while True:
        now = time.time()

        if now - last_heartbeat > HEARTBEAT_INTERVAL:
            await send("💓 Bot Alive | Monitoring markets")
            last_heartbeat = now

        for symbol in symbols:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=100)
                df = pd.DataFrame(ohlcv, columns=["t","open","high","low","close","v"])
                signal = generate_signal(df, EMA_LENGTH, RR_RATIO)

                if signal:
                    side, entry, sl, tp = signal
                    candle = df["t"].iloc[-1]
                    key = f"{symbol}_{side}"

                    if last_signal.get(key) == candle:
                        continue

                    last_signal[key] = candle

                    await send(
                        f"<b>{side} SIGNAL</b>\n"
                        f"📊 {symbol}\n"
                        f"⏱ TF: {TIMEFRAME}\n\n"
                        f"Entry: {entry:.4f}\n"
                        f"SL: {sl:.4f}\n"
                        f"TP: {tp:.4f}\n"
                        f"RR: 1:{RR_RATIO}"
                    )
                    await asyncio.sleep(1)

            except Exception as e:
                print(symbol, e)

        await asyncio.sleep(SCAN_INTERVAL)

asyncio.run(scan())
