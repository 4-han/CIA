import os
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT", 5432)
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")

print(f"Debug: DB_HOST loaded in config: {DB_HOST}")
DATA_FILE = os.getenv("DATA_FILE", "../data/database.json") 
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-2.0-flash-lite")
print("Config loading complete.")