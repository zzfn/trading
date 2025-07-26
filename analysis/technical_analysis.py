import pandas as pd
import pandas_ta as ta

def analyze_data(df: pd.DataFrame) -> dict:
    """
    Performs technical analysis on the stock data.
    """
    analysis = {}

    # Calculate technical indicators
    df.ta.rsi(append=True)
    df.ta.macd(append=True)
    df.ta.bbands(append=True)

    # Get the latest data
    latest = df.iloc[-1]

    analysis['latest_close'] = latest.get('Close')
    analysis['rsi'] = latest.get('RSI_14')
    analysis['macd_line'] = latest.get('MACD_12_26_9')
    analysis['macd_signal'] = latest.get('MACDs_12_26_9')
    analysis['bollinger_upper'] = latest.get('BBU_20_2.0')
    analysis['bollinger_lower'] = latest.get('BBL_20_2.0')

    # Basic support and resistance
    recent_data = df.tail(60)
    analysis['support'] = recent_data['Low'].min()
    analysis['resistance'] = recent_data['High'].max()

    # Basic bullish/bearish engulfing pattern detection
    if len(df) >= 2:
        previous = df.iloc[-2]
        if latest['Close'] > previous['Open'] and latest['Open'] < previous['Close'] and latest['Close'] > previous['Close'] and latest['Open'] < previous['Open']:
            analysis['candlestick_pattern'] = 'Bullish Engulfing'
        elif latest['Close'] < previous['Open'] and latest['Open'] > previous['Close'] and latest['Close'] < previous['Close'] and latest['Open'] > previous['Open']:
            analysis['candlestick_pattern'] = 'Bearish Engulfing'
        else:
            analysis['candlestick_pattern'] = 'None'

    return analysis