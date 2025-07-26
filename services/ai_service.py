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
    You are a professional financial analyst specializing in price action trading.
    Analyze the following stock data for {symbol} and provide a brief analysis.

    **Technical Indicators:**
    - Latest Close Price: {format_indicator(analysis_data.get('latest_close'))}
    - RSI (14): {format_indicator(analysis_data.get('rsi'))}
    - MACD Line: {format_indicator(analysis_data.get('macd_line'))}
    - MACD Signal: {format_indicator(analysis_data.get('macd_signal'))}
    - Bollinger Upper Band: {format_indicator(analysis_data.get('bollinger_upper'))}
    - Bollinger Lower Band: {format_indicator(analysis_data.get('bollinger_lower'))}
    - Candlestick Pattern: {analysis_data.get('candlestick_pattern', 'N/A')}

    **Your Task:**
    1.  **Market Sentiment:** Based on the data, is the current sentiment bullish, bearish, or neutral?
    2.  **Key Levels:** What are the potential short-term support and resistance levels?
    3.  **Actionable Insight:** Provide a concise, actionable insight for a trader. Do not give financial advice.
    4. response in chinese
    """

    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        },
        json={
            "model": "anthropic/claude-3.5-sonnet",
            "messages": [
                {"role": "user", "content": prompt}
            ]
        }
    )
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content']