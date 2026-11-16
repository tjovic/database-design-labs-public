import pyodbc

from app.config import SERVER, DATABASE, DRIVER, DB_USER, DB_PASSWORD


def quote(value):
    """Wrap a value in { } so that characters such as ; or } in a
    password cannot break the connection string (ODBC escaping rule)."""
    return "{" + value.replace("}", "}}") + "}"


def get_connection():
    connection_string = (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER};"
        f"DATABASE={DATABASE};"
        "TrustServerCertificate=yes;"
    )

    if DB_USER:
        # SQL authentication (login and password)
        connection_string += f"UID={quote(DB_USER)};PWD={quote(DB_PASSWORD or '')};"
    else:
        # Windows authentication
        connection_string += "Trusted_Connection=yes;"

    conn = pyodbc.connect(connection_string)

    return conn
