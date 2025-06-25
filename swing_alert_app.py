# swing_alert_app.py
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import schedule
import time

# Define stock watchlist and trade parameters
stocks = {
    "KPITTECH.NS": {
        "entry_min": 1320,
        "entry_max": 1330,
        "stop_loss": 1270,
        "target1": 1410,
        "target2": 1460
    },
    "INDUSTOWER.NS": {
        "entry_min": 405,
        "entry_max": 407,
        "stop_loss": 392,
        "target1": 425,
        "target2": 444
    }
}

# Function to scan and display alerts
def run_swing_scanner():
    # Set date range for historical data
    end = datetime.today()
    start = end - timedelta(days=30)

    # Load data and analyze
    st.title("📈 Swing Trade Alert System (2–4 Days)")
    st.caption("Live scanner for winning breakout stocks like KPITTECH & INDUSTOWER")

    for symbol, config in stocks.items():
        st.subheader(f"{symbol}")
        df = yf.download(symbol, start=start, end=end)

        if df.empty:
            st.error("No data found. Check symbol or internet connection.")
            continue

        # Calculate 20-day average volume
        df['20_day_avg_vol'] = df['Volume'].rolling(window=20).mean()

        # Trigger condition: price in entry zone + volume > 1.5x avg
        latest = df.iloc[-1]
        trigger = (
            config['entry_min'] <= latest['Close'] <= config['entry_max']
            and latest['Volume'] > 1.5 * latest['20_day_avg_vol']
        )

        st.write(f"**Current Price:** ₹{latest['Close']:.2f}")
        st.write(f"**Volume:** {int(latest['Volume'])}, **Avg Vol (20D):** {int(latest['20_day_avg_vol'])}")

        if trigger:
            st.success("✅ Entry Conditions Met! Possible swing setup.")
            st.markdown(f"**Entry Zone**: ₹{config['entry_min']} – ₹{config['entry_max']}")
            st.markdown(f"**Target 1**: ₹{config['target1']}, **Target 2**: ₹{config['target2']}")
            st.markdown(f"**Stop Loss**: ₹{config['stop_loss']}")
        else:
            st.warning("⚠️ Entry conditions **not met** yet.")

        st.line_chart(df[['Close']].tail(30))

# Run scanner
run_swing_scanner()

# Optional: schedule daily auto-refresh (commented out unless used in script automation)
# def scheduled_job():
#     run_swing_scanner()
# schedule.every().day.at("10:00").do(scheduled_job)
# while True:
#     schedule.run_pending()
#     time.sleep(60)
