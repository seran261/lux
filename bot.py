import requests, time, asyncio
import pandas as pd
from telegram import Bot
from config import *
from strategy import generate_signal

bot = Bot(token=TELEGRAM_TOKEN)

# 🔒 OKX USDT PERPETUALS (Top coins)
SYMBOLS = [
    "BTC-USDT-SWAP","ETH-USDT-SWAP","BNB-USDT-SWAP","SOL-USDT-SWAP",
    "XRP-USDT-SWAP","ADA-USDT-SWAP","AVAX-USDT-SWAP","DOGE-USDT-SWAP",
    "DOT-USDT-SWAP","LINK-USDT-SWAP","MATIC-USDT-SWAP","LTC-USDT-SWAP",
    "TRX-USDT-SWAP","ATOM-USDT-SWAP","OP-USDT-SWAP","AR-USDT-SWAP",
    "NEAR-USDT-SWAP","APT-USDT-SWAP","SUI-USDT-SWAP","INJ-USDT-SWAP"
]

last_signal = {}
last_heartbeat = 0

def fetch_ohlcv(symbol):
    url = "https://www.okx.com/api/v5/market/candles"
    params = {
        "instId": symbol,
        "bar": TIMEFRAME,
        "limit": 100
    }

    try:
        r = requests.get(url, params=params, timeout=10)
        data = r.json()

        if data.get("code") != "0":
            return None

        candles = data["data"]
        if not candles:
            return None

        df = pd.DataFrame(
            candles,
            columns=["t","open","high","low","close","vol","volCcy","volCcyQuote","confirm"]
        )

        df = df[["t","open","high","low","close"]].astype(float)
        df = df.sort_values("t")
        return df

    except Exception as e:
        print(symbol, e)
        return None

async def send(msg):
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML")

async def scan():
    global last_heartbeat

    await send("✅ <b>OKX FUTURES BOT STARTED</b>\nRailway Safe | EMA Strategy")

    while True:
        now = time.time()

        # 💓 HEARTBEAT
        if now - last_heartbeat > HEARTBEAT_INTERVAL:
            await send("💓 Bot Alive | Scanning OKX Futures")
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
                f"⏱ TF: {TIMEFRAME}\n\n"
                f"Entry: {entry:.4f}\n"
                f"SL: {sl:.4f}\n"
                f"TP: {tp:.4f}\n"
                f"RR: 1:{RR_RATIO}"
            )
            await asyncio.sleep(1)

        await asyncio.sleep(SCAN_INTERVAL)

asyncio.run(scan())
