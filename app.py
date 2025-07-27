from flask import Flask, jsonify, Response, render_template
from services import data_service, ai_service
from analysis import technical_analysis
from config import ALPACA_API_KEY, OPENROUTER_API_KEY
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from datetime import datetime, timedelta
import json

app = Flask(__name__)

def format_sse(data: dict, event: str = 'message') -> str:
    """
    Formats data as a Server-Sent Event (SSE) string.
    """
    json_data = json.dumps(data, ensure_ascii=False)
    return f"event: {event}\ndata: {json_data}\n\n"

@app.route('/')
def index():
    return render_template('index.html')

def generate_analysis_stream(symbol: str):
    """
    Generates a stream of analysis updates for a given symbol.
    """
    if not ALPACA_API_KEY or not OPENROUTER_API_KEY:
        yield format_sse({"status": "error", "message": "Error: API keys for Alpaca or OpenRouter are not set."}, event="message")
        return

    try:
        yield format_sse({"status": "info", "message": f"Starting analysis for {symbol}..."}, event="message")

        # --- 1. Set Time Range (Live Analysis) ---
        end_date = datetime.now()
        one_year_ago = end_date - timedelta(days=365)
        five_days_ago = end_date - timedelta(days=5)
        two_days_ago = end_date - timedelta(days=2)

        # --- 2. Fetch Data ---
        yield format_sse({"status": "info", "message": f"Fetching data for {symbol} from Alpaca..."}, event="message")
        dfs = {
            'daily': data_service.get_bars_from_alpaca(symbol, TimeFrame.Day, one_year_ago, end_date),
            '5min': data_service.get_bars_from_alpaca(symbol, TimeFrame(5, TimeFrameUnit.Minute), five_days_ago, end_date),
            '1min': data_service.get_bars_from_alpaca(symbol, TimeFrame.Minute, two_days_ago, end_date)
        }
        yield format_sse({"status": "info", "message": "Data fetched successfully."},
                         event="message")

        # --- 3. Analyze Price Action ---
        yield format_sse({"status": "info", "message": "Analyzing price action..."}, event="message")
        analysis = technical_analysis.analyze_price_action(dfs)
        yield format_sse({"status": "info", "message": "Analysis complete."},
                         event="message")

        # --- 4. Get AI Opportunity Report ---
        yield format_sse({"status": "info", "message": "Generating AI Opportunity Report..."}, event="message")
        full_report = ""
        for chunk in ai_service.get_price_action_opportunity_report(symbol, analysis):
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

if __name__ == '__main__':
    app.run(debug=True)
