import requests, time, asyncio
import pandas as pd
from telegram import Bot
from config import *
from strategy import check_signal

bot = Bot(token=TELEGRAM_TOKEN)

SYMBOLS = {
    "BTC": "BTC-USDT-SWAP",
    "ETH": "ETH-USDT-SWAP",
    "SOL": "SOL-USDT-SWAP",
    "LTC": "LTC-USDT-SWAP",
    "BNB": "BNB-USDT-SWAP",
    "TAO": "TAO-USDT-SWAP"
}

active_trades = {}
last_signal = {}
last_heartbeat = 0

def fetch_ohlcv(symbol, tf):
    url = "https://www.okx.com/api/v5/market/candles"
    params = {"instId": symbol, "bar": tf, "limit": 120}

    try:
        r = requests.get(url, params=params, timeout=10).json()
        if r.get("code") != "0":
            return None

        df = pd.DataFrame(
            r["data"],
            columns=["t","open","high","low","close","vol","v2","v3","confirm"]
        )
        df = df[["t","open","high","low","close"]].astype(float)
        return df.sort_values("t")

    except:
        return None

def calc_levels(side, entry):
    sl = entry * (1 - STOP_LOSS_PCT/100) if side == "LONG" else entry * (1 + STOP_LOSS_PCT/100)
    tps = []

    for p in TP_LEVELS:
        if side == "LONG":
            tps.append(entry * (1 + p/100))
        else:
            tps.append(entry * (1 - p/100))

    return sl, tps

async def send(msg):
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML")

async def scan():
    global last_heartbeat

    await send(
        "✅ <b>OKX MULTI-TF BOT STARTED</b>\n"
        "BTC ETH SOL LTC BNB TAO\n"
        "5m → 1W | TP 1%–5%"
    )

    while True:
        now = time.time()

        if now - last_heartbeat > HEARTBEAT_INTERVAL:
            await send("💓 Bot Alive | Multi-TF EMA Strategy Running")
            last_heartbeat = now

        for name, symbol in SYMBOLS.items():
            for tf_name, tf in TIMEFRAMES.items():

                df = fetch_ohlcv(symbol, tf)
                if df is None or len(df) < 50:
                    continue

                signal = check_signal(df, EMA_LENGTH)
                if not signal:
                    continue

                candle_time = df["t"].iloc[-1]
                key = f"{symbol}_{tf}_{signal}"

                if last_signal.get(key) == candle_time:
                    continue

                last_signal[key] = candle_time
                entry = df["close"].iloc[-1]
                sl, tps = calc_levels(signal, entry)

                tp_text = "\n".join([f"TP{i+1}: {tp:.4f}" for i, tp in enumerate(tps)])

                await send(
                    f"<b>{signal} SIGNAL</b>\n"
                    f"📊 {name}\n"
                    f"⏱ TF: {tf_name}\n\n"
                    f"Entry: {entry:.4f}\n"
                    f"SL: {sl:.4f}\n"
                    f"{tp_text}"
                )

                await asyncio.sleep(1)

        await asyncio.sleep(SCAN_INTERVAL)

asyncio.run(scan())
