import os
import dotenv
dotenv.load_dotenv()

# 魔搭
MODEL_NAME = os.getenv('MODA_MODEL_NAME')
API_KEY = os.getenv('MODA_API_KEY')
BASE_URL = os.getenv('MODA_BASE_URL')

# tavily
TAVILY_API_KEY = os.getenv('TAVILY_API_KEY')

# Google Search API
SERPAPI_API_KEY= os.getenv('SERPAPI_API_KEY')

# 高德天气
GAODE_WEATHER_KEY = os.getenv('GAODE_WEATHER_KEY')

