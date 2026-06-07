import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
SUPER_ADMIN_ID = int(os.getenv("SUPER_ADMIN_ID", "1150695"))
DB_URL = os.getenv("DB_URL", "sqlite+aiosqlite:///data/bot.db")
TMP_DIR = Path(os.getenv("TMP_DIR", "./tmp")).resolve()

# Extract database directory if sqlite
if DB_URL.startswith("sqlite"):
    # e.g., sqlite+aiosqlite:///data/bot.db -> data/bot.db
    db_path_str = DB_URL.split(":///")[1]
    db_dir = Path(db_path_str).parent
    db_dir.mkdir(parents=True, exist_ok=True)

# Ensure temporary directory exists
TMP_DIR.mkdir(parents=True, exist_ok=True)
