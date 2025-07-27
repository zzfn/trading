import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # Common configurations
    ALPACA_API_KEY = os.getenv("ALPACA_API_KEY")
    ALPACA_SECRET_KEY = os.getenv("ALPACA_SECRET_KEY")
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
    POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

class DevelopmentConfig(Config):
    DEBUG = True
    # Add development-specific configurations here

class ProductionConfig(Config):
    DEBUG = False
    # Add production-specific configurations here

def get_config():
    env = os.getenv("FLASK_ENV", "development") # Default to development
    if env == "production":
        return ProductionConfig
    else:
        return DevelopmentConfig

# Instantiate the correct config based on FLASK_ENV
current_config = get_config()

# Expose API keys directly from the current_config for existing code compatibility
ALPACA_API_KEY = current_config.ALPACA_API_KEY
ALPACA_SECRET_KEY = current_config.ALPACA_SECRET_KEY
OPENROUTER_API_KEY = current_config.OPENROUTER_API_KEY
POLYGON_API_KEY = current_config.POLYGON_API_KEY
ALPHA_VANTAGE_API_KEY = current_config.ALPHA_VANTAGE_API_KEY
