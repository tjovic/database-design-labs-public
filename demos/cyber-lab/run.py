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

load_dotenv(os.path.join(base_dir, "config.env"))

import uvicorn
from app.main import app

port = int(os.getenv("PORT", "8001"))
url = f"http://127.0.0.1:{port}/login"

print(f"Cyber Lab -> {url}")
print(f"SQL Server: {os.getenv('SERVER', 'localhost')}  Database: {os.getenv('DATABASE', 'CyberLab')}")
print("Press CTRL+C to stop.")

threading.Timer(1.5, lambda: webbrowser.open(url)).start()

try:
    uvicorn.run(app, host="127.0.0.1", port=port)
except Exception as error:
    print(f"\nError: {error}")
    input("Press Enter to close...")
