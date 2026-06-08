import os
import requests
import pandas as pd
import yfinance as yf

# ======================
# TELEGRAM CONFIG
# ======================

TOKEN = os.environ.get("TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": text})

# ======================
# S&P500 UNIVERSE
# ======================

def get_sp500_universe():
    import requests

    url = "https://raw.githubusercontent.com/datasets/s-and-p-500-companies/master/data/constituents.csv"
    import pandas as pd

    df = pd.read_csv(url)
    return df["Symbol"].tolist()

# ======================
# DATA
# ======================

def get_data(symbol):
    try:
        df = yf.download(
            symbol,
            period="6mo",
            interval="1d",
            progress=False,
            threads=False
        )

        if df is None or df.empty:
            return None

        df = df[["Close"]].copy()
        df["Close"] = pd.to_numeric(df["Close"], errors="coerce")
        df = df.dropna()

        if len(df) < 50:
            return None

        return df

    except:
        return None

# ======================
# INDICATORS
# ======================

def ema20(df):
    return df["Close"].ewm(span=20).mean()

def macd(df):
    ema12 = df["Close"].ewm(span=12).mean()
    ema26 = df["Close"].ewm(span=26).mean()
    macd_line = ema12 - ema26
    signal_line = macd_line.ewm(span=9).mean()
    return macd_line, signal_line

# ======================
# SIGNAL LOGIC
# ======================

def check_signal(df):
    df["ema20"] = ema20(df)
    macd_line, signal_line = macd(df)

    df["macd"] = macd_line
    df["signal"] = signal_line

    prev = df.iloc[-2]
    last = df.iloc[-1]

    ema_cross = prev["Close"] < prev["ema20"] and last["Close"] > last["ema20"]
    macd_cross = prev["macd"] < prev["signal"] and last["macd"] > last["signal"]

    return ema_cross and macd_cross

# ======================
# SCAN ENGINE
# ======================

def run_scan():
    signals = []
    symbols = get_us_universe()

    for symbol in symbols:
        try:
            df = get_data(symbol)
            if df is None:
                continue

            if check_signal(df):
                price = float(df.iloc[-1]["Close"])
                signals.append(f"{symbol} @ {round(price, 2)}")

        except:
            continue

    return signals

# ======================
# MAIN
# ======================

if __name__ == "__main__":
    print("S&P500 scan starting...")

    results = run_scan()

    if results:
        msg = "🇺🇸 S&P500 SIGNALS\n\n" + "\n".join(results[:10])
        send_message(msg)
        print("Signals sent:", results)
    else:
        print("No signals found")
