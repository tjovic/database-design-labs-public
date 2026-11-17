from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.database import get_connection
from app.config import TEMPLATES_DIR

router = APIRouter()

templates = Jinja2Templates(directory=TEMPLATES_DIR)

COLUMNS = ["Id", "Name", "Category", "Price"]


def render(request, mode=None, query=None, term=None, result=None):
    return templates.TemplateResponse(
        request=request,
        name="search.html",
        context={
            "request": request,
            "mode": mode,
            "query": query,
            "term": term,
            "columns": COLUMNS,
            "result": result,
        },
    )


@router.get("/search", response_class=HTMLResponse)
async def search_page(request: Request, q: str | None = None, safe: int = 0):
    # No search term yet -> just show the empty form.
    if q is None:
        return render(request)

    if safe:
        # Secure: the term is a parameter value, so it can only ever be a
        # product name to look for -- never new SQL.
        query = (
            "SELECT Id, Name, Category, Price\n"
            "FROM Products\n"
            "WHERE Name LIKE ?\n"
            "ORDER BY Name"
        )
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(query, ("%" + q + "%",))
        rows = cursor.fetchall()
        conn.close()
        mode = "Secure"
    else:
        # VULNERABLE ON PURPOSE: the term is pasted into the SQL text.
        # A search box returns a table of rows, so a UNION SELECT can add
        # rows from any other table -- Users, CreditCards -- to the result.
        query = (
            "SELECT Id, Name, Category, Price\n"
            "FROM Products\n"
            f"WHERE Name LIKE '%{q}%'\n"
            "ORDER BY Name"
        )
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(query)
            rows = cursor.fetchall()
        except Exception as error:
            conn.close()
            return render(request, "Vulnerable", query, q,
                          {"success": False, "message": f"SQL error: {error}"})
        conn.close()
        mode = "Vulnerable"

    result = {
        "success": True,
        "rows": [[cell for cell in row] for row in rows],
    }
    return render(request, mode, query, q, result)
