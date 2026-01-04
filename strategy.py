def ema(series, length):
    return series.ewm(span=length, adjust=False).mean()

def check_signal(df, ema_len):
    df["ema"] = ema(df["close"], ema_len)

    prev = df.iloc[-2]
    last = df.iloc[-1]

    if prev["close"] < prev["ema"] and last["close"] > last["ema"]:
        return "LONG"

    if prev["close"] > prev["ema"] and last["close"] < last["ema"]:
        return "SHORT"

    return None
