from services import data_service, ai_service
from analysis import technical_analysis
from config import ALPACA_API_KEY, OPENROUTER_API_KEY
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from datetime import datetime, timedelta

def main():
    """
    Main function to run the pure Price Action analysis and print the report to the console.
    """
    if not ALPACA_API_KEY or not OPENROUTER_API_KEY:
        print("Error: API keys for Alpaca or OpenRouter are not set.")
        return

    symbol = "NVDA"  # Example stock symbol

    try:
        # --- 1. Set Time Range (Live Analysis) ---
        print("--- RUNNING IN LIVE ANALYSIS MODE ---")
        end_date = datetime.now()

        one_year_ago = end_date - timedelta(days=365)
        five_days_ago = end_date - timedelta(days=5)
        two_days_ago = end_date - timedelta(days=2)

        time_ranges = {
            'daily': f"{one_year_ago.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d %H:%M')}",
            '5min': f"{five_days_ago.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}",
            '1min': f"{two_days_ago.strftime('%Y-%m-%d %H:%M')} to {end_date.strftime('%Y-%m-%d %H:%M')}"
        }

        # --- 2. Fetch Data ---
        print(f"Fetching data for {symbol} from Alpaca...")
        dfs = {
            'daily': data_service.get_bars_from_alpaca(symbol, TimeFrame.Day, one_year_ago, end_date),
            '5min': data_service.get_bars_from_alpaca(symbol, TimeFrame(5, TimeFrameUnit.Minute), five_days_ago, end_date),
            '1min': data_service.get_bars_from_alpaca(symbol, TimeFrame.Minute, two_days_ago, end_date)
        }
        print("Data fetched successfully.")

        # --- 3. Analyze Price Action ---
        print("Analyzing price action...")
        analysis = technical_analysis.analyze_price_action(dfs)
        print("Analysis complete.")

        # --- 4. Get AI Opportunity Report ---
        print("Generating AI Opportunity Report...")
        report = ai_service.get_price_action_opportunity_report(symbol, analysis)
        print("Report generated.")

        # --- 5. Print Final Report to Console ---
        print("\n--- Price Action Opportunity Report ---")
        print(report)

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
