from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database import get_connection

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html"
    )

@router.get("/db-test")
async def db_test():

    conn = get_connection()

    cursor = conn.cursor()

    cursor.execute("SELECT @@VERSION")

    version = cursor.fetchone()[0]

    conn.close()

    return {
        "sql_server": version
    }