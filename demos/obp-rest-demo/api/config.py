from dotenv import load_dotenv
import os

# interpolate=False: a "$" in a password is kept as it is
load_dotenv(interpolate=False)

SERVER = os.getenv("SERVER")
DATABASE = os.getenv("DATABASE")
DRIVER = os.getenv("DRIVER")

# Optional SQL authentication. Leave empty to use Windows authentication.
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
