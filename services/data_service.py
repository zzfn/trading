import pandas as pd
from config import ALPACA_API_KEY, ALPACA_SECRET_KEY
from typing import Optional
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime
import pandas as pd
from config import ALPACA_API_KEY, ALPACA_SECRET_KEY
from typing import Optional
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from datetime import datetime
from analysis import technical_analysis

def get_bars_from_alpaca(symbol: str, timeframe: TimeFrame, start_date: datetime, end_date: datetime) -> Optional[pd.DataFrame]:
    """
    Fetches historical stock bars from Alpaca. It will use the free IEX feed.
    """
    # For free data, we must use the IEX feed. The client for that is the default.
    client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
    
    request_params = StockBarsRequest(
        symbol_or_symbols=[symbol],
        timeframe=timeframe,
        start=start_date,
        end=end_date,
        feed='iex' # Explicitly request the free IEX data feed
    )
    try:
        bars = client.get_stock_bars(request_params)
        df = bars.df
        if df.empty:
            print(f"No data returned from Alpaca for {symbol} with timeframe {timeframe}.")
            return None
        if isinstance(df.index, pd.MultiIndex):
            df = df.reset_index(level=0, drop=True)
        if df.index.tz is not None:
            df.index = df.index.tz_convert(None)
        df.rename(columns={'open': 'Open', 'high': 'High', 'low': 'Low', 'close': 'Close', 'volume': 'Volume'}, inplace=True)
        
        # Calculate technical indicators and detect Pin Bar
        _, df_with_ta = technical_analysis.calculate_technical_indicators(df.copy())
        df_with_ta = technical_analysis.detect_pin_bar(df_with_ta)

        # Trend judgment based on EMA (using EMA_20 from pandas_ta)
        if 'EMA_20' in df_with_ta.columns:
            df_with_ta['Trend'] = 'Neutral'
            df_with_ta.loc[df_with_ta['Close'] > df_with_ta['EMA_20'], 'Trend'] = 'Uptrend'
            df_with_ta.loc[df_with_ta['Close'] < df_with_ta['EMA_20'], 'Trend'] = 'Downtrend'
        else:
            print("Warning: EMA_20 not found in DataFrame. Trend analysis skipped.")

        return df_with_ta
    except Exception as e:
        print(f"Error fetching data from Alpaca for {symbol}: {e}")
        return None