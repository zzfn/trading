import requests
import json
from config import OPENROUTER_API_KEY, current_config # 导入 current_config
import time # 用于重试间隔

def get_price_action_opportunity_report(symbol: str, analysis_data: dict):
    """
    Generates a comprehensive trading opportunity report using Price Action and Technical Indicators.
    This function now streams the AI response with retry mechanism.
    """
    def format_indicator(value, precision=2):
        return f"{value:.{precision}f}" if value is not None else "N/A"

    # Helper to format a dictionary of indicators
    def format_indicator_dict(indicators: dict) -> str:
        if not indicators:
            return "  - N/A"
        
        # Define the order and description for each indicator
        indicator_order = {
            'sma_20': '20周期简单移动平均线 (SMA)',
            'sma_50': '50周期简单移动平均线 (SMA)',
            'ema_20': '20周期指数移动平均线 (EMA)',
            'ema_50': '50周期指数移动平均线 (EMA)',
            'rsi': '相对强弱指数 (RSI)',
            'macd_line': 'MACD线',
            'macd_signal': 'MACD信号线',
            'macd_hist': 'MACD柱',
            'bb_upper': '布林带上轨',
            'bb_middle': '布林带中轨',
            'bb_lower': '布林带下轨',
            'stoch_k': '随机指标 %K',
            'stoch_d': '随机指标 %D',
            'adx': '平均动向指数 (ADX)',
            'obv': '能量潮 (OBV)',
            'atr': '平均真实波幅 (ATR)'
        }
        
        lines = []
        for key, description in indicator_order.items():
            value = indicators.get(key)
            if value is not None:
                # OBV is a large number, format it as an integer
                precision = 0 if key == 'obv' else 2
                lines.append(f"     - {description}: {format_indicator(value, precision)}")
        
        return "\n".join(lines) if lines else "  - N/A"

    daily_indicators = analysis_data.get('technical_indicators', {}).get('daily', {})
    five_min_indicators = analysis_data.get('technical_indicators', {}).get('5min', {})

    prompt = f"""
你是一位顶级的、纯粹的价格行为交易宗师 (Price Action Master)。你只相信K线图本身讲述的语言，所有指标都只是次要的辅助确认工具。
你的任务是分析以下 {symbol} 的数据，并输出一份关于“机会点位”的精炼报告。

**--- 最新关键价格 (5分钟线) ---**
- 开盘价: {format_indicator(analysis_data['price_action'].get('latest_open'))}
- 最高价: {format_indicator(analysis_data['price_action'].get('latest_high'))}
- 最低价: {format_indicator(analysis_data['price_action'].get('latest_low'))}
- 收盘价: {format_indicator(analysis_data['price_action'].get('latest_close'))}

**--- 核心价格行为分析 ---**

**1. 日线市场结构 (多维度趋势):**
   - **90天宏观趋势:** 高点: {format_indicator(analysis_data['price_action'].get('daily_90d_high'))}, 低点: {format_indicator(analysis_data['price_action'].get('daily_90d_low'))}
   - **30天中趋势:** 高点: {format_indicator(analysis_data['price_action'].get('daily_30d_high'))}, 低点: {format_indicator(analysis_data['price_action'].get('daily_30d_low'))}
   - **7天周趋势:** 高点: {format_indicator(analysis_data['price_action'].get('daily_7d_high'))}, 低点: {format_indicator(analysis_data['price_action'].get('daily_7d_low'))}
   - **3天微观趋势:** 高点: {format_indicator(analysis_data['price_action'].get('daily_3d_high'))}, 低点: {format_indicator(analysis_data['price_action'].get('daily_3d_low'))}
   - **90天斐波那契50%回调位:** {format_indicator(analysis_data['price_action'].get('fib_50_retracement_90d'))}

**2. 日线价格行为分析:**
   - **价格与50日均线关系:** {analysis_data['price_action'].get('daily_trend_sma50', 'N/A')}
   - **20日与50日均线交叉:** {analysis_data['price_action'].get('daily_sma_crossover', 'N/A')}
   - **价格相对90天高低点:** {analysis_data['price_action'].get('relative_to_90d_range', 'N/A')}

**3. 5分钟K线与成交量:**
   - **最新关键K线:** {analysis_data['price_action'].get('candlestick_pattern', '无')}
   - **看涨吞没形态:** {'是' if analysis_data['price_action'].get('bullish_engulfing') else '否'}
   - **看跌吞没形态:** {'是' if analysis_data['price_action'].get('bearish_engulfing') else '否'}
   - **十字星形态:** {'是' if analysis_data['price_action'].get('doji_pattern') else '否'}
   - **锤头形态:** {'是' if analysis_data['price_action'].get('hammer_pattern') else '否'}
   - **倒锤头形态:** {'是' if analysis_data['price_action'].get('inverted_hammer_pattern') else '否'}
   - **射击之星形态:** {'是' if analysis_data['price_action'].get('shooting_star_pattern') else '否'}
   - **上吊线形态:** {'是' if analysis_data['price_action'].get('hanging_man_pattern') else '否'}
   - **早晨之星形态:** {'是' if analysis_data['price_action'].get('morning_star_pattern') else '否'}
   - **黄昏之星形态:** {'是' if analysis_data['price_action'].get('evening_star_pattern') else '否'}
   - **通用突破信号:** {analysis_data['price_action'].get('general_breakout', '无')}
   - **最新5分钟成交量是否放大:** {analysis_data['confirmation'].get('is_volume_high')}

**--- 全面技术指标 ---**

**1. 日线指标:**
{format_indicator_dict(daily_indicators)}

**2. 5分钟指标:**
{format_indicator_dict(five_min_indicators)}

**--- 你的任务：输出机会点位报告 ---**

请严格按照以下格式，直接输出报告，不要包含任何其他无关内容。

**第一部分：市场综合解读**
   - **趋势与结构:** [以日线市场结构（波段高低点、斐波那契位）为主，结合日线技术指标（如移动平均线、ADX）进行辅助确认，判断当前市场的宏观趋势（上涨、下跌、盘整）和所处阶段。]
   - **短期动能与情绪:** [以5分钟K线和成交量为主，结合5分钟技术指标（如RSI、MACD、Stoch）进行辅助确认，分析当前市场的短期动能、超买/超卖状态和潜在反转信号。]
   - **关键价位:** [列出当前最重要的支撑和阻力位，这些价位主要来自价格行为（如波段高低点、斐波那契位），技术指标（如移动平均线、布林带轨道）作为参考。]

**第二部分：机会点位报告**
   - **重要免责声明:** [必须声明：“以下内容仅为基于数据分析的概率性推测，并非投资建议，市场风险极高，请谨慎参考。”]
   - **核心机会:** [用“如果...那么...”的格式，清晰地描述一个具体的、高概率的交易机会，需结合价格行为和技术指标。]
   - **交易计划:**
     - **方向:** [Call / Put / 观望]
     - **理想入场条件:** [描述触发交易的具体条件，例如：价格回踩至[某个关键价位]，同时5分钟[某个指标]出现[金叉/底背离]信号，并出现[看涨/看跌K线形态]。]
     - **目标价:** [设定1-2个价格目标，并说明依据（如前期高点、布林带上轨、ATR扩展等）。]
     - **止损位:** [设定在关键结构或信号的另一侧，并可参考ATR进行动态调整。]
     - **盈亏比:** [计算并说明这个交易的盈亏比，例如：1:2，1:3]
     - **胜率预估:** [百分比，例如：60%]
   - **依据总结:** [用1-2句话总结此交易计划的核心逻辑，需同时提及价格行为和关键指标的共振。]
"""

    for model_name in current_config.OPENROUTER_MODELS:
        for attempt in range(current_config.OPENROUTER_RETRIES):
            try:
                print(f"Attempting to call OpenRouter API with model: {model_name}, attempt: {attempt + 1}")
                response = requests.post(
                    url="https://openrouter.ai/api/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": model_name, # 使用配置的模型
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "stream": True  # Enable streaming
                    },
                    stream=True  # Important: enable streaming for requests library
                )
                response.raise_for_status()

                for chunk in response.iter_lines():
                    if chunk:
                        decoded_chunk = chunk.decode('utf-8')
                        if decoded_chunk.startswith('data: '):
                            try:
                                json_data = json.loads(decoded_chunk[6:])
                                if 'choices' in json_data and len(json_data['choices']) > 0:
                                    delta = json_data['choices'][0].get('delta', {})
                                    if 'content' in delta and delta['content']:
                                        yield delta['content']
                            except json.JSONDecodeError:
                                # Handle cases where a chunk might not be complete JSON
                                pass
                return # If successful, exit the function

            except requests.exceptions.RequestException as e:
                print(f"Detailed OpenRouter API error for model {model_name}, attempt {attempt + 1}: {e}") # 后端打印详细错误
                time.sleep(1) # 等待1秒后重试

    yield "An error occurred while generating the report after multiple retries. Please try again later." # 所有模型和重试都失败
