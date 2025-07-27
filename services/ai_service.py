import requests
import json
from config import OPENROUTER_API_KEY, current_config # 导入 current_config
import time # 用于重试间隔
from utils.formatters import format_indicator, format_indicator_dict
from templates.ai_prompts import generate_trading_signal_prompt

def get_ai_analysis(symbol: str, analysis_data: dict, backtest_results: dict = None, current_time: str = 'N/A'):
    """
    Generates a comprehensive trading opportunity report using Price Action and Technical Indicators.
    This function now streams the AI response with retry mechanism.
    """
    daily_indicators = analysis_data.get('technical_indicators', {}).get('daily', {})
    five_min_indicators = analysis_data.get('technical_indicators', {}).get('5min', {})

    # Explicitly yield the latest close price at the beginning of the report
    latest_close_price = analysis_data['price_action'].get('latest_close')
    if latest_close_price is not None:
        yield f"**{symbol} 最新收盘价:** {format_indicator(latest_close_price)}\n\n"

    prompt = generate_trading_signal_prompt(symbol, analysis_data, backtest_results, current_time)

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
