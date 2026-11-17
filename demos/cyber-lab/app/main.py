from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import STATIC_DIR

from app.routes import home
from app.routes import login
from app.routes import search

app = FastAPI(title="Cyber Lab")

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

app.include_router(home.router)
app.include_router(login.router)
app.include_router(search.router)
