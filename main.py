from app import app
from config import current_config # 导入 current_config

if __name__ == '__main__':
    if current_config.DEBUG: # 根据配置判断是否启用调试模式
        app.run(debug=True, port=8080)
    else:
        # 在非调试模式下，通常由Gunicorn等WSGI服务器启动
        # 这里可以留空，或者添加一些提示信息
        print("Application is configured for production. Use a WSGI server like Gunicorn to run.")
