from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes import login

from app.routes import home

app = FastAPI(title="Cyber Lab")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(home.router)

app.include_router(login.router)