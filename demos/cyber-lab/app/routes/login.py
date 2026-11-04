from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database import get_connection

router = APIRouter()

templates = Jinja2Templates(directory="app/templates")


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "result": None,
        },
    )


@router.post("/login/secure")
async def secure_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):

    query = """
        SELECT Id,
               Username,
               FullName,
               Department
        FROM Users
        WHERE Username = ?
          AND Password = ?
    """

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (username, password))
    rows = cursor.fetchall()
    conn.close()

    if rows:
        result = {
            "success": True,
            "rows": [
                {
                    "id": r[0],
                    "username": r[1],
                    "full_name": r[2],
                    "department": r[3],
                }
                for r in rows
            ],
        }
    else:
        result = {
            "success": False,
            "message": "Incorrect username or password.",
        }

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "mode": "Secure",
            "query": query,
            "parameters": {"username": username, "password": password},
            "result": result,
        },
    )


@router.post("/login/vulnerable")
async def vulnerable_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):

    query = (
        "SELECT Id, Username, FullName, Department, Password "
        "FROM Users "
        f"WHERE Username = '{username}' AND Password = '{password}'"
    )

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(query)
        rows = cursor.fetchall()

        if rows:
            result = {
                "success": True,
                "rows": [
                    {
                        "id": r[0],
                        "username": r[1],
                        "full_name": r[2],
                        "department": r[3],
                        "password": r[4],
                    }
                    for r in rows
                ],
            }
        else:
            result = {
                "success": False,
                "message": "Incorrect username or password.",
            }

    except Exception as e:
        result = {
            "success": False,
            "message": f"SQL error: {e}",
        }

    finally:
        conn.close()

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "mode": "Vulnerable",
            "query": query,
            "parameters": {"username": username, "password": password},
            "result": result,
        },
    )
