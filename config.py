import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL") # Public URL (e.g., https://bot-l6ln.onrender.com)
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
try:
    ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
except ValueError:
    ADMIN_ID = 0
