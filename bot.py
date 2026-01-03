import requests, time, asyncio
import pandas as pd
from telegram import Bot
from config import *
from strategy import generate_signal

bot = Bot(token=TELEGRAM_TOKEN)

SYMBOLS = [
    "BTCUSDT","ETHUSDT","BNBUSDT","SOLUSDT","XRPUSDT",
    "ADAUSDT","AVAXUSDT","DOGEUSDT","DOTUSDT","LINKUSDT",
    "MATICUSDT","LTCUSDT","TRXUSDT","ATOMUSDT","OPUSDT",
    "ARUSDT","NEARUSDT","APTUSDT","SUIUSDT","INJUSDT"
]

last_signal = {}
last_heartbeat = 0

def fetch_ohlcv(symbol):
    url = "https://api.bybit.com/v5/market/kline"
    params = {
        "category": "linear",
        "symbol": symbol,
        "interval": TIMEFRAME,
        "limit": 100
    }

    try:
        r = requests.get(url, params=params, timeout=10)

        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}")

        data = r.json()

        if data.get("retCode") != 0:
            raise Exception(data.get("retMsg"))

        candles = data["result"]["list"]
        if not candles:
            raise Exception("No candles")

        df = pd.DataFrame(
            candles,
            columns=["t","open","high","low","close","vol","turnover"]
        )
        df = df.astype(float)
        return df.sort_values("t")

    except Exception as e:
        print(symbol, e)
        return None

async def send(msg):
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML")

async def scan():
    global last_heartbeat

    await send("✅ <b>BYBIT FUTURES BOT STARTED</b>\nStable JSON Handling Enabled")

    while True:
        now = time.time()

        if now - last_heartbeat > HEARTBEAT_INTERVAL:
            await send("💓 Bot Alive | EMA Strategy Running")
            last_heartbeat = now

        for symbol in SYMBOLS:
            df = fetch_ohlcv(symbol)
            if df is None or len(df) < 50:
                continue

            signal = generate_signal(df, EMA_LENGTH, RR_RATIO)
            if not signal:
                continue

            side, entry, sl, tp = signal
            candle = df["t"].iloc[-1]
            key = f"{symbol}_{side}"

            if last_signal.get(key) == candle:
                continue

            last_signal[key] = candle

            await send(
                f"<b>{side} SIGNAL</b>\n"
                f"📊 {symbol}\n"
                f"⏱ TF: {TIMEFRAME}m\n\n"
                f"Entry: {entry:.4f}\n"
                f"SL: {sl:.4f}\n"
                f"TP: {tp:.4f}\n"
                f"RR: 1:{RR_RATIO}"
            )
            await asyncio.sleep(1)

        await asyncio.sleep(SCAN_INTERVAL)

asyncio.run(scan())
