from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

# Folders are resolved relative to this file, so the app works from any
# working directory and inside the packaged .exe.
APP_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = APP_DIR / "templates"
STATIC_DIR = APP_DIR / "static"

SERVER = os.getenv("SERVER", "localhost")
DATABASE = os.getenv("DATABASE", "CyberLab")
DRIVER = os.getenv("DRIVER", "ODBC Driver 18 for SQL Server")

# Optional SQL authentication. Leave empty to use Windows authentication.
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
