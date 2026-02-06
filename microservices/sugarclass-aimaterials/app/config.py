import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# For debugging purposes:
print(f"DEBUG: Attempting to load .env file.")
print(f"DEBUG: LLM_API_URL loaded as: {os.getenv('LLM_API_URL')}")
print(f"DEBUG: LLM_API_KEY is set: {bool(os.getenv('LLM_API_KEY'))}")


class Config:
    """Base configuration."""
    # Project root
    PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    # Database
    DB_NAME = 'rag_content.db'
    DB_PATH = os.path.join(PROJECT_ROOT, 'database', DB_NAME)

    # API Configuration
    LLM_API_URL = os.getenv('LLM_API_URL')
    LLM_API_KEY = os.getenv('LLM_API_KEY')
    LLM_MODEL = os.getenv('LLM_MODEL', 'gemini-3-pro-preview')

    # Fallback APIs
    FALLBACK_APIS = []
    # Example of how to add a fallback API in your .env file:
    # FALLBACK_API_1_URL=https://...
    # FALLBACK_API_1_KEY=sk-...
    # FALLBACK_API_1_MODEL=gemini-2.5-pro
    i = 1
    while True:
        fallback_url = os.getenv(f'FALLBACK_API_{i}_URL')
        fallback_key = os.getenv(f'FALLBACK_API_{i}_KEY')
        fallback_model = os.getenv(f'FALLBACK_API_{i}_MODEL')
        if fallback_url and fallback_key:
            FALLBACK_APIS.append({
                'url': fallback_url,
                'key': fallback_key,
                'model': fallback_model or 'gemini-2.5-pro'
            })
            i += 1
        else:
            break

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

# Select the appropriate configuration based on the environment
config_by_name = dict(
    dev=DevelopmentConfig,
    prod=ProductionConfig
)

key = os.getenv('FLASK_ENV', 'dev')
config = config_by_name[key]
