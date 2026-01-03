def ema(series, length):
    return series.ewm(span=length, adjust=False).mean()

def generate_signal(df, ema_len, rr):
    df["ema"] = ema(df["close"], ema_len)

    prev = df.iloc[-2]
    last = df.iloc[-1]

    if prev["close"] < prev["ema"] and last["close"] > last["ema"]:
        sl = df["low"].rolling(10).min().iloc[-1]
        tp = last["close"] + (last["close"] - sl) * rr
        return "LONG", last["close"], sl, tp

    if prev["close"] > prev["ema"] and last["close"] < last["ema"]:
        sl = df["high"].rolling(10).max().iloc[-1]
        tp = last["close"] - (sl - last["close"]) * rr
        return "SHORT", last["close"], sl, tp

    return None
