import os
from dotenv import load_dotenv

load_dotenv()

LLM_API_KEY = os.getenv("DEEPSEEK_API_KEY")
LLM_BASE_URL = "https://api.deepseek.com"
LLM_MODEL = "deepseek-chat"

DATABASE_PATH = "data/demo.db"  