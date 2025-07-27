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
你是一位遵循 Al Brooks 价格行为理论的专业交易员。你的任务是解读市场结构，识别高概率的交易机会。你必须在看涨（Call）和看跌（Put）之间做出明确选择，并提供具体的入场、目标和止损价格。

**--- Al Brooks 分析框架 ---
1.  **市场状态识别**: 当前市场是趋势市（Trend）还是区间震荡市（Trading Range）？是强势趋势还是弱势趋势？
2.  **关键价格水平**: 识别重要的支撑和阻力，特别是前期高低点、趋势线、以及50%回调位。
3.  **寻找交易信号**: 在关键价格水平附近寻找高概率的K线形态（如 Pin Bar, Engulfing Bar）。信号K线本身是否强劲？（例如，Pin Bar的影线是否足够长？收盘价是否超越了前一根K线？）
4.  **入场与风险管理**: 基于信号K线的高低点设置入场（Entry）。使用ATR或信号K线的另一端设置止损（Stop Loss）。
5.  **目标设定**: 至少以1倍的风险（止损距离）作为初始目标。寻找逻辑上的价格目标，如前期高低点或基于前期波段计算的1倍或2倍“衡量波动”（Measured Move）目标。
6.  **综合决策**: 结合所有证据，特别是当前趋势的强度，做出最终的交易决策（Call/Put），并估算胜率。

**--- 数据汇总 ---**

**当前价格:** {format_indicator(current_price)}
**VWAP (5分钟):** {format_indicator(five_min_indicators.get('vwap'))}

**1. 多时间框架趋势:**
   - **日线趋势:** {analysis_data.get('trends', {}).get('daily', 'N/A')}
   - **4小时趋势:** {analysis_data.get('trends', {}).get('4h', 'N/A')}
   - **1小时趋势:** {analysis_data.get('trends', {}).get('1h', 'N/A')}

**2. 关键价格水平:**
   - **前日高点/低点:** {format_indicator(analysis_data['price_action'].get('previous_day_high'))} / {format_indicator(analysis_data['price_action'].get('previous_day_low'))}
   - **90天高点/低点:** {format_indicator(analysis_data['price_action'].get('daily_90d_high'))} / {format_indicator(analysis_data['price_action'].get('daily_90d_low'))}
   - **90天波段50%回调位:** {format_indicator(analysis_data['price_action'].get('swing_50_retracement'))}
   - **衡量波动目标 (基于前日日K):** 1倍: {format_indicator(analysis_data['price_action'].get('measured_move_1x'))}, 2倍: {format_indicator(analysis_data['price_action'].get('measured_move_2x'))}

**3. 关键K线形态:**
   - **5分钟:** Pin Bar: {format_pin_bar('5min')}, 看涨吞没: {format_engulfing('5min', 'bullish')}, 看跌吞没: {format_engulfing('5min', 'bearish')}
   - **1小时:** Pin Bar: {format_pin_bar('1h')}, 看涨吞没: {format_engulfing('1h', 'bullish')}, 看跌吞没: {format_engulfing('1h', 'bearish')}
   - **4小时:** Pin Bar: {format_pin_bar('4h')}, 看涨吞没: {format_engulfing('4h', 'bullish')}, 看跌吞没: {format_engulfing('4h', 'bearish')}

**4. 技术指标:**
   - **5分钟:** RSI: {format_indicator(five_min_indicators.get('rsi'))}, MACD Hist: {format_indicator(five_min_indicators.get('macd_hist'))}, ATR: {format_indicator(five_min_indicators.get('atr'))}
   - **1小时:** RSI: {format_indicator(h1_indicators.get('rsi'))}
   - **日线:** RSI: {format_indicator(daily_indicators.get('rsi'))}
{backtest_section}
**--- 你的任务：生成交易信号报告 ---**

请严格按照以下格式输出报告，不要添加任何额外的解释或评论。

**交易信号报告: {symbol}**

**当前价格**: [在此处插入当前价格]
**信号**: [Call 或 Put]
**目标价**: [在此处插入计算出的目标价，优先考虑衡量波动目标]
**止损价**: [在此处插入计算出的止损价，考虑ATR或信号K线]
**胜率估算**: [在此处插入你的胜率估算，例如: 60%]

**核心依据**:
- **市场结构**: [描述当前市场是趋势还是震荡，以及你的主要判断依据]
- **价格行为**: [描述最关键的K线信号及其位置，例如: 1小时看涨Pin Bar，测试了90天波段的50%回调位]
- **入场与目标**: [简述你的入场逻辑和选择目标价的依据，例如: 在信号K线上方入场，目标为1倍衡量波动]
- **回测参考**: [如果适用，简要说明回测结果如何支持你的决策]

**风险提示**:
- 每笔交易风险控制在账户的 1%-2%。
- 考虑交易成本（佣金、滑点）。
- 当前时间: {current_time}。
"""
    return prompt
    return prompt