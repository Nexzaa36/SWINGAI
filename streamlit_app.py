# swinglit_app.py
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

# --------------------------
# CONFIGURATION
# --------------------------
MAX_RISK_PCT = 2  # Max stop loss %
RR_RATIO = 4       # Reward to Risk

# Static NIFTY 500 stock list (replace with dynamic fetch later)
# For now, using sample subset for performance
NIFTY_500 = [
    "ICICIBANK.NS", "RELIANCE.NS", "HDFCBANK.NS", "INFY.NS", "TCS.NS",
    "LT.NS", "SBIN.NS", "KOTAKBANK.NS", "AXISBANK.NS", "AUROPHARMA.NS"
    # Add full list here or load from CSV
]

# --------------------------
# Functions
# --------------------------

def get_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def get_sma(series, period):
    return series.rolling(window=period).mean()

def fetch_stock_data(symbol, start, end):
    try:
        df = yf.download(symbol, start=start, end=end)
        if df.empty:
            return None
        df['EMA_5'] = get_ema(df['Close'], 5)
        df['EMA_20'] = get_ema(df['Close'], 20)
        df['Volume_SMA_20'] = get_sma(df['Volume'], 20)
        df['Range'] = df['High'] - df['Low']
        df['Range_SMA_20'] = get_sma(df['Range'], 20)
        return df
    except:
        return None

def check_breakout_criteria(df):
    if df is None or len(df) < 21:
        return False, None

    df = df.dropna()  # <-- Drop rows with any NaN
    if df.empty or len(df) < 21:
        return False, None

    today = df.iloc[-1]
    prev = df.iloc[-2]

    # Conditions
    c1 = today['Close'] > today['EMA_5']
    c2 = today['Volume'] > today['Volume_SMA_20'] * 1.5
    c3 = today['Close'] > today['Open']
    c4 = today['Close'] > prev['High']
    c5 = today['Range'] < 1.5 * today['Range_SMA_20']
    c6 = today['Close'] >= df['Close'].iloc[-20:].min()

    if all([c1, c2, c3, c4, c5, c6]):
        entry = today['Close']
        sl = round(entry * 0.98, 2)  # 2% SL
        target = round(entry + (entry - sl) * RR_RATIO, 2)
        return True, {"entry": entry, "sl": sl, "target": target}
    return False, None

# --------------------------
# Streamlit UI
# --------------------------
st.set_page_config(page_title="Swing Breakout Scanner 📈", layout="wide")
st.title("Swing Breakout Scanner 📈")

capital = st.number_input("Enter your capital (₹)", min_value=1000, value=17000)
risk_pct = st.selectbox("Risk per trade (%)", [1, 2], index=1)
rr_ratio = st.selectbox("Reward-to-Risk Ratio", [2, 3, 4], index=2)

# Backtest date selection
st.subheader("📅 Select Date for Scanning")
btest_date = st.date_input("Choose a date (today or past):", datetime.now().date())

# Date logic based on user input
today = btest_date
start = today - timedelta(days=30)
end = today + timedelta(days=1)  # include selected day

st.subheader("Swing Trade Setups for: " + str(today))

results = []

with st.spinner("Scanning NIFTY 500 stocks..."):
    for symbol in NIFTY_500:
        df = fetch_stock_data(symbol, start, end)
        is_valid, levels = check_breakout_criteria(df)
        if is_valid:
            risk_amt = capital * risk_pct / 100
            qty = int(risk_amt / (levels['entry'] - levels['sl']))
            results.append({
                "Symbol": symbol,
                "Entry": levels['entry'],
                "SL": levels['sl'],
                "Target": levels['target'],
                "Qty": qty
            })

if results:
    df_results = pd.DataFrame(results)
    st.dataframe(df_results)
else:
    st.info("No trade setups for the selected date. Try another date 📆")
