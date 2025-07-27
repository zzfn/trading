import pandas as pd
import pandas_ta as ta

def calculate_technical_indicators(df: pd.DataFrame) -> tuple[dict, pd.DataFrame]:
    """
    Calculates a wide range of technical indicators for a given DataFrame.
    Returns a tuple: (latest_indicators_dict, df_with_indicators).
    """
    if df is None or df.empty:
        return {}, df

    # Create a custom strategy for comprehensive indicators
    custom_strategy = ta.Strategy(
        name="Comprehensive Indicators",
        description="A collection of common technical indicators.",
        ta=[
            {"kind": "sma", "length": 20},
            {"kind": "sma", "length": 50},
            {"kind": "ema", "length": 20},
            {"kind": "ema", "length": 50},
            {"kind": "rsi"},
            {"kind": "macd"},
            {"kind": "bbands", "length": 20},
            {"kind": "stoch"},
            {"kind": "adx"},
            {"kind": "obv"},
            {"kind": "atr"},
        ]
    )
    
    # Apply the strategy to the DataFrame (modifies df in place)
    df.ta.strategy(custom_strategy)

    indicators = {}
    # Ensure there's at least one row after TA calculation
    if not df.empty:
        latest = df.iloc[-1]

        key_mapping = {
            'SMA_20': 'sma_20',
            'SMA_50': 'sma_50',
            'EMA_20': 'ema_20',
            'EMA_50': 'ema_50',
            'RSI_14': 'rsi',
            'MACD_12_26_9': 'macd_line',
            'MACDs_12_26_9': 'macd_signal',
            'MACDh_12_26_9': 'macd_hist',
            'BBU_20_2.0': 'bb_upper',
            'BBM_20_2.0': 'bb_middle',
            'BBL_20_2.0': 'bb_lower',
            'STOCHk_14_3_3': 'stoch_k',
            'STOCHd_14_3_3': 'stoch_d',
            'ADX_14': 'adx',
            'OBV': 'obv',
            'ATR_14': 'atr'
        }

        for original_key, new_key in key_mapping.items():
            value = latest.get(original_key)
            indicators[new_key] = float(value) if pd.notna(value) else None

    return indicators, df

def analyze_price_action(dfs: dict) -> dict:
    """
    Performs a pure price action analysis with volume and a comprehensive set of technical indicators.
    """
    analysis = {'price_action': {}, 'confirmation': {}, 'technical_indicators': {}}

    # --- Daily Analysis: Market Structure & Key Zones ---
    df_daily = dfs.get('daily')
    if df_daily is not None and not df_daily.empty:
        # Ensure the index is sorted for time-based slicing
        df_daily = df_daily.sort_index()

        # Calculate and add technical indicators for the daily timeframe
        daily_latest_indicators, df_daily_with_ta = calculate_technical_indicators(df_daily.copy())
        analysis['technical_indicators']['daily'] = daily_latest_indicators

        def _get_swing_points(df_period, prefix):
            if df_period.empty:
                return {}
            
            swing_analysis = {}
            period_high = df_period['High'].max()
            period_low = df_period['Low'].min()
            swing_analysis[f'{prefix}_high'] = period_high
            swing_analysis[f'{prefix}_low'] = period_low
            return swing_analysis

        # Analyze market structure for different daily periods
        df_90d = df_daily_with_ta.loc[df_daily_with_ta.index >= (df_daily_with_ta.index.max() - pd.Timedelta(days=90))]
        analysis['price_action'].update(_get_swing_points(df_90d, 'daily_90d'))

        df_30d = df_daily_with_ta.loc[df_daily_with_ta.index >= (df_daily_with_ta.index.max() - pd.Timedelta(days=30))]
        analysis['price_action'].update(_get_swing_points(df_30d, 'daily_30d'))

        df_7d = df_daily_with_ta.loc[df_daily_with_ta.index >= (df_daily_with_ta.index.max() - pd.Timedelta(days=7))]
        analysis['price_action'].update(_get_swing_points(df_7d, 'daily_7d'))

        df_3d = df_daily_with_ta.loc[df_daily_with_ta.index >= (df_daily_with_ta.index.max() - pd.Timedelta(days=3))]
        analysis['price_action'].update(_get_swing_points(df_3d, 'daily_3d'))

        # Fibonacci 50% Retracement (based on the 90-day range)
        high_90d = analysis['price_action'].get('daily_90d_high')
        low_90d = analysis['price_action'].get('daily_90d_low')
        if high_90d is not None and low_90d is not None:
            analysis['price_action']['fib_50_retracement_90d'] = high_90d - 0.5 * (high_90d - low_90d)

        # Daily Trend Analysis
        latest_daily_close = df_daily_with_ta['Close'].iloc[-1]
        daily_sma_50 = analysis['technical_indicators']['daily'].get('sma_50')
        daily_sma_20 = analysis['technical_indicators']['daily'].get('sma_20')

        if daily_sma_50 is not None:
            if latest_daily_close > daily_sma_50:
                analysis['price_action']['daily_trend_sma50'] = "Above 50-SMA (Bullish Bias)"
            elif latest_daily_close < daily_sma_50:
                analysis['price_action']['daily_trend_sma50'] = "Below 50-SMA (Bearish Bias)"
            else:
                analysis['price_action']['daily_trend_sma50'] = "At 50-SMA (Neutral)"
        
        # Check for sufficient data before accessing iloc[-2]
        if daily_sma_20 is not None and daily_sma_50 is not None and len(df_daily_with_ta) >= 2:
            # Access SMA values from the DataFrame with TA columns
            prev_daily_sma_20 = df_daily_with_ta['SMA_20'].iloc[-2]
            prev_daily_sma_50 = df_daily_with_ta['SMA_50'].iloc[-2]

            if daily_sma_20 > daily_sma_50 and prev_daily_sma_20 <= prev_daily_sma_50:
                analysis['price_action']['daily_sma_crossover'] = "20-SMA crossed above 50-SMA (Golden Cross)"
            elif daily_sma_20 < daily_sma_50 and prev_daily_sma_20 >= prev_daily_sma_50:
                analysis['price_action']['daily_sma_crossover'] = "20-SMA crossed below 50-SMA (Death Cross)"
            else:
                analysis['price_action']['daily_sma_crossover'] = "No recent SMA crossover"
        else:
            analysis['price_action']['daily_sma_crossover'] = "N/A (Insufficient data for SMA crossover)"

        # Price relative to 90-day high/low
        if high_90d is not None and low_90d is not None:
            if latest_daily_close >= high_90d * 0.99: # Within 1% of 90-day high
                analysis['price_action']['relative_to_90d_range'] = "Near 90-day High"
            elif latest_daily_close <= low_90d * 1.01: # Within 1% of 90-day low
                analysis['price_action']['relative_to_90d_range'] = "Near 90-day Low"
            else:
                analysis['price_action']['relative_to_90d_range'] = "Within 90-day Range"

    # --- 5-Minute Analysis: Candlestick & Volume Confirmation ---
    df_5min = dfs.get('5min')
    if df_5min is not None and not df_5min.empty:
        # Calculate and add technical indicators for the 5-minute timeframe
        five_min_latest_indicators, df_5min_with_ta = calculate_technical_indicators(df_5min.copy())
        analysis['technical_indicators']['5min'] = five_min_latest_indicators

        latest_bar = df_5min_with_ta.iloc[-1]
        analysis['price_action']['latest_open'] = latest_bar['Open']
        analysis['price_action']['latest_high'] = latest_bar['High']
        analysis['price_action']['latest_low'] = latest_bar['Low']
        analysis['price_action']['latest_close'] = latest_bar['Close']

        # Volume Analysis
        avg_volume = df_5min_with_ta['Volume'].tail(20).mean()
        analysis['confirmation']['is_volume_high'] = latest_bar['Volume'] > (avg_volume * 1.5)
        
        # Candlestick Pattern (Pin Bar detection) - existing
        body_size = abs(latest_bar['Open'] - latest_bar['Close'])
        total_range = latest_bar['High'] - latest_bar['Low']
        upper_wick = latest_bar['High'] - max(latest_bar['Open'], latest_bar['Close'])
        lower_wick = min(latest_bar['Open'], latest_bar['Close']) - latest_bar['Low']
        candlestick_pattern = "None"
        if total_range > 0 and body_size / total_range < 0.33:
            if lower_wick > body_size * 2: 
                candlestick_pattern = "Bullish Pin Bar"
            elif upper_wick > body_size * 2:
                candlestick_pattern = "Bearish Pin Bar"
        analysis['price_action']['candlestick_pattern'] = candlestick_pattern

        # Manual Candlestick Pattern Detection
        # Ensure there are enough bars for pattern recognition (at least 2 for engulfing, 3 for morning/evening star)
        if len(df_5min_with_ta) >= 3:
            # Engulfing Pattern
            prev_bar = df_5min_with_ta.iloc[-2]
            current_bar = df_5min_with_ta.iloc[-1]

            # Bullish Engulfing
            if (current_bar['Close'] > current_bar['Open'] and 
                prev_bar['Close'] < prev_bar['Open'] and 
                current_bar['Open'] < prev_bar['Close'] and 
                current_bar['Close'] > prev_bar['Open']):
                analysis['price_action']['bullish_engulfing'] = True
            else:
                analysis['price_action']['bullish_engulfing'] = False

            # Bearish Engulfing
            if (current_bar['Close'] < current_bar['Open'] and 
                prev_bar['Close'] > prev_bar['Open'] and 
                current_bar['Open'] > prev_bar['Close'] and 
                current_bar['Close'] < prev_bar['Open']):
                analysis['price_action']['bearish_engulfing'] = True
            else:
                analysis['price_action']['bearish_engulfing'] = False

            # Doji (simplified: very small body)
            if abs(current_bar['Open'] - current_bar['Close']) < (current_bar['High'] - current_bar['Low']) * 0.1:
                analysis['price_action']['doji_pattern'] = True
            else:
                analysis['price_action']['doji_pattern'] = False

            # Hammer (simplified: small body, long lower wick, little/no upper wick)
            if (current_bar['Close'] > current_bar['Open'] and # Bullish body
                (current_bar['High'] - max(current_bar['Open'], current_bar['Close'])) < (current_bar['High'] - current_bar['Low']) * 0.1 and # Small upper wick
                (min(current_bar['Open'], current_bar['Close']) - current_bar['Low']) > (current_bar['High'] - current_bar['Low']) * 0.6):
                analysis['price_action']['hammer_pattern'] = True
            elif (current_bar['Close'] < current_bar['Open'] and # Bearish body
                  (current_bar['High'] - max(current_bar['Open'], current_bar['Close'])) < (current_bar['High'] - current_bar['Low']) * 0.1 and # Small upper wick
                  (min(current_bar['Open'], current_bar['Close']) - current_bar['Low']) > (current_bar['High'] - current_bar['Low']) * 0.6):
                analysis['price_action']['hammer_pattern'] = True
            else:
                analysis['price_action']['hammer_pattern'] = False

            # Inverted Hammer (simplified: small body, long upper wick, little/no lower wick)
            if (current_bar['Close'] > current_bar['Open'] and # Bullish body
                (current_bar['High'] - max(current_bar['Open'], current_bar['Close'])) > (current_bar['High'] - current_bar['Low']) * 0.6 and # Long upper wick
                (min(current_bar['Open'], current_bar['Close']) - current_bar['Low']) < (current_bar['High'] - current_bar['Low']) * 0.1):
                analysis['price_action']['inverted_hammer_pattern'] = True
            elif (current_bar['Close'] < current_bar['Open'] and # Bearish body
                  (current_bar['High'] - max(current_bar['Open'], current_bar['Close'])) > (current_bar['High'] - current_bar['Low']) * 0.6 and # Long upper wick
                  (min(current_bar['Open'], current_bar['Close']) - current_bar['Low']) < (current_bar['High'] - current_bar['Low']) * 0.1):
                analysis['price_action']['inverted_hammer_pattern'] = True
            else:
                analysis['price_action']['inverted_hammer_pattern'] = False

            # Shooting Star (simplified: small body, long upper wick, little/no lower wick, bearish context)
            # Similar to inverted hammer, but typically appears after an uptrend
            # For simplicity, we'll use the same logic as inverted hammer for now, and let AI interpret context
            analysis['price_action']['shooting_star_pattern'] = analysis['price_action']['inverted_hammer_pattern']

            # Hanging Man (simplified: small body, long lower wick, little/no upper wick, bullish context)
            # Similar to hammer, but typically appears after an uptrend
            # For simplicity, we'll use the same logic as hammer for now, and let AI interpret context
            analysis['price_action']['hanging_man_pattern'] = analysis['price_action']['hammer_pattern']

            # Morning Star (simplified: 3-bar pattern)
            # Bar 1: Long bearish candle
            # Bar 2: Small body (doji or small candle), gaps down
            # Bar 3: Long bullish candle, closes well into 1st bar's body
            if len(df_5min_with_ta) >= 3:
                bar1 = df_5min_with_ta.iloc[-3]
                bar2 = df_5min_with_ta.iloc[-2]
                bar3 = df_5min_with_ta.iloc[-1]

                if (bar1['Close'] < bar1['Open'] and # Bar 1 bearish
                    abs(bar1['Open'] - bar1['Close']) > (bar1['High'] - bar1['Low']) * 0.6 and # Bar 1 long body
                    abs(bar2['Open'] - bar2['Close']) < (bar2['High'] - bar2['Low']) * 0.3 and # Bar 2 small body
                    bar2['High'] < bar1['Close'] and # Bar 2 gaps down
                    bar3['Close'] > bar3['Open'] and # Bar 3 bullish
                    abs(bar3['Open'] - bar3['Close']) > (bar3['High'] - bar3['Low']) * 0.6 and # Bar 3 long body
                    bar3['Close'] > bar1['Open'] and bar3['Open'] < bar1['Close']):
                    analysis['price_action']['morning_star_pattern'] = True
                else:
                    analysis['price_action']['morning_star_pattern'] = False
            else:
                analysis['price_action']['morning_star_pattern'] = False

            # Evening Star (simplified: 3-bar pattern)
            # Bar 1: Long bullish candle
            # Bar 2: Small body (doji or small candle), gaps up
            # Bar 3: Long bearish candle, closes well into 1st bar's body
            if len(df_5min_with_ta) >= 3:
                bar1 = df_5min_with_ta.iloc[-3]
                bar2 = df_5min_with_ta.iloc[-2]
                bar3 = df_5min_with_ta.iloc[-1]

                if (bar1['Close'] > bar1['Open'] and # Bar 1 bullish
                    abs(bar1['Open'] - bar1['Close']) > (bar1['High'] - bar1['Low']) * 0.6 and # Bar 1 long body
                    abs(bar2['Open'] - bar2['Close']) < (bar2['High'] - bar2['Low']) * 0.3 and # Bar 2 small body
                    bar2['Low'] > bar1['Close'] and # Bar 2 gaps up
                    bar3['Close'] < bar3['Open'] and # Bar 3 bearish
                    abs(bar3['Open'] - bar3['Close']) > (bar3['High'] - bar3['Low']) * 0.6 and # Bar 3 long body
                    bar3['Close'] < bar1['Open'] and bar3['Open'] > bar1['Close']):
                    analysis['price_action']['evening_star_pattern'] = True
                else:
                    analysis['price_action']['evening_star_pattern'] = False
            else:
                analysis['price_action']['evening_star_pattern'] = False

        # Simplified General Breakout Detection (using Bollinger Bands)
        # Ensure BBands are calculated in technical_indicators for 5min
        bb_upper = analysis['technical_indicators']['5min'].get('bb_upper')
        bb_lower = analysis['technical_indicators']['5min'].get('bb_lower')

        if bb_upper is not None and bb_lower is not None:
            if latest_bar['Close'] > bb_upper:
                analysis['price_action']['general_breakout'] = "Bullish Breakout (above BBands)"
            elif latest_bar['Close'] < bb_lower:
                analysis['price_action']['general_breakout'] = "Bearish Breakout (below BBands)"
            else:
                analysis['price_action']['general_breakout'] = "No significant breakout (within BBands)"
        else:
            analysis['price_action']['general_breakout'] = "N/A (BBands not available)"

    # --- 1-Minute Analysis: Precise Entry ---
    df_1min = dfs.get('1min')
    if df_1min is not None and not df_1min.empty:
        if 'latest_close' not in analysis['price_action']:
            analysis['price_action']['latest_close'] = df_1min['Close'].iloc[-1]

    return analysis
