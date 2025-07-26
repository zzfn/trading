import pandas as pd
import pandas_ta as ta

def analyze_price_action(dfs: dict) -> dict:
    """
    Performs a pure price action analysis with volume and RSI as secondary indicators.
    """
    analysis = {'price_action': {}, 'confirmation': {}}

    # --- Daily Analysis: Market Structure & Key Zones ---
    df_daily = dfs.get('daily')
    if df_daily is not None and not df_daily.empty:
        # Market Structure (based on last 90 days for swing/intraday relevance)
        df_daily_recent = df_daily.loc[df_daily.index >= (df_daily.index.max() - pd.Timedelta(days=90))]
        
        # Ensure df_daily_recent is not empty before proceeding
        if not df_daily_recent.empty:
            swing_highs = df_daily_recent['High'].rolling(window=10, center=True).max().dropna().nlargest(2).sort_index()
            swing_lows = df_daily_recent['Low'].rolling(window=10, center=True).min().dropna().nsmallest(2).sort_index()

            if len(swing_highs) > 1:
                analysis['price_action']['prev_swing_high'] = swing_highs.iloc[0]
                analysis['price_action']['last_swing_high'] = swing_highs.iloc[1]
            if len(swing_lows) > 1:
                analysis['price_action']['prev_swing_low'] = swing_lows.iloc[0]
                analysis['price_action']['last_swing_low'] = swing_lows.iloc[1]

            # Fibonacci 50% Retracement (based on the 90-day range)
            high_90d = df_daily_recent['High'].max()
            low_90d = df_daily_recent['Low'].min()
            if high_90d and low_90d:
                analysis['price_action']['fib_50_retracement'] = high_90d - 0.5 * (high_90d - low_90d)

    # --- 5-Minute Analysis: Candlestick & Volume Confirmation ---
    df_5min = dfs.get('5min')
    if df_5min is not None and not df_5min.empty:
        latest_bar = df_5min.iloc[-1]
        # Add latest OHLC to price_action
        analysis['price_action']['latest_open'] = latest_bar['Open']
        analysis['price_action']['latest_high'] = latest_bar['High']
        analysis['price_action']['latest_low'] = latest_bar['Low']
        analysis['price_action']['latest_close'] = latest_bar['Close']

        # Volume Analysis
        avg_volume = df_5min['Volume'].tail(20).mean()
        analysis['confirmation']['is_volume_high'] = latest_bar['Volume'] > (avg_volume * 1.5)
        
        # Candlestick Pattern (Pin Bar detection)
        body_size = abs(latest_bar['Open'] - latest_bar['Close'])
        total_range = latest_bar['High'] - latest_bar['Low']
        upper_wick = latest_bar['High'] - max(latest_bar['Open'], latest_bar['Close'])
        lower_wick = min(latest_bar['Open'], latest_bar['Close']) - latest_bar['Low']
        candlestick_pattern = "None"
        if total_range > 0 and body_size / total_range < 0.33: # Body is less than 1/3 of the total range
            if lower_wick > body_size * 2: 
                candlestick_pattern = "Bullish Pin Bar"
            elif upper_wick > body_size * 2:
                candlestick_pattern = "Bearish Pin Bar"
        analysis['price_action']['candlestick_pattern'] = candlestick_pattern

        # RSI as a final confirmation indicator
        df_5min.ta.rsi(append=True)
        analysis['confirmation']['5min_rsi'] = df_5min['RSI_14'].iloc[-1]

        # MACD for auxiliary confirmation
        df_5min.ta.macd(append=True)
        analysis['confirmation']['5min_macd_line'] = df_5min['MACD_12_26_9'].iloc[-1]
        analysis['confirmation']['5min_macd_signal'] = df_5min['MACDs_12_26_9'].iloc[-1]

    # --- 1-Minute Analysis: Precise Entry ---
    df_1min = dfs.get('1min')
    if df_1min is not None and not df_1min.empty:
        # We already get latest_close from 5min, but ensure it's there if 5min is empty
        if 'latest_close' not in analysis['price_action']:
            analysis['price_action']['latest_close'] = df_1min['Close'].iloc[-1]

    return analysis
