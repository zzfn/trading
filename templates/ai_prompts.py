from utils.formatters import format_indicator, format_indicator_dict

def generate_trading_signal_prompt(symbol: str, analysis_data: dict, backtest_results: dict = None, current_time: str = 'N/A') -> str:
    daily_indicators = analysis_data.get('technical_indicators', {}).get('daily', {})
    h4_indicators = analysis_data.get('technical_indicators', {}).get('4h', {})
    h1_indicators = analysis_data.get('technical_indicators', {}).get('1h', {})
    five_min_indicators = analysis_data.get('technical_indicators', {}).get('5min', {})
    current_price = analysis_data.get('current_price', 'N/A')

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

    backtest_section = ""
    if backtest_results and backtest_results.get('total_trades', 0) > 0:
        backtest_section = f"""
**回测参考**: 历史胜率 {backtest_results.get('win_rate', 0):.2%}, 基于 {backtest_results.get('total_trades', 0)} 笔交易 ({backtest_results.get('strategy_description', 'N/A')})
"""

    prompt = f"""
你是一位专业的、果断的交易信号分析师。你的任务是基于提供的多时间框架数据，为 {symbol} 生成一个清晰、可操作的交易信号报告。你必须在看涨（Call）和看跌（Put）之间做出明确选择，并提供具体的进入、目标和止损价格。

**--- 分析框架 ---**
你必须严格遵循以下思维过程：
1.  **趋势与结构分析**: 首先判断更高时间框架（日线, 4小时, 1小时）的主要趋势是什么？当前价格是处于顺势延续、回调，还是潜在的趋势反转点？
2.  **价格行为分析**: 在当前趋势背景下，寻找关键的价格行为信号（如 Pin Bar, 吞没形态）。这些信号是否出现在关键的支撑/阻力位或斐波那契水平上？成交量是否支持该信号？
3.  **技术指标确认**: 使用RSI、MACD等指标来确认价格行为的动能。是否存在背离或超买/超卖信号来增强你的判断？
4.  **风险/回报评估**: 基于最近的支撑/阻力位和ATR，设定一个合理的止损价（Stop Loss）和目标价（Target Price）。确保目标价至少是止损价距离的1.5倍以上。
5.  **综合决策**: 结合所有证据，包括历史回测参考（如果提供），做出最终的交易决策（Call/Put），并估算胜率。

**--- 数据汇总 ---**

**当前价格:** {format_indicator(current_price)}
**VWAP (5分钟):** {format_indicator(five_min_indicators.get('vwap'))}

**1. 多时间框架趋势:**
   - **日线趋势:** {analysis_data.get('trends', {}).get('daily', 'N/A')}
   - **4小时趋势:** {analysis_data.get('trends', {}).get('4h', 'N/A')}
   - **1小时趋势:** {analysis_data.get('trends', {}).get('1h', 'N/A')}

**2. 关键支撑与阻力:**
   - **前日高点/低点:** {format_indicator(analysis_data['price_action'].get('previous_day_high'))} / {format_indicator(analysis_data['price_action'].get('previous_day_low'))}
   - **90天高点/低点:** {format_indicator(analysis_data['price_action'].get('daily_90d_high'))} / {format_indicator(analysis_data['price_action'].get('daily_90d_low'))}
   - **斐波那契回调位 (90天):** 38.2%: {format_indicator(analysis_data['price_action'].get('fib_382_retracement_90d'))}, 50%: {format_indicator(analysis_data['price_action'].get('fib_50_retracement_90d'))}, 61.8%: {format_indicator(analysis_data['price_action'].get('fib_618_retracement_90d'))}

**3. 关键K线形态:**
   - **5分钟:** Pin Bar: {format_pin_bar('5min')}, 看涨吞没: {format_engulfing('5min', 'bullish')}, 看跌吞没: {format_engulfing('5min', 'bearish')}
   - **1小时:** Pin Bar: {format_pin_bar('1h')}, 看涨吞没: {format_engulfing('1h', 'bullish')}, 看跌吞没: {format_engulfing('1h', 'bearish')}
   - **4小时:** Pin Bar: {format_pin_bar('4h')}, 看涨吞没: {format_engulfing('4h', 'bullish')}, 看跌吞没: {format_engulfing('4h', 'bearish')}

**4. 技术指标:**
   - **5分钟:** RSI: {format_indicator(five_min_indicators.get('rsi'))}, MACD Hist: {format_indicator(five_min_indicators.get('macd_hist'))}, ATR: {format_indicator(five_min_indicators.get('atr'))}, Volume Spike: {analysis_data['price_action'].get('5min_pin_bar', {}).get('volume_spike', 'N/A')}
   - **1小时:** RSI: {format_indicator(h1_indicators.get('rsi'))}, MACD Hist: {format_indicator(h1_indicators.get('macd_hist'))}
   - **日线:** RSI: {format_indicator(daily_indicators.get('rsi'))}, MACD Hist: {format_indicator(daily_indicators.get('macd_hist'))}
{backtest_section}
**--- 你的任务：生成交易信号报告 ---**

请严格按照以下格式输出报告，不要添加任何额外的解释或评论。

**交易信号报告: {symbol}**

**当前价格**: [在此处插入当前价格]
**信号**: [Call 或 Put]
**目标价**: [在此处插入计算出的目标价]
**止损价**: [在此处插入计算出的止损价]
**胜率估算**: [在此处插入你的胜率估算，例如: 65.00%]

**核心依据**:
- **价格行为**: [描述最关键的K线形态和位置，例如: 5分钟看涨 Pin Bar，影线/实体比 2.5，靠近 30 天低点]
- **趋势**: [描述当前趋势背景，例如: 1 小时上升趋势，5 分钟回调至支撑]
- **技术指标**: [描述起决定性作用的指标读数，例如: 价格 > VWAP ($150.00)，成交量放大 1.6 倍，RSI=48]
- **回测参考**: [如果适用，简要说明回测结果如何支持你的决策，例如: 历史胜率 65%，基于 1 个月 5 分钟数据]

**风险提示**:
- 每笔交易风险控制在账户的 1%-2%。
- 考虑交易成本（佣金、滑点，如 Alpaca 每股 $0.0005）。
- 当前时间: {current_time}。
"""
    return prompt
    return prompt