def format_indicator(value, precision=2):
    if isinstance(value, (int, float)):
        return f"{value:.{precision}f}"
    return str(value) if value is not None else "N/A"

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

