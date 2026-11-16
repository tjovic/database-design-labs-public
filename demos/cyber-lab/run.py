"""
Entry point for the packaged demo (cyber-lab.exe).

Reads config.env from the folder the .exe (or this script) is in,
starts the app on http://127.0.0.1:<PORT> and opens the login page.
"""

import os
import sys
import threading
import webbrowser

from dotenv import load_dotenv

if getattr(sys, "frozen", False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(base_dir, "config.env"), interpolate=False)

import uvicorn
from app.main import app
from app.database import get_connection
from app.config import DB_USER, DB_PASSWORD

HINTS = [
    ("IM002", "ODBC Driver 18 for SQL Server is not installed. Check in PowerShell: Get-OdbcDriver"),
    ("(4060)", "The database does not exist on this instance. Run the setup scripts on the "
               "instance in SERVER, or fix SERVER in config.env."),
    ("(18456)", "Login failed. Check DB_USER and DB_PASSWORD in config.env (try the same login "
                "in SSMS), or leave both empty for Windows authentication."),
    ("08001", "SQL Server was not found. Check SERVER in config.env (e.g. PCNAME\\SQLEXPRESS) "
              "and that the SQL Server service is running."),
]


def check_connection():
    if DB_USER:
        print(f"Login:      {DB_USER} (SQL authentication, password has "
              f"{len(DB_PASSWORD or '')} characters)")
    else:
        print("Login:      Windows authentication")

    try:
        get_connection().close()
        print("Database:   connection OK")
        return True
    except Exception as error:
        print(f"\nCannot connect to SQL Server:\n{error}\n")
        for code, hint in HINTS:
            if code in str(error):
                print(f"Hint: {hint}")
                break
        return False


port = int(os.getenv("PORT", "8001"))
url = f"http://127.0.0.1:{port}/login"

print(f"Cyber Lab -> {url}")
print(f"SQL Server: {os.getenv('SERVER', 'localhost')}  Database: {os.getenv('DATABASE', 'CyberLab')}")
if not check_connection():
    input("\nFix config.env, then start the program again. Press Enter to close...")
    sys.exit(1)

print("Press CTRL+C to stop.")

threading.Timer(1.5, lambda: webbrowser.open(url)).start()

try:
    uvicorn.run(app, host="127.0.0.1", port=port)
except Exception as error:
    print(f"\nError: {error}")
    input("Press Enter to close...")
