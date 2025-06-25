# swing_alert_app.py
import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta

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

def run_swing_scanner():
    st.title("📈 Swing Trade Alert System (2–4 Days)")
    st.caption("Live scanner for breakout stocks like KPITTECH & INDUSTOWER")

    end = datetime.today()
    start = end - timedelta(days=30)

    for symbol, config in stocks.items():
        st.subheader(f"{symbol}")

        try:
            df = yf.download(symbol, start=start, end=end)
            if df.empty:
                st.error(f"⚠️ No data found for {symbol}. Possibly a connection or symbol issue.")
                continue

            df['20_day_avg_vol'] = df['Volume'].rolling(window=20).mean()
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

        except Exception as e:
            st.error(f"❌ Error loading {symbol}: {e}")

# Run the scanner
run_swing_scanner()
