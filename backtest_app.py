import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="Swing Trade App", layout="wide")

# --- Sidebar Configuration ---
st.sidebar.title("📋 Settings")
capital = st.sidebar.number_input("Enter your capital (₹)", min_value=1000, value=17000)
risk_percent = st.sidebar.slider("Risk per trade (%)", 1, 5, 2)
reward_ratio = st.sidebar.selectbox("Reward-to-Risk Ratio", [2, 3, 4], index=1)
backtest_days = st.sidebar.slider("Backtest Days", 30, 365, 100)

stocks = ['ICICIBANK.NS', 'TATASTEEL.NS', 'IRCON.NS', 'RKFORGE.NS', 'SECURKLOUD.NS']

# --- Scanner Logic ---
def calculate_signals(stock):
    end = datetime.today()
    start = end - timedelta(days=20)
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

# --- Backtest Logic ---
def backtest_strategy(stock):
    end = datetime.today()
    start = end - timedelta(days=backtest_days + 30)
    df = yf.download(stock, start=start, end=end)

    if df.empty or len(df) < 30:
        return 0, 0, pd.DataFrame()

    df["20EMA"] = df["Close"].ewm(span=20).mean()
    df.dropna(inplace=True)

    wins, losses = 0, 0
    results = []

    for i in range(1, len(df) - 5):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]

        if prev["Close"] < prev["20EMA"] and curr["Close"] > curr["20EMA"] and curr["Close"] > prev["High"]:
            entry = curr["Close"]
            sl = curr["Low"]
            risk = entry - sl
            target = entry + reward_ratio * risk

            next_days = df.iloc[i + 1:i + 6]
            hit = "None"
            for _, day in next_days.iterrows():
                if day["Low"] <= sl:
                    hit = "SL"
                    break
                if day["High"] >= target:
                    hit = "Target"
                    break

            if hit == "Target":
                wins += 1
            elif hit == "SL":
                losses += 1

            qty = int((risk_percent / 100 * capital) // risk)
            results.append({
                "Date": curr.name.date(),
                "Stock": stock,
                "Entry": round(entry, 2),
                "SL": round(sl, 2),
                "Target": round(target, 2),
                "Qty": qty,
                "Hit": hit
            })

    return wins, losses, pd.DataFrame(results)

# --- Tabs for Scanner and Backtest ---
tab1, tab2 = st.tabs(["🔍 Live Scanner", "🧪 Backtest"])

with tab1:
    st.header("🔍 Today's Swing Trade Setups")
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

with tab2:
    st.header("🧪 Backtest Swing Strategy")
    if st.button("Run Backtest"):
        total_wins, total_losses = 0, 0
        all_trades = []

        with st.spinner("Scanning..."):
            for stock in stocks:
                wins, losses, trades = backtest_strategy(stock)
                total_wins += wins
                total_losses += losses
                if not trades.empty:
                    all_trades.append(trades)

        if all_trades:
            df_result = pd.concat(all_trades)
            st.subheader("📄 Trade Log")
            st.dataframe(df_result)

            accuracy = total_wins / (total_wins + total_losses) * 100 if total_wins + total_losses > 0 else 0
            st.markdown(f"""
            ### 📈 Backtest Summary
            - Total Trades: **{total_wins + total_losses}**
            - ✅ Wins: **{total_wins}**
            - ❌ Losses: **{total_losses}**
            - 🎯 Accuracy: **{accuracy:.2f}%**
            """)
        else:
            st.warning("No valid trades found in this backtest range.")
