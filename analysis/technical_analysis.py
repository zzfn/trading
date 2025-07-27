import pandas as pd
import pandas_ta as ta
import numpy as np

def get_key_levels(analysis_data: dict) -> dict:
    """Extracts all key support and resistance levels from the analysis data."""
    levels = {'support': {}, 'resistance': {}}
    pa = analysis_data.get('price_action', {})

    # Support Levels
    levels['support']['daily_90d_low'] = pa.get('daily_90d_low')
    levels['support']['previous_day_low'] = pa.get('previous_day_low')
    levels['support']['fib_382'] = pa.get('fib_382_retracement_90d')
    levels['support']['fib_50'] = pa.get('fib_50_retracement_90d')
    levels['support']['fib_618'] = pa.get('fib_618_retracement_90d')

    # Resistance Levels
    levels['resistance']['daily_90d_high'] = pa.get('daily_90d_high')
    levels['resistance']['previous_day_high'] = pa.get('previous_day_high')

    # Remove None values
    levels['support'] = {k: v for k, v in levels['support'].items() if v is not None}
    levels['resistance'] = {k: v for k, v in levels['resistance'].items() if v is not None}
    return levels

def check_proximity_to_levels(price: float, levels: dict, tolerance_percent: float = 0.005) -> tuple[str | None, float | None]:
    """Checks if a price is close to any of the key levels."""
    for level_type, level_values in levels.items():
        for name, value in level_values.items():
            if abs(price - value) / value <= tolerance_percent:
                return level_type, value
    return None, None


def detect_pin_bar(df):
    df['Body'] = abs(df['Close'] - df['Open'])
    df['Upper_Shadow'] = df['High'] - df[['Open', 'Close']].max(axis=1)
    df['Lower_Shadow'] = df[['Open', 'Close']].min(axis=1) - df['Low']
    df['Pin_Bar'] = (df['Body'] < 0.3 * (df['High'] - df['Low'])) & \
                   ((df['Upper_Shadow'] > 2 * df['Body']) | (df['Lower_Shadow'] > 2 * df['Body']))
    df['shadow_to_body_ratio'] = np.where(df['Body'] > 0, (df['Upper_Shadow'] + df['Lower_Shadow']) / df['Body'], 0)
    return df

def calculate_vwap(df):
    df['VWAP'] = ta.vwap(df['High'], df['Low'], df['Close'], df['Volume'])
    return df

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
    df = calculate_vwap(df)

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
            'ATR_14': 'atr',
            'VWAP': 'vwap'
        }

        for original_key, new_key in key_mapping.items():
            value = latest.get(original_key)
            indicators[new_key] = float(value) if pd.notna(value) else None

    return indicators, df

def analyze_price_action(dfs: dict) -> dict:
    """
    Performs a pure price action analysis with volume and a comprehensive set of technical indicators.
    """
    analysis = {'price_action': {}, 'confirmation': {}, 'technical_indicators': {}, 'trends': {}}

    # --- Daily Analysis: Market Structure & Key Zones ---
    df_daily = dfs.get('daily')
    if df_daily is not None and not df_daily.empty:
        df_daily = df_daily.sort_index()
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

        df_90d = df_daily_with_ta.loc[df_daily_with_ta.index >= (df_daily_with_ta.index.max() - pd.Timedelta(days=90))]
        analysis['price_action'].update(_get_swing_points(df_90d, 'daily_90d'))

        high_90d = analysis['price_action'].get('daily_90d_high')
        low_90d = analysis['price_action'].get('daily_90d_low')
        if high_90d is not None and low_90d is not None:
            analysis['price_action']['fib_382_retracement_90d'] = high_90d - 0.382 * (high_90d - low_90d)
            analysis['price_action']['fib_50_retracement_90d'] = high_90d - 0.5 * (high_90d - low_90d)
            analysis['price_action']['fib_618_retracement_90d'] = high_90d - 0.618 * (high_90d - low_90d)

        if len(df_daily_with_ta) > 1:
            analysis['price_action']['previous_day_high'] = df_daily_with_ta['High'].iloc[-2]
            analysis['price_action']['previous_day_low'] = df_daily_with_ta['Low'].iloc[-2]

    key_levels = get_key_levels(analysis)

    # --- Multi-Timeframe Analysis ---
    for timeframe in ['1h', '4h', 'daily']:
        df = dfs.get(timeframe)
        if df is not None and not df.empty:
            latest_indicators, df_with_ta = calculate_technical_indicators(df.copy())
            analysis['technical_indicators'][timeframe] = latest_indicators

            latest_bar = df_with_ta.iloc[-1]
            analysis['price_action'][f'{timeframe}_ohlcv'] = {
                'open': latest_bar['Open'],
                'high': latest_bar['High'],
                'low': latest_bar['Low'],
                'close': latest_bar['Close'],
                'volume': latest_bar['Volume']
            }

            # Trend Analysis
            sma_20 = latest_indicators.get('sma_20')
            sma_50 = latest_indicators.get('sma_50')
            if sma_20 and sma_50:
                if sma_20 > sma_50:
                    analysis['trends'][timeframe] = 'Uptrend'
                else:
                    analysis['trends'][timeframe] = 'Downtrend'
            else:
                analysis['trends'][timeframe] = 'Neutral'


            # Candlestick Pattern Detection
            df_with_ta = detect_pin_bar(df_with_ta.copy())
            latest_bar_with_pin = df_with_ta.iloc[-1]
            if latest_bar_with_pin['Pin_Bar']:
                level_type, level_value = check_proximity_to_levels(latest_bar_with_pin['Close'], key_levels)
                analysis['price_action'][f'{timeframe}_pin_bar'] = {
                    'detected': True,
                    'shadow_to_body_ratio': latest_bar_with_pin['shadow_to_body_ratio'],
                    'volume_spike': latest_bar_with_pin['Volume'] > df_with_ta['Volume'].iloc[-10:-1].mean() * 1.5,
                    f'near_{level_type}': level_value
                }
            else:
                analysis['price_action'][f'{timeframe}_pin_bar'] = {'detected': False}

            if len(df_with_ta) >= 2:
                prev_bar = df_with_ta.iloc[-2]
                current_bar = df_with_ta.iloc[-1]
                if (current_bar['Close'] > current_bar['Open'] and
                    prev_bar['Close'] < prev_bar['Open'] and
                    current_bar['Open'] < prev_bar['Close'] and
                    current_bar['Close'] > prev_bar['Open']):
                    level_type, level_value = check_proximity_to_levels(current_bar['Close'], key_levels)
                    analysis['price_action'][f'{timeframe}_bullish_engulfing'] = {
                        'detected': True,
                        'volume_spike': current_bar['Volume'] > prev_bar['Volume'] * 1.5,
                        f'near_{level_type}': level_value
                    }
                else:
                    analysis['price_action'][f'{timeframe}_bullish_engulfing'] = {'detected': False}

                if (current_bar['Close'] < current_bar['Open'] and
                    prev_bar['Close'] > prev_bar['Open'] and
                    current_bar['Open'] > prev_bar['Close'] and
                    current_bar['Close'] < prev_bar['Open']):
                    level_type, level_value = check_proximity_to_levels(current_bar['Close'], key_levels)
                    analysis['price_action'][f'{timeframe}_bearish_engulfing'] = {
                        'detected': True,
                        'volume_spike': current_bar['Volume'] > prev_bar['Volume'] * 1.5,
                        f'near_{level_type}': level_value
                    }
                else:
                    analysis['price_action'][f'{timeframe}_bearish_engulfing'] = {'detected': False}


    # --- 5-Minute Analysis: Candlestick & Volume Confirmation ---
    df_5min = dfs.get('5min')
    if df_5min is not None and not df_5min.empty:
        five_min_latest_indicators, df_5min_with_ta = calculate_technical_indicators(df_5min.copy())
        analysis['technical_indicators']['5min'] = five_min_latest_indicators

        latest_bar = df_5min_with_ta.iloc[-1]
        analysis['price_action']['latest_open'] = latest_bar['Open']
        analysis['price_action']['latest_high'] = latest_bar['High']
        analysis['price_action']['latest_low'] = latest_bar['Low']
        analysis['price_action']['latest_close'] = latest_bar['Close']

        avg_volume = df_5min_with_ta['Volume'].tail(20).mean()
        analysis['confirmation']['is_volume_high'] = latest_bar['Volume'] > (avg_volume * 1.5)

        df_5min_with_ta = detect_pin_bar(df_5min_with_ta.copy())
        latest_bar_with_pin = df_5min_with_ta.iloc[-1]
        if latest_bar_with_pin['Pin_Bar']:
            analysis['price_action']['pin_bar_detected'] = True
        else:
            analysis['price_action']['pin_bar_detected'] = False

    return analysis

def generate_price_action_signals(df: pd.DataFrame, key_levels: dict, tolerance_percent: float = 0.005, trend_filter_ema: int = 50) -> list:
    """
    Generates trading signals based on price action patterns with a trend filter.

    :param df: DataFrame with OHLCV and EMA indicators.
    :param key_levels: A dictionary with 'support' and 'resistance' levels.
    :param tolerance_percent: The proximity tolerance to a key level.
    :param trend_filter_ema: The period for the EMA trend filter.
    :return: A list of trading signals.
    """
    signals = []
    ema_col = f'EMA_{trend_filter_ema}'
    if ema_col not in df.columns:
        print(f"Warning: Trend filter EMA column '{ema_col}' not found in DataFrame. Skipping trend filter.")
        return signals

    if 'Body' not in df.columns:
        df['Body'] = abs(df['Close'] - df['Open'])
    if 'Upper_Shadow' not in df.columns:
        df['Upper_Shadow'] = df['High'] - df[['Open', 'Close']].max(axis=1)
    if 'Lower_Shadow' not in df.columns:
        df['Lower_Shadow'] = df[['Open', 'Close']].min(axis=1) - df['Low']

    for i in range(1, len(df)):
        current_bar = df.iloc[i]
        prev_bar = df.iloc[i-1]

        # Trend Filter Condition
        is_uptrend = current_bar['Close'] > current_bar[ema_col]
        is_downtrend = current_bar['Close'] < current_bar[ema_col]

        # --- Signal 1: Bullish Pin Bar at Support in an Uptrend ---
        is_bullish_pin_bar = current_bar['Lower_Shadow'] > 2 * current_bar['Body'] and current_bar['Upper_Shadow'] < current_bar['Body']
        if is_bullish_pin_bar and is_uptrend:
            level_type, _ = check_proximity_to_levels(current_bar['Low'], {'support': key_levels.get('support', {})}, tolerance_percent)
            if level_type == 'support':
                signals.append((current_bar.name, 'long'))
                continue

        # --- Signal 2: Bearish Pin Bar at Resistance in a Downtrend ---
        is_bearish_pin_bar = current_bar['Upper_Shadow'] > 2 * current_bar['Body'] and current_bar['Lower_Shadow'] < current_bar['Body']
        if is_bearish_pin_bar and is_downtrend:
            level_type, _ = check_proximity_to_levels(current_bar['High'], {'resistance': key_levels.get('resistance', {})}, tolerance_percent)
            if level_type == 'resistance':
                signals.append((current_bar.name, 'short'))
                continue

        # --- Signal 3: Bullish Engulfing at Support in an Uptrend ---
        is_bullish_engulfing = (current_bar['Close'] > current_bar['Open'] and
                                prev_bar['Close'] < prev_bar['Open'] and
                                current_bar['Close'] > prev_bar['Open'] and
                                current_bar['Open'] < prev_bar['Close'])
        if is_bullish_engulfing and is_uptrend:
            level_type, _ = check_proximity_to_levels(current_bar['Close'], {'support': key_levels.get('support', {})}, tolerance_percent)
            if level_type == 'support':
                signals.append((current_bar.name, 'long'))
                continue

        # --- Signal 4: Bearish Engulfing at Resistance in a Downtrend ---
        is_bearish_engulfing = (current_bar['Close'] < current_bar['Open'] and
                                prev_bar['Close'] > prev_bar['Open'] and
                                current_bar['Close'] < prev_bar['Open'] and
                                current_bar['Open'] > prev_bar['Close'])
        if is_bearish_engulfing and is_downtrend:
            level_type, _ = check_proximity_to_levels(current_bar['Close'], {'resistance': key_levels.get('resistance', {})}, tolerance_percent)
            if level_type == 'resistance':
                signals.append((current_bar.name, 'short'))
                continue

    return signals
