"""
Entry point for the packaged demo (obp-rest-demo.exe).

Reads config.env from the folder the .exe (or this script) is in,
starts the API on http://127.0.0.1:<PORT> and opens Swagger.
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

load_dotenv(os.path.join(base_dir, "config.env"))

import uvicorn
from api.app import app

port = int(os.getenv("PORT", "8000"))
url = f"http://127.0.0.1:{port}/docs"

print(f"OBP REST Demo -> {url}")
print(f"SQL Server: {os.getenv('SERVER')}  Database: {os.getenv('DATABASE')}")
print("Press CTRL+C to stop.")

threading.Timer(1.5, lambda: webbrowser.open(url)).start()

try:
    uvicorn.run(app, host="127.0.0.1", port=port)
except Exception as error:
    print(f"\nError: {error}")
    input("Press Enter to close...")
