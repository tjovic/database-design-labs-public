from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database import get_connection
from app.config import TEMPLATES_DIR

router = APIRouter()

templates = Jinja2Templates(directory=TEMPLATES_DIR)


def render(request, mode=None, query=None, username=None, password=None, result=None):
    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "request": request,
            "mode": mode,
            "query": query,
            "parameters": None if username is None else {
                "username": username,
                "password": password,
            },
            "result": result,
        },
    )


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return render(request)


@router.post("/login/secure")
async def secure_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    # The input is sent as a parameter value (? placeholders), never as
    # SQL text. The parser cannot confuse it for code.
    query = (
        "SELECT FullName\n"
        "FROM Users\n"
        "WHERE Username = ? AND Password = ?"
    )

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(query, (username, password))
    row = cursor.fetchone()
    conn.close()

    if row:
        result = {"success": True, "full_name": row[0]}
    else:
        result = {"success": False, "message": "Incorrect username or password."}

    return render(request, "Secure", query, username, password, result)


@router.post("/login/vulnerable")
async def vulnerable_login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    # VULNERABLE ON PURPOSE. The input is pasted straight into the SQL
    # text, so an attacker can change what the query does.
    #
    # Like a real login, this endpoint shows only a welcome message or an
    # error -- it never prints the rows it read. Data still leaks: through
    # the welcome name (UNION), through error messages, or one yes/no
    # answer at a time (blind). That is the point of this page.
    query = (
        "SELECT FullName\n"
        "FROM Users\n"
        f"WHERE Username = '{username}' AND Password = '{password}'"
    )

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query)
        row = cursor.fetchone()
        if row:
            result = {"success": True, "full_name": row[0]}
        else:
            result = {"success": False, "message": "Incorrect username or password."}
    except Exception as error:
        # A real application should never show the database error to the
        # user. This one does, so you can see error-based injection work.
        result = {"success": False, "message": f"SQL error: {error}"}
    finally:
        conn.close()

    return render(request, "Vulnerable", query, username, password, result)
