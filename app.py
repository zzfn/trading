from flask import Flask, jsonify, Response, render_template
from services import data_service, ai_service, backtest_service
from analysis import technical_analysis
from config import ALPACA_API_KEY, OPENROUTER_API_KEY, current_config # Import current_config
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.debug = current_config.DEBUG # Set debug mode based on config

def format_sse(data: dict, event: str = 'message') -> str:
    """
    Formats data as a Server-Sent Event (SSE) string.
    """
    json_data = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {json_data}\n\n"

@app.route('/analyze')
def analyze_page():
    return render_template('analyze.html')

@app.route('/backtest')
def backtest_page():
    return render_template('backtest.html')

@app.route('/backtest/<symbol>', methods=['POST'])
def run_backtest_endpoint(symbol):
    try:
        end_date = datetime.now()
        backtest_start_date = end_date - timedelta(days=30)
        df_backtest_raw = data_service.get_bars_from_alpaca(symbol, TimeFrame(5, TimeFrameUnit.Minute), backtest_start_date, end_date)

        if df_backtest_raw is None or df_backtest_raw.empty:
            return jsonify({"status": "error", "message": "No data for backtest."}), 400

        # We need to run a broader analysis to get key levels for the backtest
        daily_start_date = end_date - timedelta(days=365)
        dfs_for_levels = {
            'daily': data_service.get_bars_from_alpaca(symbol, TimeFrame.Day, daily_start_date, end_date),
        }
        analysis_for_levels = technical_analysis.analyze_price_action(dfs_for_levels)
        key_levels = technical_analysis.get_key_levels(analysis_for_levels)

        _, df_backtest = technical_analysis.calculate_technical_indicators(df_backtest_raw.copy())
        signals = technical_analysis.generate_price_action_signals(df_backtest, key_levels, trend_filter_ema=20)
        
        backtest_results = backtest_service.get_backtest_results(df_backtest, signals, atr_multiplier=2.0, reward_risk_ratio=2.0)
        
        return jsonify({"status": "success", "results": backtest_results})

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

def generate_analysis_stream(symbol: str):
    """
    Generates a stream of AI analysis updates for a given symbol.
    """
    if not ALPACA_API_KEY or not OPENROUTER_API_KEY:
        yield format_sse({"status": "error", "message": "Error: API keys for Alpaca or OpenRouter are not set."}, event="message")
        return

    try:
        yield format_sse({"status": "info", "message": f"Starting analysis for {symbol}..."}, event="message")

        end_date = datetime.now()
        daily_start_date = end_date - timedelta(days=365)
        five_days_ago = end_date - timedelta(days=5)

        yield format_sse({"status": "info", "message": f"Fetching data for {symbol}..."}, event="message")
        dfs = {
            'daily': data_service.get_bars_from_alpaca(symbol, TimeFrame.Day, daily_start_date, end_date),
            '5min': data_service.get_bars_from_alpaca(symbol, TimeFrame(5, TimeFrameUnit.Minute), five_days_ago, end_date),
        }
        yield format_sse({"status": "info", "message": "Data fetched successfully."},
                         event="message")

        yield format_sse({"status": "info", "message": "Analyzing price action..."}, event="message")
        analysis = technical_analysis.analyze_price_action(dfs)
        yield format_sse({"status": "info", "message": "Analysis complete."},
                         event="message")

        yield format_sse({"status": "info", "message": "Generating AI Opportunity Report..."}, event="message")
        full_report = ""
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M EDT')
        # Note: backtest_results are no longer passed to the AI in this streamlined flow
        for chunk in ai_service.get_ai_analysis(symbol, analysis, backtest_results=None, current_time=current_time_str):
            full_report += chunk
            yield format_sse({"status": "ai_chunk", "content": chunk}, event="message")
        yield format_sse({"status": "info", "message": "Report generated."},
                         event="message")

        yield format_sse({"status": "complete", "symbol": symbol, "report": full_report}, event="message")

    except Exception as e:
        yield format_sse({"status": "error", "message": f"An error occurred: {e}"}, event="message")

@app.route('/analyze/<symbol>', methods=['GET'])
def analyze_stock(symbol):
    return Response(generate_analysis_stream(symbol.upper()), mimetype="text/event-stream")

# Remove the app.run() block as Gunicorn will handle running the app

