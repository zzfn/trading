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
        daily_start_date = end_date - timedelta(days=365) # Default to one year ago

        five_days_ago = end_date - timedelta(days=5)
        two_days_days_ago = end_date - timedelta(days=2)

        # --- 2. Fetch Data ---
        yield format_sse({"status": "info", "message": f"Fetching data for {symbol} from Alpaca..."}, event="message")
        dfs = {
            'daily': data_service.get_bars_from_alpaca(symbol, TimeFrame.Day, daily_start_date, end_date),
            '5min': data_service.get_bars_from_alpaca(symbol, TimeFrame(5, TimeFrameUnit.Minute), five_days_ago, end_date),
            '1min': data_service.get_bars_from_alpaca(symbol, TimeFrame.Minute, two_days_days_ago, end_date)
        }
        yield format_sse({"status": "info", "message": "Data fetched successfully."},
                         event="message")

        # --- 3. Analyze Price Action ---
        yield format_sse({"status": "info", "message": "Analyzing price action..."}, event="message")
        analysis = technical_analysis.analyze_price_action(dfs)
        yield format_sse({"status": "info", "message": "Analysis complete."},
                         event="message")

        # --- 4. Backtest ---
        yield format_sse({"status": "info", "message": "正在运行优化后的价格行为回测..."}, event="message")
        backtest_start_date = end_date - timedelta(days=30)
        df_backtest_raw = data_service.get_bars_from_alpaca(symbol, TimeFrame(5, TimeFrameUnit.Minute), backtest_start_date, end_date)
        
        if df_backtest_raw is not None and not df_backtest_raw.empty:
            key_levels = technical_analysis.get_key_levels(analysis)
            _, df_backtest = technical_analysis.calculate_technical_indicators(df_backtest_raw.copy())
            signals = technical_analysis.generate_price_action_signals(df_backtest, key_levels, trend_filter_ema=50)
            
            backtest_results = backtest_service.get_backtest_results(df_backtest, signals, take_profit_pct=0.03, atr_multiplier=2.0)
            
            # --- 翻译并格式化回测结果 ---
            strategy_desc_cn = "价格行为 (Pin Bar/吞噬形态 at S/R) + EMA50趋势过滤 & ATR动态止损"
            backtest_results['strategy_description'] = strategy_desc_cn

            start_date_str = backtest_start_date.strftime("%Y-%m-%d")
            end_date_str = end_date.strftime("%Y-%m-%d")
            date_range_str = f"{start_date_str} to {end_date_str}"

            results_cn = {
                "策略描述": strategy_desc_cn,
                "回测时间范围": date_range_str,
                "胜率": f"{backtest_results.get('win_rate', 0):.2%}",
                "总交易次数": backtest_results.get('total_trades', 0),
                "平均每笔盈亏": f"{backtest_results.get('average_pnl', 0):.4f}",
                "总盈亏": f"{backtest_results.get('total_pnl', 0):.4f}",
                "夏普比率": f"{backtest_results.get('sharpe_ratio', 'N/A')}",
                "最大回撤": f"{backtest_results.get('max_drawdown', 0):.2%}",
            }

            print(f"--- 价格行为回测结果 ---")
            for key, value in results_cn.items():
                print(f"{key}: {value}")
            print("--------------------------")
            yield format_sse({"status": "backtest_results", "results": results_cn}, event="message")
        else:
            backtest_results = {}
            yield format_sse({"status": "info", "message": "没有足够数据进行回测。"}, event="message")


        # --- 5. Get AI Opportunity Report ---
        yield format_sse({"status": "info", "message": "Generating AI Opportunity Report..."}, event="message")
        full_report = ""
        current_time_str = datetime.now().strftime('%Y-%m-%d %H:%M EDT')
        for chunk in ai_service.get_ai_analysis(symbol, analysis, backtest_results=backtest_results, current_time=current_time_str):
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

