import pandas as pd
import numpy as np

def ema(series, length):
    return series.ewm(span=length, adjust=False).mean()

def generate_signal(df, ema_len):
    df["ema"] = ema(df["close"], ema_len)

    last = df.iloc[-1]
    prev = df.iloc[-2]

    long_signal = prev["close"] < prev["ema"] and last["close"] > last["ema"]
    short_signal = prev["close"] > prev["ema"] and last["close"] < last["ema"]

    if long_signal:
        sl = df["low"].rolling(10).min().iloc[-1]
        tp = last["close"] + (last["close"] - sl) * 2
        return "LONG", last["close"], sl, tp

    if short_signal:
        sl = df["high"].rolling(10).max().iloc[-1]
        tp = last["close"] - (sl - last["close"]) * 2
        return "SHORT", last["close"], sl, tp

    return None
