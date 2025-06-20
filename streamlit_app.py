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
# For testing purposes:
# NIFTY_500 = ["AUBANK.NS"]

# ---------------------- SCANNER FUNCTION ----------------------
def fetch_stock_data(symbol):
    try:
        df = yf.download(symbol, period="6mo", interval="1d", progress=False)
        df.dropna(inplace=True)
        df['EMA_5'] = df['Close'].ewm(span=5).mean()
        df['Volume_SMA_20'] = df['Volume'].rolling(20).mean()
        df['Range'] = df['High'] - df['Low']
        df['Range_SMA_20'] = df['Range'].rolling(20).mean()
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
        c2 = today['Volume'] > (today['Volume_SMA_20'] * (1.1 if strict_mode else 0.9))
        c3 = today['Close'] > today['Open']
        c4 = today['Close'] > prev['High']
        c5 = today['Range'] < 2 * today['Range_SMA_20']
        c6 = today['Close'] >= df['Close'].iloc[-20:].min()

        st.write(f"{df.name}: C1={c1}, C2={c2}, C3={c3}, C4={c4}, C5={c5}, C6={c6}")

        if all([c1, c2, c3, c4, c5, c6]):
            entry = today['Close']
            sl = round(entry * 0.98, 2)
            target = round(entry + (entry - sl) * RR_RATIO, 2)
            return True, {"entry": entry, "sl": sl, "target": target, "symbol": df.name, "date": df.index[-1]}
        return False, None
    except Exception as e:
        st.error(f"Error evaluating conditions for {df.name}: {e}")
        return False, None

# ---------------------- SCAN ----------------------
results = []
with st.spinner("Scanning NIFTY 500 stocks..."):
    for stock in NIFTY_500:
        data = fetch_stock_data(stock)
        if data is not None:
            data.name = stock
            valid, levels = check_breakout_criteria(data)
            if valid:
                risk = (levels['entry'] - levels['sl']) * (risk_pct / 100 * capital) / (levels['entry'] - levels['sl'])
                levels['qty'] = int((risk_pct / 100 * capital) / (levels['entry'] - levels['sl']))
                results.append(levels)

# ---------------------- RESULTS ----------------------
if results:
    st.success(f"Found {len(results)} trade setup(s)")
    df_results = pd.DataFrame(results)
    st.dataframe(df_results[['symbol', 'entry', 'sl', 'target', 'qty']])

    for res in results:
        df = fetch_stock_data(res['symbol'])
        if df is not None:
            fig = go.Figure()
            fig.add_trace(go.Candlestick(
                x=df.index[-50:],
                open=df['Open'][-50:],
                high=df['High'][-50:],
                low=df['Low'][-50:],
                close=df['Close'][-50:],
                name="Candles"
            ))
            fig.add_hline(y=res['entry'], line_dash="dash", line_color="blue", annotation_text="Entry")
            fig.add_hline(y=res['sl'], line_dash="dot", line_color="red", annotation_text="SL")
            fig.add_hline(y=res['target'], line_dash="dot", line_color="green", annotation_text="Target")
            st.plotly_chart(fig)
else:
    st.warning("No trade setups for the selected date. Try another date 📆")
