import requests
from config import OPENROUTER_API_KEY

def get_price_action_opportunity_report(symbol: str, analysis_data: dict) -> str:
    """
    Generates a pure Price Action opportunity report.
    """
    def format_indicator(value):
        return f"{value:.2f}" if value is not None else "N/A"

    prompt = f"""
你是一位顶级的、纯粹的价格行为交易宗师 (Price Action Master)。你只相信K线图本身讲述的语言，所有指标都只是次要的辅助确认工具。
你的任务是分析以下 {symbol} 的价格数据，并输出一份关于“机会点位”的精炼报告。

**--- 最新关键价格 (5分钟线) ---**
- 开盘价: {format_indicator(analysis_data['price_action'].get('latest_open'))}
- 最高价: {format_indicator(analysis_data['price_action'].get('latest_high'))}
- 最低价: {format_indicator(analysis_data['price_action'].get('latest_low'))}
- 收盘价: {format_indicator(analysis_data['price_action'].get('latest_close'))}

**--- 核心价格行为数据 ---**

**1. 日线市场结构 (多维度趋势判断):**
   - **90天宏观趋势:**
     - 高点: {format_indicator(analysis_data['price_action'].get('daily_90d_high'))}
     - 低点: {format_indicator(analysis_data['price_action'].get('daily_90d_low'))}
   - **30天中趋势:**
     - 高点: {format_indicator(analysis_data['price_action'].get('daily_30d_high'))}
     - 低点: {format_indicator(analysis_data['price_action'].get('daily_30d_low'))}
   - **7天周趋势:**
     - 高点: {format_indicator(analysis_data['price_action'].get('daily_7d_high'))}
     - 低点: {format_indicator(analysis_data['price_action'].get('daily_7d_low'))}
   - **3天微观趋势:**
     - 高点: {format_indicator(analysis_data['price_action'].get('daily_3d_high'))}
     - 低点: {format_indicator(analysis_data['price_action'].get('daily_3d_low'))}
   - 90天斐波那契50%回调位: {format_indicator(analysis_data['price_action'].get('fib_50_retracement_90d'))}

**2. 5分钟K线与成交量:**
   - 最新关键K线: {analysis_data['price_action'].get('candlestick_pattern', '无')}
   - 最新5分钟成交量是否放大: {analysis_data['confirmation'].get('is_volume_high')}

**3. 辅助确认指标 (仅供参考):**
   - 5分钟RSI: {format_indicator(analysis_data['confirmation'].get('5min_rsi'))}
   - 5分钟MACD线: {format_indicator(analysis_data['confirmation'].get('5min_macd_line'))}
   - 5分钟MACD信号线: {format_indicator(analysis_data['confirmation'].get('5min_macd_signal'))}

**--- 你的任务：输出机会点位报告 ---**

请严格按照以下格式，直接输出报告，不要包含任何其他无关内容。

**第一部分：价格行为解读**
   - **宏观趋势 (多维度判断):** [综合90天、30天、7天和3天的高低点结构，判断当前是上涨、下跌还是盘整趋势。]
   - **当前态势:** [描述当前价格处于什么位置，以及与关键波段高/低点、斐波那契50%回调位的关系。]
   - **潜在图表形态 (TBTL):** [是否存在宽通道、窄通道、三推楔形、头肩顶/底、双顶/底、旗形、三角形、矩形等形态？或者价格是否在“突破”、“测试”某个关键级别？如果没有，请直说“无明显图表形态”。]

**第二部分：机会点位报告**
   - **重要免责声明:** [必须声明：“以下内容仅为基于价格行为的概率性推测，并非投资建议，市场风险极高，请谨慎参考。”]
   - **核心机会:** [用“如果...那么...”的格式，清晰地描述一个具体的、高概率的交易机会。]
   - **交易计划:**
     - **方向:** [Call / Put / 观望]
     - **理想入场条件:** [描述触发交易的具体条件，例如：价格在[关键区域]出现[看涨/看跌K线形态]并伴随[成交量放大/缩量]。]
     - **目标价:** [设定价格目标，并说明是基于哪个价格行为概念（如Measure Move，并给出计算）]
     - **止损位:** [设定在关键K线或关键区域的另一侧]
     - **盈亏比:** [计算并说明这个交易的盈亏比，例如：1:2，1:3]
     - **胜率预估:** [百分比]
   - **依据总结:** [用1-2句话总结此交易计划的核心逻辑。]
"""

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        },
        json={
            "model": "microsoft/mai-ds-r1:free",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']
