import requests
from config import OPENROUTER_API_KEY

def get_ai_analysis(symbol: str, analysis_data: dict) -> str:
    """
    Gets AI analysis from OpenRouter.
    """
    def format_indicator(value):
        """Helper to format numbers or return 'N/A' if None."""
        if value is None:
            return "N/A"
        return f"{value:.2f}"

    prompt = f"""
    你是一位顶级的中文价格行为分析师 (Price Action Trader)。请忘记传统的、滞后的技术指标，专注于K线、成交量、市场结构和斐波那契回调。
    请根据以下提供的 {symbol} 股票数据，用中文进行深入的价格行为分析，并给出一个明确的交易策略。

    **核心价格行为数据:**
    - 最新收盘价: {format_indicator(analysis_data.get('latest_close'))}
    - 90天高点: {format_indicator(analysis_data.get('resistance'))}
    - 90天低点: {format_indicator(analysis_data.get('support'))}
    - **斐波那契50%回调位:** {format_indicator(analysis_data.get('fib_500'))}
    - **斐波那契61.8%回调位 (黄金分割位):** {format_indicator(analysis_data.get('fib_618'))}
    - 最新K线形态: {analysis_data.get('candlestick_pattern', '无明显形态')}

    **你的任务:**
    请严格按照以下格式分点输出你的分析和交易计划：

    **1. 市场结构和趋势分析:**
       - 当前是上涨趋势、下跌趋势还是盘整？是否存在更高的高点(HH)和更高的低点(HL)，或者更低的高点(LH)和更低的低点(LL)？
       - 价格目前处于趋势的哪个阶段（启动、延续、末端）？

    **2. 关键区域分析 (Key Zones):**
       - 基于斐波那契回调位和前期高低点，分析当前价格所处的关键支撑或阻力区域。
       - 价格在50%回调位附近有何表现？是支撑住了还是被突破了？

    **3. 图表形态分析:**
       - 从价格走势看，是否存在潜在的图表形态，如头肩顶/底、双重顶/底、三角形、旗形等？（如果没有，请直说“无明显形态”）

    **4. 明确交易策略:**
       - **重要免责声明:** 在此部分开头必须声明：“以下内容仅为基于价格行为的概率性推测，并非投资建议，市场风险极高，请谨慎参考。”
       - **交易方向:** Call (看涨) 或 Put (看跌)
       - **理想入场点:** [基于关键区域和形态，给出一个具体的价格范围]
       - **短期目标价:** [基于下一个关键区域或形态目标，给出一个具体的价格目标]
       - **止损位:** [给出一个明确的止损价格]
       - **预估胜率:** [给出一个基于当前价格行为的估算百分比]
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