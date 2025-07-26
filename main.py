from services import data_service, ai_service
from analysis import technical_analysis, charting_service
from config import ALPHA_VANTAGE_API_KEY, OPENROUTER_API_KEY

def main():
    """
    Main function to run the stock analysis.
    """
    if not ALPHA_VANTAGE_API_KEY or not OPENROUTER_API_KEY or ALPHA_VANTAGE_API_KEY == 'YOUR_ALPHA_VANTAGE_API_KEY' or OPENROUTER_API_KEY == 'YOUR_OPENROUTER_API_KEY':
        print("Error: API keys for Alpha Vantage or OpenRouter are not set.")
        print("Please create a .env file from .env.example and add your API keys.")
        return

    symbol = "BABA"  # Example stock symbol

    try:
        # 1. Get data
        print(f"Fetching daily data for {symbol}...")
        df = data_service.get_daily_data(symbol)
        print("Data fetched successfully.")

        # 2. Analyze data
        print("Analyzing technical data...")
        analysis = technical_analysis.analyze_data(df)
        print("Analysis complete.")

        # 3. Get AI analysis
        print("Getting AI analysis from OpenRouter...")
        ai_insight = ai_service.get_ai_analysis(symbol, analysis)
        print("AI analysis received.")

        # 4. Generate and save chart
        print("Generating chart...")
        charting_service.plot_chart(df, symbol, analysis['support'], analysis['resistance'])

        # 5. Print the report
        print("\n--- Stock Analysis Report ---")
        print(f"Symbol: {symbol}")
        print(f"Date: {df.index[-1].date()}")
        print("\n--- Technical Snapshot ---")
        for key, value in analysis.items():
            if isinstance(value, float):
                print(f"- {key.replace('_', ' ').title()}: {value:.2f}")
            else:
                print(f"- {key.replace('_', ' ').title()}: {value}")

        print("\n--- AI Analyst Insights ---")
        print(ai_insight)
        print("\n---------------------------\n")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
