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
        # Ensure the index is sorted for time-based slicing
        df_daily = df_daily.sort_index()

        def _get_swing_points(df_period, prefix):
            # Simplified swing point detection: highest/lowest in a period
            # For more robust swing detection, a more complex algorithm would be needed.
            if df_period.empty:
                return {}
            
            swing_analysis = {}
            
            # Get the highest and lowest points in the period
            period_high = df_period['High'].max()
            period_low = df_period['Low'].min()

            # Find the actual bars for these highs/lows
            high_bar = df_period[df_period['High'] == period_high].iloc[-1] if not df_period[df_period['High'] == period_high].empty else None
            low_bar = df_period[df_period['Low'] == period_low].iloc[-1] if not df_period[df_period['Low'] == period_low].empty else None

            # Store the highest and lowest values in the period
            swing_analysis[f'{prefix}_high'] = period_high
            swing_analysis[f'{prefix}_low'] = period_low

            # For more detailed swing points (prev_swing_high/low), we need more sophisticated logic
            # For now, we'll just use the period's max/min as the "latest" swing for that period.
            # A true swing high/low requires looking for a peak/trough with lower/higher points around it.
            # Given the constraints, we'll use the max/min of the period as the primary "swing" reference.
            
            return swing_analysis

        # Analyze market structure for different daily periods
        # 90-day macro trend
        df_90d = df_daily.loc[df_daily.index >= (df_daily.index.max() - pd.Timedelta(days=90))]
        analysis['price_action'].update(_get_swing_points(df_90d, 'daily_90d'))

        # 30-day medium trend
        df_30d = df_daily.loc[df_daily.index >= (df_daily.index.max() - pd.Timedelta(days=30))]
        analysis['price_action'].update(_get_swing_points(df_30d, 'daily_30d'))

        # 7-day weekly trend
        df_7d = df_daily.loc[df_daily.index >= (df_daily.index.max() - pd.Timedelta(days=7))]
        analysis['price_action'].update(_get_swing_points(df_7d, 'daily_7d'))

        # 3-day micro trend
        df_3d = df_daily.loc[df_daily.index >= (df_daily.index.max() - pd.Timedelta(days=3))]
        analysis['price_action'].update(_get_swing_points(df_3d, 'daily_3d'))

        # Fibonacci 50% Retracement (based on the 90-day range for broader context)
        high_90d = analysis['price_action'].get('daily_90d_high')
        low_90d = analysis['price_action'].get('daily_90d_low')
        if high_90d is not None and low_90d is not None:
            analysis['price_action']['fib_50_retracement_90d'] = high_90d - 0.5 * (high_90d - low_90d)

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