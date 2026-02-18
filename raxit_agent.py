



import yfinance as yf
import pandas as pd
import requests
import datetime
import os
import traceback

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

        payload = {
            "chat_id": CHAT_ID,
            "text": message
        }
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram Error:", e)

# =========================
# 📊 GET NIFTY 500 LIST
# =========================

def get_nifty500():
    url = "https://archives.nseindia.com/content/indices/ind_nifty500list.csv"
    df = pd.read_csv(url)
    symbols = df['Symbol'].tolist()
    return symbols

# =========================
# 📈 SCORE CALCULATION
# =========================

def calculate_score(symbol):
    try:
        data = yf.download(symbol + ".NS", period="6mo", interval="1d", progress=False)

        if len(data) < 60:
            return None

        # Momentum
        one_month_return = data['Close'].pct_change(21).iloc[-1]
        three_month_return = data['Close'].pct_change(63).iloc[-1]

        score = (one_month_return * 50) + (three_month_return * 50)

        # Breakout Detection
        recent_close = data['Close'].iloc[-1]
        highest_60 = data['Close'].rolling(60).max().iloc[-2]
        breakout = recent_close > highest_60

        return {
            "symbol": symbol,
            "score": score,
            "breakout": breakout
        }

    except Exception:
        return None

# =========================
# 🚀 MAIN ENGINE
# =========================

def main():
    try:
        today = datetime.datetime.now().strftime("%d-%b-%Y")
        symbols = get_nifty500()

        results = []

        for symbol in symbols:
            result = calculate_score(symbol)
            if result:
                results.append(result)

        if not results:
            send_telegram("⚠️ Raxit AI: No data processed today.")
            return

        df = pd.DataFrame(results)

        # Remove invalid rows
        df = df.dropna(subset=["score"])

        # Ensure score is numeric
        df["score"] = pd.to_numeric(df["score"], errors="coerce")

        df = df.dropna(subset=["score"])

        if df.empty:
            send_telegram("⚠️ Raxit AI: No valid stocks processed today.")
            return

        df = df.sort_values(by="score", ascending=False).head(10)


        message = f"📊 RAXIT DAILY TOP 10\n📅 {today}\n\n"

        for index, row in df.iterrows():
            line = f"{row['symbol']} | Score: {round(row['score'], 2)}"
            if row['breakout']:
                line += " 🔥 Breakout"
            message += line + "\n"

        send_telegram(message)

    except Exception as e:
        error_message = f"❌ Raxit AI Error:\n{traceback.format_exc()}"
        send_telegram(error_message)

# =========================

if __name__ == "__main__":
    main()
