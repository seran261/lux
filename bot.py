import requests
import pandas as pd
import asyncio, time
from telegram import Bot
from config import *
from strategy import generate_signal

bot = Bot(token=TELEGRAM_TOKEN)

# ✅ SAFE USDT PERPETUAL SYMBOLS
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
    r = requests.get(url, params=params, timeout=10).json()
    data = r["result"]["list"]
    df = pd.DataFrame(
        data,
        columns=["t","open","high","low","close","vol","turnover"]
    )
    df = df.astype(float)
    df = df.sort_values("t")
    return df

async def send(msg):
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML")

async def scan():
    global last_heartbeat
    await send("✅ <b>BYBIT FUTURES BOT STARTED</b>\nDirect API | No CCXT | Railway Safe")

    while True:
        now = time.time()

        if now - last_heartbeat > HEARTBEAT_INTERVAL:
            await send("💓 Bot Alive | EMA Strategy Running")
            last_heartbeat = now

        for symbol in SYMBOLS:
            try:
                df = fetch_ohlcv(symbol)
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
                        f"⏱ TF: {TIMEFRAME}m\n\n"
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
