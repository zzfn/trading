from utils.formatters import format_indicator, format_indicator_dict

def generate_price_action_prompt(symbol: str, analysis_data: dict) -> str:
    daily_indicators = analysis_data.get('technical_indicators', {}).get('daily', {})
    h4_indicators = analysis_data.get('technical_indicators', {}).get('4h', {})
    h1_indicators = analysis_data.get('technical_indicators', {}).get('1h', {})
    five_min_indicators = analysis_data.get('technical_indicators', {}).get('5min', {})

    def format_pin_bar(timeframe):
        pin_bar_data = analysis_data['price_action'].get(f'{timeframe}_pin_bar', {})
        if not pin_bar_data.get('detected'):
            return "否"
        proximity = ""
        if pin_bar_data.get('near_support'):
            proximity = f", 接近支撑: {format_indicator(pin_bar_data.get('near_support'))}"
        if pin_bar_data.get('near_resistance'):
            proximity = f", 接近阻力: {format_indicator(pin_bar_data.get('near_resistance'))}"
        return f"是 (影线/实体比: {pin_bar_data.get('shadow_to_body_ratio'):.2f}, 成交量放大: {pin_bar_data.get('volume_spike')}{proximity})"

    def format_engulfing(timeframe, pattern_type):
        engulfing_data = analysis_data['price_action'].get(f'{timeframe}_{pattern_type}_engulfing', {})
        if not engulfing_data.get('detected'):
            return "否"
        proximity = ""
        if engulfing_data.get('near_support'):
            proximity = f", 接近支撑: {format_indicator(engulfing_data.get('near_support'))}"
        if engulfing_data.get('near_resistance'):
            proximity = f", 接近阻力: {format_indicator(engulfing_data.get('near_resistance'))}"
        return f"是 (成交量放大: {engulfing_data.get('volume_spike')}{proximity})"

    prompt = f"""
你是一位专业的、客观的价格行为分析师。你的任务是基于提供的多时间框架数据，对 {symbol} 的未来价格方向进行概率性评估。你必须保持中立，并根据所有可用的证据，为看涨（Call）和看跌（Put）两种情况分别提供胜率估算。

**--- 分析框架 ---**
你必须遵循以下框架，先分析价格行为，再结合技术指标进行确认。

1.  **价格行为分析 (核心)**:
    - **K线形态与位置**: 当前K线（特别是Pin Bar, Doji, 吞没形态）出现在哪个关键价位（支撑/阻力/斐波那契）？这暗示了什么？
    - **趋势与结构**: 价格在日线、4小时、1小时的趋势中处于什么位置？是顺势延续、回调，还是潜在的趋势反转？
    - **成交量**: 当前的成交量是放大了还是缩小了？它是否支持K线形态发出的信号？（例如，反转形态是否伴随成交量放大？）

2.  **技术指标分析 (辅助确认)**:
    - **RSI**: RSI是否处于超买（>70）或超卖（<30）区域？这是否与价格行为信号共振？
    - **MACD**: MACD是否出现金叉/死叉，或者出现背离？这是否确认了价格行为的动能？
    - **ATR**: 当前的ATR数值是多少？它反映了市场的波动性是高还是低？这对潜在的盈亏空间和风险有何影响？

**--- 数据汇总 ---**

**1. 多时间框架趋势:**
   - **日线趋势:** {analysis_data.get('trends', {}).get('daily', 'N/A')}
   - **4小时趋势:** {analysis_data.get('trends', {}).get('4h', 'N/A')}
   - **1小时趋势:** {analysis_data.get('trends', {}).get('1h', 'N/A')}

**2. 关键支撑与阻力:**
   - **前日高点/低点:** {format_indicator(analysis_data['price_action'].get('previous_day_high'))} / {format_indicator(analysis_data['price_action'].get('previous_day_low'))}
   - **90天高点/低点:** {format_indicator(analysis_data['price_action'].get('daily_90d_high'))} / {format_indicator(analysis_data['price_action'].get('daily_90d_low'))}
   - **斐波那契回调位:** 38.2%: {format_indicator(analysis_data['price_action'].get('fib_382_retracement_90d'))}, 50%: {format_indicator(analysis_data['price_action'].get('fib_50_retracement_90d'))}, 61.8%: {format_indicator(analysis_data['price_action'].get('fib_618_retracement_90d'))}

**3. 关键K线形态:**
   - **日线:** Pin Bar: {format_pin_bar('daily')}, 看涨吞没: {format_engulfing('daily', 'bullish')}, 看跌吞没: {format_engulfing('daily', 'bearish')}
   - **4小时:** Pin Bar: {format_pin_bar('4h')}, 看涨吞没: {format_engulfing('4h', 'bullish')}, 看跌吞没: {format_engulfing('4h', 'bearish')}
   - **1小时:** Pin Bar: {format_pin_bar('1h')}, 看涨吞没: {format_engulfing('1h', 'bullish')}, 看跌吞没: {format_engulfing('1h', 'bearish')}

**4. 技术指标:**
   - **日线:** RSI: {format_indicator(daily_indicators.get('rsi'))}, MACD Hist: {format_indicator(daily_indicators.get('macd_hist'))}, ATR: {format_indicator(daily_indicators.get('atr'))}
   - **4小时:** RSI: {format_indicator(h4_indicators.get('rsi'))}, MACD Hist: {format_indicator(h4_indicators.get('macd_hist'))}, ATR: {format_indicator(h4_indicators.get('atr'))}
   - **1小时:** RSI: {format_indicator(h1_indicators.get('rsi'))}, MACD Hist: {format_indicator(h1_indicators.get('macd_hist'))}, ATR: {format_indicator(h1_indicators.get('atr'))}
   - **5分钟:** RSI: {format_indicator(five_min_indicators.get('rsi'))}, MACD Hist: {format_indicator(five_min_indicators.get('macd_hist'))}, ATR: {format_indicator(five_min_indicators.get('atr'))}

**--- 你的任务：输出概率性评估报告 ---**

请严格按照以下格式，对Call和Put的胜率进行独立的、概率性的评估。

**第一部分：看涨 (Call) 概率分析**
   - **支持证据:** [列出所有支持看涨的价格行为和技术指标证据。例如：价格在日线级别的支撑位0.618回调位附近出现了一个1小时的看涨吞没形态，成交量放大1.8倍，同时4小时RSI处于超卖区域。]
   - **反对证据:** [列出所有反对看涨的证据。例如：日线趋势仍为下跌，5分钟MACD出现死叉。]
   - **胜率估算:** [基于以上证据，给出一个具体的看涨胜率估算（例如：60%），并简要说明理由。]

**第二部分：看跌 (Put) 概率分析**
   - **支持证据:** [列出所有支持看跌的证据。]
   - **反对证据:** [列出所有反对看跌的证据。]
   - **胜率估算:** [给出一个具体的看跌胜率估算（例如：40%），并简要说明理由。]

**第三部分：综合结论**
   - **核心观点:** [明确指出当前是Call的胜率更高，还是Put的胜率更高，或者建议“观望”。]
   - **主要依据:** [用1-2句话总结你的核心观点所依赖的最重要证据。]
"""
    return prompt