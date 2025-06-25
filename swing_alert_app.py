import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Swing Trade Scanner", layout="wide")

st.title("Swing Breakout Scanner 📈")
capital = st.number_input("Enter your capital (₹)", min_value=1000, value=17000)
risk_percent = st.slider("Risk per trade (%)", 1, 5, 2)
reward_ratio = st.selectbox("Reward-to-Risk Ratio", [2, 3, 4], index=1)

stocks = ['ICICIBANK.NS', 'TATASTEEL.NS', 'IRCON.NS', 'RKFORGE.NS', 'SECURKLOUD.NS']
end = datetime.today()
start = end - timedelta(days=20)

def calculate_signals(stock):
    df = yf.download(stock, start=start, end=end)
    if df.empty or len(df) < 20:
        return None

    df["20EMA"] = df["Close"].ewm(span=20).mean()
    last = df.iloc[-1]
    prev = df.iloc[-2]

    if (prev["Close"] < prev["20EMA"]) and (last["Close"] > last["20EMA"]) and (last["Close"] > prev["High"]):
        sl = last["Low"]
        entry = last["Close"]
        risk = entry - sl
        target = entry + reward_ratio * risk
        qty = int((risk_percent / 100 * capital) // risk)
        return {
            "Stock": stock,
            "Entry": round(entry, 2),
            "SL": round(sl, 2),
            "Target": round(target, 2),
            "Qty": qty,
            "RR": reward_ratio
        }
    return None

st.subheader("Today's Swing Trade Setups")

results = []
for stock in stocks:
    signal = calculate_signals(stock)
    if signal:
        results.append(signal)

if results:
    df = pd.DataFrame(results)
    st.dataframe(df)
else:
    st.info("No trade setups today. Come back tomorrow between 10–11 AM 📆")
