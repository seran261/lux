import requests, time, asyncio
import pandas as pd
from telegram import Bot
from config import *
from strategy import generate_signal

bot = Bot(token=TELEGRAM_TOKEN)

# ===== OKX USDT PERPETUALS =====
SYMBOLS = [
    "BTC-USDT-SWAP","ETH-USDT-SWAP","BNB-USDT-SWAP","SOL-USDT-SWAP",
    "XRP-USDT-SWAP","ADA-USDT-SWAP","AVAX-USDT-SWAP","DOGE-USDT-SWAP",
    "DOT-USDT-SWAP","LINK-USDT-SWAP","MATIC-USDT-SWAP","LTC-USDT-SWAP",
    "TRX-USDT-SWAP","ATOM-USDT-SWAP","OP-USDT-SWAP","AR-USDT-SWAP",
    "NEAR-USDT-SWAP","APT-USDT-SWAP","SUI-USDT-SWAP","INJ-USDT-SWAP"
]

# ===== VOLUME SPIKE SETTINGS =====
VOLUME_LOOKBACK = 20
VOLUME_MULTIPLIER = 2.0   # 2x average volume

last_signal = {}
active_trades = {}
last_heartbeat = 0

# ===== FETCH OKX OHLCV =====
def fetch_ohlcv(symbol):
    url = "https://www.okx.com/api/v5/market/candles"
    params = {"instId": symbol, "bar": TIMEFRAME, "limit": 120}

    try:
        r = requests.get(url, params=params, timeout=10).json()
        if r.get("code") != "0":
            return None

        df = pd.DataFrame(
            r["data"],
            columns=["t","open","high","low","close","vol","volCcy","volQuote","confirm"]
        )

        df = df[["t","open","high","low","close","vol"]].astype(float)
        return df.sort_values("t")

    except Exception:
        return None

# ===== VOLUME SPIKE CHECK =====
def volume_spike(df):
    if len(df) < VOLUME_LOOKBACK + 1:
        return False

    avg_vol = df["vol"].iloc[-(VOLUME_LOOKBACK+1):-1].mean()
    curr_vol = df["vol"].iloc[-1]

    return curr_vol >= avg_vol * VOLUME_MULTIPLIER

async def send(msg):
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML")

# ===== TP / SL CHECK =====
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

    await send(
        "✅ <b>OKX FUTURES BOT STARTED</b>\n"
        "EMA + Volume Spike Filter Enabled"
    )

    while True:
        now = time.time()

        if now - last_heartbeat > HEARTBEAT_INTERVAL:
            await send("💓 Bot Alive | Volume-confirmed signals only")
            last_heartbeat = now

        for symbol in SYMBOLS:
            df = fetch_ohlcv(symbol)
            if df is None or len(df) < 60:
                continue

            last_candle = df.iloc[-1]

            # 🔁 CHECK ACTIVE TRADE
            if symbol in active_trades:
                closed = await check_trade(symbol, active_trades[symbol], last_candle)
                if closed:
                    del active_trades[symbol]
                continue

            # 🔍 SIGNAL LOGIC
            signal = generate_signal(df, EMA_LENGTH, RR_RATIO)
            if not signal:
                continue

            # 🔊 VOLUME SPIKE FILTER
            if not volume_spike(df):
                continue  # ❌ block low-volume signals

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
                f"⏱ TF: {TIMEFRAME}\n"
                f"🔊 Volume Spike: {VOLUME_MULTIPLIER}×\n\n"
                f"Entry: {entry:.4f}\n"
                f"SL: {sl:.4f}\n"
                f"TP: {tp:.4f}\n"
                f"RR: 1:{RR_RATIO}"
            )

            await asyncio.sleep(1)

        await asyncio.sleep(SCAN_INTERVAL)

asyncio.run(scan())
