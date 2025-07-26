import pandas as pd
import pandas_ta as ta

def analyze_data(df: pd.DataFrame) -> dict:
    """
    Performs technical analysis on the stock data.
    Returns a dictionary with analysis results and the DataFrame with indicators.
    """
    analysis = {}
    df_copy = df.copy()

    # Calculate technical indicators using pandas-ta
    df_copy.ta.rsi(append=True)
    df_copy.ta.macd(append=True)
    df_copy.ta.bbands(append=True)
    df_copy.ta.sma(length=20, append=True)
    df_copy.ta.sma(length=50, append=True)

    # Get the latest data row
    latest = df_copy.iloc[-1]

    # Populate analysis dictionary with latest values
    analysis['latest_close'] = latest.get('Close')
    analysis['rsi'] = latest.get('RSI_14')
    analysis['macd_line'] = latest.get('MACD_12_26_9')
    analysis['macd_signal'] = latest.get('MACDs_12_26_9')
    analysis['bollinger_upper'] = latest.get('BBU_20_2.0')
    analysis['bollinger_lower'] = latest.get('BBL_20_2.0')

    # Basic support and resistance
    recent_data = df_copy.tail(60)
    analysis['support'] = recent_data['Low'].min()
    analysis['resistance'] = recent_data['High'].max()

    # --- Price Action Analysis: Fibonacci Retracement ---
    # Find the highest and lowest points over the last 90 days
    recent_period = df_copy.tail(90)
    high_point = recent_period['High'].max()
    low_point = recent_period['Low'].min()

    # Calculate Fibonacci levels
    price_range = high_point - low_point
    analysis['fib_382'] = high_point - 0.382 * price_range
    analysis['fib_500'] = high_point - 0.5 * price_range
    analysis['fib_618'] = high_point - 0.618 * price_range
    # --- End of Price Action Analysis ---

    # Basic bullish/bearish engulfing pattern detection
    candlestick_pattern = 'None'
    if len(df_copy) >= 2:
        previous = df_copy.iloc[-2]
        if latest['Close'] > previous['Open'] and latest['Open'] < previous['Close'] and latest['Close'] > previous['Close'] and latest['Open'] < previous['Open']:
            candlestick_pattern = 'Bullish Engulfing'
        elif latest['Close'] < previous['Open'] and latest['Open'] > previous['Close'] and latest['Close'] < previous['Close'] and latest['Open'] > previous['Open']:
            candlestick_pattern = 'Bearish Engulfing'
    analysis['candlestick_pattern'] = candlestick_pattern

    # Return both the analysis dictionary and the DataFrame with indicators
    return analysis, df_copy