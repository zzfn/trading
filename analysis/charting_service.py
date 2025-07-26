import pandas as pd
import mplfinance as mpf
import os

def plot_chart_advanced(df: pd.DataFrame, symbol: str, analysis: dict):
    """
    Generates and saves an advanced stock chart with multiple technical indicators.
    """
    # --- Create an absolute path for saving the chart ---
    # Get the directory where this script is located (analysis/)
    script_dir = os.path.dirname(__file__)
    # Go up one level to get the project root (stock_analysis_engine/)
    project_root = os.path.dirname(script_dir)
    # Define the save path
    save_path = os.path.join(project_root, f'{symbol}_advanced_chart.png')
    # --- End of path creation ---

    # Prepare data for plotting
    data_to_plot = df.tail(120)  # Plot last 120 days

    # 1. Build list of additional plots (subplots) safely
    ap = []
    if 'RSI_14' in data_to_plot.columns:
        ap.append(mpf.make_addplot(data_to_plot['RSI_14'], panel=1, color='blue', ylabel='RSI'))
    if 'MACD_12_26_9' in data_to_plot.columns and 'MACDs_12_26_9' in data_to_plot.columns:
        ap.append(mpf.make_addplot(data_to_plot['MACD_12_26_9'], panel=2, color='fuchsia', ylabel='MACD'))
        ap.append(mpf.make_addplot(data_to_plot['MACDs_12_26_9'], panel=2, color='cyan'))

    # 2. Build list of moving averages to overlay safely
    moving_averages_to_plot = []
    if 'SMA_20' in data_to_plot.columns:
        moving_averages_to_plot.append(20)
    if 'SMA_50' in data_to_plot.columns:
        moving_averages_to_plot.append(50)

    # 3. Set chart title with candlestick pattern info
    chart_title = f"{symbol} Price Action - Last 120 Days\nLatest Pattern: {analysis.get('candlestick_pattern', 'N/A')}"

    # --- Add Fibonacci 50% line to the plot ---
    fib_50_level = analysis.get('fib_500')
    hlines = []
    if fib_50_level:
        hlines.append((fib_50_level, 'orange', '--', '50% Fib'))
    # --- End of Fibonacci line ---

    # 4. Plot the chart
    mpf.plot(
        data_to_plot,
        type='candle',
        style='yahoo',
        title=chart_title,
        ylabel='Price ($)',
        volume=True,
        mav=moving_averages_to_plot if moving_averages_to_plot else None,
        addplot=ap if ap else None,
        panel_ratios=(3, 1, 1) if ap else (1,),
        figscale=1.5,
        hlines=dict(hlines=[line[0] for line in hlines], colors=[line[1] for line in hlines], linestyle=[line[2] for line in hlines]),
        savefig=save_path
    )

    print(f"Advanced chart saved to {save_path}")
