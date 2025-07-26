import pandas as pd
import mplfinance as mpf

def plot_chart(df: pd.DataFrame, title: str, save_path: str):
    """
    Generates and saves a stock chart.
    """
    if df is None or df.empty:
        print(f"Cannot plot chart, data is empty for {title}")
        return

    mpf.plot(
        df,
        type='candle',
        style='yahoo',
        title=title,
        volume=True,
        figscale=1.2,
        savefig=save_path
    )
    print(f"Chart saved to {save_path}")