import pandas as pd
import mplfinance as mpf

def plot_chart(df: pd.DataFrame, symbol: str, support: float, resistance: float):
    """
    Generates and saves a stock chart with support and resistance lines.
    """
    # Take the last 90 days of data for a cleaner chart
    data_to_plot = df.tail(90)

    # Create horizontal lines for support and resistance
    hlines = dict(hlines=[support, resistance], colors=['g', 'r'], linestyle='--')

    # Plot the chart
    mpf.plot(
        data_to_plot,
        type='candle',
        style='yahoo',
        title=f'{symbol} Price Action',
        ylabel='Price ($)',
        volume=True,
        hlines=hlines,
        savefig='stock_analysis_engine/stock_chart.png'  # Save the chart to a file
    )
    print(f"Chart saved to stock_analysis_engine/stock_chart.png")