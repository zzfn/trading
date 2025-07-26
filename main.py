from services import data_service, ai_service
from analysis import technical_analysis, charting_service
from config import ALPACA_API_KEY, ALPACA_SECRET_KEY, OPENROUTER_API_KEY
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
import os
from datetime import datetime, timedelta

def main():
    """
    Main function to run the multi-timeframe stock analysis using Alpaca as the sole data source.
    """
    if not ALPACA_API_KEY or not OPENROUTER_API_KEY:
        print("Error: API keys for Alpaca or OpenRouter are not set.")
        return

    symbol = "SPY"  # Example stock symbol

    try:
        # --- 1. Fetch Data from Alpaca ---
        print("Fetching all data from Alpaca...")
        today = datetime.now()
        one_year_ago = today - timedelta(days=365)
        five_days_ago = today - timedelta(days=5)
        two_days_ago = today - timedelta(days=2)

        time_ranges = {
            'daily': f"{one_year_ago.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}",
            '5min': f"{five_days_ago.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}",
            '1min': f"{two_days_ago.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}"
        }

        dfs = {
            'daily': data_service.get_bars_from_alpaca(symbol, TimeFrame.Day, one_year_ago, today),
            '5min': data_service.get_bars_from_alpaca(symbol, TimeFrame(5, TimeFrameUnit.Minute), five_days_ago, today),
            '1min': data_service.get_bars_from_alpaca(symbol, TimeFrame.Minute, two_days_ago, today)
        }
        print("Data fetched successfully.")

        # --- 2. Analyze Data ---
        print("Analyzing multi-timeframe data...")
        analysis = technical_analysis.analyze_data_multi_timeframe(dfs)
        print("Analysis complete.")

        # --- 3. Get AI Analysis ---
        print("Getting AI analysis...")
        ai_insight = ai_service.get_multi_timeframe_ai_analysis(symbol, analysis, time_ranges)
        print("AI analysis received.")

        # --- 4. Save Results ---
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        result_dir = os.path.join("analysis_results", f"{symbol}_{timestamp}_Alpaca_MTA")
        os.makedirs(result_dir, exist_ok=True)

        # Save charts
        charting_service.plot_chart(dfs['daily'], f"{symbol} Daily Chart", os.path.join(result_dir, "daily_chart.png"))
        charting_service.plot_chart(dfs['5min'], f"{symbol} 5-Minute Chart", os.path.join(result_dir, "5min_chart.png"))
        charting_service.plot_chart(dfs['1min'], f"{symbol} 1-Minute Chart", os.path.join(result_dir, "1min_chart.png"))

        # Save report
        report_path = os.path.join(result_dir, "report.txt")
        with open(report_path, 'w') as f:
            f.write(ai_insight)
        print(f"Full report saved to {report_path}")

        # --- 5. Print to Console ---
        print("\n--- Multi-Timeframe Analysis Report (Alpaca Unified) ---")
        print(ai_insight)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
