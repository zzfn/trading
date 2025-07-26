import requests
import pandas as pd
from io import StringIO
from config import ALPHA_VANTAGE_API_KEY

def get_daily_data(symbol: str) -> pd.DataFrame:
    """
    Fetches daily stock data from Alpha Vantage and returns it as a pandas DataFrame.
    """
    url = (
        f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY"
        f"&symbol={symbol}&outputsize=full&apikey={ALPHA_VANTAGE_API_KEY}&datatype=csv"
    )
    response = requests.get(url)
    response.raise_for_status()  # Raise an exception for bad status codes

    # Alpha Vantage may return a JSON error message instead of CSV.
    if response.text.strip().startswith('{'):
        raise ValueError(f"Failed to retrieve valid CSV data. API response: {response.text}")

    # Read the CSV data into a pandas DataFrame
    csv_data = StringIO(response.text)
    df = pd.read_csv(csv_data)

    if 'timestamp' not in df.columns:
        raise KeyError("Column 'timestamp' not found in the data. The API response may have changed or returned an error.")

    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp')
    df = df.sort_index(ascending=True)
    
    # Rename columns for clarity
    df.rename(columns={
        'open': 'Open',
        'high': 'High',
        'low': 'Low',
        'close': 'Close',
        'volume': 'Volume'
    }, inplace=True)

    return df