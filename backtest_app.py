mode = st.radio("Select Mode", ["Live Scan", "Backtest"])

if mode == "Backtest":
    backtest_days = st.slider("Backtest over past N days", min_value=10, max_value=90, value=30)
    results = []

    for day in range(backtest_days, 1, -1):
        start_bt = datetime.today() - timedelta(days=day+1)
        end_bt = datetime.today() - timedelta(days=day-1)
        for stock in stocks:
            df = yf.download(stock, start=start_bt, end=end_bt, progress=False)
            if df.empty or len(df) < 2:
                continue

            df["20EMA"] = df["Close"].ewm(span=20).mean()
            prev = df.iloc[0]
            last = df.iloc[1]

            if (prev["Close"] < prev["20EMA"]) and (last["Close"] > last["20EMA"]) and (last["Close"] > prev["High"]):
                entry = last["Close"]
                sl = last["Low"]
                risk = entry - sl
                target = entry + reward_ratio * risk

                # Simulate outcome by looking ahead
                future_df = yf.download(stock, start=end_bt, end=end_bt + timedelta(days=5), progress=False)
                outcome = "Open"
                if not future_df.empty:
                    for i in range(len(future_df)):
                        low = future_df["Low"].iloc[i]
                        high = future_df["High"].iloc[i]
                        if low <= sl:
                            outcome = "SL Hit"
                            break
                        elif high >= target:
                            outcome = "Target Hit"
                            break

                results.append({
                    "Date": last.name.date(),
                    "Stock": stock,
                    "Entry": round(entry, 2),
                    "SL": round(sl, 2),
                    "Target": round(target, 2),
                    "Outcome": outcome
                })

    st.write("Backtest Results")
    if results:
        st.dataframe(pd.DataFrame(results))
    else:
        st.warning("No signals found in backtest period.")
