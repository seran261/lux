import ccxt
import pandas as pd
import asyncio
from telegram import Bot
from config import *
from strategy import generate_signal

exchange = ccxt.binance({
    "enableRateLimit": True,
    "options": {"defaultType": "future"}
})

bot = Bot(token=TELEGRAM_TOKEN)

def get_top_50():
    markets = exchange.load_markets()
    usdt = [m for m in markets if m.endswith("USDT") and markets[m]["active"]]
    return usdt[:50]

async def send(msg):
    await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="HTML")

async def scan():
    symbols = get_top_50()
    await send("🤖 Bot Started | EMA Strategy Active")

    while True:
        for symbol in symbols:
            try:
                ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=100)
                df = pd.DataFrame(ohlcv, columns=["t","open","high","low","close","v"])
                signal = generate_signal(df, EMA_LENGTH)

                if signal:
                    side, entry, sl, tp = signal
                    msg = f"""
<b>{side} SIGNAL</b>
📊 <b>{symbol}</b>
⏱ TF: {TIMEFRAME}

Entry: {entry:.4f}
SL: {sl:.4f}
TP: {tp:.4f}

📐 RR: 1:{RR_RATIO}
"""
                    await send(msg)
                    await asyncio.sleep(2)

            except Exception as e:
                print(symbol, e)

        await asyncio.sleep(SCAN_INTERVAL)

asyncio.run(scan())
