import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go

# ---------------------- SETTINGS ----------------------
RR_RATIO = st.sidebar.selectbox("Select Reward-to-Risk Ratio", [2, 3, 4], index=1)
strict_mode = st.sidebar.toggle("Strict Mode", value=False)

# ---------------------- UI ----------------------
st.title("📈 Swing Breakout Scanner")
capital = st.number_input("Enter your capital (₹)", min_value=1000, value=17000)
risk_pct = st.slider("Risk per trade (%)", min_value=1, max_value=5, value=2)
btest_date = st.date_input("📅 Choose a date (today or past):", datetime.now().date())
st.markdown(f"### Swing Trade Setups for: {btest_date}")

# ---------------------- STOCK UNIVERSE ----------------------
from nse500list import NIFTY_500
# For testing only:
# NIFTY_500 = ["AUBANK.NS"]

# ---------------------- FUNCTIONS ----------------------
def fetch_stock_data(symbol):
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)
        df.dropna(inplace=True)
        df['EMA_5'] = df['Close'].ewm(span=5).mean()
        df['Volume_SMA_20'] = df['Volume'].rolling(20).mean()
        df['Range'] = df['High'] - df['Low']
        df['Range_SMA_20'] = df['Range'].rolling(20).mean()
        df.dropna(inplace=True)
        return df
    except Exception as e:
        st.error(f"Error fetching {symbol}: {e}")
        return None

def check_breakout_criteria(df):
    if df is None or len(df) < 21:
        return False, None

    df = df.dropna()
    if df.empty or len(df) < 21:
        return False, None

    today = df.iloc[-1]
    prev = df.iloc[-2]

    try:
        c1 = today['Close'] > today['EMA_5']
        c2 = today['Volume'] > (today['Volume_SMA_20'] * (1.5 if strict_mode else 1.0))
        c3 = today['Close'] > today['Open']
        c4 = today['Close'] > prev['High']
        c5 = today['Range'] < 1.5 * df['Range_SMA_20'].iloc[-1]
        c6 = today['Close'] >= df['Close'].iloc[-20:].min()

        if all([c1, c2, c3, c4, c5, c6]):
            entry = today['Close']
            sl = round(entry * 0.98, 2)
            target = round(entry + (entry - sl) * RR_RATIO, 2)
            symbol = df.attrs.get("symbol", "Unknown")
            return True, {
                "entry": entry,
                "sl": sl,
                "target": target,
                "symbol": symbol,
                "date": df.index[-1]
            }
        return False, None

    except Exception as e:
        symbol = df.attrs.get("symbol", "Unknown")
        st.error(f"Error evaluating conditions for {symbol}: {e}")
        return False, None

# ---------------------- SCAN ----------------------
results = []
with st.spinner("🔍 Scanning NIFTY 500 stocks..."):
    for stock in NIFTY_500:
        data = fetch_stock_data(stock)
        if data is not None:
            # 🔎 Only include candles up to selected date
            data = data[data.index <= pd.to_datetime(btest_date)]
            if data.empty or len(data) < 21:
                continue

            data.attrs["symbol"] = stock
            valid, levels = check_breakout_criteria(data)
            if valid:
                risk_amount = (risk_pct / 100) * capital
                risk_per_share = levels['entry'] - levels['sl']
                if risk_per_share == 0:
                    continue  # prevent division by zero
                qty = int(risk_amount / risk_per_share)
                levels['qty'] = qty
                results.append(levels)

# ---------------------- RESULTS ----------------------
if results:
    st.success(f"✅ Found {len(results)} trade setup(s)")
    df_results = pd.DataFrame(results)
    st.dataframe(df_results[['symbol', 'entry', 'sl', 'target', 'qty']])

    for res in results:
        df = fetch_stock_data(res['symbol'])
        if df is not None:
            df = df[df.index <= pd.to_datetime(btest_date)]
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index[-50:],
                open=df['Open'][-50:],
                high=df['High'][-50:],
                low=df['Low'][-50:],
                close=df['Close'][-50:],
                name="Candles"
            ))
            # Horizontal lines for entry/SL/target
            for level, color, label in zip(
                [res['entry'], res['sl'], res['target']],
                ["blue", "red", "green"],
                ["Entry", "SL", "Target"]
            ):
                fig.add_shape(
                    type="line",
                    x0=df.index[-50],
                    x1=df.index[-1],
                    y0=level,
                    y1=level,
                    line=dict(color=color, dash="dot"),
                )
                fig.add_annotation(
                    x=df.index[-1], y=level,
                    text=label,
                    showarrow=False,
                    yshift=10 if label == "Entry" else -10,
                    font=dict(color=color)
                )
            st.plotly_chart(fig)
else:
    st.warning("⚠️ No valid trade setups for the selected date. Try changing the date.")
