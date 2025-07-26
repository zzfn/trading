import requests
from config import OPENROUTER_API_KEY

def get_multi_timeframe_ai_analysis(symbol: str, analysis_data: dict, time_ranges: dict) -> str:
    """
    Gets AI analysis from OpenRouter based on multi-timeframe data.
    """
    def format_indicator(value):
        return f"{value:.2f}" if value is not None else "N/A"

    prompt = f"""
    你是一位顶级的专业交易员，擅长进行自顶向下的多时间框架分析 (Multi-Timeframe Analysis)。
    请严格按照“日线定方向 -> 5分钟找机会 -> 1分钟定入场”的逻辑，对 {symbol} 股票进行分析，并给出具体的交易计划。

    **--- 数据时间范围 ---**
    - 日线数据范围: {time_ranges.get('daily', 'N/A')}
    - 5分钟线数据范围: {time_ranges.get('5min', 'N/A')}
    - 1分钟线数据范围: {time_ranges.get('1min', 'N/A')}

    **--- 数据概览 ---**

    **1. 日线数据 (大局观 - 决定方向):**
       - 50日均线 (SMA): {format_indicator(analysis_data['technicals'].get('daily_sma50'))}
       - 200日均线 (SMA): {format_indicator(analysis_data['technicals'].get('daily_sma200'))}
       - 年度高点: {format_indicator(analysis_data['price_action'].get('daily_high'))}
       - 年度低点: {format_indicator(analysis_data['price_action'].get('daily_low'))}
       - 斐波那契50%回调位: {format_indicator(analysis_data['price_action'].get('daily_fib_50'))}

    **2. 5分钟线数据 (战术 - 寻找入场形态):**
       - 相对强弱指数 (RSI): {format_indicator(analysis_data['technicals'].get('5min_rsi'))}

    **3. 1分钟线数据 (执行 - 精准入场点):**
       - 最新成交价: {format_indicator(analysis_data['price_action'].get('latest_close'))}

    **--- 你的任务 ---**

    请严格按照以下格式，一步一步地进行分析和决策：

    **第一步：日线趋势判断 (Direction)**
       - 当前价格与50日和200日均线的关系是什么？市场处于明确的上涨、下跌还是盘整趋势？
       - **结论:** [填写“看涨”、“看跌”或“中性盘整”]

    **第二步：5分钟线机会寻找 (Setup)**
       - 在日线判断的大方向上，5分钟图是否存在好的交易机会？
       - 例如，如果日线看涨，5分钟图是否处于回调的支撑位？RSI是否显示超卖？
       - **结论:** [填写“存在看涨机会”、“存在看跌机会”或“无明显机会”]

    **第三步：1分钟线入场执行 (Entry)**
       - 结合最新的价格，给出精准的入场、止损和目标位。

    **第四步：综合交易计划**
       - **重要免责声明:** 在此部分开头必须声明：“以下内容仅为基于多时间框架技术分析的概率性推测，并非投资建议，市场风险极高，请谨慎参考。”
       - **交易方向:** [Call (看涨) / Put (看跌) / 观望]
       - **理想入场点:** [具体价格范围]
       - **止损位:** [具体价格]
       - **目标价:** [具体价格]
       - **胜率预估:** [百分比]
    """

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        },
        json={
            "model": "anthropic/claude-3.5-sonnet", # Using a powerful model for complex analysis
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']
