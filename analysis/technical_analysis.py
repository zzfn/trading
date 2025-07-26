import pandas as pd
import pandas_ta as ta

def analyze_data_multi_timeframe(dfs: dict) -> dict:
    """
    Performs multi-timeframe technical analysis.
    :param dfs: A dictionary of pandas DataFrames with keys like 'daily', '5min', '1min'.
    """
    analysis = {'technicals': {}, 'price_action': {}}

    # --- Daily Analysis (for overall trend) ---
    df_daily = dfs.get('daily')
    if df_daily is not None:
        df_daily.ta.sma(length=50, append=True)
        df_daily.ta.sma(length=200, append=True)
        analysis['technicals']['daily_sma50'] = df_daily['SMA_50'].iloc[-1]
        analysis['technicals']['daily_sma200'] = df_daily['SMA_200'].iloc[-1]

        # Price Action: Highs, Lows, Fibonacci
        high_point = df_daily['High'].max()
        low_point = df_daily['Low'].min()
        price_range = high_point - low_point
        analysis['price_action']['daily_high'] = high_point
        analysis['price_action']['daily_low'] = low_point
        analysis['price_action']['daily_fib_50'] = high_point - 0.5 * price_range

    # --- 5-Minute Analysis (for entry setup) ---
    df_5min = dfs.get('5min')
    if df_5min is not None:
        df_5min.ta.rsi(append=True)
        analysis['technicals']['5min_rsi'] = df_5min['RSI_14'].iloc[-1]

    # --- 1-Minute Analysis (for precise entry) ---
    df_1min = dfs.get('1min')
    if df_1min is not None:
        latest_close = df_1min['Close'].iloc[-1]
        analysis['price_action']['latest_close'] = latest_close

    return analysis
