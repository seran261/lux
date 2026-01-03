import requests, time, asyncio
import pandas as pd
from telegram import Bot
from config import *
from strategy import generate_signal

bot = Bot(token=TELEGRAM_TOKEN)

SYMBOLS = [
    "BTC-USDT-SWAP","ETH-USDT-SWAP","BNB-USDT-SWAP","SOL-USDT-SWAP",
    "XRP-USDT-SWAP","ADA-USDT-SWAP","AVAX-USDT-SWAP","DOGE-USDT-SWAP",
    "DOT-USDT-SWAP","LINK-USDT-SWAP","MATIC-USDT-SWAP","LTC-USDT-SWAP",
    "TRX-USDT-SWAP","ATOM-USDT-SWAP","OP-USDT-SWAP","AR-USDT-SWAP",
    "NEAR-USDT-SWAP","APT-USDT-SWAP","SUI-USDT-SWAP","INJ-USDT-SWAP"
]

last_signal = {}
active_trades = {}   # 🔑 TRACK OPEN TRADES
last_heartbeat = 0

# ===== OKX OHLCV =====
def fetch_ohlcv(symbol):
    url = "https://www.okx.com/api/v5/market/candles"
    params = {"instId": symbol, "bar": TIMEFRAME, "limit": 100}

    try:
        r = requests.get(url, params=params, timeout=10).json()
        if r.get("code") != "0":
            return None

        df = pd.DataFrame(
            r["data"],
            columns=["t","open","high","low","close","vol","volCcy","volCcyQuote","confirm"]
        )
        df = df[["t","open","high","low","close"]].astype(float)
        return df.sort_values("t")

    except Exception:
        return None

async def send(msg):
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML")

# ===== CHECK TP / SL =====
async def check_trade(symbol, trade, candle):
    high = candle["high"]
    low = candle["low"]

    if trade["side"] == "LONG":
        if high >= trade["tp"]:
            await send(f"🎯 <b>TP HIT</b>\n📊 {symbol}\nTP: {trade['tp']:.4f}")
            return True
        if low <= trade["sl"]:
            await send(f"🛑 <b>SL HIT</b>\n📊 {symbol}\nSL: {trade['sl']:.4f}")
            return True

    if trade["side"] == "SHORT":
        if low <= trade["tp"]:
            await send(f"🎯 <b>TP HIT</b>\n📊 {symbol}\nTP: {trade['tp']:.4f}")
            return True
        if high >= trade["sl"]:
            await send(f"🛑 <b>SL HIT</b>\n📊 {symbol}\nSL: {trade['sl']:.4f}")
            return True

    return False

# ===== MAIN LOOP =====
async def scan():
    global last_heartbeat

    await send("✅ <b>OKX FUTURES BOT STARTED</b>\nTP / SL Alerts Enabled")

    while True:
        now = time.time()

        if now - last_heartbeat > HEARTBEAT_INTERVAL:
            await send("💓 Bot Alive | Monitoring trades")
            last_heartbeat = now

        for symbol in SYMBOLS:
            df = fetch_ohlcv(symbol)
            if df is None or len(df) < 50:
                continue

            last_candle = df.iloc[-1]

            # 🔁 CHECK ACTIVE TRADE
            if symbol in active_trades:
                closed = await check_trade(symbol, active_trades[symbol], last_candle)
                if closed:
                    del active_trades[symbol]
                continue

            # 🔍 LOOK FOR NEW SIGNAL
            signal = generate_signal(df, EMA_LENGTH, RR_RATIO)
            if not signal:
                continue

            side, entry, sl, tp = signal
            candle_time = df["t"].iloc[-1]

            key = f"{symbol}_{side}"
            if last_signal.get(key) == candle_time:
                continue

            last_signal[key] = candle_time

            active_trades[symbol] = {
                "side": side,
                "entry": entry,
                "sl": sl,
                "tp": tp
            }

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
